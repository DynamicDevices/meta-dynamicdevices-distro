FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://0001-Only-query-DRI-driver-dir-for-X11-Ozone.patch \
    file://0002-bytemuck-Drop-removed-LaneCount-bound.patch \
"

# Keep this late link fix in do_compile so the already built Chromium tree can
# be resumed without re-running do_unpack and discarding its object files.
DD_CHROMIUM_GBM_PATCH := "${THISDIR}/${PN}/0003-gl-Match-GBM-EGL-native-window-type.patch"
do_compile[file-checksums] += "${DD_CHROMIUM_GBM_PATCH}:True"

# Foundries' high-memory worker is required for Chromium.  Keep Ninja's
# concurrency deterministic so a mis-sized worker cannot silently turn this
# task into a nine-hour timeout, and record the effective resources in the
# normal task log for every build.
DD_CHROMIUM_BUILD_JOBS ?= "32"
DD_CHROMIUM_MIN_CPUS ?= "16"
DD_CHROMIUM_MIN_MEMORY_KIB ?= "67108864"
PARALLEL_MAKE = "-j ${DD_CHROMIUM_BUILD_JOBS}"

do_compile:prepend() {
    dd_chromium_cpus="$(getconf _NPROCESSORS_ONLN)"
    dd_chromium_memory_kib="$(awk '/^MemTotal:/ { print $2 }' /proc/meminfo)"

    bbnote "DD Chromium build resources: jobs=${DD_CHROMIUM_BUILD_JOBS} online_cpus=$dd_chromium_cpus min_cpus=${DD_CHROMIUM_MIN_CPUS} memory_kib=$dd_chromium_memory_kib min_memory_kib=${DD_CHROMIUM_MIN_MEMORY_KIB}"
    bbnote "DD Chromium CPU affinity: $(awk '/^Cpus_allowed_list:/ { print $2 }' /proc/self/status)"
    bbnote "DD Chromium load: $(cat /proc/loadavg)"
    bbnote "DD Chromium cgroup CPU limit: $(cat /sys/fs/cgroup/cpu.max 2>/dev/null || echo unavailable)"
    bbnote "DD Chromium cgroup memory limit: $(cat /sys/fs/cgroup/memory.max 2>/dev/null || echo unavailable)"
    df -h "${TMPDIR}"

    if [ "$dd_chromium_cpus" -lt "${DD_CHROMIUM_MIN_CPUS}" ]; then
        bbfatal "Chromium requires at least ${DD_CHROMIUM_MIN_CPUS} online CPUs; worker exposes $dd_chromium_cpus"
    fi
    if [ "$dd_chromium_memory_kib" -lt "${DD_CHROMIUM_MIN_MEMORY_KIB}" ]; then
        bbfatal "Chromium requires at least ${DD_CHROMIUM_MIN_MEMORY_KIB} KiB RAM; worker exposes $dd_chromium_memory_kib KiB"
    fi

    if ! grep -Fq '#include <gbm.h>' "${S}/ui/gl/gl_surface_egl.cc"; then
        patch -d "${S}" -p1 --fuzz=0 < "${DD_CHROMIUM_GBM_PATCH}"
    fi
}
