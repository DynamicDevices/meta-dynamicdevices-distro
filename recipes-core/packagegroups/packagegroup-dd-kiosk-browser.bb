SUMMARY = "Dynamic Devices browser kiosk runtime"
DESCRIPTION = "Browser kiosk bundle; the selected runtime supplies its browser and launcher"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit packagegroup

DD_KIOSK_BROWSER_RUNTIME ?= "dd-kiosk-browser"

RDEPENDS:${PN} = "${DD_KIOSK_BROWSER_RUNTIME}"
