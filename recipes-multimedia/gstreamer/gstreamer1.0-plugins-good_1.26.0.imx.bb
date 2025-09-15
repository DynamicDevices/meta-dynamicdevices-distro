# GStreamer 1.26.0 plugins-good recipe for Conversa v2.0 support

SUMMARY = "'Good' GStreamer plugins"
HOMEPAGE = "https://gstreamer.freedesktop.org/"
BUGTRACKER = "https://gitlab.freedesktop.org/gstreamer/gst-plugins-good/-/issues"

# Use NXP i.MX fork of GStreamer plugins-good 1.26.0 for hardware acceleration
SRC_URI = "${GST1.0_SRC};branch=${SRCBRANCH}"
GST1.0_SRC ?= "gitsm://github.com/nxp-imx/gst-plugins-good.git;protocol=https"
SRCBRANCH = "MM_04.10.01_2508_L6.12.34"
SRCREV = "6b8d873767a9055cd2b59abd16cef63783826d3b"

S = "${WORKDIR}/git"

LICENSE = "LGPL-2.1-or-later"
LIC_FILES_CHKSUM = "file://COPYING;md5=a6f89e2100d9b6cdffcea4f398e37343 \
                    file://gst/replaygain/rganalysis.c;beginline=1;endline=23;md5=b60ebefd5b2f5a8e0cab6bfee391a5fe"

DEPENDS += "gstreamer1.0 gstreamer1.0-plugins-base libcap zlib"

inherit meson pkgconfig upstream-version-is-even gobject-introspection

RPROVIDES:${PN}-pulseaudio += "${PN}-pulse"
RPROVIDES:${PN}-soup += "${PN}-souphttpsrc"
RDEPENDS:${PN}-soup += "${MLPREFIX}${@bb.utils.contains('PACKAGECONFIG', 'soup2', 'libsoup-2.4', 'libsoup', d)}"

PACKAGECONFIG_SOUP ?= "soup3"

PACKAGECONFIG ??= " \
    ${@bb.utils.contains('DISTRO_FEATURES', 'orc', 'orc', '', d)} \
    ${PACKAGECONFIG_SOUP} \
    ${@bb.utils.filter('DISTRO_FEATURES', 'pulseaudio x11', d)} \
    ${@bb.utils.contains('TUNE_FEATURES', 'm64', 'asm', '', d)} \
    bz2 cairo flac gdk-pixbuf gudev jpeg lame libpng mpg123 speex taglib v4l2 \
"

X11DEPENDS = "virtual/libx11 libsm libxrender libxfixes libxdamage"
X11ENABLEOPTS = "-Dximagesrc=enabled -Dximagesrc-xshm=enabled -Dximagesrc-xfixes=enabled -Dximagesrc-xdamage=enabled"
X11DISABLEOPTS = "-Dximagesrc=disabled -Dximagesrc-xshm=disabled -Dximagesrc-xfixes=disabled -Dximagesrc-xdamage=disabled"

QT5WAYLANDDEPENDS = "${@bb.utils.contains("DISTRO_FEATURES", "wayland", "qtwayland", "", d)}"

PACKAGECONFIG[asm]        = "-Dasm=enabled,-Dasm=disabled,nasm-native"
PACKAGECONFIG[bz2]        = "-Dbz2=enabled,-Dbz2=disabled,bzip2"
PACKAGECONFIG[cairo]      = "-Dcairo=enabled,-Dcairo=disabled,cairo"
PACKAGECONFIG[dv1394]     = "-Ddv1394=enabled,-Ddv1394=disabled,libiec61883 libavc1394 libraw1394"
PACKAGECONFIG[flac]       = "-Dflac=enabled,-Dflac=disabled,flac"
PACKAGECONFIG[gdk-pixbuf] = "-Dgdk-pixbuf=enabled,-Dgdk-pixbuf=disabled,gdk-pixbuf"
PACKAGECONFIG[gtk3]       = "-Dgtk3=enabled,-Dgtk3=disabled,gtk+3"
PACKAGECONFIG[gudev]      = "-Dv4l2-gudev=enabled,-Dv4l2-gudev=disabled,libgudev"
PACKAGECONFIG[jack]       = "-Djack=enabled,-Djack=disabled,jack"
PACKAGECONFIG[jpeg]       = "-Djpeg=enabled,-Djpeg=disabled,jpeg"
PACKAGECONFIG[lame]       = "-Dlame=enabled,-Dlame=disabled,lame"
PACKAGECONFIG[libpng]     = "-Dpng=enabled,-Dpng=disabled,libpng"
PACKAGECONFIG[mpg123]     = "-Dmpg123=enabled,-Dmpg123=disabled,mpg123"
PACKAGECONFIG[orc]        = "-Dorc=enabled,-Dorc=disabled,orc orc-native"
PACKAGECONFIG[pulseaudio] = "-Dpulse=enabled,-Dpulse=disabled,pulseaudio"
PACKAGECONFIG[qt5]        = "-Dqt5=enabled,-Dqt5=disabled,qtbase qtdeclarative qtx11extras ${QT5WAYLANDDEPENDS}"
PACKAGECONFIG[soup2]      = "-Dsoup=enabled,-Dsoup=disabled,libsoup-2.4,,,soup3"
PACKAGECONFIG[soup3]      = "-Dsoup=enabled,-Dsoup=disabled,libsoup,,,soup2"
PACKAGECONFIG[speex]      = "-Dspeex=enabled,-Dspeex=disabled,speex"
PACKAGECONFIG[taglib]     = "-Dtaglib=enabled,-Dtaglib=disabled,taglib"
PACKAGECONFIG[v4l2]       = "-Dv4l2=enabled,-Dv4l2=disabled,v4l-utils"
PACKAGECONFIG[vpx]        = "-Dvpx=enabled,-Dvpx=disabled,libvpx"
PACKAGECONFIG[wavpack]    = "-Dwavpack=enabled,-Dwavpack=disabled,wavpack"
PACKAGECONFIG[x11]        = "${X11ENABLEOPTS},${X11DISABLEOPTS},${X11DEPENDS}"

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

# Default preference for i.MX fork (matches 1.24.0.imx pattern)
DEFAULT_PREFERENCE = "-1"

# Compatible with i.MX platforms
COMPATIBLE_MACHINE = "(imx-nxp-bsp)"

PACKAGES =+ "${PN}-equalizer ${PN}-level"

FILES:${PN}-equalizer += "${libdir}/gstreamer-1.0/libequalizer.so"
FILES:${PN}-level += "${libdir}/gstreamer-1.0/liblevel.so"

CVE_PRODUCT = "gstreamer"
