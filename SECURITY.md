# Security Policy

NEXUS OS is an infrastructure control panel. Treat every deployed instance as a
privileged system because it can manage files, VM disks, libvirt, networking and
system services.

## Before Publishing A Fork

- Do not commit `app/password.txt`, `app/users.json`, API tokens, rclone tokens,
  Gemini keys, OpenCore files, ISO images, VM disks or backups.
- Keep BYOL media and commercial OS images outside the repository.
- Change all credentials immediately after installation.
- Review `.gitignore` before adding new runtime files.

## Supported Deployment Model

The public repository should contain source code, templates, installers and
documentation only. Runtime state belongs on the target machine under paths such
as `/opt/nexusos`, `/var/lib/nexus`, `/var/lib/libvirt/images` and
`/etc/nexusos`.

## Reporting Issues

Open a private issue or contact the maintainer directly for vulnerabilities.
Do not publish active credentials, public IPs, private SSH keys or VM disk images
inside issue reports.
