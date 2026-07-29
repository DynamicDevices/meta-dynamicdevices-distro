# DEPRECATED in public distro — portal gateway conf.d lives in private subscriber.
# See active-esl/factory-aesl-lab-meta-subscriber-overrides recipes-sota/aesl-gateway-defaults.
#
# Recipe kept as a no-op stub so old references fail closed rather than ship URLs.

SUMMARY = "stub — AESL gateway defaults moved to private subscriber"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

ALLOW_EMPTY:${PN} = "1"
