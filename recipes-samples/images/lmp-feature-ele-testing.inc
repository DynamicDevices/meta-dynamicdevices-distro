# EdgeLock Enclave Testing Feature - DEVELOPMENT ONLY
# Include this feature to add ELE testing tools to development images
# This feature should only be enabled for development builds with debug-tweaks

SUMMARY = "EdgeLock Enclave testing tools and utilities for development"

# Add ELE test suite for i.MX93 development
IMAGE_INSTALL:append = " \
    nxp-ele-test-suite \
    nxp-ele-dev-tools \
"

# Add additional debugging and development tools for ELE
IMAGE_INSTALL:append = " \
    openssl-bin \
    openssl-dev \
    devmem2 \
    i2c-tools \
    spitools \
"

# Add kernel modules that might be useful for ELE debugging
IMAGE_INSTALL:append = " \
    kernel-module-nvmem-core \
    kernel-module-nvmem-sysfs \
"

# Development packages for ELE library development
IMAGE_INSTALL:append = " \
    nxp-ele-test-suite-dev \
"

FEATURE_DESCRIPTION = "EdgeLock Enclave testing and development tools for i.MX93"
