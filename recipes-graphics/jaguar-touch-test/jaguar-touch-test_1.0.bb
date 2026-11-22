SUMMARY = "Jaguar browser-based touchscreen and multitouch test"
DESCRIPTION = "Manual touch and gesture test with bounded artwork compositing, lightweight contact overlays, optional trails and independent native-touch/pointer counters. Does not alter calibration."
# Includes Active-Edge brand artwork; do not offer its marks under the MIT licence.
LICENSE = "CLOSED"

SRC_URI = "file://index.html file://jaguar-touch-test"
S = "${WORKDIR}"

RDEPENDS:${PN} = "packagegroup-dd-kiosk-browser"
COMPATIBLE_MACHINE = "^imx8mm-jaguar-screen$"
DD_KIOSK_TEST_BROWSER ?= "${bindir}/${@d.getVar('DD_KIOSK_BROWSER_RUNTIME') or 'dd-kiosk-browser'}"

def jaguar_browser_replacement(d):
    import shlex
    path = d.getVar('DD_KIOSK_TEST_BROWSER')
    if not path or not path.startswith('/') or any(c in path for c in '\n\r\x00'):
        raise ValueError('DD_KIOSK_TEST_BROWSER must be an absolute single-line path')
    # The replacement is inside a double-quoted shell parameter default.
    shell_path = ''.join('\\' + c if c in '\\$`"}' else c for c in path)
    sed_path = ''.join('\\' + c if c in '\\&|' else c for c in shell_path)
    return shlex.quote('s|/usr/bin/dd-kiosk-browser|' + sed_path + '|g')

do_install() {
    install -d ${D}${datadir}/jaguar-touch-test ${D}${bindir}
    install -m 0644 ${WORKDIR}/index.html ${D}${datadir}/jaguar-touch-test/index.html
    install -m 0755 ${WORKDIR}/jaguar-touch-test ${D}${bindir}/jaguar-touch-test
    sed -i ${@jaguar_browser_replacement(d)} ${D}${bindir}/jaguar-touch-test
}

FILES:${PN} += "${datadir}/jaguar-touch-test/index.html"
