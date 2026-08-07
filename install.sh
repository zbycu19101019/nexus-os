#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="/opt/nexusos"
PORT="9090"
BIND="0.0.0.0"
DOMAIN=""
WITH_NGINX="0"
WITH_HYPERVISOR="0"
NO_SYSTEMD="0"
ADMIN_PASSWORD=""

usage() {
    cat <<'USAGE'
NEXUS OS Linux installer

Usage:
  sudo bash install.sh [options]

Options:
  --prefix PATH          Install path. Default: /opt/nexusos
  --port PORT            Backend port. Default: 9090
  --bind ADDR            Backend bind address. Default: 0.0.0.0
  --domain DOMAIN        Public domain, e.g. nexusos.pl
  --with-nginx           Install/configure nginx reverse proxy
  --with-hypervisor      Install/configure QEMU, libvirt, virt-install, noVNC helpers
  --no-systemd           Do not install a systemd service
  --admin-password PASS  Write initial admin password to app/password.txt
  --help                 Show this help

Examples:
  sudo bash install.sh
  sudo bash install.sh --with-hypervisor --with-nginx --domain nexusos.pl
USAGE
}

log() { printf '\033[1;36m[NEXUS]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[NEXUS WARN]\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31m[NEXUS ERROR]\033[0m %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

while [ "$#" -gt 0 ]; do
    case "$1" in
        --prefix) PREFIX="${2:?missing value}"; shift 2 ;;
        --port) PORT="${2:?missing value}"; shift 2 ;;
        --bind) BIND="${2:?missing value}"; shift 2 ;;
        --domain) DOMAIN="${2:?missing value}"; shift 2 ;;
        --with-nginx) WITH_NGINX="1"; shift ;;
        --with-hypervisor) WITH_HYPERVISOR="1"; shift ;;
        --no-systemd) NO_SYSTEMD="1"; shift ;;
        --admin-password) ADMIN_PASSWORD="${2:?missing value}"; shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) die "Unknown option: $1" ;;
    esac
done

[ "$(id -u)" = "0" ] || die "Run as root: sudo bash install.sh"
[ -d "$SCRIPT_DIR/app" ] || die "Missing payload directory: $SCRIPT_DIR/app"
[ -f "$SCRIPT_DIR/app/server.py" ] || die "Missing backend: $SCRIPT_DIR/app/server.py"

APP_DIR="$PREFIX/app"
VENV_DIR="$PREFIX/venv"
ETC_DIR="/etc/nexusos"
ENV_FILE="$ETC_DIR/nexusos.env"
DATA_DIR="/var/lib/nexus"
ISO_STORAGE_DIR="$DATA_DIR/iso_storage"
UPLOAD_TMP_DIR="$DATA_DIR/upload_tmp"
LOG_DIR="/var/log/nexus"
BACKUP_DIR="/var/backups/nexusos"
LIBVIRT_IMAGE_DIR="/var/lib/libvirt/images"
PUBLIC_URL="${DOMAIN:+https://$DOMAIN}"
PUBLIC_URL="${PUBLIC_URL:-http://127.0.0.1:$PORT}"

detect_pm() {
    if have apt-get; then echo "apt"; return; fi
    if have dnf; then echo "dnf"; return; fi
    if have yum; then echo "yum"; return; fi
    if have pacman; then echo "pacman"; return; fi
    if have zypper; then echo "zypper"; return; fi
    if have apk; then echo "apk"; return; fi
    echo "none"
}

PM="$(detect_pm)"

install_packages() {
    local role="$1"; shift
    [ "$#" -gt 0 ] || return 0
    log "Installing $role packages via $PM"
    case "$PM" in
        apt)
            DEBIAN_FRONTEND=noninteractive apt-get update
            DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
            ;;
        dnf) dnf install -y "$@" ;;
        yum) yum install -y "$@" ;;
        pacman) pacman -Sy --needed --noconfirm "$@" ;;
        zypper) zypper --non-interactive install "$@" ;;
        apk) apk add --no-cache "$@" ;;
        none) warn "No supported package manager found. Install packages manually: $*"; return 1 ;;
    esac
}

install_base_deps() {
    case "$PM" in
        apt) install_packages "base" python3 python3-venv python3-pip curl ca-certificates tar gzip openssl rsync ;;
        dnf|yum) install_packages "base" python3 python3-pip curl ca-certificates tar gzip openssl rsync ;;
        pacman) install_packages "base" python python-pip curl ca-certificates tar gzip openssl rsync ;;
        zypper) install_packages "base" python3 python3-pip python3-virtualenv curl ca-certificates tar gzip openssl rsync ;;
        apk) install_packages "base" python3 py3-pip py3-virtualenv curl ca-certificates tar gzip openssl rsync ;;
        none) warn "Skipping base dependency installation";;
    esac
}

install_hypervisor_deps() {
    [ "$WITH_HYPERVISOR" = "1" ] || return 0
    set +e
    case "$PM" in
        apt) install_packages "hypervisor" qemu-kvm qemu-utils libvirt-daemon-system libvirt-clients virtinst bridge-utils websockify novnc nginx rclone ;;
        dnf|yum) install_packages "hypervisor" qemu-kvm qemu-img libvirt virt-install bridge-utils websockify novnc nginx rclone ;;
        pacman) install_packages "hypervisor" qemu-full libvirt virt-install dnsmasq bridge-utils websockify novnc nginx rclone ;;
        zypper) install_packages "hypervisor" qemu-kvm qemu-tools libvirt virt-install bridge-utils python3-websockify nginx rclone ;;
        apk) install_packages "hypervisor" qemu-system-x86_64 qemu-img libvirt libvirt-daemon py3-websockify nginx rclone ;;
        none) warn "Skipping hypervisor packages";;
    esac
    local rc=$?
    set -e
    if [ "$rc" -ne 0 ]; then
        warn "Some hypervisor packages were not installed. Continue, but VM features may need manual distro-specific packages."
    fi
}

python_bin() {
    if have python3; then echo "python3"; return; fi
    if have python; then echo "python"; return; fi
    die "Python 3 not found"
}

render_template() {
    local src="$1"
    local dst="$2"
    sed \
        -e "s|__PREFIX__|$PREFIX|g" \
        -e "s|__PORT__|$PORT|g" \
        -e "s|__DOMAIN__|${DOMAIN:-_}|g" \
        "$src" > "$dst"
}

install_base_deps
install_hypervisor_deps

log "Creating directories"
install -d -m 0755 "$PREFIX" "$APP_DIR" "$ETC_DIR" "$DATA_DIR" "$ISO_STORAGE_DIR" "$UPLOAD_TMP_DIR" "$LOG_DIR" "$BACKUP_DIR"
install -d -m 0755 "$LIBVIRT_IMAGE_DIR" "$LIBVIRT_IMAGE_DIR/nexus-isos" "$LIBVIRT_IMAGE_DIR/nexus-opencore-overlays" "$LIBVIRT_IMAGE_DIR/nexus-cupertino-media-overlays" 2>/dev/null || true

if [ -d "$APP_DIR" ] && [ -n "$(find "$APP_DIR" -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" ]; then
    SNAPSHOT="$PREFIX/app.backup.$(date +%Y%m%d-%H%M%S)"
    log "Existing app detected, creating backup: $SNAPSHOT"
    mkdir -p "$SNAPSHOT"
    if have rsync; then
        rsync -a "$APP_DIR/" "$SNAPSHOT/"
    else
        cp -a "$APP_DIR/." "$SNAPSHOT/"
    fi
fi

log "Copying NEXUS OS files"
if have rsync; then
    rsync -a --delete --exclude '__pycache__' "$SCRIPT_DIR/app/" "$APP_DIR/"
else
    rm -rf "$APP_DIR"
    mkdir -p "$APP_DIR"
    cp -a "$SCRIPT_DIR/app/." "$APP_DIR/"
    find "$APP_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} +
fi

PYTHON="$(python_bin)"
log "Preparing Python virtualenv"
"$PYTHON" -m venv "$VENV_DIR" || die "Could not create venv. Install python3-venv for this distro."
"$VENV_DIR/bin/python" -m pip install --upgrade pip wheel setuptools
"$VENV_DIR/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"

if [ -n "$ADMIN_PASSWORD" ]; then
    printf '%s' "$ADMIN_PASSWORD" > "$APP_DIR/password.txt"
    chmod 0600 "$APP_DIR/password.txt"
    if [ -f "$APP_DIR/users.json" ]; then
        warn "users.json already exists. Existing user database stays unchanged; change password in Admin/IAM after login if needed."
    fi
elif [ ! -f "$APP_DIR/password.txt" ]; then
    GENERATED_PASSWORD="$(openssl rand -base64 18 | tr -d '\n')"
    printf '%s' "$GENERATED_PASSWORD" > "$APP_DIR/password.txt"
    chmod 0600 "$APP_DIR/password.txt"
else
    GENERATED_PASSWORD=""
fi

log "Writing environment: $ENV_FILE"
cat > "$ENV_FILE" <<EOF
NEXUS_BIND=$BIND
NEXUS_PORT=$PORT
NEXUS_PUBLIC_URL=$PUBLIC_URL
NEXUS_BACKUP_DIR=$BACKUP_DIR
NEXUS_LIBVIRT_IMAGE_DIR=$LIBVIRT_IMAGE_DIR
NEXUS_ISO_STORAGE_DIR=$ISO_STORAGE_DIR
NEXUS_UPLOAD_TMP_DIR=$UPLOAD_TMP_DIR
NEXUS_LOG_DIR=$LOG_DIR
NEXUS_MAX_VM_UPLOAD_BYTES=85899345920
RCLONE_CONFIG=/root/.config/rclone/rclone.conf
PYTHONUNBUFFERED=1
EOF
chmod 0644 "$ENV_FILE"

cat > "$PREFIX/run-nexusos.sh" <<EOF
#!/usr/bin/env bash
set -a
[ -f "$ENV_FILE" ] && . "$ENV_FILE"
set +a
cd "$APP_DIR"
exec "$VENV_DIR/bin/python" "$APP_DIR/server.py"
EOF
chmod 0755 "$PREFIX/run-nexusos.sh"

if [ "$WITH_HYPERVISOR" = "1" ]; then
    log "Preparing KVM/libvirt services when available"
    modprobe kvm >/dev/null 2>&1 || true
    modprobe kvm_amd >/dev/null 2>&1 || modprobe kvm_intel >/dev/null 2>&1 || true
    if have systemctl; then
        systemctl enable --now libvirtd >/dev/null 2>&1 || systemctl enable --now virtqemud >/dev/null 2>&1 || true
        systemctl enable --now virtlogd >/dev/null 2>&1 || true
    fi
    if have virsh; then
        virsh net-autostart default >/dev/null 2>&1 || true
        virsh net-start default >/dev/null 2>&1 || true
    fi
    if [ -w /sys/kernel/mm/ksm/run ]; then
        echo 1 > /sys/kernel/mm/ksm/run || true
    fi
fi

if [ "$NO_SYSTEMD" != "1" ] && have systemctl && [ -d /run/systemd/system ]; then
    log "Installing systemd service"
    render_template "$SCRIPT_DIR/systemd/nexusos.service" /etc/systemd/system/nexusos.service
    systemctl daemon-reload
    systemctl enable --now nexusos.service
else
    warn "systemd service skipped. Start manually with: $PREFIX/run-nexusos.sh"
fi

if [ "$WITH_NGINX" = "1" ]; then
    if ! have nginx; then
        warn "nginx command not found after package install. Skipping reverse proxy."
    else
        log "Configuring nginx reverse proxy"
        render_template "$SCRIPT_DIR/nginx/nexusos.conf.example" /etc/nginx/conf.d/nexusos.conf
        nginx -t
        if have systemctl; then
            systemctl enable --now nginx >/dev/null 2>&1 || true
            systemctl reload nginx >/dev/null 2>&1 || systemctl restart nginx >/dev/null 2>&1 || true
        else
            nginx -s reload >/dev/null 2>&1 || nginx
        fi
    fi
fi

log "Smoke check"
if have curl; then
    curl -fsS "http://127.0.0.1:$PORT/" >/dev/null 2>&1 && log "HTTP is responding on port $PORT" || warn "HTTP check failed. Inspect: journalctl -u nexusos -n 80 --no-pager"
fi

cat <<EOF

NEXUS OS installed.

Open:
  $PUBLIC_URL
  $PUBLIC_URL/static/aero.html

Service:
  systemctl status nexusos --no-pager
  journalctl -u nexusos -f

Important paths:
  App:      $APP_DIR
  Env:      $ENV_FILE
  ISO:      $ISO_STORAGE_DIR
  VM disks: $LIBVIRT_IMAGE_DIR
  Logs:     $LOG_DIR
  Backups:  $BACKUP_DIR

EOF

if [ "${GENERATED_PASSWORD:-}" != "" ]; then
    cat <<EOF
Initial login:
  user: admin
  pass: $GENERATED_PASSWORD

Change it immediately in Admin/IAM.
EOF
fi

if [ -z "$ADMIN_PASSWORD" ] && [ "${GENERATED_PASSWORD:-}" = "" ]; then
    cat <<'EOF'
Initial login uses the existing app/password.txt or user database.
If this is a fresh payload with no users.json, default user is admin and password is read from app/password.txt.
EOF
fi
