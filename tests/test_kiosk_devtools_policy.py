"""Exercise the recipe's DEV_MODE policy fragment without running BitBake."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / 'recipes-graphics/dd-kiosk-browser/dd-kiosk-browser_1.0.bb'
POLICY = ROOT / 'recipes-graphics/dd-kiosk-browser/dd-kiosk-browser/kiosk-policy.json'


class DeveloperToolsPolicyTest(unittest.TestCase):
    def test_only_exact_dev_mode_enables_tools(self):
        original_bytes = POLICY.read_bytes()
        original = json.loads(original_bytes)
        self.assertEqual(original['DeveloperToolsAvailability'], 2)
        recipe = RECIPE.read_text()
        install_body = recipe.split('do_install() {', 1)[1].split('\n}', 1)[0]
        match = re.search(r'    if \[ "\$\{DEV_MODE\}" = "1" \]; then\n.*?\n    fi', install_body, re.S)
        self.assertIsNotNone(match, 'DEV_MODE gate must be in the installation path')
        fragment = match.group(0)
        self.assertIn('install -m 0644 ${WORKDIR}/kiosk-policy.json', install_body[:match.start()])
        for mode in ('1', '0', '', 'true', '01', 'production'):
            with self.subTest(DEV_MODE=mode), tempfile.TemporaryDirectory() as directory:
                destination = Path(directory) / 'etc/chromium/policies/managed/dd-kiosk-browser.json'
                destination.parent.mkdir(parents=True)
                destination.write_bytes(original_bytes)
                rendered = fragment.replace('${DEV_MODE}', mode).replace('${D}', directory).replace('${sysconfdir}', '/etc')
                subprocess.run(['sh', '-eu', '-c', rendered], check=True, capture_output=True)
                actual = json.loads(destination.read_text())
                expected = dict(original, DeveloperToolsAvailability=1 if mode == '1' else 2)
                self.assertEqual(actual, expected, 'No other policy may change')
                if mode != '1':
                    self.assertEqual(destination.read_bytes(), original_bytes)


if __name__ == '__main__':
    unittest.main()
