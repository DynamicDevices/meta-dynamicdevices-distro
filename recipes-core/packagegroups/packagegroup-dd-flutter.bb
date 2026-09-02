SUMMARY = "Dynamic Devices Flutter UI runtime"
DESCRIPTION = "Flutter engine and launcher selected by the Dynamic Devices product feature contract"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit packagegroup

RDEPENDS:${PN} = " \
    flutter-engine \
    ivi-homescreen \
"
