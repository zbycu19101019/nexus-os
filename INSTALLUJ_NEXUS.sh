#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/nexusos-install-$(date +%Y%m%d-%H%M%S).log"
DOMAIN=""
EMAIL=""
ADMIN_PASSWORD=""
YES_MODE="1"
NO_CERT="0"
NO_MINIO="0"
PANEL_ONLY="0"
WITH_APPLIANCE="0"
KIOSK_USER=""
KIOSK_WIDTH=""
KIOSK_HEIGHT=""

usage() {
    cat <<'USAGE'
NEXUS OS idiot-proof installer

Najprosciej:
  bash INSTALLUJ_NEXUS.sh

Bez pytan postawi pelny NEXUS OS na:
  http://IP_SERWERA/
  http://IP_SERWERA:9090/

Albo jednym strzalem:
  sudo bash INSTALLUJ_NEXUS.sh --domain nexusos.pl --email admin@example.com

Opcje:
  --domain DOMENA         Domena panelu, np. nexusos.pl
  --email EMAIL           Email do certyfikatu HTTPS Let's Encrypt
  --admin-password HASLO  Poczatkowe haslo admina
  --yes                   Bez pytan, instaluj na IP:9090 (domyslne)
  --ask                   Tryb kreatora z pytaniami
  --no-cert               Nie probuj HTTPS/Certbot
  --no-minio              Nie instaluj MinIO
  --panel-only            Tylko panel, bez calego stosu hypervisora
  --with-appliance        Tryb bare-metal kiosk na tty1 + lekki pulpit awaryjny
  --kiosk-user USER       Uzytkownik kiosku, np. zibi
  --kiosk-width PX        Szerokosc widoku kiosku
  --kiosk-height PX       Wysokosc widoku kiosku
  --help                  Pomoc
USAGE
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --domain) DOMAIN="${2:?missing value}"; shift 2 ;;
        --email) EMAIL="${2:?missing value}"; shift 2 ;;
        --admin-password) ADMIN_PASSWORD="${2:?missing value}"; shift 2 ;;
        --yes|-y) YES_MODE="1"; shift ;;
        --ask) YES_MODE="0"; shift ;;
        --no-cert) NO_CERT="1"; shift ;;
        --no-minio) NO_MINIO="1"; shift ;;
        --panel-only) PANEL_ONLY="1"; shift ;;
        --with-appliance) WITH_APPLIANCE="1"; shift ;;
        --kiosk-user) KIOSK_USER="${2:?missing value}"; shift 2 ;;
        --kiosk-width) KIOSK_WIDTH="${2:?missing value}"; shift 2 ;;
        --kiosk-height) KIOSK_HEIGHT="${2:?missing value}"; shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) echo "Nieznana opcja: $1"; usage; exit 1 ;;
    esac
done

exec > >(tee -a "$LOG_FILE") 2>&1

log() { printf '\033[1;36m[NEXUS EASY]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[NEXUS EASY WARN]\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31m[NEXUS EASY ERROR]\033[0m %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

on_error() {
    local code="$?"
    echo
    echo "============================================================"
    echo "INSTALACJA NIE DOSZLA DO KONCA"
    echo "Kod bledu: $code"
    echo "Log: $LOG_FILE"
    echo
    echo "Najpierw pokaz ostatnie linie:"
    echo "  tail -n 120 $LOG_FILE"
    echo
    echo "Jesli usluga powstala, sprawdz:"
    echo "  systemctl status nexusos --no-pager"
    echo "  journalctl -u nexusos -n 100 --no-pager"
    echo "============================================================"
    exit "$code"
}
trap on_error ERR

if [ "$(id -u)" != "0" ]; then
    if have sudo; then
        log "Potrzebny root. Przelaczam przez sudo."
        sudo_args=()
        [ -n "$DOMAIN" ] && sudo_args+=(--domain "$DOMAIN")
        [ -n "$EMAIL" ] && sudo_args+=(--email "$EMAIL")
        [ -n "$ADMIN_PASSWORD" ] && sudo_args+=(--admin-password "$ADMIN_PASSWORD")
        [ "$YES_MODE" = "1" ] && sudo_args+=(--yes)
        [ "$YES_MODE" != "1" ] && sudo_args+=(--ask)
        [ "$NO_CERT" = "1" ] && sudo_args+=(--no-cert)
        [ "$NO_MINIO" = "1" ] && sudo_args+=(--no-minio)
        [ "$PANEL_ONLY" = "1" ] && sudo_args+=(--panel-only)
        [ "$WITH_APPLIANCE" = "1" ] && sudo_args+=(--with-appliance)
        [ -n "$KIOSK_USER" ] && sudo_args+=(--kiosk-user "$KIOSK_USER")
        [ -n "$KIOSK_WIDTH" ] && sudo_args+=(--kiosk-width "$KIOSK_WIDTH")
        [ -n "$KIOSK_HEIGHT" ] && sudo_args+=(--kiosk-height "$KIOSK_HEIGHT")
        exec sudo -E bash "$0" "${sudo_args[@]}"
    fi
    die "Uruchom jako root: sudo bash INSTALLUJ_NEXUS.sh"
fi

[ -f "$SCRIPT_DIR/install_everything.sh" ] || die "Brakuje install_everything.sh w katalogu paczki."
[ -f "$SCRIPT_DIR/install.sh" ] || die "Brakuje install.sh w katalogu paczki."

is_interactive() {
    [ -t 0 ] && [ "$YES_MODE" != "1" ]
}

first_ip() {
    hostname -I 2>/dev/null | awk '{print $1}' || true
}

public_ip() {
    if have curl; then
        curl -fsS --max-time 5 https://api.ipify.org 2>/dev/null || true
    fi
}

print_header() {
    clear 2>/dev/null || true
    cat <<'BANNER'
============================================================
                 NEXUS OS - EASY INSTALL
============================================================
Ten instalator zrobi za Ciebie:
  - Python/FastAPI panel
  - KVM/QEMU/libvirt
  - nginx reverse proxy
  - noVNC/websockify
  - OVMF/UEFI + swtpm
  - rclone, MinIO, narzedzia ISO i diagnostyke
  - usluge systemd nexusos

Tryb domyslny: BEZ PYTAN. Instalacja startuje od razu.
Panel bedzie dostepny na http://IP_SERWERA/ oraz http://IP_SERWERA:9090/.
============================================================
BANNER
}

system_preflight() {
    log "Sprawdzam system"
    echo "Host: $(hostname 2>/dev/null || echo unknown)"
    echo "Kernel: $(uname -a)"
    echo "IP lokalne: $(first_ip)"
    local pub
    pub="$(public_ip)"
    [ -n "$pub" ] && echo "IP publiczne: $pub"

    local ram_mb disk_gb
    ram_mb="$(awk '/MemTotal/ {printf "%d", $2/1024}' /proc/meminfo 2>/dev/null || echo 0)"
    disk_gb="$(df -Pk / 2>/dev/null | awk 'NR==2 {printf "%d", $4/1024/1024}' || echo 0)"
    echo "RAM: ${ram_mb} MB"
    echo "Wolne miejsce /: ${disk_gb} GB"

    if [ "${ram_mb:-0}" -lt 1800 ]; then
        warn "Malo RAM. Panel ruszy, ale VM moga miec problem."
    fi
    if [ "${disk_gb:-0}" -lt 15 ]; then
        warn "Malo miejsca. Zalecane minimum dla pelnego NEXUS OS to 30+ GB."
    fi

    if [ -e /dev/kvm ]; then
        log "KVM widoczny: /dev/kvm"
    else
        warn "Nie widze /dev/kvm. Jesli to VPS, wlacz nested virtualization albo uzyj serwera dedykowanego."
    fi
}

ask_questions() {
    if ! is_interactive; then
        return 0
    fi

    if [ -z "$DOMAIN" ]; then
        echo
        read -r -p "Domena panelu, np. nexusos.pl (Enter = uzyj IP:9090): " DOMAIN || true
    fi

    if [ -n "$DOMAIN" ] && [ "$NO_CERT" != "1" ] && [ -z "$EMAIL" ]; then
        read -r -p "Email do HTTPS Let's Encrypt (Enter = bez HTTPS teraz): " EMAIL || true
    fi

    if [ -z "$ADMIN_PASSWORD" ]; then
        echo
        echo "Haslo admina mozesz zostawic puste - system wygeneruje je sam."
        read -r -s -p "Haslo admina (Enter = wygeneruj): " ADMIN_PASSWORD || true
        echo
    fi

    echo
    echo "Wybrana konfiguracja:"
    echo "  Domena: ${DOMAIN:-brak, panel na IP:9090}"
    echo "  HTTPS:  $([ -n "$EMAIL" ] && [ "$NO_CERT" != "1" ] && echo tak || echo nie/pozniej)"
    echo "  Tryb:   $([ "$PANEL_ONLY" = "1" ] && echo 'tylko panel' || echo 'pelny stack')"
    echo "  Kiosk:  $([ "$WITH_APPLIANCE" = "1" ] && echo "tak (${KIOSK_USER:-auto})" || echo nie)"
    echo
    read -r -p "Startowac instalacje? [ENTER = tak, Ctrl+C = przerwij] " _ || true
}

run_install() {
    local args=()

    if [ "$PANEL_ONLY" = "1" ]; then
        args=(--with-nginx)
        [ -n "$DOMAIN" ] && args+=(--domain "$DOMAIN")
        [ -n "$ADMIN_PASSWORD" ] && args+=(--admin-password "$ADMIN_PASSWORD")
        log "Odpalam prosty instalator panelu"
        bash "$SCRIPT_DIR/install.sh" "${args[@]}"
        return 0
    fi

    args=()
    [ -n "$DOMAIN" ] && args+=(--domain "$DOMAIN")
    [ -n "$ADMIN_PASSWORD" ] && args+=(--admin-password "$ADMIN_PASSWORD")
    [ "$NO_MINIO" = "1" ] && args+=(--no-minio)
    [ "$WITH_APPLIANCE" = "1" ] && args+=(--with-appliance)
    [ -n "$KIOSK_USER" ] && args+=(--kiosk-user "$KIOSK_USER")
    [ -n "$KIOSK_WIDTH" ] && args+=(--kiosk-width "$KIOSK_WIDTH")
    [ -n "$KIOSK_HEIGHT" ] && args+=(--kiosk-height "$KIOSK_HEIGHT")
    if [ -n "$EMAIL" ] && [ "$NO_CERT" != "1" ]; then
        args+=(--issue-cert "$EMAIL")
    fi

    log "Odpalam pelny instalator NEXUS OS"
    bash "$SCRIPT_DIR/install_everything.sh" "${args[@]}"
}

final_summary() {
    local ip url
    ip="$(public_ip)"
    [ -z "$ip" ] && ip="$(first_ip)"
    if [ -n "$DOMAIN" ] && [ -n "$EMAIL" ] && [ "$NO_CERT" != "1" ]; then
        url="https://$DOMAIN"
    elif [ -n "$DOMAIN" ]; then
        url="http://$DOMAIN"
    else
        url="http://${ip:-SERVER_IP}:9090"
    fi

    echo
    echo "============================================================"
    echo "NEXUS OS POWINIEN BYC GOTOWY"
    echo "============================================================"
    echo "Otworz:"
    if [ -z "$DOMAIN" ]; then
        echo "  http://${ip:-SERVER_IP}/"
    fi
    echo "  $url"
    echo "  $url/static/aero.html"
    echo
    echo "Diagnostyka:"
    echo "  /opt/nexusos/bin/nexusos-doctor.sh"
    echo
    echo "Log instalacji:"
    echo "  $LOG_FILE"
    echo
    echo "Status:"
    echo "  systemctl status nexusos --no-pager"
    echo "============================================================"
}

print_header
system_preflight
ask_questions
run_install
final_summary
