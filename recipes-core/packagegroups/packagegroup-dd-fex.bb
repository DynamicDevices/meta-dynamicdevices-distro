SUMMARY = "Dynamic Devices optional x86 userspace emulation"
DESCRIPTION = "Headless FEX runtime and a trusted static x86-64 diagnostic fixture"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit packagegroup

COMPATIBLE_HOST = "aarch64.*-linux"
COMPATIBLE_HOST:libc-musl = "null"

RDEPENDS:${PN} = "fex-emu fex-smoke-test"
