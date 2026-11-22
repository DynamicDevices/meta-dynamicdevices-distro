"""Local launcher regression tests; no device, browser or network required."""

import os
import importlib.util
import re
import shlex
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent
FILES = ROOT / "dd-kiosk-browser"


class KioskStartupTests(unittest.TestCase):
    def test_touch_recipe_preserves_configured_browser_paths(self):
        recipe = (ROOT.parent / 'jaguar-touch-test/jaguar-touch-test_1.0.bb').read_text()
        helper = recipe[recipe.index('def jaguar_browser_replacement(d):'):recipe.index('\ndo_install()')]
        namespace = {}
        exec(helper, namespace)
        spec = importlib.util.spec_from_file_location('verify_kiosk_image', ROOT.parents[1] / 'scripts/verify-kiosk-image.py')
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        install = recipe.split('do_install() {\n', 1)[1].split('\n}', 1)[0]
        with tempfile.TemporaryDirectory(prefix='touch-recipe-') as directory:
            work = Path(directory)
            source = ROOT.parent / 'jaguar-touch-test/jaguar-touch-test'
            for name in ('browser', 'browser&one|two', 'browser\\name',
                         'browser "quoted" $dollar `tick`', "browser's }brace"):
                with self.subTest(name=name):
                    browser = work / name
                    browser.write_text('#!/bin/sh\nprintf "exact browser reached\\n"\n')
                    browser.chmod(0o755)
                    data = type('Data', (), {'getVar': lambda self, key: str(browser)})()
                    command = install.replace('${@jaguar_browser_replacement(d)}',
                                              namespace['jaguar_browser_replacement'](data))
                    for key, value in {'D': str(work / 'image'), 'datadir': '/usr/share',
                                       'bindir': '/usr/bin', 'WORKDIR': str(source)}.items():
                        command = command.replace('${' + key + '}', value)
                    rendered = subprocess.run(['/bin/sh', '-ec', command],
                                              capture_output=True, text=True, timeout=5)
                    self.assertEqual(rendered.returncode, 0, rendered.stderr)
                    result = subprocess.run(['/bin/sh', str(work / 'image/usr/bin/jaguar-touch-test')],
                                            env={'PATH': os.defpath}, capture_output=True,
                                            text=True, timeout=5)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, 'exact browser reached\n')
                    payload = {
                        '/usr/bin/jaguar-touch-test': work / 'image/usr/bin/jaguar-touch-test',
                        verifier.JAGUAR_TOUCH_FILES[0]: ROOT.parent / 'jaguar-screen-touch/jaguar-screen-touch/99-jaguar-screen-touch.rules',
                    }
                    verifier.verify_touch_policy(payload.__getitem__, lambda path: path.read_text())

    def launch(self, **settings):
        with tempfile.TemporaryDirectory(prefix="kiosk-startup-") as directory:
            runtime = Path(directory)
            with socket.socket(socket.AF_UNIX) as wayland:
                wayland.bind(str(runtime / "wayland-1"))
                source = (FILES / "dd-kiosk-browser").read_text()
                source = source.replace(
                    'runtime_dir=/run/user/$(id -u)',
                    'runtime_dir="${TEST_RUNTIME_DIR}"',
                )
                browser = runtime / "chromium"
                browser.write_text('#!/bin/sh\nprintf \'%s\\n\' /usr/bin/chromium "$@"\n')
                browser.chmod(0o755)
                source = source.replace('/usr/bin/chromium', str(browser))
                launcher = runtime / "launcher"
                launcher.write_text(source)
                # Substitute only the executable and runtime directory, retaining
                # the real validation, socket selection and argument quoting.
                env = {"PATH": os.defpath, "TEST_RUNTIME_DIR": directory}
                env.update(settings)
                return subprocess.run(
                    ["/bin/sh", str(launcher)],
                    env=env, text=True, capture_output=True, timeout=5,
                )

    def test_silent_youtube_autoplay_and_loop_preserve_one_url_argument(self):
        url = "https://www.youtube.com/watch?v=nfWlot6h_JM&autoplay=1&mute=1&loop=1&playlist=nfWlot6h_JM"
        result = self.launch(DD_KIOSK_URL=url, DD_KIOSK_MUTE_AUDIO="1",
                             DD_KIOSK_GLES2_COMPAT="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = result.stdout.splitlines()
        self.assertEqual(args[0], "/usr/bin/chromium")
        self.assertEqual(args[-1], url)
        self.assertIn("--mute-audio", args)
        self.assertIn("--disable-features=FallbackToSWIfGLES3NotSupported", args)
        self.assertIn("--kiosk", args)
        self.assertNotIn("--no-sandbox", args)
        self.assertFalse(any("autoplay-policy" in arg for arg in args))

    def test_other_hardware_does_not_inherit_gles2_or_mute_flags(self):
        result = self.launch(DD_KIOSK_URL="https://example.com")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("--mute-audio", result.stdout)
        self.assertNotIn("--disable-features", result.stdout)

    def test_custom_and_offline_urls(self):
        for settings, expected in [
            ({"DD_KIOSK_URL": "https://example.com/start?a=1&b=2"},
             "https://example.com/start?a=1&b=2"),
            ({}, "file:///usr/share/dd-kiosk-browser/offline.html"),
        ]:
            with self.subTest(settings=settings):
                result = self.launch(**settings)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines()[-1], expected)

    def test_invalid_options_fail_before_browser_launch(self):
        for key in ("DD_KIOSK_MUTE_AUDIO", "DD_KIOSK_GLES2_COMPAT"):
            with self.subTest(key=key):
                result = self.launch(**{key: "invalid"})
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(key, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_invalid_urls_fail_before_browser_launch(self):
        for url in ("javascript:alert(1)", "https://", "https://bad host/"):
            with self.subTest(url=url):
                result = self.launch(DD_KIOSK_URL=url)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("DD_KIOSK_URL", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_recipe_enables_boot_and_installs_editable_configuration(self):
        recipe = (ROOT / "dd-kiosk-browser_1.0.bb").read_text()
        service = (FILES / "dd-kiosk-browser.service").read_text()
        defaults = (FILES / "dd-kiosk-browser.env").read_text()
        self.assertIn('SYSTEMD_AUTO_ENABLE:${PN} = "enable"', recipe)
        self.assertIn('CONFFILES:${PN} = "${sysconfdir}/default/dd-kiosk-browser', recipe)
        self.assertIn('DD_KIOSK_GLES2_COMPAT:imx8mm-jaguar-screen = "1"', recipe)
        self.assertIn('DD_KIOSK_GLES2_COMPAT=${DD_KIOSK_GLES2_COMPAT}', recipe)
        self.assertIn('EnvironmentFile=-/etc/default/dd-kiosk-browser', service)
        self.assertIn('WantedBy=multi-user.target', service)
        self.assertIn('DD_KIOSK_START_URL:imx8mm-jaguar-screen = "https://www.youtube.com/watch?v=nfWlot6h_JM&autoplay=1&mute=1&loop=1&playlist=nfWlot6h_JM"', recipe)
        self.assertIn('DD_KIOSK_URL=https://active-esl.com', defaults)
        self.assertIn('DD_KIOSK_MUTE_AUDIO=0', defaults)

    def test_installed_defaults_are_machine_scoped_and_preserve_ampersands(self):
        recipe = (ROOT / "dd-kiosk-browser_1.0.bb").read_text()
        # Execute the real recipe's URL/mute/GLES2 rendering block, not a duplicate
        # Python implementation of sed's replacement/escaping behaviour.
        block = re.search(r'(?m)^    dd_kiosk_start_url=.*\n(?:    sed -i .*\n){3}', recipe)[0]
        helper = recipe[recipe.index('def dd_kiosk_start_url_shell(d):'):recipe.index('\ndo_install()')]
        namespace = {}
        exec(helper, namespace)
        spec = importlib.util.spec_from_file_location('verify_kiosk_image', ROOT.parents[1] / 'scripts/verify-kiosk-image.py')
        verifier = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(verifier)
        for machine, override_url in (
                ('imx8mm-jaguar-screen', None), ('another-machine', None),
                ('imx8mm-jaguar-screen', "https://example.com/it's?a=1&b=2"),
                ('another-machine', "https://example.com/it's?literal=$(false)&q='"),
                ('imx8mm-jaguar-screen', 'https://example.com/quote"?pipe=|&slash=\\')):
            def setting(name):
                override = re.search(r'^' + name + ':' + machine + r' = "([^"]+)"', recipe, re.M)
                return override[1] if override else re.search(r'^' + name + r' \?= "([^"]+)"', recipe, re.M)[1]
            url, mute = setting('DD_KIOSK_START_URL'), setting('DD_KIOSK_START_MUTED')
            url = override_url or url
            gles2 = setting('DD_KIOSK_GLES2_COMPAT')
            with self.subTest(machine=machine, url=url), tempfile.TemporaryDirectory() as directory:
                installed = Path(directory) / 'etc/default/dd-kiosk-browser'
                installed.parent.mkdir(parents=True)
                installed.write_text((FILES / 'dd-kiosk-browser.env').read_text())
                data = type('Data', (), {'getVar': lambda self, key: url})()
                script = block.replace('${@dd_kiosk_start_url_shell(d)}', namespace['dd_kiosk_start_url_shell'](data))
                script = script.replace('${DD_KIOSK_START_MUTED}', mute)
                script = script.replace('${DD_KIOSK_GLES2_COMPAT}', gles2)
                script = script.replace('${D}', directory).replace('${sysconfdir}', '/etc')
                result = subprocess.run(['/bin/sh', '-ec', script], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                environment = dict(line.split('=', 1) for line in installed.read_text().splitlines()
                                   if line and not line.startswith('#'))
                environment['DD_KIOSK_URL'] = shlex.split(environment['DD_KIOSK_URL'])[0]
                self.assertEqual(environment['DD_KIOSK_URL'], url)
                self.assertEqual(environment['DD_KIOSK_MUTE_AUDIO'], mute)
                self.assertEqual(environment['DD_KIOSK_GLES2_COMPAT'], gles2)
                if machine == 'imx8mm-jaguar-screen':
                    verifier.verify_startup_environment(installed.read_text(), url)
                if override_url:
                    self.assertEqual(environment['DD_KIOSK_URL'], override_url)
                    continue
                if machine == 'imx8mm-jaguar-screen':
                    self.assertIn('&loop=1&playlist=nfWlot6h_JM', url)
                    self.assertEqual(mute, '1')
                    self.assertEqual(gles2, '1')
                else:
                    self.assertEqual((url, mute), ('https://active-esl.com', '0'))
                    self.assertEqual(gles2, '0')

    def test_recipe_rejects_multiline_start_urls(self):
        recipe = (ROOT / 'dd-kiosk-browser_1.0.bb').read_text()
        helper = recipe[recipe.index('def dd_kiosk_start_url_shell(d):'):recipe.index('\ndo_install()')]
        namespace = {}
        exec(helper, namespace)
        for url in ('', 'https://example.com/\nnext', 'https://example.com/\rnext',
                    'https://example.com/\x00next'):
            with self.subTest(url=url):
                data = type('Data', (), {'getVar': lambda self, key: url})()
                with self.assertRaisesRegex(ValueError, 'single-line URL'):
                    namespace['dd_kiosk_start_url_shell'](data)


if __name__ == "__main__":
    unittest.main()
