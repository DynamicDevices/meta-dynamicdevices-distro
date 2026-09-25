# Jaguar Screen Chromium kiosk acceptance

This record applies to `imx8mm-jaguar-screen` with
`DD_PRODUCT_FEATURES = "kiosk-browser audio"`. Keep the exact manifest revision,
factory target, image checksums, and observed results together. A local parse
or recipe build does not count as hardware acceptance.

After the image build, run `scripts/verify-kiosk-image.py` with the candidate
package manifest, WIC gzip, both OTA artifacts, and the BitBake image rootfs.
It checks compressed-file integrity and SHA-256, package membership and size
against active target 2945, plus the installed Chromium binary, service,
policy, network hook, offline page, Weston kiosk shell, and panel transform.
The rootfs check inspects BitBake's staging tree. The verifier also decompresses
the OTA ext4 artifact and uses `debugfs` to confirm the kiosk files and service
are present in every OSTree deployment checkout in the shipped filesystem.
It also checks the WIC boot FAT and compares the WIC root partition byte for
byte with the verified OTA ext4. Inspect the actual boot files and
test both installation paths before hardware acceptance.

After installing the candidate, `scripts/check-kiosk-board.sh` provides a
read-only SSH smoke check for the expected OSTree SHA, Weston, the browser
service, NetworkManager, Chromium kiosk flags, managed policy, and Wayland
socket. Supply the board's current `fio@address` and the exact expected
64-character deployment SHA. This check does not prove visible rendering,
touch handling, network recovery, reboot, or OTA; record those separately.

## Build record

| Evidence | Value / result |
| --- | --- |
| Kiosk manifest commit | `ce04cfa7e6e9cf382114ee4a667c8962ec41e831` |
| Distro feature commit | `73d88d480886997845667a53f841988add78aaaf` |
| Jaguar Screen BSP commit | `36db9b8195d0e5cd098d5f1d73c19718d1a4db41` |
| Factory configuration commit | Pending |
| Chromium recipe version and layer commit | `chromium-ozone-wayland_147.0.7727.116.bb` at `85eeb6b50883d22c977396f5e8fe211a7961cf2e` |
| Feature contract negative parses | Separate BitBake parses rejected `kiosk-browser flutter`, kiosk on `imx8mm-jaguar-sentai` without `display-multimedia`, and unknown feature `bogus`; each exited 1 with the intended error |
| Exact changed-component preflight | `bitbake lmp-device-tree -c compile -f`: 871 tasks successful |
| Foundries platform target | `2998`, signed manifest `951a1a538cea6f1bc04fb06d71e7d9dcbe497754`, distro `97499cec6a151a9898ccdcea491a30d4e0757ee7`; startup validation entered the real container workload, so release-artifact proof remains pending |
| `bitbake chromium-ozone-wayland` | Exact `bitbake -e` preflight passed; target 2998 remains the release gate |
| `bitbake lmp-factory-image` | Pending target 2998 completion |
| WIC and OTA artifact names, SHA-256, bytes | Pending |
| Image manifest includes Chromium, launcher, Weston | Pending |
| Image manifest excludes Flutter, Godot, Waydroid payloads | Pending |
| Size delta against the matching screen base | Pending |
| Maintained tuple and recovery-image gates | Pending |

## Board record

The registered physical target is
`imx8mm-jaguar-screen-2210a09dab86563`. Before installing a test image,
confirm its hostname, current OSTree deployment and rollback entry, and the
factory/tag to which it is registered. The last read-only baseline observed
target `2945` (`d100cd3b1577a91a897f24befcc1d3e51c2b7639705c7315abb3f4fe13100b9e`)
with Weston active and target 2943 retained as rollback. This baseline is not
a kiosk test result.

| Check | Required evidence | Result |
| --- | --- | --- |
| Boot | New deployment selected; Weston and `dd-kiosk-browser` active without restart loop | Pending |
| Render | Fullscreen page fills the panel in the intended orientation; no browser chrome or dialogs | Pending |
| Touch | Tap, scroll and any required text input work; public input cannot leave the kiosk page | Pending |
| Audio | Chromium has a Pulse sink input, `wm8524audio` PCM is `RUNNING`, and a DPX play/pause/play capture follows the injected transition without clipping | Pending |
| Network loss | Remote test URL may show a transient error, but the service stays recoverable | Pending |
| Network return | NetworkManager dispatcher restarts Chromium and the configured URL loads | Pending |
| Browser crash | Killing Chromium causes systemd restart without a restore prompt | Pending |
| Reboot | URL, profile state and kiosk service return after power-cycle or reboot | Pending |
| OTA | New target installs and boots; URL/configuration survives; rollback path remains valid | Pending |

Record command output, screenshots, timestamps, and the resulting OSTree
deployment alongside each result. Check panel rotation and touch coordinates
together; the kiosk candidate currently uses the base `rotate-90` transform,
while a separate uncommitted screen edit uses `rotate-270`.

### 2026-09-24 development-board acceptance

The live development board was deliberately hotpatched before the source image
was available. Michael physically accepted the restored touchscreen mapping:
native `600x1024` controller geometry with X inversion. Chromium rendered a
Taylor Swift YouTube video fullscreen and sustained playback well; Michael
also accepted playback performance. The YouTube consent dialog was handled by
making keyboard focus visible in a screenshot and selecting the privacy-safe
`Reject all` choice, followed by one verification capture.

This is strong bench evidence for the source fix and browser runtime, but it is
not OTA/image acceptance. Keep the reversible hotpatch until target 2998 has
passed, its exact artifacts and source pins have been verified, and the signed
image has booted with physical touch and playback rechecked. Only then remove
the hotpatch and complete the Boot, Touch, Render, Reboot, and OTA rows above.

For development images, `DEV_MODE=1` supplies `debug-tweaks`, which enables
Weston's `--debug` protocol for bounded screenshot capture. Production images
omit `--debug`; do not hotpatch or remotely expose it in PROD. Synthetic touch
tests must clone the deployed device's ABS capabilities and effective udev
policy (`ID_INPUT_TOUCHSCREEN`, `WL_OUTPUT`, calibration, and seat when
present), and fail closed if the virtual endpoint differs. Synthetic input
starts above the physical controller, bus, IRQ, and kernel driver, so Michael's
physical acceptance remains mandatory.

The audio investigation found that the `kiosk-browser`-only tuple deliberately
removed both ALSA and PulseAudio, leaving Chromium with no usable audio backend.
The corrected Screen kiosk tuple therefore selects `kiosk-browser audio`.
The kiosk audio drop-in joins the service to the `audio` group, orders it after
the system PulseAudio service, and points Chromium at the image's Unix socket.
The Screen machine selects ALSA card `wm8524audio` by stable name, never by the
observed card index. Target 2995 predates this correction and cannot be the
audio acceptance image; target 2998 is the replacement build gate.

### OSTree hotpatch isolation

Do not add another OSTree deployment's `/usr/lib`, PulseAudio directory, or
ALSA plugin directory to global `ld.so.conf` or a broad service
`LD_LIBRARY_PATH`. Target 2991 demonstrated why: Weston loaded current
`libg2d`/`libGAL` together with rollback `libweston`/`libEGL`/`libgbm`, so G2D
opened successfully but compositor-backend creation failed on every reboot.
The kiosk package now runs a fail-closed linker guard before Weston, migrates
the two named development hotpatches, and restores the native packaged browser
launcher. Acceptance requires zero `/ostree/deploy/.../usr/lib` entries in
`ldconfig -p` and zero such mappings in the Weston and browser cgroups.

For the controlled-input check, exercise the panel with touch and a temporary
USB keyboard. Try taps and scrolling, text entry where the application needs
it, long press/context menu, `Ctrl+L`, `Ctrl+N`, `Ctrl+T`, `Ctrl+W`, `F11`,
`Alt+F4`, developer-tools shortcuts, and direct `view-source:` navigation.
Open links that request a new window,
file selection, download, or external protocol. Record whether each attempt
stays on the managed fullscreen page, is blocked by policy, or restarts the
kiosk service back into that page. Treat any usable browser chrome, shell,
unrestricted file picker, or persistent blank screen as a failed input check.
Also try creating a second browser profile and signing the browser into an
account; both must be blocked by the managed kiosk policy. Signing into the
deployed web application, if it offers its own login, is a separate test.
