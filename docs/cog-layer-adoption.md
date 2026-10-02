# Cog / WPE WebKit layer adoption record

Date: 2026-10-01

## Purpose

`kiosk-cog` is a test-only lightweight browser feature for the Jaguar Screen.
It selects Cog and WPE WebKit behind the existing provider-neutral kiosk
packagegroup and service contract. Chromium remains the production browser
direction; Cog is being evaluated for comparative rendering, touch, audio and
video tests.

WebKitGTK `MiniBrowser` is deliberately out of scope until Cog has built and
been tested successfully on the target. When that gate passes, MiniBrowser can
be added behind the same packagegroup contract for a controlled comparison.

## Exact external layer

- Repository: `https://github.com/Igalia/meta-webkit.git`
- Branch: `scarthgap`
- Commit: `2d29669a3d78e462276044f3f8bde0e4dec33696`
- Cog: `0.18.5`
- WPE WebKit: `2.46.7`
- libwpe: `1.16.2`
- wpebackend-fdo: `1.14.4`

The layer audit identified two global behaviours that must not affect existing
products:

- `BB_DANGLINGAPPENDS_WARNONLY = "true"` in `meta-webkit/conf/layer.conf`;
- a global HarfBuzz append that enables ICU.

The distro restores dangling appends to fatal. For product tuples without
`kiosk-cog`, it masks `meta-webkit` files and removes the `webkit` collection;
this prevents its recipes, appends and provider priority from participating and
also avoids BitBake's enabled-but-empty-layer warning. The collection remains
active only for the explicit Cog feature.

## Existing-product isolation proof

Test tuple:

```bitbake
MACHINE = "imx8mm-jaguar-screen"
DISTRO = "lmp-dynamicdevices"
DD_PRODUCT_FEATURES = "kiosk-browser audio"
```

Bounded metadata comparison on ai-tools proved:

- no `webkit` collection in `bitbake-layers show-layers`;
- zero `meta-webkit` recipe paths in `show-recipes`;
- zero `meta-webkit` append paths in `show-appends`;
- no `BBFILE_PATTERN_webkit` empty-layer warning;
- `DD_KIOSK_BROWSER_RUNTIME="dd-kiosk-browser"`;
- `RDEPENDS:packagegroup-dd-kiosk-browser="dd-kiosk-browser"`.

The remaining preferred-version warnings for NXP GStreamer and
`gcc-arm-none-eabi` are present in the existing LmP stack and are not introduced
by Cog.

## Cog selection proof

Test tuple:

```bitbake
MACHINE = "imx8mm-jaguar-screen"
DISTRO = "lmp-dynamicdevices"
DD_PRODUCT_FEATURES = "kiosk-cog audio"
```

The corresponding metadata proof showed:

- one active `webkit` layer collection;
- the expected `meta-webkit` HarfBuzz append;
- no empty-layer warning;
- `DD_KIOSK_BROWSER_RUNTIME="dd-kiosk-cog"`;
- `RDEPENDS:packagegroup-dd-kiosk-browser="dd-kiosk-cog"`;
- Cog `PV="0.18.5"` and `PACKAGECONFIG="wl"`.

The Cog runtime uses the same board audio selection and mixed-userspace
linker guard as the Chromium provider. With the `audio` feature selected it
waits for the system PulseAudio service and uses its Unix socket; on the
Jaguar Screen, a TAS2555-capable machine selects the named `tas2555audio`
ALSA card. Before Weston starts, the linker guard removes only the two known
legacy development hotpatches and rejects any other cross-deployment library
path so G2D, EGL, GBM and Weston cannot be mixed between OSTree deployments.

## Native build compatibility

The ai-tools development workspace intentionally uses `PATCHTOOL = "git"` so
patched sources remain inspectable. Bison sees the resulting `.git` directory
as a maintainer checkout and regenerates `bison.1`, which requires
`help2man-native`. The existing Chromium-specific Bison dependency is therefore
also enabled by the `ddkioskcog` override; the global Git patch workflow remains
unchanged.

The base LmP Pseudo 1.9.0 cannot track directory descriptors used by the host's
modern GNU tar during `do_package`, producing `unknown base path for fd` and
`EFAULT`. The existing Chromium native-only Pseudo 1.9.7 pin and compatibility
patch are also enabled by `ddkioskcog`. Target and nativesdk Pseudo remain
unchanged.

## Build evidence

On ai-tools in the isolated `build-cog` tree:

- the final `dd-kiosk-cog` provider payload was included in the successful
  factory image build;
- `bitbake wpewebkit -c configure` passed: 2,549 tasks attempted, all
  successful;
- full `bitbake cog` passed;
- targeted `gdb ltrace iotop -c compile` passed: 843 tasks attempted, all
  successful, with the existing GCC exceptions extended only to `ddkioskcog`;
- targeted `diffutils -c compile` passed: 626 tasks attempted, all successful,
  retaining Clang and disabling only the Git-checkout developer warning mode;
- `bitbake lmp-factory-image` passed: 10,158 tasks attempted, all successful,
  including WIC and both OTA formats;
- after synchronising the staged TAS2555 BSP into the same full manifest,
  `bitbake kernel-module-tas2555 -c package_qa` with a temporary feature
  override passed: 1,005 tasks attempted, 954 already satisfied, all
  successful;
- the resolved native Pseudo is `1.9.7` at
  `5b7c4b59e7e198aab54b35ea194aeb6d99794f96`.

The image produced on 2026-10-01 is an intermediate browser-build artifact,
not an audio-complete deployment candidate. The provider-neutral verifier
correctly rejected it because the resolved Screen machine lacked the `tas2555`
feature and the root filesystem retained a generic `hw:0,0` ALSA default. No
TAS2555 package was present. The staged BSP driver requires the
speaker-specific `tas2555_uCDSP.bin`; neither that firmware nor the speaker
load/tuning data is present in the task repositories or MemPalace. ROM playback
would omit speaker protection, so it must not be silently substituted.

Evidence is retained below
`/srv/yocto/jaguar-screen-kiosk/build-cog/cog-evidence/` on ai-tools.

## Remaining gates

The feature is not yet release-ready. Required evidence still includes:

1. obtain the correct TAS2555 speaker firmware and load/tuning information, or
   approve and engineer a separately named DEV-only unprotected ROM-mode path;
2. enable the TAS2555 machine feature only after that audio path is safe;
3. rebuild the Jaguar Screen image and pass the full provider-neutral verifier;
4. deploy to the target and verify fullscreen rendering;
5. verify physical and injected touchscreen input using the deployed mapping;
6. verify TAS2555 audio playback and DPX capture;
7. verify sustained video playback and retain a Weston capture;
8. verify boot/restart, network recovery, OTA and rollback behaviour;
9. make an explicit security/product decision before production promotion.
