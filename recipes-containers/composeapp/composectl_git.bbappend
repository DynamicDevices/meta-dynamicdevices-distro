# AESL image line: composectl with COMPOSE_APPS_PROXY (v96.3.0+)
# Gated by DISTROOVERRIDES aesl-ota — does not affect vixdt SaaS builds.
# Pin tag v96.3.0 (07a5b14…); that tag lives on main — there is no branch v96.3.0.

SRCBRANCH:aesl-ota = "main"
SRCREV:aesl-ota = "07a5b14b2e55f6882f7323ad6a32e62438aa5098"

# v96.3.0 uses Go generics in internal/progress; Yocto go-mod -linkshared
# hits cmd/link "duplicated definition of symbol …reporterImpl…Stop.func1"
# (golang/go#64801). Build statically for aesl-ota only.
GO_LINKSHARED:aesl-ota = ""

# Upstream ships debian/ packaging next to Go sources; go-mod installs that
# tree into composectl-dev and file-rdeps QA fails on debian/rules → make.
do_install:append:aesl-ota() {
    rm -rf ${D}${libdir}/go/src/${GO_IMPORT}/debian
}
