# LE Audio / Auracast-style BAP broadcast (NXP UM12155) — optional host stack
#
# Gated by MACHINE_FEATURES "auracast" (see lmp-factory-image.bb). Intended only on
# machines that already enable IW612 (nxpiw612-sdio): firmware + mlan/moal + hci.
#
# Prerequisite: nxpiw612-sdio on the same MACHINE (lmp-feature-iw612.inc).
# Follow-up: NXP LEA-patched BlueZ + validated firmware/kernel per IW612 release notes;
#            this fragment pulls PipeWire/WirePlumber + a WirePlumber role drop-in.
#
# PipeWire Bluetooth/LC3: recipes-multimedia/pipewire/pipewire_%.bbappend (auracast) —
# aligned with meta-openembedded at lmp-manifest/lmp-base.xml; re-sync if that pin changes.
#
# Note: Images may also ship PulseAudio (lmp-feature-pulseaudio.inc). Coexistence /
#       default session policy is product-specific — validate on hardware.

CORE_IMAGE_BASE_INSTALL += " \
    pipewire \
    pipewire-alsa \
    wireplumber \
    bluez5 \
    bluez5-testtools \
    le-audio-wireplumber-config \
"
