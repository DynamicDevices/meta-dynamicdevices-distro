FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

# Patch to prevent "no secrets" error on headless systems
# When 4-way handshake fails, retry with existing PSK from connection file
# instead of clearing secrets and requesting new ones from non-existent agent
# This works together with psk-flags=0 configuration to ensure secrets are
# stored in connection files and can be reused on retry
SRC_URI += "file://0001-wifi-dont-clear-secrets-if-stored-in-keyfile.patch"
