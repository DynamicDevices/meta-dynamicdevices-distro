FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

# Patch to prevent "no secrets" error on headless systems
# When 4-way handshake fails, retry with existing PSK from connection file
# instead of clearing secrets and requesting new ones from non-existent agent
# This works together with psk-flags=0 configuration to ensure secrets are
# stored in connection files and can be reused on retry
SRC_URI += "file://0001-wifi-dont-clear-secrets-if-stored-in-keyfile.patch"

# The Screen has both Wi-Fi and optional wired Ethernet.  Do not hold the
# runtime for the full startup timeout when one usable connection is already
# online but an unplugged wired profile is still attempting DHCP.
SRC_URI:append:imx8mm-jaguar-screen = " file://10-screen-wait-any-online.conf"

do_install:append:imx8mm-jaguar-screen() {
    install -d ${D}${systemd_system_unitdir}/NetworkManager-wait-online.service.d
    install -m 0644 \
        ${WORKDIR}/10-screen-wait-any-online.conf \
        ${D}${systemd_system_unitdir}/NetworkManager-wait-online.service.d/10-screen-wait-any-online.conf
}
