#!/usr/bin/env python3
"""Validate one completed kiosk image against the deployed screen baseline."""
import argparse
import gzip
import hashlib
import json
import lzma
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile

COMMON_REQUIRED = {'weston', 'networkmanager-daemon',
                   'packagegroup-dd-kiosk-browser'}
PROVIDER_REQUIRED = {
    'chromium': {'chromium-ozone-wayland', 'dd-kiosk-browser'},
    'cog': {'cog', 'wpewebkit', 'dd-kiosk-cog'},
}
PROVIDER_RUNTIME = {
    'chromium': 'dd-kiosk-browser',
    'cog': 'dd-kiosk-cog',
}
FORBIDDEN_PREFIXES = (
    'waydroid', 'packagegroup-dd-android-container',
    'screen-flutter-demo', 'flutter', 'libflutter',
    'packagegroup-dd-flutter', 'ivi-homescreen',
    'godot', 'screen-godot-smoke', 'screen-aero-demo',
)
COMMON_ARTIFACT_FILES = (
    '/usr/bin/dd-kiosk-browser',
    '/usr/libexec/dd-kiosk-linker-guard',
    '/etc/default/dd-kiosk-browser',
    '/etc/asound.conf',
    '/etc/NetworkManager/dispatcher.d/90-dd-kiosk-browser',
    '/etc/xdg/weston/weston-screen.ini',
    '/etc/systemd/system/weston.service.d/screen.conf',
    '/usr/share/dd-kiosk-browser/offline.html',
    '/usr/lib/systemd/system/weston.service.d/zzzz-kiosk-linker-guard.conf',
    '/usr/lib/systemd/system/dd-kiosk-browser.service.d/audio.conf',
    '/usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzz-native-runtime.conf',
)
PROVIDER_ARTIFACT_FILES = {
    'chromium': (
        '/usr/bin/chromium',
        '/etc/chromium/policies/managed/dd-kiosk-browser.json',
    ),
    'cog': ('/usr/bin/cog', '/usr/lib/libWPEBackend-fdo-1.0.so.1'),
}


def packages(path):
    result = set()
    for line in path.read_text().splitlines():
        if line.strip():
            result.add(line.split()[0])
    return result


def kiosk_provider(package_set):
    providers = [name for name, runtime in PROVIDER_RUNTIME.items()
                 if runtime in package_set]
    if len(providers) != 1:
        raise ValueError(
            'candidate must contain exactly one kiosk runtime; found '
            f'{providers or "none"}'
        )
    return providers[0]


def artifact_files(provider):
    return COMMON_ARTIFACT_FILES + PROVIDER_ARTIFACT_FILES[provider]


def required_packages(provider):
    return COMMON_REQUIRED | PROVIDER_REQUIRED[provider]


def forbidden_packages(package_set, provider):
    other_provider_packages = set().union(
        *(packages for name, packages in PROVIDER_REQUIRED.items()
          if name != provider)
    )
    return {
        name for name in package_set
        if name.startswith(FORBIDDEN_PREFIXES) or name in other_provider_packages
    }


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as artifact:
        while True:
            chunk = artifact.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def verify_compressed(path, opener, label):
    try:
        with opener(path, 'rb') as artifact:
            while artifact.read(1024 * 1024):
                pass
    except (OSError, EOFError, lzma.LZMAError) as exc:
        raise ValueError(f'{label} failed integrity check: {exc}') from exc


def verify_ota_ext4(path, provider):
    """Inspect the shipped filesystem, not only BitBake's staging rootfs."""
    if shutil.which('debugfs') is None:
        raise ValueError('debugfs is required to inspect the OTA ext4 artifact')

    def debugfs(image, command):
        return subprocess.run(
            ['debugfs', '-R', command, str(image)],
            capture_output=True, text=True, check=False,
        )

    def entries(image, directory):
        result = debugfs(image, f'ls -p {directory}')
        if result.returncode or 'File not found' in result.stderr:
            raise ValueError(f'OTA ext4 missing directory {directory}')
        return [fields[5] for line in result.stdout.splitlines()
                if len(fields := line.split('/')) > 5 and fields[5] not in ('.', '..')]

    def has_file(image, name):
        result = debugfs(image, f'stat {name}')
        return result.returncode == 0 and 'Inode:' in result.stdout

    with tempfile.TemporaryDirectory(prefix='dd-kiosk-ext4-') as directory:
        image = pathlib.Path(directory) / 'ota.ext4'
        with gzip.open(path, 'rb') as compressed, image.open('wb') as output:
            shutil.copyfileobj(compressed, output, 1024 * 1024)
        deployments = []
        for osname in entries(image, '/ostree/deploy'):
            deploy_dir = f'/ostree/deploy/{osname}/deploy'
            for checkout in entries(image, deploy_dir):
                if checkout.endswith(('.0', '.1')):
                    deployments.append(f'{deploy_dir}/{checkout}')
        if not deployments:
            raise ValueError('OTA ext4 has no OSTree deployment checkout')
        units = ('/usr/lib/systemd/system/dd-kiosk-browser.service',
                 '/lib/systemd/system/dd-kiosk-browser.service')
        for deployment in deployments:
            missing = [name for name in artifact_files(provider)
                       if not has_file(image, deployment + name)]
            if not any(has_file(image, deployment + name) for name in units):
                missing.append('dd-kiosk-browser.service')
            if missing:
                raise ValueError(f'OTA ext4 deployment {deployment} missing {missing}')
    print(f'OTA ext4 kiosk payload: verified in {len(deployments)} deployment(s) of {path}')
    return {deployment.lstrip('/') for deployment in deployments}


def verify_ota_tar(path, deployments, provider, ostree_tool):
    """Resolve the OTA's OSTree refs and inspect the committed filesystem."""
    if not ostree_tool or not pathlib.Path(ostree_tool).is_file():
        raise ValueError('an OSTree executable is required to inspect the OTA tar')

    def ostree(repo, *args):
        result = subprocess.run(
            [str(ostree_tool), f'--repo={repo}', *args],
            capture_output=True, text=True, check=False,
        )
        if result.returncode:
            raise ValueError(result.stderr.strip() or 'OSTree inspection failed')
        return result.stdout

    with tempfile.TemporaryDirectory(prefix='dd-kiosk-ota-tar-') as directory:
        extracted = subprocess.run(
            ['tar', '-xJf', str(path), '-C', directory, '--no-same-owner'],
            capture_output=True, text=True, check=False,
        )
        if extracted.returncode:
            raise ValueError(f'cannot extract OTA tar: {extracted.stderr.strip()}')
        repo = pathlib.Path(directory) / 'ostree/repo'
        if not repo.is_dir():
            raise ValueError('OTA tar does not contain ostree/repo')
        refs = [line for line in ostree(repo, 'refs').splitlines() if line]
        if not refs:
            raise ValueError('OTA tar OSTree repository has no refs')
        commits = {ostree(repo, 'rev-parse', ref).strip() for ref in refs}
        expected = {pathlib.PurePosixPath(deployment).name.rsplit('.', 1)[0]
                    for deployment in deployments}
        if not expected <= commits:
            raise ValueError(
                f'OTA tar commits {sorted(commits)} do not include ext4 deployments '
                f'{sorted(expected)}'
            )
        required = [('/usr/etc' + name[4:]) if name.startswith('/etc/') else name
                    for name in artifact_files(provider)]
        unit_variants = ('/usr/lib/systemd/system/dd-kiosk-browser.service',
                         '/lib/systemd/system/dd-kiosk-browser.service')
        for commit in expected:
            missing = [name for name in required
                       if subprocess.run(
                           [str(ostree_tool), f'--repo={repo}', 'ls', commit, name],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=False,
                       ).returncode]
            if all(subprocess.run(
                    [str(ostree_tool), f'--repo={repo}', 'ls', commit, name],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    check=False,
                   ).returncode for name in unit_variants):
                missing.append('dd-kiosk-browser.service')
            if missing:
                raise ValueError(f'OTA tar commit {commit} missing kiosk payload: {missing}')
    print(f'OTA tar kiosk payload: verified in {len(expected)} commit(s) of {path}')


def verify_wic_partitions(wic_gz, ota_gz):
    """Prove WIC contains the checked OTA root and a readable FAT boot volume."""
    for tool in ('sfdisk', 'fsck.vfat'):
        if shutil.which(tool) is None:
            raise ValueError(f'{tool} is required to inspect the WIC artifact')
    with tempfile.TemporaryDirectory(prefix='dd-kiosk-wic-') as directory:
        image = pathlib.Path(directory) / 'factory.wic'
        ota = pathlib.Path(directory) / 'ota.ext4'
        for source, target in ((wic_gz, image), (ota_gz, ota)):
            with gzip.open(source, 'rb') as compressed, target.open('wb') as output:
                shutil.copyfileobj(compressed, output, 1024 * 1024)
        result = subprocess.run(['sfdisk', '--json', str(image)],
                                capture_output=True, text=True, check=False)
        if result.returncode:
            raise ValueError(f'cannot read WIC partition table: {result.stderr.strip()}')
        table = json.loads(result.stdout)['partitiontable']
        partitions = table.get('partitions', [])
        if table.get('label') != 'dos' or len(partitions) != 2:
            raise ValueError('WIC does not have the expected DOS boot/root layout')
        sector_size = table.get('sectorsize', 512)
        boot, root = partitions
        if boot['start'] >= root['start'] or boot['size'] <= 0 or root['size'] <= 0:
            raise ValueError('WIC boot/root partition geometry is invalid')
        ota_size = ota.stat().st_size
        if root['size'] * sector_size < ota_size:
            raise ValueError('WIC root partition is smaller than the OTA ext4 image')
        with image.open('rb') as candidate, ota.open('rb') as expected:
            candidate.seek(root['start'] * sector_size)
            while chunk := expected.read(1024 * 1024):
                if candidate.read(len(chunk)) != chunk:
                    raise ValueError('WIC root partition differs from OTA ext4')
        boot_image = pathlib.Path(directory) / 'boot.vfat'
        with image.open('rb') as candidate, boot_image.open('wb') as output:
            candidate.seek(boot['start'] * sector_size)
            remaining = boot['size'] * sector_size
            while remaining:
                chunk = candidate.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise ValueError('WIC boot partition is truncated')
                output.write(chunk)
                remaining -= len(chunk)
        check = subprocess.run(['fsck.vfat', '-n', str(boot_image)],
                               capture_output=True, text=True, check=False)
        if check.returncode:
            raise ValueError(f'WIC boot FAT check failed: {check.stdout.strip()}')
    print(f'WIC boot FAT and OTA root copy: verified in {wic_gz}')


def verify_rootfs(rootfs, provider):
    required = tuple(path.lstrip('/') for path in artifact_files(provider))
    missing = [path for path in required if not (rootfs / path).is_file()]
    if missing:
        raise ValueError(f'rootfs missing files: {missing}')
    unit_paths = (
        rootfs / 'lib/systemd/system/dd-kiosk-browser.service',
        rootfs / 'usr/lib/systemd/system/dd-kiosk-browser.service',
    )
    unit_path = next((path for path in unit_paths if path.is_file()), None)
    if unit_path is None:
        raise ValueError('rootfs lacks dd-kiosk-browser.service')
    service = unit_path.read_text()
    if 'User=weston' not in service or 'StateDirectory=dd-kiosk-browser' not in service:
        raise ValueError('rootfs kiosk service lacks Weston ownership or writable state')
    if 'Restart=always' not in service or 'After=weston.service' not in service:
        raise ValueError('rootfs kiosk service lacks restart or compositor ordering')
    enabled = rootfs / 'etc/systemd/system/multi-user.target.wants/dd-kiosk-browser.service'
    if not enabled.is_symlink():
        raise ValueError('rootfs kiosk service is not enabled for startup')
    launcher = (rootfs / 'usr/bin/dd-kiosk-browser').read_text()
    provider_flags = {
        'chromium': ('--ozone-platform=wayland', '--kiosk'),
        'cog': ('--platform=wl', '--webprocess-failure=restart'),
    }
    for flag in provider_flags[provider]:
        if flag not in launcher:
            raise ValueError(
                f'rootfs {provider} launcher lacks required flag {flag}'
            )
    if '--disable-gpu' in launcher:
        raise ValueError('rootfs kiosk launcher disables GPU acceleration')
    linker_guard = (rootfs / 'usr/libexec/dd-kiosk-linker-guard').read_text()
    for contract in ('kiosk-audio-hotpatch.conf', 'zz-audio-hotpatch.conf',
                     '/sbin/ldconfig', '/ostree/deploy/'):
        if contract not in linker_guard:
            raise ValueError(f'rootfs linker guard lacks migration contract {contract}')
    native_runtime = (rootfs / 'usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzz-native-runtime.conf').read_text()
    if 'UnsetEnvironment=LD_LIBRARY_PATH' not in native_runtime:
        raise ValueError('rootfs kiosk runtime does not clear legacy library overrides')
    weston_guard = (rootfs / 'usr/lib/systemd/system/weston.service.d/zzzz-kiosk-linker-guard.conf').read_text()
    if 'ExecStartPre=+/usr/libexec/dd-kiosk-linker-guard' not in weston_guard:
        raise ValueError('rootfs Weston service does not gate mixed-deployment linkage')
    environment = (rootfs / 'etc/default/dd-kiosk-browser').read_text()
    if 'DD_KIOSK_URL=https://active-esl.com' not in environment:
        raise ValueError('rootfs kiosk URL is not https://active-esl.com')
    weston = (rootfs / 'etc/xdg/weston/weston-screen.ini').read_text()
    if 'shell=kiosk-shell.so' not in weston:
        raise ValueError('rootfs Weston config does not select kiosk shell')
    if 'transform=rotate-90' not in weston:
        raise ValueError('rootfs Weston config lacks candidate panel transform')
    weston_service = (rootfs / 'etc/systemd/system/weston.service.d/screen.conf').read_text()
    if '--config=/etc/xdg/weston/weston-screen.ini' not in weston_service:
        raise ValueError('rootfs Weston service does not select candidate screen config')
    if not any(path.is_file() for path in rootfs.rglob('kiosk-shell.so')):
        raise ValueError('rootfs lacks Weston kiosk-shell.so module')
    audio = (rootfs / 'usr/lib/systemd/system/dd-kiosk-browser.service.d/audio.conf').read_text()
    for contract in ('After=pulseaudio.service',
                     'PULSE_SERVER=unix:/tmp/pulseaudio.socket'):
        if contract not in audio:
            raise ValueError(f'rootfs kiosk audio drop-in lacks {contract}')
    asound = (rootfs / 'etc/asound.conf').read_text()
    if 'tas2555audio' not in asound or 'rate 48000' not in asound:
        raise ValueError('rootfs ALSA default is not the Jaguar Screen TAS2555 card')

    if provider == 'chromium':
        policy_path = rootfs / 'etc/chromium/policies/managed/dd-kiosk-browser.json'
        policy = json.loads(policy_path.read_text())
        expected_policy = {
            'AllowFileSelectionDialogs': False,
            'BrowserAddPersonEnabled': False,
            'BrowserGuestModeEnabled': False,
            'BrowserSignin': 0,
            'DeveloperToolsAvailability': 2,
            'DownloadRestrictions': 3,
            'ExtensionInstallBlocklist': ['*'],
            'IncognitoModeAvailability': 1,
            'PrintingEnabled': False,
            'URLBlocklist': ['view-source:*'],
        }
        for name, value in expected_policy.items():
            if policy.get(name) != value:
                raise ValueError(
                    f'rootfs Chromium policy {name} does not match kiosk contract'
                )

    executables = ('usr/bin/dd-kiosk-browser',
                   'etc/NetworkManager/dispatcher.d/90-dd-kiosk-browser',
                   f'usr/bin/{"chromium" if provider == "chromium" else "cog"}')
    for executable in executables:
        if not (rootfs / executable).stat().st_mode & 0o111:
            raise ValueError(f'rootfs file is not executable: {executable}')
    print(f'rootfs {provider} payload and kiosk service: verified at {rootfs}')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('candidate_manifest', type=pathlib.Path)
    p.add_argument('candidate_wic_gz', type=pathlib.Path)
    p.add_argument('--baseline-manifest', type=pathlib.Path, required=True)
    p.add_argument('--baseline-wic-gz-bytes', type=int, required=True)
    p.add_argument('--baseline-ota-ext4-gz-bytes', type=int, required=True)
    p.add_argument('--baseline-ota-tar-xz-bytes', type=int, required=True)
    p.add_argument('--ota-ext4-gz', type=pathlib.Path, required=True)
    p.add_argument('--ota-tar-xz', type=pathlib.Path, required=True)
    p.add_argument('--rootfs', type=pathlib.Path, required=True,
                   help='BitBake image rootfs directory to inspect installed files')
    p.add_argument('--ostree-tool', type=pathlib.Path,
                   default=shutil.which('ostree'),
                   help='OSTree executable used to inspect the OTA repository')
    args = p.parse_args()
    for name in ('baseline_wic_gz_bytes', 'baseline_ota_ext4_gz_bytes',
                 'baseline_ota_tar_xz_bytes'):
        if getattr(args, name) <= 0:
            p.error(f'--{name.replace("_", "-")} must be positive')
    if not args.rootfs.is_dir():
        p.error(f'--rootfs does not name a directory: {args.rootfs}')
    candidate = packages(args.candidate_manifest)
    baseline = packages(args.baseline_manifest)
    try:
        provider = kiosk_provider(candidate)
        verify_rootfs(args.rootfs, provider)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    if not args.candidate_wic_gz.name.endswith('.wic.gz'):
        p.error('candidate_wic_gz must be a .wic.gz image artifact')
    if not args.ota_ext4_gz.name.endswith('.ota-ext4.gz'):
        p.error('--ota-ext4-gz must name a .ota-ext4.gz artifact')
    if not args.ota_tar_xz.name.endswith('.ota.tar.xz'):
        p.error('--ota-tar-xz must name a .ota.tar.xz artifact')
    for artifact, opener, label in (
        (args.candidate_wic_gz, gzip.open, 'WIC gzip'),
        (args.ota_ext4_gz, gzip.open, 'OTA ext4 gzip'),
        (args.ota_tar_xz, lzma.open, 'OTA tar xz'),
    ):
        try:
            verify_compressed(artifact, opener, label)
        except ValueError as exc:
            p.error(str(exc))
    try:
        deployments = verify_ota_ext4(args.ota_ext4_gz, provider)
        verify_ota_tar(args.ota_tar_xz, deployments, provider, args.ostree_tool)
        verify_wic_partitions(args.candidate_wic_gz, args.ota_ext4_gz)
    except (ValueError, OSError, tarfile.TarError) as exc:
        p.error(str(exc))
    required = required_packages(provider)
    missing = sorted(required - candidate)
    forbidden = sorted(forbidden_packages(candidate, provider))
    size = args.candidate_wic_gz.stat().st_size
    delta = size - args.baseline_wic_gz_bytes
    print(f'kiosk provider: {provider}')
    print(f'candidate packages: {len(candidate)}; deployed baseline: {len(baseline)}')
    print(f'added: {len(candidate - baseline)}; removed: {len(baseline - candidate)}')
    print(f'WIC gzip: {size:,} bytes; deployed baseline: {args.baseline_wic_gz_bytes:,} bytes; delta: {delta:+,} bytes ({delta / args.baseline_wic_gz_bytes:+.1%})')
    print(f'WIC SHA-256: {sha256(args.candidate_wic_gz)}')
    for label, artifact, baseline_bytes in (
        ('OTA ext4 gzip', args.ota_ext4_gz, args.baseline_ota_ext4_gz_bytes),
        ('OTA tar xz', args.ota_tar_xz, args.baseline_ota_tar_xz_bytes),
    ):
        if artifact is not None:
            artifact_size = artifact.stat().st_size
            artifact_delta = artifact_size - baseline_bytes
            print(f'{label}: {artifact.name}; {artifact_size:,} bytes; deployed baseline: {baseline_bytes:,} bytes; delta: {artifact_delta:+,} bytes ({artifact_delta / baseline_bytes:+.1%})')
            print(f'{label} SHA-256: {sha256(artifact)}')
    print('required missing:', missing or 'none')
    print('forbidden payload:', forbidden or 'none')
    return 1 if missing or forbidden else 0


if __name__ == '__main__':
    sys.exit(main())
