#!/usr/bin/env python3
"""Native source/recipe fixtures; not a substitute for BitBake or TV tests."""
import configparser
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import types
import unittest
from pathlib import Path

from PIL import Image, ImageChops

DISTRO = Path(__file__).resolve().parents[1]
BSP = Path(os.environ.get("BSP_ROOT", DISTRO.parent / "meta-dynamicdevices-bsp"))
SESSION = DISTRO / "recipes-graphics/aesl-display-session"
FILES = SESSION / "files"
ART = BSP / "recipes-bsp/dt510-hdmi-splash/files"
LINUX_ART = BSP / "recipes-graphics/aesl-display-splash/files/make-linux-splash.py"


class Data:
    def __init__(self, **values):
        self.values = values

    def getVar(self, key):
        return self.values.get(key, "")

    def setVar(self, key, value):
        self.values[key] = value


def contains(variable, expected, yes, no, data):
    return yes if set(expected.split()) <= set(data.getVar(variable).split()) else no


def expression(text, variable, data):
    match = re.search(r'^' + re.escape(variable) + r' \?= "\$\{@(.*)\}"$', text, re.M)
    return eval(match[1], {"bb": types.SimpleNamespace(utils=types.SimpleNamespace(contains=contains)), "d": data})


class DisplaySplashTest(unittest.TestCase):
    def test_default_is_explicit_interactive_capability_not_evk_screen(self):
        contract = (DISTRO / "conf/distro/include/lmp-dynamicdevices-product-features.inc").read_text()
        for hardware, expected in [("display-multimedia", "display"), ("screen", ""), ("wifi bluetooth", "")]:
            with self.subTest(hardware=hardware):
                self.assertEqual(expression(contract, "DD_PRODUCT_FEATURES", Data(MACHINE_FEATURES=hardware)), expected)
        for machine in ("imx8mm-jaguar-dt510", "imx8mm-jaguar-screen"):
            conf = (BSP / f"conf/machine/{machine}.conf").read_text()
            self.assertIn(f'MACHINE_FEATURES:append:{machine} = " display-multimedia"', conf)
        eink = (BSP / "conf/machine/imx93-jaguar-eink.conf").read_text()
        self.assertNotIn("display-multimedia", eink)

    def test_splash_opt_out_and_headless_exclusion(self):
        contract = (DISTRO / "conf/distro/include/lmp-dynamicdevices-product-features.inc").read_text()
        # The expression contains a set literal, so extract through the closing quote.
        expr = re.search(r"\$\{@('display-boot-splash' if .*?)\} \\", contract)[1]
        for features, enabled, expected in [("display alsa", "1", "display-boot-splash"), ("flutter", "1", "display-boot-splash"), ("alsa usb-gadget", "1", ""), ("display", "0", "")]:
            self.assertEqual(eval(expr, {"d": Data(DD_PRODUCT_FEATURES=features, DD_DISPLAY_BOOT_SPLASH=enabled)}), expected)
        image = (DISTRO / "recipes-samples/images/lmp-factory-image.bb").read_text()
        self.assertIn("contains('DISTRO_FEATURES', 'display-boot-splash'", image)

    def test_boot_arguments_keep_serial_root_and_ota(self):
        text = (DISTRO / "recipes-samples/images/lmp-feature-display-boot-splash.inc").read_text()
        remove = re.search(r'OSTREE_KERNEL_ARGS:remove = "\$\{@(.*)\}"', text)[1]
        removed = set(eval(remove).split())
        args = "console=tty0 console=ttymxc1,115200 root=LABEL=otaroot rootfstype=ext4 ostree=/ostree/boot.1/lmp/example/0".split()
        actual = [arg for arg in args if arg not in removed]
        self.assertEqual(actual, args[1:])
        self.assertNotRegex(text, r"(?:loglevel=| quiet|fw_setenv|mmcblk)")
        self.assertIn("video=HDMI-A-1:1280x720@60e", text)

    def test_actual_psplash_prepend_runs_and_preserves_default_package(self):
        append = (BSP / "recipes-core/psplash/psplash_%.bbappend").read_text()
        body = re.search(r"python do_compile:prepend\(\) \{\n(.*?)\n\}", append, re.S)[1]
        compile_task = compile("def task(d):\n" + textwrap.indent(textwrap.dedent(body), "    ") + "\n    d.setVar('UPSTREAM_RAN', True)\n", "psplash-compile-fixture", "exec")
        env = {"bb": types.SimpleNamespace(utils=types.SimpleNamespace(contains=contains))}
        exec(compile_task, env)
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            for source in (ART / "make-splash.py", ART / "active-edge-splash-1920x1200.png", LINUX_ART):
                shutil.copy(source, work)
            for selected in (False, True):
                data = Data(WORKDIR=temp, PYTHON=sys.executable, MACHINE="imx8mm-jaguar-dt510", DISTRO_FEATURES="display-boot-splash" if selected else "systemd", SPLASH_LOCALPATHS="lmp-logo.png", SPLASH_INSTALL="psplash-default")
                env["task"](data)
                self.assertTrue(data.getVar("UPSTREAM_RAN"))
                self.assertEqual(data.getVar("SPLASH_INSTALL"), "psplash-default")
                self.assertEqual(data.getVar("SPLASH_LOCALPATHS"), "aesl-splash.png" if selected else "lmp-logo.png")
            with Image.open(work / "aesl-desktop.bmp") as bitmap:
                with Image.open(work / "aesl-splash.png") as image:
                    self.assertIsNone(ImageChops.difference(bitmap.convert("RGB"), image.convert("RGB")).getbbox())
            self.assertEqual(hashlib.sha256((work / "aesl-desktop.bmp").read_bytes()).hexdigest(), "64b2f36f6305a8012d9dbab4ec2a266aba9f023bb4f4294eb30754dd37573da3")

    def test_screen_rotation_and_shared_desktop_pixels(self):
        spec = importlib.util.spec_from_file_location("linux_art", LINUX_ART)
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)
        with tempfile.TemporaryDirectory() as temp:
            desktop, fb = Path(temp) / "desktop.png", Path(temp) / "fb.png"
            renderer.render("imx8mm-jaguar-screen", ART / "active-edge-splash-1920x1200.png", desktop, fb)
            with Image.open(desktop) as image, Image.open(fb) as rotated:
                self.assertEqual(image.size, (1920, 1200))
                self.assertEqual(rotated.size, (1200, 1920))
                self.assertIsNone(ImageChops.difference(image.transpose(Image.Transpose.ROTATE_90), rotated).getbbox())
        screen = (DISTRO / "recipes-samples/images/lmp-feature-display-multimedia.inc").read_text()
        self.assertIn("transform=rotate-90", screen)
        self.assertIn("--use-g2d", screen)
        self.assertIn("--debug', '', d)", screen)
        self.assertIn("/usr/share/aesl-display-splash/splash.png", screen)

    def test_service_graph_and_nonfatal_splash(self):
        psplash = (FILES / "psplash-start.conf").read_text()
        weston = (FILES / "weston-splash.conf").read_text()
        quit_unit = (FILES / "aesl-splash-quit.service").read_text()
        self.assertIn("--no-console-switch", psplash)
        self.assertIn("TimeoutStartSec=15s", psplash)
        self.assertIn("Wants=psplash-start.service", weston)
        self.assertNotIn("Requires=psplash", weston)
        self.assertIn("After=psplash-start.service", weston)
        self.assertIn("$OPTARGS", weston)
        self.assertIn("--modules=systemd-notify.so", weston)
        self.assertIn("After=weston.service psplash-start.service", quit_unit)
        self.assertIn("ExecStart=-/usr/bin/psplash-write QUIT", quit_unit)
        self.assertIn("WantedBy=weston.service", quit_unit)
        self.assertIn("ConditionPathExists=!", (FILES / "psplash-progress.conf").read_text())
        recipe = (SESSION / "aesl-display-session_1.0.bb").read_text()
        self.assertIn("TAG+=\"systemd\"", recipe)
        self.assertNotIn("serial-getty@.service.d", recipe)
        self.assertIn("ConditionPathExists=/etc/aesl-enable-display-getty", (FILES / "no-vt-getty.conf").read_text())

    def test_mode_policy_is_dt510_only(self):
        generic = configparser.ConfigParser()
        generic.read(FILES / "weston-aesl.ini")
        self.assertFalse(generic.has_section("output"))
        dt510 = configparser.ConfigParser()
        dt510.read(SESSION / "aesl-display-session/imx8mm-jaguar-dt510/weston-aesl.ini")
        self.assertEqual(dt510["output"]["name"], "HDMI-A-1")
        self.assertEqual(dt510["output"]["mode"], "1280x720")
        self.assertEqual(dt510["shell"]["background-image"], generic["shell"]["background-image"])

    def test_recipe_installs_dropins_and_device_tag(self):
        recipe = (SESSION / "aesl-display-session_1.0.bb").read_text()
        body = re.search(r"\ndo_install\(\) \{\n(.*?)\n\}", recipe, re.S)[1]
        with tempfile.TemporaryDirectory() as temp:
            for key, value in {"D": temp, "WORKDIR": str(FILES), "systemd_system_unitdir": "/usr/lib/systemd/system", "sysconfdir": "/etc", "libdir": "/usr/lib"}.items():
                body = body.replace("${" + key + "}", value)
            self.assertNotIn("${", body)
            subprocess.run(["sh", "-eu", "-c", body], check=True)
            root = Path(temp)
            for unit in ("psplash-start", "psplash-systemd", "weston", "getty@"):
                self.assertTrue(any((root / f"usr/lib/systemd/system/{unit}.service.d").glob("*.conf")))
            self.assertIn('TAG+="systemd"', (root / "etc/udev/rules.d/71-aesl-splash.rules").read_text())
            self.assertIn("weston weston", (root / "usr/lib/tmpfiles.d/aesl-weston.conf").read_text())


if __name__ == "__main__":
    unittest.main()
