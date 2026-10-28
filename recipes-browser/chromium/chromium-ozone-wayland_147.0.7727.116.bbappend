FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://0001-Only-query-DRI-driver-dir-for-X11-Ozone.patch \
    file://0002-bytemuck-Drop-removed-LaneCount-bound.patch \
"

# The old implementation-only GBM include changed EGLNativeWindowType to
# void*, while Wayland callers use Ozone's intptr_t. Never apply it to fresh
# sources. Reverse it on reused trees so Ninja rebuilds the implementation
# with the same constructor signature as its callers, without discarding all
# existing Chromium objects through do_unpack.
DD_CHROMIUM_LEGACY_GBM_PATCH := "${THISDIR}/${PN}/0003-gl-Match-GBM-EGL-native-window-type.patch"
do_compile[file-checksums] += "${DD_CHROMIUM_LEGACY_GBM_PATCH}:True"

# Bound compiler concurrency on the Foundries worker (44 CPUs, ~65 GiB limit).
PARALLEL_MAKE = "-j 16"

# Send diagnostics through BitBake's live FIFO instead of waiting for its
# failure-log dump. Keep ordinary Ninja progress in the complete task log.
DD_CHROMIUM_LIVE_BUILD := "${THISDIR}/${PN}/chromium-live-build.py"
do_compile[file-checksums] += "${DD_CHROMIUM_LIVE_BUILD}:True"

do_compile() {
    python3 "${DD_CHROMIUM_LIVE_BUILD}" \
        --fifo "${LOGFIFO}" --task-log "${T}/log.do_compile" -- \
        ninja ${PARALLEL_MAKE} chrome chrome_sandbox chromedriver.unstripped
}

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

    if grep -Fq '#include <gbm.h>' "${S}/ui/gl/gl_surface_egl.cc"; then
        bbnote "DD Chromium: reversing legacy implementation-only GBM include"
        patch -d "${S}" -p1 --reverse --fuzz=0 < "${DD_CHROMIUM_LEGACY_GBM_PATCH}"
    fi
}
