# The NXP machine override enables the proprietary G2D renderer. Etnaviv uses
# Weston's normal GL renderer and must not pull virtual/libg2d/libgal-imx.
PACKAGECONFIG_G2D:dd-graphics-etnaviv = ""
PACKAGECONFIG:remove:dd-graphics-etnaviv = "imxg2d"

# The Screen service deliberately requires --use-g2d. Build the corresponding
# NXP renderer instead of inheriting a GL-only compositor from the kiosk path.
PACKAGECONFIG_G2D:dd-graphics-imxg2d = "imxg2d"

# Fail during image preparation rather than shipping a compositor that rejects
# the Screen service's required option. Path matches the pinned NXP Meson build.
do_install:append:dd-graphics-imxg2d() {
    if [ ! -f ${D}${libdir}/libweston-${WESTON_MAJOR_VERSION}/g2d-renderer.so ]; then
        bbfatal "Screen G2D graphics backend selected but Weston G2D renderer is missing"
    fi
}
