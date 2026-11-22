"""Check the image acceptance contract with controlled filesystem fixtures."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('kiosk_acceptance', ROOT / 'scripts/verify-kiosk-image.py')
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class KioskAcceptanceTests(unittest.TestCase):
    def test_jaguar_and_custom_startup_urls(self):
        for url in (VERIFY.JAGUAR_START_URL, 'https://example.com/start?a=1&b=2'):
            with self.subTest(url=url), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = root / 'etc/default/dd-kiosk-browser'
                config.parent.mkdir(parents=True)
                config.write_text('DD_KIOSK_URL="' + url + '"\nDD_KIOSK_MUTE_AUDIO=1\n')
                VERIFY.verify_startup_url(root, url)
                with self.assertRaisesRegex(ValueError, 'differs from expected'):
                    VERIFY.verify_startup_url(root, 'https://wrong.example.com')

    def test_url_must_be_present_and_nonempty(self):
        for content in ('# DD_KIOSK_URL=https://example.com\n', 'DD_KIOSK_URL=\n'):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = root / 'etc/default/dd-kiosk-browser'
                config.parent.mkdir(parents=True)
                config.write_text(content)
                with self.assertRaises(ValueError):
                    VERIFY.verify_startup_url(root, VERIFY.JAGUAR_START_URL)

    def test_touch_payload_is_required_in_rootfs_and_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in VERIFY.JAGUAR_TOUCH_FILES:
                self.assertIn(name, VERIFY.ARTIFACT_FILES)
                with self.assertRaisesRegex(ValueError, 'missing Jaguar touch payload'):
                    VERIFY.verify_jaguar_touch(root)
                path = root / name.lstrip('/')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('fixture')
            with self.assertRaisesRegex(ValueError, 'not executable'):
                VERIFY.verify_jaguar_touch(root)
            (root / 'usr/bin/jaguar-touch-test').chmod(0o755)
            VERIFY.verify_jaguar_touch(root)


if __name__ == '__main__':
    unittest.main()
