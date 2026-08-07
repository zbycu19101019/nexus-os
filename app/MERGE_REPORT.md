# NEXUS merged candidate

Frontend base: `root\nexus_game\nexus2\static\index.html`

Backend base: `tmp\nexus_backup_audit_20260712\extracted\dabb8710cb41__nexus-2026-07-09-2033.tar.gz\server.py`

Changes:

- preserved the NEXUS MASTER layout and all 13 original tabs;
- excluded the separate NEXUS NOC project and public story-game sandbox;
- removed the runtime Admin-page overwrite and duplicate direct-backup button;
- restored authenticated login using the token returned by the backend;
- implemented backup list, restore and delete controls;
- repaired authenticated file downloads;
- retained `/root/backups` as the backup directory in the clean backend;
- data files are intentionally not included and will remain untouched on the VPS.

SHA256:

- `static/index.html`: `ce9c4009a3f64f04c51123fef9940b82fe480fdbe17a75c7f39bd7414b53dfb7`
- `server.py`: `6d2ea30e4a56fc44d6dd1a44d4de55e9b9ac9cc0388cbd17c973a19ab7d00cee`
