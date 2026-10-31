SUMMARY = "Dynamic Devices Weston browser kiosk launcher"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = " \
    file://dd-kiosk-browser \
    file://dd-kiosk-browser.service \
    file://dd-kiosk-browser.env \
    file://offline.html \
    file://90-dd-kiosk-browser \
    file://kiosk-policy.json \
    file://dd-kiosk-linker-guard \
    file://weston-linker-guard.conf \
    file://dd-kiosk-native-runtime.conf \
"
SRC_URI:append = "${@bb.utils.contains('DISTRO_FEATURES', 'pulseaudio', ' file://dd-kiosk-browser-audio.conf', '', d)}"
SRC_URI:append:imx8mm-jaguar-screen = "${@bb.utils.contains('DISTRO_FEATURES', 'pulseaudio', ' file://dd-kiosk-browser-screen-audio.conf', '', d)}"

S = "${WORKDIR}"

inherit systemd

PACKAGE_ARCH = "${MACHINE_ARCH}"

SYSTEMD_SERVICE:${PN} = "dd-kiosk-browser.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

RDEPENDS:${PN} = "chromium-ozone-wayland networkmanager-daemon"
# The machine's ALSA recipe owns its default hardware routing configuration.
RDEPENDS:${PN}:append:imx8mm-jaguar-screen = " alsa-state"

do_install() {
    install -d ${D}${bindir} ${D}${libexecdir} ${D}${systemd_system_unitdir} ${D}${systemd_system_unitdir}/weston.service.d ${D}${systemd_system_unitdir}/dd-kiosk-browser.service.d ${D}${sysconfdir}/default ${D}${datadir}/dd-kiosk-browser ${D}${sysconfdir}/NetworkManager/dispatcher.d ${D}${sysconfdir}/chromium/policies/managed
    install -m 0755 ${WORKDIR}/dd-kiosk-browser ${D}${bindir}/dd-kiosk-browser
    install -m 0644 ${WORKDIR}/dd-kiosk-browser.service ${D}${systemd_system_unitdir}/dd-kiosk-browser.service
    install -m 0644 ${WORKDIR}/dd-kiosk-browser.env ${D}${sysconfdir}/default/dd-kiosk-browser
    install -m 0644 ${WORKDIR}/offline.html ${D}${datadir}/dd-kiosk-browser/offline.html
    install -m 0755 ${WORKDIR}/90-dd-kiosk-browser ${D}${sysconfdir}/NetworkManager/dispatcher.d/90-dd-kiosk-browser
    install -m 0644 ${WORKDIR}/kiosk-policy.json ${D}${sysconfdir}/chromium/policies/managed/dd-kiosk-browser.json
    # Production stays locked down; only the explicit development build enables tools.
    if [ "${DEV_MODE}" = "1" ]; then
        sed -i 's/"DeveloperToolsAvailability": 2/"DeveloperToolsAvailability": 1/' ${D}${sysconfdir}/chromium/policies/managed/dd-kiosk-browser.json
    fi
    install -m 0755 ${WORKDIR}/dd-kiosk-linker-guard ${D}${libexecdir}/dd-kiosk-linker-guard
    install -m 0644 ${WORKDIR}/weston-linker-guard.conf ${D}${systemd_system_unitdir}/weston.service.d/zzzz-kiosk-linker-guard.conf
    install -m 0644 ${WORKDIR}/dd-kiosk-native-runtime.conf ${D}${systemd_system_unitdir}/dd-kiosk-browser.service.d/zzzz-native-runtime.conf
    if ${@bb.utils.contains('DISTRO_FEATURES', 'pulseaudio', 'true', 'false', d)}; then
        install -d ${D}${systemd_system_unitdir}/dd-kiosk-browser.service.d
        install -m 0644 ${WORKDIR}/dd-kiosk-browser-audio.conf ${D}${systemd_system_unitdir}/dd-kiosk-browser.service.d/audio.conf
    fi
}

do_install:append:imx8mm-jaguar-screen() {
    if ${@bb.utils.contains('DISTRO_FEATURES', 'pulseaudio', 'true', 'false', d)}; then
        install -m 0644 ${WORKDIR}/dd-kiosk-browser-screen-audio.conf ${D}${systemd_system_unitdir}/dd-kiosk-browser.service.d/screen-audio.conf
    fi
}

CONFFILES:${PN} = "${sysconfdir}/default/dd-kiosk-browser ${sysconfdir}/chromium/policies/managed/dd-kiosk-browser.json"
FILES:${PN} += "${datadir}/dd-kiosk-browser/offline.html ${libexecdir}/dd-kiosk-linker-guard ${sysconfdir}/NetworkManager/dispatcher.d/90-dd-kiosk-browser ${sysconfdir}/chromium/policies/managed/dd-kiosk-browser.json ${systemd_system_unitdir}/weston.service.d/zzzz-kiosk-linker-guard.conf ${systemd_system_unitdir}/dd-kiosk-browser.service.d/audio.conf ${systemd_system_unitdir}/dd-kiosk-browser.service.d/zzzz-native-runtime.conf"
FILES:${PN}:append:imx8mm-jaguar-screen = " ${systemd_system_unitdir}/dd-kiosk-browser.service.d/screen-audio.conf"
