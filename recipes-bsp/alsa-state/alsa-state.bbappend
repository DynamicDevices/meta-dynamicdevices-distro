# alsa-state already owns /etc/asound.conf and declares it as a conffile.
# Override its contents here, rather than creating a conflicting second copy
# in dd-kiosk-browser. Keep other machines' upstream configuration unchanged.
PACKAGE_ARCH = "${MACHINE_ARCH}"

DD_KIOSK_AUDIO_CARD ?= ""
DD_KIOSK_AUDIO_CARD:imx8mm-jaguar-screen = "wm8524audio"

do_install:append() {
    if [ -n "${DD_KIOSK_AUDIO_CARD}" ]; then
        printf '%s\n' \
            'pcm.!default { type hw; card ${DD_KIOSK_AUDIO_CARD}; device 0; }' \
            'ctl.!default { type hw; card ${DD_KIOSK_AUDIO_CARD}; }' \
            > ${D}${sysconfdir}/asound.conf
    fi
}
