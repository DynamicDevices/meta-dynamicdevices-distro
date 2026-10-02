# Global PATCHTOOL = "git" leaves a .git directory in the unpacked source.
# diffutils treats any Git checkout as a developer tree and enables its full
# warning set with -Werror, unlike a normal release-tarball build.  Disable
# that developer-only mode for both kiosk browser tuples while retaining the
# selected Clang toolchain and ordinary compiler diagnostics.
EXTRA_OECONF:append:ddkioskbrowser = " --disable-gcc-warnings"
EXTRA_OECONF:append:ddkioskcog = " --disable-gcc-warnings"
