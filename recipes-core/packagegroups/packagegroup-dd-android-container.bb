SUMMARY = "Dynamic Devices Android container runtime"
DESCRIPTION = "Provider-neutral Android container bundle, currently implemented by Waydroid"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit packagegroup

RDEPENDS:${PN} = "waydroid"
