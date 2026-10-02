# Jaguar Screen Cog kiosk acceptance

This record applies to `imx8mm-jaguar-screen` with:

```bitbake
DD_PRODUCT_FEATURES = "kiosk-cog audio"
```

Cog acceptance is independent of Chromium acceptance. A successful parse,
runtime-package task or WPE WebKit configure task does not count as a browser
build or hardware result. Keep the exact manifest, distro and BSP commits,
artifact hashes, OSTree deployment and observed board evidence together.

WebKitGTK `MiniBrowser` remains deferred until every required Cog gate below is
complete. It must not be introduced as a substitute for an incomplete Cog
build or board test.

## Build and artifact record

| Evidence | Value / result |
| --- | --- |
| `meta-webkit` revision | `2d29669a3d78e462276044f3f8bde0e4dec33696` (`scarthgap`) |
| Cog / WPE WebKit | Cog `0.18.5`; WPE WebKit `2.46.7` |
| Existing Chromium tuple isolation | Passed: no WebKit collection, recipes or appends; Chromium packagegroup unchanged |
| Cog metadata selection | Passed: Wayland Cog and `dd-kiosk-cog` selected |
| `wpewebkit:do_configure` | Passed: 2,549 tasks, all successful |
| Final `dd-kiosk-cog` payload | Passed inside the successful factory image build |
| Full `bitbake cog` | Passed |
| Intermediate `kiosk-cog audio` image | Build passed: 10,158 tasks, all successful; WIC and OTA tasks completed |
| Intermediate manifest | `lmp-factory-image-imx8mm-jaguar-screen-20261001175921.manifest`; 117,907 bytes; SHA-256 `0d71afa7dae3f7c1c6622cb0b40a091021c5b3d1127b472aa41adc20d6574591` |
| Intermediate WIC gzip | 462,546,487 bytes; SHA-256 `66aa3f8f2db97d330cd274c42457c88220b1e7da6a86e199a92ea1204ed3aabd` |
| Intermediate OTA ext4 gzip | 461,604,929 bytes; SHA-256 `b0e6687ce086ea1c1dd4eb105254daea9bcb6cb0e62e719be3d97a8f24bdf4fe` |
| Intermediate OTA tar.xz | 331,897,412 bytes; SHA-256 `62e4f31e52f04fdf57cdfbd48c3e0478ccdbb8e6f09c3472714f997a8d26f72f` |
| `scripts/verify-kiosk-image.py` | Correctly failed: rootfs ALSA default was not `tas2555audio`; artifact is not a deployment candidate |
| Exact-manifest TAS2555 component proof | Passed with a temporary feature override: 1,005 tasks, all successful; module package QA and Screen kernel/DT dependencies included |
| DEV ROM1 Cog/audio image | `20261002135738`; 10,175 tasks attempted, all successful; OSTree `24ceffd0d1225ca9b6dcee34c7eadfc339427ac43a9e04fe1f6a363ade1c357e` |
| DEV manifest | 118,035 bytes; SHA-256 `17017e1e46a570e4f4878d9f93dbb1d6278949ab7d9711ad358a6f44c1553485` |
| DEV WIC gzip | 462,568,423 bytes; SHA-256 `54db1450a41dcc804f3ff40d46a5023c82544d2164363b16de798cbeb37efe1d`; +4.2% against deployed target 2945 |
| DEV OTA ext4 gzip | 461,626,856 bytes; SHA-256 `5106df888e982b2b77b47b37dd32489ff04e22ea84eaab7cad7b7b8636a05a2d`; +4.3% |
| DEV OTA tar.xz | 331,716,340 bytes; SHA-256 `784519267fd9205911431874ece77e273181c0a05e1f7267150a0b416b28a60f`; +14.2% |
| Final provider-aware verification | Passed: rootfs, OTA ext4 deployment, OTA OSTree commit, WIC boot FAT and byte-identical WIC/OTA root; required missing none, forbidden payload none |

The image verifier derives the browser provider from the package manifest. For
Cog it requires `cog`, `wpewebkit`, `dd-kiosk-cog`, Weston, NetworkManager and
the provider-neutral kiosk packagegroup, plus the shipped
`libWPEBackend-fdo-1.0.so.1` runtime artifact. It also verifies
the Wayland/restart flags, TAS2555 ALSA default, PulseAudio drop-in, linker
guard, service ownership, Weston kiosk shell and the payload inside both OTA
formats and the WIC root partition. The OTA tar is an OSTree object repository,
so the verifier resolves its refs and checks the committed tree, mapping
deployment `/etc` content to OSTree's `/usr/etc`. Chromium policy is
deliberately not a Cog requirement.

The final DEV image proves the Cog/WPE WebKit integration and image construction
path with `tas2555 tas2555-rom1-dev`. The machine depends on the stable
`kernel-module-tas2555` recipe package, and the kernel-versioned split package
contains the module. Jaguar Screen's `/etc/asound.conf` is owned by
`alsa-state`, not either browser provider, and selects `tas2555audio` through a
48 kHz ALSA plug path. This avoids a package ownership clash and keeps physical
audio policy at the BSP boundary. It does not close audio acceptance: ROM1 is
unprotected, and no speaker-specific PPC3/uCDSP characterization or tuning has
been performed for the arbitrary 4 ohm development speaker.

The BSP now fail-closes this earlier than the external verifier: enabling the
`tas2555` machine feature adds a rootfs postprocess gate requiring non-empty
`/usr/lib/firmware/tas2555_uCDSP.bin`. Exact metadata validation proved the hook
is selected with the feature and absent from the saved feature-off Cog tuple.
This prevents another audio-labelled image from completing without the device
configuration while preserving existing-product isolation.

## Target record

The registered physical target is `imx8mm-jaguar-screen-2210a09dab86563`.
Before installation, record its hostname, factory/tag, active and rollback
deployments. After installation run:

```sh
scripts/check-kiosk-board.sh fio@BOARD_ADDRESS EXPECTED_OSTREE_SHA256
```

The script must identify `kiosk provider: cog`, find the Cog process with
`--platform=wl` and `--webprocess-failure=restart`, and pass the common
service, Wayland socket and mixed-deployment checks. This is only a read-only
smoke check; it does not prove visible output, touch, sound or video.

| Check | Required evidence | Result |
| --- | --- | --- |
| Boot | Candidate deployment selected; Weston and browser service active without restart loop | Pending |
| Render | Cog fills the rotated panel with no shell chrome, dialogs or blank regions | Pending |
| Physical touch | Michael or another bench operator checks centre, corners, tap and scroll on the real panel | Pending |
| Injected touch | Harness clones the deployed physical device axes and udev mapping; one capture-guided tap and swipe reach the intended controls | Pending |
| Audio | `tas2555audio` is the configured ALSA default; Pulse sink input and PCM become `RUNNING`; captured output follows play/pause/play without clipping | Pending |
| Video | A representative YouTube video autoplays fullscreen and sustains playback; retain Weston capture and dropped-frame/CPU observations | Pending |
| Network recovery | Loss may show a transient page, then the NetworkManager hook restarts Cog and reloads the URL after recovery | Pending |
| Web process failure | Terminating the WebKit web process exercises Cog's restart policy without leaving the kiosk | Pending |
| Service failure | Terminating Cog causes systemd to restart the provider without a prompt or browser chrome | Pending |
| Reboot | URL, orientation, touch mapping, audio and playback return after reboot | Pending |
| OTA / rollback | Candidate installs and boots; configuration survives; rollback remains bootable and free of cross-deployment library maps | Pending |

## Board-faithful capture and input

Use the `weston-browser-lab` standard workflow. Do not encode a known-good
rotation, calibration or coordinate transform in the harness. It must discover
the physical touch device, clone its kernel axis ranges and allowlisted udev
policy, and fail closed if the synthetic device does not receive the same
mapping.

```sh
LAB="$HOME/.codex/skills/weston-browser-lab/scripts/weston-board-lab.sh"

BOARD_ADDR=BOARD_ADDRESS EXPECTED_HOSTNAME=EXPECTED_HOSTNAME "$LAB" status
BOARD_ADDR=BOARD_ADDRESS EXPECTED_HOSTNAME=EXPECTED_HOSTNAME "$LAB" probe-touch
BOARD_ADDR=BOARD_ADDRESS EXPECTED_HOSTNAME=EXPECTED_HOSTNAME "$LAB" verify-touch-clone
BOARD_ADDR=BOARD_ADDRESS EXPECTED_HOSTNAME=EXPECTED_HOSTNAME "$LAB" capture /absolute/path/cog-before.png
BOARD_ADDR=BOARD_ADDRESS EXPECTED_HOSTNAME=EXPECTED_HOSTNAME "$LAB" tap-normalized X_PERMILLE Y_PERMILLE
BOARD_ADDR=BOARD_ADDRESS EXPECTED_HOSTNAME=EXPECTED_HOSTNAME "$LAB" capture /absolute/path/cog-after.png
BOARD_ADDR=BOARD_ADDRESS EXPECTED_HOSTNAME=EXPECTED_HOSTNAME "$LAB" record-touch 10 /absolute/path/cog-physical-touch.evtest.log
```

Screenshot capture requires the live Weston command line to include `--debug`.
That is a DEV-image capability and must not be hotpatched or remotely exposed
in PROD. Use capture → identify the exact control → inject → one verification
capture. Synthetic input exercises uinput, udev, libinput, Weston, Wayland and
Cog, but it does not prove the physical controller, bus, IRQ or kernel driver;
retain a physical corner/centre trace and human acceptance.

## Completion evidence

Acceptance requires one compact evidence bundle containing:

1. exact signed commits and manifest pins;
2. BitBake terminal summaries and image-verifier output;
3. artifact names, sizes and SHA-256 hashes;
4. expected and active OSTree deployment hashes;
5. provider-aware board smoke output;
6. one pre-action and one post-action Weston capture;
7. cloned-touch policy output plus a physical touch trace;
8. audio device, Pulse stream and DPX capture evidence;
9. sustained video observations;
10. reboot and OTA/rollback results.

Only after this evidence is complete may Cog be described as working on the
Jaguar Screen or MiniBrowser integration begin.
