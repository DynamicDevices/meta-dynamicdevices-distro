# LE Audio / PipeWire: meta-oe pipewire recipe creates system user "pipewire" (useradd-staticids).
# LmP sets USERADD_ERROR_DYNAMIC = "error" — add tables so the recipe is not skipped.
# Paths are resolved on BBPATH (see meta-dynamicdevices-distro/conf/layer.conf).
USERADD_UID_TABLES:append = " files/lmp-passwd-table-pipewire"
USERADD_GID_TABLES:append = " files/lmp-group-table-pipewire"
