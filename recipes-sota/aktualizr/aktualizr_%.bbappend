#SYSTEMD_AUTO_ENABLE:${PN}-lite:imx8mm-jaguar-sentai = "mask"

# AESL image line: aklite with compose_apps_proxy (v97+)
# Gated by DISTROOVERRIDES aesl-ota — does not affect vixdt SaaS builds.
# Evidence: COMPOSE_APPS_PROXY only on foundriesio/aktualizr-lite branch v97
# (not on v95/v96 tips as of 2026-07-28).
#
# Must live under recipes-sota/aktualizr/ — layer.conf BBFILES is
# recipes-*/*/*.bbappend (two path components). A top-level
# recipes-sota/aktualizr_%.bbappend was never parsed.
#
# Prefer :aesl-ota (not :lmp:aesl-ota) so aesl-ota wins over meta-lmp
# BRANCH:lmp via OVERRIDES order — same pattern as composectl.

BRANCH:aesl-ota = "v97"
SRCREV:aesl-ota = "2362e88f8b105b32cf871505082bdf3ed242009c"
