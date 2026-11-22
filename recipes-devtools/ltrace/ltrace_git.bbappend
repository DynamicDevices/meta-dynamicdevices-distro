# ltrace's legacy procfs path macros use strlen() in stack array bounds while
# building with -Werror. The LmP Clang version diagnoses these as
# -Wgnu-folding-constant. Keep the compatibility exception kiosk-scoped and
# build this old C recipe with GCC, as for the other non-clangable tools.
TOOLCHAIN:ddkioskbrowser = "gcc"
