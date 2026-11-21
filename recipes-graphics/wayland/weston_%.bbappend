# DT510 only. Renderer selection and GPU access policy are unchanged.
FILESEXTRAPATHS:prepend := "${THISDIR}/${BPN}:"
# Upstream uses MACHINE_SOCARCH; this board-specific ABI must not share a
# same-version package with unpatched compositors for other i.MX8MM boards.
PACKAGE_ARCH:imx8mm-jaguar-dt510 = "${MACHINE_ARCH}"
SRC_URI:append:imx8mm-jaguar-dt510 = " ${@bb.utils.contains('DISTRO_FEATURES', 'display-boot-splash', 'file://0001-retain-boot-display-until-background.patch', '', d)}"
