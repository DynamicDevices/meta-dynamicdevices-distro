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
    def test_factory_legacy_entry_routes_display_to_real_headed_distro(self):
        entry = (DISTRO / "conf/distro/lmp-dynamicdevices-headless.conf").read_text()
        expr = re.search(r'DD_LEGACY_DISTRO_PROFILE = "\$\{@(.*)\}"', entry)[1]
        env = {"bb": types.SimpleNamespace(utils=types.SimpleNamespace(contains=contains))}
        for machine, hardware, profile in [("imx8mm-jaguar-dt510", "display-multimedia", "display"), ("imx8mm-jaguar-screen", "display-multimedia", "display"), ("imx93-jaguar-eink", "screen", "headless"), ("imx8mm-jaguar-sentai", "wifi", "headless")]:
            with self.subTest(machine=machine):
                env["d"] = Data(MACHINE=machine, MACHINE_FEATURES=hardware)
                self.assertEqual(eval(expr, env), profile)
                target = re.search(r"^require (.+)$", entry, re.M)[1].replace("${DD_LEGACY_DISTRO_PROFILE}", profile)
                policy = (DISTRO / target).read_text()
                if profile == "display":
                    self.assertIn("require conf/distro/lmp-dynamicdevices.conf", policy)
                    headed = (DISTRO / "conf/distro/lmp-dynamicdevices.conf").read_text()
                    self.assertIn('DISTRO = "lmp-dynamicdevices"', headed)
                    self.assertIn("require conf/distro/include/lmp-dynamicdevices-product-features.inc", headed)
                    self.assertIn('PREFERRED_VERSION_u-boot-fio = "2024.04%"', policy)
                    self.assertIn('PREFERRED_VERSION_u-boot-fio-imx = "2024.04%"', policy)
                else:
                    self.assertIn('DISTRO = "lmp-dynamicdevices-headless"', policy)

    def test_non_display_legacy_policy_is_byte_preserved(self):
        policy = (DISTRO / "conf/distro/include/lmp-dynamicdevices-headless-compat.inc").read_text()
        original = policy.replace("# Legacy headless fallback: retain existing policy for non-display machines.\n", "", 1)
        self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), "77e04240ae9445b6e085a050507b6d080c4a0ed4dd84b832e79ab89c8ba058df")

    def test_assembled_image_gate_rejects_705_failure(self):
        recipe = (DISTRO / "recipes-samples/images/lmp-factory-image.bb").read_text()
        body = re.search(r"python do_rootfs:append\(\) \{\n(.*?)\n\}", recipe, re.S)[1]
        def fatal(message):
            raise RuntimeError(message)
        env = {"bb": types.SimpleNamespace(fatal=fatal)}
        exec(compile("def check(d):\n" + textwrap.indent(textwrap.dedent(body), "    "), "image-payload-gate", "exec"), env)
        check = env['check']
        with tempfile.TemporaryDirectory() as temp:
            data = Data(IMAGE_ROOTFS=temp, DISTRO="lmp-dynamicdevices-headless", DD_PRODUCT_FEATURES="display alsa usb-gadget", DISTRO_FEATURES="alsa usbgadget", OSTREE_KERNEL_ARGS="console=tty1 console=ttymxc1,115200 root=LABEL=otaroot")
            with self.assertRaisesRegex(RuntimeError, "missing distro features"):
                check(data)
            data.setVar('DISTRO_FEATURES', 'display-runtime wayland opengl display-boot-splash')
            with self.assertRaisesRegex(RuntimeError, "missing /usr/bin/weston"):
                check(data)
            for name in ('usr/bin/weston', 'usr/share/aesl-display-splash/splash.png', 'etc/xdg/weston/weston-aesl.ini', 'usr/lib/systemd/system/aesl-splash-quit.service'):
                path = Path(temp) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
                if name.startswith('usr/bin/'):
                    path.chmod(0o755)
            link = Path(temp) / 'usr/bin/psplash'
            link.symlink_to('/etc/alternatives/aesl-psplash-fixture')
            with self.assertRaisesRegex(RuntimeError, "missing /usr/bin/psplash"):
                check(data)
            alternatives = Path(temp) / 'etc/alternatives'
            alternatives.mkdir(parents=True)
            (alternatives / 'aesl-psplash-fixture').symlink_to('../../usr/bin/psplash-default')
            target = Path(temp) / 'usr/bin/psplash-default'
            target.touch()
            target.chmod(0o755)
            with self.assertRaisesRegex(RuntimeError, "display-VT kernel console"):
                check(data)
            data.setVar('OSTREE_KERNEL_ARGS', 'console=ttymxc1,115200 root=LABEL=otaroot splash')
            check(data)
            target.chmod(0o644)
            with self.assertRaisesRegex(RuntimeError, "non-executable /usr/bin/psplash"):
                check(data)
            target.chmod(0o755)
            link.unlink()
            link.symlink_to('//usr/bin/psplash-default')
            check(data)
            link.unlink()
            link.symlink_to('/usr/bin/psplash')
            with self.assertRaisesRegex(RuntimeError, "missing /usr/bin/psplash"):
                check(data)
            link.unlink()
            link.symlink_to('../../../../etc/passwd')
            with self.assertRaisesRegex(RuntimeError, "missing /usr/bin/psplash"):
                check(data)
            data.setVar('DD_DISPLAY_BOOT_SPLASH', '0')
            data.setVar('DISTRO_FEATURES', 'display-runtime wayland opengl')
            check(data)
            data.setVar('DD_PRODUCT_FEATURES', 'alsa')
            data.setVar('DISTRO_FEATURES', 'alsa')
            check(data)

    def test_legacy_screen_bundle_and_explicit_optout(self):
        policy = (DISTRO / "conf/distro/include/lmp-dynamicdevices-display-compat.inc").read_text()
        self.assertEqual(expression(policy, "DD_PRODUCT_FEATURES", Data(MACHINE="imx8mm-jaguar-screen")), "display flutter godot alsa")
        self.assertEqual(expression(policy, "DD_PRODUCT_FEATURES", Data(MACHINE="imx8mm-jaguar-dt510")), "display")
        self.assertNotRegex(policy, r"DD_PRODUCT_FEATURES(?:\s*=|:append)")
        self.assertIn('DISTRO_FEATURES:append:imx8mm-jaguar-dt510 = " improv"', policy)

    def test_effective_product_removals_survive_distro_include(self):
        contract = (DISTRO / "conf/distro/include/lmp-dynamicdevices-product-features.inc").read_text()
        headed = (DISTRO / "conf/distro/lmp-dynamicdevices.conf").read_text()
        self.assertNotRegex(headed, r'(?m)^DISTRO_FEATURES:remove\s*=', "Canonical distro must not overwrite product removals")
        base = {'wayland', 'opengl', 'alsa', 'pulseaudio', 'vulkan', 'x11', 'directfb', 'zeroconf', 'wifi', 'systemd', 'sota', 'cra-audit'}
        for selected in ('', 'alsa usb-gadget', 'display alsa usb-gadget'):
            with self.subTest(selected=selected):
                data = Data(DD_PRODUCT_FEATURES=selected, DD_DISPLAY_BOOT_SPLASH='1')
                env = {"d": data, "bb": types.SimpleNamespace(utils=types.SimpleNamespace(contains=contains))}
                expanded = '\n'.join(re.sub(r'\$\{@(.*)\}', lambda m: str(eval(m[1], env)), line) for line in contract.splitlines())
                removals = re.search(r'^DISTRO_FEATURES:remove = "(.*?)"', expanded, re.M | re.S)[1]
                effective = base - set(removals.replace('\\\n', ' ').split())
                self.assertTrue({'wifi', 'systemd', 'sota', 'cra-audit'} <= effective)
                self.assertFalse({'zeroconf', 'x11', 'directfb', 'pulseaudio', 'vulkan'} & effective)
                if 'display' in selected:
                    self.assertTrue({'wayland', 'opengl', 'alsa'} <= effective)
                else:
                    self.assertFalse({'wayland', 'opengl'} & effective)
                    self.assertEqual('alsa' in effective, 'alsa' in selected)

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

    def test_ota_boot_policy_preserves_non_vt_arguments_and_failure_is_safe(self):
        fragment = (BSP / "recipes-bsp/u-boot/u-boot-ostree-scr-fit/display-bootargs.cmd").read_text()
        self.assertIn('"^console=tty[0123456789]+$"', fragment)
        # Exercise the actual fragment with setexpr's U-Boot 2024.04 no-match
        # return code (1), not sed's always-success status.
        shim = r'''
setenv() {
    key=$1; shift
    if test "$#" = 0; then unset "$key"; else export "$key=$*"; fi
}
setexpr() {
    test "$FAIL_REGEX" != 1 || return 1
    key=$1; shift
    test "$1" = sub || return 1
    expr=$2; replacement=$3; value=$4
    printf '%s\n' "$value" | grep -Eq "$expr" || return 1
    value=$(printf '%s\n' "$value" | sed -E "s/$expr/$replacement/")
    export "$key=$value"
}
'''
        original = "console=tty1 console=tty0 console=ttymxc1,115200 earlycon=ec_imx6q,0x30890000,115200 rootfstype=ext4 ostree=/ostree/boot.1/lmp/hash/0 console=tty63 root=/dev/mmcblk2p2 rw audit=1 video=DSI-1:d"
        for failure in (False, True):
            for mode in ("", " video=HDMI-A-1:1280x720@60e"):
                env = dict(os.environ, bootargs=original, FAIL_REGEX=str(int(failure)))
                script = shim + fragment.replace('@@AESL_DISPLAY_MODE@@', mode) + '\nprintf "%s\\n" "$bootargs"\n'
                # Hush expands unset environment names to empty strings.
                actual = subprocess.run(['sh', '-e', '-c', script], env=env, text=True, capture_output=True, check=True).stdout.split()
                retained = original.split() if failure else [x for x in original.split() if not re.fullmatch(r'console=tty\d+', x)]
                self.assertEqual(actual, retained + ['splash', 'logo.nologo', 'vt.global_cursor_default=0'] + mode.split())
        self.assertNotRegex(fragment, r'\b(?:saveenv|fw_setenv|mmc|ext4write|reset)\b')

    def test_ota_boot_policy_is_opt_in_and_after_rollback_before_root(self):
        append = (BSP / 'recipes-bsp/u-boot/u-boot-ostree-scr-fit.bbappend').read_text()
        body = re.search(r'python do_unpack:append\(\) \{\n(.*?)\n\}', append, re.S)[1]
        def fatal(message):
            raise RuntimeError(message)
        env = {'bb': types.SimpleNamespace(utils=types.SimpleNamespace(contains=contains), fatal=fatal)}
        # Model a later task append as well as the isolated function: a return
        # in this append must not skip subsequent machine-specific appends.
        exec('def unpack(d):\n' + textwrap.indent(textwrap.dedent(body), '    ') + '\n    d.setVar("LATER_APPEND_RAN", True)\n', env)
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            original = 'run bootcmd_rollback\nrun bootcmd_bootargs_add_root\nrun bootcmd_load_f\nrun bootcmd_run\nreset\n'
            footer = work / 'boot-footer.cmd.in'
            shutil.copy(BSP / 'recipes-bsp/u-boot/u-boot-ostree-scr-fit/display-bootargs.cmd', work)
            for features, machine in [('systemd', 'imx8mm-jaguar-dt510'), ('display-boot-splash', 'imx8mm-jaguar-dt510'), ('display-boot-splash', 'imx8mm-jaguar-screen')]:
                footer.write_text(original)
                data = Data(WORKDIR=temp, DISTRO_FEATURES=features, MACHINE=machine)
                env['unpack'](data)
                self.assertTrue(data.getVar('LATER_APPEND_RAN'))
                actual = footer.read_text()
                if features == 'systemd':
                    self.assertEqual(actual, original)
                else:
                    self.assertLess(actual.index('run bootcmd_rollback'), actual.index('for aesl_display_arg'))
                    self.assertLess(actual.index('setenv bootargs'), actual.index('run bootcmd_bootargs_add_root'))
                    self.assertEqual('video=HDMI-A-1:1280x720@60e' in actual, machine == 'imx8mm-jaguar-dt510')
            footer.write_text('run bootcmd_run\n')
            with self.assertRaisesRegex(RuntimeError, 'rollback selection'):
                env['unpack'](Data(WORKDIR=temp, DISTRO_FEATURES='display-boot-splash'))

    def test_dt510_keeps_hardware_accelerated_renderer(self):
        config = configparser.ConfigParser()
        config.read(SESSION / 'aesl-display-session/imx8mm-jaguar-dt510/weston-aesl.ini')
        self.assertTrue(config.getboolean('core', 'use-g2d'))
        self.assertFalse(config.getboolean('core', 'use-pixman', fallback=False))

    def test_dt510_gpu_access_is_active_seat_only(self):
        recipe = (SESSION / 'aesl-display-session_1.0.bb').read_text()
        self.assertIn('SRC_URI:append:imx8mm-jaguar-dt510 = " file://70-aesl-galcore.rules"', recipe)
        body = re.search(r'do_install:append:imx8mm-jaguar-dt510\(\) \{\n(.*?)\n\}', recipe, re.S)[1]
        rule = (FILES / '70-aesl-galcore.rules').read_text()
        effective = [line for line in rule.splitlines() if line and not line.startswith('#')]
        self.assertEqual(effective, ['SUBSYSTEM=="gpu_class", KERNEL=="galcore", TAG+="seat", TAG+="uaccess"'])
        self.assertLess('70-aesl-galcore.rules', '73-seat-late.rules')
        self.assertNotRegex(rule, r'\b(?:MODE|GROUP|OWNER|RUN)\s*[:+]?=')
        self.assertIn('REQUIRED_DISTRO_FEATURES = "display-boot-splash wayland systemd"', recipe)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'etc/udev/rules.d').mkdir(parents=True)
            for key, value in {'D': temp, 'WORKDIR': str(FILES), 'sysconfdir': '/etc'}.items():
                body = body.replace('${' + key + '}', value)
            subprocess.run(['sh', '-eu', '-c', body], check=True)
            self.assertEqual((root / 'etc/udev/rules.d/70-aesl-galcore.rules').read_text(), rule)

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
