"""Run generated Screen launchers and renderer guards without BitBake."""

import importlib.util
from pathlib import Path
import re
import subprocess
import tempfile
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
DISPLAY = ROOT / 'recipes-samples/images/lmp-feature-display-multimedia.inc'
WESTON = ROOT / 'recipes-graphics/wayland/weston_%.bbappend'
spec = importlib.util.spec_from_file_location('verify_kiosk', ROOT / 'scripts/verify-kiosk-image.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class EtnavivTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def generate(self, features='kiosk-browser etnaviv wayland opengl', debug=False):
        values = {'DISTRO_FEATURES': features, 'IMAGE_FEATURES': 'debug-tweaks' if debug else '',
                  'libexecdir': '/usr/libexec'}
        contains = lambda name, items, yes, no, data: yes if set(items.split()) <= set(values[name].split()) else no
        context = {'bb': types.SimpleNamespace(utils=types.SimpleNamespace(contains=contains)),
                   'd': types.SimpleNamespace(getVar=values.get)}
        body = re.search(r'configure_jaguar_screen_weston\(\) \{\n(.*?)^\}', DISPLAY.read_text(), re.M | re.S)[1]
        body = re.sub(r'\$\{@(.*?)\}', lambda m: eval(m[1], {}, context), body)
        for name, value in {'IMAGE_ROOTFS': str(self.root), 'sysconfdir': '/etc',
                            'systemd_system_unitdir': '/usr/lib/systemd/system',
                            'libexecdir': '/usr/libexec'}.items():
            body = body.replace('${' + name + '}', value)
        subprocess.run(['sh', '-eu', '-c', body], capture_output=True, text=True, check=True, timeout=10)
        return self.root / 'usr/lib/systemd/system/weston.service.d/zzzzzz-screen-etnaviv.conf'

    def renderer(self, name):
        path = self.root / 'usr/lib/libweston-12' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()

    def guard(self):
        body = re.search(r'do_install:append:dd-graphics-etnaviv\(\) \{\n(.*?)^\}', WESTON.read_text(), re.M | re.S)[1]
        for name, value in {'D': str(self.root), 'libdir': '/usr/lib', 'WESTON_MAJOR_VERSION': '12'}.items():
            body = body.replace('${' + name + '}', value)
        return subprocess.run(['sh', '-eu', '-c', 'bbfatal() { echo "$*" >&2; return 1; }\n' + body],
                              capture_output=True, text=True, timeout=10)

    def test_gl_launcher_overrides_retained_g2d_command_without_debug(self):
        vendor = self.generate()
        command = vendor.read_text()
        self.assertNotIn('--use-g2d', command)
        self.assertNotIn('--debug', command)
        self.assertIn('ExecStart=\n', command)
        self.assertIn('ExecStart=/usr/libexec/dd-screen-weston ', command)
        self.assertNotIn('--drm-device=card', command)
        self.assertIn('--modules=systemd-notify.so', command)
        self.assertGreater(vendor.name, 'screen.conf')
        self.assertEqual(command, (self.root / 'etc/systemd/system/weston.service.d/screen.conf').read_text())
        context = self.root / 'usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzzzz-screen-etnaviv-context.conf'
        self.assertIn('Environment=DD_KIOSK_GLES2_COMPAT=1', context.read_text())
        ini = (self.root / 'etc/xdg/weston/weston-screen.ini').read_text()
        self.assertIn('use-g2d=false', ini)
        self.assertIn('shell=kiosk-shell.so', ini)
        self.assertIn('transform=rotate-90', ini)
        self.renderer('gl-renderer.so')
        verifier.verify_etnaviv_weston(self.root)

    def test_capture_stays_development_only(self):
        self.assertIn('--debug', self.generate(debug=True).read_text())

    def test_non_kiosk_screen_retains_g2d(self):
        vendor = self.generate(features='wayland opengl')
        self.assertFalse(vendor.exists())
        self.assertFalse((self.root / 'usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzzzz-screen-etnaviv-context.conf').exists())
        self.assertIn('--use-g2d', (self.root / 'etc/systemd/system/weston.service.d/screen.conf').read_text())

    def test_etnaviv_requires_gl_and_rejects_g2d(self):
        self.assertNotEqual(self.guard().returncode, 0)
        self.renderer('gl-renderer.so')
        self.assertEqual(self.guard().returncode, 0)
        self.renderer('g2d-renderer.so')
        self.assertNotEqual(self.guard().returncode, 0)

    def test_image_checks_reject_missing_override_renderer_and_wrong_command(self):
        with self.assertRaisesRegex(ValueError, 'override'):
            verifier.verify_etnaviv_weston(self.root)
        vendor = self.generate()
        with self.assertRaisesRegex(ValueError, 'gl-renderer'):
            verifier.verify_etnaviv_weston(self.root)
        self.renderer('gl-renderer.so')
        original = vendor.read_text()
        vendor.write_text(original.replace('--modules=', '--use-g2d --modules='))
        with self.assertRaisesRegex(ValueError, 'non-GL'):
            verifier.verify_etnaviv_weston(self.root)
        vendor.write_text(original)
        self.renderer('g2d-renderer.so')
        with self.assertRaisesRegex(ValueError, 'G2D'):
            verifier.verify_etnaviv_weston(self.root)

    def selector(self, drivers):
        self.generate()
        for card, driver in drivers.items():
            target = self.root / 'drivers' / driver
            target.mkdir(parents=True, exist_ok=True)
            device = self.root / 'sys/class/drm' / card / 'device'
            device.mkdir(parents=True)
            (device / 'driver').symlink_to(target)
        stub = self.root / 'weston-stub'
        stub.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
        stub.chmod(0o755)
        launcher = (self.root / 'usr/libexec/dd-screen-weston').read_text()
        launcher = launcher.replace('/sys/class/drm/', str(self.root / 'sys/class/drm') + '/')
        launcher = launcher.replace('/usr/bin/weston', str(stub))
        return subprocess.run(['sh', '-c', launcher, 'selector', '--config=screen.ini'],
                              capture_output=True, text=True, timeout=10)

    def test_selects_imx_display_after_etnaviv_changes_numbering(self):
        result = self.selector({'card0': 'simple-framebuffer', 'card1': 'etnaviv', 'card2': 'imx-drm'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ['--drm-device=card2', '--config=screen.ini'])

    def test_selects_imx_display_with_original_numbering(self):
        result = self.selector({'card0': 'simple-framebuffer', 'card1': 'imx-drm', 'card2': 'etnaviv'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--drm-device=card1', result.stdout)

    def test_selector_refuses_missing_display(self):
        result = self.selector({'card0': 'simple-framebuffer', 'card1': 'etnaviv'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('No imx-drm', result.stderr)

    def test_selector_refuses_ambiguous_display(self):
        result = self.selector({'card1': 'imx-drm', 'card2': 'imx-drm'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Multiple imx-drm', result.stderr)

    def test_image_check_rejects_missing_display_selector(self):
        self.generate()
        self.renderer('gl-renderer.so')
        (self.root / 'usr/libexec/dd-screen-weston').unlink()
        with self.assertRaisesRegex(ValueError, 'dynamic display selector'):
            verifier.verify_etnaviv_weston(self.root)


if __name__ == '__main__':
    unittest.main()
