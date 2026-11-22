"""Local launcher regression tests; no device, browser or network required."""

import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent
FILES = ROOT / "dd-kiosk-browser"


class KioskStartupTests(unittest.TestCase):
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
        self.assertIn('DD_KIOSK_URL=https://www.youtube.com/watch?v=nfWlot6h_JM&autoplay=1&mute=1&loop=1&playlist=nfWlot6h_JM', defaults)
        self.assertIn('DD_KIOSK_MUTE_AUDIO=1', defaults)


if __name__ == "__main__":
    unittest.main()
