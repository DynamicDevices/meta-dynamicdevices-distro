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
    flutter \
    improv \
    usb-gadget \
    wayland \
"

# Product-facing features expand to their complete runtime prerequisites.
# "android-container" is intentionally implementation-neutral; Waydroid is
# the current provider and may be replaced without changing factory contracts.
DISTRO_FEATURES:append = " \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'alsa', 'alsa', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'audio', 'alsa pulseaudio', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'wayland', 'wayland opengl', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'flutter', 'flutter wayland opengl', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'android-container', 'waydroid wayland opengl pulseaudio alsa', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'auto-register', 'auto-register', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'cra-audit', 'cra-audit', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'improv', 'improv', '', d)} \
    ${@bb.utils.contains('DD_PRODUCT_FEATURES', 'usb-gadget', 'usbgadget', '', d)} \
"

python () {
    selected = set((d.getVar("DD_PRODUCT_FEATURES") or "").split())
    valid = set((d.getVar("DD_PRODUCT_FEATURES_VALID") or "").split())
    unknown = sorted(selected - valid)
    if unknown:
        bb.fatal(
            "Unknown DD_PRODUCT_FEATURES value(s): %s. Valid values: %s"
            % (" ".join(unknown), " ".join(sorted(valid)))
        )
}
