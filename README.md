# NEXUS OS Linux Rebuild Package

This package rebuilds the NEXUS OS control panel after a VPS loss.
It contains the FastAPI backend, Classic Core UI, AERO UI, Hyper-Deck VM controls,
file/media modules, transfer center, admin/IAM tools, and Windows Manager downloads.

Full Polish operator/admin documentation:

```text
docs/NEXUS_OS_DOKUMENTACJA.md
```

## Quick install

Idiot-proof install, recommended:

```bash
bash INSTALLUJ_NEXUS.sh
```

This default mode asks nothing. It installs the full stack and exposes:

```text
http://SERVER_IP/
http://SERVER_IP:9090/
```

If you do not pass `--admin-password`, the installer generates the initial
administrator password locally and stores it in `/opt/nexusos/app/password.txt`.
For a known first password, use:

```bash
sudo bash install_everything.sh --admin-password 'change-me-now'
```

If you use the one-file installer:

```bash
bash nexusos-installer.run
```

This also asks nothing by default. Use `--ask` only if you intentionally want the interactive wizard.

Full fresh-VPS install, recommended when you want everything:

```bash
tar -xzf nexusos-linux-installer.tar.gz
cd nexusos_linux_package
sudo bash install_everything.sh --domain nexusos.pl
```

Full install with HTTPS attempt:

```bash
sudo bash install_everything.sh --domain nexusos.pl --issue-cert you@example.com
```

The full installer adds NEXUS OS, KVM/libvirt/QEMU, nginx, noVNC helpers,
OVMF/UEFI tooling, swtpm, bridge/Open vSwitch/network tools, ISO utilities,
hardware telemetry tools, rclone, certbot, MinIO object storage and a doctor script.

Standard install:

```bash
tar -xzf nexusos-linux-installer.tar.gz
cd nexusos_linux_package
sudo bash install.sh --with-hypervisor --with-nginx --domain nexusos.pl
```

Minimal panel-only install:

```bash
sudo bash install.sh
```

Open after install:

```text
http://SERVER_IP:9090/
http://SERVER_IP:9090/static/aero.html
```

If `--with-nginx --domain nexusos.pl` was used and DNS points to the VPS:

```text
http://nexusos.pl/
http://nexusos.pl/static/aero.html
```

## Supported Linux families

The installer detects and uses:

- Debian / Ubuntu / Proxmox: `apt-get`
- Fedora / Rocky / Alma / RHEL-like: `dnf` or `yum`
- Arch / Endeavour / Manjaro: `pacman`
- openSUSE: `zypper`
- Alpine: `apk`

The panel can install without hypervisor packages on almost any Linux with Python 3.
Full VM control needs KVM/libvirt support from the host provider.

## Important paths

```text
App:               /opt/nexusos/app
Virtualenv:        /opt/nexusos/venv
Env file:          /etc/nexusos/nexusos.env
ISO storage:       /var/lib/nexus/iso_storage
Chunk uploads:     /var/lib/nexus/upload_tmp
VM disks:          /var/lib/libvirt/images
Panel logs:        /var/log/nexus
Backups:           /var/backups/nexusos
```

These paths can be changed in `/etc/nexusos/nexusos.env`.

## Service commands

```bash
systemctl status nexusos --no-pager
journalctl -u nexusos -f
systemctl restart nexusos
```

Full installer diagnostic:

```bash
/opt/nexusos/bin/nexusos-doctor.sh
```

If systemd is not available:

```bash
/opt/nexusos/run-nexusos.sh
```

## What was rebuilt from the conversation

- Classic dark NEXUS Core dashboard.
- AERO / Pure Snow panel.
- Login with users and admin/IAM area.
- VM / Hyper-Deck controls: create, start, shutdown, reset, delete, config, logs, snapshots, ISO tools.
- ISO vault and chunked uploads prepared for large files.
- OpenCore / Cupertino workflow as BYOL infrastructure only.
- VM noVNC console shell with scaling controls, focus, mouse reset, keyboard panel, clipboard buttons and ISO modal entry points.
- Media Deck, Visual Archive, Secure Drop, BBS, Kanban, chat drawer, news/weather/radio/games modules.
- Admin backups for panel and whole-server archive paths.
- Token/time billing files and VM ownership data files.
- Object/Vault/Drive bridge files, including rclone config path for Google Drive workflows.
- Windows Nexus Capsule Manager download area from the static payload.

## BYOL and legal shield

NEXUS OS only provides infrastructure orchestration.
It does not ship Apple licenses, OSK/SMC secrets, protected Apple components,
Windows licenses, or third-party commercial OS licenses.

For macOS/OpenCore workflows:

- Upload your own legal bootloader/media to `/var/lib/nexus/iso_storage`.
- Use the panel's Cupertino BYOL confirmation before starting such a VM.
- Keep OpenCore and recovery images under your own license/compliance responsibility.

## Large uploads and 413 errors

The nginx template sets:

```nginx
client_max_body_size 0;
```

This removes the classic `413 Request Entity Too Large` proxy block.
The backend also uses a configurable upload limit:

```text
NEXUS_MAX_VM_UPLOAD_BYTES=85899345920
```

For very large ISO/qcow2 files, direct admin transfer is still recommended:

```bash
rsync -avP ./isos/ root@SERVER:/var/lib/nexus/iso_storage/
```

## Google Drive / rclone

Configure rclone as root:

```bash
rclone config
```

Default config path:

```text
/root/.config/rclone/rclone.conf
```

The app reads it from `RCLONE_CONFIG`.

## MinIO object storage

`install_everything.sh` installs MinIO unless `--no-minio` is passed.

```text
API:     http://SERVER_IP:9000
Console: http://SERVER_IP:9001
Env:     /etc/nexusos/minio.env
Data:    /var/lib/nexus/minio
```

Credentials are generated locally and saved in `/etc/nexusos/minio.env`.

## Fresh VPS checklist

1. Point DNS `nexusos.pl` to the new VPS IP.
2. Install the package with `--with-hypervisor --with-nginx --domain nexusos.pl`.
3. Confirm `/var/lib/libvirt/images` has enough free space.
4. Upload ISO files to `/var/lib/nexus/iso_storage`.
5. Upload OpenCore only if you own and manage the BYOL macOS flow.
6. Open AERO and scan the hypervisor.
7. Change the admin password in Admin/IAM.
8. Create a server backup after first good boot.

## Uninstall

Remove app, keep data:

```bash
sudo bash uninstall.sh
```

Remove app and data:

```bash
sudo bash uninstall.sh --purge
```
