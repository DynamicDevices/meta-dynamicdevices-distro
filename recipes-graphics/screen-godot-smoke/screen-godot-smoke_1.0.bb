SUMMARY = "Godot runtime smoke project for the Jaguar Screen"
DESCRIPTION = "Installs a deterministic Godot 3 GLES2 project used to prove the target engine can load and execute GDScript."
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://godot-screen-smoke \
    file://project.godot \
    file://smoke.gd \
    file://smoke.tscn \
"

S = "${WORKDIR}"

RDEPENDS:${PN} = "godot3-frt"

do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/godot-screen-smoke ${D}${bindir}/godot-screen-smoke

    install -d ${D}${datadir}/godot-screen-smoke
    install -m 0644 ${WORKDIR}/project.godot ${D}${datadir}/godot-screen-smoke/project.godot
    install -m 0644 ${WORKDIR}/smoke.gd ${D}${datadir}/godot-screen-smoke/smoke.gd
    install -m 0644 ${WORKDIR}/smoke.tscn ${D}${datadir}/godot-screen-smoke/smoke.tscn
}

FILES:${PN} += "${datadir}/godot-screen-smoke"

COMPATIBLE_MACHINE = "^imx8mm-jaguar-screen$"
