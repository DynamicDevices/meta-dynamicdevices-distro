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

S = "${WORKDIR}"

inherit systemd

PACKAGE_ARCH = "${MACHINE_ARCH}"

# Boards with a preferred physical output name it here. Keeping this as a
# machine override avoids encoding card indices or Screen-specific policy in
# the generic kiosk launcher.
DD_KIOSK_AUDIO_CARD ?= ""
DD_KIOSK_AUDIO_CARD:imx8mm-jaguar-screen = "wm8524audio"

SYSTEMD_SERVICE:${PN} = "dd-kiosk-browser.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

RDEPENDS:${PN} = "chromium-ozone-wayland networkmanager-daemon"

do_install() {
    install -d ${D}${bindir} ${D}${libexecdir} ${D}${systemd_system_unitdir} ${D}${systemd_system_unitdir}/weston.service.d ${D}${systemd_system_unitdir}/dd-kiosk-browser.service.d ${D}${sysconfdir}/default ${D}${datadir}/dd-kiosk-browser ${D}${sysconfdir}/NetworkManager/dispatcher.d ${D}${sysconfdir}/chromium/policies/managed
    install -m 0755 ${WORKDIR}/dd-kiosk-browser ${D}${bindir}/dd-kiosk-browser
    install -m 0644 ${WORKDIR}/dd-kiosk-browser.service ${D}${systemd_system_unitdir}/dd-kiosk-browser.service
    install -m 0644 ${WORKDIR}/dd-kiosk-browser.env ${D}${sysconfdir}/default/dd-kiosk-browser
    install -m 0644 ${WORKDIR}/offline.html ${D}${datadir}/dd-kiosk-browser/offline.html
    install -m 0755 ${WORKDIR}/90-dd-kiosk-browser ${D}${sysconfdir}/NetworkManager/dispatcher.d/90-dd-kiosk-browser
    install -m 0644 ${WORKDIR}/kiosk-policy.json ${D}${sysconfdir}/chromium/policies/managed/dd-kiosk-browser.json
    install -m 0755 ${WORKDIR}/dd-kiosk-linker-guard ${D}${libexecdir}/dd-kiosk-linker-guard
    install -m 0644 ${WORKDIR}/weston-linker-guard.conf ${D}${systemd_system_unitdir}/weston.service.d/zzzz-kiosk-linker-guard.conf
    install -m 0644 ${WORKDIR}/dd-kiosk-native-runtime.conf ${D}${systemd_system_unitdir}/dd-kiosk-browser.service.d/zzzz-native-runtime.conf
    if ${@bb.utils.contains('DISTRO_FEATURES', 'pulseaudio', 'true', 'false', d)}; then
        install -d ${D}${systemd_system_unitdir}/dd-kiosk-browser.service.d
        install -m 0644 ${WORKDIR}/dd-kiosk-browser-audio.conf ${D}${systemd_system_unitdir}/dd-kiosk-browser.service.d/audio.conf
    fi
    if [ -n "${DD_KIOSK_AUDIO_CARD}" ]; then
        printf '%s\n' \
            'pcm.!default { type hw; card ${DD_KIOSK_AUDIO_CARD}; device 0; }' \
            'ctl.!default { type hw; card ${DD_KIOSK_AUDIO_CARD}; }' \
            > ${D}${sysconfdir}/asound.conf
    fi
}

CONFFILES:${PN} = "${sysconfdir}/default/dd-kiosk-browser ${sysconfdir}/chromium/policies/managed/dd-kiosk-browser.json"
FILES:${PN} += "${datadir}/dd-kiosk-browser/offline.html ${libexecdir}/dd-kiosk-linker-guard ${sysconfdir}/NetworkManager/dispatcher.d/90-dd-kiosk-browser ${sysconfdir}/chromium/policies/managed/dd-kiosk-browser.json ${systemd_system_unitdir}/weston.service.d/zzzz-kiosk-linker-guard.conf ${systemd_system_unitdir}/dd-kiosk-browser.service.d/audio.conf ${systemd_system_unitdir}/dd-kiosk-browser.service.d/zzzz-native-runtime.conf ${sysconfdir}/asound.conf"
