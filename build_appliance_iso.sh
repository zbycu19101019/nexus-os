#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# Build a bootable Debian Live ISO that contains the NEXUS OS installer package
# and an appliance autoinstall helper. Run this script on Debian as root.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"
OUT_DIR="${OUT_DIR:-$SCRIPT_DIR/../iso-output}"
WORK_DIR="${WORK_DIR:-$SCRIPT_DIR/../iso-build-work}"
ISO_NAME="${ISO_NAME:-nexusos-appliance.iso}"
KIOSK_USER="${NEXUS_KIOSK_USER:-nexuskiosk}"
KIOSK_PASSWORD="${NEXUS_KIOSK_PASSWORD:-changeme-nexus}"
DEBIAN_CODENAME="${DEBIAN_CODENAME:-}"

log() { printf '\033[1;36m[NEXUS ISO]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[NEXUS ISO ERROR]\033[0m %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

[ "$(id -u)" = "0" ] || die "Run as root on Debian: sudo bash build_appliance_iso.sh"
have apt-get || die "This ISO builder targets Debian with apt-get"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y live-build xorriso isolinux syslinux-common squashfs-tools debootstrap rsync

if [ -z "$DEBIAN_CODENAME" ] && [ -r /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    DEBIAN_CODENAME="${VERSION_CODENAME:-trixie}"
fi
DEBIAN_CODENAME="${DEBIAN_CODENAME:-trixie}"

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR" "$OUT_DIR"
cd "$WORK_DIR"

lb config \
  --distribution "$DEBIAN_CODENAME" \
  --archive-areas "main contrib non-free-firmware" \
  --binary-images iso-hybrid \
  --bootappend-live "boot=live components quiet splash loglevel=3 vt.global_cursor_default=0"

mkdir -p config/includes.chroot/opt/nexusos-installer
mkdir -p config/includes.chroot/usr/local/sbin
mkdir -p config/package-lists config/hooks/live
rsync -a --delete "$SCRIPT_DIR/" config/includes.chroot/opt/nexusos-installer/

cat > config/package-lists/nexusos-appliance.list.chroot <<'EOF'
sudo
curl
ca-certificates
python3
python3-venv
python3-pip
rsync
qemu-kvm
qemu-utils
libvirt-daemon-system
libvirt-clients
virtinst
bridge-utils
websockify
novnc
nginx
ovmf
swtpm
swtpm-tools
cage
chromium
seatd
dbus-user-session
libpam-systemd
xwayland
xserver-xorg-core
xserver-xorg-legacy
xinit
openbox
tint2
pcmanfm
xterm
x11-xserver-utils
fonts-dejavu-core
fonts-liberation
libgl1-mesa-dri
libegl1
mesa-vulkan-drivers
systemd-container
EOF

cat > config/includes.chroot/usr/local/sbin/nexusos-appliance-install <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
if ! id "$KIOSK_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$KIOSK_USER"
  printf '%s:%s\n' "$KIOSK_USER" "$KIOSK_PASSWORD" | chpasswd
fi
cd /opt/nexusos-installer
bash ./install_everything.sh --with-appliance --kiosk-user "$KIOSK_USER" --admin-password "$KIOSK_PASSWORD"
EOF
chmod 0755 config/includes.chroot/usr/local/sbin/nexusos-appliance-install

cat > config/hooks/live/9000-nexusos-preinstall.hook.chroot <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail

KIOSK_USER="$KIOSK_USER"
KIOSK_PASSWORD="$KIOSK_PASSWORD"

if ! id "\$KIOSK_USER" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "\$KIOSK_USER"
fi
printf '%s:%s\n' "\$KIOSK_USER" "\$KIOSK_PASSWORD" | chpasswd
for group in video render input seat; do
  getent group "\$group" >/dev/null 2>&1 && usermod -aG "\$group" "\$KIOSK_USER" || true
done

cd /opt/nexusos-installer
bash ./install.sh --with-hypervisor --with-nginx --no-systemd --prefix /opt/nexusos --port 9090 --bind 127.0.0.1 --admin-password "\$KIOSK_PASSWORD"

install -d -m 0755 /opt/nexusos/bin /etc/nexusos /etc/systemd/system/multi-user.target.wants
install -m 0755 ./bin/nexusos-kiosk.sh /opt/nexusos/bin/nexusos-kiosk.sh
cat > /etc/nexusos/kiosk.env <<'KIOSKENV'
NEXUS_KIOSK_URL=http://127.0.0.1:9090/
NEXUS_KIOSK_WIDTH=1920
NEXUS_KIOSK_HEIGHT=1080
NEXUS_KIOSK_POLL_SECONDS=2
NEXUS_APPLIANCE_LOCAL_SWITCH=1
KIOSKENV

uid="\$(id -u "\$KIOSK_USER")"
sed -e 's|__PREFIX__|/opt/nexusos|g' -e 's|__PORT__|9090|g' -e 's|__DOMAIN__|_|g' ./systemd/nexusos.service > /etc/systemd/system/nexusos.service
install -m 0755 ./bin/nexusos-desktop.sh /opt/nexusos/bin/nexusos-desktop.sh
sed -e 's|__PREFIX__|/opt/nexusos|g' -e "s|__KIOSK_USER__|\$KIOSK_USER|g" -e "s|__KIOSK_UID__|\$uid|g" ./systemd/nexusos-appliance.service > /etc/systemd/system/nexusos-appliance.service
sed -e 's|__PREFIX__|/opt/nexusos|g' -e "s|__KIOSK_USER__|\$KIOSK_USER|g" -e "s|__KIOSK_UID__|\$uid|g" ./systemd/nexusos-desktop.service > /etc/systemd/system/nexusos-desktop.service

ln -sf ../nexusos.service /etc/systemd/system/multi-user.target.wants/nexusos.service
ln -sf ../nexusos-appliance.service /etc/systemd/system/multi-user.target.wants/nexusos-appliance.service
ln -sf ../seatd.service /etc/systemd/system/multi-user.target.wants/seatd.service || true
rm -f /etc/systemd/system/multi-user.target.wants/nexusos-desktop.service || true
ln -sf /dev/null /etc/systemd/system/getty@tty1.service
systemctl set-default multi-user.target >/dev/null 2>&1 || true
EOF
chmod 0755 config/hooks/live/9000-nexusos-preinstall.hook.chroot

cat > config/hooks/live/9999-nexusos-readme.hook.chroot <<'EOF'
#!/usr/bin/env bash
set -e
cat >/etc/motd <<'MOTD'
NEXUS OS Appliance ISO

Install command:
  sudo nexusos-appliance-install

Default credentials prepared by the build script:
  kiosk/linux user: nexuskiosk / changeme-nexus
  NEXUS admin:      admin / changeme-nexus

Override before building:
  export NEXUS_KIOSK_USER='your-user'
  export NEXUS_KIOSK_PASSWORD='your-strong-password'
MOTD
EOF
chmod 0755 config/hooks/live/9999-nexusos-readme.hook.chroot

lb build

iso="$(find . -maxdepth 1 -type f -name '*.iso' | head -n 1)"
[ -n "$iso" ] || die "live-build finished without ISO"
install -m 0644 "$iso" "$OUT_DIR/$ISO_NAME"
log "ready ISO: $OUT_DIR/$ISO_NAME"
