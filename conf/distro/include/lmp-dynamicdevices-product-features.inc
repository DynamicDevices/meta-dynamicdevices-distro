# Dynamic Devices product composition contract.
#
# DISTRO policy remains in lmp-dynamicdevices.conf.  Factory/product
# configurations select optional software capabilities through
# DD_PRODUCT_FEATURES.  An empty value is the minimal/headless default.
#
# Keep the mapping to standard/existing DISTRO_FEATURES here so recipes can
# continue to use Yocto feature checks while products migrate incrementally.

DD_PRODUCT_FEATURES ?= ""

DD_PRODUCT_FEATURES_VALID = " \
    alsa \
    android-container \
    audio \
    auto-register \
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
DD_PRODUCT_GRAPHICS_FEATURES = "wayland opengl x11 directfb vulkan"
DD_PRODUCT_AUDIO_FEATURES = "pulseaudio alsa"
DISTRO_FEATURES:remove = " \
    ${@'' if set((d.getVar('DD_PRODUCT_FEATURES') or '').split()) & {'display', 'wayland', 'flutter', 'godot', 'android-container'} else d.getVar('DD_PRODUCT_GRAPHICS_FEATURES')} \
    ${@'' if set((d.getVar('DD_PRODUCT_FEATURES') or '').split()) & {'alsa', 'audio', 'godot', 'android-container'} else d.getVar('DD_PRODUCT_AUDIO_FEATURES')} \
"

# Product-facing features expand to their complete runtime prerequisites.
# "android-container" is intentionally implementation-neutral; Waydroid is
# the current provider and may be replaced without changing factory contracts.
DISTRO_FEATURES:append = " \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'alsa', 'alsa', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'audio', 'alsa pulseaudio', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'display', 'display-runtime wayland opengl vulkan', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'wayland', 'wayland opengl', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'flutter', 'display-runtime flutter wayland opengl vulkan pulseaudio', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'godot', 'display-runtime godot wayland opengl vulkan alsa', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'android-container', 'waydroid wayland opengl vulkan pulseaudio alsa', '', d)} \
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

    display_software = selected & {"display", "flutter", "godot"}
    machine_features = set((e.data.getVar("MACHINE_FEATURES") or "").split())
    if display_software and "display-multimedia" not in machine_features:
        bb.fatal(
            "DD_PRODUCT_FEATURES value(s) %s require MACHINE_FEATURES "
            "'display-multimedia'"
            % " ".join(sorted(display_software))
        )
}
