#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="/opt/nexusos"
PORT="9090"
BIND="0.0.0.0"
DOMAIN=""
ADMIN_PASSWORD="${NEXUS_ADMIN_PASSWORD:-}"
NO_SYSTEMD="0"
NO_MINIO="0"
WITH_APPLIANCE="0"
KIOSK_USER="${NEXUS_KIOSK_USER:-}"
KIOSK_WIDTH="${NEXUS_KIOSK_WIDTH:-1920}"
KIOSK_HEIGHT="${NEXUS_KIOSK_HEIGHT:-1080}"
ISSUE_CERT_EMAIL=""

usage() {
    cat <<'USAGE'
NEXUS OS full-stack installer

This is the "install literally everything" path for a fresh Linux VPS.
It installs NEXUS OS plus KVM/libvirt/QEMU, nginx, noVNC helpers, OVMF,
TPM support, bridge/network tooling, ISO utilities, hardware telemetry tools,
rclone/Drive helpers, certbot, optional MinIO object storage and diagnostic scripts.

Usage:
  sudo bash install_everything.sh [options]

Options:
  --prefix PATH          Install path. Default: /opt/nexusos
  --port PORT            Backend port. Default: 9090
  --bind ADDR            Backend bind address. Default: 0.0.0.0
  --domain DOMAIN        Public domain, e.g. nexusos.pl
  --admin-password PASS  Initial admin password
  --no-systemd           Do not install systemd services
  --no-minio             Skip MinIO object storage service
  --with-appliance       Enable bare-metal kiosk mode on tty1 (cage + Chromium) plus emergency desktop switch
  --kiosk-user USER      Non-root user for kiosk. Default: zibi/UID 1000/SUDO_USER
  --kiosk-width PX       Chromium kiosk viewport width. Default: 1920
  --kiosk-height PX      Chromium kiosk viewport height. Default: 1080
  --issue-cert EMAIL     Run certbot for DOMAIN using this email after nginx is ready
  --help                 Show this help

Recommended:
  sudo bash install_everything.sh --domain nexusos.pl --issue-cert you@example.com
USAGE
}

log() { printf '\033[1;36m[NEXUS FULL]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[NEXUS FULL WARN]\033[0m %s\n' "$*" >&2; }
die() { printf '\033[1;31m[NEXUS FULL ERROR]\033[0m %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

while [ "$#" -gt 0 ]; do
    case "$1" in
        --prefix) PREFIX="${2:?missing value}"; shift 2 ;;
        --port) PORT="${2:?missing value}"; shift 2 ;;
        --bind) BIND="${2:?missing value}"; shift 2 ;;
        --domain) DOMAIN="${2:?missing value}"; shift 2 ;;
        --admin-password) ADMIN_PASSWORD="${2:?missing value}"; shift 2 ;;
        --no-systemd) NO_SYSTEMD="1"; shift ;;
        --no-minio) NO_MINIO="1"; shift ;;
        --with-appliance) WITH_APPLIANCE="1"; shift ;;
        --kiosk-user) KIOSK_USER="${2:?missing value}"; shift 2 ;;
        --kiosk-width) KIOSK_WIDTH="${2:?missing value}"; shift 2 ;;
        --kiosk-height) KIOSK_HEIGHT="${2:?missing value}"; shift 2 ;;
        --issue-cert) ISSUE_CERT_EMAIL="${2:?missing value}"; shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) die "Unknown option: $1" ;;
    esac
done

[ "$(id -u)" = "0" ] || die "Run as root: sudo bash install_everything.sh"
[ -f "$SCRIPT_DIR/install.sh" ] || die "Missing installer: $SCRIPT_DIR/install.sh"

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

pm_update() {
    case "$PM" in
        apt) DEBIAN_FRONTEND=noninteractive apt-get update ;;
        pacman) pacman -Sy --noconfirm ;;
        zypper) zypper --non-interactive refresh ;;
        dnf|yum|apk|none) true ;;
    esac
}

pm_install_one() {
    local pkg="$1"
    case "$PM" in
        apt) DEBIAN_FRONTEND=noninteractive apt-get install -y "$pkg" ;;
        dnf) dnf install -y "$pkg" ;;
        yum) yum install -y "$pkg" ;;
        pacman) pacman -S --needed --noconfirm "$pkg" ;;
        zypper) zypper --non-interactive install "$pkg" ;;
        apk) apk add --no-cache "$pkg" ;;
        none) return 1 ;;
    esac
}

install_best_effort() {
    local label="$1"; shift
    log "Installing extra layer: $label"
    for pkg in "$@"; do
        if pm_install_one "$pkg" >/dev/null 2>&1; then
            log "OK package: $pkg"
        else
            warn "Skipped/unavailable package on this distro: $pkg"
        fi
    done
}

full_extra_packages() {
    case "$PM" in
        apt)
            echo ovmf swtpm swtpm-tools dnsmasq-base bridge-utils openvswitch-switch nftables iptables ipset ebtables smartmontools lm-sensors nvme-cli jq unzip p7zip-full genisoimage xorriso cloud-image-utils whois acl socat certbot python3-certbot-nginx git make gcc pkg-config qemu-guest-agent
            ;;
        dnf|yum)
            echo edk2-ovmf swtpm swtpm-tools dnsmasq bridge-utils openvswitch nftables iptables ipset ebtables smartmontools lm_sensors nvme-cli jq unzip p7zip p7zip-plugins genisoimage xorriso cloud-utils-growpart whois acl socat certbot python3-certbot-nginx git make gcc pkgconf-pkg-config qemu-guest-agent
            ;;
        pacman)
            echo edk2-ovmf swtpm dnsmasq openvswitch nftables iptables ipset ebtables smartmontools lm_sensors nvme-cli jq unzip p7zip cdrtools xorriso cloud-utils whois acl socat certbot certbot-nginx git make gcc pkgconf qemu-guest-agent
            ;;
        zypper)
            echo ovmf swtpm swtpm-tools dnsmasq bridge-utils openvswitch nftables iptables ipset ebtables smartmontools sensors nvme-cli jq unzip p7zip genisoimage xorriso cloud-init growpart whois acl socat certbot python3-certbot-nginx git make gcc pkgconf-pkg-config qemu-guest-agent
            ;;
        apk)
            echo ovmf swtpm dnsmasq bridge openvswitch nftables iptables ipset ebtables smartmontools lm-sensors nvme-cli jq unzip p7zip cdrkit xorriso cloud-utils-growpart whois acl socat certbot certbot-nginx git make gcc pkgconf qemu-guest-agent
            ;;
        none)
            echo
            ;;
    esac
}

install_minio() {
    [ "$NO_MINIO" = "0" ] || return 0
    if have minio; then
        log "MinIO already installed"
    else
        local arch minio_arch url
        arch="$(uname -m)"
        case "$arch" in
            x86_64|amd64) minio_arch="amd64" ;;
            aarch64|arm64) minio_arch="arm64" ;;
            *) warn "MinIO binary skipped for unsupported arch: $arch"; return 0 ;;
        esac
        url="https://dl.min.io/server/minio/release/linux-${minio_arch}/minio"
        if have curl; then
            log "Installing MinIO from $url"
            curl -fsSL "$url" -o /usr/local/bin/minio && chmod 0755 /usr/local/bin/minio || {
                warn "MinIO download failed"
                return 0
            }
        else
            warn "curl missing, MinIO skipped"
            return 0
        fi
    fi

    install -d -m 0755 /var/lib/nexus/minio /etc/nexusos
    if [ ! -f /etc/nexusos/minio.env ]; then
        local root_user root_pass
        root_user="nexusadmin"
        root_pass="$(openssl rand -base64 30 | tr -d '\n' | tr '/+' 'Aa')"
        cat > /etc/nexusos/minio.env <<EOF
MINIO_ROOT_USER=$root_user
MINIO_ROOT_PASSWORD=$root_pass
MINIO_VOLUMES=/var/lib/nexus/minio
MINIO_OPTS=--console-address :9001
EOF
        chmod 0600 /etc/nexusos/minio.env
        log "MinIO credentials saved in /etc/nexusos/minio.env"
    fi

    if [ "$NO_SYSTEMD" != "1" ] && have systemctl && [ -d /run/systemd/system ]; then
        cat > /etc/systemd/system/nexus-minio.service <<'EOF'
[Unit]
Description=NEXUS Object Storage (MinIO)
Wants=network-online.target
After=network-online.target

[Service]
EnvironmentFile=/etc/nexusos/minio.env
ExecStart=/usr/local/bin/minio server $MINIO_OPTS $MINIO_VOLUMES
Restart=always
RestartSec=3
User=root
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF
        systemctl daemon-reload
        systemctl enable --now nexus-minio.service >/dev/null 2>&1 || warn "Could not start nexus-minio.service"
    fi
}

detect_kiosk_user() {
    if [ -n "$KIOSK_USER" ]; then echo "$KIOSK_USER"; return 0; fi
    if id zibi >/dev/null 2>&1; then echo zibi; return 0; fi
    local uid1000
    uid1000="$(awk -F: '$3 == 1000 { print $1; exit }' /etc/passwd 2>/dev/null || true)"
    if [ -n "$uid1000" ]; then echo "$uid1000"; return 0; fi
    if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ] && id "$SUDO_USER" >/dev/null 2>&1; then echo "$SUDO_USER"; return 0; fi
    echo nexuskiosk
}

install_appliance_deps() {
    [ "$WITH_APPLIANCE" = "1" ] || return 0
    log "Installing appliance kiosk stack"
    case "$PM" in
        apt)
            install_best_effort "appliance kiosk" cage chromium seatd dbus-user-session libpam-systemd xwayland fonts-dejavu-core fonts-liberation libgl1-mesa-dri libegl1 mesa-vulkan-drivers curl ca-certificates systemd-container xserver-xorg-core xserver-xorg-legacy xinit openbox tint2 pcmanfm xterm x11-xserver-utils
            ;;
        *)
            warn "Appliance mode is production-targeted for minimal Debian. Trying best-effort packages for $PM."
            install_best_effort "appliance kiosk" cage chromium chromium-browser seatd dbus-user-session xwayland curl ca-certificates xorg-xinit openbox tint2 pcmanfm xterm
            ;;
    esac
    have cage || die "Appliance mode requires cage"
    if ! have chromium && ! have chromium-browser && ! have google-chrome-stable && ! have google-chrome; then
        die "Appliance mode requires Chromium"
    fi
    if ! have startx || ! have openbox-session; then
        warn "Emergency desktop packages are incomplete. The web switch will still fall back to display-manager/tty."
    fi
}

add_user_to_existing_groups() {
    local user="$1" group
    for group in video render input seat; do
        if getent group "$group" >/dev/null 2>&1; then
            usermod -aG "$group" "$user" || warn "Could not add $user to group $group"
        fi
    done
}

render_appliance_template() {
    local src="$1" dst="$2" uid="$3"
    sed \
        -e "s|__PREFIX__|$PREFIX|g" \
        -e "s|__KIOSK_USER__|$KIOSK_USER|g" \
        -e "s|__KIOSK_UID__|$uid|g" \
        "$src" > "$dst"
}

configure_quiet_boot() {
    [ "$WITH_APPLIANCE" = "1" ] || return 0
    [ -f /etc/default/grub ] || { warn "GRUB config not found, quiet boot skipped"; return 0; }
    cp -a /etc/default/grub "/etc/default/grub.nexusos.bak.$(date +%Y%m%d-%H%M%S)" || true
    if grep -q '^GRUB_CMDLINE_LINUX_DEFAULT=' /etc/default/grub; then
        sed -i 's|^GRUB_CMDLINE_LINUX_DEFAULT=.*|GRUB_CMDLINE_LINUX_DEFAULT="quiet splash loglevel=3 vt.global_cursor_default=0"|' /etc/default/grub
    else
        printf '%s\n' 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash loglevel=3 vt.global_cursor_default=0"' >> /etc/default/grub
    fi
    if have update-grub; then
        update-grub || warn "update-grub failed"
    elif have grub-mkconfig; then
        grub-mkconfig -o /boot/grub/grub.cfg || warn "grub-mkconfig failed"
    else
        warn "No GRUB update command found"
    fi
}

install_appliance_mode() {
    [ "$WITH_APPLIANCE" = "1" ] || return 0
    [ "$NO_SYSTEMD" != "1" ] || die "--with-appliance requires systemd"
    have systemctl || die "--with-appliance requires systemd"
    [ -f "$SCRIPT_DIR/bin/nexusos-kiosk.sh" ] || die "Missing kiosk launcher: $SCRIPT_DIR/bin/nexusos-kiosk.sh"
    [ -f "$SCRIPT_DIR/bin/nexusos-desktop.sh" ] || die "Missing desktop launcher: $SCRIPT_DIR/bin/nexusos-desktop.sh"
    [ -f "$SCRIPT_DIR/systemd/nexusos-appliance.service" ] || die "Missing appliance unit template"
    [ -f "$SCRIPT_DIR/systemd/nexusos-desktop.service" ] || die "Missing desktop unit template"

    KIOSK_USER="$(detect_kiosk_user)"
    [ "$KIOSK_USER" != "root" ] || die "Kiosk user cannot be root"
    if ! id "$KIOSK_USER" >/dev/null 2>&1; then
        log "Creating unprivileged kiosk user: $KIOSK_USER"
        useradd -m -s /bin/bash "$KIOSK_USER"
    fi
    local uid
    uid="$(id -u "$KIOSK_USER")"
    [ "$uid" != "0" ] || die "Kiosk user cannot have UID 0"
    add_user_to_existing_groups "$KIOSK_USER"

    install -d -m 0755 "$PREFIX/bin" /etc/nexusos
    install -m 0755 "$SCRIPT_DIR/bin/nexusos-kiosk.sh" "$PREFIX/bin/nexusos-kiosk.sh"
    install -m 0755 "$SCRIPT_DIR/bin/nexusos-desktop.sh" "$PREFIX/bin/nexusos-desktop.sh"
    cat > /etc/nexusos/kiosk.env <<EOF
NEXUS_KIOSK_URL=http://127.0.0.1:${PORT}/
NEXUS_KIOSK_WIDTH=${KIOSK_WIDTH}
NEXUS_KIOSK_HEIGHT=${KIOSK_HEIGHT}
NEXUS_KIOSK_POLL_SECONDS=2
NEXUS_APPLIANCE_LOCAL_SWITCH=1
EOF
    chmod 0644 /etc/nexusos/kiosk.env

    render_appliance_template "$SCRIPT_DIR/systemd/nexusos-appliance.service" /etc/systemd/system/nexusos-appliance.service "$uid"
    render_appliance_template "$SCRIPT_DIR/systemd/nexusos-desktop.service" /etc/systemd/system/nexusos-desktop.service "$uid"
    systemctl enable --now seatd.service >/dev/null 2>&1 || warn "Could not start seatd.service"
    for svc in lightdm gdm3 sddm lxdm xdm display-manager; do
        systemctl disable --now "$svc" >/dev/null 2>&1 || true
    done
    systemctl disable --now getty@tty1.service >/dev/null 2>&1 || true
    systemctl disable --now nexusos-desktop.service >/dev/null 2>&1 || true
    systemctl set-default multi-user.target >/dev/null 2>&1 || true
    configure_quiet_boot
    systemctl daemon-reload
    systemctl enable --now nexusos-appliance.service >/dev/null 2>&1 || warn "Could not start nexusos-appliance.service yet; it will retry after reboot"
    log "Appliance kiosk enabled on tty1 as $KIOSK_USER (uid $uid)"
}

write_doctor() {
    install -d -m 0755 "$PREFIX/bin"
    cat > "$PREFIX/bin/nexusos-doctor.sh" <<'EOF'
#!/usr/bin/env bash
set -u
FIX=0
case "${1:-}" in
  --fix|-f) FIX=1 ;;
  --help|-h)
    echo "Usage: nexusos-doctor.sh [--fix]"
    exit 0
    ;;
esac

[ -f /etc/nexusos/nexusos.env ] && . /etc/nexusos/nexusos.env
PORT="${NEXUS_PORT:-9090}"
ISO_DIR="${NEXUS_ISO_STORAGE_DIR:-/var/lib/nexus/iso_storage}"
LIBVIRT_DIR="${NEXUS_LIBVIRT_IMAGE_DIR:-/var/lib/libvirt/images}"
LOG_DIR="${NEXUS_LOG_DIR:-/var/log/nexus}"

ok() { printf '\033[1;32m[OK]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[WARN]\033[0m %s\n' "$*"; }
bad() { printf '\033[1;31m[FAIL]\033[0m %s\n' "$*"; }
info() { printf '\033[1;36m[INFO]\033[0m %s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

service_state() {
  local svc="$1"
  if ! have systemctl; then warn "systemctl unavailable"; return; fi
  if systemctl is-active --quiet "$svc" 2>/dev/null; then ok "service $svc active"; else warn "service $svc inactive/missing"; fi
}

port_state() {
  local port="$1" label="$2"
  if have ss && ss -ltn "( sport = :$port )" 2>/dev/null | grep -q ":$port"; then ok "port $port $label open"; return; fi
  if timeout 1 bash -c "</dev/tcp/127.0.0.1/$port" >/dev/null 2>&1; then ok "port $port $label reachable"; else warn "port $port $label closed"; fi
}

fix_permissions() {
  [ "$FIX" = "1" ] || return 0
  info "repairing NEXUS/libvirt storage permissions"
  install -d -m 0755 "$ISO_DIR" "$LIBVIRT_DIR" "$LIBVIRT_DIR/nexus-isos" "$LOG_DIR" 2>/dev/null || true
  chmod 0755 "$ISO_DIR" "$LIBVIRT_DIR" "$LIBVIRT_DIR/nexus-isos" "$LOG_DIR" 2>/dev/null || true
  find "$ISO_DIR" "$LIBVIRT_DIR/nexus-isos" -type d -exec chmod 0755 {} \; 2>/dev/null || true
  find "$ISO_DIR" "$LIBVIRT_DIR/nexus-isos" -type f -exec chmod 0644 {} \; 2>/dev/null || true
  if have setfacl && id libvirt-qemu >/dev/null 2>&1; then
    setfacl -R -m u:libvirt-qemu:rx "$ISO_DIR" "$LIBVIRT_DIR/nexus-isos" 2>/dev/null || true
    find "$ISO_DIR" "$LIBVIRT_DIR/nexus-isos" -type f -exec setfacl -m u:libvirt-qemu:r {} \; 2>/dev/null || true
  fi
  ok "permissions repaired for ISO Vault and libvirt image folders"
}

echo "== NEXUS OS doctor =="
fix_permissions

echo "-- services --"
for svc in nexusos nginx libvirtd virtqemud virtlogd nexus-minio postgresql; do service_state "$svc"; done

echo "-- ports --"
port_state "$PORT" "NEXUS API"
port_state 80 "HTTP"
port_state 443 "HTTPS"
port_state 9000 "MinIO API"
port_state 9001 "MinIO console"

echo "-- api --"
if have curl && curl -fsS "http://127.0.0.1:$PORT/" >/dev/null 2>&1; then ok "NEXUS HTTP responds on 127.0.0.1:$PORT"; else bad "NEXUS HTTP not responding on 127.0.0.1:$PORT"; fi

echo "-- virtualization --"
[ -e /dev/kvm ] && ok "/dev/kvm exists" || warn "/dev/kvm missing - nested virtualization may be disabled"
lsmod 2>/dev/null | grep -q '^kvm' && ok "kvm kernel module loaded" || warn "kvm module not visible"
have qemu-img && ok "qemu-img: $(qemu-img --version | head -n 1)" || bad "qemu-img missing"
if have virsh; then virsh list --all || warn "virsh list failed"; else bad "virsh missing"; fi

echo "-- disk and memory --"
df -h / "$ISO_DIR" "$LIBVIRT_DIR" 2>/dev/null || df -h /
free -h 2>/dev/null || true

echo "-- recent service log --"
journalctl -u nexusos -n 25 --no-pager 2>/dev/null || warn "journalctl nexusos unavailable"

echo "-- iso storage sample --"
find "$ISO_DIR" "$LIBVIRT_DIR/nexus-isos" -maxdepth 1 -type f 2>/dev/null | sed 's#^#  #' | head -n 30 || true
EOF
    chmod 0755 "$PREFIX/bin/nexusos-doctor.sh"
}

configure_host() {
    log "Configuring host services and kernel helpers"
    modprobe kvm >/dev/null 2>&1 || true
    modprobe kvm_amd >/dev/null 2>&1 || modprobe kvm_intel >/dev/null 2>&1 || true
    modprobe nbd max_part=16 >/dev/null 2>&1 || true

    if [ -w /sys/kernel/mm/ksm/run ]; then echo 1 > /sys/kernel/mm/ksm/run || true; fi
    if [ -w /sys/kernel/mm/ksm/pages_to_scan ]; then echo 1000 > /sys/kernel/mm/ksm/pages_to_scan || true; fi
    if [ -w /sys/kernel/mm/ksm/sleep_millisecs ]; then echo 100 > /sys/kernel/mm/ksm/sleep_millisecs || true; fi

    if have systemctl; then
        systemctl enable --now libvirtd >/dev/null 2>&1 || systemctl enable --now virtqemud >/dev/null 2>&1 || true
        systemctl enable --now virtlogd >/dev/null 2>&1 || true
        systemctl enable --now openvswitch >/dev/null 2>&1 || systemctl enable --now openvswitch-switch >/dev/null 2>&1 || true
    fi

    if have virsh; then
        virsh net-autostart default >/dev/null 2>&1 || true
        virsh net-start default >/dev/null 2>&1 || true
    fi

    if have ufw; then
        ufw allow 80/tcp >/dev/null 2>&1 || true
        ufw allow 443/tcp >/dev/null 2>&1 || true
        ufw allow "$PORT/tcp" >/dev/null 2>&1 || true
        ufw allow 9000/tcp >/dev/null 2>&1 || true
        ufw allow 9001/tcp >/dev/null 2>&1 || true
    fi

    if have firewall-cmd; then
        firewall-cmd --permanent --add-service=http >/dev/null 2>&1 || true
        firewall-cmd --permanent --add-service=https >/dev/null 2>&1 || true
        firewall-cmd --permanent --add-port="${PORT}/tcp" >/dev/null 2>&1 || true
        firewall-cmd --permanent --add-port=9000/tcp >/dev/null 2>&1 || true
        firewall-cmd --permanent --add-port=9001/tcp >/dev/null 2>&1 || true
        firewall-cmd --reload >/dev/null 2>&1 || true
    fi
}

issue_certificate() {
    [ -n "$ISSUE_CERT_EMAIL" ] || return 0
    [ -n "$DOMAIN" ] || { warn "--issue-cert requires --domain"; return 0; }
    if ! have certbot; then
        warn "certbot unavailable, certificate skipped"
        return 0
    fi
    log "Requesting Let's Encrypt certificate for $DOMAIN"
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$ISSUE_CERT_EMAIL" --redirect || warn "Certbot failed. Check DNS and rerun certbot manually."
}

log "Package manager: $PM"
pm_update || warn "Package index refresh failed; continuing"

EXTRAS="$(full_extra_packages)"
if [ -n "$EXTRAS" ]; then
    # shellcheck disable=SC2086
    install_best_effort "enterprise host extras" $EXTRAS
else
    warn "No supported package manager. Core installer will still try to continue."
fi
install_appliance_deps

INSTALL_ARGS=(--with-hypervisor --with-nginx --prefix "$PREFIX" --port "$PORT" --bind "$BIND")
[ -n "$DOMAIN" ] && INSTALL_ARGS+=(--domain "$DOMAIN")
[ -n "$ADMIN_PASSWORD" ] && INSTALL_ARGS+=(--admin-password "$ADMIN_PASSWORD")
[ "$NO_SYSTEMD" = "1" ] && INSTALL_ARGS+=(--no-systemd)

log "Running core NEXUS installer"
bash "$SCRIPT_DIR/install.sh" "${INSTALL_ARGS[@]}"

install_minio
configure_host
write_doctor
install_appliance_mode
"$PREFIX/bin/nexusos-doctor.sh" --fix || warn "Doctor reported issues; inspect output above and rerun $PREFIX/bin/nexusos-doctor.sh --fix"
issue_certificate

cat <<EOF

NEXUS full-stack install finished.

Open:
  ${DOMAIN:+https://$DOMAIN}
  http://SERVER_IP:$PORT

Doctor:
  $PREFIX/bin/nexusos-doctor.sh

Appliance:
  ${WITH_APPLIANCE:+systemctl status nexusos-appliance --no-pager}
  ${WITH_APPLIANCE:+systemctl status nexusos-desktop --no-pager}
  ${WITH_APPLIANCE:+journalctl -u nexusos-appliance -n 100 --no-pager}

MinIO:
  API:     http://SERVER_IP:9000
  Console: http://SERVER_IP:9001
  Env:     /etc/nexusos/minio.env

Next steps:
  1. Change admin password in Admin/IAM.
  2. Upload ISO files to /var/lib/nexus/iso_storage.
  3. Run $PREFIX/bin/nexusos-doctor.sh.
  4. Create first backup from Admin.

EOF
