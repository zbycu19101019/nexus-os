#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

[ -f /etc/nexusos/kiosk.env ] && . /etc/nexusos/kiosk.env

URL="${NEXUS_KIOSK_URL:-http://127.0.0.1:9090/}"
POLL_SECONDS="${NEXUS_KIOSK_POLL_SECONDS:-2}"
STATE_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}/nexusos-desktop"
LOG_FILE="$STATE_ROOT/desktop.log"

mkdir -p "$STATE_ROOT" "$HOME/.config/openbox"
touch "$LOG_FILE"

log() { printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG_FILE" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }

browser_bin() {
    for bin in chromium chromium-browser google-chrome-stable google-chrome firefox-esr firefox; do
        if have "$bin"; then
            command -v "$bin"
            return 0
        fi
    done
    return 1
}

wait_for_backend() {
    local tries="${NEXUS_KIOSK_WAIT_TRIES:-180}"
    local code=""
    for _ in $(seq 1 "$tries"); do
        code="$(curl -k -sS -o /dev/null -w '%{http_code}' --max-time 2 "$URL" 2>/dev/null || true)"
        case "$code" in
            200|204|301|302|307|308|401|403) log "Backend ready at $URL (HTTP $code)"; return 0 ;;
        esac
        sleep "$POLL_SECONDS"
    done
    log "Backend not ready after $tries tries, starting desktop anyway"
}

if [ "${1:-}" = "--x-session" ]; then
    wait_for_backend
    browser="$(browser_bin || true)"

    {
        printf '%s\n' 'xset -dpms s off s noblank >/dev/null 2>&1 || true'
        printf '%s\n' 'tint2 >/tmp/nexusos-tint2.log 2>&1 &'
        printf '%s\n' 'pcmanfm --desktop >/tmp/nexusos-pcmanfm.log 2>&1 &'
        if [ -n "$browser" ]; then
            printf '"%s" --no-first-run --new-window "%s" >/tmp/nexusos-browser.log 2>&1 &\n' "$browser" "$URL"
        fi
    } > "$HOME/.config/openbox/autostart"

    log "Starting Openbox emergency desktop"
    exec openbox-session
fi

if ! have startx || ! have openbox-session; then
    log "Missing startx/openbox-session. Install: xserver-xorg-core xinit openbox tint2 pcmanfm"
    exit 127
fi

export XDG_SESSION_TYPE=x11
export XDG_CURRENT_DESKTOP=NEXUS
exec startx "$0" --x-session -- :0 vt1 -keeptty -nolisten tcp
