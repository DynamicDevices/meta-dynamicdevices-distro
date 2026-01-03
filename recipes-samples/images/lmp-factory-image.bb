SUMMARY = "Minimal factory image which includes OTA Lite, Docker and optional development support such as OpenSSH"
DESCRIPTION = "Factory image for Dynamic Devices edge computing platforms with OTA capabilities, Docker containers and optional development tools"

LICENSE = "MIT"

require recipes-samples/images/lmp-image-common.inc

# Factory tooling requires SOTA (OSTree + Aktualizr-lite)
require ${@bb.utils.contains('DISTRO_FEATURES', 'sota', 'recipes-samples/images/lmp-feature-factory.inc', '', d)}

# Enable wayland related recipes if required by DISTRO
require ${@bb.utils.contains('DISTRO_FEATURES', 'wayland', 'recipes-samples/images/lmp-feature-wayland.inc', '', d)}

# Enable waydroid related recipes if required by DISTRO
require ${@bb.utils.contains('DISTRO_FEATURES', 'waydroid', 'recipes-samples/images/lmp-feature-waydroid.inc', '', d)}

# Enable auto register related recipes if required by DISTRO
require ${@bb.utils.contains('DISTRO_FEATURES', 'auto-register', 'recipes-samples/images/lmp-feature-auto-register.inc', '', d)}

# Enable alsa related recipes if required by DISTRO
require ${@bb.utils.contains('DISTRO_FEATURES', 'alsa', 'recipes-samples/images/lmp-feature-alsa.inc', '', d)}

# Enable alsa related recipes if required by DISTRO
require ${@bb.utils.contains('DISTRO_FEATURES', 'pulseaudio', 'recipes-samples/images/lmp-feature-pulseaudio.inc', '', d)}

# Enable improv protocol (BLE/serial onboarding) recipes if required by DISTRO
require ${@bb.utils.contains('DISTRO_FEATURES', 'improv', 'recipes-samples/images/lmp-feature-improv.inc', '', d)}

# Enable flutter related recipes if required by DISTRO
require ${@bb.utils.contains('DISTRO_FEATURES', 'flutter', 'recipes-samples/images/lmp-feature-flutter.inc', '', d)}

# Enable OP-TEE related recipes if provided by the image
require ${@bb.utils.contains('MACHINE_FEATURES', 'optee', 'recipes-samples/images/lmp-feature-optee.inc', '', d)}

# Enable SE05X related recipes if provided by machine
require ${@bb.utils.contains('MACHINE_FEATURES', 'se05x', 'recipes-samples/images/lmp-feature-se05x.inc', '', d)}

# Enable TPM2 related recipes if provided by machine
require ${@bb.utils.contains('MACHINE_FEATURES', 'tpm2', 'recipes-samples/images/lmp-feature-tpm2.inc', '', d)}

# Enable EFI support if provided by machine
require ${@bb.utils.contains('MACHINE_FEATURES', 'efi', 'recipes-samples/images/lmp-feature-efi.inc', '', d)}

# Enable IMA support if required by DISTRO
require ${@bb.utils.contains('MACHINE_FEATURES', 'ima', 'recipes-samples/images/lmp-feature-ima.inc', '', d)}

# Enable Xenomai4 related recipes if provided by the image
require ${@bb.utils.contains('MACHINE_FEATURES', 'xeno4', 'recipes-samples/images/lmp-feature-xeno4.inc', '', d)}

# Enable Intel AX210 WiFi related recipes if required by MACHINE
require ${@bb.utils.contains('MACHINE_FEATURES', 'ax210', 'recipes-samples/images/lmp-feature-ax210.inc', '', d)}

# Enable TI tas2563/tas2781 integrated driver related recipes if required by MACHINE
require ${@bb.utils.contains('MACHINE_FEATURES', 'tas2781-integrated', 'recipes-samples/images/lmp-feature-tas2781-integrated.inc', '', d)}

# Enable ST usb4500 related recipes if required by MACHINE
require ${@bb.utils.contains('MACHINE_FEATURES', 'stusb4500', 'recipes-samples/images/lmp-feature-stusb4500.inc', '', d)}

# Enable Infineon bgt60 related recipes if required by MACHINE
require ${@bb.utils.contains('MACHINE_FEATURES', 'bgt60', 'recipes-samples/images/lmp-feature-bgt60.inc', '', d)}

# Enable NXP IW612 related recipes if required by MACHINE
require ${@bb.utils.contains('MACHINE_FEATURES', 'nxpiw612-sdio', 'recipes-samples/images/lmp-feature-iw612.inc', '', d)}

# Enable Renesas upd72020x related recipes if required by MACHINE
require ${@bb.utils.contains('MACHINE_FEATURES', 'upd72020x', 'recipes-samples/images/lmp-feature-upd72020x.inc', '', d)}

# Enable alsa related recipes if required by MACHINE
require ${@bb.utils.contains('MACHINE_FEATURES', 'zigbee', 'recipes-samples/images/lmp-feature-zigbee.inc', '', d)}

# Enable power management for eink boards
require ${@bb.utils.contains('MACHINE_FEATURES', 'el133uf1', 'recipes-samples/images/lmp-feature-eink-power.inc', '', d)}

# Enable MCUboot support for boards with microcontrollers
require ${@bb.utils.contains('MACHINE_FEATURES', 'mcuboot', 'recipes-samples/images/lmp-feature-mcuboot.inc', '', d)}

# Enable XM125 radar support if provided by machine
require ${@bb.utils.contains('MACHINE_FEATURES', 'xm125-radar', 'recipes-samples/images/lmp-feature-xm125-radar.inc', '', d)}

# E-Ink Spectra 6 EL133UF1 display support
# Note: eink-spectra6 support is provided by meta-subscriber-overrides (private repository)

# Enable boot profiling if requested
require ${@bb.utils.contains('ENABLE_BOOT_PROFILING', '1', 'recipes-samples/images/lmp-feature-boot-profiling.inc', '', d)}

# Enable EdgeLock Enclave testing for i.MX93 development builds only
require ${@bb.utils.contains('IMAGE_FEATURES', 'debug-tweaks', bb.utils.contains('MACHINE', 'imx93-jaguar-eink', 'recipes-samples/images/lmp-feature-ele-testing.inc', '', d), '', d)}

# Set image features based on DEV_MODE environment variable defined in Factory configuration
# Only include debug-tweaks for runtime debugging, not tools-sdk which bloats the image
IMAGE_FEATURES += "${@bb.utils.contains('DEV_MODE', '1', 'debug-tweaks', '', d)}"

# Set image features based on CE_TEST environment variable defined in Factory configuration
IMAGE_FEATURES += "${@bb.utils.contains('CE_TESTING', '1', 'ce-testing', '', d)}"

# Enable development related recipes if required by IMAGE_FEATURES
require ${@bb.utils.contains('IMAGE_FEATURES', 'debug-tweaks', 'recipes-samples/images/lmp-feature-dev.inc', '', d)}

# Enable power monitoring tools for development builds
require ${@bb.utils.contains('IMAGE_FEATURES', 'debug-tweaks', 'recipes-samples/images/lmp-feature-power-monitoring.inc', '', d)}

# Enable CE test related recipes if required by IMAGE_FEATURES
require ${@bb.utils.contains('IMAGE_FEATURES', 'ce-testing', 'recipes-samples/images/lmp-feature-ce-testing.inc', '', d)}

require recipes-samples/images/lmp-feature-softhsm.inc
require recipes-samples/images/lmp-feature-wireguard.inc
require recipes-samples/images/lmp-feature-docker.inc
require recipes-samples/images/lmp-feature-wifi.inc
require recipes-samples/images/lmp-feature-ota-utils.inc
require recipes-samples/images/lmp-feature-sbin-path-helper.inc

CORE_IMAGE_BASE_INSTALL_GPLV3 = "\
    packagegroup-core-full-cmdline-utils \
    packagegroup-core-full-cmdline-multiuser \
"

CORE_IMAGE_BASE_INSTALL += " \
    board-init \
    board-scripts \
    nano \
    lmp-auto-hostname \
    kernel-modules \
    networkmanager-nmcli \
    modemmanager \
    libiio \
    lmsensors \
    tzdata-core \
    tzdata-europe \
    nodejs \
    nodejs-npm \
    python3-pyserial \
    python3-paho-mqtt \
    packagegroup-core-full-cmdline-extended \
    ${@bb.utils.contains('LMP_DISABLE_GPLV3', '1', '', '${CORE_IMAGE_BASE_INSTALL_GPLV3}', d)} \
"

# lmp-auto-hostname is already included in CORE_IMAGE_BASE_INSTALL for all machines

CORE_IMAGE_BASE_INSTALL:append:imx8mm-jaguar-sentai = " \
    socat \
    default-network-manager \
    gstreamer1.0-rtsp-server gstreamer1.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav \
    stm32flash \
"

CORE_IMAGE_BASE_INSTALL:append:imx8mm-jaguar-inst = " \
       linux-firmware-iwlwifi \
       pciutils \
       socat \
"

CORE_IMAGE_BASE_INSTALL:append:imx93-jaguar-eink = " \
       default-network-manager \
       libpng \
       rng-tools \
       libpng-dev \
       jpeg \
       libjpeg-turbo \
       libjpeg-turbo-dev \
       libcurl \
       curl-dev \
       stm32flash \
"

# Include audit feature for comprehensive logging and security monitoring
require ${@bb.utils.contains('MACHINE', 'imx93-jaguar-eink', 'lmp-feature-audit.inc', '', d)}

# === Image Size Configuration for imx93-jaguar-eink ===
# Increase root partition size to accommodate all packages and avoid "Image too large" errors
IMAGE_ROOTFS_EXTRA_SPACE:append:imx93-jaguar-eink = " + 1048576"
WKS_FILE:imx93-jaguar-eink = "imx93-jaguar-eink-large.wks"

IMAGE_FEATURES += "ssh-server-openssh"

#CORE_IMAGE_BASE_INSTALL:append:imx8mm-jaguar-phasora = " \
#    phasora-config \
#    gstreamer1.0-meta-base \
#"

#DRM-REMOVE:imxgpu:imx8mm-jaguar-phasora = "drm-gl drm-gles2"

#postprocess_function_phasora() {
#
#   # Setup the Weston UI (rotate)
#   sed -z -i 's/#\[output\]\n#name=HDMI-A-1/[output]\nname=DSI-1/g' ${IMAGE_ROOTFS}/etc/xdg/weston/weston.ini
#   sed -i 's/#transform=rotate-90/transform=rotate-270/g' ${IMAGE_ROOTFS}/etc/xdg/weston/weston.ini
#
#   # Add use of the calibration helper file
#   sed -i 's|touchscreen_calibrator=true|touchscreen_calibrator=true\ncalibration_helper=/usr/bin/save-calibration.sh|g' ${IMAGE_ROOTFS}/etc/xdg/weston/weston.ini
#
#   # Set a default calibration matrix
#   echo "ENV{LIBINPUT_CALIBRATION_MATRIX}=\"0.868808 -0.002796 0.188540 -0.006824 0.982137 -0.013213\"" >> ${IMAGE_ROOTFS}/etc/udev/rules.d/touchscreen.rules
#}

#ROOTFS_POSTPROCESS_COMMAND:imx8mm-jaguar-phasora += "postprocess_function; "

# Disable root login - NOTE: This means we can't use "sudo su" any more *but* running commands as root works
inherit extrausers

# Create fio user home directory at build time
# The LmP base layer creates the fio user with useradd -M (no home directory)
# and expects pam_mkhomedir to create it at first login. This causes problems
# when services need to write to the home directory before user login.
# CRITICAL: Create parent directory structure before usermod -m runs
# usermod -m requires the parent directory to exist, so we create it first
EXTRA_USERS_PARAMS:append = "\
  mkdir -p /var/rootdirs/home; \
  usermod -d /var/rootdirs/home/fio -m ${LMP_USER}; \
  usermod -s /sbin/nologin root; \
"

# Fix fio home directory ownership after creation
# usermod -m creates the directory but may create it as root, so we need to fix ownership
# Derive the actual UID/GID from the user created by EXTRA_USERS_PARAMS, not assume a fixed value
# CRITICAL: This must run AFTER EXTRA_USERS_PARAMS but BEFORE any PAM configuration that might
# recreate the directory. We also ensure the directory exists so pam_mkhomedir skips creation.
# CRITICAL: Always use numeric UID/GID for chown since the user doesn't exist on the build host
fix_fio_home_ownership() {
    # Ensure the directory exists (usermod -m should create it, but be defensive)
    if [ ! -d ${IMAGE_ROOTFS}/var/rootdirs/home/fio ]; then
        mkdir -p ${IMAGE_ROOTFS}/var/rootdirs/home/fio
    fi
    
    # Get the actual UID and GID from the passwd file in the rootfs
    # This ensures we use the correct IDs even if LMP_USER has a different UID/GID
    # CRITICAL: Must use numeric IDs because the user doesn't exist on the build host
    local fio_uid=$(grep "^${LMP_USER}:" ${IMAGE_ROOTFS}/etc/passwd 2>/dev/null | cut -d: -f3)
    local fio_gid=$(grep "^${LMP_USER}:" ${IMAGE_ROOTFS}/etc/passwd 2>/dev/null | cut -d: -f4)
    
    # Validate that we got numeric IDs (should always succeed if EXTRA_USERS_PARAMS ran)
    if [ -n "$fio_uid" ] && [ -n "$fio_gid" ] && [ "$fio_uid" -eq "$fio_uid" ] 2>/dev/null && [ "$fio_gid" -eq "$fio_gid" ] 2>/dev/null; then
        chown -R ${fio_uid}:${fio_gid} ${IMAGE_ROOTFS}/var/rootdirs/home/fio
        chmod 755 ${IMAGE_ROOTFS}/var/rootdirs/home/fio
        # Create marker file with correct ownership
        touch ${IMAGE_ROOTFS}/var/rootdirs/home/fio/.build-time-home
        chown ${fio_uid}:${fio_gid} ${IMAGE_ROOTFS}/var/rootdirs/home/fio/.build-time-home
    else
        # Fallback: Use default LmP fio user UID/GID (1000:1000)
        # This should only happen if passwd file doesn't exist or user wasn't created
        # which would indicate a more serious build problem
        bbwarn "Could not determine ${LMP_USER} UID/GID from passwd file, using default 1000:1000"
        chown -R 1000:1000 ${IMAGE_ROOTFS}/var/rootdirs/home/fio
        chmod 755 ${IMAGE_ROOTFS}/var/rootdirs/home/fio
        touch ${IMAGE_ROOTFS}/var/rootdirs/home/fio/.build-time-home
        chown 1000:1000 ${IMAGE_ROOTFS}/var/rootdirs/home/fio/.build-time-home
    fi
}
ROOTFS_POSTPROCESS_COMMAND += "fix_fio_home_ownership; "