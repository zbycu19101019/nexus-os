#!/usr/bin/env bash
set -Eeuo pipefail

PREFIX="/opt/nexusos"
PURGE="0"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --prefix) PREFIX="${2:?missing value}"; shift 2 ;;
        --purge) PURGE="1"; shift ;;
        --help|-h)
            echo "Usage: sudo bash uninstall.sh [--prefix /opt/nexusos] [--purge]"
            exit 0
            ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

[ "$(id -u)" = "0" ] || { echo "Run as root: sudo bash uninstall.sh" >&2; exit 1; }

if command -v systemctl >/dev/null 2>&1; then
    systemctl disable --now nexusos.service >/dev/null 2>&1 || true
    rm -f /etc/systemd/system/nexusos.service
    systemctl daemon-reload >/dev/null 2>&1 || true
fi

rm -f /etc/nginx/conf.d/nexusos.conf
rm -rf "$PREFIX"

if [ "$PURGE" = "1" ]; then
    rm -rf /etc/nexusos /var/lib/nexus /var/log/nexus /var/backups/nexusos
    echo "NEXUS OS removed with data purge."
else
    echo "NEXUS OS app removed. Data kept in /var/lib/nexus, /var/log/nexus and /var/backups/nexusos."
fi
