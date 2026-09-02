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
Selecting `display`, `flutter`, `audio`, or `android-container` retains and
expands the corresponding runtime. CRA audit and automatic registration remain
global shipped-product policy rather than product options.

## Ownership

| Concern | Owner | Examples |
| --- | --- | --- |
| Organisation policy | distro | OTA baseline, security policy, licences, providers and preferred versions |
| Physical capability | machine/BSP | display controller, panel, touch, audio codec, TPM, Wi-Fi chipset |
| Product software | `DD_PRODUCT_FEATURES` | Wayland, Flutter, host audio, Android container |
| Development access | `IMAGE_FEATURES` | `debug-tweaks`, profiling and test tools |

Do not infer a full graphical stack merely because hardware has a display. An
e-ink product may use its display directly without Wayland or OpenGL.

## Product feature contract

Examples:

```bitbake
# Minimal/headless
DD_PRODUCT_FEATURES = ""

# Screen product with a host Wayland display runtime
DD_PRODUCT_FEATURES = "display"

# Flutter screen
DD_PRODUCT_FEATURES = "improv flutter"

# Android screen; currently implemented by Waydroid
DD_PRODUCT_FEATURES = "improv android-container"
```

Feature bundles expand prerequisites centrally. In particular,
`display` enables the current host display provider (`wayland`, `opengl`, and
`vulkan`).
The lower-level `wayland` selector remains available for migration
compatibility, but new product configurations should use `display`.
`android-container` currently enables `waydroid`, `wayland`, `opengl`,
`vulkan`, `pulseaudio`, and `alsa`. Factory configuration must use the stable
`android-container` name rather than the provider name `waydroid`.

Runtime payloads are owned by provider-neutral packagegroups:

- `packagegroup-dd-alsa`
- `packagegroup-dd-audio`
- `packagegroup-dd-flutter`
- `packagegroup-dd-android-container`

The legacy `lmp-feature-*.inc` image hooks now select these packagegroups so
existing products retain their package payload while factory configuration is
migrated. Wayland remains provided by the upstream LmP Wayland feature hook.

Unknown feature names are fatal at parse time. Hardware compatibility checks
will be added as machines acquire explicit capability declarations; until then,
the existing recipe `COMPATIBLE_MACHINE` checks remain authoritative.

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

`lmp-dynamicdevices-base` and `lmp-dynamicdevices-aesl` need separate review:
they also encode updater/factory policy, so they must not be mechanically
collapsed with UI variants.
