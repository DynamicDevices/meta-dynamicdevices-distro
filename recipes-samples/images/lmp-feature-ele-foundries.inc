# ELE-based Foundries.io LMP Integration Feature
# Include this feature to add ELE-based Foundries.io device registration and OTA support

SUMMARY = "EdgeLock Enclave integration with Foundries.io Linux microPlatform"

# Add ELE-based Foundries.io integration
IMAGE_INSTALL:append = " \
    lmp-ele-foundries \
    aktualizr-lite \
"

# Add additional tools for Foundries.io development
IMAGE_INSTALL:append = " \
    curl \
    ca-certificates \
    openssl-bin \
    python3-requests \
    python3-json \
"

# Add systemd services for automatic registration
SYSTEMD_AUTO_ENABLE:append = " \
    lmp-ele-auto-register.service \
"

FEATURE_DESCRIPTION = "ELE-based Foundries.io LMP device registration and OTA support for i.MX93"

# This feature provides:
# - Automatic device registration with Foundries.io factory
# - ELE-based secure credential storage
# - OTA update configuration and management
# - Device lifecycle management
# - Factory-specific device provisioning
