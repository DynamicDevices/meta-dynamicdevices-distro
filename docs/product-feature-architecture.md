# Dynamic Devices product feature architecture

## Decision

Shipped Foundries products use one canonical distro:

```bitbake
DISTRO = "lmp-dynamicdevices"
```

The distro owns organisation-wide policy. Hardware facts stay in the BSP and
`MACHINE_FEATURES`. Optional product software is selected with
`DD_PRODUCT_FEATURES`. An empty product feature set is the headless/minimal
default; `headless` is not itself a feature.

The canonical distro removes graphical and host-audio features by default.
Selecting `display`, `flutter`, `kiosk-browser`, `audio`, or `android-container` retains and
expands the corresponding runtime. CRA audit and automatic registration remain
global shipped-product policy rather than product options.

## Ownership

| Concern | Owner | Examples |
| --- | --- | --- |
| Organisation policy | distro | OTA baseline, security policy, licences, providers and preferred versions |
| Physical capability | machine/BSP | display controller, panel, touch, audio codec, TPM, Wi-Fi chipset |
| Product software | `DD_PRODUCT_FEATURES` | Wayland, Flutter, host audio, Android container |
| Development access | `IMAGE_FEATURES` | `debug-tweaks`, profiling and test tools |

For the display stack, Factory `DEV_MODE=1` adds `debug-tweaks` and permits
Weston's `--debug` protocol for development-only capture and diagnosis. A PROD
build omits that argument. Do not enable the debug protocol at runtime to make
a production test harness work.

Do not infer a full graphical stack merely because hardware has a display. An
e-ink product may use its display directly without Wayland or OpenGL.

## Product feature contract

Examples:

```bitbake
# Minimal/headless
DD_PRODUCT_FEATURES = ""

# Jaguar Screen: established Weston, Flutter and Godot payload, without Improv
DD_PRODUCT_FEATURES = "display flutter godot"

# Flutter screen
DD_PRODUCT_FEATURES = "improv flutter"

# Chromium kiosk screen with host audio
DD_PRODUCT_FEATURES = "kiosk-browser audio"

# Cog/WPE WebKit test kiosk with host audio
DD_PRODUCT_FEATURES = "kiosk-cog audio"

# Android screen; currently implemented by Waydroid
DD_PRODUCT_FEATURES = "improv android-container"
```

Feature bundles expand prerequisites centrally. In particular,
`display` enables the shipped screen stack (`wayland`, `opengl`, and
`pipewire`) and the hardware multimedia image fragment. `flutter` and `godot`
select their respective UI runtimes and also imply the display runtime.
`kiosk-browser` selects Chromium Ozone Wayland and a Weston-owned fullscreen
launcher, and also implies the display runtime. Its URL is configured in
`/etc/default/dd-kiosk-browser`; the default is a local provisioning page.
`kiosk-cog` selects Cog with WPE WebKit behind the same provider-neutral kiosk
packagegroup and Weston kiosk shell. It exists for comparative build,
rendering, touch, audio and video tests while Chromium CI is being repaired.
Cog is intentionally a small single-view embedded web application container,
but this integration does not implement the Chromium managed-policy contract.
Do not promote `kiosk-cog` to a release feature without a separate security
and product-readiness decision.
WebKitGTK `MiniBrowser` remains a useful second lightweight-browser provider.
Its integration is deliberately deferred until Cog is built and working on the
target, at which point it should be added behind the same packagegroup contract
for a controlled Cog/MiniBrowser comparison.
On Jaguar Screen it selects Weston's kiosk shell, so other windows do not
become part of the public display. Audio remains an explicit `audio` feature;
select it for browser playback so Chromium is built with its audio backend and
the ALSA/PulseAudio runtime is present.
The kiosk package installs Chromium managed policies under
`/etc/chromium/policies/managed`: public users cannot open file pickers,
downloads, printing, Developer Tools, guest/incognito profiles, or install
extensions. The policy file is a conffile for product-specific adjustments;
physical keyboard and touch escape paths still require board testing.
The two kiosk browser features are mutually exclusive. Neither can be combined
with `flutter`, `godot`, or `android-container`, which are alternative owners
of the same display.
The lower-level `wayland` selector remains available for migration
compatibility, but new product configurations should use `display`.
`android-container` currently enables `waydroid`, `wayland`, `opengl`,
`vulkan`, `pulseaudio`, and `alsa`. Vulkan is an intentional compatibility
addition because the current Waydroid recipe declares it in
`REQUIRED_DISTRO_FEATURES`; without it the provider is skipped. Factory
configuration must use the stable
`android-container` name rather than the provider name `waydroid`.

The `display`, `flutter`, `godot`, `kiosk-browser`, and `kiosk-cog`
selections require the BSP to declare
`display-multimedia` in `MACHINE_FEATURES`. This keeps panel/GPU capability in
the machine while preventing capable hardware from implicitly installing a UI.

Runtime payloads are owned by provider-neutral packagegroups:

- `packagegroup-dd-alsa`
- `packagegroup-dd-audio`
- `packagegroup-dd-flutter`
- `packagegroup-dd-kiosk-browser`
- `packagegroup-dd-android-container`

`packagegroup-dd-kiosk-browser` installs `DD_KIOSK_BROWSER_RUNTIME`, which
defaults to `dd-kiosk-browser`. The `kiosk-cog` feature selects
`dd-kiosk-cog` instead. Both providers expose the same service, launcher,
URL configuration and offline page paths, so the image hook and Weston kiosk
integration remain unchanged.

The legacy `lmp-feature-*.inc` image hooks now select these packagegroups so
existing products retain their package payload while factory configuration is
migrated. Wayland remains provided by the upstream LmP Wayland feature hook.

Unknown feature names are fatal at parse time. Display, Flutter and Godot
selection is also fatal unless the machine declares `display-multimedia`;
recipe `COMPATIBLE_MACHINE` checks remain the final provider-level guard.

`imx8mm-jaguar-screen` intentionally has no `improv` feature: the product has
no working Bluetooth onboarding path. Do not infer onboarding protocols from
the presence of generic Wi-Fi or Bluetooth-related BSP components.

## Migration invariants

1. Introduce feature selection without changing existing product branches.
2. Migrate one product at a time and record old/new expanded feature sets.
3. Compare package manifests and important generated configuration before OTA.
4. Preserve security, registration, storage layout and updater behaviour.
5. Prove the resulting image on the applicable hardware before retiring its
   legacy distro selection.
6. Remove legacy distro files only after no Foundries or local build consumer
   references them.

## Planned legacy retirement

The following are compatibility inputs during migration, not the target model:

- `lmp-dynamicdevices-headless`
- `lmp-dynamicdevices-flutter`
- `lmp-dynamicdevices-waydroid`
- `lmp-dynamicdevices-headless-waydroid`

`lmp-dynamicdevices-aesl` remains a policy overlay for the self-hosted updater,
but now inherits `lmp-dynamicdevices`; its multi-machine Factory Definition
passes product features per machine. `lmp-dynamicdevices-base` remains outside
the UI-variant retirement because it has a different image-policy role.

Retirement is deliberately the final rollout step. Keep the aliases until the
layer, Foundries Factory Definition, AESL runner and manifest pins have been
published together and hardware validation has passed.
