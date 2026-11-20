# Keep the serial console verbose. Remove only the virtual-console sinks from
# OSTree's generated kernel arguments; never edit a live U-Boot environment.
OSTREE_KERNEL_ARGS:remove = "${@' '.join('console=tty%d' % n for n in range(64))}"
OSTREE_KERNEL_ARGS:append = " splash logo.nologo vt.global_cursor_default=0"

# Keep Linux's initial mode equal to the proved U-Boot stream on DT510.
# SEC DSIM applies its existing four-lane horizontal timing adjustment.
OSTREE_KERNEL_ARGS:append:imx8mm-jaguar-dt510 = " video=HDMI-A-1:1280x720@60e"

CORE_IMAGE_BASE_INSTALL += "aesl-display-splash aesl-display-session"
