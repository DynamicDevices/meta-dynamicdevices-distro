# Optional development / bring-up tools on factory image (e.g. DT510 Ethernet)
# Sourced from meta-dynamicdevices-distro: recipes-samples/images/lmp-factory-image.bbappend
CORE_IMAGE_BASE_INSTALL:append:imx8mm-jaguar-dt510 = " phytool mdio-tools"
