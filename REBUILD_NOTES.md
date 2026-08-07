# NEXUS OS rebuild notes

This package was assembled from `outputs/nexus_merged_candidate`.

Portability changes:

- `NEXUS_BACKUP_DIR` replaces the hardcoded `/root/backups` default.
- `NEXUS_LIBVIRT_IMAGE_DIR` controls VM disk/image root.
- `NEXUS_ISO_STORAGE_DIR` controls large ISO/OpenCore storage.
- `NEXUS_UPLOAD_TMP_DIR` controls chunk upload staging.
- `NEXUS_LOG_DIR` controls panel/daemon logs.
- `NEXUS_BIND` and `NEXUS_PORT` control the API listener.

The Linux installer writes these values into `/etc/nexusos/nexusos.env`.

Operational default:

- Service runs as root because VM, backup, libvirt, qemu-img, mount and network
  operations need host-level permissions. Lock down the VPS firewall and use
  the panel IAM/admin roles.

Known production hardening still recommended:

- Put HTTPS in front of nginx using Certbot, Caddy or a cloud load balancer.
- Move persistent JSON state to PostgreSQL before multi-user commercial use.
- Add off-host backups for `/var/lib/libvirt/images` and `/var/lib/nexus`.
- Test every OS preset once on the new hardware before selling/handing it to users.
