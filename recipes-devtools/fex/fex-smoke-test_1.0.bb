SUMMARY = "Source-built static x86-64 smoke test for FEX board evaluation"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://x86_64-smoke.asm file://fex-smoke-test"
S = "${WORKDIR}"
DEPENDS = "nasm-native"
RDEPENDS:${PN} = "fex-emu"
COMPATIBLE_HOST = "aarch64.*-linux"
COMPATIBLE_HOST:libc-musl = "null"

do_compile() {
    nasm -f bin -o ${B}/x86_64-smoke ${WORKDIR}/x86_64-smoke.asm
}

do_install() {
    install -d ${D}${bindir} ${D}${datadir}/fex-emu/tests/empty-rootfs
    install -m 0755 ${B}/x86_64-smoke ${D}${datadir}/fex-emu/tests/x86_64-smoke
    install -m 0755 ${WORKDIR}/fex-smoke-test ${D}${bindir}/fex-smoke-test
    sed -i 's|@DATADIR@|${datadir}|g' ${D}${bindir}/fex-smoke-test
}

# This package intentionally carries an x86-64 ELF as data on an ARM64 target.
# It has no dynamic dependencies or symbols for the ARM strip tool to process.
INSANE_SKIP:${PN} += "arch"
INHIBIT_PACKAGE_STRIP = "1"
INHIBIT_PACKAGE_DEBUG_SPLIT = "1"
INHIBIT_SYSROOT_STRIP = "1"
FILES:${PN} += "${datadir}/fex-emu/tests"
