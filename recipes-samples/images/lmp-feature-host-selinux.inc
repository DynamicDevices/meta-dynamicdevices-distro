# Build-time labelling is required for immutable OSTree content. Persistent
# /var paths are relabelled explicitly by their owning services during the
# R26 migration rather than attempting to rewrite the full immutable rootfs.
inherit selinux-image

CORE_IMAGE_BASE_INSTALL += " \
    packagegroup-core-selinux \
"

DEFAULT_ENFORCING = "enforcing"
FIRST_BOOT_RELABEL = "0"
