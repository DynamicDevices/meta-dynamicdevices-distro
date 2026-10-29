"""Graphics selection fixtures, not a substitute for a BSP build or panel test."""

from pathlib import Path
import re
import subprocess
import tempfile
import types
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "conf/distro/include/lmp-dynamicdevices-product-features.inc"
WESTON = ROOT / "recipes-graphics/wayland/weston_%.bbappend"
DISPLAY = ROOT / "recipes-samples/images/lmp-feature-display-multimedia.inc"


class Data:
    def __init__(self, **values):
        self.values = values

    def getVar(self, name):
        return self.values.get(name, "")


class G2DSelectionTests(unittest.TestCase):
    def setUp(self):
        self.contract = CONTRACT.read_text()

    def backend(self, machine):
        default = re.search(r'^DD_KIOSK_GRAPHICS_BACKEND \?= "([^"]+)"', self.contract, re.M)[1]
        override = re.search(
            rf'^DD_KIOSK_GRAPHICS_BACKEND:{re.escape(machine)} = "([^"]+)"',
            self.contract, re.M,
        )
        return override[1] if override else default

    def overrides(self, features, machine):
        expression = re.search(r'^OVERRIDES:append = "\$\{@(.+)\}"$', self.contract, re.M)[1]
        return eval(expression, {}, {"d": Data(
            DD_PRODUCT_FEATURES=features,
            DD_KIOSK_GRAPHICS_BACKEND=self.backend(machine),
        )})

    def test_screen_selects_nxp_and_not_mesa(self):
        self.assertEqual(self.backend("imx8mm-jaguar-screen"), "imxg2d")
        active = self.overrides("kiosk-browser audio", "imx8mm-jaguar-screen")
        self.assertEqual(active, ":ddkioskbrowser:dd-graphics-imxg2d")
        self.assertNotIn("dd-graphics-etnaviv", active)
        self.assertIn('DISTRO_FEATURES:remove:dd-graphics-imxg2d = "etnaviv"', self.contract)

    def test_other_kiosk_machines_keep_existing_backend(self):
        self.assertEqual(self.overrides("kiosk-browser", "another-display"),
                         ":ddkioskbrowser:dd-graphics-etnaviv")

    def test_non_kiosk_products_get_no_graphics_override(self):
        for features in ("", "display flutter audio", "android-container"):
            self.assertEqual(self.overrides(features, "imx8mm-jaguar-screen"), "")

    def test_weston_enables_nxp_renderer_for_selected_backend(self):
        weston = WESTON.read_text()
        self.assertIn('PACKAGECONFIG_G2D:dd-graphics-imxg2d = "imxg2d"', weston)
        self.assertIn('PACKAGECONFIG:remove:dd-graphics-etnaviv = "imxg2d"', weston)
        self.assertNotIn('PACKAGECONFIG:remove:dd-graphics-imxg2d', weston)

    def test_install_fails_if_required_renderer_was_not_built(self):
        weston = WESTON.read_text()
        self.assertIn("do_install:append:dd-graphics-imxg2d()", weston)
        self.assertIn("${D}${libdir}/libweston-${WESTON_MAJOR_VERSION}/g2d-renderer.so", weston)
        self.assertIn('bbfatal "Screen G2D graphics backend selected', weston)

    def run_install_guard(self, present):
        body = re.search(r'do_install:append:dd-graphics-imxg2d\(\) \{\n(.*?)^\}',
                         WESTON.read_text(), re.M | re.S)[1]
        with tempfile.TemporaryDirectory() as directory:
            renderer = Path(directory) / "usr/lib/libweston-12/g2d-renderer.so"
            if present:
                renderer.parent.mkdir(parents=True)
                renderer.touch()
            body = body.replace("${D}", directory).replace("${libdir}", "/usr/lib")
            body = body.replace("${WESTON_MAJOR_VERSION}", "12")
            return subprocess.run(
                ["sh", "-c", 'set -eu\nbbfatal() { echo "$*" >&2; return 1; }\n' + body],
                capture_output=True, text=True, check=False,
            )

    def test_install_guard_rejects_a_gl_only_weston(self):
        result = self.run_install_guard(False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("G2D renderer is missing", result.stderr)

    def test_install_guard_accepts_installed_g2d_renderer(self):
        self.assertEqual(self.run_install_guard(True).returncode, 0)

    def test_mesa_provider_overrides_remain_backend_scoped(self):
        providers = re.findall(r'^(PREFERRED_PROVIDER_[^=]+)= "mesa-gl"', self.contract, re.M)
        self.assertTrue(providers)
        self.assertTrue(all(':dd-graphics-etnaviv ' in p for p in providers))
        for path in (ROOT / "recipes-graphics/mesa").glob("*.bbappend"):
            for line in path.read_text().splitlines():
                if re.match(r'^(?:PACKAGECONFIG|PROVIDES|DEPENDS|RRECOMMENDS).*=', line):
                    self.assertIn(":dd-graphics-etnaviv", line)

    def test_screen_launcher_keeps_required_g2d_and_debug_guard(self):
        display = DISPLAY.read_text()
        self.assertIn("'use-g2d=false', 'use-g2d=true'", display)
        self.assertIn("'etnaviv', '', '--use-g2d'", display)
        self.assertIn("'debug-tweaks', '--debug', ''", display)

    def test_unknown_backend_fails_configuration(self):
        handler = re.search(r'python dd_validate_product_features\(\) \{\n(.*?)^\}',
                            self.contract, re.M | re.S)[1]
        def fatal(message):
            raise ValueError(message)
        context = {"e": types.SimpleNamespace(data=Data(
            DD_PRODUCT_FEATURES="kiosk-browser", DD_KIOSK_GRAPHICS_BACKEND="typo")),
            "bb": types.SimpleNamespace(fatal=fatal)}
        with self.assertRaisesRegex(ValueError, "Unknown DD_KIOSK_GRAPHICS_BACKEND"):
            exec("if True:\n" + handler, context)


if __name__ == "__main__":
    unittest.main()
