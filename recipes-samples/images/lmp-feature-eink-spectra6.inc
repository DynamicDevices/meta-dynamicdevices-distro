# EL133UF1 E-Ink Display Driver Feature
# This feature adds the EL133UF1 e-ink display driver and related tools

CORE_IMAGE_BASE_INSTALL += " \
    eink-spectra6 \
"

# Additional packages for e-ink display development and debugging
CORE_IMAGE_BASE_INSTALL += " \
    spitools \
    i2c-tools \
    devmem2 \
"

# Ensure SPI and GPIO kernel modules are available
CORE_IMAGE_BASE_INSTALL += " \
    kernel-module-spi-dev \
    kernel-module-gpio-sysfs \
"
