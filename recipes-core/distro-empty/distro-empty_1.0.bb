# Trivial recipe so the layer is a valid BitBake collection
SUMMARY = "meta-dynamicdevices-distro layer presence marker"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI = "file://empty"
S = "${WORKDIR}"
EXCLUDE_FROM_WORLD = "1"

do_install() {
    install -d ${D}/${datadir}/doc/distro-empty
    install -m 644 ${WORKDIR}/empty ${D}/${datadir}/doc/distro-empty/README
}
FILES:${PN} = "${datadir}/doc/distro-empty/README"
