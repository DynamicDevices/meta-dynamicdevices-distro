"""Execute the real launcher against a fake Wayland socket and browser."""
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / 'recipes-graphics/dd-kiosk-browser/dd-kiosk-browser/dd-kiosk-browser'


class KioskMutedStartupTests(unittest.TestCase):
    def launch(self, mute=None, compat=None):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            browser = base / 'browser'
            browser.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
            browser.chmod(0o755)
            with socket.socket(socket.AF_UNIX) as wayland:
                wayland.bind(str(base / 'wayland-0'))
                source = LAUNCHER.read_text().replace('runtime_dir=/run/user/$(id -u)', 'runtime_dir=' + directory)
                source = source.replace('/usr/bin/chromium', str(browser))
                env = {k: v for k, v in os.environ.items()
                       if k not in ('DD_KIOSK_MUTE_AUDIO', 'DD_KIOSK_GLES2_COMPAT')}
                env.update(DD_KIOSK_URL='https://active-esl.com', STATE_DIRECTORY=directory)
                if mute is not None:
                    env['DD_KIOSK_MUTE_AUDIO'] = mute
                if compat is not None:
                    env['DD_KIOSK_GLES2_COMPAT'] = compat
                return subprocess.run(['sh', '-eu', '-c', source], env=env,
                                      capture_output=True, text=True, timeout=5)

    def test_mute_is_applied_to_real_browser_argv(self):
        result = self.launch('1')
        self.assertEqual(result.returncode, 0, result.stderr)
        args = json.loads(result.stdout)
        self.assertEqual(args.count('--mute-audio'), 1)
        self.assertIn('--kiosk', args)
        self.assertIn('--ozone-platform=wayland', args)
        self.assertEqual(args[-1], 'https://active-esl.com')
        self.assertNotIn('--disable-gpu', args)
        self.assertNotIn('--no-sandbox', args)

    def test_unset_empty_and_zero_preserve_existing_audio_behavior(self):
        for value in (None, '', '0'):
            with self.subTest(value=value):
                result = self.launch(value)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn('--mute-audio', json.loads(result.stdout))

    def test_invalid_values_fail_before_browser_start(self):
        for value in ('true', '01', '1 --no-sandbox', '$(touch /not-executed)'):
            with self.subTest(value=value):
                result = self.launch(value)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')
                self.assertIn('must be 0 or 1', result.stderr)

    def test_screen_es2_compatibility_preserves_mute_and_sandbox(self):
        result = self.launch('1', '1')
        self.assertEqual(result.returncode, 0, result.stderr)
        args = json.loads(result.stdout)
        self.assertIn('--disable-features=FallbackToSWIfGLES3NotSupported', args)
        self.assertIn('--mute-audio', args)
        self.assertNotIn('--no-sandbox', args)
        self.assertNotIn('--ignore-gpu-blocklist', args)

    def test_es2_compatibility_is_opt_in(self):
        for value in (None, '', '0'):
            with self.subTest(value=value):
                result = self.launch('1', value)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(any('FallbackToSWIfGLES3NotSupported' in a for a in json.loads(result.stdout)))

    def test_invalid_es2_compatibility_fails_before_browser_start(self):
        result = self.launch('1', '1 --no-sandbox')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertIn('DD_KIOSK_GLES2_COMPAT must be 0 or 1', result.stderr)


if __name__ == '__main__':
    unittest.main()
