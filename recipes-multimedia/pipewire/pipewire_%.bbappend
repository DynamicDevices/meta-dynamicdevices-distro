# LE Audio / Auracast: build PipeWire's BlueZ5 backend + LC3 (BAP) without relying on
# DISTRO_FEATURES:bluetooth alone. Gated on MACHINE_FEATURES "auracast".
#
# PACKAGECONFIG names must match the pipewire recipe in meta-openembedded at the
# manifest pin (see lmp-manifest/lmp-base.xml). At meta-oe e92d0173a80e, pipewire_1.0.9.bb
# defines bluez, bluez-opus, bluez-lc3. Re-sync if meta-openembedded is bumped.

PACKAGECONFIG:append:class-target = "${@bb.utils.contains('MACHINE_FEATURES', 'auracast', ' bluez bluez-opus bluez-lc3', '', d)}"
