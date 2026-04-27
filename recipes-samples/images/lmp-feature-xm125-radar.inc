# XM125 Radar Module Feature
# Include XM125 radar monitoring and control utilities

SUMMARY = "Acconeer XM125 radar module support"

# Add XM125 radar monitor (Rust CLI) and firmware
IMAGE_INSTALL:append = " \
    xm125-radar-monitor \
    xm125-firmware \
"

FEATURE_DESCRIPTION = "Acconeer XM125 radar module monitoring and control utilities"
