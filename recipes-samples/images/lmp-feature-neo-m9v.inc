# u-blox NEO-M9V GNSS host tools — gated by MACHINE_FEATURES "neo-m9v"
# (see lmp-factory-image.bb).
#
# OE package names (Debian docs often say gpsd-clients — that name is not in meta-oe):
#   gps-utils-python → ubxtool (and peers); pulls gpsd via python3-pygps.
# BSP gpsd_%.bbappend keeps the daemon/socket disabled so /dev/gnss stays free for NDTR.

CORE_IMAGE_BASE_INSTALL += " \
    gpsd \
    gps-utils \
    gps-utils-python \
"
