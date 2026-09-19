# The Foundries native host compiler accepts the C++20 dialect as gnu++2a,
# but does not recognise the newer gnu++20 spelling emitted by Node's GYP.
# Keep other product tuples on their existing inputs.
FILESEXTRAPATHS:prepend := "${THISDIR}/nodejs:"
SRC_URI:append:ddkioskbrowser = " \
    file://0001-Use-compatible-CXX20-spelling-for-native-build.patch \
    file://0002-crypto-remove-unused-compare-include.patch \
"

# The Foundries host GCC also lacks C++20 language support needed by Node 22
# (notably operator<=>). Use pinned clang-native for the kiosk native recipe
# and for host helpers built by the kiosk target recipe. Keep the ARM target
# compiler unchanged. Node's GYP uses both CC/CXX and BUILD_CC/CXX.
DEPENDS:append:ddkioskbrowser = " clang-native"
CC:class-native:ddkioskbrowser = "clang"
CXX:class-native:ddkioskbrowser = "clang++"
BUILD_CC:class-native:ddkioskbrowser = "clang"
BUILD_CXX:class-native:ddkioskbrowser = "clang++"
BUILD_CC:class-target:ddkioskbrowser = "clang"
BUILD_CXX:class-target:ddkioskbrowser = "clang++"
