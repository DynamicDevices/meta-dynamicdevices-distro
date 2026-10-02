#!/usr/bin/env python3
"""Regression tests for the provider-neutral kiosk image verifier."""
import importlib.util
import json
import os
import pathlib
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).with_name('verify-kiosk-image.py')
SPEC = importlib.util.spec_from_file_location('verify_kiosk_image', SCRIPT)
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class KioskVerifierTests(unittest.TestCase):
    def write(self, root, name, content='', executable=False):
        path = root / name.lstrip('/')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        if executable:
            path.chmod(0o755)
        return path

    def make_rootfs(self, root, provider):
        for name in VERIFY.artifact_files(provider):
            self.write(root, name)

        self.write(
            root,
            'usr/lib/systemd/system/dd-kiosk-browser.service',
            '[Unit]\nAfter=weston.service\n'
            '[Service]\nUser=weston\nStateDirectory=dd-kiosk-browser\n'
            'Restart=always\n',
        )
        enabled = root / 'etc/systemd/system/multi-user.target.wants/dd-kiosk-browser.service'
        enabled.parent.mkdir(parents=True, exist_ok=True)
        os.symlink('/usr/lib/systemd/system/dd-kiosk-browser.service', enabled)

        flags = ('--ozone-platform=wayland --kiosk' if provider == 'chromium'
                 else '--platform=wl --webprocess-failure=restart')
        self.write(root, 'usr/bin/dd-kiosk-browser', flags, executable=True)
        self.write(root, 'usr/libexec/dd-kiosk-linker-guard',
                   'kiosk-audio-hotpatch.conf zz-audio-hotpatch.conf '
                   '/sbin/ldconfig /ostree/deploy/', executable=True)
        self.write(
            root,
            'usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzz-native-runtime.conf',
            '[Service]\nUnsetEnvironment=LD_LIBRARY_PATH ALSA_CONFIG_PATH\n',
        )
        self.write(
            root,
            'usr/lib/systemd/system/weston.service.d/zzzz-kiosk-linker-guard.conf',
            '[Service]\nExecStartPre=+/usr/libexec/dd-kiosk-linker-guard\n',
        )
        self.write(
            root,
            'usr/lib/systemd/system/dd-kiosk-browser.service.d/audio.conf',
            '[Unit]\nAfter=pulseaudio.service\n'
            '[Service]\nEnvironment=PULSE_SERVER=unix:/tmp/pulseaudio.socket\n',
        )
        self.write(root, 'etc/asound.conf', 'pcm.!default { card tas2555audio; }\n')
        self.write(root, 'etc/default/dd-kiosk-browser',
                   'DD_KIOSK_URL=https://active-esl.com\n')
        self.write(root, 'etc/xdg/weston/weston-screen.ini',
                   '[core]\nshell=kiosk-shell.so\n[output]\ntransform=rotate-90\n')
        self.write(root, 'etc/systemd/system/weston.service.d/screen.conf',
                   'ExecStart=/usr/bin/weston --config=/etc/xdg/weston/weston-screen.ini\n')
        self.write(root, 'usr/lib/weston/kiosk-shell.so')
        self.write(root, 'etc/NetworkManager/dispatcher.d/90-dd-kiosk-browser',
                   '#!/bin/sh\n', executable=True)
        self.write(root, f'usr/bin/{"chromium" if provider == "chromium" else "cog"}',
                   executable=True)

        if provider == 'chromium':
            policy = {
                'AllowFileSelectionDialogs': False,
                'BrowserAddPersonEnabled': False,
                'BrowserGuestModeEnabled': False,
                'BrowserSignin': 0,
                'DeveloperToolsAvailability': 2,
                'DownloadRestrictions': 3,
                'ExtensionInstallBlocklist': ['*'],
                'IncognitoModeAvailability': 1,
                'PrintingEnabled': False,
                'URLBlocklist': ['view-source:*'],
            }
            self.write(
                root,
                'etc/chromium/policies/managed/dd-kiosk-browser.json',
                json.dumps(policy),
            )

    def test_provider_selection(self):
        self.assertEqual(
            VERIFY.kiosk_provider({'dd-kiosk-browser'}), 'chromium')
        self.assertEqual(VERIFY.kiosk_provider({'dd-kiosk-cog'}), 'cog')
        with self.assertRaises(ValueError):
            VERIFY.kiosk_provider(set())
        with self.assertRaises(ValueError):
            VERIFY.kiosk_provider({'dd-kiosk-browser', 'dd-kiosk-cog'})

    def test_other_browser_stack_is_forbidden(self):
        self.assertEqual(
            VERIFY.forbidden_packages(
                {'dd-kiosk-cog', 'cog', 'chromium-ozone-wayland'}, 'cog'),
            {'chromium-ozone-wayland'},
        )
        self.assertEqual(
            VERIFY.forbidden_packages(
                {'dd-kiosk-browser', 'chromium-ozone-wayland', 'wpewebkit'},
                'chromium',
            ),
            {'wpewebkit'},
        )

    def test_chromium_rootfs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.make_rootfs(root, 'chromium')
            VERIFY.verify_rootfs(root, 'chromium')

    def test_cog_rootfs_without_chromium_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.make_rootfs(root, 'cog')
            self.assertFalse(
                (root / 'etc/chromium/policies/managed/dd-kiosk-browser.json').exists()
            )
            VERIFY.verify_rootfs(root, 'cog')


if __name__ == '__main__':
    unittest.main()
