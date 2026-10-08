SUMMARY = "Headless x86/x86-64 userspace emulator for ARM64 Linux"
DESCRIPTION = "Opt-in FEX board evaluation build. No graphics thunks, GUI, Steam integration, guest rootfs downloads or automatic binfmt registration."
HOMEPAGE = "https://fex-emu.com/"
LICENSE = "MIT & BSD-2-Clause & BSD-3-Clause & BSL-1.0 & 0BSD"
LIC_FILES_CHKSUM = " \
    file://LICENSE;md5=70d20d502833c35d6d5a4f0ef5d9efcc \
    file://External/fmt/LICENSE;md5=6ec080902ed8f82f5a97ed13e8042634 \
    file://External/range-v3/LICENSE.txt;md5=5dc23d5193abaedb6e42f05650004624 \
    file://External/rpmalloc/LICENSE;md5=9fd7f8f5d4cfec178012a97fc56eaa11 \
    file://External/unordered_dense/LICENSE;md5=1d7f9e1447a1ba175cfd5e005c801e89 \
    file://External/xxhash/LICENSE;md5=13be6b481ff5616f77dda971191bb29b \
    file://External/jemalloc_glibc/COPYING;md5=ea061f8731d5e6a5761dfad951ef5f5f \
    file://Source/Common/cpp-optparse/LICENSE;md5=0ea9669e97a394711e89bc28ccd82277 \
    file://External/tiny-json/LICENSE;md5=970183ccb33b0e6b6282bbfd729e56cc \
    file://External/SoftFloat-3e/include/SoftFloat-3e/softfloat.h;beginline=1;endline=36;md5=d67822501d8a23e684a0cebb84a7f3bd \
    file://External/cephes/LICENSE;md5=48df7931ed7ac1f7ac0d2ab29e0de04a \
"

# Fetch only the submodules required by this configuration, with the exact
# revisions recorded by FEX-2609. gitsm would also download unused test binaries.
# drm-headers contains Linux UAPI declarations with the Linux-syscall-note
# exception; those headers are not installed in the runtime package.
SRC_URI = " \
    git://github.com/FEX-Emu/FEX.git;protocol=https;nobranch=1;name=fex \
    git://github.com/fmtlib/fmt.git;protocol=https;nobranch=1;name=fmt;destsuffix=git/External/fmt \
    git://github.com/ericniebler/range-v3.git;protocol=https;nobranch=1;name=range;destsuffix=git/External/range-v3 \
    git://github.com/FEX-Emu/rpmalloc.git;protocol=https;nobranch=1;name=rpmalloc;destsuffix=git/External/rpmalloc \
    git://github.com/martinus/unordered_dense.git;protocol=https;nobranch=1;name=dense;destsuffix=git/External/unordered_dense \
    git://github.com/Cyan4973/xxHash.git;protocol=https;nobranch=1;name=xxhash;destsuffix=git/External/xxhash \
    git://github.com/FEX-Emu/jemalloc.git;protocol=https;nobranch=1;name=jemalloc;destsuffix=git/External/jemalloc_glibc \
    git://github.com/Sonicadvance1/cpp-optparse.git;protocol=https;nobranch=1;name=optparse;destsuffix=git/Source/Common/cpp-optparse \
    git://github.com/FEX-Emu/drm-headers.git;protocol=https;nobranch=1;name=drm;destsuffix=git/External/drm-headers \
    file://0001-cmake-make-rootfs-fetcher-optional.patch \
    file://0002-cmake-leave-symbol-stripping-to-packaging.patch \
"
SRCREV_fex = "395b132f346b1a45def246d10c52245edba1ef02"
SRCREV_fmt = "c07e2aa4b130b4fd359a1c6455a5201b17af01fa"
SRCREV_range = "ca1388fb9da8e69314dda222dc7b139ca84e092f"
SRCREV_rpmalloc = "09142d726429416bfa7b459151515fe3ab7622dd"
SRCREV_dense = "3234af2c03549bc85656bfd3a86993bf1cd8aef1"
SRCREV_xxhash = "e626a72bc2321cd320e953a0ccf1584cad60f363"
SRCREV_jemalloc = "8436195ad5e1bc347d9b39743af3d29abee59f06"
SRCREV_optparse = "9f94388a339fcbb0bc95c17768eb786c85988f6e"
SRCREV_drm = "3e49836995c1dcb3df709440ad2f270b569c6a5f"
SRCREV_FORMAT = "fex_fmt_range_rpmalloc_dense_xxhash_jemalloc_optparse_drm"
S = "${WORKDIR}/git"

inherit cmake python3native

# meta-clang is already in the canonical KAS stack. Select it for this recipe
# only; do not change the distro-wide compiler or add a global layer dependency.
TOOLCHAIN = "clang"
# The FRDM partner stack has a machine-level GCC override. Target-class
# selection is recipe-local and takes precedence without changing other recipes.
TOOLCHAIN:class-target = "clang"
TC_CXX_RUNTIME = "gnu"
COMPATIBLE_HOST = "aarch64.*-linux"
COMPATIBLE_HOST:libc-musl = "null"

python __anonymous() {
    if 'clang-layer' not in (d.getVar('BBFILE_COLLECTIONS') or '').split():
        raise bb.parse.SkipRecipe('FEX requires meta-clang in BBLAYERS')
}

EXTRA_OECMAKE = " \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_CXX_SCAN_FOR_MODULES=OFF \
    -DBUILD_TESTING=OFF \
    -DBUILD_FEX_LINUX_TESTS=OFF \
    -DBUILD_THUNKS=OFF \
    -DBUILD_FEXCONFIG=OFF \
    -DBUILD_ROOTFS_FETCHER=OFF \
    -DBUILD_STEAM_SUPPORT=OFF \
    -DENABLE_LTO=OFF \
    -DENABLE_CCACHE=OFF \
    -DENABLE_GDB_SYMBOLS=OFF \
    -DENABLE_OFFLINE_TELEMETRY=OFF \
    -DTUNE_CPU=none \
    -DTUNE_ARCH=generic \
    -DOVERRIDE_VERSION=FEX-${PV} \
    -DOVERRIDE_HASH=${SRCREV_fex} \
    -DPython_EXECUTABLE=${PYTHON} \
    -DCMAKE_DISABLE_FIND_PACKAGE_fmt=ON \
    -DCMAKE_DISABLE_FIND_PACKAGE_range-v3=ON \
    -DCMAKE_DISABLE_FIND_PACKAGE_unordered_dense=ON \
"

# This build uses ordinary C++20 translation units, not C++ modules. CMake
# 3.28 otherwise enables scanning with Clang 18 even when this cross sysroot
# does not provide clang-scan-deps; bundled fmt then fails before compilation.

do_install:append() {
    # Upstream installs systemd handlers by default. Explicit FEX invocation is
    # sufficient for evaluation and must not take over existing QEMU handlers.
    rm -f ${D}${prefix}/lib/binfmt.d/FEX-x86.conf \
          ${D}${prefix}/lib/binfmt.d/FEX-x86_64.conf
    # Do not leave an unowned empty handler directory in the staging image.
    rmdir ${D}${prefix}/lib/binfmt.d
}

# FEXCore is an unversioned runtime DSO, not a development linker symlink.
# Leave headers and other development files in -dev, but ship this real ELF
# with the emulator rather than the default unversioned-.so development glob.
FILES_SOLIBSDEV = ""
FILES:${PN} += "${datadir}/fex-emu ${libdir}/libFEXCore.so"
