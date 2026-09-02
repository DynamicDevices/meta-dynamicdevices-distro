SUMMARY = "Touch-enabled aero pressure digital-twin demonstration"
DESCRIPTION = "Installs and starts the Active-Edge Godot 3 aero pressure demo on the Jaguar Screen."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=e751627664afcd19daaa085e1699cf09"

SRC_URI = "git://github.com/active-esl/godot-demos.git;protocol=https;branch=main"
SRCREV = "72b5fa043dfd16d813374428891da44170adf984"
S = "${WORKDIR}/git"

inherit systemd

SYSTEMD_SERVICE:${PN} = "screen-aero-demo.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

RDEPENDS:${PN} = "godot3-frt"

do_install() {
    install -d ${D}${datadir}/godot-demos/aero-pressure-digital-twin
    cp -R ${S}/demos/aero-pressure-digital-twin/. \
        ${D}${datadir}/godot-demos/aero-pressure-digital-twin/

    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/screen-aero-demo ${D}${bindir}/screen-aero-demo

    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/screen-aero-demo.service \
        ${D}${systemd_system_unitdir}/screen-aero-demo.service
}

FILES:${PN} += "${datadir}/godot-demos"

COMPATIBLE_MACHINE = "^imx8mm-jaguar-screen$"

SRC_URI += " \
    file://screen-aero-demo \
    file://screen-aero-demo.service \
"
