# E-Ink Spectra 6 EL133UF1 Display Feature
# Adds userspace library and test tools for Spectra 6 EL133UF1 E-Ink display
# This feature is enabled by the 'el133uf1' machine feature

SUMMARY = "E-Ink Spectra 6 EL133UF1 Display Support"
DESCRIPTION = "Feature to add Spectra 6 EL133UF1 E-Ink display userspace library and test tools"

# Core E-Ink Spectra 6 support
CORE_IMAGE_BASE_INSTALL += " \
    eink-spectra6 \
    spidev-test \
"

# Development and debugging tools
CORE_IMAGE_BASE_INSTALL += " \
    i2c-tools \
    spitools \
    devmem2 \
    strace \
"

# Additional utilities for E-Ink development
CORE_IMAGE_BASE_INSTALL += " \
    fbset \
    fbgrab \
    imagemagick \
"

# Python support for E-Ink scripting (optional - only if meta-python layer is available)
CORE_IMAGE_BASE_INSTALL += " \
    python3-spidev \
    ${@bb.utils.contains('BBFILE_COLLECTIONS', 'meta-python', 'python3-gpiod', '', d)} \
    python3-pillow \
"

# Documentation and examples
CORE_IMAGE_BASE_INSTALL += " \
    ${@bb.utils.contains('PACKAGECONFIG', 'examples', 'eink-spectra6-examples', '', d)} \
"
