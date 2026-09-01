SUMMARY = "Flutter display and touch proof for the Jaguar Screen"
DESCRIPTION = "Launches the ivi-homescreen multi-touch test bundle fullscreen on Weston."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://screen-flutter-demo.service \
    file://screen-flutter-demo \
    file://99-jaguar-screen-touch.rules \
"

S = "${WORKDIR}"

inherit systemd

SYSTEMD_SERVICE:${PN} = "screen-flutter-demo.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

RDEPENDS:${PN} = " \
    ivi-homescreen \
    ivi-homescreen-multi-touch-test \
"

do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/screen-flutter-demo ${D}${bindir}/screen-flutter-demo

    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/screen-flutter-demo.service \
        ${D}${systemd_system_unitdir}/screen-flutter-demo.service

    install -d ${D}${sysconfdir}/udev/rules.d
    install -m 0644 ${WORKDIR}/99-jaguar-screen-touch.rules \
        ${D}${sysconfdir}/udev/rules.d/99-jaguar-screen-touch.rules
}

FILES:${PN} += "${sysconfdir}/udev/rules.d/99-jaguar-screen-touch.rules"

COMPATIBLE_MACHINE = "^imx8mm-jaguar-screen$"
