#!/usr/bin/env python3
"""Exercise the actual install-time DEV_MODE policy block without BitBake."""

import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DevtoolsPolicyTests(unittest.TestCase):
    def test_only_exact_dev_mode_enables_developer_tools(self):
        recipe = (ROOT / "recipes-graphics/dd-kiosk-browser/dd-kiosk-browser_1.0.bb").read_text()
        source = ROOT / "recipes-graphics/dd-kiosk-browser/dd-kiosk-browser/kiosk-policy.json"
        # Match the complete real shell conditional, rather than reimplementing it.
        block = re.search(r'    if \[ "\$\{DEV_MODE\}" = "1" \]; then\n.*?\n    fi', recipe, re.S).group(0)
        for mode in ("", "0", "1", "01", "true", "2"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / "etc/chromium/policies/managed/dd-kiosk-browser.json"
                target.parent.mkdir(parents=True)
                original = json.loads(source.read_text())
                self.assertEqual(original["DeveloperToolsAvailability"], 2)
                target.write_text(source.read_text())
                command = block.replace("${DEV_MODE}", mode).replace("${D}", directory).replace("${sysconfdir}", "/etc")
                subprocess.run(["sh", "-eu", "-c", command], check=True)
                expected = dict(original, DeveloperToolsAvailability=1 if mode == "1" else 2)
                self.assertEqual(json.loads(target.read_text()), expected)


if __name__ == "__main__":
    unittest.main()
