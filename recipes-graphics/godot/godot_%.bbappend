# The Screen image uses PipeWire's ALSA compatibility rather than a separate
# PulseAudio daemon, and intentionally does not carry the GNOME desktop layer.
PACKAGECONFIG:remove:imx8mm-jaguar-screen = "pulseaudio"
PACKAGECONFIG:append:imx8mm-jaguar-screen = " wayland opengl alsa touch udev"
RRECOMMENDS:${PN}:remove:imx8mm-jaguar-screen = "zenity adwaita-icon-theme-cursors"

# meta-godot installs the target editor using its architecture-qualified name.
# Supply the stable command name used by applications and runtime smoke tests.
do_install:append:class-target() {
    editor="$(find ${D}${bindir} -maxdepth 1 -type f -name 'godot.linuxbsd.editor.*' -printf '%f\n' | head -n 1)"
    if [ -n "$editor" ]; then
        ln -s "$editor" ${D}${bindir}/godot
    fi
}
