SUMMARY = "Console-free AESL splash to Weston session handover"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"
SRC_URI = "file://psplash-start.conf file://psplash-progress.conf file://weston-splash.conf file://weston-aesl.ini file://aesl-splash-quit.service file://no-vt-getty.conf"
PACKAGE_ARCH = "${MACHINE_ARCH}"
FILESEXTRAPATHS:prepend := "${THISDIR}/${BPN}/${MACHINE}:"
S = "${WORKDIR}"
inherit systemd features_check
REQUIRED_DISTRO_FEATURES = "display-boot-splash wayland systemd"
RDEPENDS:${PN} = "aesl-display-splash psplash weston weston-init"
SYSTEMD_SERVICE:${PN} = "aesl-splash-quit.service"

do_install() {
    install -d ${D}${systemd_system_unitdir} ${D}${sysconfdir}/xdg/weston
    install -m 0644 ${WORKDIR}/aesl-splash-quit.service ${D}${systemd_system_unitdir}/
    install -m 0644 ${WORKDIR}/weston-aesl.ini ${D}${sysconfdir}/xdg/weston/
    for unit in psplash-start psplash-systemd weston getty@; do
        install -d ${D}${systemd_system_unitdir}/$unit.service.d
    done
    install -m 0644 ${WORKDIR}/psplash-start.conf ${D}${systemd_system_unitdir}/psplash-start.service.d/aesl.conf
    install -m 0644 ${WORKDIR}/psplash-progress.conf ${D}${systemd_system_unitdir}/psplash-systemd.service.d/aesl.conf
    install -m 0644 ${WORKDIR}/weston-splash.conf ${D}${systemd_system_unitdir}/weston.service.d/20-aesl.conf
    install -m 0644 ${WORKDIR}/no-vt-getty.conf ${D}${systemd_system_unitdir}/getty@.service.d/aesl.conf
    install -d ${D}${libdir}/tmpfiles.d
    printf '%s\n' 'd /var/rootdirs/home/weston 0750 weston weston -' > ${D}${libdir}/tmpfiles.d/aesl-weston.conf
    install -d ${D}${sysconfdir}/udev/rules.d
    printf '%s\n' 'SUBSYSTEM=="graphics", KERNEL=="fb0", TAG+="systemd"' > ${D}${sysconfdir}/udev/rules.d/71-aesl-splash.rules
}

FILES:${PN} += "${systemd_system_unitdir} ${libdir}/tmpfiles.d"
