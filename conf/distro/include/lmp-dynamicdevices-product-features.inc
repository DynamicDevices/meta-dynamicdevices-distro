# Dynamic Devices product composition contract.
#
# DISTRO policy remains in lmp-dynamicdevices.conf.  Factory/product
# configurations select optional software capabilities through
# DD_PRODUCT_FEATURES.  An empty value is the minimal/headless default.
#
# Keep the mapping to standard/existing DISTRO_FEATURES here so recipes can
# continue to use Yocto feature checks while products migrate incrementally.

DD_PRODUCT_FEATURES ?= ""

# The kiosk manifest carries its own pinned Chromium and Rust-mixin layers.
# Limit their provider choices to kiosk builds so this shared distro contract
# does not alter any existing product's toolchain or recipe selection.
OVERRIDES:append = "${@':ddkioskbrowser' if 'kiosk-browser' in (d.getVar('DD_PRODUCT_FEATURES') or '').split() else ''}"
RUSTVERSION:ddkioskbrowser = "1.98.1"
PREFERRED_VERSION_nativesdk-cargo:ddkioskbrowser = "${RUSTVERSION}"
PREFERRED_VERSION_nativesdk-libstd-rs:ddkioskbrowser = "${RUSTVERSION}"
PREFERRED_VERSION_nativesdk-rust:ddkioskbrowser = "${RUSTVERSION}"
PREFERRED_VERSION_nativesdk-rust-llvm:ddkioskbrowser = "${RUSTVERSION}"
PREFERRED_VERSION_rust-cross-canadian-aarch64:ddkioskbrowser = "${RUSTVERSION}"
PREFERRED_VERSION_nodejs:ddkioskbrowser = "22.11.0"
PREFERRED_VERSION_nodejs-native:ddkioskbrowser = "22.11.0"
PREFERRED_VERSION_nodejs-oe-cache-native:ddkioskbrowser = "22.11"
PREFERRED_VERSION_librsvg:ddkioskbrowser = "2.62.3"
PREFERRED_VERSION_librsvg-native:ddkioskbrowser = "2.62.3"
PREFERRED_VERSION_nativesdk-librsvg:ddkioskbrowser = "2.62.3"
PREFERRED_VERSION_libgit2:ddkioskbrowser = "1.9.7"
PREFERRED_VERSION_libgit2-native:ddkioskbrowser = "1.9.7"
PREFERRED_VERSION_gn-native:ddkioskbrowser = "147.0.7727.116"
PREFERRED_VERSION_cargo-c-native:ddkioskbrowser = "0.10.25+cargo-0.99.0"

DD_PRODUCT_FEATURES_VALID = " \
    alsa \
    android-container \
    audio \
    auto-register \
    kiosk-browser \
    cra-audit \
    display \
    flutter \
    godot \
    improv \
    usb-gadget \
    wayland \
"

# The canonical distro is headless/minimal unless a product opts into a
# graphical or audio runtime. Conditional removal is used instead of a fixed
# :remove so a selected bundle can re-enable its prerequisites.
DISTRO_FEATURES:remove = " \
    x11 directfb \
    ${@'' if 'android-container' in set((d.getVar('DD_PRODUCT_FEATURES') or '').split()) else 'vulkan'} \
    ${@'' if set((d.getVar('DD_PRODUCT_FEATURES') or '').split()) & {'display', 'wayland', 'flutter', 'godot', 'android-container', 'kiosk-browser'} else 'wayland opengl'} \
    ${@'' if set((d.getVar('DD_PRODUCT_FEATURES') or '').split()) & {'audio', 'android-container'} else 'pulseaudio'} \
    ${@'' if set((d.getVar('DD_PRODUCT_FEATURES') or '').split()) & {'alsa', 'audio', 'godot', 'android-container'} else 'alsa'} \
"

# Product-facing features expand to their complete runtime prerequisites.
# "android-container" is intentionally implementation-neutral; Waydroid is
# the current provider and may be replaced without changing factory contracts.
DISTRO_FEATURES:append = " \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'alsa', 'alsa', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'audio', 'alsa pulseaudio', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'display', 'display-runtime wayland opengl pipewire', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'wayland', 'wayland opengl', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'flutter', 'display-runtime flutter wayland opengl', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'godot', 'display-runtime godot wayland opengl alsa', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'kiosk-browser', 'display-runtime kiosk-browser wayland opengl', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'android-container', 'waydroid apparmor wayland opengl vulkan pulseaudio alsa', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'auto-register', 'auto-register', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'cra-audit', 'cra-audit', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'improv', 'improv', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'usb-gadget', 'usbgadget', '', d)} \
"

addhandler dd_validate_product_features
dd_validate_product_features[eventmask] = "bb.event.ConfigParsed"

python dd_validate_product_features() {
    selected = set((e.data.getVar("DD_PRODUCT_FEATURES") or "").split())
    valid = set((e.data.getVar("DD_PRODUCT_FEATURES_VALID") or "").split())
    unknown = sorted(selected - valid)
    if unknown:
        bb.fatal(
            "Unknown DD_PRODUCT_FEATURES value(s): %s. Valid values: %s"
            % (" ".join(unknown), " ".join(sorted(valid)))
        )

    other_display_apps = selected & {"flutter", "godot", "android-container"}
    if "kiosk-browser" in selected and other_display_apps:
        bb.fatal(
            "kiosk-browser owns the display and cannot be combined with %s"
            % " ".join(sorted(other_display_apps))
        )

    display_software = selected & {"display", "flutter", "godot", "kiosk-browser"}
    machine_features = set((e.data.getVar("MACHINE_FEATURES") or "").split())
    if display_software and "display-multimedia" not in machine_features:
        bb.fatal(
            "DD_PRODUCT_FEATURES value(s) %s require MACHINE_FEATURES "
            "'display-multimedia'"
            % " ".join(sorted(display_software))
        )
}
