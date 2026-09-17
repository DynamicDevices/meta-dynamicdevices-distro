FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://0001-Only-query-DRI-driver-dir-for-X11-Ozone.patch \
    file://0002-bytemuck-Drop-removed-LaneCount-bound.patch \
"

# Keep this late link fix in do_compile so the already built Chromium tree can
# be resumed without re-running do_unpack and discarding its object files.
DD_CHROMIUM_GBM_PATCH := "${THISDIR}/${PN}/0003-gl-Match-GBM-EGL-native-window-type.patch"
do_compile[file-checksums] += "${DD_CHROMIUM_GBM_PATCH}:True"
do_compile:prepend() {
    if ! grep -Fq '#include <gbm.h>' "${S}/ui/gl/gl_surface_egl.cc"; then
        patch -d "${S}" -p1 --fuzz=0 < "${DD_CHROMIUM_GBM_PATCH}"
    fi
}
