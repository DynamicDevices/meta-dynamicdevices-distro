# mfgtool uses recipe optee-os-fio-mfgtool (not optee-os-fio).
# The SE050 disable intended for DISTRO=lmp-mfgtool in optee-os-fio_%.bbappend
# never applied here, so meta-lmp EVK defaults (CFG_CORE_SE05X_I2C_BUS=2 +
# SCP03_EARLY) shipped in AESL DT510 mfgtool and OpTEE panicked on SE050 I2C
# before U-Boot fastboot — USB stuck at 1fc9:0151.
#
# Match Sentai working mfgtool (no SE050 in OpTEE) and the comments on
# optee-os-fio_%.bbappend: programming path does not need SE050.

EXTRA_OEMAKE:append:imx8mm-jaguar-dt510 = " \
    CFG_NXP_SE05X=n CFG_CORE_SE05X=n \
    CFG_CORE_SE05X_SCP03_EARLY=n CFG_CORE_SE05X_EARLY_INIT=n \
    CFG_RPMB_FS=n CFG_REE_FS_INTEGRITY_RPMB=n \
"

EXTRA_OEMAKE:append:imx8mm-jaguar-sentai = " \
    CFG_NXP_SE05X=n CFG_CORE_SE05X=n \
    CFG_CORE_SE05X_SCP03_EARLY=n CFG_CORE_SE05X_EARLY_INIT=n \
"

EXTRA_OEMAKE:append:imx8mm-jaguar-inst = " \
    CFG_NXP_SE05X=n CFG_CORE_SE05X=n \
    CFG_CORE_SE05X_SCP03_EARLY=n CFG_CORE_SE05X_EARLY_INIT=n \
"

EXTRA_OEMAKE:append:imx93-jaguar-eink = " \
    CFG_NXP_SE05X=n CFG_CORE_SE05X=n \
    CFG_CORE_SE05X_SCP03_EARLY=n CFG_CORE_SE05X_EARLY_INIT=n \
"
