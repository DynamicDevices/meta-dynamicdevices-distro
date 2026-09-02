SUMMARY = "Dynamic Devices host audio runtime"
DESCRIPTION = "PulseAudio runtime selected by the Dynamic Devices product feature contract"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit packagegroup

# This packagegroup is machine-specific because Sentai retains its existing
# commercial-codec-enabled SoX payload during the migration.
PACKAGE_ARCH = "${MACHINE_ARCH}"

RDEPENDS:${PN} = " \
    pulseaudio \
    pulseaudio-server \
    pulseaudio-misc \
"

RDEPENDS:${PN}:append:imx8mm-jaguar-sentai = " sox"
