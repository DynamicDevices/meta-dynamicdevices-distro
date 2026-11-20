# Factory Definitions that still request the old -headless name arrive here
# for interactive display machines. Load the real headed policy and identity,
# including DD_PRODUCT_FEATURES. An explicit empty product bundle still works.
DD_PRODUCT_FEATURES ?= "${@'display flutter godot alsa' if d.getVar('MACHINE') == 'imx8mm-jaguar-screen' else 'display'}"
require conf/distro/lmp-dynamicdevices.conf

# Preserve the legacy entry point's bootloader selection and timestamp; this
# repair must not change the confirmed build704/705 U-Boot implementation.
PREFERRED_VERSION_u-boot-fio = "2024.04%"
PREFERRED_VERSION_u-boot-fio-imx = "2024.04%"
SOURCE_DATE_EPOCH ?= "1609459200"

# Keep DT510's existing onboarding feature alongside its selected display,
# ALSA and USB gadget runtime. No portal or credential configuration changes.
DISTRO_FEATURES:append:imx8mm-jaguar-dt510 = " improv"
