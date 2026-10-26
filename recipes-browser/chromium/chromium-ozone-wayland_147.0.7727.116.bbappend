FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://0001-Only-query-DRI-driver-dir-for-X11-Ozone.patch \
    file://0002-bytemuck-Drop-removed-LaneCount-bound.patch \
"

# Keep this late link fix in do_compile so the already built Chromium tree can
# be resumed without re-running do_unpack and discarding its object files.
DD_CHROMIUM_GBM_PATCH := "${THISDIR}/${PN}/0003-gl-Match-GBM-EGL-native-window-type.patch"
do_compile[file-checksums] += "${DD_CHROMIUM_GBM_PATCH}:True"

# Inherit parallelism from the build configuration instead of imposing a
# Chromium-specific job count, and log the selected setting and worker resources.

do_compile:prepend() {
    dd_chromium_cpus="$(getconf _NPROCESSORS_ONLN)"
    dd_chromium_memory_kib="$(awk '/^MemTotal:/ { print $2 }' /proc/meminfo)"
    dd_chromium_physical_memory_bytes="$(awk '/^MemTotal:/ { printf "%.0f", $2 * 1024 }' /proc/meminfo)"
    dd_chromium_memory_limit="$(cat /sys/fs/cgroup/memory.max 2>/dev/null || echo max)"
    if [ "$dd_chromium_memory_limit" = "max" ]; then
        dd_chromium_memory_limit="$dd_chromium_physical_memory_bytes"
    fi

    bbnote "DD Chromium build resources: parallel_make='${PARALLEL_MAKE}' online_cpus=$dd_chromium_cpus memory_kib=$dd_chromium_memory_kib cgroup_memory_bytes=$dd_chromium_memory_limit"
    bbnote "DD Chromium CPU affinity: $(awk '/^Cpus_allowed_list:/ { print $2 }' /proc/self/status)"
    bbnote "DD Chromium load: $(cat /proc/loadavg)"
    bbnote "DD Chromium cgroup CPU limit: $(cat /sys/fs/cgroup/cpu.max 2>/dev/null || echo unavailable)"

    if ! grep -Fq '#include <gbm.h>' "${S}/ui/gl/gl_surface_egl.cc"; then
        patch -d "${S}" -p1 --fuzz=0 < "${DD_CHROMIUM_GBM_PATCH}"
    fi
}
