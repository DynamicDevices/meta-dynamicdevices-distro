"""Keep hardware audio defaults in the BSP; no local Yocto tasks are run."""

from pathlib import Path
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

    def test_distro_does_not_select_a_hardware_card(self):
        self.assertNotIn("DD_KIOSK_AUDIO_CARD", self.alsa)
        self.assertNotIn("wm8524", self.alsa)
        self.assertNotIn("tas2555", self.alsa)

    def test_other_machine_defaults_are_not_replaced(self):
        self.assertNotIn("do_install", self.alsa)
        self.assertNotIn("pcm.!default", self.alsa)
        self.assertNotIn("ctl.!default", self.alsa)

    def test_machine_arch_and_upstream_ownership_are_preserved(self):
        self.assertIn('PACKAGE_ARCH = "${MACHINE_ARCH}"', self.alsa)
        self.assertNotIn("> ${D}${sysconfdir}/asound.conf", self.alsa)
        self.assertNotRegex(self.alsa, r'(?m)^(?:FILES|CONFFILES|RREPLACES|RCONFLICTS)[: ]')
        self.assertNotIn("force-overwrite", self.alsa + self.kiosk)


if __name__ == "__main__":
    unittest.main()
