SUMMARY = "Power Analysis Suite for i.MX93 development boards"
DESCRIPTION = "Comprehensive power monitoring and analysis tools specifically designed for i.MX93 Jaguar E-Ink board development and optimization"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI = " \
    file://power-analysis-suite.sh \
    file://pm-analyzer.sh \
"

S = "${WORKDIR}"

# This package is only for development builds
COMPATIBLE_MACHINE = "(imx93-jaguar-eink)"

do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/power-analysis-suite.sh ${D}${bindir}/power-analysis-suite
    install -m 0755 ${WORKDIR}/pm-analyzer.sh ${D}${bindir}/pm-analyzer
}

FILES:${PN} = " \
    ${bindir}/power-analysis-suite \
    ${bindir}/pm-analyzer \
"

# Runtime dependencies for full functionality
RDEPENDS:${PN} = " \
    bash \
    coreutils \
    util-linux \
    procps \
"

# Recommended packages for enhanced functionality (all verified for scarthgap/v95)
RRECOMMENDS:${PN} = " \
    powertop \
    iotop \
    htop \
    perf \
    iw \
    i2c-tools \
    lmsensors \
    ethtool \
    wireless-tools \
    trace-cmd \
    upower \
"
