# Hardware multimedia application stack for machines with an active display.
#
# The i.MX machine configuration selects the appropriate GStreamer plugin
# family through MACHINE_GSTREAMER_1_0_PLUGIN.  On i.MX8M Mini this resolves
# to gstreamer1.0-plugins-imx-meta and pulls the libimxvpuapi2/Hantro codec
# integration.  Keep this opt-in so headless and e-ink images are not bloated.

CORE_IMAGE_BASE_INSTALL += " \
    gstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-bad-kms \
    gstreamer1.0-plugins-bad-videoparsersbad \
    ${MACHINE_GSTREAMER_1_0_PLUGIN} \
"

# Screen-specific display policy: the panel is mounted 90 degrees clockwise
# from its native scan direction.  Apply the inverse transform at
# the compositor so every client (Flutter, Godot and video) shares the same
# logical orientation; applications must not compensate independently.
# Weston uses NXP G2D by default.  Android-container selects Mesa/Etnaviv and
# therefore uses Weston's standard GL renderer instead.  Both paths retain the
# same persistent runtime directory, branded background and GPU access.
configure_jaguar_screen_weston() {
    install -d ${IMAGE_ROOTFS}${sysconfdir}/xdg/weston
    cat > ${IMAGE_ROOTFS}${sysconfdir}/xdg/weston/weston-screen.ini <<'EOF'
[core]
${@bb.utils.contains('DISTRO_FEATURES', 'etnaviv', '', 'use-g2d=true', d)}
repaint-window=16
idle-time=0

[shell]
background-image=/usr/share/screen-splash/active-edge-splash-1200x1920.png
background-type=scale
background-color=0xff07111f
panel-position=none

[libinput]
touchscreen_calibrator=true

[output]
name=DSI-1
mode=1200x1920
transform=rotate-270
EOF

    install -d ${IMAGE_ROOTFS}${sysconfdir}/systemd/system/weston.service.d
    cat > ${IMAGE_ROOTFS}${sysconfdir}/systemd/system/weston.service.d/screen.conf <<'EOF'
[Service]
WorkingDirectory=/var/rootdirs/home/weston
ExecStart=
SupplementaryGroups=render video
# Weston's debug extension authorises weston-screenshooter. Keep it strictly
# tied to DEV_MODE/debug-tweaks so production images do not expose capture.
ExecStart=/usr/bin/weston --config=/etc/xdg/weston/weston-screen.ini ${@bb.utils.contains('DISTRO_FEATURES', 'etnaviv', '', '--use-g2d', d)} --modules=systemd-notify.so ${@bb.utils.contains('IMAGE_FEATURES', 'debug-tweaks', '--debug', '', d)} --log=/var/rootdirs/home/weston/weston.log
EOF

    install -d ${IMAGE_ROOTFS}${sysconfdir}/tmpfiles.d
    cat > ${IMAGE_ROOTFS}${sysconfdir}/tmpfiles.d/jaguar-screen-weston.conf <<'EOF'
d /var/rootdirs/home/weston 0750 weston weston -
EOF

    install -d ${IMAGE_ROOTFS}${sysconfdir}/udev/rules.d
    cat > ${IMAGE_ROOTFS}${sysconfdir}/udev/rules.d/70-jaguar-screen-gpu.rules <<'EOF'
KERNEL=="galcore", GROUP="render", MODE="0660"
SUBSYSTEM=="drm", KERNEL=="renderD*", GROUP="render", MODE="0660"
SUBSYSTEM=="dma_heap", GROUP="video", MODE="0660"
KERNEL=="mxc_hantro*", GROUP="video", MODE="0660"
EOF
}
ROOTFS_POSTPROCESS_COMMAND:append:imx8mm-jaguar-screen = " configure_jaguar_screen_weston;"
