# Jaguar Screen Chromium kiosk acceptance

This record applies to `imx8mm-jaguar-screen` with
`DD_PRODUCT_FEATURES = "kiosk-browser"`. Keep the exact manifest revision,
factory target, image checksums, and observed results together. A local parse
or recipe build does not count as hardware acceptance.

## Build record

| Evidence | Value / result |
| --- | --- |
| Kiosk manifest commit | Pending |
| Distro feature commit | Pending |
| Factory configuration commit | Pending |
| Chromium recipe version and layer commit | Pending |
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
target `2943` (`81e0a111532fc9bbddeb3e2cdf1c18683a8a0369bea5cb41b8586e8ad59d648e`)
with Weston active. This baseline is not a kiosk test result.

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
