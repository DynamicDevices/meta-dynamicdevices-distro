# GStreamer 1.26.0 plugins-base recipe for Conversa v2.0 support

SUMMARY = "'Base' GStreamer plugins and helper libraries"
HOMEPAGE = "https://gstreamer.freedesktop.org/"
BUGTRACKER = "https://gitlab.freedesktop.org/gstreamer/gst-plugins-base/-/issues"
LICENSE = "LGPL-2.1-or-later"
LIC_FILES_CHKSUM = "file://COPYING;md5=69333daa044cb77e486cc36129f7a770"

# Use NXP i.MX fork of GStreamer plugins-base 1.26.0 for hardware acceleration
SRC_URI = "${GST1.0_SRC};branch=${SRCBRANCH}"
GST1.0_SRC ?= "gitsm://github.com/nxp-imx/gst-plugins-base.git;protocol=https"
SRCBRANCH = "MM_04.10.01_2508_L6.12.34"
SRCREV = "92c89c850b8295aa263fb6de8b5b29bf67057202"

S = "${WORKDIR}/git"

DEPENDS += "gstreamer1.0 iso-codes util-linux zlib"

inherit meson pkgconfig upstream-version-is-even gobject-introspection

# opengl packageconfig factored out to make it easy for distros
# and BSP layers to choose OpenGL APIs/platforms/window systems
PACKAGECONFIG_X11 = "${@bb.utils.contains('DISTRO_FEATURES', 'x11', 'opengl glx', '', d)}"
PACKAGECONFIG_GL ?= "${@bb.utils.contains('DISTRO_FEATURES', 'opengl', 'gles2 egl ${PACKAGECONFIG_X11}', '', d)}"

PACKAGECONFIG ??= " \
    ${@bb.utils.contains('DISTRO_FEATURES', 'orc', 'orc', '', d)} \
    ${PACKAGECONFIG_GL} \
    ${@bb.utils.filter('DISTRO_FEATURES', 'alsa x11', d)} \
    jpeg ogg pango png theora vorbis \
    ${@bb.utils.contains('DISTRO_FEATURES', 'wayland', 'wayland egl', '', d)} \
"

OPENGL_APIS = 'opengl gles2'
OPENGL_PLATFORMS = 'egl glx'

X11DEPENDS = "virtual/libx11 libsm libxrender libxv"
X11ENABLEOPTS = "-Dx11=enabled -Dxvideo=enabled -Dxshm=enabled"
X11DISABLEOPTS = "-Dx11=disabled -Dxvideo=disabled -Dxshm=disabled"

PACKAGECONFIG[alsa]         = "-Dalsa=enabled,-Dalsa=disabled,alsa-lib"
PACKAGECONFIG[cdparanoia]   = "-Dcdparanoia=enabled,-Dcdparanoia=disabled,cdparanoia"
PACKAGECONFIG[egl]          = "-Degl=enabled,-Degl=disabled,virtual/egl"
PACKAGECONFIG[gio-unix-2.0] = "-Dgio-unix-2.0=enabled,-Dgio-unix-2.0=disabled,glib-2.0"
PACKAGECONFIG[gl]           = "-Dgl=enabled,-Dgl=disabled,virtual/libgl libglu"
PACKAGECONFIG[gles2]        = "-Dgles2=enabled,-Dgles2=disabled,virtual/libgles2"
PACKAGECONFIG[glx]          = "-Dglx=enabled,-Dglx=disabled,virtual/libgl"
PACKAGECONFIG[jpeg]         = "-Dgl-jpeg=enabled,-Dgl-jpeg=disabled,jpeg"
PACKAGECONFIG[ogg]          = "-Dogg=enabled,-Dogg=disabled,libogg"
PACKAGECONFIG[opengl]       = "-Dopengl=enabled,-Dopengl=disabled"
PACKAGECONFIG[orc]          = "-Dorc=enabled,-Dorc=disabled,orc orc-native"
PACKAGECONFIG[pango]        = "-Dpango=enabled,-Dpango=disabled,pango"
PACKAGECONFIG[png]          = "-Dgl-png=enabled,-Dgl-png=disabled,libpng"
PACKAGECONFIG[theora]       = "-Dtheora=enabled,-Dtheora=disabled,libtheora"
PACKAGECONFIG[tremor]       = "-Dtremor=enabled,-Dtremor=disabled,tremor"
PACKAGECONFIG[vorbis]       = "-Dvorbis=enabled,-Dvorbis=disabled,libvorbis"
PACKAGECONFIG[wayland]      = "-Dwayland=enabled,-Dwayland=disabled,wayland-native wayland wayland-protocols libdrm"
PACKAGECONFIG[x11]          = "${X11ENABLEOPTS},${X11DISABLEOPTS},${X11DEPENDS}"

EXTRA_OEMESON += " \
    -Ddoc=disabled \
    -Dexamples=disabled \
    ${@get_opengl_cmdline_list('gl_api', d.getVar('OPENGL_APIS'), d)} \
    ${@get_opengl_cmdline_list('gl_platform', d.getVar('OPENGL_PLATFORMS'), d)} \
"

def get_opengl_cmdline_list(switch_name, options, d):
    selected_options = []
    if bb.utils.contains('PACKAGECONFIG', 'opengl', True, False, d):
        for option in options.split():
            if bb.utils.contains('PACKAGECONFIG', option, True, False, d):
                selected_options.append(option)
    if selected_options:
        return '-D' + switch_name + '=' + ','.join(selected_options)
    else:
        return '-D' + switch_name + '=auto'

GIR_MESON_ENABLE_FLAG = "enabled"
GIR_MESON_DISABLE_FLAG = "disabled"

# Default preference for i.MX fork (matches 1.24.0.imx pattern)
DEFAULT_PREFERENCE = "-1"

# Compatible with i.MX platforms
COMPATIBLE_MACHINE = "(imx-nxp-bsp)"

PACKAGES =+ "${PN}-apps ${PN}-meta"

FILES:${PN}-apps = "${bindir}"
FILES:${PN}-meta = "${datadir}/gst-plugins-base/1.0/gst-plugins-base.pot"

RDEPENDS:${PN}-dev += "${PN}-apps (= ${EXTENDPKGV})"

CVE_PRODUCT = "gstreamer"
