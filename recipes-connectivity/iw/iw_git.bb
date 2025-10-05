SUMMARY = "nl80211 based CLI configuration utility for wireless devices with TWT support"
DESCRIPTION = "iw is a new nl80211 based CLI configuration utility for wireless devices. \
This version includes Target Wake Time (TWT) support for WiFi 6 power optimization."
HOMEPAGE = "https://wireless.wiki.kernel.org/en/users/documentation/iw"
SECTION = "base"
LICENSE = "ISC"
LIC_FILES_CHKSUM = "file://COPYING;md5=878618a5c4af25e9b93ef0be1a93f774"

DEPENDS = "libnl pkgconfig-native"

# Use git source to get latest version with TWT support
SRCREV = "v6.9"
SRC_URI = "git://git.kernel.org/pub/scm/linux/kernel/git/jberg/iw.git;protocol=https;branch=master"

S = "${WORKDIR}/git"
PV = "6.9+git${SRCPV}"

# Ensure proper linking flags
TARGET_CC_ARCH += "${LDFLAGS}"

EXTRA_OEMAKE = "\
    'PREFIX=${prefix}' \
    'SBINDIR=${sbindir}' \
    'MANDIR=${mandir}' \
"

do_compile() {
    oe_runmake
}

do_install() {
    oe_runmake 'DESTDIR=${D}' 'PREFIX=${prefix}' install
}

# Package information
PACKAGES = "${PN} ${PN}-dbg ${PN}-doc"
FILES:${PN} = "${sbindir}/iw"
FILES:${PN}-doc = "${mandir}"

# Ensure this version is preferred over the default
DEFAULT_PREFERENCE = "1"