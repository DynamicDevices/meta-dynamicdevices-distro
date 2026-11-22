"""Check the image acceptance contract with controlled filesystem fixtures."""
import importlib.util
import gzip
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('kiosk_acceptance', ROOT / 'scripts/verify-kiosk-image.py')
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class KioskAcceptanceTests(unittest.TestCase):
    DEPLOYMENTS = {'ostree/deploy/test/deploy/good.0',
                   'ostree/deploy/test/deploy/candidate.1'}

    def environment(self, url=VERIFY.JAGUAR_START_URL):
        return (f'DD_KIOSK_URL="{url}"\nDD_KIOSK_MUTE_AUDIO=1\n'
                'DD_KIOSK_GLES2_COMPAT=1\n')

    def make_deployment(self, root, deployment, case):
        checkout = root / deployment
        for name in (*VERIFY.ARTIFACT_FILES,
                     '/usr/lib/systemd/system/dd-kiosk-browser.service'):
            path = checkout / name.lstrip('/')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture')
            path.chmod(0o755 if name in VERIFY.ARTIFACT_EXECUTABLES else 0o644)
        (checkout / 'etc/default/dd-kiosk-browser').write_text(self.environment())
        for name, settings in VERIFY.KIOSK_CONTENTS.items():
            (checkout / name.lstrip('/')).write_text(
                ('[Service]\n' if name.endswith('.conf') else '') + '\n'.join(settings) + '\n')
        (checkout / 'usr/bin/dd-kiosk-browser').write_text(
            'exec /usr/bin/chromium --ozone-platform=wayland --kiosk\n')
        (checkout / 'usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzz-native-runtime.conf').write_text(
            (ROOT / 'recipes-graphics/dd-kiosk-browser/dd-kiosk-browser/dd-kiosk-native-runtime.conf').read_text())
        (checkout / 'etc/chromium/policies/managed/dd-kiosk-browser.json').write_text(json.dumps(VERIFY.CHROMIUM_POLICY))
        (checkout / 'usr/lib/systemd/system/dd-kiosk-browser.service').write_text(
            (ROOT / 'recipes-graphics/dd-kiosk-browser/dd-kiosk-browser/dd-kiosk-browser.service').read_text())
        enabled = checkout / VERIFY.KIOSK_ENABLEMENT.lstrip('/')
        enabled.unlink()
        enabled.symlink_to('/usr/lib/systemd/system/dd-kiosk-browser.service')
        (checkout / 'usr/lib/systemd/system/weston.service.d/zzzzzz-screen-etnaviv.conf').write_text(
            'ExecStart=\nExecStart=/usr/libexec/dd-screen-weston --config=/etc/xdg/weston/weston-screen.ini\n')
        (checkout / 'etc/xdg/weston/weston-screen.ini').write_text('shell=kiosk-shell.so\ntransform=rotate-90\n')
        for module in ('gl-renderer.so', 'kiosk-shell.so'):
            path = checkout / 'usr/lib/libweston-13' / module
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture')
        launcher = checkout / 'usr/bin/jaguar-touch-test'
        launcher.chmod(0o755)
        if case == 'regular':
            return
        launcher.unlink()
        if case == 'directory':
            launcher.mkdir()
        elif case == 'non-executable':
            launcher.write_text('fixture')
            launcher.chmod(0o644)
        else:
            target = checkout / 'usr/libexec/touch-launcher'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('fixture')
            target.chmod(0o644 if case == 'symlink-non-executable' else 0o755)
            if case == 'symlink-directory':
                target.unlink()
                target.mkdir()
            link = {
                'relative': '../libexec/touch-launcher',
                'absolute': '/usr/libexec/touch-launcher',
                'broken': '../libexec/missing',
                'cycle': 'jaguar-touch-test',
                'escape': '../../../outside',
                'symlink-non-executable': '../libexec/touch-launcher',
                'symlink-directory': '../libexec/touch-launcher',
                'long': '../libexec/' + 'long-' * 20,
            }[case]
            if case == 'long':
                target.rename(checkout / 'usr/libexec' / ('long-' * 20))
            launcher.symlink_to(link)

    def check_artifact(self, root, directory, artifact, expected_url=VERIFY.JAGUAR_START_URL):
        path = Path(directory) / ('ota.tar.xz' if artifact == 'tar' else 'ota.ext4.gz')
        with contextlib.redirect_stdout(io.StringIO()):
            if artifact == 'tar':
                with tarfile.open(path, 'w:xz') as archive:
                    archive.add(root, arcname='.')
                return VERIFY.verify_ota_tar(path, self.DEPLOYMENTS, expected_url)
            image = Path(directory) / 'ota.ext4'
            with image.open('wb') as output:
                output.truncate(16 * 1024 * 1024)
            subprocess.run(['mkfs.ext4', '-q', '-F', '-d', str(root), str(image)],
                           check=True, capture_output=True)
            with image.open('rb') as source, gzip.open(path, 'wb') as output:
                shutil.copyfileobj(source, output)
            return VERIFY.verify_ota_ext4(path, expected_url)

    def test_shipped_tar_and_ext4_require_executable_touch_launcher(self):
        for case in ('regular', 'relative', 'absolute', 'long', 'directory',
                     'non-executable', 'broken', 'cycle', 'escape',
                     'symlink-non-executable', 'symlink-directory'):
            for artifact in ('tar', 'ext4'):
                with self.subTest(case=case, artifact=artifact), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / 'root'
                    self.make_deployment(root, 'ostree/deploy/test/deploy/good.0', 'regular')
                    self.make_deployment(root, 'ostree/deploy/test/deploy/candidate.1', case)
                    check = lambda: self.check_artifact(root, directory, artifact)
                    if case in ('regular', 'relative', 'absolute', 'long'):
                        result = check()
                        if artifact == 'ext4':
                            self.assertEqual(result, self.DEPLOYMENTS)
                    else:
                        with self.assertRaises(ValueError):
                            check()

    def test_shipped_touch_rule_and_page_must_resolve_to_regular_files(self):
        for name in VERIFY.JAGUAR_TOUCH_FILES[:2]:
            for kind in ('directory', 'broken-link', 'valid-link'):
                for artifact in ('tar', 'ext4'):
                    with self.subTest(name=name, kind=kind, artifact=artifact), tempfile.TemporaryDirectory() as directory:
                        root = Path(directory) / 'root'
                        for deployment in self.DEPLOYMENTS:
                            self.make_deployment(root, deployment, 'regular')
                        path = root / 'ostree/deploy/test/deploy/candidate.1' / name.lstrip('/')
                        path.unlink()
                        if kind == 'directory':
                            path.mkdir()
                        elif kind == 'broken-link':
                            path.symlink_to('missing')
                        else:
                            path.with_name('actual-payload').write_text('fixture')
                            path.symlink_to('actual-payload')
                        if kind == 'valid-link':
                            self.check_artifact(root, directory, artifact)
                        else:
                            with self.assertRaises(ValueError):
                                self.check_artifact(root, directory, artifact)

    def test_tar_deployments_must_match_ext4_exactly(self):
        for case in ('extra-stale', 'missing', 'duplicate', 'implicit-directories', 'serial-two'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / 'root'
                for deployment in self.DEPLOYMENTS:
                    self.make_deployment(root, deployment, 'regular')
                if case == 'extra-stale':
                    extra = 'ostree/deploy/other/deploy/stale.0'
                    self.make_deployment(root, extra, 'regular')
                    (root / extra / 'etc/default/dd-kiosk-browser').write_text(self.environment('https://stale.example.com'))
                elif case == 'missing':
                    shutil.rmtree(root / 'ostree/deploy/test/deploy/candidate.1')
                elif case == 'serial-two':
                    old = root / 'ostree/deploy/test/deploy/candidate.1'
                    old.rename(old.with_name('candidate.2'))
                if case == 'serial-two':
                    # The ext4 enumerator must also see deployment serials beyond .1.
                    original = self.DEPLOYMENTS
                    self.DEPLOYMENTS = {x.replace('candidate.1', 'candidate.2') for x in original}
                    try:
                        self.assertEqual(self.check_artifact(root, directory, 'ext4'), self.DEPLOYMENTS)
                        self.check_artifact(root, directory, 'tar')
                    finally:
                        self.DEPLOYMENTS = original
                    continue
                path = Path(directory) / 'ota.tar.xz'
                with tarfile.open(path, 'w:xz') as archive:
                    if case == 'implicit-directories':
                        for file in root.rglob('*'):
                            if file.is_file() or file.is_symlink():
                                archive.add(file, arcname=str(file.relative_to(root)))
                    else:
                        archive.add(root, arcname='.')
                    if case == 'duplicate':
                        name = 'ostree/deploy/test/deploy/good.0'
                        archive.add(root / name, arcname=name, recursive=False)
                if case == 'implicit-directories':
                    with contextlib.redirect_stdout(io.StringIO()):
                        VERIFY.verify_ota_tar(path, self.DEPLOYMENTS)
                else:
                    with self.assertRaisesRegex(ValueError, 'deployments differ|duplicate deployment'):
                        VERIFY.verify_ota_tar(path, self.DEPLOYMENTS)

    def test_display_boot_contract_is_shared_by_rootfs_tar_and_ext4(self):
        cases = {
            'missing-selector': ('usr/libexec/dd-screen-weston', 'remove'),
            'non-executable-selector': ('usr/libexec/dd-screen-weston', 'chmod'),
            'missing-renderer': ('usr/lib/libweston-13/gl-renderer.so', 'remove'),
            'missing-shell': ('usr/lib/libweston-13/kiosk-shell.so', 'remove'),
            'wrong-launch-command': ('usr/lib/systemd/system/weston.service.d/zzzzzz-screen-etnaviv.conf', 'wrong-command'),
            'wrong-shell': ('etc/xdg/weston/weston-screen.ini', 'wrong-shell'),
        }
        for case, (name, action) in cases.items():
            for artifact in ('rootfs', 'tar', 'ext4'):
                with self.subTest(case=case, artifact=artifact), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / 'root'
                    for deployment in self.DEPLOYMENTS:
                        self.make_deployment(root, deployment, 'regular')
                    checkout = root / 'ostree/deploy/test/deploy/candidate.1'
                    path = checkout / name
                    if action == 'remove':
                        path.unlink()
                    elif action == 'chmod':
                        path.chmod(0o644)
                    elif action == 'wrong-command':
                        path.write_text(path.read_text().replace('/usr/libexec/dd-screen-weston ', '/usr/bin/weston '))
                    else:
                        path.write_text('shell=missing-shell.so\ntransform=rotate-90\n')
                    with self.assertRaises(ValueError):
                        if artifact == 'rootfs':
                            VERIFY.verify_etnaviv_weston(checkout)
                        else:
                            self.check_artifact(root, directory, artifact)

    def test_kiosk_boot_and_policy_contract_in_all_image_views(self):
        for case in ('valid', 'missing-context', 'wrong-context', 'disabled',
                     'broken-link', 'regular-enablement', 'wrong-target',
                     'wrong-unit-user', 'wrong-unit-restart', 'wrong-browser-policy', 'lib-unit',
                     'commented-user', 'later-user', 'missing-exec', 'wrong-exec',
                     'duplicate-exec', 'commented-flags', 'wrong-group', 'wrong-groups',
                     'wrong-state', 'wrong-envfile', 'wrong-order', 'wrong-target-unit',
                     'dropin-user', 'global-dropin', 'prefix-dropin', 'runtime-dropin',
                     'admin-unit', 'commented-context', 'later-context', 'reset-unset',
                     'valid-audio', 'valid-reset', 'dropin-wrong-exec',
                     'later-restart', 'unqualified-env', 'escaped-context'):
            for artifact in ('rootfs', 'tar', 'ext4'):
                with self.subTest(case=case, artifact=artifact), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / 'root'
                    for deployment in self.DEPLOYMENTS:
                        self.make_deployment(root, deployment, 'regular')
                    checkout = root / 'ostree/deploy/test/deploy/candidate.1'
                    context = checkout / 'usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzzzz-screen-etnaviv-context.conf'
                    enabled = checkout / VERIFY.KIOSK_ENABLEMENT.lstrip('/')
                    unit = checkout / 'usr/lib/systemd/system/dd-kiosk-browser.service'
                    if case == 'missing-context':
                        context.unlink()
                    elif case == 'wrong-context':
                        context.write_text('Environment=DD_KIOSK_GLES2_COMPAT=0\n')
                    elif case in ('disabled', 'broken-link', 'regular-enablement', 'wrong-target', 'lib-unit'):
                        enabled.unlink()
                        if case == 'broken-link':
                            enabled.symlink_to('/usr/lib/systemd/system/missing.service')
                        elif case == 'regular-enablement':
                            enabled.write_text(unit.read_text())
                        elif case == 'wrong-target':
                            unit.with_name('other.service').write_text(unit.read_text())
                            enabled.symlink_to('/usr/lib/systemd/system/other.service')
                        elif case == 'lib-unit':
                            target = checkout / 'lib/systemd/system/dd-kiosk-browser.service'
                            target.parent.mkdir(parents=True)
                            unit.rename(target)
                            enabled.symlink_to('/lib/systemd/system/dd-kiosk-browser.service')
                    elif case == 'wrong-unit-user':
                        unit.write_text(unit.read_text().replace('User=weston', 'User=root'))
                    elif case == 'wrong-unit-restart':
                        unit.write_text(unit.read_text().replace('Restart=always', 'Restart=no'))
                    elif case == 'wrong-browser-policy':
                        (checkout / 'etc/chromium/policies/managed/dd-kiosk-browser.json').write_text('{}')
                    elif case == 'commented-user':
                        unit.write_text(unit.read_text().replace('User=weston', '#User=weston'))
                    elif case == 'later-user':
                        unit.write_text(unit.read_text() + '\n[Service]\nUser=root\n')
                    elif case in ('missing-exec', 'wrong-exec', 'duplicate-exec'):
                        command = 'ExecStart=/usr/bin/dd-kiosk-browser'
                        replacement = {'missing-exec': '#' + command,
                                       'wrong-exec': 'ExecStart=/bin/false',
                                       'duplicate-exec': command + '\nExecStart=/bin/false'}[case]
                        unit.write_text(unit.read_text().replace(command, replacement))
                        runtime = context.with_name('zzzz-native-runtime.conf')
                        runtime.write_text('[Service]\nUnsetEnvironment=LD_LIBRARY_PATH\n')
                    elif case == 'commented-flags':
                        (checkout / 'usr/bin/dd-kiosk-browser').write_text(
                            '# --ozone-platform=wayland --kiosk\nexec /usr/bin/chromium\n')
                    elif case.startswith('wrong-'):
                        key, value = {'wrong-group': ('Group=weston', 'Group=root'),
                                      'wrong-groups': ('SupplementaryGroups=render video', 'SupplementaryGroups=render'),
                                      'wrong-state': ('StateDirectory=dd-kiosk-browser', '#StateDirectory=dd-kiosk-browser'),
                                      'wrong-envfile': ('EnvironmentFile=-/etc/default/dd-kiosk-browser', 'EnvironmentFile=/tmp/kiosk'),
                                      'wrong-order': ('After=weston.service', '#After=weston.service'),
                                      'wrong-target-unit': ('WantedBy=multi-user.target', 'WantedBy=other.target')}[case]
                        unit.write_text(unit.read_text().replace(key, value))
                    elif case in ('dropin-user', 'global-dropin', 'prefix-dropin', 'runtime-dropin'):
                        parent = {'dropin-user': 'etc/systemd/system/dd-kiosk-browser.service.d',
                                  'global-dropin': 'usr/lib/systemd/system/service.d',
                                  'prefix-dropin': 'usr/lib/systemd/system/dd-kiosk-.service.d',
                                  'runtime-dropin': 'run/systemd/system/dd-kiosk-browser.service.d'}[case]
                        override = checkout / parent / 'zzzzzzz-override.conf'
                        override.parent.mkdir(parents=True, exist_ok=True)
                        override.write_text('[Service]\nUser=root\n')
                    elif case == 'admin-unit':
                        override = checkout / 'etc/systemd/system/dd-kiosk-browser.service'
                        override.write_text(unit.read_text().replace('User=weston', 'User=root'))
                    elif case == 'commented-context':
                        context.write_text('[Service]\n#Environment=DD_KIOSK_GLES2_COMPAT=1\n')
                    elif case == 'later-context':
                        context.write_text('[Service]\nEnvironment=DD_KIOSK_GLES2_COMPAT=1\nEnvironment=DD_KIOSK_GLES2_COMPAT=0\n')
                    elif case == 'reset-unset':
                        runtime = context.with_name('zzzz-native-runtime.conf')
                        runtime.write_text('[Service]\nUnsetEnvironment=LD_LIBRARY_PATH\nUnsetEnvironment=\n')
                    elif case == 'valid-audio':
                        for name in ('audio', 'screen-audio'):
                            context.with_name(name + '.conf').write_text(
                                (ROOT / ('recipes-graphics/dd-kiosk-browser/dd-kiosk-browser/dd-kiosk-browser-' + name + '.conf')).read_text())
                    elif case == 'valid-reset':
                        context.write_text('[Service]\nEnvironment=DD_KIOSK_GLES2_COMPAT=0\nEnvironment=\nEnvironment=DD_KIOSK_GLES2_COMPAT=1\n')
                    elif case == 'dropin-wrong-exec':
                        context.write_text(context.read_text() + 'ExecStart=\nExecStart=/bin/false\n')
                    elif case == 'later-restart':
                        unit.write_text(unit.read_text() + '\n[Service]\nRestart=no\n')
                    elif case == 'unqualified-env':
                        context.write_text(context.read_text() + 'Environment=LD_PRELOAD=/tmp/inject.so\n')
                    elif case == 'escaped-context':
                        context.write_text(context.read_text() + 'Environment=DD_KIOSK_GLES2_COMPAT=\\1\n')
                    def check():
                        if artifact == 'rootfs':
                            with contextlib.redirect_stdout(io.StringIO()):
                                VERIFY.verify_rootfs(checkout)
                        else:
                            self.check_artifact(root, directory, artifact)
                    if case in ('valid', 'lib-unit', 'valid-audio', 'valid-reset'):
                        check()
                    else:
                        with self.assertRaises(ValueError):
                            check()

    def test_rootfs_environment_links_are_contained(self):
        for kind in ('absolute-escape', 'relative-escape', 'parent-escape',
                     'absolute-internal', 'relative-internal'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / 'root'
                config = root / 'etc/default/dd-kiosk-browser'
                config.parent.mkdir(parents=True)
                host = Path(directory) / 'host'
                host.mkdir()
                (host / config.name).write_text(self.environment())
                if kind == 'parent-escape':
                    config.parent.rmdir()
                    config.parent.symlink_to(host)
                elif kind.endswith('internal'):
                    target = config.with_name('real-environment')
                    target.write_text(self.environment())
                    config.symlink_to('/etc/default/real-environment'
                                      if kind == 'absolute-internal' else target.name)
                else:
                    target = host / config.name
                    config.symlink_to(str(target) if kind == 'absolute-escape'
                                      else os.path.relpath(target, config.parent))
                if kind.endswith('internal'):
                    VERIFY.verify_startup_url(root, VERIFY.JAGUAR_START_URL)
                else:
                    with self.assertRaises(ValueError):
                        VERIFY.verify_startup_url(root, VERIFY.JAGUAR_START_URL)

    def test_rootfs_reads_use_image_not_host_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'root'
            self.make_deployment(root, '', 'regular')
            files = {
                'usr/lib/systemd/system/weston.service.d/zzzzzz-screen-etnaviv.conf': 'ExecStart=\nExecStart=/usr/libexec/dd-screen-weston --config=/etc/xdg/weston/weston-screen.ini\n',
                'usr/libexec/dd-screen-weston': 'fixture',
                'usr/lib/libweston-13/gl-renderer.so': 'fixture',
                'usr/lib/libweston-13/kiosk-shell.so': 'fixture',
                'usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzzzz-screen-etnaviv-context.conf': 'Environment=DD_KIOSK_GLES2_COMPAT=1',
                'usr/lib/systemd/system/dd-kiosk-browser.service': 'User=weston\nStateDirectory=dd-kiosk-browser\nRestart=always\nAfter=weston.service\n',
                'usr/bin/dd-kiosk-browser': '--ozone-platform=wayland --kiosk',
                'usr/libexec/dd-kiosk-linker-guard': 'kiosk-audio-hotpatch.conf zz-audio-hotpatch.conf /sbin/ldconfig /ostree/deploy/',
                'usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzz-native-runtime.conf': 'UnsetEnvironment=LD_LIBRARY_PATH',
                'usr/lib/systemd/system/weston.service.d/zzzz-kiosk-linker-guard.conf': 'ExecStartPre=+/usr/libexec/dd-kiosk-linker-guard',
                'etc/xdg/weston/weston-screen.ini': 'shell=kiosk-shell.so\ntransform=rotate-90',
                'etc/systemd/system/weston.service.d/screen.conf': '--config=/etc/xdg/weston/weston-screen.ini',
                'etc/chromium/policies/managed/dd-kiosk-browser.json': json.dumps({
                    'AllowFileSelectionDialogs': False, 'BrowserAddPersonEnabled': False,
                    'BrowserGuestModeEnabled': False, 'BrowserSignin': 0,
                    'DeveloperToolsAvailability': 2, 'DownloadRestrictions': 3,
                    'ExtensionInstallBlocklist': ['*'], 'IncognitoModeAvailability': 1,
                    'PrintingEnabled': False, 'URLBlocklist': ['view-source:*']}),
            }
            # Keep the contained-read fixture's valid units/launcher identical to
            # make_deployment; each is subsequently replaced by an escaping link.
            for name in list(files):
                if name.endswith('.conf') or name.endswith('.service') or name == 'usr/bin/dd-kiosk-browser':
                    files[name] = (root / name).read_text()
            for name, content in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            (root / 'usr/libexec/dd-screen-weston').chmod(0o755)
            enabled = root / 'etc/systemd/system/multi-user.target.wants/dd-kiosk-browser.service'
            enabled.parent.mkdir(parents=True, exist_ok=True)
            enabled.unlink()
            enabled.symlink_to('/usr/lib/systemd/system/dd-kiosk-browser.service')
            with contextlib.redirect_stdout(io.StringIO()):
                VERIFY.verify_rootfs(root)
            for name, content in files.items():
                with self.subTest(name=name):
                    path = root / name
                    mode = path.stat().st_mode
                    host = Path(directory) / 'host-file'
                    host.write_text(content)
                    host.chmod(0o755)
                    path.unlink()
                    path.symlink_to(host)
                    with self.assertRaises(ValueError):
                        VERIFY.verify_rootfs(root)
                    path.unlink()
                    path.write_text(content)
                    path.chmod(mode)

    def test_every_shipped_program_must_be_executable(self):
        for name in sorted(VERIFY.ARTIFACT_EXECUTABLES):
            for symlink in (False, True):
                for artifact in ('tar', 'ext4'):
                    with self.subTest(name=name, symlink=symlink, artifact=artifact), tempfile.TemporaryDirectory() as directory:
                        root = Path(directory) / 'root'
                        for deployment in self.DEPLOYMENTS:
                            self.make_deployment(root, deployment, 'regular')
                        path = root / 'ostree/deploy/test/deploy/candidate.1' / name.lstrip('/')
                        path.chmod(0o644)
                        if symlink:
                            path.rename(path.with_name('not-executable'))
                            path.symlink_to('not-executable')
                        with self.assertRaisesRegex(ValueError, 'regular executable'):
                            self.check_artifact(root, directory, artifact)

    def test_rootfs_touch_symlinks_stay_inside_rootfs(self):
        for name in VERIFY.JAGUAR_TOUCH_FILES:
            for kind in ('absolute-escape', 'relative-escape', 'absolute-internal',
                         'relative-internal', 'cycle', 'parent-escape'):
                with self.subTest(name=name, kind=kind), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / 'root'
                    outside = Path(directory) / 'host-payload'
                    outside.write_text('host fixture must never satisfy rootfs checks')
                    outside.chmod(0o755)
                    for payload in VERIFY.JAGUAR_TOUCH_FILES:
                        path = root / payload.lstrip('/')
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text('fixture')
                        path.chmod(0o755)
                    path = root / name.lstrip('/')
                    path.unlink()
                    if kind == 'parent-escape':
                        host = Path(directory) / 'host-directory'
                        host.mkdir()
                        (host / path.name).write_text('fixture')
                        (host / path.name).chmod(0o755)
                        path.parent.rmdir()
                        path.parent.symlink_to(host)
                    elif kind.endswith('internal'):
                        target = path.with_name('real-payload')
                        target.write_text('fixture')
                        target.chmod(0o755)
                        path.symlink_to('/' + str(target.relative_to(root))
                                        if kind == 'absolute-internal' else target.name)
                    else:
                        path.symlink_to(str(outside) if kind == 'absolute-escape' else
                                        os.path.relpath(outside, path.parent) if kind == 'relative-escape'
                                        else path.name)
                    if kind.endswith('internal'):
                        VERIFY.verify_jaguar_touch(root)
                    else:
                        with self.assertRaises(ValueError):
                            VERIFY.verify_jaguar_touch(root)

    def test_shipped_environment_content_in_every_deployment(self):
        custom = 'https://example.com/start?a=1&b=2'
        cases = {
            'youtube': (self.environment(), VERIFY.JAGUAR_START_URL, True),
            'custom': (self.environment(custom), custom, True),
            'stale-url': (self.environment('https://active-esl.com'), VERIFY.JAGUAR_START_URL, False),
            'wrong-custom-url': (self.environment(), custom, False),
            'unmuted': (self.environment().replace('MUTE_AUDIO=1', 'MUTE_AUDIO=0'), VERIFY.JAGUAR_START_URL, False),
            'no-gles2': (self.environment().replace('GLES2_COMPAT=1', 'GLES2_COMPAT=0'), VERIFY.JAGUAR_START_URL, False),
            'missing-gles2': (self.environment().replace('DD_KIOSK_GLES2_COMPAT=1\n', ''), VERIFY.JAGUAR_START_URL, False),
            'last-assignment': (self.environment() + 'DD_KIOSK_URL=https://stale.example.com\n', VERIFY.JAGUAR_START_URL, False),
            'valid-symlink': (self.environment(), VERIFY.JAGUAR_START_URL, True),
        }
        for case, (content, expected, valid) in cases.items():
            for artifact in ('tar', 'ext4'):
                with self.subTest(case=case, artifact=artifact), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory) / 'root'
                    for deployment in self.DEPLOYMENTS:
                        self.make_deployment(root, deployment, 'regular')
                        (root / deployment / 'etc/default/dd-kiosk-browser').write_text(self.environment(expected))
                    config = root / 'ostree/deploy/test/deploy/candidate.1/etc/default/dd-kiosk-browser'
                    config.write_text(content)
                    if case == 'valid-symlink':
                        config.rename(config.with_name('actual-environment'))
                        config.symlink_to('/etc/default/actual-environment')
                    if valid:
                        self.check_artifact(root, directory, artifact, expected)
                    else:
                        with self.assertRaises(ValueError):
                            self.check_artifact(root, directory, artifact, expected)

    def test_jaguar_and_custom_startup_urls(self):
        for url in (VERIFY.JAGUAR_START_URL, 'https://example.com/start?a=1&b=2'):
            with self.subTest(url=url), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = root / 'etc/default/dd-kiosk-browser'
                config.parent.mkdir(parents=True)
                config.write_text(self.environment(url))
                VERIFY.verify_startup_url(root, url)
                with self.assertRaisesRegex(ValueError, 'differs from expected'):
                    VERIFY.verify_startup_url(root, 'https://wrong.example.com')

    def test_url_must_be_present_and_nonempty(self):
        for content in ('# DD_KIOSK_URL=https://example.com\n', 'DD_KIOSK_URL=\n'):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = root / 'etc/default/dd-kiosk-browser'
                config.parent.mkdir(parents=True)
                config.write_text(content)
                with self.assertRaises(ValueError):
                    VERIFY.verify_startup_url(root, VERIFY.JAGUAR_START_URL)

    def test_touch_payload_is_required_in_rootfs_and_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in VERIFY.JAGUAR_TOUCH_FILES:
                self.assertIn(name, VERIFY.ARTIFACT_FILES)
                with self.assertRaisesRegex(ValueError, 'missing Jaguar touch payload'):
                    VERIFY.verify_jaguar_touch(root)
                path = root / name.lstrip('/')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('fixture')
            with self.assertRaisesRegex(ValueError, 'regular executable'):
                VERIFY.verify_jaguar_touch(root)
            (root / 'usr/bin/jaguar-touch-test').chmod(0o755)
            VERIFY.verify_jaguar_touch(root)


if __name__ == '__main__':
    unittest.main()
