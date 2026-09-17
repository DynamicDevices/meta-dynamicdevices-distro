FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://0001-Only-query-DRI-driver-dir-for-X11-Ozone.patch \
    file://0002-bytemuck-Drop-removed-LaneCount-bound.patch \
"
