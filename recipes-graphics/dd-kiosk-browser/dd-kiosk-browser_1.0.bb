SUMMARY = "Dynamic Devices Weston browser kiosk launcher"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://dd-kiosk-browser \
    file://dd-kiosk-browser.service \
    file://dd-kiosk-browser.env \
    file://offline.html \
    file://90-dd-kiosk-browser \
"

S = "${WORKDIR}"

inherit systemd

SYSTEMD_SERVICE:${PN} = "dd-kiosk-browser.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

RDEPENDS:${PN} = "chromium-ozone-wayland"

do_install() {
    install -d ${D}${bindir} ${D}${systemd_system_unitdir} ${D}${sysconfdir}/default ${D}${datadir}/dd-kiosk-browser ${D}${sysconfdir}/NetworkManager/dispatcher.d
    install -m 0755 ${WORKDIR}/dd-kiosk-browser ${D}${bindir}/dd-kiosk-browser
    install -m 0644 ${WORKDIR}/dd-kiosk-browser.service ${D}${systemd_system_unitdir}/dd-kiosk-browser.service
    install -m 0644 ${WORKDIR}/dd-kiosk-browser.env ${D}${sysconfdir}/default/dd-kiosk-browser
    install -m 0644 ${WORKDIR}/offline.html ${D}${datadir}/dd-kiosk-browser/offline.html
    install -m 0755 ${WORKDIR}/90-dd-kiosk-browser ${D}${sysconfdir}/NetworkManager/dispatcher.d/90-dd-kiosk-browser
}

CONFFILES:${PN} = "${sysconfdir}/default/dd-kiosk-browser"
FILES:${PN} += "${datadir}/dd-kiosk-browser/offline.html ${sysconfdir}/NetworkManager/dispatcher.d/90-dd-kiosk-browser"
