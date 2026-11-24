# Native tools remain unchanged. Enable Widgets/DBus for the selected runtime.
PACKAGECONFIG:append:class-target = "${@bb.utils.contains('DISTRO_FEATURES', 'qt6', ' gui widgets dbus fontconfig', '', d)}"
