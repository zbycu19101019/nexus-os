# GitHub Publish Checklist

This folder is the repository root for NEXUS OS.

## 1. Final Local Check

```bash
python3 -m py_compile app/server.py
bash -n install.sh install_everything.sh INSTALLUJ_NEXUS.sh build_appliance_iso.sh
bash -n bin/nexusos-kiosk.sh bin/nexusos-desktop.sh uninstall.sh
```

## 2. Initialize Repository

```bash
git init
git add .
git status
git commit -m "Initial NEXUS OS release"
```

## 3. Connect Remote

```bash
git branch -M main
git remote add origin https://github.com/YOUR_NAME/YOUR_REPO.git
git push -u origin main
```

## 4. Do Not Commit

- ISO images, VM disks, OpenCore files, Windows/macOS/Linux installer media.
- `app/password.txt`, `app/users.json`, `app/gemini_key.txt`.
- rclone/Google Drive tokens and MinIO credentials.
- Backups, upload folders, logs and runtime JSON state.

## 5. Release Artifacts

If you want to attach installers to a GitHub Release, generate them outside the
repository and upload them as release binaries:

```bash
tar -czf nexusos-linux-installer.tar.gz nexusos_linux_package
sudo bash nexusos_linux_package/build_appliance_iso.sh
```

Large ISO files should go to GitHub Releases, object storage or your own download
server, not into git history.
