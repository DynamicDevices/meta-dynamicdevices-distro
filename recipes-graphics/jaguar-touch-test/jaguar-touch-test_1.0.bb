SUMMARY = "Jaguar browser-based touchscreen and multitouch test"
DESCRIPTION = "Manual touch and gesture test with bounded artwork compositing, lightweight contact overlays, optional trails and independent native-touch/pointer counters. Does not alter calibration."
# Includes Active-Edge brand artwork; do not offer its marks under the MIT licence.
LICENSE = "CLOSED"

SRC_URI = "file://index.html file://jaguar-touch-test"
S = "${WORKDIR}"

RDEPENDS:${PN} = "packagegroup-dd-kiosk-browser"
COMPATIBLE_MACHINE = "^imx8mm-jaguar-screen$"
DD_KIOSK_TEST_BROWSER ?= "${bindir}/${@d.getVar('DD_KIOSK_BROWSER_RUNTIME') or 'dd-kiosk-browser'}"

do_install() {
    install -d ${D}${datadir}/jaguar-touch-test ${D}${bindir}
    install -m 0644 ${WORKDIR}/index.html ${D}${datadir}/jaguar-touch-test/index.html
    install -m 0755 ${WORKDIR}/jaguar-touch-test ${D}${bindir}/jaguar-touch-test
    sed -i 's|/usr/bin/dd-kiosk-browser|${DD_KIOSK_TEST_BROWSER}|g' ${D}${bindir}/jaguar-touch-test
}

FILES:${PN} += "${datadir}/jaguar-touch-test/index.html"
