SUMMARY = "Earlier serial login prompt for Jaguar Screen debug images"
DESCRIPTION = "Overrides serial-getty Type=idle only in development images so the diagnostic prompt is printed as soon as the service starts."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://COPYING;md5=58e968fa7d52287094a10513bbd44a9c"

FILESEXTRAPATHS:prepend := "${THISDIR}:"

SRC_URI = " \
    file://COPYING \
    file://10-screen-debug-no-idle.conf \
"

S = "${WORKDIR}"

do_install() {
    install -d ${D}${systemd_system_unitdir}/serial-getty@.service.d
    install -m 0644 \
        ${WORKDIR}/10-screen-debug-no-idle.conf \
        ${D}${systemd_system_unitdir}/serial-getty@.service.d/10-screen-debug-no-idle.conf
}

FILES:${PN} = "${systemd_system_unitdir}/serial-getty@.service.d/10-screen-debug-no-idle.conf"

COMPATIBLE_MACHINE = "^imx8mm-jaguar-screen$"
