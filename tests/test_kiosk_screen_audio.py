"""Screen-only PulseAudio routing; these are source checks, not Yocto tasks."""
from configparser import ConfigParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "recipes-graphics/dd-kiosk-browser/dd-kiosk-browser_1.0.bb"
FILES = RECIPE.parent / "dd-kiosk-browser"
DROPIN = "dd-kiosk-browser-screen-audio.conf"


class ScreenAudioRoutingTests(unittest.TestCase):
    def test_dropin_selects_only_the_existing_speaker_sink(self):
        parser = ConfigParser(interpolation=None)
        parser.optionxform = str
        parser.read(FILES / DROPIN)
        self.assertEqual(parser.sections(), ["Service"])
        self.assertEqual(dict(parser["Service"]), {
            "Environment": "PULSE_SINK=alsa_output.platform-sound-tas2555.stereo-fallback",
        })

    def test_dropin_is_fetched_only_for_screen_with_pulseaudio(self):
        recipe = RECIPE.read_text()
        lines = [line for line in recipe.splitlines() if "file://" + DROPIN in line]
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("SRC_URI:append:imx8mm-jaguar-screen = "))
        self.assertIn("bb.utils.contains('DISTRO_FEATURES', 'pulseaudio'", lines[0])

    def test_install_and_package_are_machine_scoped(self):
        recipe = RECIPE.read_text()
        body = re.search(r"do_install:append:imx8mm-jaguar-screen\(\) \{\n(.*?)\n\}",
                         recipe, re.S).group(1)
        self.assertIn("bb.utils.contains('DISTRO_FEATURES', 'pulseaudio'", body)
        self.assertIn("${WORKDIR}/" + DROPIN, body)
        self.assertIn("dd-kiosk-browser.service.d/screen-audio.conf", body)
        packages = [line for line in recipe.splitlines()
                    if line.startswith("FILES:") and "screen-audio.conf" in line]
        self.assertEqual(len(packages), 1)
        self.assertTrue(packages[0].startswith("FILES:${PN}:append:imx8mm-jaguar-screen = "))

    def test_generic_audio_and_launcher_do_not_gain_a_sink_override(self):
        self.assertNotIn("PULSE_SINK", (FILES / "dd-kiosk-browser-audio.conf").read_text())
        self.assertNotIn("PULSE_SINK", (FILES / "dd-kiosk-browser").read_text())
        self.assertNotIn("PULSE_SINK", (FILES / "dd-kiosk-browser.env").read_text())


if __name__ == "__main__":
    unittest.main()
