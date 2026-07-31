#SYSTEMD_AUTO_ENABLE:${PN}-lite:imx8mm-jaguar-sentai = "mask"

# AESL image line: aklite with compose_apps_proxy (v97+)
# Gated by DISTROOVERRIDES aesl-ota — does not affect vixdt SaaS builds.
# Evidence: COMPOSE_APPS_PROXY only on foundriesio/aktualizr-lite branch v97
# (not on v95/v96 tips as of 2026-07-28).
#
# Use :aesl-ota (not :lmp:aesl-ota). Chained :lmp:aesl-ota did not override
# meta-lmp BRANCH:lmp/SRCREV:lmp in bitbake -e (stayed on v95 / 6cda15b);
# :aesl-ota wins because aesl-ota appears after lmp in OVERRIDES — same
# pattern as composectl_git.bbappend SRCBRANCH:aesl-ota.

BRANCH:aesl-ota = "v97"
SRCREV:aesl-ota = "2362e88f8b105b32cf871505082bdf3ed242009c"
