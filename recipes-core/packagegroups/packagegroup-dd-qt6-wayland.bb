SUMMARY = "Native Qt 6 Widgets and Wayland client runtime"
DESCRIPTION = "Image-built Qt runtime for native Wayland applications; no application payload or X11 server."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit packagegroup features_check

REQUIRED_DISTRO_FEATURES = "qt6 wayland opengl alsa"

# Keep plugin packages explicit. ELF dependencies supply matching ICU/graphics.
RDEPENDS:${PN} = " \
    qtbase \
    qtbase-plugins \
    qtwayland \
    qtwayland-plugins \
    alsa-lib \
    util-linux-libuuid \
    fontconfig \
    liberation-fonts \
"
