# GDB 14.2's enum-flags helper is rejected by the LmP Clang version because
# it casts -1 to enums in a constant expression. Build this recipe with GCC
# for the kiosk tuple, following LmP's existing non-clangable exceptions.
TOOLCHAIN:ddkioskbrowser = "gcc"
