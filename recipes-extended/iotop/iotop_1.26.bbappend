# iotop's build enables LTO by default. With the LmP Clang toolchain on
# AArch64 it invokes GNU ld with a missing LLVMgold plugin. Keep this
# exception scoped to the kiosk browser tuples and use the supported GCC
# toolchain.
TOOLCHAIN:ddkioskbrowser = "gcc"
TOOLCHAIN:ddkioskcog = "gcc"
