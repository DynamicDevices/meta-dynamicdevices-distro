# alsa-utils (aplay, arecord) for USB audio gadget testing on DT510
CORE_IMAGE_BASE_INSTALL += "${@bb.utils.contains('DISTRO_FEATURES', 'alsa', 'alsa-utils', '', d)}"
CORE_IMAGE_BASE_INSTALL += " \
   libgpiod libgpiod-tools libgpiod-dev \
   evtest \
   i2c-tools \
   strace \
   tmate \
   curl \
   git \
   vim \
   default-network-manager \
   spidev-test \
   minicom \
   gpio-utils \
   htop \
   gst-instruments \
   tcpdump \
   pv \
   sysstat \
   ser2net \
"
# MDIO/PHY bring-up: KSZ9896 (FEC MDIO) — only where this dev set is used (debug-tweaks)
CORE_IMAGE_BASE_INSTALL:append:imx8mm-jaguar-dt510 = " phytool mdio-tools"
