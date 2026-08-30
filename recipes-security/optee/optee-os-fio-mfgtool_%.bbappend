# mfgtool uses recipe optee-os-fio-mfgtool (not optee-os-fio).
#
# Root cause (AESL DT510): MACHINEOVERRIDES include imx8mm-lpddr4-evk, so
# meta-lmp sets CFG_CORE_SE05X_I2C_BUS=2. DT510 SE050 is on I2C4 → OpTEE bus
# index 3 (see production optee-os-fio_%.bbappend). Wrong bus → OpTEE panics in
# se050_early_init → U-Boot never starts → USB stuck at 1fc9:0151 after SDP.
#
# Do not only set CFG_NXP_SE05X=n here: MACHINE_FEATURES se05x pulls
# optee-os-fio-se05x.inc (CRYPTO_DRV_* + EXTRA_OEMAKE:remove CFG_CRYPTO_DRIVER=y).
# Clearing NXP_SE05X alone leaves CIPHER drivers on and breaks the link
# (drvcrypt_cipher_alloc_ctx). Prefer the production bus override for mfgtool.

EXTRA_OEMAKE:append:imx8mm-jaguar-dt510 = " \
    CFG_CORE_SE05X_I2C_BUS=3 \
"

# Sentai / inst / eink: programming path historically without SE050 early init.
# Full stack unwind + restore CAAM crypto (se05x.inc removes CFG_CRYPTO_DRIVER=y).
python() {
    machines = ("imx8mm-jaguar-sentai", "imx8mm-jaguar-inst", "imx8mm-jaguar-screen", "imx93-jaguar-eink")
    machine = d.getVar("MACHINE") or ""
    if machine not in machines:
        return
    rem = d.getVarFlag("EXTRA_OEMAKE", "remove") or ""
    rem = " ".join(t for t in rem.split() if t != "CFG_CRYPTO_DRIVER=y")
    d.setVarFlag("EXTRA_OEMAKE", "remove", rem)
}

EXTRA_OEMAKE:append:imx8mm-jaguar-sentai = " \
    CFG_NXP_SE05X=n CFG_CORE_SE05X=n \
    CFG_CORE_SE05X_SCP03_EARLY=n CFG_CORE_SE05X_EARLY_INIT=n \
    CFG_CRYPTO_DRV_CIPHER=n CFG_CRYPTO_DRV_ACIPHER=n \
    CFG_NXP_SE05X_SCP03_DRV=n CFG_NXP_SE05X_APDU_DRV=n \
    CFG_NXP_SE05X_RSA_DRV=n CFG_NXP_SE05X_RSA_DRV_FALLBACK=n \
    CFG_NXP_SE05X_ECC_DRV=n CFG_NXP_SE05X_ECC_DRV_FALLBACK=n \
    CFG_NXP_SE05X_DIEID_DRV=n \
    CFG_CRYPTO_DRIVER=y \
"

EXTRA_OEMAKE:append:imx8mm-jaguar-inst = " \
    CFG_NXP_SE05X=n CFG_CORE_SE05X=n \
    CFG_CORE_SE05X_SCP03_EARLY=n CFG_CORE_SE05X_EARLY_INIT=n \
    CFG_CRYPTO_DRV_CIPHER=n CFG_CRYPTO_DRV_ACIPHER=n \
    CFG_NXP_SE05X_SCP03_DRV=n CFG_NXP_SE05X_APDU_DRV=n \
    CFG_NXP_SE05X_RSA_DRV=n CFG_NXP_SE05X_RSA_DRV_FALLBACK=n \
    CFG_NXP_SE05X_ECC_DRV=n CFG_NXP_SE05X_ECC_DRV_FALLBACK=n \
    CFG_NXP_SE05X_DIEID_DRV=n \
    CFG_CRYPTO_DRIVER=y \
"
EXTRA_OEMAKE:append:imx8mm-jaguar-screen = " \
    CFG_NXP_SE05X=n CFG_CORE_SE05X=n \
    CFG_CORE_SE05X_SCP03_EARLY=n CFG_CORE_SE05X_EARLY_INIT=n \
    CFG_CRYPTO_DRV_CIPHER=n CFG_CRYPTO_DRV_ACIPHER=n \
    CFG_NXP_SE05X_SCP03_DRV=n CFG_NXP_SE05X_APDU_DRV=n \
    CFG_NXP_SE05X_RSA_DRV=n CFG_NXP_SE05X_RSA_DRV_FALLBACK=n \
    CFG_NXP_SE05X_ECC_DRV=n CFG_NXP_SE05X_ECC_DRV_FALLBACK=n \
    CFG_NXP_SE05X_DIEID_DRV=n \
    CFG_CRYPTO_DRIVER=y \
"

EXTRA_OEMAKE:append:imx93-jaguar-eink = " \
    CFG_NXP_SE05X=n CFG_CORE_SE05X=n \
    CFG_CORE_SE05X_SCP03_EARLY=n CFG_CORE_SE05X_EARLY_INIT=n \
    CFG_CRYPTO_DRV_CIPHER=n CFG_CRYPTO_DRV_ACIPHER=n \
    CFG_NXP_SE05X_SCP03_DRV=n CFG_NXP_SE05X_APDU_DRV=n \
    CFG_NXP_SE05X_RSA_DRV=n CFG_NXP_SE05X_RSA_DRV_FALLBACK=n \
    CFG_NXP_SE05X_ECC_DRV=n CFG_NXP_SE05X_ECC_DRV_FALLBACK=n \
    CFG_NXP_SE05X_DIEID_DRV=n \
    CFG_CRYPTO_DRIVER=y \
"
