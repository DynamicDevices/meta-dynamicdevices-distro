# Jaguar Screen Chromium kiosk acceptance

This record applies to `imx8mm-jaguar-screen` with
`DD_PRODUCT_FEATURES = "kiosk-browser"`. Keep the exact manifest revision,
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
| Kiosk manifest commit | Pending |
| Distro feature commit | Pending |
| Factory configuration commit | Pending |
| Chromium recipe version and layer commit | `chromium-ozone-wayland_147.0.7727.116.bb` at `85eeb6b50883d22c977396f5e8fe211a7961cf2e` |
| Feature contract negative parses | Separate BitBake parses rejected `kiosk-browser flutter`, kiosk on `imx8mm-jaguar-sentai` without `display-multimedia`, and unknown feature `bogus`; each exited 1 with the intended error |
| `bitbake chromium-ozone-wayland` | Pending |
| `bitbake lmp-factory-image` | Pending |
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
| Network loss | Remote test URL may show a transient error, but the service stays recoverable | Pending |
| Network return | NetworkManager dispatcher restarts Chromium and the configured URL loads | Pending |
| Browser crash | Killing Chromium causes systemd restart without a restore prompt | Pending |
| Reboot | URL, profile state and kiosk service return after power-cycle or reboot | Pending |
| OTA | New target installs and boots; URL/configuration survives; rollback path remains valid | Pending |

Record command output, screenshots, timestamps, and the resulting OSTree
deployment alongside each result. Check panel rotation and touch coordinates
together; the kiosk candidate currently uses the base `rotate-90` transform,
while a separate uncommitted screen edit uses `rotate-270`.

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
