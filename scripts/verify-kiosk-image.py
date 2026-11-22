#!/usr/bin/env python3
"""Validate one completed kiosk image against the deployed screen baseline."""
import argparse
import fnmatch
import functools
import gzip
import hashlib
import json
import lzma
import pathlib
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile

REQUIRED = {'chromium-ozone-wayland', 'dd-kiosk-browser', 'weston',
            'networkmanager-daemon', 'packagegroup-dd-kiosk-browser',
            'jaguar-screen-touch', 'jaguar-touch-test'}
JAGUAR_START_URL = 'https://www.youtube.com/watch?v=nfWlot6h_JM&autoplay=1&mute=1&loop=1&playlist=nfWlot6h_JM'
JAGUAR_TOUCH_FILES = (
    '/etc/udev/rules.d/99-jaguar-screen-touch.rules',
    '/usr/share/jaguar-touch-test/index.html',
    '/usr/bin/jaguar-touch-test',
)
FORBIDDEN_PREFIXES = (
    'waydroid', 'packagegroup-dd-android-container',
    'screen-flutter-demo', 'flutter', 'libflutter',
    'packagegroup-dd-flutter', 'ivi-homescreen',
    'godot', 'screen-godot-smoke', 'screen-aero-demo',
)
ARTIFACT_FILES = JAGUAR_TOUCH_FILES + (
    '/usr/bin/chromium',
    '/usr/bin/dd-kiosk-browser',
    '/usr/libexec/dd-kiosk-linker-guard',
    '/usr/libexec/dd-screen-weston',
    '/etc/default/dd-kiosk-browser',
    '/etc/chromium/policies/managed/dd-kiosk-browser.json',
    '/etc/NetworkManager/dispatcher.d/90-dd-kiosk-browser',
    '/etc/xdg/weston/weston-screen.ini',
    '/etc/systemd/system/weston.service.d/screen.conf',
    '/usr/share/dd-kiosk-browser/offline.html',
    '/usr/lib/systemd/system/weston.service.d/zzzz-kiosk-linker-guard.conf',
    '/usr/lib/systemd/system/weston.service.d/zzzzzz-screen-etnaviv.conf',
    '/usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzz-native-runtime.conf',
    '/usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzzzz-screen-etnaviv-context.conf',
    '/etc/systemd/system/multi-user.target.wants/dd-kiosk-browser.service',
)
ARTIFACT_EXECUTABLES = {
    '/usr/bin/jaguar-touch-test',
    '/usr/bin/chromium',
    '/usr/bin/dd-kiosk-browser',
    '/usr/libexec/dd-kiosk-linker-guard',
    '/usr/libexec/dd-screen-weston',
    '/etc/NetworkManager/dispatcher.d/90-dd-kiosk-browser',
}
DISPLAY_MODULES = {
    'gl-renderer.so': ('/usr/lib*/libweston-*/gl-renderer.so',),
    'kiosk-shell.so': ('/usr/lib*/weston*/kiosk-shell.so',
                       '/usr/lib*/libweston-*/kiosk-shell.so'),
}
KIOSK_ENABLEMENT = '/etc/systemd/system/multi-user.target.wants/dd-kiosk-browser.service'
KIOSK_CONTENTS = {
    '/usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzzzz-screen-etnaviv-context.conf': ('Environment=DD_KIOSK_GLES2_COMPAT=1',),
    '/usr/bin/dd-kiosk-browser': ('--ozone-platform=wayland', '--kiosk'),
    '/usr/libexec/dd-kiosk-linker-guard': ('kiosk-audio-hotpatch.conf', 'zz-audio-hotpatch.conf', '/sbin/ldconfig', '/ostree/deploy/'),
    '/usr/lib/systemd/system/dd-kiosk-browser.service.d/zzzz-native-runtime.conf': ('UnsetEnvironment=LD_LIBRARY_PATH',),
    '/usr/lib/systemd/system/weston.service.d/zzzz-kiosk-linker-guard.conf': ('ExecStartPre=+/usr/libexec/dd-kiosk-linker-guard',),
    '/etc/systemd/system/weston.service.d/screen.conf': ('--config=/etc/xdg/weston/weston-screen.ini',),
}
CHROMIUM_POLICY = {
    'AllowFileSelectionDialogs': False, 'BrowserAddPersonEnabled': False,
    'BrowserGuestModeEnabled': False, 'BrowserSignin': 0,
    'DeveloperToolsAvailability': 2, 'DownloadRestrictions': 3,
    'ExtensionInstallBlocklist': ['*'], 'IncognitoModeAvailability': 1,
    'PrintingEnabled': False, 'URLBlocklist': ['view-source:*'],
}


def unit_settings(contents):
    """Parse active unit assignments; reject syntax we cannot interpret safely."""
    section = None
    result = {}
    logical = ''
    for line in contents.splitlines():
        line = line.strip()
        if not line or line.startswith(('#', ';')):
            continue
        logical += line
        if len(logical) - len(logical.rstrip('\\')) & 1:
            logical = logical[:-1] + ' '
            continue
        line, logical = logical, ''
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
            continue
        if section is None or '=' not in line:
            raise ValueError('image kiosk unit has unsupported syntax')
        key, value = line.split('=', 1)
        if '\\' in value or '%' in value:
            raise ValueError('image kiosk unit has unqualified escaping or specifiers')
        result.setdefault((section, key.strip()), []).append(value.strip())
    if logical:
        raise ValueError('image kiosk unit has unfinished continuation')
    return result


def verify_effective_kiosk_unit(deployment, file, entry, read, listdir, unit):
    """Fail closed on unrecognised overrides instead of guessing systemd policy.

    Only shipped kiosk drop-ins are admitted. Global, dash-prefix,
    runtime and administrator overrides must be qualified before acceptance.
    Directory traversal and symlinks use the same image-contained resolver as
    the payload reads, including when the image uses /lib -> /usr/lib.
    """
    roots = ('/etc/systemd/system.control', '/run/systemd/system.control',
             '/run/systemd/transient', '/run/systemd/generator.early',
             '/etc/systemd/system', '/etc/systemd/system.attached',
             '/run/systemd/system', '/run/systemd/system.attached',
             '/run/systemd/generator',
             '/usr/local/lib/systemd/system', '/usr/lib/systemd/system',
             '/lib/systemd/system', '/run/systemd/generator.late')
    dropins = ('service.d', 'dd-.service.d', 'dd-kiosk-.service.d',
               'dd-kiosk-browser.service.d')
    expected = {
        file('/usr/lib/systemd/system/dd-kiosk-browser.service.d/' + name)
        for name in ('zzzz-native-runtime.conf', 'zzzzzz-screen-etnaviv-context.conf')}
    audio_contracts = {
        'audio.conf': {('Unit', 'After'): ['pulseaudio.service'],
                       ('Unit', 'Wants'): ['pulseaudio.service'],
                       ('Service', 'SupplementaryGroups'): ['render video audio'],
                       ('Service', 'Environment'): ['PULSE_SERVER=unix:/tmp/pulseaudio.socket']},
        'screen-audio.conf': {('Service', 'Environment'): [
            'PULSE_SINK=alsa_output.platform-sound-tas2555.stereo-fallback']},
    }
    optional = {}
    for name, contract in audio_contracts.items():
        path = '/usr/lib/systemd/system/dd-kiosk-browser.service.d/' + name
        parent = resolve_artifact_file(deployment, str(pathlib.PurePosixPath(path).parent), entry, directory=True)
        if entry(parent + '/' + name) is not None:
            resolved = file(path)
            if unit_settings(read(resolved)) != contract:
                raise ValueError('image kiosk service has an unqualified audio drop-in')
            optional[resolved] = contract
    found = set()
    for root in roots:
        for directory in ('', *dropins):
            path = root + ('/' + directory if directory else '')
            # Probe one resolved component at a time: never follow host parents.
            current = deployment.rstrip('/')
            for component in path.strip('/').split('/'):
                candidate = current + '/' + component
                if entry(candidate) is None:
                    break
                relative = candidate[len(deployment.rstrip('/')):]
                current = resolve_artifact_file(deployment, relative, entry, directory=True)
            else:
                names = listdir(current)
                if not directory:
                    if 'dd-kiosk-browser.service' in names:
                        if file(root + '/dd-kiosk-browser.service') != unit:
                            raise ValueError('image kiosk service has an unqualified unit override')
                    continue
                for name in names:
                    if not name.endswith('.conf'):
                        continue
                    resolved = file(path + '/' + name)
                    if directory != 'dd-kiosk-browser.service.d' or resolved not in expected | optional.keys():
                        raise ValueError('image kiosk service has an unqualified drop-in: ' + path + '/' + name)
                    found.add(resolved)
    if not expected <= found:
        raise ValueError('image kiosk service lacks its runtime drop-ins')
    settings = unit_settings(read(unit))
    supported = {
        'Unit': {'Description', 'After', 'Wants', 'Conflicts', 'StartLimitIntervalSec'},
        'Service': {'Type', 'User', 'Group', 'SupplementaryGroups', 'StateDirectory',
                    'EnvironmentFile', 'ExecStart', 'Restart', 'RestartSec',
                    'Environment', 'UnsetEnvironment'},
        'Install': {'WantedBy'},
    }
    if any(key not in supported.get(section, set()) for section, key in settings):
        raise ValueError('image kiosk service has unqualified unit directives')
    for name in sorted(found, key=lambda path: pathlib.PurePosixPath(path).name):
        for key, values in unit_settings(read(name)).items():
            if name not in optional and key not in (('Service', 'Environment'), ('Service', 'UnsetEnvironment'), ('Service', 'ExecStart')):
                raise ValueError('image kiosk runtime drop-in has unsupported directives')
            settings.setdefault(key, []).extend(values)
    def scalar(section, key, expected_value):
        values = settings.get((section, key), [])
        if not values or values[-1] != expected_value:
            raise ValueError(f'image kiosk service lacks effective {key}={expected_value}')
    def words(section, key):
        result = []
        for value in settings.get((section, key), []):
            if not value:
                result = []
            else:
                result.extend(shlex.split(value))
        return result
    for key, value in {'User': 'weston', 'Group': 'weston',
                       'Restart': 'always', 'Type': 'simple'}.items():
        scalar('Service', key, value)
    for key, value in {'ExecStart': ['/usr/bin/dd-kiosk-browser'],
                       'StateDirectory': ['dd-kiosk-browser'],
                       'EnvironmentFile': ['-/etc/default/dd-kiosk-browser']}.items():
        if words('Service', key) != value:
            raise ValueError('image kiosk service has incorrect effective ' + key)
    groups = {'render', 'video'}
    if any(pathlib.PurePosixPath(path).name == 'audio.conf' for path in optional):
        groups.add('audio')
    if set(words('Service', 'SupplementaryGroups')) != groups:
        raise ValueError('image kiosk service has incorrect effective SupplementaryGroups')
    if 'weston.service' not in words('Unit', 'After') or 'multi-user.target' not in words('Install', 'WantedBy'):
        raise ValueError('image kiosk service lacks boot ordering or target')
    environment = dict(value.split('=', 1) for value in words('Service', 'Environment'))
    unset = words('Service', 'UnsetEnvironment')
    if environment.get('DD_KIOSK_GLES2_COMPAT') != '1' or any(
            value in unset for value in ('DD_KIOSK_GLES2_COMPAT', 'DD_KIOSK_GLES2_COMPAT=1')):
        raise ValueError('image kiosk service lacks effective GLES2 context')
    if 'LD_LIBRARY_PATH' not in unset:
        raise ValueError('image kiosk service lacks native runtime environment guard')
    expected_environment = {'DD_KIOSK_GLES2_COMPAT': '1'}
    for contract in optional.values():
        for assignment in contract.get(('Service', 'Environment'), []):
            key, value = assignment.split('=', 1)
            expected_environment[key] = value
    if environment != expected_environment:
        raise ValueError('image kiosk service has unqualified environment assignments')


def verify_kiosk_policy(deployment, file, entry, read, expected_url, listdir):
    """Boot, graphics and service policy shared by all three image views."""
    parent = resolve_artifact_file(deployment, str(pathlib.PurePosixPath(KIOSK_ENABLEMENT).parent),
                                   entry, directory=True)
    enabled = entry(parent + '/' + pathlib.PurePosixPath(KIOSK_ENABLEMENT).name)
    if enabled is None or enabled[0] != 'symlink':
        raise ValueError('image kiosk service is not enabled by a symlink')
    enabled_file = file(KIOSK_ENABLEMENT)
    units = set()
    for name in ('/usr/lib/systemd/system/dd-kiosk-browser.service',
                 '/lib/systemd/system/dd-kiosk-browser.service'):
        try:
            units.add(file(name))
        except ValueError:
            continue
    if enabled_file not in units:
        raise ValueError('image enabled kiosk service does not resolve to its unit')
    verify_effective_kiosk_unit(deployment, file, entry, read, listdir, enabled_file)
    for name, settings in KIOSK_CONTENTS.items():
        content = read(file(name))
        if any(setting not in content for setting in settings):
            raise ValueError(f'image kiosk policy differs from expected content: {name}')
        if name == '/usr/bin/dd-kiosk-browser':
            commands = re.findall(r'^\s*exec /usr/bin/chromium\s+([^\n]*)', content.replace('\\\n', ' '), re.M)
            if len(commands) != 1:
                raise ValueError('image kiosk launcher lacks a unique Chromium exec')
            arguments = shlex.split(commands[0], comments=True)
            if not {'--ozone-platform=wayland', '--kiosk'} <= set(arguments) or '--disable-gpu' in arguments:
                raise ValueError('image kiosk launcher has incorrect active GPU/kiosk flags')
    policy = json.loads(read(file('/etc/chromium/policies/managed/dd-kiosk-browser.json')))
    for name, value in CHROMIUM_POLICY.items():
        if policy.get(name) != value:
            raise ValueError(f'image Chromium policy {name} differs from kiosk contract')
    verify_startup_environment(read(file('/etc/default/dd-kiosk-browser')), expected_url)


def display_matches(paths, patterns):
    return [name for name in paths if any(
        name.count('/') == pattern.count('/') and fnmatch.fnmatchcase(name, pattern)
        for pattern in patterns)]


def verify_display_payload(file, read, paths):
    """The same Weston boot contract for staging, ext4 and tar deployments."""
    try:
        vendor = file('/usr/lib/systemd/system/weston.service.d/zzzzzz-screen-etnaviv.conf')
    except ValueError as exc:
        raise ValueError('image lacks valid deployment-owned Etnaviv Weston override') from exc
    command = read(vendor)
    if '--use-g2d' in command or '--use-pixman' in command:
        raise ValueError('image Etnaviv Weston override selects a non-GL renderer')
    if 'ExecStart=\n' not in command or '--config=/etc/xdg/weston/weston-screen.ini' not in command:
        raise ValueError('image Etnaviv Weston override lacks command reset or screen config')
    for module, patterns in DISPLAY_MODULES.items():
        matches = display_matches(paths, patterns)
        if not matches:
            raise ValueError(f'image Weston lacks {module}')
        for name in matches:
            file(name)
    try:
        file('/usr/libexec/dd-screen-weston', executable=True)
    except ValueError as exc:
        raise ValueError('image Etnaviv Weston lacks executable dynamic display selector') from exc
    if 'ExecStart=/usr/libexec/dd-screen-weston ' not in command or '--drm-device=' in command:
        raise ValueError('image Etnaviv Weston lacks executable dynamic display selector')
    if display_matches(paths, ('/usr/lib*/libweston-*/g2d-renderer.so',)):
        raise ValueError('image Etnaviv Weston includes the NXP G2D renderer')
    weston = read(file('/etc/xdg/weston/weston-screen.ini'))
    if 'shell=kiosk-shell.so' not in weston or 'transform=rotate-90' not in weston:
        raise ValueError('image Weston config lacks kiosk shell or candidate panel transform')


def packages(path):
    result = set()
    for line in path.read_text().splitlines():
        if line.strip():
            result.add(line.split()[0])
    return result


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


def resolve_artifact_file(deployment, filename, entry, executable=False, directory=False):
    """Resolve a regular file inside its deployment, never against the host root."""
    pending = filename.lstrip('/').split('/')
    resolved = []
    links = 0
    while pending:
        component = pending.pop(0)
        if component in ('', '.'):
            continue
        if component == '..':
            if not resolved:
                raise ValueError(f'OTA file symlink escapes its deployment: {filename}')
            resolved.pop()
            continue
        name = '/'.join([deployment.rstrip('/'), *resolved, component])
        metadata = entry(name)
        if metadata is None:
            raise ValueError(f'OTA file has a missing path or symlink target: {name}')
        kind, mode, target = metadata
        if kind == 'symlink':
            links += 1
            # Linux pathname resolution permits at most 40 symlink traversals.
            if links > 40 or not target:
                raise ValueError(f'OTA file has a cyclic or invalid symlink: {filename}')
            if target.startswith('/'):
                resolved = []
            pending = target.split('/') + pending
        elif kind == 'directory':
            resolved.append(component)
        elif kind == 'regular' and not directory and not pending and (not executable or mode & 0o111):
            return name
        else:
            raise ValueError(f'OTA file is not a regular {"executable" if executable else "file"}: {name}')
    if directory:
        return '/'.join([deployment.rstrip('/'), *resolved])
    raise ValueError(f'OTA file resolves to a directory: {filename}')


def verify_artifact_payload(deployment, entry, read, expected_url, paths, listdir):
    for name in ARTIFACT_FILES:
        resolve_artifact_file(
            deployment, name, entry, executable=name in ARTIFACT_EXECUTABLES)
    file = lambda name, executable=False: resolve_artifact_file(deployment, name, entry, executable)
    verify_kiosk_policy(deployment, file, entry, read, expected_url, listdir)
    verify_display_payload(
        file, read, paths)


def verify_ota_ext4(path, expected_url=JAGUAR_START_URL):
    """Inspect the shipped filesystem, not only BitBake's staging rootfs."""
    if shutil.which('debugfs') is None:
        raise ValueError('debugfs is required to inspect the OTA ext4 artifact')

    def debugfs(image, command):
        return subprocess.run(
            ['debugfs', '-R', command, str(image)],
            capture_output=True, text=True, check=False,
        )

    @functools.cache
    def entries(image, directory):
        result = debugfs(image, f'ls -p {directory}')
        if result.returncode or 'File not found' in result.stderr:
            raise ValueError(f'OTA ext4 missing directory {directory}')
        return [fields[5] for line in result.stdout.splitlines()
                if len(fields := line.split('/')) > 5 and fields[5] not in ('.', '..')]

    def quote(name):
        return '"' + name.replace('\\', '\\\\').replace('"', '\\"') + '"'

    @functools.cache
    def read(image, name):
        contents = debugfs(image, f'cat {quote(name)}')
        if contents.returncode or contents.stderr.strip().splitlines()[1:]:
            raise ValueError(f'cannot read OTA file: {name}')
        return contents.stdout

    @functools.cache
    def entry(image, name):
        result = debugfs(image, f'stat {quote(name)}')
        match = re.search(r'Type:\s+(\S+)\s+Mode:\s+([0-7]+)', result.stdout)
        if result.returncode or match is None:
            return None
        kind, mode = match.groups()
        target = None
        if kind == 'symlink':
            fast = re.search(r'^Fast link dest: "(.*)"$', result.stdout, re.M)
            if fast:
                target = fast[1]
            else:
                target = read(image, name)
        return kind, int(mode, 8), target

    with tempfile.TemporaryDirectory(prefix='dd-kiosk-ext4-') as directory:
        image = pathlib.Path(directory) / 'ota.ext4'
        with gzip.open(path, 'rb') as compressed, image.open('wb') as output:
            shutil.copyfileobj(compressed, output, 1024 * 1024)
        deployments = []
        for osname in entries(image, '/ostree/deploy'):
            deploy_dir = f'/ostree/deploy/{osname}/deploy'
            for checkout in entries(image, deploy_dir):
                if re.fullmatch(r'.+\.\d+', checkout):
                    deployments.append(f'{deploy_dir}/{checkout}')
        if not deployments:
            raise ValueError('OTA ext4 has no OSTree deployment checkout')
        for deployment in deployments:
            paths = []
            for library in entries(image, deployment + '/usr'):
                library_path = deployment + '/usr/' + library
                if not library.startswith('lib') or (entry(image, library_path) or (None,))[0] != 'directory':
                    continue
                for module_dir in entries(image, library_path):
                    if not (module_dir.startswith('libweston-') or module_dir.startswith('weston')):
                        continue
                    module_path = library_path + '/' + module_dir
                    if (entry(image, module_path) or (None,))[0] != 'directory':
                        continue
                    paths.extend('/usr/' + library + '/' + module_dir + '/' + name
                                 for name in entries(image, module_path))
            verify_artifact_payload(deployment, lambda name: entry(image, name),
                                    lambda name: read(image, name), expected_url, paths,
                                    lambda name: entries(image, quote(name)))
    print(f'OTA ext4 kiosk payload: verified in {len(deployments)} deployment(s) of {path}')
    return {deployment.lstrip('/') for deployment in deployments}


def verify_ota_tar(path, deployments, expected_url=JAGUAR_START_URL):
    """Check the separate OTA tar ships the same named deployment payload."""
    metadata = {}
    members = {}
    tar_deployments = set()
    deployment_pattern = re.compile(r'^(ostree/deploy/[^/]+/deploy/[^/]+\.\d+)(?:/|$)')
    with tarfile.open(path, mode='r:xz') as archive:
        for member in archive:
            parts = pathlib.PurePosixPath(member.name)
            if parts.is_absolute() or '..' in parts.parts:
                raise ValueError(f'OTA tar contains an unsafe path: {member.name}')
            name = str(parts)
            # Keep only deployment metadata; never extract untrusted archive paths.
            match = deployment_pattern.match(name)
            if match:
                deployment = match[1]
                tar_deployments.add(deployment)
                if name == deployment and not member.isdir():
                    raise ValueError(f'OTA tar deployment root is not a directory: {name}')
                kind = ('regular' if member.isfile() else 'symlink' if member.issym()
                        else 'directory' if member.isdir() else 'other')
                if name in metadata:
                    raise ValueError(f'OTA tar contains duplicate deployment path: {name}')
                metadata[name] = (kind, member.mode, member.linkname)
                members[name] = member
        if not tar_deployments or tar_deployments != set(deployments):
            raise ValueError(f'OTA tar deployments differ from ext4: '
                             f'missing={sorted(set(deployments) - tar_deployments)}, '
                             f'unexpected={sorted(tar_deployments - set(deployments))}')
        # Tar permits omitted directory headers; children imply those directories.
        for name in list(metadata):
            for parent in pathlib.PurePosixPath(name).parents:
                metadata.setdefault(str(parent), ('directory', 0o755, None))

        def read(name):
            with archive.extractfile(members[name]) as contents:
                return contents.read().decode('utf-8')

        for deployment in tar_deployments:
            paths = [name[len(deployment):] for name in metadata
                     if name.startswith(deployment + '/')]
            verify_artifact_payload(deployment, metadata.get, read, expected_url, paths,
                                    lambda directory: [name[len(directory) + 1:] for name in metadata
                                                       if name.startswith(directory + '/') and '/' not in name[len(directory) + 1:]])
    print(f'OTA tar kiosk payload: verified in {len(deployments)} deployment(s) of {path}')


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


def verify_etnaviv_weston(rootfs):
    """Reject stale G2D launchers and a missing GL runtime in the candidate."""
    patterns = tuple(pattern for values in DISPLAY_MODULES.values() for pattern in values)
    patterns += ('/usr/lib*/libweston-*/g2d-renderer.so',)
    paths = ['/' + str(path.relative_to(rootfs)) for pattern in patterns
             for path in rootfs.glob(pattern.lstrip('/'))]
    verify_display_payload(lambda name, executable=False: rootfs_file(rootfs, name, executable),
                           lambda path: path.read_text(), paths)


def verify_startup_url(rootfs, expected_url):
    environment = rootfs_file(rootfs, '/etc/default/dd-kiosk-browser').read_text()
    verify_startup_environment(environment, expected_url)


def verify_startup_environment(environment, expected_url):
    expected = {'DD_KIOSK_URL': expected_url, 'DD_KIOSK_MUTE_AUDIO': '1',
                'DD_KIOSK_GLES2_COMPAT': '1'}
    configured = {}
    for line in environment.splitlines():
        key, separator, value = line.strip().partition('=')
        if separator and key in expected:
            parts = shlex.split(value, comments=False)
            if len(parts) != 1:
                raise ValueError(f'kiosk environment {key} is missing or malformed')
            configured[key] = parts[0]
    if configured.get('DD_KIOSK_URL') != expected_url:
        raise ValueError(f'kiosk URL differs from expected URL: {expected_url}')
    for key, value in expected.items():
        if configured.get(key) != value:
            raise ValueError(f'kiosk environment requires {key}={value}')


def rootfs_entry(name):
    path = pathlib.Path(name)
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return None
    kind = ('regular' if stat.S_ISREG(mode) else 'directory' if stat.S_ISDIR(mode)
            else 'symlink' if stat.S_ISLNK(mode) else 'other')
    return kind, mode, str(path.readlink()) if kind == 'symlink' else None


def rootfs_file(rootfs, name, executable=False):
    """Return a real image file with image-rooted symlink semantics."""
    return pathlib.Path(resolve_artifact_file(str(rootfs.resolve()), name, rootfs_entry, executable))


def verify_jaguar_touch(rootfs):
    for name in JAGUAR_TOUCH_FILES:
        try:
            rootfs_file(rootfs, name, executable=name in ARTIFACT_EXECUTABLES)
        except ValueError as exc:
            raise ValueError(f'rootfs missing Jaguar touch payload or invalid file: {name}: {exc}') from exc


def verify_rootfs(rootfs, expected_url=JAGUAR_START_URL):
    verify_etnaviv_weston(rootfs)
    verify_jaguar_touch(rootfs)
    for name in ARTIFACT_FILES:
        rootfs_file(rootfs, name, executable=name in ARTIFACT_EXECUTABLES)
    verify_kiosk_policy(
        str(rootfs.resolve()),
        lambda name, executable=False: rootfs_file(rootfs, name, executable),
        rootfs_entry, lambda path: path.read_text(), expected_url,
        lambda directory: [path.name for path in pathlib.Path(directory).iterdir()])
    print(f'rootfs payload and kiosk service: verified at {rootfs}')


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
    p.add_argument('--expected-url', default=JAGUAR_START_URL,
                   help='Expected configured startup URL; defaults to Jaguar Screen silent YouTube autoplay/loop')
    args = p.parse_args()
    for name in ('baseline_wic_gz_bytes', 'baseline_ota_ext4_gz_bytes',
                 'baseline_ota_tar_xz_bytes'):
        if getattr(args, name) <= 0:
            p.error(f'--{name.replace("_", "-")} must be positive')
    if not args.rootfs.is_dir():
        p.error(f'--rootfs does not name a directory: {args.rootfs}')
    try:
        verify_rootfs(args.rootfs, args.expected_url)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    candidate = packages(args.candidate_manifest)
    baseline = packages(args.baseline_manifest)
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
        deployments = verify_ota_ext4(args.ota_ext4_gz, args.expected_url)
        verify_ota_tar(args.ota_tar_xz, deployments, args.expected_url)
        verify_wic_partitions(args.candidate_wic_gz, args.ota_ext4_gz)
    except (ValueError, OSError, tarfile.TarError) as exc:
        p.error(str(exc))
    missing = sorted(REQUIRED - candidate)
    forbidden = sorted(x for x in candidate if x.startswith(FORBIDDEN_PREFIXES))
    size = args.candidate_wic_gz.stat().st_size
    delta = size - args.baseline_wic_gz_bytes
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
