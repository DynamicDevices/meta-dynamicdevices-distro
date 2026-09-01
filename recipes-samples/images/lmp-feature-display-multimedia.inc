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
