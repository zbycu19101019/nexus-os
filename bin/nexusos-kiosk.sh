#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# NEXUS OS bare-metal appliance launcher.
# It starts Chromium only after the local FastAPI backend responds.

[ -f /etc/nexusos/nexusos.env ] && . /etc/nexusos/nexusos.env
[ -f /etc/nexusos/kiosk.env ] && . /etc/nexusos/kiosk.env

PORT="${NEXUS_PORT:-9090}"
URL="${NEXUS_KIOSK_URL:-http://127.0.0.1:${PORT}/}"
WIDTH="${NEXUS_KIOSK_WIDTH:-1920}"
HEIGHT="${NEXUS_KIOSK_HEIGHT:-1080}"
POLL_SECONDS="${NEXUS_KIOSK_POLL_SECONDS:-2}"
STATE_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}/nexusos-kiosk"
CHROME_STATE="$STATE_ROOT/chromium"

log() { printf '[NEXUS KIOSK] %s\n' "$*" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }

browser_bin() {
    for bin in chromium chromium-browser google-chrome-stable google-chrome; do
        if have "$bin"; then
            command -v "$bin"
            return 0
        fi
    done
    return 1
}

http_alive() {
    local code
    if have curl; then
        code="$(curl -k -L -sS -o /dev/null -w '%{http_code}' --max-time 3 "$URL" 2>/dev/null || true)"
    elif have wget; then
        code="$(wget --server-response --spider --timeout=3 "$URL" 2>&1 | awk '/^  HTTP\// {print $2}' | tail -n 1)"
    else
        log "curl/wget missing; cannot probe $URL"
        return 1
    fi

    case "$code" in
        200|204|301|302|303|307|308|401|403) return 0 ;;
        *) return 1 ;;
    esac
}

wait_for_backend() {
    local tries=0
    log "waiting for backend: $URL"
    until http_alive; do
        tries=$((tries + 1))
        if [ $((tries % 15)) -eq 0 ]; then
            log "backend still not ready after $((tries * POLL_SECONDS))s"
        fi
        sleep "$POLL_SECONDS"
    done
    log "backend ready"
}

main() {
    local browser
    browser="$(browser_bin)" || {
        log "Chromium not found. Install package: chromium"
        exit 127
    }

    mkdir -p "$CHROME_STATE"
    chmod 0700 "$STATE_ROOT" "$CHROME_STATE" 2>/dev/null || true

    export XDG_SESSION_TYPE="${XDG_SESSION_TYPE:-wayland}"
    export XDG_CURRENT_DESKTOP="${XDG_CURRENT_DESKTOP:-NEXUS}"
    export XDG_SEAT="${XDG_SEAT:-seat0}"
    export WLR_BACKENDS="${WLR_BACKENDS:-drm}"

    wait_for_backend

    exec cage -- "$browser" \
        --kiosk "$URL" \
        --ozone-platform=wayland \
        --enable-features=UseOzonePlatform \
        --no-first-run \
        --no-default-browser-check \
        --incognito \
        --noerrdialogs \
        --disable-infobars \
        --disable-translate \
        --disable-pinch \
        --disable-session-crashed-bubble \
        --disable-features=Translate,TouchpadOverscrollHistoryNavigation \
        --overscroll-history-navigation=0 \
        --autoplay-policy=no-user-gesture-required \
        --force-device-scale-factor=1 \
        --window-size="${WIDTH},${HEIGHT}" \
        --start-fullscreen \
        --user-data-dir="$CHROME_STATE"
}

main "$@"
