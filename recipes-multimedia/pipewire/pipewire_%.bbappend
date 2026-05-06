# LE Audio / Auracast: build PipeWire's BlueZ5 backend + LC3 (BAP) without relying on
# DISTRO_FEATURES:bluetooth alone. Gated on MACHINE_FEATURES "auracast".
#
# alsa + pipewire-alsa: emit the pipewire-alsa / card-profile split packages (lmp-feature-le-audio.inc
# installs pipewire-alsa). Headless distro removes DISTRO_FEATURES alsa globally — do not rely on
# that alone for pipewire's PACKAGECONFIG.
#
# PACKAGECONFIG names must match the pipewire recipe in meta-openembedded at the
# manifest pin (see lmp-manifest/lmp-base.xml). At meta-oe e92d0173a80e, pipewire_1.0.9.bb
# defines alsa, pipewire-alsa, bluez, bluez-opus, bluez-lc3. Re-sync if meta-openembedded is bumped.

PACKAGECONFIG:append:class-target = "${@bb.utils.contains('MACHINE_FEATURES', 'auracast', ' alsa pipewire-alsa bluez bluez-opus bluez-lc3', '', d)}"
