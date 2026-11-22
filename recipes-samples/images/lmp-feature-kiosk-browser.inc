CORE_IMAGE_BASE_INSTALL += " \
    packagegroup-dd-kiosk-browser \
"

# Installed for manual bench testing; never replace the configured boot URL.
CORE_IMAGE_BASE_INSTALL:append:imx8mm-jaguar-screen = " jaguar-touch-test"
