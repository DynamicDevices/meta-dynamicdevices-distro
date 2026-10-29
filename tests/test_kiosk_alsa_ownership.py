"""Source-contract and rendering fixtures; no local Yocto tasks are run."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
KIOSK = ROOT / "recipes-graphics/dd-kiosk-browser/dd-kiosk-browser_1.0.bb"
ALSA = ROOT / "recipes-bsp/alsa-state/alsa-state.bbappend"


class KioskALSAOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.kiosk = KIOSK.read_text()
        self.alsa = ALSA.read_text()

    def test_kiosk_no_longer_installs_or_packages_asound(self):
        self.assertNotIn("${sysconfdir}/asound.conf", self.kiosk)
        self.assertNotIn("DD_KIOSK_AUDIO_CARD", self.kiosk)

    def test_screen_runtime_requires_the_single_owner(self):
        self.assertIn(
            'RDEPENDS:${PN}:append:imx8mm-jaguar-screen = " alsa-state"',
            self.kiosk,
        )

    def test_screen_audio_defaults_are_byte_identical(self):
        card = re.search(
            r'^DD_KIOSK_AUDIO_CARD:imx8mm-jaguar-screen = "([^"]+)"$',
            self.alsa, re.MULTILINE,
        ).group(1)
        templates = re.findall(r"^\s*'((?:pcm|ctl)\.!default[^']*)'", self.alsa, re.MULTILINE)
        rendered = "".join(
            line.replace("${DD_KIOSK_AUDIO_CARD}", card) + "\n"
            for line in templates
        )
        self.assertEqual(
            rendered,
            "pcm.!default { type hw; card wm8524audio; device 0; }\n"
            "ctl.!default { type hw; card wm8524audio; }\n",
        )

    def test_other_machine_defaults_are_not_replaced(self):
        self.assertIn('DD_KIOSK_AUDIO_CARD ?= ""', self.alsa)
        self.assertIn('if [ -n "${DD_KIOSK_AUDIO_CARD}" ]; then', self.alsa)
        overrides = re.findall(r'^DD_KIOSK_AUDIO_CARD:([^ ]+) =', self.alsa, re.MULTILINE)
        self.assertEqual(overrides, ["imx8mm-jaguar-screen"])

    def test_machine_arch_and_upstream_ownership_are_preserved(self):
        self.assertIn('PACKAGE_ARCH = "${MACHINE_ARCH}"', self.alsa)
        self.assertIn('do_install:append() {', self.alsa)
        self.assertIn('> ${D}${sysconfdir}/asound.conf', self.alsa)
        self.assertNotRegex(self.alsa, r'(?m)^(?:FILES|CONFFILES|RREPLACES|RCONFLICTS)[: ]')
        self.assertNotIn("force-overwrite", self.alsa + self.kiosk)


if __name__ == "__main__":
    unittest.main()
