# alsa-utils (aplay, arecord) for USB audio gadget testing on DT510
CORE_IMAGE_BASE_INSTALL += "${@bb.utils.contains('DISTRO_FEATURES', 'alsa', 'alsa-utils', '', d)}"
# imx-memtool: NXP memtool (imx-test/test/memtool), ${bindir}/memtool — named registers / modules.
# devmem2: tiny arbitrary physical MMIO read/write via /dev/mem (ADDRESS [w|h|b [VALUE]]).
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
   phytool \
   mdio-tools \
   imx-memtool \
   devmem2 \
"
# lmp-factory-image.bb: this inc is only required when IMAGE_FEATURES contains debug-tweaks
# (e.g. DEV_MODE), so the packages above including phytool/mdio/imx-memtool/devmem2 apply to any such image.
