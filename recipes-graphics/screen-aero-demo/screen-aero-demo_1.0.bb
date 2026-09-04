SUMMARY = "Touch-enabled aero pressure digital-twin demonstration"
DESCRIPTION = "Installs and starts the Active-Edge Godot 3 aero pressure demo on the Jaguar Screen."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=e751627664afcd19daaa085e1699cf09"

SRC_URI = "git://github.com/active-esl/godot-demos.git;protocol=https;branch=main"
SRCREV = "2aa940639e5605b09542de59cb0dc3990470f0a7"
S = "${WORKDIR}/git"

inherit systemd

SYSTEMD_SERVICE:${PN} = "screen-aero-demo.service"
SYSTEMD_AUTO_ENABLE:${PN} = "disable"

RDEPENDS:${PN} = "godot3-frt"

do_install() {
    install -d ${D}${datadir}/godot-demos/aero-pressure-digital-twin
    install -m 0644 ${WORKDIR}/active-edge-aero-pressure.pck \
        ${D}${datadir}/godot-demos/aero-pressure-digital-twin/active-edge-aero-pressure.pck

    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/screen-aero-demo ${D}${bindir}/screen-aero-demo

    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/screen-aero-demo.service \
        ${D}${systemd_system_unitdir}/screen-aero-demo.service
}

FILES:${PN} += "${datadir}/godot-demos"

COMPATIBLE_MACHINE = "^imx8mm-jaguar-screen$"

SRC_URI += " \
    https://github.com/active-esl/godot-demos/releases/download/aero-pressure-v1.0.0/active-edge-aero-pressure-2aa940639e56.pck;downloadfilename=active-edge-aero-pressure.pck;sha256sum=804479119a36881537ea5875d7a335f0a13f8f13ea296125a7791870d38d752e \
    file://screen-aero-demo \
    file://screen-aero-demo.service \
"
