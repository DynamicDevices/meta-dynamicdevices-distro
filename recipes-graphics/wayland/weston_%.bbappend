# The NXP machine override enables the proprietary G2D renderer. Etnaviv uses
# Weston's normal GL renderer and must not pull virtual/libg2d/libgal-imx.
PACKAGECONFIG_G2D:dd-graphics-etnaviv = ""
PACKAGECONFIG:remove:dd-graphics-etnaviv = "imxg2d"
PACKAGECONFIG:append:dd-graphics-etnaviv = " egl"

# Check the renderer we actually intend to start, not just a successful link.
do_install:append:dd-graphics-etnaviv() {
    if [ ! -f ${D}${libdir}/libweston-${WESTON_MAJOR_VERSION}/gl-renderer.so ]; then
        bbfatal "Etnaviv graphics backend selected but Weston GL renderer is missing"
    fi
    if [ -f ${D}${libdir}/libweston-${WESTON_MAJOR_VERSION}/g2d-renderer.so ]; then
        bbfatal "Etnaviv graphics backend must not ship the NXP G2D renderer"
    fi
}

# Explicit G2D users still require the matching NXP renderer. The Screen kiosk
# no longer selects this backend.
PACKAGECONFIG_G2D:dd-graphics-imxg2d = "imxg2d"

# Fail during image preparation rather than shipping a compositor that rejects
# the Screen service's required option. Path matches the pinned NXP Meson build.
do_install:append:dd-graphics-imxg2d() {
    if [ ! -f ${D}${libdir}/libweston-${WESTON_MAJOR_VERSION}/g2d-renderer.so ]; then
        bbfatal "Screen G2D graphics backend selected but Weston G2D renderer is missing"
    fi
}
