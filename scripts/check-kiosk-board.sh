#!/bin/sh
set -eu
host=${1:?usage: check-kiosk-board.sh fio@board-address expected-ostree-sha256}
expected=${2:?usage: check-kiosk-board.sh fio@board-address expected-ostree-sha256}
printf '%s\n' "$expected" | grep -Eq '^[0-9a-f]{64}$' || {
    echo 'expected deployment must be a 64-character lowercase SHA-256' >&2
    exit 2
}
ssh -o BatchMode=yes -o ConnectTimeout=5 "$host" "sh -s -- $expected" <<'REMOTE'
set -u
expected=$1
failed=0
service_state() {
    name=$1
    state=$(systemctl is-active "$name" 2>/dev/null || true)
    printf '%s: %s\n' "$name" "${state:-unknown}"
    [ "$state" = active ] || failed=1
}
printf 'hostname: '; hostname
printf 'image version: '; sed -n 's/^IMAGE_VERSION=//p' /etc/os-release | head -n 1
active_deployment=$(ostree admin status | awk '/^[[:space:]]*\*/ {print; exit}')
printf 'active deployment: %s\n' "${active_deployment:-unknown}"
case "$active_deployment" in
    *"$expected"*) ;;
    *) echo 'expected candidate deployment is not active' >&2; failed=1 ;;
esac
service_state weston.service
service_state dd-kiosk-browser.service
service_state NetworkManager.service
service_user=$(systemctl show dd-kiosk-browser.service --property=User --value 2>/dev/null || true)
printf 'kiosk service user: %s\n' "${service_user:-unknown}"
[ "$service_user" = weston ] || failed=1
state_owner=$(stat -c %U /var/lib/dd-kiosk-browser 2>/dev/null || true)
printf 'kiosk state owner: %s\n' "${state_owner:-missing}"
[ "$state_owner" = weston ] || failed=1
printf 'chromium kiosk process: '
browser_flags=absent
for pid in $(pgrep -f chromium-bin || true); do
    [ -r "/proc/$pid/cmdline" ] || continue
    command_line=$(tr '\000' ' ' < "/proc/$pid/cmdline")
    case "$command_line" in
        *" --ozone-platform=wayland "*) ;;
        *) continue ;;
    esac
    case "$command_line" in
        *" --kiosk "*) browser_flags=present; break ;;
    esac
done
printf '%s\n' "$browser_flags"
[ "$browser_flags" = present ] || failed=1
printf 'kiosk policy: '; if test -r /etc/chromium/policies/managed/dd-kiosk-browser.json; then echo present; else echo absent; failed=1; fi
weston_uid=$(id -u weston)
printf 'wayland socket: '; if grep -Fq "/run/user/$weston_uid/wayland-" /proc/net/unix; then echo present; else echo absent; failed=1; fi
exit "$failed"
REMOTE
