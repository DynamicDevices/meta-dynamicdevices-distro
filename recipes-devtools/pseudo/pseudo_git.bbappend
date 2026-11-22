# The base LmP Scarthgap pseudo 1.9.0 mishandles directory descriptors used by
# modern GNU tar during do_package ("unknown base path for fd", EFAULT).
# Pin the upstream Scarthgap 1.9.7 revision for native build tasks on this
# isolated kiosk manifest. Keep the target and nativesdk recipe unchanged.
SRCREV:class-native:ddkioskbrowser = "5b7c4b59e7e198aab54b35ea194aeb6d99794f96"
PV:class-native:ddkioskbrowser = "1.9.7"
# 1.9.7 already filters PIE flags in configure; the base recipe's old patch
# targets the earlier configure layout and no longer applies.
FILESEXTRAPATHS:prepend := "${THISDIR}/pseudo:"
SRC_URI:remove:class-native:ddkioskbrowser = "file://0001-configure-Prune-PIE-flags.patch file://older-glibc-symbols.patch"
SRC_URI:append:class-native:ddkioskbrowser = " file://0001-link-native-pseudo-against-old-glibc.patch"
