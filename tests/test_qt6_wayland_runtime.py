"""Source checks only; BitBake/image acceptance belongs on the remote builder."""

import re
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


class QtRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.features = (ROOT / "conf/distro/include/lmp-dynamicdevices-product-features.inc").read_text()

    def test_opt_in_feature_expansion(self):
        self.assertIn('DD_PRODUCT_FEATURES ?= ""', self.features)
        valid = re.search(r'DD_PRODUCT_FEATURES_VALID = "(.*?)"', self.features, re.S)
        self.assertIn("qt6", valid.group(1).split())
        expansion = re.search(r"contains\('DD_PRODUCT_FEATURES', 'qt6', '([^']+)'", self.features)
        self.assertEqual(set(expansion.group(1).split()), {"display-runtime", "qt6", "wayland", "opengl", "alsa"})

    def test_prerequisites_survive_removal(self):
        removal = re.search(r'DISTRO_FEATURES:remove = "(.*?)"', self.features, re.S).group(1)
        expressions = re.findall(r"\$\{@(.*)\}", removal)
        for selection in ("qt6", "qt6 kiosk-browser"):
            data = SimpleNamespace(getVar=lambda name: selection)
            removed = " ".join(eval(expr, {"d": data}) for expr in expressions).split()
            self.assertTrue({"wayland", "opengl", "alsa"}.isdisjoint(removed))
        self.assertIn("x11", removal.split())

    def test_hardware_guard(self):
        guard = re.search(r"display_software = selected & (\{[^}]+\})", self.features)
        self.assertIn("qt6", eval(guard.group(1)))

    def test_image_and_runtime_packages(self):
        image = (ROOT / "recipes-samples/images/lmp-factory-image.bb").read_text()
        self.assertIn("contains('DISTRO_FEATURES', 'qt6', 'recipes-samples/images/lmp-feature-qt.inc', '', d)", image)
        group = (ROOT / "recipes-core/packagegroups/packagegroup-dd-qt6-wayland.bb").read_text()
        packages = re.search(r'RDEPENDS:\$\{PN\} = "(.*?)"', group, re.S).group(1).split()
        self.assertTrue({"qtbase", "qtbase-plugins", "qtwayland", "qtwayland-plugins", "alsa-lib", "util-linux-libuuid", "fontconfig", "liberation-fonts"}.issubset(packages))

    def test_conditional_append_and_no_application_runtime(self):
        layer = (ROOT / "conf/layer.conf").read_text()
        self.assertIn('BBFILES_DYNAMIC += "qt6-layer:', layer)
        append = (ROOT / "dynamic-layers/qt6-layer/recipes-qt/qt6/qtbase_%.bbappend").read_text()
        self.assertIn("PACKAGECONFIG:append:class-target", append)
        self.assertIn(" gui widgets dbus fontconfig", append)
        distro = (ROOT / "conf/distro/lmp-dynamicdevices.conf").read_text()
        self.assertNotRegex(distro, r'GCCVERSION\s*=\s*"14')


if __name__ == "__main__":
    unittest.main()
