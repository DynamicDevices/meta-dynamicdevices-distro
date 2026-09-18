# The Foundries native host compiler accepts the C++20 dialect as gnu++2a,
# but does not recognise the newer gnu++20 spelling emitted by Node's GYP.
# Keep the target recipe and other product tuples on their existing inputs.
FILESEXTRAPATHS:prepend := "${THISDIR}/nodejs:"
SRC_URI:append:class-native:ddkioskbrowser = " file://0001-Use-compatible-CXX20-spelling-for-native-build.patch"
