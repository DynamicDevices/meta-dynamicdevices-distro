HOMEPAGE = "http://mesonbuild.com"
SUMMARY = "A high performance build system"
DESCRIPTION = "Meson is a build system designed to increase programmer \
productivity. It does this by providing a fast, simple and easy to use \
interface for modern software development tools and practices."

LICENSE = "Apache-2.0"
LIC_FILES_CHKSUM = "file://COPYING;md5=3b83ef96387f14655fc854ddc3c6bd57"

GITHUB_BASE_URI = "https://github.com/mesonbuild/meson/releases/"
SRC_URI = "${GITHUB_BASE_URI}/download/${PV}/meson-${PV}.tar.gz \
           file://meson-setup.py \
           file://meson-wrapper \
           file://0001-python-module-do-not-manipulate-the-environment-when.patch \
           file://0001-Make-CPU-family-warnings-fatal.patch \
           file://0002-Support-building-allarch-recipes-again.patch \
           "
SRC_URI[sha256sum] = "ea2546a26f4a171a741c1fd036f22c9c804d6198e3259f1df588e01f842dd69f"
UPSTREAM_CHECK_REGEX = "(?P<pver>\d+(\.\d+)+)$"

inherit python_setuptools_build_meta github-releases

RDEPENDS:${PN} = "ninja python3-modules python3-pkg-resources"

FILES:${PN} += "${datadir}/polkit-1"

do_install:append () {
	# As per the same issue in the python recipe itself:
	# Unfortunately the following pyc files are non-deterministc due to 'frozenset'
	# being written without strict ordering, even with PYTHONHASHSEED = 0
	# Upstream is discussing ways to solve the issue properly, until then let's just
	# not install the problematic files.
	# More info: http://benno.id.au/blog/2013/01/15/python-determinism
	find ${D} -name "*.pyc" -exec rm {} \;

	# Meson calls the various tools it needs via the $PATH environment variable
	# If these tools are delivered by recipes that stage to sysroot such as
	# python3-native, meson-native, ninja-native etc, then meson will find them
	# via the manipulated $PATH environment variable that bitbake sets up. This
	# is fine.
	#
	# However, if the tool is delivered by a recipe that stages to some other sysroot
	# such as gcc-cross-<arch>, then meson will not find the tool since the $PATH
	# environment variable is not manipulated to include those sysroots.
	#
	# The Yocto / OpenEmbedded build system can get around this by setting up the
	# environment correctly per recipe, but meson has no way of knowing this.
	#
	# In particular, when meson needs to compile something to test the compiler
	# during configure, it needs to call:
	# - the compiler: gcc-cross-<arch>
	# - the linker: ld-cross-<arch> (typically this is actually part of gcc-cross-<arch>)
	# - the strip command: strip-cross-<arch>
	#
	# These are typically delivered by gcc-cross-<arch>.
	# We can find out where these commands are by asking bitbake, and then we can
	# tell meson where they are by writing a cross-compilation file and telling
	# meson to use it with --cross-file.
	#
	# This is only required for the -native version of this recipe.
	if [ "${PN}" = "meson-native" ]; then
		# Create the meson directory first
		install -d ${D}${datadir}/meson
		# Write out a cross-compilation file
		cat >${D}${datadir}/meson/cross-compilation.conf <<EOF
[binaries]
c = '${CC}'
cpp = '${CXX}'
ar = '${AR}'
strip = '${STRIP}'
pkgconfig = 'pkg-config'

[host_machine]
system = 'linux'
cpu_family = '${HOST_ARCH}'
cpu = '${HOST_ARCH}'
endian = '${@bb.utils.contains("TUNE_FEATURES", "bigendian", "big", "little", d)}'

[target_machine]
system = 'linux'
cpu_family = '${TARGET_ARCH}'
cpu = '${TARGET_ARCH}'
endian = '${@bb.utils.contains("TUNE_FEATURES", "bigendian", "big", "little", d)}'
EOF
	fi
}

BBCLASSEXTEND = "native nativesdk"

# Higher preference than the 1.3.1 version for GStreamer 1.26.0 support
DEFAULT_PREFERENCE = "100"
