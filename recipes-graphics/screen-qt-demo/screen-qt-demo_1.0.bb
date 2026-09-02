SUMMARY = "Qt Quick display and touch proof for the Jaguar Screen"
DESCRIPTION = "Minimal fullscreen Qt Quick Wayland application for validating accelerated rendering and touch input."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://CMakeLists.txt \
    file://main.cpp \
    file://Main.qml \
    file://screen-qt-demo \
    file://screen-qt-demo.service \
"

S = "${WORKDIR}"

inherit qt6-cmake systemd

DEPENDS = "qtbase qtdeclarative qtdeclarative-native qtwayland"

SYSTEMD_SERVICE:${PN} = "screen-qt-demo.service"
SYSTEMD_AUTO_ENABLE:${PN} = "disable"

do_install:append() {
    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/screen-qt-demo ${D}${bindir}/screen-qt-demo-launcher

    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/screen-qt-demo.service \
        ${D}${systemd_system_unitdir}/screen-qt-demo.service
}

COMPATIBLE_MACHINE = "^imx8mm-jaguar-screen$"
