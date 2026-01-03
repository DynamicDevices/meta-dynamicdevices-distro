SUMMARY = "CRA Audit System for EU Cyber Resilience Act Compliance"
DESCRIPTION = "Distro-level audit event detection, queuing, and reporting system for CRA compliance on Foundries.io devices"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI = " \
    file://cra-audit-handler.sh \
    file://cra-audit-monitor.service \
    file://cra-audit-queue-processor.service \
    file://cra-audit-queue-processor.timer \
    file://cra-audit-config.env \
    file://cra-audit.rules \
    file://cra-audit-dispatcher.sh \
    file://auditd.conf \
    file://cra-audit-test.sh \
"

RDEPENDS:${PN} = " \
    bash \
    curl \
    openssl \
    systemd \
    util-linux \
    coreutils \
    findutils \
    jq \
    audit \
"

inherit systemd

SYSTEMD_SERVICE:${PN} = " \
    cra-audit-monitor.service \
    cra-audit-queue-processor.service \
    cra-audit-queue-processor.timer \
"

# Auto-enable queue processor timer, but monitor service is manual
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

do_install() {
    # Install main audit handler script
    install -d ${D}${sbindir}
    install -m 0755 ${WORKDIR}/cra-audit-handler.sh ${D}${sbindir}/
    install -m 0755 ${WORKDIR}/cra-audit-dispatcher.sh ${D}${sbindir}/
    install -m 0755 ${WORKDIR}/cra-audit-test.sh ${D}${sbindir}/

    # Install systemd service files
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/cra-audit-monitor.service ${D}${systemd_system_unitdir}/
    install -m 0644 ${WORKDIR}/cra-audit-queue-processor.service ${D}${systemd_system_unitdir}/
    install -m 0644 ${WORKDIR}/cra-audit-queue-processor.timer ${D}${systemd_system_unitdir}/

    # Install audit configuration
    install -d ${D}${sysconfdir}/audit
    install -m 0644 ${WORKDIR}/auditd.conf ${D}${sysconfdir}/audit/
    install -d ${D}${sysconfdir}/audit/rules.d
    install -m 0644 ${WORKDIR}/cra-audit.rules ${D}${sysconfdir}/audit/rules.d/

    # Install distro configuration
    install -d ${D}${sysconfdir}/default
    install -m 0644 ${WORKDIR}/cra-audit-config.env ${D}${sysconfdir}/default/cra-audit-system

    # Create audit directories with proper permissions
    install -d ${D}${localstatedir}/sota/audit-queue
    install -d ${D}${localstatedir}/sota/audit-uploaded
    # Create log directory in /var/sota instead of /var/log to avoid symlink issues
    install -d ${D}${localstatedir}/sota/logs
}

FILES:${PN} = " \
    ${sbindir}/cra-audit-handler.sh \
    ${sbindir}/cra-audit-dispatcher.sh \
    ${sbindir}/cra-audit-test.sh \
    ${systemd_system_unitdir}/cra-audit-monitor.service \
    ${systemd_system_unitdir}/cra-audit-queue-processor.service \
    ${systemd_system_unitdir}/cra-audit-queue-processor.timer \
    ${sysconfdir}/default/cra-audit-system \
    ${sysconfdir}/audit/auditd.conf \
    ${sysconfdir}/audit/rules.d/cra-audit.rules \
    ${localstatedir}/sota/audit-queue \
    ${localstatedir}/sota/audit-uploaded \
    ${localstatedir}/sota/logs \
"

# This is a distro-level compliance feature
PROVIDES = "cra-compliance-audit"

# Compatible with all Dynamic Devices machines using Foundries.io
COMPATIBLE_MACHINE = "imx93-jaguar-eink|imx8mm-jaguar-sentai|imx8mm-jaguar-dt510|imx8mm-jaguar-phasora|imx8mm-jaguar-inst|imx8mm-jaguar-handheld"
