# NEXUS OS Appliance Mode

Minimal Debian kiosk deployment for NEXUS OS.

The host boots to `multi-user.target`, skips desktop login, starts
`nexusos.service`, then launches Chromium in a locked full-screen Wayland
session on tty1 through `cage`. A protected bottom-right switch in AERO/Core can
move the machine between `KIOSK` and a lightweight `DESKTOP` emergency session.

## Micro Graphical Packages

```bash
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  cage chromium seatd dbus-user-session libpam-systemd \
  xwayland xserver-xorg-core xserver-xorg-legacy xinit openbox tint2 pcmanfm xterm \
  fonts-dejavu-core fonts-liberation \
  libgl1-mesa-dri libegl1 mesa-vulkan-drivers \
  curl ca-certificates systemd-container
```

Do not install GNOME, KDE, LXQt, XFCE, LightDM, GDM or SDDM unless you really
want a full desktop. The built-in fallback desktop uses Openbox to stay light.

## Kiosk/Desktop Switch

The panel exposes a fixed switch in the bottom-right corner:

- `PULPIT` while kiosk is active: stops `nexusos-appliance.service` and starts
  `nexusos-desktop.service`.
- `KIOSK` while desktop/TTY is active: stops desktop/display-manager/getty and
  starts `nexusos-appliance.service`.
- On the local appliance browser (`127.0.0.1`) the switch is allowed before
  login, so there is always a physical escape route.
- From another computer it requires an admin session token.

Manual commands:

```bash
sudo systemctl stop nexusos-appliance.service
sudo systemctl start nexusos-desktop.service

sudo systemctl stop nexusos-desktop.service display-manager.service getty@tty1.service
sudo systemctl start nexusos-appliance.service
```

## One Command

```bash
sudo bash install_everything.sh --with-appliance --kiosk-user zibi
```

Optional fixed viewport:

```bash
sudo bash install_everything.sh --with-appliance --kiosk-user zibi --kiosk-width 1920 --kiosk-height 1080
```

## Manual Enable

```bash
sudo systemctl disable --now lightdm gdm3 sddm lxdm xdm display-manager 2>/dev/null || true
sudo systemctl disable --now getty@tty1.service 2>/dev/null || true
sudo systemctl set-default multi-user.target
sudo systemctl daemon-reload
sudo systemctl enable --now seatd.service
sudo systemctl enable --now nexusos.service
sudo systemctl disable --now nexusos-desktop.service
sudo systemctl enable --now nexusos-appliance.service
```

## Quiet Boot

```bash
sudo cp -a /etc/default/grub /etc/default/grub.nexusos.bak.$(date +%Y%m%d-%H%M%S)
sudo sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash loglevel=3 vt.global_cursor_default=0"/' /etc/default/grub
sudo update-grub
```

## Diagnostics

```bash
systemctl status nexusos-appliance --no-pager
systemctl status nexusos-desktop --no-pager
journalctl -u nexusos-appliance -n 100 --no-pager
journalctl -u nexusos-desktop -n 100 --no-pager
systemctl status seatd --no-pager
```
