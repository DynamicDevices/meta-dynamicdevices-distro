CORE_IMAGE_BASE_INSTALL += " \
  linux-firmware-nxpiw612-sdio \
  mlanutl \
"

# BlueZ test utilities (btmgmt, extra hci helpers) — IW612 lab / LE Audio debug only; omit from production.
# When: nxpiw612-sdio AND (IMAGE_FEATURES debug-tweaks from Factory DEV_MODE=1, OR LOCAL_DEVELOPMENT_BUILD=1 in local.conf).
CORE_IMAGE_BASE_INSTALL += "${@' bluez5-testtools' if bb.utils.contains('MACHINE_FEATURES', 'nxpiw612-sdio', True, False, d) and (bb.utils.contains('IMAGE_FEATURES', 'debug-tweaks', True, False, d) or d.getVar('LOCAL_DEVELOPMENT_BUILD') == '1') else ''}"
