"""Check the image acceptance contract with controlled filesystem fixtures."""
import importlib.util
import gzip
import contextlib
import io
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
        (checkout / 'etc/default/dd-kiosk-browser').write_text(self.environment())
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
            with self.assertRaisesRegex(ValueError, 'not executable'):
                VERIFY.verify_jaguar_touch(root)
            (root / 'usr/bin/jaguar-touch-test').chmod(0o755)
            VERIFY.verify_jaguar_touch(root)


if __name__ == '__main__':
    unittest.main()
