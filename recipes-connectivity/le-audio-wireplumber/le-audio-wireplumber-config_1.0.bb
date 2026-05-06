# SPDX-License-Identifier: MIT
SUMMARY = "WirePlumber fragment for LE Audio / Auracast (BAP broadcast) BlueZ roles"
DESCRIPTION = "Installs a drop-in under ${datadir}/wireplumber/wireplumber.conf.d/ so PipeWire's \
BlueZ monitor exposes BAP unicast + broadcast roles (NXP UM12155). Replace or extend per NXP \
LE Audio release / validated BlueZ build. See lmp-feature-le-audio.inc."

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2ffb40327"

SRC_URI = "file://51-bluez-imx-le-audio.conf"

S = "${WORKDIR}"

do_install() {
	install -d ${D}${datadir}/wireplumber/wireplumber.conf.d
	install -m 0644 ${WORKDIR}/51-bluez-imx-le-audio.conf \
		${D}${datadir}/wireplumber/wireplumber.conf.d/51-bluez-imx-le-audio.conf
}

FILES:${PN} += "${datadir}/wireplumber/wireplumber.conf.d/51-bluez-imx-le-audio.conf"

RDEPENDS:${PN} += "wireplumber"
