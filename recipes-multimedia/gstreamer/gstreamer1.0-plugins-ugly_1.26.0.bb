# GStreamer 1.26.0 plugins-ugly recipe for Conversa v2.0 support

SUMMARY = "'Ugly' GStreamer plugins"
HOMEPAGE = "https://gstreamer.freedesktop.org/"
BUGTRACKER = "https://gitlab.freedesktop.org/gstreamer/gst-plugins-ugly/-/issues"

# Use upstream GStreamer plugins-ugly 1.26.0 (NXP doesn't maintain a separate fork)
SRC_URI = "https://gstreamer.freedesktop.org/src/gst-plugins-ugly/gst-plugins-ugly-${PV}.tar.xz"
SRC_URI[sha256sum] = "a86b51c8454a813120848c803421f327d8c07aabcae461e0597cc49398c0fcde"

S = "${WORKDIR}/gst-plugins-ugly-${PV}"

LICENSE = "LGPL-2.1-or-later"
LIC_FILES_CHKSUM = "file://COPYING;md5=a6f89e2100d9b6cdffcea4f398e37343"

DEPENDS += "gstreamer1.0 gstreamer1.0-plugins-base"

inherit meson pkgconfig upstream-version-is-even gobject-introspection

PACKAGECONFIG ??= " \
    ${@bb.utils.contains('DISTRO_FEATURES', 'orc', 'orc', '', d)} \
    ${@bb.utils.contains('DISTRO_FEATURES', 'x11', 'x264', '', d)} \
    a52dec mpeg2dec \
"

PACKAGECONFIG[a52dec]   = "-Da52dec=enabled,-Da52dec=disabled,liba52"
PACKAGECONFIG[amrnb]    = "-Damrnb=enabled,-Damrnb=disabled,opencore-amr"
PACKAGECONFIG[amrwb]    = "-Damrwb=enabled,-Damrwb=disabled,opencore-amr"
PACKAGECONFIG[cdio]     = "-Dcdio=enabled,-Dcdio=disabled,libcdio"
PACKAGECONFIG[dvdread]  = "-Ddvdread=enabled,-Ddvdread=disabled,libdvdread"
PACKAGECONFIG[mpeg2dec] = "-Dmpeg2dec=enabled,-Dmpeg2dec=disabled,mpeg2dec"
PACKAGECONFIG[orc]      = "-Dorc=enabled,-Dorc=disabled,orc orc-native"
PACKAGECONFIG[x264]     = "-Dx264=enabled,-Dx264=disabled,x264"

EXTRA_OEMESON += " \
    -Ddoc=disabled \
    -Dexamples=disabled \
    ${@gettext_oemeson(d)} \
"

def gettext_oemeson(d):
    if d.getVar('USE_NLS') == 'no':
        return '-Dnls=disabled'
    # Remove the NLS bits if USE_NLS is no or INHIBIT_DEFAULT_DEPS is set
    if d.getVar('INHIBIT_DEFAULT_DEPS') and not oe.utils.inherits(d, 'cross-canadian'):
        return '-Dnls=disabled'
    return '-Dnls=enabled'

GIR_MESON_ENABLE_FLAG = "enabled"
GIR_MESON_DISABLE_FLAG = "disabled"

# Higher preference than the 1.24.0.imx version for Conversa v2.0 support
DEFAULT_PREFERENCE = "1"

# Compatible with i.MX platforms
COMPATIBLE_MACHINE = "(imx-nxp-bsp)"

CVE_PRODUCT = "gstreamer"
