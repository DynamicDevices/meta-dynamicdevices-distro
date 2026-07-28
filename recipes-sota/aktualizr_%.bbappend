#SYSTEMD_AUTO_ENABLE:${PN}-lite:imx8mm-jaguar-sentai = "mask"

# AESL image line: aklite with compose_apps_proxy (v97+)
# Gated by DISTROOVERRIDES aesl-ota — does not affect vixdt SaaS builds.
# Evidence: COMPOSE_APPS_PROXY only on foundriesio/aktualizr-lite branch v97
# (not on v95/v96 tips as of 2026-07-28).

BRANCH:lmp:aesl-ota = "v97"
SRCREV:lmp:aesl-ota = "2362e88f8b105b32cf871505082bdf3ed242009c"
