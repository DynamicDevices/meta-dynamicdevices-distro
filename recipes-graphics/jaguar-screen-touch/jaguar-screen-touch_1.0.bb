SUMMARY = "Native Jaguar touchscreen mapping shared by all display applications"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://99-jaguar-screen-touch.rules"
S = "${WORKDIR}"
COMPATIBLE_MACHINE = "^imx8mm-jaguar-screen$"

do_install() {
    install -d ${D}${sysconfdir}/udev/rules.d
    install -m 0644 ${WORKDIR}/99-jaguar-screen-touch.rules \
        ${D}${sysconfdir}/udev/rules.d/99-jaguar-screen-touch.rules
}

FILES:${PN} += "${sysconfdir}/udev/rules.d/99-jaguar-screen-touch.rules"
