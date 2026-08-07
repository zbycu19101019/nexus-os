import os, subprocess, platform, shutil, uuid, datetime, json, hashlib, hmac, secrets, re, mimetypes, html, email.utils, asyncio, socket, zipfile, tarfile, tempfile, configparser, ipaddress, struct, plistlib
import urllib.request, urllib.error, urllib.parse
import signal
import xml.etree.ElementTree as ET
from typing import List
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, Depends, Header, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import psycopg
    from psycopg.rows import dict_row
    HAS_PG = True
except Exception:
    psycopg = None
    dict_row = None
    HAS_PG = False

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError
    ARGON2 = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
    HAS_ARGON2 = True
except Exception:
    ARGON2 = None
    VerifyMismatchError = VerificationError = Exception
    HAS_ARGON2 = False

import uvicorn

app = FastAPI()

# --- ŚCIEŻKI I PLIKI ---
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
PLUGINS_DIR = BASE_DIR / "plugins"
BACKUP_DIR = Path(os.environ.get("NEXUS_BACKUP_DIR", "/var/backups/nexusos"))
SERVER_BACKUP_DIR = BACKUP_DIR / "server-full"
MEDIA_DIR = BASE_DIR / "media"
ISO_DIR = BASE_DIR / "isos"
LIBVIRT_IMAGE_DIR = Path(os.environ.get("NEXUS_LIBVIRT_IMAGE_DIR", "/var/lib/libvirt/images"))
LIBVIRT_ISO_DIR = LIBVIRT_IMAGE_DIR / "nexus-isos"
OPENCORE_OVERLAY_DIR = LIBVIRT_IMAGE_DIR / "nexus-opencore-overlays"
CUPERTINO_MEDIA_OVERLAY_DIR = LIBVIRT_IMAGE_DIR / "nexus-cupertino-media-overlays"
NEXUS_ISO_STORAGE_DIR = Path(os.environ.get("NEXUS_ISO_STORAGE_DIR", "/var/lib/nexus/iso_storage"))
VM_CHUNK_UPLOAD_DIR = Path(os.environ.get("NEXUS_UPLOAD_TMP_DIR", "/var/lib/nexus/upload_tmp"))
DRIVER_DIR = BASE_DIR / "vm_drivers"
DRIVER_EXTRACT_DIR = DRIVER_DIR / "extracted"
VISUAL_DIR = BASE_DIR / "visual_archive"
DROP_DIR = BASE_DIR / "secure_drop"
BBS_UPLOAD_DIR = BASE_DIR / "bbs_uploads"
CONFIG_FILE = BASE_DIR / "config.txt"
PASS_FILE = BASE_DIR / "password.txt"
USERS_FILE = BASE_DIR / "users.json"
LOG_FILE = BASE_DIR / "nexus.log"
COMMUNITY_FILE = BASE_DIR / "community.json"
BBS_FILE = BASE_DIR / "bbs.json"
LOGIN_AUDIT_FILE = BASE_DIR / "login_audit.json"
KANBAN_FILE = BASE_DIR / "kanban.json"
SHARES_FILE = BASE_DIR / "shares.json"
ALERTS_FILE = BASE_DIR / "alerts.json"
VM_PORT_FORWARDS_FILE = BASE_DIR / "vm_port_forwards.json"
VM_ALERTS_CONFIG_FILE = BASE_DIR / "vm_alerts_config.json"
VM_GUEST_AGENTS_FILE = BASE_DIR / "vm_guest_agents.json"
VM_GUEST_TELEMETRY_FILE = BASE_DIR / "vm_guest_telemetry.json"
VM_BILLING_FILE = BASE_DIR / "vm_billing.json"
OBJECTS_FILE = BASE_DIR / "object_storage.json"
OBJECT_TOKENS_FILE = BASE_DIR / "object_tokens.json"
CLOUD_USB_DIR = BASE_DIR / "cloud_usb"
USB_MOUNTS_FILE = BASE_DIR / "usb_mounts.json"
CAPSULE_DIR = BASE_DIR / "capsules"
CAPSULE_UPLOAD_DIR = CAPSULE_DIR / "uploads"
CAPSULE_TEMP_DIR = CAPSULE_DIR / "tmp"
PUSH_SUBS_FILE = BASE_DIR / "push_subscriptions.json"
BRIEFING_FILE = BASE_DIR / "briefing.json"
KARMA_FILE = BASE_DIR / "karma.json"
CRYPTO_PORTFOLIO_FILE = BASE_DIR / "crypto_portfolio.json"
P2P_FILE = BASE_DIR / "p2p_signals.json"
WEB3_FILE = BASE_DIR / "web3_auth.json"
GEMINI_KEY_FILE = BASE_DIR / "gemini_key.txt"
PLUGINS_STATE_FILE = BASE_DIR / "plugins_installed.json"
SHIELD_RULES_FILE = BASE_DIR / "shield_firewall_rules.json"
TIME_MACHINE_FILE = BASE_DIR / "time_machine_policies.json"
CLOUD_INIT_FILE = BASE_DIR / "cloud_init_recipes.json"
API_TOKENS_FILE = BASE_DIR / "api_tokens.json"
WEBHOOKS_FILE = BASE_DIR / "webhooks.json"
COOP_SESSIONS_FILE = BASE_DIR / "coop_sessions.json"
HYPER_SLEEP_DIR = BASE_DIR / "hyper_sleep"
HYPER_SLEEP_FILE = BASE_DIR / "hyper_sleep_states.json"
CANVAS_FILE = BASE_DIR / "nexus_canvas.json"
FORGE_FILE = BASE_DIR / "nexus_forge.json"
AI_COMMANDER_FILE = BASE_DIR / "ai_commander_log.json"
ARCHIVER_JOBS_FILE = BASE_DIR / "archiver_jobs.json"
BASTION_FILE = BASE_DIR / "bastion_targets.json"
WORKERS_FILE = BASE_DIR / "workers.json"
WORKER_RUNS_FILE = BASE_DIR / "worker_runs.json"
VAULT_DIR = BASE_DIR / "vault"
VAULT_FILE = BASE_DIR / "vault_links.json"
GLOBAL_TERMINAL_FILE = BASE_DIR / "global_terminal_log.json"
XOPS_AUDIT_FILE = BASE_DIR / "xops_audit.json"
NEXTGEN_FILE = BASE_DIR / "nextgen_state.json"
VM_CHUNK_UPLOADS_FILE = BASE_DIR / "vm_chunk_uploads.json"
NEXUS_LOG_DIR = Path(os.environ.get("NEXUS_LOG_DIR", "/var/log/nexus"))
PHASE2_POLICY_FILE = BASE_DIR / "phase2_autonomy.json"
PHASE2_TENANTS_FILE = BASE_DIR / "phase2_tenants.json"
PHASE2_NETWORK_RULES_FILE = BASE_DIR / "phase2_network_rules.json"
PHASE2_NANO_RECIPES_FILE = BASE_DIR / "phase2_nano_recipes.json"
PHASE2_FORGE_BUILDS_FILE = BASE_DIR / "phase2_forge_builds.json"
PHASE2_BRANDING_FILE = BASE_DIR / "phase2_branding.json"
EDGE_FUNCTIONS_FILE = BASE_DIR / "edge_functions.json"
EDGE_SECRETS_FILE = BASE_DIR / "edge_secrets.json"
EDGE_RUNS_FILE = BASE_DIR / "edge_runs.json"
STORAGE_RETENTION_FILE = BASE_DIR / "storage_retention.json"
NEURAL_CACHE_FILE = BASE_DIR / "neural_cache.json"
RCLONE_CONFIG_FILE = Path(os.environ.get("RCLONE_CONFIG", "/root/.config/rclone/rclone.conf"))
CLOUD_DRIVE_DEFAULT_REMOTE = "gdrive"
CLOUD_DRIVE_DEFAULT_ROOT = "NEXUS_CORE"
CLOUD_DRIVE_JOBS = {}
VM_CHUNK_UPLOAD_MAX_BYTES = int(os.environ.get("NEXUS_MAX_VM_UPLOAD_BYTES", 80 * 1024 * 1024 * 1024))
TIME_MACHINE_SCHEDULER_STARTED = False
VM_BILLING_SCHEDULER_STARTED = False
COOP_PEERS = {}
VNC_SESSIONS = {}
VNC_SESSION_TTL_SECONDS = 600

for d in [STATIC_DIR, PLUGINS_DIR, BACKUP_DIR, SERVER_BACKUP_DIR, MEDIA_DIR, ISO_DIR, LIBVIRT_ISO_DIR, NEXUS_ISO_STORAGE_DIR, VM_CHUNK_UPLOAD_DIR, DRIVER_DIR, DRIVER_EXTRACT_DIR, VISUAL_DIR, DROP_DIR, BBS_UPLOAD_DIR, CLOUD_USB_DIR, CAPSULE_UPLOAD_DIR, CAPSULE_TEMP_DIR, VAULT_DIR, NEXUS_LOG_DIR]: d.mkdir(parents=True, exist_ok=True)
if not CONFIG_FILE.exists(): CONFIG_FILE.write_text("NEXUS MASTER CONFIG\n")
if not PASS_FILE.exists(): PASS_FILE.write_text("nexus123")
if not LOG_FILE.exists(): LOG_FILE.write_text("--- NEXUS LOG INIT ---\n")
if not COMMUNITY_FILE.exists(): COMMUNITY_FILE.write_text("[]")
if not BBS_FILE.exists(): BBS_FILE.write_text("[]")
if not LOGIN_AUDIT_FILE.exists(): LOGIN_AUDIT_FILE.write_text("[]")
if not KANBAN_FILE.exists(): KANBAN_FILE.write_text(json.dumps({"columns":[{"id":"ideas","title":"POMYSLY","cards":[]},{"id":"doing","title":"W TRAKCIE","cards":[]},{"id":"done","title":"ZROBIONE","cards":[]}]}, ensure_ascii=False, indent=2))
if not SHARES_FILE.exists(): SHARES_FILE.write_text("[]")
if not ALERTS_FILE.exists(): ALERTS_FILE.write_text("[]")
if not VM_PORT_FORWARDS_FILE.exists(): VM_PORT_FORWARDS_FILE.write_text("[]")
if not VM_ALERTS_CONFIG_FILE.exists(): VM_ALERTS_CONFIG_FILE.write_text(json.dumps({"disk_threshold": 90, "webhook_url": ""}, ensure_ascii=False, indent=2))
if not VM_GUEST_AGENTS_FILE.exists(): VM_GUEST_AGENTS_FILE.write_text("{}")
if not VM_GUEST_TELEMETRY_FILE.exists(): VM_GUEST_TELEMETRY_FILE.write_text("{}")
if not VM_BILLING_FILE.exists(): VM_BILLING_FILE.write_text(json.dumps({"enabled": True, "rate_per_hour": 10.0, "wallets": {}, "vm_owners": {}, "runtime": {}, "ledger": []}, ensure_ascii=False, indent=2))
if not OBJECTS_FILE.exists(): OBJECTS_FILE.write_text("[]")
if not OBJECT_TOKENS_FILE.exists(): OBJECT_TOKENS_FILE.write_text("[]")
if not USB_MOUNTS_FILE.exists(): USB_MOUNTS_FILE.write_text("[]")
if not PUSH_SUBS_FILE.exists(): PUSH_SUBS_FILE.write_text("[]")
if not BRIEFING_FILE.exists(): BRIEFING_FILE.write_text("{}")
if not KARMA_FILE.exists(): KARMA_FILE.write_text("{}")
if not CRYPTO_PORTFOLIO_FILE.exists(): CRYPTO_PORTFOLIO_FILE.write_text("{}")
if not P2P_FILE.exists(): P2P_FILE.write_text("{}")
if not WEB3_FILE.exists(): WEB3_FILE.write_text("{}")
if not GEMINI_KEY_FILE.exists(): GEMINI_KEY_FILE.write_text("")
if not PLUGINS_STATE_FILE.exists(): PLUGINS_STATE_FILE.write_text("[]")
if not SHIELD_RULES_FILE.exists(): SHIELD_RULES_FILE.write_text("[]")
if not TIME_MACHINE_FILE.exists(): TIME_MACHINE_FILE.write_text("[]")
if not CLOUD_INIT_FILE.exists(): CLOUD_INIT_FILE.write_text("[]")
if not API_TOKENS_FILE.exists(): API_TOKENS_FILE.write_text("[]")
if not WEBHOOKS_FILE.exists(): WEBHOOKS_FILE.write_text("[]")
if not COOP_SESSIONS_FILE.exists(): COOP_SESSIONS_FILE.write_text("[]")
if not HYPER_SLEEP_FILE.exists(): HYPER_SLEEP_FILE.write_text("[]")
if not CANVAS_FILE.exists(): CANVAS_FILE.write_text("[]")
if not FORGE_FILE.exists(): FORGE_FILE.write_text("[]")
if not AI_COMMANDER_FILE.exists(): AI_COMMANDER_FILE.write_text("[]")
if not ARCHIVER_JOBS_FILE.exists(): ARCHIVER_JOBS_FILE.write_text("[]")
if not BASTION_FILE.exists(): BASTION_FILE.write_text("[]")
if not WORKERS_FILE.exists(): WORKERS_FILE.write_text("[]")
if not WORKER_RUNS_FILE.exists(): WORKER_RUNS_FILE.write_text("[]")
if not VAULT_FILE.exists(): VAULT_FILE.write_text("[]")
if not GLOBAL_TERMINAL_FILE.exists(): GLOBAL_TERMINAL_FILE.write_text("[]")
if not XOPS_AUDIT_FILE.exists(): XOPS_AUDIT_FILE.write_text("[]")
if not VM_CHUNK_UPLOADS_FILE.exists(): VM_CHUNK_UPLOADS_FILE.write_text("{}")
if not PHASE2_POLICY_FILE.exists(): PHASE2_POLICY_FILE.write_text(json.dumps({"enabled": False, "mode": "observe", "dry_run": True, "idle_cpu_threshold": 1.0, "idle_minutes": 30, "auto_suspend": False, "ram_autoscale": False, "ram_grow_threshold": 82.0, "ram_shrink_threshold": 32.0, "ram_step_mb": 512, "ram_min_mb": 512, "ram_cooldown_seconds": 120, "auto_heal": False, "rollback_snapshot": False, "iowait_threshold": 15.0, "disk_threshold": 90.0, "updated_at": datetime.datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False, indent=2))
if not PHASE2_TENANTS_FILE.exists(): PHASE2_TENANTS_FILE.write_text("[]")
if not PHASE2_NETWORK_RULES_FILE.exists(): PHASE2_NETWORK_RULES_FILE.write_text("[]")
if not PHASE2_NANO_RECIPES_FILE.exists(): PHASE2_NANO_RECIPES_FILE.write_text("[]")
if not PHASE2_FORGE_BUILDS_FILE.exists(): PHASE2_FORGE_BUILDS_FILE.write_text("[]")
if not PHASE2_BRANDING_FILE.exists(): PHASE2_BRANDING_FILE.write_text("{}")
if not EDGE_FUNCTIONS_FILE.exists(): EDGE_FUNCTIONS_FILE.write_text("[]")
if not EDGE_SECRETS_FILE.exists(): EDGE_SECRETS_FILE.write_text("{}")
if not EDGE_RUNS_FILE.exists(): EDGE_RUNS_FILE.write_text("[]")
if not STORAGE_RETENTION_FILE.exists(): STORAGE_RETENTION_FILE.write_text("[]")
if not NEURAL_CACHE_FILE.exists(): NEURAL_CACHE_FILE.write_text("{}")

def log_event(msg: str):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f: f.write(f"[{now}] {msg}\n")

AUTH_TOKEN = "NEXUS_SECURE_ROOT_SESSION_TOKEN"
def verify_bootstrap_token(x_auth_token: str = Header(None)):
    if x_auth_token != AUTH_TOKEN: raise HTTPException(status_code=401, detail="Odmowa dostępu")

terminal_cwd = BASE_DIR
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class TextInput(BaseModel): text: str = Field(..., min_length=1, max_length=100)
class FileContent(BaseModel): path: str; content: str
class CommandRequest(BaseModel): command: str
class LoginRequest(BaseModel): username: str = Field("admin", min_length=1, max_length=32); password: str
class RegisterRequest(BaseModel): username: str = Field(..., min_length=3, max_length=32); password: str = Field(..., min_length=8, max_length=128)
class KillRequest(BaseModel): pid: int; signal: str = Field("term", max_length=8)
class ChatMessage(BaseModel): author: str = Field(..., max_length=20); text: str = Field(..., max_length=200)
class UserCreateRequest(BaseModel): username: str = Field(..., min_length=3, max_length=32); password: str = Field(..., min_length=4, max_length=128); role: str = Field("user", max_length=16)
class UserPasswordRequest(BaseModel): username: str = Field(..., min_length=1, max_length=32); password: str = Field(..., min_length=4, max_length=128)
class UserRoleRequest(BaseModel): role: str = Field(..., min_length=4, max_length=16)
class ApplianceModeRequest(BaseModel): mode: str = Field(..., min_length=4, max_length=16); dry_run: bool = False

class StorageItem(BaseModel):
    name: str = Field("disk.qcow2", min_length=1, max_length=160)
    path: str = Field("disk.qcow2", min_length=1, max_length=240)
    format: str = Field("qcow2", max_length=16)
    size_bytes: int = Field(0, ge=0)
    bus: str = Field("virtio", max_length=16)
    boot: bool = True
    sha256: str = Field("", max_length=128)

class CapsuleManifest(BaseModel):
    schema_version: str = Field("1", max_length=16)
    capsule_id: str = Field("", max_length=80)
    name: str = Field(..., min_length=3, max_length=80)
    display_name: str = Field("", max_length=120)
    description: str = Field("", max_length=500)
    architecture: str = Field("x86_64", max_length=32)
    os_id: str = Field("generic", max_length=64)
    memory_mb: int = Field(1024, ge=256, le=262144)
    vcpus: int = Field(1, ge=1, le=128)
    network_bridge: str = Field("nexus-default", max_length=64)
    thumbnail_path: str = Field("thumbnail.jpg", max_length=240)
    storage: List[StorageItem] = Field(default_factory=lambda: [StorageItem()])
    start_after_import: bool = False

class InspectResponse(BaseModel):
    valid: bool
    capsule_id: str
    required_bytes: int
    available_bytes: int
    fits: bool
    warnings: List[str] = Field(default_factory=list)
    normalized_manifest: dict = Field(default_factory=dict)

class UploadInitRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=180)
    size: int = Field(..., ge=1)
    sha256: str = Field("", max_length=128)
    manifest: dict = Field(default_factory=dict)

class UploadCompleteRequest(BaseModel):
    parts: List[int] = Field(default_factory=list)
    sha256: str = Field("", max_length=128)

class VMChunkUploadInitRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=240)
    size: int = Field(..., ge=1, le=VM_CHUNK_UPLOAD_MAX_BYTES)
    sha256: str = Field("", max_length=128)
    purpose: str = Field("auto", max_length=32)
    chunk_size: int = Field(5 * 1024 * 1024, ge=1024 * 1024, le=64 * 1024 * 1024)
    overwrite: bool = False

class VMChunkUploadCompleteRequest(BaseModel):
    upload_id: str = Field(..., min_length=6, max_length=80)
    sha256: str = Field("", max_length=128)

class VMChunkUploadCancelRequest(BaseModel):
    upload_id: str = Field(..., min_length=6, max_length=80)

SESSIONS = {}
LOGIN_ATTEMPTS = {}
CAPSULE_UPLOADS = {}
CAPSULE_JOBS = {}
VM_CHUNK_UPLOAD_LOCK = asyncio.Lock()
DATABASE_URL = os.environ.get("NEXUS_DATABASE_URL", "").strip()
SESSION_SECRET = os.environ.get("NEXUS_SESSION_SECRET", secrets.token_hex(48))
ACCOUNT_STATUSES = {"pending", "active", "suspended", "rejected", "deleted"}
ACCOUNT_ROLES = {"admin", "operator", "viewer", "user"}
IAM_DB_INIT_ATTEMPTED = False
IAM_DB_AVAILABLE = False
IAM_DB_ERROR_LOGGED = False

def hash_password(password: str, salt: str = None):
    if salt is None and HAS_ARGON2:
        return ARGON2.hash(password)
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
    return f"pbkdf2_sha256${salt}${digest}"

def verify_password(password: str, stored: str):
    if stored.startswith("$argon2") and HAS_ARGON2:
        try:
            return ARGON2.verify(stored, password)
        except (VerifyMismatchError, VerificationError, Exception):
            return False
    try:
        method, salt, digest = stored.split("$", 2)
        if method != "pbkdf2_sha256":
            return False
        return hmac.compare_digest(hash_password(password, salt).split("$", 2)[2], digest)
    except Exception:
        return False

def password_needs_upgrade(stored: str):
    if not stored:
        return True
    if stored.startswith("$argon2") and HAS_ARGON2:
        try:
            return bool(ARGON2.check_needs_rehash(stored))
        except Exception:
            return False
    return HAS_ARGON2

def normalize_status(value: str, default: str = "active"):
    status = (value or default).strip().lower()
    return status if status in ACCOUNT_STATUSES else default

def normalize_role(value: str):
    role = (value or "user").strip().lower()
    aliases = {
        "administrator": "admin",
        "ops": "operator",
        "operator": "operator",
        "viewer": "viewer",
        "view": "viewer",
        "readonly": "viewer",
        "read-only": "viewer",
        "user": "user",
    }
    role = aliases.get(role, role)
    return role if role in ACCOUNT_ROLES else "user"

def db_status(value: str):
    return normalize_status(value).upper()

def db_role(value: str):
    return normalize_role(value).upper()

def iso_value(value):
    if isinstance(value, datetime.datetime):
        if value.tzinfo:
            value = value.astimezone()
        return value.isoformat(timespec="seconds")
    return str(value or "")

def _default_users_json():
    password = PASS_FILE.read_text().strip() if PASS_FILE.exists() else "nexus123"
    return {"admin": {
        "username": "admin",
        "role": "admin",
        "status": "active",
        "password_hash": hash_password(password),
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }}

def _save_users_json(users):
    tmp = USERS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(USERS_FILE)

def _load_users_json():
    if not USERS_FILE.exists():
        users = _default_users_json()
        _save_users_json(users)
        return users
    try:
        data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "admin" not in data:
            data.update(_default_users_json())
            _save_users_json(data)
        return data if isinstance(data, dict) else {}
    except Exception:
        shutil.copy2(USERS_FILE, USERS_FILE.with_suffix(".json.bak"))
        users = _default_users_json()
        _save_users_json(users)
        return users

def iam_db_configured():
    return HAS_PG and bool(DATABASE_URL) and os.environ.get("NEXUS_IAM_DB", "1") != "0"

def db_connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=True)

def token_hash(token: str):
    return hmac.new(SESSION_SECRET.encode("utf-8"), (token or "").encode("utf-8"), hashlib.sha256).hexdigest()

def _legacy_user_from_db(row):
    return {
        "id": row.get("id", ""),
        "username": row.get("username", ""),
        "role": normalize_role(row.get("role", "USER")),
        "status": normalize_status(row.get("status", "ACTIVE")),
        "password_hash": row.get("password_hash", ""),
        "created_at": iso_value(row.get("created_at")),
        "updated_at": iso_value(row.get("updated_at")),
        "approved_at": iso_value(row.get("approved_at")),
        "approved_by": row.get("approved_by") or "",
        "last_login_at": iso_value(row.get("last_login_at")),
        "password_changed_at": iso_value(row.get("password_changed_at")),
    }

def _iam_insert_migrated_user_raw(conn, username, data):
    clean = (username or data.get("username") or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9_.-]{3,32}", clean):
        return
    role = db_role(data.get("role", "admin" if clean == "admin" else "user"))
    status = db_status(data.get("status", "active"))
    created_at = data.get("created_at") or datetime.datetime.now().isoformat(timespec="seconds")
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO iam_users (id, username, password_hash, role, status, created_at, updated_at, approved_at, approved_by)
            VALUES (%s, %s, %s, %s, %s, %s, now(), CASE WHEN %s='ACTIVE' THEN now() ELSE NULL END, CASE WHEN %s='ACTIVE' THEN 'migration' ELSE NULL END)
            ON CONFLICT (username) DO NOTHING
        """, (data.get("id") or str(uuid.uuid4()), clean, data.get("password_hash") or hash_password(secrets.token_urlsafe(18)), role, status, created_at, status, status))

def ensure_iam_db():
    global IAM_DB_INIT_ATTEMPTED, IAM_DB_AVAILABLE, IAM_DB_ERROR_LOGGED
    if IAM_DB_INIT_ATTEMPTED:
        return IAM_DB_AVAILABLE
    IAM_DB_INIT_ATTEMPTED = True
    if not iam_db_configured():
        return False
    try:
        with db_connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS iam_users (
                        id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'USER' CHECK (role IN ('ADMIN','OPERATOR','VIEWER','USER')),
                        status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','ACTIVE','SUSPENDED','REJECTED','DELETED')),
                        token_version INTEGER NOT NULL DEFAULT 1,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        approved_at TIMESTAMPTZ,
                        approved_by TEXT,
                        rejected_at TIMESTAMPTZ,
                        rejected_by TEXT,
                        suspended_at TIMESTAMPTZ,
                        suspended_by TEXT,
                        last_login_at TIMESTAMPTZ,
                        password_changed_at TIMESTAMPTZ,
                        meta JSONB NOT NULL DEFAULT '{}'::jsonb
                    )
                """)
                cur.execute("ALTER TABLE iam_users DROP CONSTRAINT IF EXISTS iam_users_role_check")
                cur.execute("ALTER TABLE iam_users ADD CONSTRAINT iam_users_role_check CHECK (role IN ('ADMIN','OPERATOR','VIEWER','USER'))")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS iam_sessions (
                        id TEXT PRIMARY KEY,
                        token_hash TEXT UNIQUE NOT NULL,
                        refresh_hash TEXT,
                        username TEXT NOT NULL REFERENCES iam_users(username) ON DELETE CASCADE,
                        role TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        last_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
                        expires_at TIMESTAMPTZ NOT NULL,
                        revoked_at TIMESTAMPTZ,
                        ip TEXT,
                        user_agent TEXT
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id BIGSERIAL PRIMARY KEY,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        actor TEXT,
                        action TEXT NOT NULL,
                        target TEXT,
                        status TEXT NOT NULL,
                        ip TEXT,
                        user_agent TEXT,
                        meta JSONB NOT NULL DEFAULT '{}'::jsonb
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_iam_users_status ON iam_users(status)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_iam_sessions_username ON iam_sessions(username)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC)")
            for username, data in _load_users_json().items():
                _iam_insert_migrated_user_raw(conn, username, data)
        IAM_DB_AVAILABLE = True
        return True
    except Exception as exc:
        IAM_DB_AVAILABLE = False
        if not IAM_DB_ERROR_LOGGED:
            IAM_DB_ERROR_LOGGED = True
            log_event(f"IAM DB disabled: {exc}")
        return False

def iam_upsert_user(username, data):
    if not ensure_iam_db():
        return False
    try:
        with db_connect() as conn, conn.cursor() as cur:
            status = db_status(data.get("status", "active"))
            role = db_role(data.get("role", "user"))
            cur.execute("""
                INSERT INTO iam_users (id, username, password_hash, role, status, created_at, updated_at, approved_at, approved_by, password_changed_at)
                VALUES (%s, %s, %s, %s, %s, COALESCE(%s::timestamptz, now()), now(), CASE WHEN %s='ACTIVE' THEN now() ELSE NULL END, CASE WHEN %s='ACTIVE' THEN %s ELSE NULL END, %s::timestamptz)
                ON CONFLICT (username) DO UPDATE SET
                    password_hash=EXCLUDED.password_hash,
                    role=EXCLUDED.role,
                    status=EXCLUDED.status,
                    updated_at=now(),
                    approved_at=COALESCE(iam_users.approved_at, EXCLUDED.approved_at),
                    approved_by=COALESCE(iam_users.approved_by, EXCLUDED.approved_by),
                    password_changed_at=COALESCE(EXCLUDED.password_changed_at, iam_users.password_changed_at)
            """, (
                data.get("id") or str(uuid.uuid4()), username, data.get("password_hash") or hash_password(secrets.token_urlsafe(18)),
                role, status, data.get("created_at") or None, status, status, data.get("approved_by") or "system",
                data.get("password_changed_at") or None,
            ))
        return True
    except Exception as exc:
        log_event(f"IAM UPSERT ERROR {username}: {exc}")
        return False

def db_fetch_users():
    if not ensure_iam_db():
        return None
    try:
        with db_connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM iam_users WHERE status <> 'DELETED' ORDER BY username")
            return {row["username"]: _legacy_user_from_db(row) for row in cur.fetchall()}
    except Exception as exc:
        log_event(f"IAM USERS FETCH ERROR: {exc}")
        return None

def save_users(users):
    _save_users_json(users)
    if ensure_iam_db():
        for username, data in users.items():
            try:
                iam_upsert_user(normalize_username(username), data)
            except Exception:
                continue

def load_users():
    users = db_fetch_users()
    if users is not None:
        return users
    return _load_users_json()

def normalize_username(username: str):
    clean = (username or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9_.-]{3,32}", clean):
        raise HTTPException(status_code=400, detail="Niepoprawna nazwa uzytkownika")
    return clean

def public_user(username, data):
    return {
        "id": data.get("id", ""),
        "username": username,
        "role": normalize_role(data.get("role", "user")),
        "status": normalize_status(data.get("status", "active")),
        "created_at": data.get("created_at", ""),
        "approved_at": data.get("approved_at", ""),
        "approved_by": data.get("approved_by", ""),
        "last_login_at": data.get("last_login_at", ""),
        "password_changed_at": data.get("password_changed_at", ""),
    }

def sync_session_user(session):
    try:
        username = session.get("username", "")
        data = load_users().get(username)
        if not data:
            session["status"] = "deleted"
            return session
        session["role"] = normalize_role(data.get("role", session.get("role", "user")))
        session["status"] = normalize_status(data.get("status", session.get("status", "active")))
    except Exception:
        session["status"] = normalize_status(session.get("status", "active"))
    return session

def db_store_session(token, refresh_token, session, request: Request):
    if not ensure_iam_db():
        return
    try:
        with db_connect() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO iam_sessions (id, token_hash, refresh_hash, username, role, status, expires_at, ip, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, now() + interval '30 days', %s, %s)
                ON CONFLICT (token_hash) DO UPDATE SET last_seen=now(), status=EXCLUDED.status, role=EXCLUDED.role
            """, (
                str(uuid.uuid4()), token_hash(token), token_hash(refresh_token) if refresh_token else None,
                session.get("username", ""), db_role(session.get("role", "user")), db_status(session.get("status", "active")),
                request_ip(request), (request.headers.get("user-agent") or "")[:220],
            ))
    except Exception as exc:
        log_event(f"IAM SESSION STORE ERROR: {exc}")

def db_touch_session(token):
    if not token or not ensure_iam_db():
        return
    try:
        with db_connect() as conn, conn.cursor() as cur:
            cur.execute("UPDATE iam_sessions SET last_seen=now() WHERE token_hash=%s AND revoked_at IS NULL", (token_hash(token),))
    except Exception:
        pass

def db_revoke_session(token):
    if not token or not ensure_iam_db():
        return
    try:
        with db_connect() as conn, conn.cursor() as cur:
            cur.execute("UPDATE iam_sessions SET revoked_at=now() WHERE token_hash=%s AND revoked_at IS NULL", (token_hash(token),))
    except Exception:
        pass

def db_revoke_user_sessions(username):
    for token, session in list(SESSIONS.items()):
        if session.get("username") == username:
            SESSIONS.pop(token, None)
    if not ensure_iam_db():
        return
    try:
        with db_connect() as conn, conn.cursor() as cur:
            cur.execute("UPDATE iam_sessions SET revoked_at=now() WHERE username=%s AND revoked_at IS NULL", (username,))
    except Exception:
        pass

def db_find_refresh_session(refresh_token):
    if not refresh_token or not ensure_iam_db():
        return None
    try:
        with db_connect() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT s.username, s.role, s.status
                FROM iam_sessions s
                WHERE s.refresh_hash=%s AND s.revoked_at IS NULL AND s.expires_at > now()
                ORDER BY s.last_seen DESC LIMIT 1
            """, (token_hash(refresh_token),))
            return cur.fetchone()
    except Exception:
        return None

def db_mark_login(username):
    if not ensure_iam_db():
        return
    try:
        with db_connect() as conn, conn.cursor() as cur:
            cur.execute("UPDATE iam_users SET last_login_at=now(), updated_at=now() WHERE username=%s", (username,))
    except Exception:
        pass

def audit_event(actor, action, target="", status="OK", request: Request = None, meta=None):
    if not ensure_iam_db():
        return
    try:
        with db_connect() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO audit_log (actor, action, target, status, ip, user_agent, meta)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
            """, (
                actor or "", action, target or "", status,
                request_ip(request) if request else "",
                ((request.headers.get("user-agent") or "")[:220] if request else ""),
                json.dumps(meta or {}, ensure_ascii=False),
            ))
    except Exception as exc:
        log_event(f"AUDIT DB ERROR: {exc}")

def db_fetch_audit(limit=120, login_only=False):
    if not ensure_iam_db():
        return None
    try:
        with db_connect() as conn, conn.cursor() as cur:
            if login_only:
                cur.execute("""
                    SELECT created_at, actor, action, target, status, ip, user_agent, meta
                    FROM audit_log
                    WHERE action LIKE 'auth.%'
                    ORDER BY created_at DESC LIMIT %s
                """, (limit,))
            else:
                cur.execute("""
                    SELECT created_at, actor, action, target, status, ip, user_agent, meta
                    FROM audit_log
                    ORDER BY created_at DESC LIMIT %s
                """, (limit,))
            rows = []
            for row in cur.fetchall():
                rows.append({
                    "time": iso_value(row.get("created_at")),
                    "username": row.get("actor") or row.get("target") or "",
                    "actor": row.get("actor") or "",
                    "action": row.get("action") or "",
                    "target": row.get("target") or "",
                    "status": row.get("status") or "",
                    "ip": row.get("ip") or "",
                    "user_agent": row.get("user_agent") or "",
                    "meta": row.get("meta") or {},
                })
            return rows
    except Exception as exc:
        log_event(f"AUDIT FETCH ERROR: {exc}")
        return None

def check_login_rate_limit(username, request: Request):
    key = f"{request_ip(request)}:{username}"
    entry = LOGIN_ATTEMPTS.get(key, {"count": 0, "first": 0, "locked_until": 0})
    now = datetime.datetime.now().timestamp()
    if entry.get("locked_until", 0) > now:
        raise HTTPException(status_code=429, detail="Za duzo prob logowania. Poczekaj chwile.")

def record_login_failure(username, request: Request):
    key = f"{request_ip(request)}:{username}"
    now = datetime.datetime.now().timestamp()
    entry = LOGIN_ATTEMPTS.get(key, {"count": 0, "first": now, "locked_until": 0})
    if now - entry.get("first", now) > 900:
        entry = {"count": 0, "first": now, "locked_until": 0}
    entry["count"] = int(entry.get("count", 0)) + 1
    if entry["count"] >= 5:
        entry["locked_until"] = now + 300
    LOGIN_ATTEMPTS[key] = entry

def record_login_success(username, request: Request):
    LOGIN_ATTEMPTS.pop(f"{request_ip(request)}:{username}", None)

def verify_session(x_auth_token: str = Header(None)):
    user = SESSIONS.get(x_auth_token or "")
    if not user:
        raise HTTPException(status_code=401, detail="Odmowa dostepu")
    user = sync_session_user(user)
    user["last_seen"] = datetime.datetime.now().isoformat(timespec="seconds")
    db_touch_session(x_auth_token or "")
    return user

def verify_token(user = Depends(verify_session)):
    if normalize_status(user.get("status", "active")) != "active":
        raise HTTPException(status_code=403, detail={"error": "account_not_active", "account_status": normalize_status(user.get("status"))})
    return user

def verify_admin(user = Depends(verify_token)):
    if normalize_role(user.get("role")) != "admin":
        raise HTTPException(status_code=403, detail="Wymagane konto admin")
    return user
class BBSCommentRequest(BaseModel): post_id: str; text: str = Field(..., min_length=1, max_length=800)
class BBSRepRequest(BaseModel): post_id: str
class KanbanStateRequest(BaseModel): columns: list
class KanbanCardRequest(BaseModel): column_id: str; title: str = Field(..., min_length=1, max_length=120); body: str = Field("", max_length=1000)
class DropShareRequest(BaseModel): path: str; title: str = Field("", max_length=120)
class PresenceHeartbeatRequest(BaseModel): device_id: str = Field(..., min_length=1, max_length=80); label: str = Field("", max_length=120)
class AlertRequest(BaseModel): title: str = Field(..., min_length=1, max_length=120); body: str = Field("", max_length=500); level: str = Field("info", max_length=20)
class PushSubscriptionRequest(BaseModel): subscription: dict = Field(default_factory=dict)
class P2PSignalRequest(BaseModel): room: str = Field(..., min_length=1, max_length=80); peer: str = Field(..., min_length=1, max_length=80); payload: dict = Field(default_factory=dict)
class Web3NonceRequest(BaseModel): address: str = Field(..., min_length=6, max_length=80)
class Web3VerifyRequest(BaseModel): address: str = Field(..., min_length=6, max_length=80); signature: str = Field(..., min_length=10, max_length=500)
class VMActionRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    action: str = Field(..., min_length=1, max_length=20)
    backend: str = Field("auto", max_length=20)
    confirm: str = Field("", max_length=120)
    reason: str = Field("", max_length=240)
    legal_byol_ack: bool = False
    bootloader: str = Field("", max_length=500)
    iso_path: str = Field("", max_length=500)
class VMStartRequest(BaseModel):
    vm_name: str = Field("", max_length=80)
    vm_id: str = Field("", max_length=80)
    backend: str = Field("auto", max_length=20)
    legal_byol_ack: bool = False
    bootloader: str = Field("", max_length=500)
    iso_path: str = Field("", max_length=500)
    ovmf_code_path: str = Field("", max_length=500)
    ovmf_vars_path: str = Field("", max_length=500)
class VMConsoleRequest(BaseModel): vm_id: str = Field(..., min_length=1, max_length=80); backend: str = Field("auto", max_length=20)
class VMSnapshotRequest(BaseModel): vm_id: str = Field(..., min_length=1, max_length=80); name: str = Field("", max_length=80); description: str = Field("", max_length=240)
class VMSnapshotActionRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    snapshot: str = Field(..., min_length=1, max_length=80)
    confirm: str = Field("", max_length=120)
class VMConfigRequest(BaseModel): vm_id: str = Field(..., min_length=1, max_length=80); memory_mb: int = Field(..., ge=128, le=262144); vcpus: int = Field(..., ge=1, le=32); live: bool = True; config: bool = True
class VMRamUpdateRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    memory_mb: int = Field(..., ge=128, le=262144)
    live: bool = True
    config: bool = True
class VMIsoAttachRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    iso_path: str = Field(..., min_length=1, max_length=500)
    target: str = Field("", max_length=16)
    force: bool = True
    live: bool = True
    config: bool = True
class VMIsoEjectRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    target: str = Field("", max_length=16)
    force: bool = True
    live: bool = True
    config: bool = True
class VMDiskAttachRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    disk_path: str = Field(..., min_length=1, max_length=500)
    bus: str = Field("ide", max_length=16)
    target: str = Field("", max_length=16)
    readonly: bool = False
    live: bool = True
    config: bool = True
class VMStorageThinRequest(BaseModel):
    vm_id: str = Field("", max_length=80)
    path: str = Field("", max_length=700)
class VMStorageCompactRequest(BaseModel):
    vm_id: str = Field("", max_length=80)
    path: str = Field("", max_length=700)
    output_path: str = Field("", max_length=700)
    dry_run: bool = True
    confirm: str = Field("", max_length=80)
class VMNetworkRequest(BaseModel): vm_id: str = Field(..., min_length=1, max_length=80); enabled: bool = True; network: str = Field("default", max_length=64); model: str = Field("virtio", max_length=32); live: bool = True; config: bool = True
class VMInputRepairRequest(BaseModel): vm_id: str = Field(..., min_length=1, max_length=80); backend: str = Field("auto", max_length=20); live: bool = True; config: bool = True
class VMMediaRepairRequest(BaseModel): vm_id: str = Field(..., min_length=1, max_length=80); live: bool = True; config: bool = True
class VMMediaRepairAllRequest(BaseModel): live: bool = True; config: bool = True
class VMCompatibilityRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    profile: str = Field("win95", max_length=32)
    restart: bool = True
    network: str = Field("safe", max_length=32)
class VMDoctorFixRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    profile: str = Field("", max_length=32)
    restart: bool = True
    fix_input: bool = True
class VMDeleteRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    backend: str = Field("auto", max_length=20)
    remove_storage: bool = False
    confirm: str = Field("", max_length=120)
    reason: str = Field("", max_length=240)
class VMPortForwardRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    vm_port: int = Field(..., ge=1, le=65535)
    host_port: int = Field(..., ge=1, le=65535)
    proto: str = Field("tcp", max_length=8)
    guest_ip: str = Field("", max_length=64)
class VMPortForwardDeleteRequest(BaseModel): id: str = Field(..., min_length=1, max_length=64)
class VMAlertConfigRequest(BaseModel): disk_threshold: int = Field(90, ge=50, le=99); webhook_url: str = Field("", max_length=500)
class VMBillingCreditRequest(BaseModel): username: str = Field("admin", min_length=3, max_length=32); amount: float = Field(..., gt=0, le=1000000); note: str = Field("", max_length=180)
class VMBillingRateRequest(BaseModel): rate_per_hour: float = Field(..., ge=0, le=100000)
class VMBillingPolicyRequest(BaseModel):
    enabled: bool = True
    rate_per_hour: float = Field(10.0, ge=0, le=100000)
    tick_seconds: int = Field(60, ge=10, le=3600)
    paused_multiplier: float = Field(0.25, ge=0, le=1)
    suspended_multiplier: float = Field(0.0, ge=0, le=1)
    stopped_multiplier: float = Field(0.0, ge=0, le=1)
    storage_rate_per_gb_hour: float = Field(0.0, ge=0, le=1000)
    storage_billing_basis: str = Field("actual", max_length=16)
    empty_balance_action: str = Field("shutdown", max_length=32)
    hard_kill_after_minutes: int = Field(0, ge=0, le=10080)
    note: str = Field("", max_length=240)
class VMBillingTickRequest(BaseModel):
    dry_run: bool = False
    confirm: str = Field("", max_length=80)
class VMAccessGrantRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    vm_id: str = Field(..., min_length=1, max_length=80)
    permissions: List[str] = Field(default_factory=list)
    expires_minutes: int = Field(0, ge=0, le=525600)
    max_vcpus: int = Field(0, ge=0, le=128)
    max_memory_mb: int = Field(0, ge=0, le=262144)
    max_running_vms: int = Field(0, ge=0, le=100)
    note: str = Field("", max_length=240)
class VMAccessRevokeRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    vm_id: str = Field(..., min_length=1, max_length=80)
    reason: str = Field("", max_length=240)
    revoke_sessions: bool = True
class VMDriverExtractRequest(BaseModel): path: str = Field(..., min_length=1, max_length=500)
class VMGuestAgentRequest(BaseModel): vm_id: str = Field(..., min_length=1, max_length=80)
class CloudDriveConfigRequest(BaseModel):
    remote: str = Field("gdrive", min_length=1, max_length=40)
    token_json: str = Field(..., min_length=20, max_length=12000)
    root_folder: str = Field("NEXUS_CORE", max_length=160)
class CloudDriveSyncRequest(BaseModel):
    source: str = Field(..., min_length=1, max_length=40)
    remote: str = Field("gdrive", max_length=40)
    root_folder: str = Field("NEXUS_CORE", max_length=160)
    mode: str = Field("copy", max_length=12)
class CloudDrivePushRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=1000)
    remote: str = Field("gdrive", max_length=40)
    root_folder: str = Field("NEXUS_CORE", max_length=160)
    dest_folder: str = Field("server-files", max_length=240)
    mode: str = Field("copy", max_length=12)
class ShieldFirewallRuleRequest(BaseModel):
    action: str = Field("block", max_length=12)
    source: str = Field(..., min_length=1, max_length=80)
    proto: str = Field("all", max_length=8)
    port: int = Field(0, ge=0, le=65535)
    note: str = Field("", max_length=180)
    apply: bool = True
class ShieldRuleDeleteRequest(BaseModel): id: str = Field(..., min_length=1, max_length=64); remove_system: bool = True
class TimeMachinePolicyRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    label: str = Field("auto", max_length=60)
    hour: str = Field("03:00", max_length=5)
    max_keep: int = Field(3, ge=1, le=30)
    enabled: bool = True
class TimeMachineRunRequest(BaseModel): id: str = Field(..., min_length=1, max_length=64)
class CloudInitRecipeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    kind: str = Field("bash", max_length=20)
    body: str = Field(..., min_length=1, max_length=12000)
    ssh_key: str = Field("", max_length=4000)
class CloudInitApplyRequest(BaseModel): recipe_id: str = Field(..., min_length=1, max_length=64); vm_id: str = Field(..., min_length=1, max_length=80)
class ApiTokenCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    scopes: List[str] = Field(default_factory=list)
    vm_id: str = Field("", max_length=80)
    days: int = Field(30, ge=1, le=3650)
class ApiTokenRevokeRequest(BaseModel): id: str = Field(..., min_length=1, max_length=64)
class WebhookCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    url: str = Field(..., min_length=8, max_length=600)
    events: List[str] = Field(default_factory=list)
    enabled: bool = True
class WebhookDeleteRequest(BaseModel): id: str = Field(..., min_length=1, max_length=64)
class CoopSessionRequest(BaseModel): vm_id: str = Field(..., min_length=1, max_length=80); role: str = Field("control", max_length=20); minutes: int = Field(120, ge=5, le=10080)
class HyperSleepRequest(BaseModel): vm_id: str = Field(..., min_length=1, max_length=80); label: str = Field("", max_length=80)
class HyperWakeRequest(BaseModel): id: str = Field(..., min_length=1, max_length=64)
class CanvasSaveRequest(BaseModel): name: str = Field("topology", max_length=80); nodes: list = Field(default_factory=list); edges: list = Field(default_factory=list)
class CanvasDeployRequest(BaseModel): id: str = Field(..., min_length=1, max_length=64)
class ForgePublishRequest(BaseModel): vm_id: str = Field(..., min_length=1, max_length=80); name: str = Field(..., min_length=1, max_length=120); description: str = Field("", max_length=500); price: float = Field(0, ge=0, le=1000000)
class ForgeBuyRequest(BaseModel): id: str = Field(..., min_length=1, max_length=64); name: str = Field(..., min_length=3, max_length=64)
class AiCommanderRequest(BaseModel): command: str = Field(..., min_length=2, max_length=1000); execute: bool = True
class ArchiverListRequest(BaseModel): path: str = Field(..., min_length=1, max_length=600)
class ArchiverExtractRequest(BaseModel): path: str = Field(..., min_length=1, max_length=600); member: str = Field(..., min_length=1, max_length=600); dest: str = Field("drop", max_length=80)
class ArchiverZipRequest(BaseModel): paths: list = Field(default_factory=list); output_name: str = Field("nexus-pack.zip", max_length=180)
class ArchiverIsoRequest(BaseModel): paths: list = Field(default_factory=list); output_name: str = Field("nexus-pack.iso", max_length=180)
class BastionTargetRequest(BaseModel): name: str = Field(..., min_length=1, max_length=120); kind: str = Field("rdp", max_length=20); host: str = Field(..., min_length=1, max_length=180); port: int = Field(3389, ge=1, le=65535); username: str = Field("", max_length=80); note: str = Field("", max_length=300)
class BastionDeleteRequest(BaseModel): id: str = Field(..., min_length=1, max_length=64)
class WorkerSaveRequest(BaseModel): name: str = Field(..., min_length=1, max_length=120); runtime: str = Field("python", max_length=20); code: str = Field(..., min_length=1, max_length=20000)
class WorkerRunRequest(BaseModel): id: str = Field("", max_length=64); runtime: str = Field("python", max_length=20); code: str = Field("", max_length=20000); timeout: int = Field(8, ge=1, le=30)
class VaultLinkRequest(BaseModel): path: str = Field(..., min_length=1, max_length=600); title: str = Field("", max_length=120); max_views: int = Field(1, ge=1, le=100); ttl_minutes: int = Field(1440, ge=1, le=43200); destroy_after_read: bool = True
class VaultDeleteRequest(BaseModel): id: str = Field(..., min_length=1, max_length=64)
class GlobalTerminalCommandRequest(BaseModel): command: str = Field(..., min_length=1, max_length=1000)
class XOpsPlanRequest(BaseModel):
    vm_id: str = Field("", max_length=80)
    profile: str = Field("balanced", max_length=40)
    features: List[str] = Field(default_factory=list)
    memory_mb: int = Field(0, ge=0, le=262144)
    vcpus: int = Field(0, ge=0, le=256)
class XOpsBalloonRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    memory_mb: int = Field(..., ge=128, le=262144)
    live: bool = True
    config: bool = False
class XOpsWatchdogRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    action: str = Field("reset", max_length=20)
    live: bool = True
    config: bool = True
class XOpsQoSRequest(BaseModel):
    vm_id: str = Field("", max_length=80)
    iface: str = Field("", max_length=64)
    rate_mbit: int = Field(10, ge=1, le=10000)
    apply: bool = False
class XOpsPcapRequest(BaseModel):
    vm_id: str = Field("", max_length=80)
    iface: str = Field("", max_length=64)
    packets: int = Field(25, ge=1, le=250)
    seconds: int = Field(8, ge=1, le=30)
class XOpsDiskRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=700)
class XOpsShrinkRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=700)
    output_path: str = Field("", max_length=700)
    dry_run: bool = True
class XOpsForensicsRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    output_path: str = Field("", max_length=700)
    dry_run: bool = True
class NextGenPolicyRequest(BaseModel):
    mode: str = Field("observe", max_length=32)
    spot_enabled: bool = False
    ksm_watch: bool = True
    visual_intensity: int = Field(60, ge=0, le=100)
    note: str = Field("", max_length=300)
class Phase2AutonomyPolicyRequest(BaseModel):
    enabled: bool = False
    mode: str = Field("observe", max_length=32)
    dry_run: bool = True
    idle_cpu_threshold: float = Field(1.0, ge=0, le=100)
    idle_minutes: int = Field(30, ge=1, le=10080)
    auto_suspend: bool = False
    ram_autoscale: bool = False
    ram_grow_threshold: float = Field(82.0, ge=40, le=99)
    ram_shrink_threshold: float = Field(32.0, ge=1, le=80)
    ram_step_mb: int = Field(512, ge=128, le=8192)
    ram_min_mb: int = Field(512, ge=128, le=65536)
    ram_cooldown_seconds: int = Field(120, ge=10, le=3600)
    auto_heal: bool = False
    rollback_snapshot: bool = False
    iowait_threshold: float = Field(15.0, ge=1, le=99)
    disk_threshold: float = Field(90.0, ge=50, le=99)
    confirm: str = Field("", max_length=80)
class Phase2TenantRequest(BaseModel):
    tenant_id: str = Field(..., min_length=2, max_length=64)
    name: str = Field("", max_length=120)
    owner: str = Field("admin", max_length=32)
    cidr: str = Field("10.90.0.0/24", max_length=64)
    vxlan_id: int = Field(0, ge=0, le=16777215)
    quota_vcpus: int = Field(4, ge=1, le=1024)
    quota_memory_gb: int = Field(8, ge=1, le=4096)
    quota_storage_gb: int = Field(100, ge=1, le=1048576)
    deny_by_default: bool = True
class Phase2DeleteRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
class Phase2NetworkRuleRequest(BaseModel):
    tenant_id: str = Field("default", min_length=1, max_length=64)
    vm_id: str = Field("", max_length=80)
    direction: str = Field("ingress", max_length=16)
    action: str = Field("allow", max_length=16)
    proto: str = Field("tcp", max_length=16)
    port: int = Field(0, ge=0, le=65535)
    source: str = Field("0.0.0.0/0", max_length=80)
    destination: str = Field("", max_length=120)
    apply: bool = False
    confirm: str = Field("", max_length=80)
class ZeroTrustTenantNetworkRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1, max_length=64)
    nat: bool = True
    autostart: bool = True
    apply: bool = False
    confirm: str = Field("", max_length=80)
class ZeroTrustVmAttachRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    tenant_id: str = Field(..., min_length=1, max_length=64)
    model: str = Field("virtio", max_length=32)
    replace_existing: bool = True
    live: bool = True
    config: bool = True
    apply: bool = False
    confirm: str = Field("", max_length=80)
class ZeroTrustFirewallApplyRequest(BaseModel):
    apply: bool = False
    confirm: str = Field("", max_length=80)
class Phase2NanoRecipeRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    kernel_path: str = Field(..., min_length=1, max_length=700)
    initrd_path: str = Field("", max_length=700)
    rootfs_path: str = Field("", max_length=700)
    cmdline: str = Field("console=ttyS0 quiet", max_length=1000)
    memory_mb: int = Field(128, ge=32, le=65536)
    vcpus: int = Field(1, ge=1, le=32)
    enabled: bool = True
class Phase2ForgeBuildRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    source_path: str = Field(..., min_length=1, max_length=700)
    dockerfile: str = Field("Dockerfile", max_length=160)
    output_name: str = Field("", max_length=180)
    memory_mb: int = Field(512, ge=128, le=65536)
    vcpus: int = Field(1, ge=1, le=32)
    disk_gb: int = Field(4, ge=1, le=2048)
    auto_register: bool = False
    dry_run: bool = True
class Phase2BrandingRequest(BaseModel):
    host: str = Field(..., min_length=3, max_length=180)
    brand_name: str = Field("NEXUS AERO", max_length=120)
    logo_url: str = Field("", max_length=700)
    palette: dict = Field(default_factory=dict)
    support_url: str = Field("", max_length=700)
    enabled: bool = True
class EdgeFunctionRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    slug: str = Field("", max_length=120)
    runtime: str = Field("python", max_length=20)
    code: str = Field(..., min_length=1, max_length=50000)
    timeout: int = Field(5, ge=1, le=30)
    public: bool = False
    description: str = Field("", max_length=500)
    secrets: dict = Field(default_factory=dict)
class EdgeFunctionDeleteRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=80)
class EdgeSecretRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    value: str = Field(..., min_length=1, max_length=5000)
    scope: str = Field("global", max_length=80)
class EdgeSecretDeleteRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    scope: str = Field("global", max_length=80)
class StorageRetentionPolicyRequest(BaseModel):
    kind: str = Field("data", max_length=32)
    days: int = Field(30, ge=1, le=3650)
    enabled: bool = True
    delete_imported: bool = False
    delete_remote: bool = False
    max_delete: int = Field(25, ge=1, le=500)
class StorageRetentionRunRequest(BaseModel):
    dry_run: bool = True
    confirm: str = Field("", max_length=80)
class NeuralChatRequest(BaseModel):
    model: str = Field("llama3", max_length=120)
    messages: list = Field(default_factory=list)
    stream: bool = False
    temperature: float = Field(0.2, ge=0, le=2)
class VMGuestTelemetryRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    token: str = Field(..., min_length=16, max_length=128)
    hostname: str = Field("", max_length=120)
    os: str = Field("", max_length=160)
    cpu_percent: float = 0
    memory_percent: float = 0
    memory_used_mb: float = 0
    memory_total_mb: float = 0
    disk_percent: float = 0
    disk_used_gb: float = 0
    disk_total_gb: float = 0
    uptime_seconds: float = 0
    ips: list = Field(default_factory=list)
class VMCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=64)
    os_id: str = Field(..., min_length=2, max_length=64)
    iso_path: str = Field(..., min_length=1, max_length=500)
    driver_path: str = Field("", max_length=500)
    driver_categories: List[str] = Field(default_factory=list)
    opencore_path: str = Field("", max_length=500)
    ovmf_code_path: str = Field("", max_length=500)
    ovmf_vars_path: str = Field("", max_length=500)
    legal_byol_ack: bool = False
    memory_mb: int = Field(..., ge=128, le=65536)
    vcpus: int = Field(..., ge=1, le=32)
    disk_gb: int = Field(..., ge=4, le=2048)
    start: bool = True
    network: str = Field("default", max_length=64)
class ISODownloadRequest(BaseModel):
    url: str = Field(..., min_length=8, max_length=1000)
    filename: str = Field("", max_length=180)
class ISOJobRequest(BaseModel): id: str = Field(..., min_length=1, max_length=64)
class ObjectPresignRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=240)
    size: int = Field(0, ge=0)
    content_type: str = Field("application/octet-stream", max_length=180)
    purpose: str = Field("auto", max_length=32)
class ObjectCompleteRequest(BaseModel):
    bucket: str = Field(..., min_length=3, max_length=80)
    key: str = Field(..., min_length=1, max_length=700)
    filename: str = Field(..., min_length=1, max_length=240)
    size: int = Field(0, ge=0)
    content_type: str = Field("application/octet-stream", max_length=180)
    purpose: str = Field("auto", max_length=32)
    etag: str = Field("", max_length=160)
class ObjectImportRequest(BaseModel):
    object_id: str = Field(..., min_length=6, max_length=80)
class ObjectTokenCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=80)
    purpose: str = Field("auto", max_length=32)
    expires_days: int = Field(30, ge=1, le=3650)
    max_size_mb: int = Field(0, ge=0, le=102400)
class ObjectTokenRevokeRequest(BaseModel):
    token_id: str = Field(..., min_length=6, max_length=80)
class CloudUSBMountRequest(BaseModel):
    vm_id: str = Field(..., min_length=1, max_length=80)
    object_ids: List[str] = Field(default_factory=list)
    label: str = Field("NEXUS_USB", max_length=32)
class CloudUSBDetachRequest(BaseModel):
    mount_id: str = Field(..., min_length=6, max_length=80)
class CryptoCoinRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    name: str = Field("", max_length=80)
    amount: float = Field(0, ge=0)
    buy_price_usd: float = Field(0, ge=0)
    note: str = Field("", max_length=240)
class CryptoCoinDeleteRequest(BaseModel):
    coin_id: str = Field(..., min_length=6, max_length=80)

OS_CATALOG = [
    {"id": "win11", "name": "Windows 11", "family": "Microsoft Windows", "variant": "generic", "memory_mb": 8192, "vcpus": 4, "disk_gb": 80, "drivers": "virtio-win", "note": "Zalecane UEFI/TPM; virtio-win dla dysku i sieci."},
    {"id": "win10", "name": "Windows 10", "family": "Microsoft Windows", "variant": "generic", "memory_mb": 4096, "vcpus": 2, "disk_gb": 64, "drivers": "virtio-win", "note": "Po instalacji doinstaluj sterowniki virtio-win."},
    {"id": "win10pe-project2015", "name": "Windows 10 Project 2015 PE PL", "family": "Microsoft Windows Live/PE", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 16, "drivers": "sata/e1000e/vga", "note": "Preset dla Win_10_Project_2015_Portable_czysty_64-bit_PL.ISO; lekki tryb PE pod VPS 4 GB."},
    {"id": "win81", "name": "Windows 8.1", "family": "Microsoft Windows", "variant": "generic", "memory_mb": 3072, "vcpus": 2, "disk_gb": 50, "drivers": "virtio-win", "note": "Starszy desktop Windows."},
    {"id": "win7", "name": "Windows 7 PL", "family": "Microsoft Windows", "variant": "generic", "memory_mb": 1536, "vcpus": 1, "disk_gb": 32, "drivers": "sata/e1000/vga", "note": "Preset dla win7.iso; tryb legacy z e1000 i VGA dla zgodnosci instalatora."},
    {"id": "win7pe-dreamos", "name": "Windows 7 DreamOS PE PL", "family": "Microsoft Windows Live/PE", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 12, "drivers": "sata/e1000/vga", "note": "Preset dla Win_7_SP1_Ent_DreamOS_Portable_czysty_64-bit_PL.ISO; lekki boot Win7PESE/DreamOS."},
    {"id": "win95", "name": "Windows 95 / OSR2", "family": "Microsoft Windows Legacy", "variant": "generic", "memory_mb": 128, "vcpus": 1, "disk_gb": 4, "drivers": "legacy-ide/no-net/vga", "note": "Tryb instalacyjny legacy: IDE, VGA, PS/2, qemu32 i siec OFF, zeby uniknac bledu NDIS."},
    {"id": "win98", "name": "Windows 98 / 98 SE", "family": "Microsoft Windows Legacy", "variant": "generic", "memory_mb": 256, "vcpus": 1, "disk_gb": 8, "drivers": "legacy-ide/no-net/vga", "note": "Tryb instalacyjny legacy: IDE, VGA, PS/2, qemu32 i siec OFF; siec wlacz po instalacji jako pcnet/rtl8139."},
    {"id": "winxp", "name": "Windows XP PL", "family": "Microsoft Windows Legacy", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 20, "drivers": "legacy-ide/e1000", "note": "Preset dla GRTMPOEM_PL.ISO; uzywa IDE, e1000 i VGA dla zgodnosci instalatora XP."},
    {"id": "win2012", "name": "Windows Server 2012 / R2", "family": "Microsoft Windows", "variant": "generic", "memory_mb": 4096, "vcpus": 2, "disk_gb": 60, "drivers": "virtio-win", "note": "Serwer legacy."},
    {"id": "win2016", "name": "Windows Server 2016", "family": "Microsoft Windows", "variant": "generic", "memory_mb": 4096, "vcpus": 2, "disk_gb": 70, "drivers": "virtio-win", "note": "Serwer produkcyjny/testowy."},
    {"id": "win2019", "name": "Windows Server 2019", "family": "Microsoft Windows", "variant": "generic", "memory_mb": 4096, "vcpus": 2, "disk_gb": 80, "drivers": "virtio-win", "note": "Serwer produkcyjny/testowy."},
    {"id": "win2022", "name": "Windows Server 2022 / 2025", "family": "Microsoft Windows", "variant": "generic", "memory_mb": 6144, "vcpus": 4, "disk_gb": 90, "drivers": "virtio-win", "note": "Nowszy serwer Windows; virtio-win zalecane."},
    {"id": "macos-uefi", "name": "macOS / Apple UEFI", "family": "Apple macOS", "variant": "generic", "memory_mb": 4096, "vcpus": 2, "disk_gb": 64, "drivers": "uefi-sata-usb-tablet", "note": "Preset legal/manual: UEFI, SATA, USB tablet, e1000e. Wymaga legalnego obrazu/firmware i nie wstrzykuje SMC/OSK."},
    {"id": "debian", "name": "Debian", "family": "Linux Debian/Ubuntu", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 16, "drivers": "native", "note": "Stabilny i lekki bazowy Linux."},
    {"id": "ubuntu", "name": "Ubuntu Server/Desktop", "family": "Linux Debian/Ubuntu", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 20, "drivers": "native", "note": "Popularny Linux serwerowy lub desktop; lekki profil pod wiele VM."},
    {"id": "mint", "name": "Linux Mint", "family": "Linux Debian/Ubuntu", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 24, "drivers": "native", "note": "Desktop oparty na Ubuntu/Debian; na malym VPS zwieksz RAM dopiero po starcie."},
    {"id": "kali", "name": "Kali Linux", "family": "Linux Debian/Ubuntu", "variant": "generic", "memory_mb": 2048, "vcpus": 2, "disk_gb": 32, "drivers": "native", "note": "Pentest lab; trzymaj odizolowany od produkcji."},
    {"id": "almalinux", "name": "AlmaLinux", "family": "Linux RHEL", "variant": "generic", "memory_mb": 2048, "vcpus": 2, "disk_gb": 24, "drivers": "native", "note": "Zgodny z RHEL."},
    {"id": "rocky", "name": "Rocky Linux", "family": "Linux RHEL", "variant": "generic", "memory_mb": 2048, "vcpus": 2, "disk_gb": 24, "drivers": "native", "note": "Stabilny zamiennik CentOS/RHEL."},
    {"id": "centos-stream", "name": "CentOS Stream", "family": "Linux RHEL", "variant": "generic", "memory_mb": 2048, "vcpus": 2, "disk_gb": 24, "drivers": "native", "note": "Rolling-preview rodziny RHEL."},
    {"id": "fedora", "name": "Fedora", "family": "Linux RHEL", "variant": "generic", "memory_mb": 3072, "vcpus": 2, "disk_gb": 32, "drivers": "native", "note": "Najnowsze pakiety i kernel."},
    {"id": "arch", "name": "Arch Linux", "family": "Linux Other", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 16, "drivers": "native", "note": "Minimalny system rolling release."},
    {"id": "alpine", "name": "Alpine Linux", "family": "Linux Other", "variant": "generic", "memory_mb": 512, "vcpus": 1, "disk_gb": 8, "drivers": "native", "note": "Ekstremalnie lekki."},
    {"id": "gentoo", "name": "Gentoo", "family": "Linux Other", "variant": "generic", "memory_mb": 2048, "vcpus": 2, "disk_gb": 32, "drivers": "native", "note": "Dla zaawansowanych; kompilacja wymaga zasobow."},
    {"id": "opensuse", "name": "openSUSE Leap/Tumbleweed", "family": "Linux Other", "variant": "generic", "memory_mb": 2048, "vcpus": 2, "disk_gb": 32, "drivers": "native", "note": "Stabilny Leap lub rolling Tumbleweed."},
    {"id": "freebsd", "name": "FreeBSD", "family": "BSD / Router", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 20, "drivers": "native", "note": "BSD bazowy, dobry do sieci i storage."},
    {"id": "openbsd", "name": "OpenBSD", "family": "BSD / Router", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 16, "drivers": "native", "note": "Security-focused BSD."},
    {"id": "netbsd", "name": "NetBSD", "family": "BSD / Router", "variant": "generic", "memory_mb": 768, "vcpus": 1, "disk_gb": 12, "drivers": "native", "note": "Lekki i przenosny BSD."},
    {"id": "pfsense", "name": "pfSense", "family": "BSD / Router", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 16, "drivers": "native", "note": "Firewall/router; uwazaj na konfiguracje sieci."},
    {"id": "opnsense", "name": "OPNsense", "family": "BSD / Router", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 16, "drivers": "native", "note": "Firewall/router alternatywny dla pfSense."},
    {"id": "truenas-core", "name": "TrueNAS CORE", "family": "BSD / Router", "variant": "generic", "memory_mb": 8192, "vcpus": 2, "disk_gb": 40, "drivers": "native", "note": "Storage lab; ZFS lubi RAM."},
    {"id": "freedos", "name": "FreeDOS", "family": "Legacy / Special", "variant": "generic", "memory_mb": 256, "vcpus": 1, "disk_gb": 4, "drivers": "legacy", "note": "DOS/retro testy."},
    {"id": "reactos", "name": "ReactOS", "family": "Legacy / Special", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 12, "drivers": "experimental", "note": "Eksperymentalny klon architektury Windows."},
    {"id": "haiku", "name": "Haiku OS", "family": "Legacy / Special", "variant": "generic", "memory_mb": 1024, "vcpus": 1, "disk_gb": 16, "drivers": "native", "note": "Nowoczesny system inspirowany BeOS."},
]

ISO_SOURCE_PRESETS = [
    {"id": "debian-netinst", "name": "Debian 13 amd64 netinst", "family": "Linux", "url": "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-13.6.0-amd64-netinst.iso", "source_page": "https://www.debian.org/download", "mode": "direct"},
    {"id": "ubuntu-server", "name": "Ubuntu Server 26.04 LTS amd64", "family": "Linux", "url": "https://releases.ubuntu.com/26.04/ubuntu-26.04-live-server-amd64.iso", "source_page": "https://ubuntu.com/download/server", "mode": "direct"},
    {"id": "ubuntu-desktop", "name": "Ubuntu Desktop", "family": "Linux", "url": "", "source_page": "https://ubuntu.com/download/desktop", "mode": "manual"},
    {"id": "kali", "name": "Kali Linux", "family": "Linux", "url": "", "source_page": "https://www.kali.org/get-kali/", "mode": "manual"},
    {"id": "fedora", "name": "Fedora", "family": "Linux", "url": "", "source_page": "https://fedoraproject.org/workstation/download", "mode": "manual"},
    {"id": "arch", "name": "Arch Linux latest x86_64", "family": "Linux", "url": "https://geo.mirror.pkgbuild.com/iso/latest/archlinux-x86_64.iso", "source_page": "https://archlinux.org/download/", "mode": "direct"},
    {"id": "alpine-virt", "name": "Alpine Linux Virt 3.24.1 x86_64", "family": "Linux", "url": "https://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/x86_64/alpine-virt-3.24.1-x86_64.iso", "source_page": "https://alpinelinux.org/downloads/", "mode": "direct"},
    {"id": "alpine-standard", "name": "Alpine Linux Standard 3.24.1 x86_64", "family": "Linux", "url": "https://dl-cdn.alpinelinux.org/alpine/latest-stable/releases/x86_64/alpine-standard-3.24.1-x86_64.iso", "source_page": "https://alpinelinux.org/downloads/", "mode": "direct"},
    {"id": "freebsd", "name": "FreeBSD amd64", "family": "BSD", "url": "", "source_page": "https://www.freebsd.org/where/", "mode": "manual"},
    {"id": "pfsense", "name": "pfSense", "family": "Router", "url": "", "source_page": "https://www.pfsense.org/download/", "mode": "manual"},
    {"id": "opnsense", "name": "OPNsense", "family": "Router", "url": "", "source_page": "https://opnsense.org/download/", "mode": "manual"},
    {"id": "freedos", "name": "FreeDOS", "family": "Legacy", "url": "", "source_page": "https://www.freedos.org/download/", "mode": "manual"},
    {"id": "reactos", "name": "ReactOS", "family": "Legacy", "url": "", "source_page": "https://reactos.org/download/", "mode": "manual"},
    {"id": "haiku", "name": "Haiku OS", "family": "Legacy", "url": "", "source_page": "https://www.haiku-os.org/get-haiku/", "mode": "manual"},
    {"id": "macos-manual", "name": "macOS recovery / installer", "family": "Apple macOS", "url": "", "source_page": "", "mode": "manual"},
    {"id": "windows11", "name": "Windows 11 ISO", "family": "Windows", "url": "", "source_page": "https://www.microsoft.com/en-us/software-download/windows11", "mode": "manual"},
    {"id": "windows10", "name": "Windows 10 ISO", "family": "Windows", "url": "", "source_page": "https://www.microsoft.com/software-download/windows10", "mode": "manual"},
    {"id": "windows7-pl-local", "name": "Windows 7 PL - win7.iso", "family": "Windows Legacy", "url": "", "source_page": "", "mode": "manual"},
    {"id": "windows7-dreamos-pe", "name": "Windows 7 DreamOS PE PL", "family": "Windows Live/PE", "url": "", "source_page": "", "mode": "manual"},
    {"id": "windows10-project2015-pe", "name": "Windows 10 Project 2015 PE PL", "family": "Windows Live/PE", "url": "", "source_page": "", "mode": "manual"},
    {"id": "windows95-local", "name": "Windows 95 / OSR2 ISO", "family": "Windows Legacy", "url": "", "source_page": "", "mode": "manual"},
    {"id": "windows98-local", "name": "Windows 98 / 98 SE ISO", "family": "Windows Legacy", "url": "", "source_page": "", "mode": "manual"},
    {"id": "windows-xp-pl", "name": "Windows XP PL - GRTMPOEM_PL.ISO", "family": "Windows Legacy", "url": "", "source_page": "", "mode": "manual"},
    {"id": "virtio-win", "name": "VirtIO Windows Drivers stable ISO", "family": "Windows", "url": "https://fedora-virt.repo.nfrance.com/virtio-win/direct-downloads/stable-virtio/virtio-win.iso", "source_page": "https://github.com/virtio-win/virtio-win-pkg-scripts/blob/master/README.md", "mode": "direct"},
]

ISO_DOWNLOADS = {}
SERVER_BACKUP_JOBS = {}

def read_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback

def write_json(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)

def fmt_size(size):
    units = ["B", "KB", "MB", "GB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024

def backup_file_row(path: Path):
    stat = path.stat()
    return {
        "filename": path.name,
        "path": str(path),
        "date": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
        "created_at": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
        "size": fmt_size(stat.st_size),
        "size_bytes": stat.st_size,
        "timestamp": stat.st_mtime,
    }

def resolve_under(root: Path, rel: str):
    target = (root / (rel or "")).resolve()
    root_resolved = root.resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise HTTPException(status_code=400, detail="Niepoprawna sciezka")
    return target

def file_meta(path: Path, root: Path, kind: str):
    stat = path.stat()
    rel = str(path.relative_to(root)).replace("\\", "/")
    return {
        "id": hashlib.sha1(f"{root}:{rel}".encode()).hexdigest()[:12],
        "name": path.name,
        "path": rel,
        "kind": kind,
        "size": stat.st_size,
        "size_label": fmt_size(stat.st_size),
        "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        "mime": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
    }

def require_query_session(token: str = ""):
    user = SESSIONS.get(token or "")
    if not user:
        raise HTTPException(status_code=401, detail="Odmowa dostepu")
    return user

def request_ip(request: Request):
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip") or ""
    direct = request.client.host if request.client else ""
    return forwarded or real_ip or direct or "unknown"

APPLIANCE_UNIT = os.environ.get("NEXUS_APPLIANCE_UNIT", "nexusos-appliance.service")
DESKTOP_UNIT = os.environ.get("NEXUS_DESKTOP_UNIT", "nexusos-desktop.service")
DISPLAY_MANAGER_UNIT = os.environ.get("NEXUS_DISPLAY_MANAGER_UNIT", "display-manager.service")
GETTY_TTY1_UNIT = os.environ.get("NEXUS_GETTY_UNIT", "getty@tty1.service")

def _is_loopback_request(request: Request):
    host = request_ip(request)
    return host in {"127.0.0.1", "::1", "localhost"} or host.startswith("127.")

def _appliance_local_switch_enabled():
    return os.environ.get("NEXUS_APPLIANCE_LOCAL_SWITCH", "1").strip().lower() not in {"0", "false", "no", "off"}

def _appliance_actor(request: Request, token: str = ""):
    if token:
        session = SESSIONS.get(token or "")
        if session:
            session = sync_session_user(session)
            if normalize_status(session.get("status", "active")) != "active":
                raise HTTPException(status_code=403, detail="Konto nieaktywne")
            if normalize_role(session.get("role")) != "admin":
                raise HTTPException(status_code=403, detail="Przelacznik pulpitu wymaga admina")
            return session.get("username") or "admin"
    if _appliance_local_switch_enabled() and _is_loopback_request(request):
        return "local-appliance"
    raise HTTPException(status_code=403, detail="Brak uprawnien do przelaczania trybu appliance")

def _systemctl_path():
    return shutil.which("systemctl") or "/bin/systemctl"

def _systemd_ready():
    return platform.system().lower() == "linux" and Path("/run/systemd/system").exists() and bool(shutil.which("systemctl") or Path("/bin/systemctl").exists())

def _running_as_root():
    geteuid = getattr(os, "geteuid", None)
    if geteuid is None:
        return False
    try:
        return geteuid() == 0
    except Exception:
        return False

def _run_systemctl(*args, timeout=14):
    cmd = [_systemctl_path(), *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "cmd": " ".join(cmd),
            "rc": proc.returncode,
            "ok": proc.returncode == 0,
            "stdout": (proc.stdout or "").strip()[-1200:],
            "stderr": (proc.stderr or "").strip()[-1200:],
        }
    except Exception as exc:
        return {"cmd": " ".join(cmd), "rc": 127, "ok": False, "stdout": "", "stderr": str(exc)}

def _unit_state(unit: str):
    if not _systemd_ready():
        return {"unit": unit, "active": "unavailable", "enabled": "unavailable", "ok": False}
    active = _run_systemctl("is-active", unit, timeout=5)
    enabled = _run_systemctl("is-enabled", unit, timeout=5)
    return {
        "unit": unit,
        "active": active["stdout"] or ("active" if active["ok"] else "inactive"),
        "enabled": enabled["stdout"] or ("enabled" if enabled["ok"] else "disabled"),
        "ok": active["ok"] or enabled["ok"],
        "active_rc": active["rc"],
        "enabled_rc": enabled["rc"],
    }

def _appliance_status():
    appliance = _unit_state(APPLIANCE_UNIT)
    desktop = _unit_state(DESKTOP_UNIT)
    display = _unit_state(DISPLAY_MANAGER_UNIT)
    getty = _unit_state(GETTY_TTY1_UNIT)
    if appliance.get("active") == "active":
        mode = "kiosk"
    elif desktop.get("active") == "active":
        mode = "desktop"
    elif display.get("active") == "active":
        mode = "desktop"
    elif getty.get("active") == "active":
        mode = "tty"
    else:
        mode = "unknown"
    return {
        "status": "success",
        "mode": mode,
        "can_switch": _systemd_ready() and _running_as_root(),
        "requires_root": not _running_as_root(),
        "systemd": _systemd_ready(),
        "local_switch": _appliance_local_switch_enabled(),
        "units": {
            "appliance": appliance,
            "desktop": desktop,
            "display_manager": display,
            "tty1": getty,
        },
    }

def _switch_appliance_mode(mode: str, dry_run: bool = False):
    target = (mode or "").strip().lower()
    if target not in {"desktop", "kiosk"}:
        raise HTTPException(status_code=400, detail="Dozwolone tryby: desktop albo kiosk")
    plan = []
    if target == "desktop":
        plan = [("stop", APPLIANCE_UNIT), ("unmask", GETTY_TTY1_UNIT), ("enable", DESKTOP_UNIT), ("start", DESKTOP_UNIT)]
    else:
        plan = [("stop", DESKTOP_UNIT), ("stop", DISPLAY_MANAGER_UNIT), ("stop", GETTY_TTY1_UNIT), ("enable", APPLIANCE_UNIT), ("start", APPLIANCE_UNIT)]
    if dry_run:
        return {"status": "success", "dry_run": True, "target": target, "plan": [" ".join(p) for p in plan], "state": _appliance_status()}
    if not _systemd_ready():
        raise HTTPException(status_code=409, detail="Systemd nie jest dostepny na tej maszynie")
    if not _running_as_root():
        raise HTTPException(status_code=403, detail="Backend musi dzialac jako root, aby przelaczac kiosk/pulpit")
    results = []
    hard_failure = None
    desktop_started = False
    for action, unit in plan:
        res = _run_systemctl(action, unit)
        res["action"] = action
        res["unit"] = unit
        results.append(res)
        if target == "desktop" and action == "start" and unit == DESKTOP_UNIT and res["ok"]:
            desktop_started = True
        if target == "kiosk" and action in {"enable", "start"} and unit == APPLIANCE_UNIT and not res["ok"]:
            hard_failure = hard_failure or res
    if target == "desktop" and not desktop_started:
        dm = _run_systemctl("start", DISPLAY_MANAGER_UNIT)
        dm["action"] = "start"
        dm["unit"] = DISPLAY_MANAGER_UNIT
        dm["fallback"] = True
        results.append(dm)
        if not dm["ok"]:
            for action, unit in [("enable", GETTY_TTY1_UNIT), ("start", GETTY_TTY1_UNIT)]:
                res = _run_systemctl(action, unit)
                res["action"] = action
                res["unit"] = unit
                res["fallback"] = True
                results.append(res)
                if action == "start" and not res["ok"]:
                    hard_failure = hard_failure or res
    status = _appliance_status()
    message = "Przelaczono na kiosk." if target == "kiosk" else "Przelaczono na pulpit albo awaryjny terminal tty1."
    if hard_failure:
        return {"status": "warning", "target": target, "message": message, "warning": hard_failure.get("stderr") or hard_failure.get("stdout"), "results": results, "state": status}
    return {"status": "success", "target": target, "message": message, "results": results, "state": status}

@app.get("/api/appliance/status")
async def appliance_status(request: Request, x_auth_token: str = Header(None)):
    _appliance_actor(request, x_auth_token or "")
    return _appliance_status()

@app.post("/api/appliance/mode")
async def appliance_mode(data: ApplianceModeRequest, request: Request, x_auth_token: str = Header(None)):
    actor = _appliance_actor(request, x_auth_token or "")
    result = _switch_appliance_mode(data.mode, data.dry_run)
    audit_event(actor, "appliance.switch", data.mode, result.get("status", "OK").upper(), request, {"dry_run": data.dry_run})
    log_event(f"APPLIANCE SWITCH actor={actor} mode={data.mode} dry_run={data.dry_run} status={result.get('status')}")
    return result

def append_login_audit(username: str, status: str, request: Request):
    rows = read_json(LOGIN_AUDIT_FILE, [])
    rows.insert(0, {
        "time": now_iso(),
        "username": username,
        "status": status,
        "ip": request_ip(request),
        "user_agent": (request.headers.get("user-agent") or "")[:220],
    })
    write_json(LOGIN_AUDIT_FILE, rows[:300])

def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")

def today_key():
    return datetime.date.today().isoformat()

def update_login_karma(username: str):
    data = read_json(KARMA_FILE, {})
    user_data = data.setdefault(username, {"login_dates": [], "exp": 0})
    dates = user_data.setdefault("login_dates", [])
    today = today_key()
    if today not in dates:
        dates.append(today)
        user_data["exp"] = int(user_data.get("exp", 0)) + 25
    user_data["last_login"] = now_iso()
    user_data["login_dates"] = dates[-90:]
    write_json(KARMA_FILE, data)

def login_streak(dates):
    parsed = set()
    for value in dates or []:
        try:
            parsed.add(datetime.date.fromisoformat(value))
        except Exception:
            pass
    streak = 0
    cursor = datetime.date.today()
    while cursor in parsed:
        streak += 1
        cursor -= datetime.timedelta(days=1)
    return streak

def system_uptime_days():
    try:
        return int(float(Path("/proc/uptime").read_text().split()[0]) // 86400)
    except Exception:
        return 0

def build_briefing():
    logs = []
    try:
        logs = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()[-120:]
    except Exception:
        pass
    important = [line for line in logs if any(word in line.upper() for word in ["ERROR", "FAIL", "CRITICAL", "WARN", "LOGIN"])]
    alerts = read_json(ALERTS_FILE, [])[:10]
    disk = shutil.disk_usage(str(BASE_DIR))
    briefing = {
        "generated_at": now_iso(),
        "date": today_key(),
        "title": "MORNING BRIEFING",
        "summary": [
            f"Uptime serwera: {system_uptime_days()} dni.",
            f"Dysk: {round(((disk.total - disk.free) / disk.total) * 100, 1) if disk.total else 0}% zajete.",
            f"Wazne wpisy z logow: {len(important)}.",
            f"Aktywne alerty w panelu: {len(alerts)}.",
        ],
        "signals": important[-12:],
        "alerts": alerts[:5],
    }
    write_json(BRIEFING_FILE, briefing)
    return briefing

# --- 🚀 GIGA BAZA WTYCZEK (45 SZTUK) 🚀 ---
MARKETPLACE_CATALOG = [
    # --- ADMIN & SECURITY ---
    {"id": "netsentry", "name": "🛡️ NetSentry FireWall", "desc": "Zaawansowany skaner portów TCP/UDP, detektor obcych urządzeń w LAN.", "cat": "ADMIN", "version": "2.1.0", "size": "850 KB", "author": "RootSlayer"},
    {"id": "hydra_sec", "name": "🐲 HydraBrute Sec", "desc": "Wykrywa i blokuje ataki brute-force na SSH (wbudowany mini fail2ban).", "cat": "ADMIN", "version": "1.1.8", "size": "440 KB", "author": "SecOps_PL"},
    {"id": "mac_spoofer", "name": "🎭 MAC Spoofer Pro", "desc": "Tymczasowo maskuje fizyczny adres MAC w publicznych sieciach.", "cat": "ADMIN", "version": "2.2.0", "size": "120 KB", "author": "GhostProtocol"},
    {"id": "ssh_forge", "name": "🔑 SSH KeyForge", "desc": "Menedżer kryptograficzny. Generuje i chroni klucze RSA/Ed25519.", "cat": "ADMIN", "version": "2.5.0", "size": "1.4 MB", "author": "CryptoPunk"},
    {"id": "pass_vault", "name": "🔒 VaultX Password", "desc": "Lokalny menedżer haseł AES-256 z wirtualną klawiaturą anty-keylogger.", "cat": "ADMIN", "version": "3.1.2", "size": "2.8 MB", "author": "ZeroTrust"},
    {"id": "wifi_kill", "name": "📡 WiFi Deauth Sec", "desc": "Narzędzie audytu. Testuj odporność swojej sieci na pakiety deautentykacyjne.", "cat": "ADMIN", "version": "1.0.5", "size": "210 KB", "author": "Pentester"},
    {"id": "malware_scan", "name": "🦠 VirusTotal Bridge", "desc": "Zintegrowane wysyłanie podejrzanych plików prosto do bazy VirusTotal.", "cat": "ADMIN", "version": "2.3.0", "size": "500 KB", "author": "SecOps_PL"},
    {"id": "tor_relay", "name": "🧅 Tor Relay Node", "desc": "Postaw prywatny serwer proxy sieci Tor i wspieraj anonimowość w internecie.", "cat": "ADMIN", "version": "1.0.0", "size": "5.5 MB", "author": "OnionSec"},
    {"id": "ping_map", "name": "🗺️ PingMap Visual", "desc": "Radar opóźnień do węzłów DNS. Wizualizuje lagi w czasie rzeczywistym.", "cat": "ADMIN", "version": "1.6.0", "size": "700 KB", "author": "NetRunner"},
    {"id": "dns_spoofer", "name": "🔀 Local DNS Masker", "desc": "Przekierowuj ruch, blokuj domeny trackerów edytując wbudowany hosts.", "cat": "ADMIN", "version": "1.0.5", "size": "340 KB", "author": "GhostNode"},
    {"id": "log_visual", "name": "📊 LogVis Pro", "desc": "Generuje wykresy słupkowe i kołowe ze statystyk surowych plików log.", "cat": "ADMIN", "version": "2.0.0", "size": "1.7 MB", "author": "DataSmith"},
    
    # --- SYSTEM & DEV ---
    {"id": "overlord", "name": "🔥 SystemOverlord X", "desc": "Moduł monitorowania temperatur CPU, cache cleaner i kontrola Termuxa.", "cat": "SYSTEM", "version": "3.0.5", "size": "2.1 MB", "author": "KernelDev"},
    {"id": "git_master", "name": "🐙 GitMaster UI", "desc": "Wizualny menedżer repozytoriów. Push, pull i commit bez wpisywania komend.", "cat": "SYSTEM", "version": "3.1.5", "size": "2.1 MB", "author": "CodeNinja"},
    {"id": "api_tester", "name": "🚀 REST API Tester", "desc": "Narzędzie dla devów a'la Postman. Testuj nagłówki i wysyłaj payloady JSON.", "cat": "SYSTEM", "version": "1.4.0", "size": "850 KB", "author": "DevOps_PL"},
    {"id": "json_forge", "name": "🔣 JSON/YAML Forge", "desc": "Walidator składni dla plików konfiguracyjnych. Automatyczna naprawa błędów.", "cat": "SYSTEM", "version": "1.1.2", "size": "300 KB", "author": "DataSmith"},
    {"id": "regex_pad", "name": "🔎 RegEx Ninja", "desc": "Tester wyrażeń regularnych z generowaniem kodu w Python/JS.", "cat": "SYSTEM", "version": "1.0.4", "size": "180 KB", "author": "StringMaster"},
    {"id": "cron_ui", "name": "⏰ Chronos Tasker", "desc": "Graficzne zarządzanie crontabem. Automatyzuj skrypty o zadanej godzinie.", "cat": "SYSTEM", "version": "2.0.1", "size": "1.1 MB", "author": "TimeLord"},
    {"id": "pdf_tools", "name": "📄 PDF Ninja", "desc": "Łącz, dziel, nakładaj znaki wodne i kompresuj pliki PDF na serwerze.", "cat": "SYSTEM", "version": "1.5.2", "size": "4.2 MB", "author": "DocMaster"},
    {"id": "docker_ui", "name": "🐳 Container Hub", "desc": "Wizualne sterowanie środowiskami chroot/proot. Uruchom distro Linuksa kliknięciem.", "cat": "SYSTEM", "version": "0.9.beta", "size": "4.5 MB", "author": "SysAdmin"},
    {"id": "sys_cleaner", "name": "🧹 DeepClean Pro", "desc": "Aplikacja do automatycznego usuwania śmieci, logów i starych cache'y.", "cat": "SYSTEM", "version": "1.2.0", "size": "320 KB", "author": "NexusCore"},
    {"id": "battery_mon", "name": "🔋 PowerCell Monitor", "desc": "Dodaje zaawansowane logowanie drenażu baterii urządzenia hostującego.", "cat": "SYSTEM", "version": "1.8.4", "size": "650 KB", "author": "VoltTech"},
    {"id": "hex_editor", "name": "🔢 HexaCore Editor", "desc": "Niskopoziomowy edytor binarny dla zaawansowanego reverse engineeringu.", "cat": "SYSTEM", "version": "1.1.0", "size": "500 KB", "author": "BinaryBoy"},

    # --- AI & INTELLIGENCE ---
    {"id": "dev_pal", "name": "🤖 AI DevPal ScriptGen", "desc": "Agent Gemini generujący gotowe pliki Py/Bash i wgrywający je do systemu.", "cat": "INTELLIGENCE", "version": "1.5.0", "size": "1.8 MB", "author": "GeminiCore"},
    {"id": "ai_coder", "name": "💻 CodeLlama Bridge", "desc": "Lokalne podpowiadanie kodu i autouzupełnianie w edytorze plików.", "cat": "INTELLIGENCE", "version": "0.9.1", "size": "12.4 MB", "author": "LlamaDev"},
    {"id": "ai_sentiment", "name": "🎭 AI Sentiment", "desc": "Moduł analizujący wydźwięk tekstów i logów (np. detekcja anomalii zachowań).", "cat": "INTELLIGENCE", "version": "1.2.0", "size": "450 KB", "author": "PsychoBot"},
    {"id": "ai_translator", "name": "🌍 BabelCore", "desc": "Tłumacz językowy oparty na silnikach neuronowych. Idealny do dokumentacji.", "cat": "INTELLIGENCE", "version": "2.0.0", "size": "1.8 MB", "author": "PolyglotAI"},
    {"id": "ai_voice", "name": "🗣️ VoiceGen TTS", "desc": "Pozwala Twojemu Asystentowi odczytywać ostrzeżenia i odpowiedzi głosowo.", "cat": "INTELLIGENCE", "version": "2.0.0", "size": "8.4 MB", "author": "AudioMind"},
    {"id": "prompt_lib", "name": "🧠 Prompt Master Lib", "desc": "Biblioteka tysięcy skutecznych poleceń dla sztucznej inteligencji.", "cat": "INTELLIGENCE", "version": "1.1.0", "size": "500 KB", "author": "PromptEng"},
    {"id": "vision_ai", "name": "👁️ Vision AI OCR", "desc": "Skaner obrazów. Wgrywaj zdjęcia, a AI automatycznie przepisze z nich kod/tekst.", "cat": "INTELLIGENCE", "version": "0.8.alpha", "size": "3.1 MB", "author": "NexusLabs"},

    # --- LIFESTYLE & ENTERTAINMENT ---
    {"id": "cryptx", "name": "🪙 NEXUS CryptX Pro", "desc": "Śledzenie portfela kryptowalut w czasie rzeczywistym, wykresy i powiadomienia.", "cat": "LIFESTYLE", "version": "1.4.2", "size": "1.2 MB", "author": "CyberGoth"},
    {"id": "extended_muzik", "name": "🎵 NeoMuzik Player", "desc": "Zewnętrzny moduł audio z equalizerem parametrycznym i wizualizerem częstotliwości.", "cat": "LIFESTYLE", "version": "2.2.1", "size": "3.4 MB", "author": "WaveMaster"},
    {"id": "game_hub", "name": "👾 Retro GameHub", "desc": "Centrum gier: Tetris, Pong, Asteroids i Space Invaders działające w panelu.", "cat": "LIFESTYLE", "version": "4.0.0", "size": "910 KB", "author": "PixelNerd"},
    {"id": "ascii_art", "name": "🎨 ASCII Generator", "desc": "Konwertuje przesłane grafiki i tekst na oldschoolowe obrazy znakowe ASCII.", "cat": "LIFESTYLE", "version": "1.0.2", "size": "150 KB", "author": "RetroVibe"},
    {"id": "pomodoro", "name": "🍅 Cyber Pomodoro", "desc": "Zegar pracy głębokiej dla programistów. Synchronizuje przerwy z wyciszaniem powiadomień.", "cat": "LIFESTYLE", "version": "2.1.0", "size": "420 KB", "author": "FocusHacker"},
    {"id": "rss_feed", "name": "📰 HackerNews Feed", "desc": "Wyciąga najświeższe newsy o cybersecurity, IT i z darknetu. Codziennie na ekranie główym.", "cat": "LIFESTYLE", "version": "1.9.0", "size": "600 KB", "author": "NewsScraper"},
    {"id": "markdown_ed", "name": "📝 MarkDown Pad", "desc": "Notatnik programistyczny z natychmiastowym podglądem i konwersją do HTML.", "cat": "LIFESTYLE", "version": "3.3.0", "size": "1.5 MB", "author": "DocBuilder"},
    {"id": "weather_pro", "name": "🌪️ Doppler Radar", "desc": "Zaawansowana, satelitarna mapa opadów dla modułu pogodowego.", "cat": "LIFESTYLE", "version": "2.4.1", "size": "4.2 MB", "author": "MeteoX"},
    {"id": "chess_engine", "name": "♟️ DeepBlue Chess", "desc": "Rozegraj partię z silnikiem Stockfish bezpośrednio w interfejsie systemowym.", "cat": "LIFESTYLE", "version": "1.1.1", "size": "2.0 MB", "author": "GrandMaster"},
    {"id": "term_browser", "name": "🌐 Lynx Web View", "desc": "Eksperymentalny port tekstowej przeglądarki. Czytaj strony WWW jako surowy tekst.", "cat": "LIFESTYLE", "version": "2.8.9", "size": "1.1 MB", "author": "RetroWeb"},
    {"id": "cyber_calc", "name": "🧮 Bitwise Calc", "desc": "Kalkulator operacji bitowych, logicznych. Szybkie konwersje HEX/DEC/BIN.", "cat": "LIFESTYLE", "version": "1.0.0", "size": "100 KB", "author": "MathGenius"},
    {"id": "habit_track", "name": "📈 HabitHacker RPG", "desc": "Monitoruj nawyki w formie gry RPG. Wbijaj poziomy w pisaniu kodu i ćwiczeniach.", "cat": "LIFESTYLE", "version": "3.1.0", "size": "950 KB", "author": "LifeDev"},
    {"id": "matrix_rain", "name": "📺 Matrix Rain", "desc": "Gdy długo nie wykonujesz akcji, ekran zasypuje klasyczny kod Matrixa.", "cat": "LIFESTYLE", "version": "1.0.0", "size": "120 KB", "author": "NeoPol"},
    {"id": "img_glitch", "name": "🖼️ GlitchArt Gen", "desc": "Narzędzie artystyczne zniekształcające pliki JPG do estetyki Cyberpunk Glitch.", "cat": "LIFESTYLE", "version": "1.1.1", "size": "2.5 MB", "author": "PixelNerd"},
    {"id": "stock_bot", "name": "📉 WallStreet Bot", "desc": "Pobiera dane giełdowe S&P500 i NASDAQ, analizuje je prostymi algorytmami.", "cat": "LIFESTYLE", "version": "1.0.5", "size": "780 KB", "author": "TradeLord"}
]

@app.get("/manifest.json")
async def get_manifest(): return { "name": "NEXUS AERO", "short_name": "NEXUS", "start_url": "/", "display": "standalone", "background_color": "#F5F5F7", "theme_color": "#F5F5F7" }
@app.get("/sw.js")
async def get_sw():
    script = """
self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('push', event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { data = { title: 'NEXUS ALERT', body: event.data ? event.data.text() : '' }; }
  event.waitUntil(self.registration.showNotification(data.title || 'NEXUS ALERT', {
    body: data.body || 'Nowy sygnal z panelu.',
    tag: data.tag || 'nexus-alert',
    data: data.url || '/'
  }));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(self.clients.openWindow(event.notification.data || '/'));
});
self.addEventListener('fetch', event => event.respondWith(fetch(event.request)));
"""
    return Response(content=script, media_type="application/javascript")
@app.get("/")
async def root(): return FileResponse(str(STATIC_DIR / "aero.html"))

@app.on_event("startup")
async def startup_init_iam():
    ensure_iam_db()

def auth_payload(username, user, token):
    public = public_user(username, user)
    return {
        "status": "success",
        "token": token,
        "username": username,
        "role": public["role"],
        "account_status": public["status"],
        "user": public,
    }

def create_runtime_session(username, user):
    now = now_iso()
    return {
        "username": username,
        "role": normalize_role(user.get("role", "user")),
        "status": normalize_status(user.get("status", "active")),
        "created_at": now,
        "last_seen": now,
        "device_id": "",
        "label": "WEB",
    }

@app.post("/api/auth/register")
async def register_user(data: RegisterRequest, request: Request):
    username = normalize_username(data.username)
    users = load_users()
    if username in users:
        audit_event(username, "auth.register", username, "CONFLICT", request)
        raise HTTPException(status_code=409, detail="Uzytkownik juz istnieje")
    users[username] = {
        "id": str(uuid.uuid4()),
        "username": username,
        "role": "user",
        "status": "pending",
        "password_hash": hash_password(data.password),
        "created_at": now_iso(),
    }
    save_users(users)
    append_login_audit(username, "REGISTER_PENDING", request)
    audit_event(username, "auth.register", username, "PENDING", request)
    log_event(f"REGISTER PENDING: {username}")
    return {"status": "pending", "account_status": "pending", "username": username, "message": "Konto czeka na akceptacje admina"}

@app.post("/api/auth/login")
async def login(data: LoginRequest, request: Request, response: Response):
    username = normalize_username(data.username or "admin")
    check_login_rate_limit(username, request)
    users = load_users()
    user = users.get(username)
    if user and normalize_status(user.get("status", "active")) != "deleted" and verify_password(data.password, user.get("password_hash", "")):
        if password_needs_upgrade(user.get("password_hash", "")):
            user["password_hash"] = hash_password(data.password)
            user["password_changed_at"] = now_iso()
            users[username] = user
            save_users(users)
        token = secrets.token_urlsafe(32)
        refresh = secrets.token_urlsafe(48)
        session = create_runtime_session(username, user)
        SESSIONS[token] = session
        db_store_session(token, refresh, session, request)
        db_mark_login(username)
        record_login_success(username, request)
        account_status = normalize_status(user.get("status", "active"))
        if account_status == "active":
            update_login_karma(username)
        audit_status = "OK" if account_status == "active" else account_status.upper()
        append_login_audit(username, audit_status, request)
        audit_event(username, "auth.login", username, audit_status, request)
        response.set_cookie("nexus_refresh", refresh, httponly=True, secure=False, samesite="lax", max_age=60 * 60 * 24 * 30)
        log_event(f"LOGIN {audit_status}: {username}")
        return auth_payload(username, user, token)
    record_login_failure(username, request)
    append_login_audit(username, "FAIL", request)
    audit_event(username, "auth.login", username, "FAIL", request)
    log_event(f"LOGIN FAIL: {username}")
    raise HTTPException(status_code=401)

@app.get("/api/auth/me")
async def auth_me(user = Depends(verify_session)):
    username = user.get("username", "")
    data = load_users().get(username, user)
    return {"status": "success", "account_status": normalize_status(data.get("status", user.get("status", "active"))), "user": public_user(username, data)}

@app.get("/api/auth/status")
async def auth_status(user = Depends(verify_session)):
    username = user.get("username", "")
    data = load_users().get(username, user)
    return {"username": username, "role": normalize_role(data.get("role", user.get("role", "user"))), "account_status": normalize_status(data.get("status", user.get("status", "active")))}

@app.post("/api/auth/refresh")
async def auth_refresh(request: Request, response: Response, x_auth_token: str = Header(None)):
    if x_auth_token and x_auth_token in SESSIONS:
        session = sync_session_user(SESSIONS[x_auth_token])
        data = load_users().get(session.get("username", ""), session)
        return auth_payload(session.get("username", ""), data, x_auth_token)
    refresh = request.cookies.get("nexus_refresh", "")
    row = db_find_refresh_session(refresh)
    if not row:
        raise HTTPException(status_code=401, detail="Brak waznej sesji odswiezania")
    username = row.get("username", "")
    data = load_users().get(username)
    if not data or normalize_status(data.get("status", "active")) == "deleted":
        raise HTTPException(status_code=401, detail="Sesja wygasla")
    token = secrets.token_urlsafe(32)
    new_refresh = secrets.token_urlsafe(48)
    session = create_runtime_session(username, data)
    SESSIONS[token] = session
    db_store_session(token, new_refresh, session, request)
    response.set_cookie("nexus_refresh", new_refresh, httponly=True, secure=False, samesite="lax", max_age=60 * 60 * 24 * 30)
    return auth_payload(username, data, token)

@app.post("/api/auth/logout")
async def auth_logout(response: Response, x_auth_token: str = Header(None), user = Depends(verify_session)):
    token = x_auth_token or ""
    SESSIONS.pop(token, None)
    db_revoke_session(token)
    response.delete_cookie("nexus_refresh")
    audit_event(user.get("username"), "auth.logout", user.get("username"), "OK", None)
    return {"status": "success"}

@app.get("/api/admin/users")
async def list_admin_users(admin = Depends(verify_admin)):
    users = load_users()
    return [public_user(username, data) for username, data in sorted(users.items())]

@app.get("/api/admin/users/")
async def list_admin_users_slash(admin = Depends(verify_admin)):
    return await list_admin_users(admin)

@app.get("/api/admin/users/pending")
async def list_pending_users(admin = Depends(verify_admin)):
    users = load_users()
    return [public_user(username, data) for username, data in sorted(users.items()) if normalize_status(data.get("status")) == "pending"]

@app.get("/api/admin/login-audit")
async def login_audit(admin = Depends(verify_admin)):
    rows = db_fetch_audit(120, login_only=True)
    if rows is not None:
        return rows
    return read_json(LOGIN_AUDIT_FILE, [])[:120]

@app.get("/api/admin/audit-log")
async def full_audit_log(admin = Depends(verify_admin)):
    rows = db_fetch_audit(200, login_only=False)
    if rows is not None:
        return rows
    return read_json(LOGIN_AUDIT_FILE, [])[:200]

def assert_not_last_active_admin(users, username, next_role=None, next_status=None):
    current = users.get(username, {})
    future_role = normalize_role(next_role if next_role is not None else current.get("role", "user"))
    future_status = normalize_status(next_status if next_status is not None else current.get("status", "active"))
    count = 0
    for name, data in users.items():
        role = future_role if name == username else normalize_role(data.get("role", "user"))
        status = future_status if name == username else normalize_status(data.get("status", "active"))
        if role == "admin" and status == "active":
            count += 1
    if count < 1:
        raise HTTPException(status_code=409, detail="Nie mozna usunac ostatniego aktywnego admina")

def set_user_status(username, status, admin, request: Request):
    username = normalize_username(username)
    status = normalize_status(status)
    users = load_users()
    if username not in users:
        raise HTTPException(status_code=404, detail="Brak uzytkownika")
    assert_not_last_active_admin(users, username, next_status=status)
    user = users[username]
    user["status"] = status
    user["updated_at"] = now_iso()
    actor = admin.get("username", "admin")
    if status == "active":
        user["approved_at"] = user.get("approved_at") or now_iso()
        user["approved_by"] = actor
    elif status == "rejected":
        user["rejected_at"] = now_iso()
        user["rejected_by"] = actor
        db_revoke_user_sessions(username)
    elif status == "suspended":
        user["suspended_at"] = now_iso()
        user["suspended_by"] = actor
        db_revoke_user_sessions(username)
    elif status in {"pending", "deleted"}:
        db_revoke_user_sessions(username)
    users[username] = user
    save_users(users)
    audit_event(actor, f"iam.user.{status}", username, "OK", request)
    log_event(f"IAM STATUS {username} -> {status} by={actor}")
    return public_user(username, user)

@app.post("/api/admin/users/create")
async def create_admin_user(data: UserCreateRequest, request: Request, admin = Depends(verify_admin)):
    username = normalize_username(data.username)
    role = normalize_role(data.role)
    users = load_users()
    if username in users:
        raise HTTPException(status_code=409, detail="Uzytkownik juz istnieje")
    users[username] = {
        "username": username,
        "role": role,
        "status": "active",
        "password_hash": hash_password(data.password),
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "approved_at": now_iso(),
        "approved_by": admin.get("username", "admin"),
    }
    save_users(users)
    audit_event(admin.get("username"), "iam.user.create", username, "OK", request, {"role": role})
    log_event(f"USER CREATE: {username} role={role} by={admin.get('username')}")
    return public_user(username, users[username])

@app.post("/api/admin/users/password")
async def change_admin_user_password(data: UserPasswordRequest, request: Request, admin = Depends(verify_admin)):
    username = normalize_username(data.username)
    users = load_users()
    if username not in users:
        raise HTTPException(status_code=404, detail="Brak uzytkownika")
    users[username]["password_hash"] = hash_password(data.password)
    users[username]["password_changed_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    save_users(users)
    db_revoke_user_sessions(username)
    audit_event(admin.get("username"), "iam.user.password", username, "OK", request)
    log_event(f"USER PASSWORD: {username} by={admin.get('username')}")
    return {"status": "success", "username": username}

@app.post("/api/admin/users/{username}/approve")
async def approve_user(username: str, request: Request, admin = Depends(verify_admin)):
    return set_user_status(username, "active", admin, request)

@app.post("/api/admin/users/{username}/reject")
async def reject_user(username: str, request: Request, admin = Depends(verify_admin)):
    return set_user_status(username, "rejected", admin, request)

@app.post("/api/admin/users/{username}/suspend")
async def suspend_user(username: str, request: Request, admin = Depends(verify_admin)):
    return set_user_status(username, "suspended", admin, request)

@app.post("/api/admin/users/{username}/activate")
async def activate_user(username: str, request: Request, admin = Depends(verify_admin)):
    return set_user_status(username, "active", admin, request)

@app.post("/api/admin/users/{username}/role")
async def change_user_role(username: str, data: UserRoleRequest, request: Request, admin = Depends(verify_admin)):
    username = normalize_username(username)
    role = normalize_role(data.role)
    users = load_users()
    if username not in users:
        raise HTTPException(status_code=404, detail="Brak uzytkownika")
    assert_not_last_active_admin(users, username, next_role=role)
    users[username]["role"] = role
    users[username]["updated_at"] = now_iso()
    save_users(users)
    db_revoke_user_sessions(username)
    audit_event(admin.get("username"), "iam.user.role", username, "OK", request, {"role": role})
    log_event(f"IAM ROLE {username} -> {role} by={admin.get('username')}")
    return public_user(username, users[username])


NEWS_SOURCES = [
    {"id": "rmf24", "name": "RMF24", "category": "POLSKA", "url": "https://www.rmf24.pl/feed"},
    {"id": "polsat", "name": "Polsat News", "category": "POLSKA", "url": "https://www.polsatnews.pl/rss/wszystkie.xml"},
    {"id": "tvn24", "name": "TVN24", "category": "POLSKA", "url": "https://tvn24.pl/najnowsze.xml"},
    {"id": "pap", "name": "PAP", "category": "POLSKA", "url": "https://www.pap.pl/rss.xml"},
    {"id": "bbc_world", "name": "BBC World", "category": "SWIAT", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"id": "dw_world", "name": "DW", "category": "SWIAT", "url": "https://rss.dw.com/rdf/rss-en-world"},
    {"id": "nyt_world", "name": "NYT World", "category": "SWIAT", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"},
    {"id": "guardian_world", "name": "Guardian World", "category": "SWIAT", "url": "https://www.theguardian.com/world/rss"},
    {"id": "niebezpiecznik", "name": "Niebezpiecznik", "category": "CYBER", "url": "https://niebezpiecznik.pl/feed/"},
    {"id": "sekurak", "name": "Sekurak", "category": "CYBER", "url": "https://sekurak.pl/feed/"},
    {"id": "thehackernews", "name": "The Hacker News", "category": "CYBER", "url": "https://feeds.feedburner.com/TheHackersNews"},
    {"id": "hn", "name": "Hacker News", "category": "TECH", "url": "https://hnrss.org/frontpage"},
    {"id": "ars", "name": "Ars Technica", "category": "TECH", "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"id": "bbc_video", "name": "BBC News Video", "category": "VIDEO", "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UC16niRr50-MSBwiO3YDb3RA"},
    {"id": "dw_video", "name": "DW News Video", "category": "VIDEO", "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCknLrEdhRCp1aegoMqRaCZg"},
    {"id": "france24_video", "name": "France24 Video", "category": "VIDEO", "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCQfwfsi5VrQ8yKZ-UWmAEFg"},
    {"id": "aljazeera_video", "name": "Al Jazeera Video", "category": "VIDEO", "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCNye-wNBqNL5ZzHSJj3l8Bg"},
]

def xml_local(tag: str):
    return str(tag).split("}", 1)[-1].lower()

def child_text(node, *names):
    wanted = {name.lower() for name in names}
    for child in list(node):
        if xml_local(child.tag) in wanted and child.text:
            return html.unescape(child.text.strip())
    return ""

def first_attr(node, local_name: str, attr_name: str):
    for child in node.iter():
        if xml_local(child.tag) == local_name and child.attrib.get(attr_name):
            return child.attrib.get(attr_name, "").strip()
    return ""

def strip_html(value: str):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def parse_news_time(value: str):
    if not value:
        return 0
    try:
        return int(email.utils.parsedate_to_datetime(value).timestamp())
    except Exception:
        try:
            return int(datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())
        except Exception:
            return 0

def youtube_embed(link: str):
    try:
        parsed = urllib.parse.urlparse(link or "")
        host = parsed.netloc.lower()
        vid = ""
        if "youtu.be" in host:
            vid = parsed.path.strip("/").split("/")[0]
        elif "youtube.com" in host:
            if parsed.path.startswith("/watch"):
                vid = urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
            elif "/shorts/" in parsed.path or "/embed/" in parsed.path:
                vid = parsed.path.rstrip("/").split("/")[-1]
        return f"https://www.youtube-nocookie.com/embed/{vid}" if vid else ""
    except Exception:
        return ""

def extract_news_media(node, link: str):
    image = ""
    video_url = ""
    for child in node.iter():
        local = xml_local(child.tag)
        ctype = (child.attrib.get("type") or "").lower()
        medium = (child.attrib.get("medium") or "").lower()
        url = (child.attrib.get("url") or child.attrib.get("href") or "").strip()
        if local == "thumbnail" and url and not image:
            image = url
        if local in ["content", "enclosure"] and url:
            if ctype.startswith("image/") and not image:
                image = url
            if ctype.startswith("video/") or medium == "video":
                video_url = url
    embed_url = youtube_embed(link) or youtube_embed(video_url)
    return image, video_url, embed_url

def parse_feed_items(source, raw):
    root = ET.fromstring(raw)
    nodes = root.findall(".//item")
    if not nodes:
        nodes = [node for node in root.iter() if xml_local(node.tag) == "entry"]
    parsed = []
    for node in nodes[:35]:
        title = child_text(node, "title")
        link = child_text(node, "link")
        if not link:
            for child in list(node):
                if xml_local(child.tag) == "link" and child.attrib.get("href"):
                    link = child.attrib.get("href", "").strip()
                    break
        published = child_text(node, "pubDate", "published", "updated")
        description = strip_html(child_text(node, "description", "summary", "content", "encoded"))
        image, video_url, embed_url = extract_news_media(node, link)
        if not image:
            image = first_attr(node, "image", "href") or first_attr(node, "thumbnail", "url")
        if title and link:
            parsed.append({
                "title": title,
                "link": link,
                "published": published,
                "pubDate": published,
                "timestamp": parse_news_time(published),
                "description": description[:420],
                "source": source["name"],
                "source_id": source["id"],
                "category": source["category"],
                "image": image,
                "video_url": video_url,
                "embed_url": embed_url,
                "type": "video" if embed_url or source["category"] == "VIDEO" else "article",
            })
    return parsed

@app.get("/api/news")
async def get_news(source: str = "ALL", limit: int = 80, video: int = 0):
    selected = (source or "ALL").upper()
    limit = max(10, min(int(limit or 80), 160))
    sources = [
        item for item in NEWS_SOURCES
        if selected == "ALL" or item["category"] == selected or item["id"].upper() == selected
    ]
    if video:
        sources = [item for item in sources if item["category"] == "VIDEO"] or [item for item in NEWS_SOURCES if item["category"] == "VIDEO"]
    items = []
    for src in sources:
        try:
            request = urllib.request.Request(src["url"], headers={"User-Agent": "NEXUS/2.0 (+https://nexusos.pl)"})
            with urllib.request.urlopen(request, timeout=7) as response:
                items.extend(parse_feed_items(src, response.read()))
        except Exception as exc:
            log_event(f"NEWS ERROR {src['id']}: {exc}")
    deduped = {}
    for item in items:
        key = item.get("link") or item.get("title")
        if key and key not in deduped:
            deduped[key] = item
    rows = list(deduped.values())
    if video:
        rows = [item for item in rows if item.get("type") == "video" or item.get("embed_url") or item.get("video_url")]
    rows.sort(key=lambda item: item.get("timestamp") or 0, reverse=True)
    return rows[:limit]

def weather_code_label(code):
    labels = {
        0: "clear",
        1: "mainly_clear",
        2: "partly_cloudy",
        3: "overcast",
        45: "fog",
        48: "rime_fog",
        51: "light_drizzle",
        53: "drizzle",
        55: "heavy_drizzle",
        61: "light_rain",
        63: "rain",
        65: "heavy_rain",
        71: "light_snow",
        73: "snow",
        75: "heavy_snow",
        80: "rain_showers",
        81: "heavy_showers",
        82: "violent_showers",
        95: "thunderstorm",
        96: "thunderstorm_hail",
        99: "heavy_thunderstorm_hail",
    }
    try:
        return labels.get(int(code), f"code_{code}")
    except Exception:
        return "unknown"

def fetch_json_url(url: str, timeout: int = 10):
    req = urllib.request.Request(url, headers={"User-Agent": "NEXUS-OSINT/2.0 (+https://nexusos.pl)"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="ignore"))

def weather_report(city: str):
    query = (city or "Warszawa").strip()[:120] or "Warszawa"
    geo_url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode({
        "name": query,
        "count": 1,
        "language": "pl",
        "format": "json",
    })
    geo = fetch_json_url(geo_url)
    rows = geo.get("results") or []
    if not rows:
        raise HTTPException(status_code=404, detail=f"Nie znaleziono lokalizacji: {query}")
    place = rows[0]
    lat = place.get("latitude")
    lon = place.get("longitude")
    forecast_url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,cloud_cover,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max",
        "timezone": "auto",
        "forecast_days": 3,
    })
    forecast = fetch_json_url(forecast_url)
    current = forecast.get("current") or {}
    hourly = forecast.get("hourly") or {}
    daily = forecast.get("daily") or {}
    precipitation = float(current.get("precipitation") or 0)
    humidity = float(current.get("relative_humidity_2m") or 0)
    cloud = float(current.get("cloud_cover") or 0)
    pressure = float(current.get("pressure_msl") or 0)
    rain_signal = precipitation > 0 or any((value or 0) for value in (daily.get("precipitation_sum") or [])[:1])
    acid_score = 0
    acid_score += 35 if rain_signal else 0
    acid_score += 25 if humidity >= 80 else 0
    acid_score += 20 if cloud >= 70 else 0
    acid_score += 20 if pressure and pressure < 1005 else 0
    acid_score = min(100, acid_score)
    risk = "high" if acid_score >= 70 else "medium" if acid_score >= 40 else "low"
    next_hours = []
    for idx, time_label in enumerate((hourly.get("time") or [])[:12]):
        next_hours.append({
            "time": time_label,
            "temperature_2m": (hourly.get("temperature_2m") or [None])[idx] if idx < len(hourly.get("temperature_2m") or []) else None,
            "humidity": (hourly.get("relative_humidity_2m") or [None])[idx] if idx < len(hourly.get("relative_humidity_2m") or []) else None,
            "precipitation_probability": (hourly.get("precipitation_probability") or [None])[idx] if idx < len(hourly.get("precipitation_probability") or []) else None,
            "weather": weather_code_label((hourly.get("weather_code") or [None])[idx] if idx < len(hourly.get("weather_code") or []) else None),
        })
    return {
        "source": "Open-Meteo",
        "query": query,
        "place": {
            "name": place.get("name"),
            "country": place.get("country"),
            "admin1": place.get("admin1"),
            "latitude": lat,
            "longitude": lon,
            "timezone": forecast.get("timezone"),
        },
        "current": {
            **current,
            "weather_label": weather_code_label(current.get("weather_code")),
        },
        "daily": daily,
        "next_12h": next_hours,
        "osint": {
            "atmospheric_risk": risk,
            "acid_rain_heuristic_score": acid_score,
            "note": "Heurystyka OSINT: Open-Meteo nie podaje chemii opadow. Score laczy opad, wilgotnosc, zachmurzenie i niskie cisnienie.",
        },
        "fetched_at": now_iso(),
    }

@app.get("/api/weather", dependencies=[Depends(verify_token)])
async def get_weather(city: str = "Warszawa"):
    return weather_report(city)

@app.get("/api/osint/atmospheric", dependencies=[Depends(verify_token)])
async def get_atmospheric_osint(city: str = "Warszawa"):
    return weather_report(city)

def capsule_available_bytes():
    stat = os.statvfs(str(LIBVIRT_IMAGE_DIR))
    return int(stat.f_bavail * stat.f_frsize)

def capsule_required_bytes(manifest: CapsuleManifest):
    total = sum(max(0, int(item.size_bytes or 0)) for item in manifest.storage)
    return total or 1024 * 1024 * 1024

def capsule_warning_list(manifest: CapsuleManifest, available: int):
    warnings = []
    if manifest.schema_version not in {"1", "v1"}:
        warnings.append("schema_version powinno byc '1' albo 'v1'")
    if manifest.architecture.lower() not in {"x86_64", "amd64"}:
        warnings.append("Host KVM jest x86_64; inna architektura moze nie wystartowac")
    if manifest.network_bridge != "nexus-default":
        warnings.append("Import uzyje manifest.network_bridge, ale standardem NEXUS jest nexus-default")
    for item in manifest.storage:
        if item.format.lower() != "qcow2":
            warnings.append(f"{item.path}: format {item.format} wymaga konwersji; importer v1 przyjmuje qcow2")
        if item.path.lower().endswith(".xml"):
            warnings.append("XML z kapsuly jest zabroniony i nie zostanie przyjety")
    if available < capsule_required_bytes(manifest) + 4 * 1024 * 1024 * 1024:
        warnings.append("Malo miejsca: wymagany dysk plus 4 GB rezerwy nie miesci sie w libvirt images")
    return warnings

def inspect_capsule_manifest(manifest: CapsuleManifest):
    available = capsule_available_bytes()
    required = capsule_required_bytes(manifest)
    warnings = capsule_warning_list(manifest, available)
    valid = not any("zabroniony" in item or "format" in item for item in warnings)
    return InspectResponse(
        valid=valid,
        capsule_id=manifest.capsule_id or safe_domain_name(manifest.name),
        required_bytes=required,
        available_bytes=available,
        fits=available >= required + 4 * 1024 * 1024 * 1024,
        warnings=warnings,
        normalized_manifest=manifest.model_dump(),
    )

def capsule_upload_record(upload_id: str):
    record = CAPSULE_UPLOADS.get(upload_id)
    if record:
        return record
    target = CAPSULE_UPLOAD_DIR / f"{safe_upload_filename(upload_id)}.nexus"
    if target.exists():
        return {"id": upload_id, "path": str(target), "status": "complete", "filename": target.name, "size": target.stat().st_size}
    raise HTTPException(status_code=404, detail="Nie znaleziono uploadu kapsuly")

def capsule_safe_zip_member(info: zipfile.ZipInfo):
    name = info.filename.replace("\\", "/")
    parts = [part for part in name.split("/") if part]
    if not parts or name.startswith("/") or ".." in parts:
        raise HTTPException(status_code=400, detail=f"Niebezpieczna sciezka w kapsule: {info.filename}")
    mode = (info.external_attr >> 16) & 0o170000
    if mode == 0o120000:
        raise HTTPException(status_code=400, detail=f"Symlink w kapsule jest zabroniony: {info.filename}")
    return "/".join(parts)

def load_capsule_manifest_from_zip(path: Path):
    with zipfile.ZipFile(path) as zf:
        try:
            with zf.open("nexus_manifest.json") as src:
                raw = src.read(1024 * 1024)
        except KeyError:
            raise HTTPException(status_code=400, detail="Brak nexus_manifest.json w kapsule")
    return CapsuleManifest(**json.loads(raw.decode("utf-8")))

def validate_capsule_zip(path: Path):
    manifest = load_capsule_manifest_from_zip(path)
    disk_paths = {item.path.replace("\\", "/").strip("/") for item in manifest.storage}
    allowed = {"nexus_manifest.json", manifest.thumbnail_path.replace("\\", "/").strip("/"), *disk_paths}
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = capsule_safe_zip_member(info)
            if name.lower().endswith(".xml"):
                raise HTTPException(status_code=400, detail="Kapsula nie moze zawierac XML; NEXUS generuje XML sam")
            if name not in allowed:
                raise HTTPException(status_code=400, detail=f"Nieznany plik w kapsule v1: {name}")
    return manifest

def extract_capsule_zip(path: Path, target_dir: Path, manifest: CapsuleManifest):
    target_dir.mkdir(parents=True, exist_ok=True)
    disk_paths = {item.path.replace("\\", "/").strip("/") for item in manifest.storage}
    allowed = {"nexus_manifest.json", manifest.thumbnail_path.replace("\\", "/").strip("/"), *disk_paths}
    extracted = {}
    root = target_dir.resolve()
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = capsule_safe_zip_member(info)
            if name not in allowed or name.lower().endswith(".xml"):
                raise HTTPException(status_code=400, detail=f"Odrzucono plik kapsuly: {name}")
            out = (root / name).resolve()
            if out != root and root not in out.parents:
                raise HTTPException(status_code=400, detail=f"Path traversal w kapsule: {name}")
            out.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted[name] = out
    return extracted

async def run_async_process(args, timeout=120):
    proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        raise HTTPException(status_code=504, detail=f"Timeout komendy: {' '.join(args)}")
    output = (stdout or b"").decode(errors="ignore") + (stderr or b"").decode(errors="ignore")
    return proc.returncode, output

def capsule_mac_address():
    raw = secrets.token_bytes(3)
    return "52:54:00:%02x:%02x:%02x" % (raw[0], raw[1], raw[2])

def capsule_domain_xml(manifest: CapsuleManifest, name: str, disk: Path):
    bridge = re.sub(r"[^A-Za-z0-9_.:-]+", "", manifest.network_bridge or "nexus-default") or "nexus-default"
    memory = int(manifest.memory_mb)
    vcpus = int(manifest.vcpus)
    mac = capsule_mac_address()
    disk_path = html.escape(str(disk), quote=True)
    domain_name = html.escape(name, quote=True)
    bridge_name = html.escape(bridge, quote=True)
    bus = "virtio"
    return f"""<domain type='kvm'>
  <name>{domain_name}</name>
  <memory unit='MiB'>{memory}</memory>
  <currentMemory unit='MiB'>{memory}</currentMemory>
  <vcpu placement='static'>{vcpus}</vcpu>
  <os>
    <type arch='x86_64' machine='pc'>hvm</type>
    <boot dev='hd'/>
  </os>
  <features><acpi/><apic/></features>
  <cpu mode='host-passthrough' check='none'/>
  <clock offset='utc'/>
  <on_poweroff>destroy</on_poweroff>
  <on_reboot>restart</on_reboot>
  <on_crash>restart</on_crash>
  <devices>
    <emulator>/usr/bin/qemu-system-x86_64</emulator>
    <disk type='file' device='disk'>
      <driver name='qemu' type='qcow2' cache='none' io='native'/>
      <source file='{disk_path}'/>
      <target dev='vda' bus='{bus}'/>
    </disk>
    <interface type='bridge'>
      <mac address='{mac}'/>
      <source bridge='{bridge_name}'/>
      <model type='virtio'/>
    </interface>
    <graphics type='vnc' port='-1' listen='127.0.0.1'>
      <listen type='address' address='127.0.0.1'/>
    </graphics>
    <video><model type='qxl'/></video>
    <input type='tablet' bus='usb'/>
    <channel type='unix'>
      <target type='virtio' name='org.qemu.guest_agent.0'/>
    </channel>
  </devices>
</domain>"""

def capsule_job_update(job_id: str, status: str, progress: int, message: str = "", **extra):
    job = CAPSULE_JOBS.setdefault(job_id, {"id": job_id, "created_at": now_iso()})
    job.update({"status": status, "progress": progress, "message": message, "updated_at": now_iso(), **extra})
    return job

async def capsule_import_job(job_id: str, upload_id: str, username: str):
    tmp = CAPSULE_TEMP_DIR / job_id
    target_disk = None
    domain_name = ""
    try:
        record = capsule_upload_record(upload_id)
        capsule_path = Path(record["path"]).resolve()
        capsule_job_update(job_id, "extracting", 10, "Waliduje i rozpakowuje kapsule")
        manifest = validate_capsule_zip(capsule_path)
        inspected = inspect_capsule_manifest(manifest)
        if not inspected.valid or not inspected.fits:
            raise HTTPException(status_code=400, detail={"inspect": inspected.model_dump(), "message": "Pre-flight check nie przeszedl"})
        extracted = extract_capsule_zip(capsule_path, tmp, manifest)
        disk_item = next((item for item in manifest.storage if item.boot), manifest.storage[0])
        disk_source = extracted.get(disk_item.path.replace("\\", "/").strip("/"))
        if not disk_source or not disk_source.exists():
            raise HTTPException(status_code=400, detail="Brak dysku boot w kapsule")
        capsule_job_update(job_id, "verifying", 42, "Sprawdzam qcow2 przez qemu-img check")
        if not shutil.which("qemu-img"):
            raise HTTPException(status_code=500, detail="Brak qemu-img na hoście")
        code, output = await run_async_process(["qemu-img", "check", str(disk_source)], timeout=300)
        if code != 0:
            raise HTTPException(status_code=400, detail=f"qemu-img check odrzucil dysk: {output[-1200:]}")
        domain_name = safe_domain_name(manifest.name)
        target_disk = (LIBVIRT_IMAGE_DIR / f"{domain_name}.qcow2").resolve()
        if target_disk.exists():
            raise HTTPException(status_code=409, detail=f"Dysk docelowy juz istnieje: {target_disk.name}")
        disk_budget_bytes = max(int(disk_item.size_bytes or 0), int(disk_source.stat().st_size))
        ensure_vm_disk_capacity(max(1, int(disk_budget_bytes / 1024 / 1024 / 1024) + 1), domain_name)
        ensure_libvirt_file_access(LIBVIRT_IMAGE_DIR, is_dir=True)
        shutil.move(str(disk_source), str(target_disk))
        ensure_libvirt_file_access(target_disk)
        capsule_job_update(job_id, "defining", 72, "Generuje bezpieczny XML libvirt")
        xml_path = tmp / f"{domain_name}.xml"
        xml_path.write_text(capsule_domain_xml(manifest, domain_name, target_disk), encoding="utf-8")
        if not shutil.which("virsh"):
            raise HTTPException(status_code=500, detail="Brak virsh/libvirt na hoście")
        code, output = await run_async_process(["virsh", "define", str(xml_path)], timeout=60)
        if code != 0:
            raise HTTPException(status_code=500, detail=f"virsh define nie przeszedl: {output[-1200:]}")
        if manifest.start_after_import:
            code, output = await run_async_process(["virsh", "start", domain_name], timeout=60)
            if code != 0:
                raise HTTPException(status_code=500, detail=f"VM zdefiniowana, ale start nie przeszedl: {output[-1200:]}")
        capsule_job_update(job_id, "active", 100, "Kapsula zaimportowana", vm_id=domain_name, disk=str(target_disk), owner=username)
        log_event(f"CAPSULE_IMPORT ok upload={upload_id} vm={domain_name} by={username}")
    except Exception as exc:
        detail = getattr(exc, "detail", str(exc))
        if domain_name:
            try:
                run_vm_command(["virsh", "undefine", domain_name, "--nvram"], timeout=20)
            except Exception:
                pass
        if target_disk and Path(target_disk).exists():
            try:
                Path(target_disk).unlink()
            except Exception:
                pass
        capsule_job_update(job_id, "failed", 100, str(detail)[:1000], error=detail)
        log_event(f"CAPSULE_IMPORT failed upload={upload_id} err={detail}")
    finally:
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass

@app.get("/api/v1/capsules/status", dependencies=[Depends(verify_token)])
async def capsules_status():
    return {
        "uploads": sorted(CAPSULE_UPLOADS.values(), key=lambda row: row.get("created_at", ""), reverse=True)[:50],
        "jobs": sorted(CAPSULE_JOBS.values(), key=lambda row: row.get("created_at", ""), reverse=True)[:50],
        "upload_dir": str(CAPSULE_UPLOAD_DIR),
        "libvirt_image_dir": str(LIBVIRT_IMAGE_DIR),
    }

@app.post("/api/v1/capsules/inspect", response_model=InspectResponse, dependencies=[Depends(verify_token)])
async def capsules_inspect(manifest: CapsuleManifest):
    return inspect_capsule_manifest(manifest)

@app.post("/uploads", dependencies=[Depends(verify_admin)])
async def capsule_upload_init(data: UploadInitRequest, admin = Depends(verify_admin)):
    filename = safe_upload_filename(data.filename)
    if not filename.lower().endswith(".nexus"):
        filename += ".nexus"
    upload_id = uuid.uuid4().hex[:16]
    part_dir = CAPSULE_UPLOAD_DIR / upload_id
    part_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "id": upload_id,
        "filename": filename,
        "size": int(data.size),
        "sha256": data.sha256.strip().lower(),
        "manifest": data.manifest or {},
        "part_dir": str(part_dir),
        "path": str(CAPSULE_UPLOAD_DIR / f"{upload_id}.nexus"),
        "parts": [],
        "status": "open",
        "created_by": admin.get("username", "admin"),
        "created_at": now_iso(),
    }
    CAPSULE_UPLOADS[upload_id] = record
    return {"upload_id": upload_id, "part_size": 64 * 1024 * 1024, "status": "open", "parts_url": f"/uploads/{upload_id}/parts/{{number}}"}

@app.put("/uploads/{upload_id}/parts/{number}", dependencies=[Depends(verify_admin)])
async def capsule_upload_part(upload_id: str, number: int, request: Request):
    if number < 1 or number > 100000:
        raise HTTPException(status_code=400, detail="Niepoprawny numer czesci")
    record = capsule_upload_record(upload_id)
    if record.get("status") == "complete":
        raise HTTPException(status_code=409, detail="Upload jest juz zamkniety")
    part_dir = Path(record["part_dir"])
    part_dir.mkdir(parents=True, exist_ok=True)
    part_path = part_dir / f"{number:08d}.part"
    size = 0
    digest = hashlib.sha256()
    with open(part_path, "wb") as out:
        async for chunk in request.stream():
            if not chunk:
                continue
            size += len(chunk)
            digest.update(chunk)
            out.write(chunk)
    parts = set(record.get("parts", []))
    parts.add(number)
    record["parts"] = sorted(parts)
    record["updated_at"] = now_iso()
    return {"status": "part_saved", "upload_id": upload_id, "part": number, "size": size, "sha256": digest.hexdigest(), "parts": record["parts"]}

@app.post("/uploads/{upload_id}/complete", dependencies=[Depends(verify_admin)])
async def capsule_upload_complete(upload_id: str, data: UploadCompleteRequest):
    record = capsule_upload_record(upload_id)
    if record.get("status") == "complete":
        return {"status": "complete", "upload_id": upload_id, "path": record["path"]}
    part_dir = Path(record["part_dir"])
    parts = data.parts or sorted(record.get("parts", []))
    if not parts:
        raise HTTPException(status_code=400, detail="Brak czesci uploadu")
    target = Path(record["path"])
    digest = hashlib.sha256()
    total = 0
    with open(target, "wb") as out:
        for number in sorted(parts):
            part_path = part_dir / f"{int(number):08d}.part"
            if not part_path.exists():
                raise HTTPException(status_code=400, detail=f"Brakuje czesci {number}")
            with open(part_path, "rb") as src:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    total += len(chunk)
                    out.write(chunk)
    actual = digest.hexdigest()
    expected = (data.sha256 or record.get("sha256") or "").strip().lower()
    if expected and expected != actual:
        try:
            target.unlink()
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="SHA256 kapsuly nie pasuje")
    validate_capsule_zip(target)
    record.update({"status": "complete", "path": str(target), "size_written": total, "sha256_actual": actual, "completed_at": now_iso()})
    shutil.rmtree(part_dir, ignore_errors=True)
    log_event(f"CAPSULE_UPLOAD complete id={upload_id} size={total}")
    return {"status": "complete", "upload_id": upload_id, "path": str(target), "size": total, "sha256": actual}

@app.post("/api/v1/capsules/{capsule_id}/import", dependencies=[Depends(verify_admin)])
async def capsule_import(capsule_id: str, background_tasks: BackgroundTasks, admin = Depends(verify_admin)):
    record = capsule_upload_record(capsule_id)
    if record.get("status") != "complete":
        raise HTTPException(status_code=409, detail="Upload kapsuly nie jest kompletny")
    job_id = uuid.uuid4().hex[:16]
    capsule_job_update(job_id, "pending", 0, "Import oczekuje w kolejce", upload_id=capsule_id)
    background_tasks.add_task(capsule_import_job, job_id, capsule_id, admin.get("username", "admin"))
    return {"job_id": job_id, "status": "pending", "upload_id": capsule_id}

@app.get("/api/v1/jobs/{job_id}", dependencies=[Depends(verify_token)])
async def capsule_job_status(job_id: str):
    job = CAPSULE_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Nie znaleziono joba")
    return job

# --- SZTUCZNA INTELIGENCJA (2.5 FLASH) ---
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

@app.post("/api/ai/chat", dependencies=[Depends(verify_token)])
async def ai_chat(data: dict):
    key = GEMINI_KEY_FILE.read_text().strip()
    if not key: return {"reply": "⚠️ Brak klucza w 'gemini_key.txt'."}
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f: lc = "".join(f.readlines()[-15:])
    except: lc = ""
    prompt = f"Jesteś NEXUS AI. Bądź krótki i techniczny. Logi:\n{lc}\n\nPytanie: {data.get('message')}"
    url = f"{GEMINI_URL}?key={key}"
    payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            return {"reply": json.loads(response.read().decode())["candidates"][0]["content"]["parts"][0]["text"]}
    except Exception as e: return {"reply": f"Błąd: {str(e)}"}

# --- SYSTEM ENDPOINTS ---
@app.get("/api/system/stats", dependencies=[Depends(verify_token)])
async def get_system_stats():
    disk = shutil.disk_usage(str(BASE_DIR))
    disk_used = disk.total - disk.free
    uptime_seconds = 0
    try:
        uptime_seconds = int(float(Path("/proc/uptime").read_text().split()[0]))
    except Exception:
        pass
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    uptime = f"{days}d {hours}h {minutes}m" if days else f"{hours}h {minutes}m"

    stats = {
        "os": f"{platform.system()} {platform.release()}",
        "uptime": uptime,
        "server_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_cores": os.cpu_count() or 1,
        "load_avg": "",
        "cpu": 0,
        "ram_percent": 0,
        "ram_used": 0,
        "ram_total": 0,
        "disk_percent": round(((disk.total - disk.free) / disk.total) * 100, 1) if disk.total else 0,
        "disk_used_label": fmt_size(disk_used),
        "disk_free_label": fmt_size(disk.free),
        "disk_total_label": fmt_size(disk.total),
        "process_count": 0,
        "active_sessions": len(SESSIONS),
        "app_base": str(BASE_DIR),
    }
    try:
        stats["load_avg"] = " / ".join(f"{value:.2f}" for value in os.getloadavg())
    except Exception:
        stats["load_avg"] = "n/a"
    if HAS_PSUTIL:
        memory = psutil.virtual_memory()
        stats.update({
            "cpu": psutil.cpu_percent(interval=0.1),
            "ram_percent": memory.percent,
            "ram_used": round(memory.used / (1024**3), 2),
            "ram_total": round(memory.total / (1024**3), 2),
            "process_count": len(psutil.pids()),
        })
    else:
        try:
            meminfo = {}
            for line in Path("/proc/meminfo").read_text().splitlines():
                key, value = line.split(":", 1)
                meminfo[key] = int(value.strip().split()[0])
            total = meminfo["MemTotal"] * 1024
            available = meminfo.get("MemAvailable", meminfo.get("MemFree", 0)) * 1024
            used = total - available
            stats.update({
                "cpu": round(min(os.getloadavg()[0] / max(os.cpu_count() or 1, 1) * 100, 100), 1),
                "ram_percent": round(used / total * 100, 1) if total else 0,
                "ram_used": round(used / (1024**3), 2),
                "ram_total": round(total / (1024**3), 2),
            })
            stats["process_count"] = len([p for p in Path("/proc").iterdir() if p.name.isdigit()])
        except Exception as exc:
            log_event(f"STATS ERROR: {exc}")
    return stats

@app.get("/api/system/network", dependencies=[Depends(verify_token)])
async def get_network():
    try:
        addresses = subprocess.check_output(["hostname", "-I"], text=True, timeout=2).split()
        addresses = [address for address in addresses if not address.startswith("127.")]
        return {"network": ", ".join(addresses) or "127.0.0.1 (Lokalnie)"}
    except Exception:
        return {"network": "127.0.0.1 (Lokalnie)"}

@app.get("/api/system/watchdog", dependencies=[Depends(verify_token)])
async def system_watchdog():
    services = []
    for name in ["nexus", "nginx", "postgresql", "minio"]:
        code, output = run_vm_command(["systemctl", "is-active", name], timeout=5)
        state = output.strip() or ("missing" if code != 0 else "unknown")
        services.append({"name": name, "active": code == 0 and state == "active", "state": state})
    ports = []
    for port, label in [(9090, "FastAPI local"), (80, "HTTP"), (443, "HTTPS"), (5432, "PostgreSQL")]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.35)
        try:
            open_port = sock.connect_ex(("127.0.0.1", port)) == 0
        finally:
            sock.close()
        ports.append({"port": port, "label": label, "open": open_port})
    threshold = vm_disk_threshold()
    disks = []
    disk_problem = False
    for label, path in [("root", Path("/")), ("nexus-app", BASE_DIR), ("libvirt-images", LIBVIRT_IMAGE_DIR)]:
        try:
            snap = disk_guard_snapshot(path, label)
            snap["threshold"] = threshold
            disks.append(snap)
            if snap["used_pct"] >= threshold:
                disk_problem = True
                record_alert(
                    "Watchdog dysku przekroczyl prog",
                    f"{label} {path}: {snap['used_pct']}% zajete, wolne {snap['free_gb']} GB, prog {threshold}%",
                    "critical" if snap["used_pct"] >= 95 else "warn",
                    f"watchdog-disk-{label}",
                )
        except Exception as exc:
            disk_problem = True
            record_alert("Watchdog nie odczytal dysku", f"{label} {path}: {exc}", "warn", f"watchdog-disk-error-{label}")
    unhealthy = [item for item in services if item["name"] in {"nexus", "nginx", "postgresql"} and not item["active"]]
    if unhealthy:
        record_alert("Watchdog wykryl problem uslugi", ", ".join(f"{item['name']}={item['state']}" for item in unhealthy), "critical", "watchdog-core-services")
    pg_port = next((item for item in ports if item["port"] == 5432), None)
    if pg_port and not pg_port["open"]:
        record_alert("PostgreSQL port zamkniety", "Port 5432 nie odpowiada lokalnie. Sprawdz usluge i miejsce na dysku.", "critical", "watchdog-postgresql-port")
    status = "ok" if not unhealthy and not disk_problem and (not pg_port or pg_port["open"]) else "warn"
    return {"services": services, "ports": ports, "disks": disks, "disk_threshold": threshold, "status": status, "checked_at": now_iso()}

@app.get("/api/system/processes", dependencies=[Depends(verify_token)])
async def get_processes():
    if HAS_PSUTIL:
        rows = []
        for process in psutil.process_iter(["pid", "ppid", "name", "username", "cpu_percent", "memory_percent", "memory_info", "status", "cmdline", "create_time"]):
            try:
                info = process.info
                mem_info = info.get("memory_info")
                cmdline = " ".join(info.get("cmdline") or [])
                rows.append({
                    "pid": info["pid"],
                    "ppid": info.get("ppid") or 0,
                    "name": info["name"] or "?",
                    "user": info["username"] or "?",
                    "cpu": round(info["cpu_percent"] or 0, 1),
                    "memory": round(info["memory_percent"] or 0, 1),
                    "memory_mb": round((getattr(mem_info, "rss", 0) or 0) / 1024 / 1024, 1),
                    "status": info.get("status") or "?",
                    "cmd": cmdline[:240],
                    "started": datetime.datetime.fromtimestamp(info.get("create_time") or 0).strftime("%Y-%m-%d %H:%M") if info.get("create_time") else "",
                })
            except Exception:
                continue
        rows.sort(key=lambda row: (row["cpu"], row["memory_mb"]), reverse=True)
        return rows[:200]
    try:
        output = subprocess.check_output(
            ["ps", "-eo", "pid=,ppid=,stat=,user=,%cpu=,%mem=,rss=,comm=,args=", "--sort=-%cpu"],
            text=True, timeout=3,
        )
        rows = []
        for line in output.splitlines()[:200]:
            parts = line.split(None, 8)
            if len(parts) >= 8:
                rows.append({
                    "pid": int(parts[0]),
                    "ppid": int(parts[1]),
                    "status": parts[2],
                    "user": parts[3],
                    "cpu": float(parts[4]),
                    "memory": float(parts[5]),
                    "memory_mb": round(float(parts[6]) / 1024, 1),
                    "name": parts[7],
                    "cmd": parts[8][:240] if len(parts) > 8 else parts[7],
                    "started": "",
                })
        return rows
    except Exception as exc:
        log_event(f"PROCESS ERROR: {exc}")
        return []

@app.post("/api/system/process/kill", dependencies=[Depends(verify_admin)])
async def kill_process(data: KillRequest):
    if data.pid <= 1 or data.pid == os.getpid():
        raise HTTPException(status_code=400, detail="Chroniony proces")
    sig = signal.SIGKILL if data.signal.lower() == "kill" else signal.SIGTERM
    try:
        os.kill(data.pid, sig)
        log_event(f"PROCESS {data.pid} signal={data.signal}")
        return {"status": "success"}
    except ProcessLookupError:
        raise HTTPException(status_code=404, detail="Proces nie istnieje")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Brak uprawnien")

def detect_vm_backend():
    if shutil.which("qm"):
        return "proxmox"
    if shutil.which("virsh"):
        return "libvirt"
    return "none"

def run_vm_command(args, timeout=20):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return result.returncode, (result.stdout or "") + (result.stderr or "")

def host_memory_snapshot():
    mem = {"total_mb": 0, "available_mb": 0, "swap_free_mb": 0, "commit_headroom_mb": 0}
    if HAS_PSUTIL:
        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()
        mem["total_mb"] = round(vm.total / 1024 / 1024)
        mem["available_mb"] = round(vm.available / 1024 / 1024)
        mem["swap_free_mb"] = round(sw.free / 1024 / 1024)
    try:
        rows = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            rows[key] = int(value.strip().split()[0])
        mem["total_mb"] = mem["total_mb"] or round(rows.get("MemTotal", 0) / 1024)
        mem["available_mb"] = mem["available_mb"] or round(rows.get("MemAvailable", rows.get("MemFree", 0)) / 1024)
        mem["swap_free_mb"] = mem["swap_free_mb"] or round(rows.get("SwapFree", 0) / 1024)
        commit_limit = rows.get("CommitLimit", 0)
        committed = rows.get("Committed_AS", 0)
        if commit_limit:
            mem["commit_headroom_mb"] = round(max(0, commit_limit - committed) / 1024)
    except Exception:
        pass
    return mem

def running_libvirt_names():
    code, output = run_vm_command(["virsh", "list", "--name"], timeout=8)
    if code != 0:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]

def ensure_vm_memory_available(requested_mb: int, name: str):
    mem = host_memory_snapshot()
    reserve_mb = 192
    effective_mb = mem["available_mb"] + int(mem["swap_free_mb"] * 0.75)
    if mem["commit_headroom_mb"]:
        effective_mb = min(effective_mb, mem["commit_headroom_mb"])
    needed_mb = int(requested_mb) + reserve_mb
    if effective_mb >= needed_mb:
        return mem
    running = running_libvirt_names()
    running_label = ", ".join(running[:8]) if running else "brak"
    raise HTTPException(
        status_code=409,
        detail=(
            f"Brak RAM dla VM {name}. Zadano {requested_mb} MB + rezerwa {reserve_mb} MB, "
            f"dostepne efektywnie {effective_mb} MB (RAM {mem['available_mb']} MB, swap {mem['swap_free_mb']} MB). "
            f"Uruchomione VM: {running_label}. Zatrzymaj jedna VM albo zmniejsz RAM w OS FORGE."
        ),
    )

def round_down_memory_mb(value: int, step: int = 128):
    value = int(value or 0)
    if value <= 0:
        return 0
    return max(step, (value // step) * step)

def vm_startup_memory_floor(preset, target_mb: int):
    preset_id = (preset.get("id") or "").lower()
    family = (preset.get("family") or "").lower()
    target_mb = int(target_mb or 0)
    if preset_id in {"win95", "win98", "freedos"}:
        return min(target_mb, int(preset.get("memory_mb") or target_mb or 128))
    if preset_id == "winxp":
        return min(target_mb, 512)
    if is_macos_preset(preset):
        return min(target_mb, 2048)
    if "windows" in family:
        return min(target_mb, 1536 if target_mb <= 4096 else 2048)
    if preset_id in {"truenas-core", "fedora", "kali", "gentoo"}:
        return min(target_mb, 1536)
    if "linux" in family or "bsd" in family:
        return min(target_mb, 512)
    return min(target_mb, 512)

def plan_vm_memory_allocation(target_mb: int, name: str, preset):
    target_mb = max(128, int(target_mb or 0))
    mem = host_memory_snapshot()
    reserve_mb = 192
    effective_mb = int(mem.get("available_mb") or 0) + int((mem.get("swap_free_mb") or 0) * 0.75)
    if mem.get("commit_headroom_mb"):
        effective_mb = min(effective_mb, int(mem.get("commit_headroom_mb") or effective_mb))
    usable_mb = max(0, effective_mb - reserve_mb)
    floor_mb = vm_startup_memory_floor(preset, target_mb)
    thin = target_mb > usable_mb
    if thin:
        startup_mb = round_down_memory_mb(min(target_mb, usable_mb), 128)
        if startup_mb < floor_mb and usable_mb >= floor_mb:
            startup_mb = round_down_memory_mb(floor_mb, 128)
        elif startup_mb < floor_mb:
            startup_mb = round_down_memory_mb(max(128, usable_mb), 128)
    else:
        startup_mb = target_mb
    if startup_mb < 128:
        running = running_libvirt_names()
        running_label = ", ".join(running[:8]) if running else "brak"
        raise HTTPException(
            status_code=409,
            detail=(
                f"Brak nawet minimalnego RAM startowego dla VM {name}. Target {target_mb} MB, "
                f"dostepne efektywnie {effective_mb} MB (RAM {mem['available_mb']} MB, swap {mem['swap_free_mb']} MB). "
                f"Uruchomione VM: {running_label}."
            ),
        )
    warnings = []
    if thin:
        warnings.append(
            f"RAM thin provisioning: VM target/max {target_mb} MB, start/current {startup_mb} MB. "
            "Po starcie OS Forge moze podniesc RAM przez balloon/config, gdy host ma zapas."
        )
        if startup_mb < floor_mb:
            warnings.append(
                f"Start RAM {startup_mb} MB jest ponizej bezpiecznego progu presetowego {floor_mb} MB; "
                "VM moze startowac wolniej albo wymagac pozniejszego podbicia RAM."
            )
    return {
        **mem,
        "status": "thin" if thin else "full",
        "target_memory_mb": target_mb,
        "startup_memory_mb": startup_mb,
        "reserve_mb": reserve_mb,
        "effective_available_mb": effective_mb,
        "usable_start_mb": usable_mb,
        "floor_memory_mb": floor_mb,
        "thin": bool(thin),
        "warnings": warnings,
    }

def vm_disk_threshold():
    try:
        config = read_json(VM_ALERTS_CONFIG_FILE, {"disk_threshold": 90})
        return max(70, min(98, int(config.get("disk_threshold") or 90)))
    except Exception:
        return 90

def disk_guard_snapshot(path: Path, label: str, reserve_gb: float = 0):
    usage = shutil.disk_usage(str(path))
    used = usage.total - usage.free
    reserve_bytes = int(max(0, float(reserve_gb)) * 1024 * 1024 * 1024)
    projected_used = min(usage.total, used + reserve_bytes)
    used_pct = round((used / usage.total) * 100, 1) if usage.total else 0
    projected_pct = round((projected_used / usage.total) * 100, 1) if usage.total else 0
    return {
        "label": label,
        "path": str(path),
        "total_gb": round(usage.total / 1024 / 1024 / 1024, 2),
        "used_gb": round(used / 1024 / 1024 / 1024, 2),
        "free_gb": round(usage.free / 1024 / 1024 / 1024, 2),
        "used_pct": used_pct,
        "projected_used_pct": projected_pct,
        "reserve_gb": round(float(reserve_gb), 2),
    }

def ensure_vm_disk_capacity(requested_gb: int, name: str, thin_provisioned: bool = True):
    threshold = vm_disk_threshold()
    min_free_after_gb = 4
    requested_gb = max(1, int(requested_gb or 1))
    physical_reserve_gb = max(1.0, min(8.0, round(requested_gb * 0.03, 2))) if thin_provisioned else float(requested_gb)
    guard_reserve_gb = physical_reserve_gb + min_free_after_gb
    snapshot = disk_guard_snapshot(LIBVIRT_IMAGE_DIR, "libvirt-images", guard_reserve_gb)
    snapshot.update({
        "virtual_requested_gb": requested_gb,
        "thin_provisioned": bool(thin_provisioned),
        "physical_reserve_gb": round(physical_reserve_gb, 2),
        "min_free_after_gb": min_free_after_gb,
        "guard_reserve_gb": round(guard_reserve_gb, 2),
    })
    if snapshot["projected_used_pct"] >= threshold or snapshot["free_gb"] < guard_reserve_gb:
        body = (
            f"{LIBVIRT_IMAGE_DIR}: wolne {snapshot['free_gb']} GB, VM {name} chce wirtualnie {requested_gb} GB "
            f"(qcow2 thin), rezerwa fizyczna {round(physical_reserve_gb, 2)} GB + bufor {min_free_after_gb} GB, "
            f"projekcja {snapshot['projected_used_pct']}% przy progu {threshold}%."
        )
        try:
            record_alert("Zatrzymano tworzenie VM przez brak miejsca", body, "critical", "vm-create-disk-guard")
        except Exception as exc:
            log_event(f"VM_DISK_GUARD alert error: {exc}")
        raise HTTPException(status_code=507, detail=body)
    return snapshot

def iso_roots():
    roots = [NEXUS_ISO_STORAGE_DIR, LIBVIRT_ISO_DIR, ISO_DIR, LIBVIRT_IMAGE_DIR]
    safe = []
    for root in roots:
        try:
            root.mkdir(parents=True, exist_ok=True)
            safe.append(root.resolve())
        except Exception:
            pass
    return safe

def safe_iso_filename(name: str):
    base = Path(name or "").name.strip()
    base = re.sub(r"[^A-Za-z0-9._+-]+", "-", base)
    if not base:
        base = f"nexus-{uuid.uuid4().hex[:8]}.iso"
    allowed = {".iso", ".img", ".qcow2", ".raw"}
    suffix = Path(base).suffix.lower()
    if suffix not in allowed:
        base += ".iso"
    return base[:160]

def safe_upload_filename(name: str):
    base = Path(name or "").name.strip()
    base = re.sub(r"[^A-Za-z0-9._+-]+", "-", base)
    return (base or f"nexus-upload-{uuid.uuid4().hex[:8]}.bin")[:180]

def unique_target_path(root: Path, filename: str):
    root.mkdir(parents=True, exist_ok=True)
    safe = safe_upload_filename(filename)
    target = (root / safe).resolve()
    root_resolved = root.resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise HTTPException(status_code=400, detail="Niepoprawna nazwa pliku")
    if not target.exists():
        return target
    stem = target.stem[:120]
    suffix = target.suffix
    for _ in range(50):
        candidate = (root / f"{stem}-{uuid.uuid4().hex[:6]}{suffix}").resolve()
        if not candidate.exists():
            return candidate
    raise HTTPException(status_code=409, detail="Nie udalo sie dobrac wolnej nazwy pliku")

def validate_iso_url(url: str):
    parsed = urllib.parse.urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Podaj URL http/https do obrazu ISO/IMG/QCOW2")
    if parsed.hostname and parsed.hostname.lower() in {"localhost", "127.0.0.1", "::1"}:
        raise HTTPException(status_code=400, detail="Nie pobieram ISO z localhost")
    path_suffix = Path(urllib.parse.unquote(parsed.path)).suffix.lower()
    if path_suffix not in {".iso", ".img", ".qcow2", ".raw"}:
        raise HTTPException(status_code=400, detail="URL musi wskazywac na .iso, .img, .qcow2 albo .raw")
    return parsed

def vm_image_file_signature(path: Path):
    path = Path(path).resolve()
    signature = {
        "head_hex": "",
        "qcow2_magic": False,
        "iso9660": False,
        "checked_offsets": ["0x8001", "0x8801", "0x9001"],
    }
    try:
        with open(path, "rb") as handle:
            head = handle.read(16)
            signature["head_hex"] = head.hex()
            signature["qcow2_magic"] = head.startswith(b"QFI\xfb")
            for offset in (0x8001, 0x8801, 0x9001):
                handle.seek(offset)
                if handle.read(5) == b"CD001":
                    signature["iso9660"] = True
                    break
    except Exception as exc:
        signature["error"] = str(exc)[:240]
    return signature

def classify_vm_image_file(path: Path):
    path = Path(path).resolve()
    suffix = path.suffix.lower()
    signature = vm_image_file_signature(path)
    media_role = "cdrom" if suffix == ".iso" else "disk"
    kind = suffix.lstrip(".") or "unknown"
    cdrom_attachable = suffix == ".iso"
    disk_attachable = suffix in {".qcow2", ".raw", ".img"}
    warnings = []
    if suffix == ".iso" and not signature.get("iso9660"):
        warnings.append("Rozszerzenie .iso, ale nie wykryto sygnatury ISO9660 CD001 w typowych offsetach.")
    if suffix == ".qcow2" and not signature.get("qcow2_magic"):
        warnings.append("Rozszerzenie .qcow2, ale naglowek nie ma magic QFI.")
    if suffix in {".raw", ".img"}:
        warnings.append("Obraz raw/img nie ma jednoznacznej sygnatury; traktuje jako dysk, chyba ze wybierzesz go recznie inaczej.")
    return {
        "kind": kind,
        "media_role": media_role,
        "cdrom_attachable": cdrom_attachable,
        "disk_attachable": disk_attachable,
        "signature": signature,
        "classification_warnings": warnings,
    }

def scan_iso_files():
    items = []
    seen = set()
    for root in iso_roots():
        for path in root.rglob("*"):
            try:
                if not path.is_file() or path.suffix.lower() not in {".iso", ".img", ".qcow2", ".raw"}:
                    continue
                resolved = path.resolve()
                if str(resolved) in seen:
                    continue
                seen.add(str(resolved))
                stat = resolved.stat()
                suffix = resolved.suffix.lower()
                classification = classify_vm_image_file(resolved)
                items.append({
                    "name": resolved.name,
                    "path": str(resolved),
                    "size": stat.st_size,
                    "size_label": fmt_size(stat.st_size),
                    "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "root": str(root),
                    **classification,
                })
            except Exception:
                continue
    items.sort(key=lambda item: item["modified"], reverse=True)
    return items

def vm_chunk_upload_store():
    data = read_json(VM_CHUNK_UPLOADS_FILE, {})
    return data if isinstance(data, dict) else {}

def save_vm_chunk_upload_store(data):
    clean = {}
    cutoff = datetime.datetime.now() - datetime.timedelta(days=3)
    for key, row in (data or {}).items():
        created = row.get("created_at", "")
        try:
            created_dt = datetime.datetime.fromisoformat(created)
        except Exception:
            created_dt = datetime.datetime.now()
        if row.get("status") in {"open", "assembling"} or created_dt >= cutoff:
            clean[str(key)] = row
    write_json(VM_CHUNK_UPLOADS_FILE, clean)

def public_vm_chunk_upload(row):
    parts = row.get("parts") or {}
    received = sum(int((item or {}).get("size", 0) or 0) for item in parts.values())
    total = int(row.get("size", 0) or 0)
    validation = row.get("validation") or {}
    return {
        "id": row.get("id", ""),
        "filename": row.get("filename", ""),
        "target": row.get("target", ""),
        "purpose": row.get("purpose", "auto"),
        "kind": validation.get("kind") or Path(row.get("filename", "")).suffix.lower().lstrip("."),
        "media_role": validation.get("media_role", ""),
        "cdrom_attachable": bool(validation.get("cdrom_attachable", False)),
        "disk_attachable": bool(validation.get("disk_attachable", False)),
        "status": row.get("status", ""),
        "error": row.get("error", ""),
        "created_by": row.get("created_by", ""),
        "created_at": row.get("created_at", ""),
        "updated_at": row.get("updated_at", ""),
        "finished_at": row.get("finished_at", ""),
        "size": total,
        "size_label": fmt_size(total),
        "received": received,
        "received_label": fmt_size(received),
        "progress": round((received / total) * 100, 1) if total else 0,
        "chunk_size": int(row.get("chunk_size", 0) or 0),
        "part_count": int(row.get("part_count", 0) or 0),
        "received_parts": len(parts),
        "sha256": row.get("actual_sha256") or row.get("sha256", ""),
        "validation": validation,
    }

def vm_upload_target_path(filename: str, overwrite: bool = False):
    safe = safe_iso_filename(filename)
    suffix = Path(safe).suffix.lower()
    if suffix not in VM_IMAGE_EXT:
        raise HTTPException(status_code=400, detail="Turbo Upload VM przyjmuje tylko .iso, .qcow2, .raw albo .img")
    root = NEXUS_ISO_STORAGE_DIR.resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / safe).resolve()
    if target != root and root not in target.parents:
        raise HTTPException(status_code=400, detail="Niepoprawna nazwa pliku")
    if target.exists() and not overwrite:
        raise HTTPException(status_code=409, detail="Taki plik juz istnieje w /var/lib/nexus/iso_storage. Uzyj overwrite=true albo zmien nazwe.")
    return target

def ensure_vm_upload_space(size: int):
    usage = shutil.disk_usage(str(NEXUS_ISO_STORAGE_DIR))
    reserve = 1024 * 1024 * 1024
    if usage.free < int(size) + reserve:
        raise HTTPException(
            status_code=507,
            detail=(
                f"Za malo miejsca na upload VM. Plik {fmt_size(size)}, wolne {fmt_size(usage.free)}, "
                f"wymagana rezerwa {fmt_size(reserve)}."
            ),
        )
    return disk_guard_snapshot(NEXUS_ISO_STORAGE_DIR, "nexus-iso-storage", (int(size) + reserve) / 1024 / 1024 / 1024)

def vm_upload_record(upload_id: str):
    clean = re.sub(r"[^a-fA-F0-9]+", "", upload_id or "")[:32]
    if not clean or clean != (upload_id or ""):
        raise HTTPException(status_code=400, detail="Niepoprawny upload_id")
    store = vm_chunk_upload_store()
    row = store.get(clean)
    if not row:
        raise HTTPException(status_code=404, detail="Nie znaleziono uploadu VM")
    return store, row

def vm_upload_part_path(row, part_number: int):
    if part_number < 0 or part_number >= int(row.get("part_count", 0) or 0):
        raise HTTPException(status_code=400, detail="Niepoprawny numer czesci")
    part_dir = Path(row.get("part_dir") or "").resolve()
    if not part_dir.exists():
        part_dir.mkdir(parents=True, exist_ok=True)
    return part_dir / f"{part_number:08d}.part"

def validate_completed_vm_upload(path: Path):
    suffix = path.suffix.lower()
    classification = classify_vm_image_file(path)
    if suffix == ".iso":
        validation = validate_cdrom_image(path)
        validation["role"] = "cdrom"
        validation.update(classification)
        validation.setdefault("warnings", []).extend(classification.get("classification_warnings") or [])
        return validation
    info = qemu_img_info(path)
    info_json = qemu_img_info_json(path)
    validation = {
        "path": str(path),
        "size": path.stat().st_size,
        "size_label": fmt_size(path.stat().st_size),
        "role": "disk",
        "qemu_img": info,
        "qemu_img_json": info_json,
        "thin_provisioned": info_json.get("format") == "qcow2",
        "thin_ratio": info_json.get("thin_ratio"),
    }
    validation.update(classification)
    if not info.get("ok"):
        validation.setdefault("warnings", []).append(info.get("output") or info.get("error") or "qemu-img nie potwierdzil obrazu")
    validation.setdefault("warnings", []).extend(classification.get("classification_warnings") or [])
    return validation

DRIVER_PACKAGE_EXT = {".iso", ".img", ".zip"}
DRIVER_NAME_RE = re.compile(r"(virtio|driver|drivers|sterownik|spice|qxl|guest|balloon|win-guest|vm-tools)", re.I)
DRIVER_CATEGORIES = [
    {"id": "storage", "label": "DYSK / SCSI", "desc": "Kontrolery dysku: viostor, vioscsi, storage.", "patterns": [r"viostor", r"vioscsi", r"storage", r"scsi", r"disk"]},
    {"id": "network", "label": "SIEC", "desc": "Karta sieciowa VM: NetKVM, ethernet, NIC.", "patterns": [r"netkvm", r"network", r"ethernet", r"\bnic\b", r"lan"]},
    {"id": "gpu", "label": "GPU / DISPLAY", "desc": "Ekran i grafika: qxl, display, video, graphics.", "patterns": [r"\bqxl\b", r"display", r"video", r"graphics", r"\bgpu\b"]},
    {"id": "memory", "label": "RAM / BALLOON", "desc": "Balonowanie pamieci RAM: Balloon.", "patterns": [r"balloon", r"memory", r"\bram\b"]},
    {"id": "cpu", "label": "CPU / CHIPSET", "desc": "Sterowniki platformy, chipsetu i procesora.", "patterns": [r"cpu", r"processor", r"chipset", r"acpi", r"qemupciserial"]},
    {"id": "agent", "label": "GUEST AGENT", "desc": "Agent goscia i integracja systemu: qemu-ga, spice agent.", "patterns": [r"qemu-ga", r"qemuga", r"guest[-_ ]?agent", r"spice.*agent", r"vdagent"]},
    {"id": "input", "label": "INPUT / MYSZ", "desc": "Mysz, tablet, klawiatura i urzadzenia wejsciowe.", "patterns": [r"vioinput", r"input", r"tablet", r"mouse", r"keyboard"]},
    {"id": "serial", "label": "SERIAL / PORTY", "desc": "Wirtualne porty szeregowe: vioser.", "patterns": [r"vioser", r"serial", r"comport", r"ports?"]},
    {"id": "filesystem", "label": "FILESYSTEM", "desc": "Wspoldzielony system plikow: viofs.", "patterns": [r"viofs", r"filesystem", r"fsdriver", r"shared"]},
    {"id": "rng", "label": "RNG / SECURITY", "desc": "Generator losowosci i elementy security.", "patterns": [r"viorng", r"\brng\b", r"random"]},
    {"id": "audio", "label": "AUDIO", "desc": "Dzwiek VM, jesli paczka go zawiera.", "patterns": [r"audio", r"sound", r"hda", r"ich"]},
    {"id": "tools", "label": "TOOLS / INSTALL", "desc": "Instalatory, MSI, EXE, dokumentacja i narzedzia pomocnicze.", "patterns": [r"\.msi$", r"\.exe$", r"installer", r"setup", r"readme", r"license"]},
]
DRIVER_CATEGORY_LABELS = {item["id"]: item["label"] for item in DRIVER_CATEGORIES}
DRIVER_RECOMMENDED_CATEGORIES = {"storage", "network", "gpu", "memory", "agent", "input", "serial", "rng"}

def driver_roots():
    roots = [DRIVER_DIR, NEXUS_ISO_STORAGE_DIR, LIBVIRT_ISO_DIR, ISO_DIR, LIBVIRT_IMAGE_DIR]
    safe = []
    for root in roots:
        try:
            root.mkdir(parents=True, exist_ok=True)
            safe.append(root.resolve())
        except Exception:
            pass
    return safe

def safe_extract_name(name: str):
    clean = re.sub(r"[^A-Za-z0-9._+-]+", "-", Path(name or "drivers").stem).strip(".-")
    return (clean or f"drivers-{uuid.uuid4().hex[:8]}")[:80]

def is_driver_candidate(path: Path, root: Path):
    suffix = path.suffix.lower()
    if suffix not in DRIVER_PACKAGE_EXT:
        return False
    if root.resolve() == DRIVER_DIR.resolve() or DRIVER_DIR.resolve() in path.resolve().parents:
        return True
    return bool(DRIVER_NAME_RE.search(path.name))

def categorize_driver_file(rel: str):
    text = str(rel or "").replace("\\", "/").lower()
    for item in DRIVER_CATEGORIES:
        for pattern in item["patterns"]:
            if re.search(pattern, text):
                return item["id"]
    return "unknown"

def driver_file_kind(rel: str):
    suffix = Path(rel or "").suffix.lower().lstrip(".")
    return suffix or "file"

def driver_file_rows(extract_dir: Path):
    rows = []
    if not extract_dir.exists():
        return rows
    for path in extract_dir.rglob("*"):
        try:
            if not path.is_file():
                continue
            rel = str(path.relative_to(extract_dir)).replace("\\", "/")
            category = categorize_driver_file(rel)
            stat = path.stat()
            rows.append({
                "path": rel,
                "name": path.name,
                "category": category,
                "category_label": DRIVER_CATEGORY_LABELS.get(category, "INNE / NIEZNANE"),
                "kind": driver_file_kind(rel),
                "size": stat.st_size,
                "size_label": fmt_size(stat.st_size),
            })
        except Exception:
            continue
    rows.sort(key=lambda row: (row["category"], row["path"].lower()))
    return rows

def driver_category_summary(files):
    buckets = {}
    for row in files or []:
        category = row.get("category") or "unknown"
        item = buckets.setdefault(category, {
            "id": category,
            "label": DRIVER_CATEGORY_LABELS.get(category, "INNE / NIEZNANE"),
            "count": 0,
            "bytes": 0,
            "recommended": category in DRIVER_RECOMMENDED_CATEGORIES,
            "samples": [],
        })
        item["count"] += 1
        item["bytes"] += int(row.get("size") or 0)
        if len(item["samples"]) < 5:
            item["samples"].append(row.get("path") or row.get("name") or "")
    for item in buckets.values():
        item["size_label"] = fmt_size(item["bytes"])
    order = {item["id"]: idx for idx, item in enumerate(DRIVER_CATEGORIES)}
    return sorted(buckets.values(), key=lambda row: order.get(row["id"], 999))

def driver_extract_dir_for(source: Path):
    return (DRIVER_EXTRACT_DIR / safe_extract_name(source.name)).resolve()

def scan_driver_packages():
    items = []
    seen = set()
    for root in driver_roots():
        try:
            paths = root.rglob("*")
        except Exception:
            continue
        for path in paths:
            try:
                if not path.is_file() or not is_driver_candidate(path, root):
                    continue
                resolved = path.resolve()
                if str(resolved) in seen:
                    continue
                seen.add(str(resolved))
                stat = resolved.stat()
                extract_dir = driver_extract_dir_for(resolved)
                extracted_rows = []
                if extract_dir.exists():
                    extracted_rows = driver_file_rows(extract_dir)
                items.append({
                    "name": resolved.name,
                    "path": str(resolved),
                    "size": stat.st_size,
                    "size_label": fmt_size(stat.st_size),
                    "modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "root": str(root),
                    "kind": resolved.suffix.lower().lstrip("."),
                    "extracted": extract_dir.exists(),
                    "extract_dir": str(extract_dir) if extract_dir.exists() else "",
                    "extracted_count": len(extracted_rows),
                    "sample_files": [row["path"] for row in extracted_rows[:12]],
                    "files": extracted_rows[:240],
                    "categories": driver_category_summary(extracted_rows),
                    "attachable": resolved.suffix.lower() in {".iso", ".img"},
                })
            except Exception:
                continue
    items.sort(key=lambda item: (not item.get("attachable"), item["modified"]), reverse=True)
    return items

def allowed_driver_path(path: str):
    target = Path(path or "").resolve()
    for root in driver_roots() + [LIBVIRT_IMAGE_DIR.resolve()]:
        if target == root or root in target.parents:
            if target.exists() and target.is_file() and target.suffix.lower() in DRIVER_PACKAGE_EXT:
                return target
    raise HTTPException(status_code=400, detail="Sterownik musi lezec w Driver Vault albo ISO Vault")

def safe_extract_member(target_root: Path, member: str):
    member_path = (target_root / member).resolve()
    root = target_root.resolve()
    if member_path != root and root not in member_path.parents:
        raise HTTPException(status_code=400, detail="Paczka sterownikow ma niebezpieczna sciezke")
    return member_path

def external_extract_tool():
    for tool in ["bsdtar", "7z", "7zz"]:
        found = shutil.which(tool)
        if found:
            return tool
    return ""

def iso_build_tool():
    for tool in ["xorrisofs", "genisoimage", "mkisofs"]:
        found = shutil.which(tool)
        if found:
            return tool
    return ""

def build_driver_iso_from_dir(source_dir: Path, name: str):
    tool = iso_build_tool()
    if not tool:
        return None, "Brak xorrisofs/genisoimage/mkisofs - paczka zostala rozpakowana, ale nie zbudowano ISO"
    target = (DRIVER_DIR / f"{safe_extract_name(name)}-drivers.iso").resolve()
    command = [tool, "-quiet", "-J", "-r", "-o", str(target), str(source_dir)]
    code, output = run_vm_command(command, timeout=180)
    if code != 0:
        return None, output.strip() or "Nie udalo sie zbudowac ISO ze sterownikami"
    ensure_libvirt_file_access(target)
    return target, ""

def extract_driver_package(path: Path):
    source = allowed_driver_path(str(path))
    target_dir = driver_extract_dir_for(source)
    if DRIVER_EXTRACT_DIR.resolve() not in target_dir.parents:
        raise HTTPException(status_code=400, detail="Niepoprawna sciezka rozpakowania")
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = source.suffix.lower()
    note = ""
    if suffix == ".zip":
        with zipfile.ZipFile(source, "r") as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                out_path = safe_extract_member(target_dir, member.filename)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as src, open(out_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        driver_iso, note = build_driver_iso_from_dir(target_dir, source.name)
    elif suffix == ".iso":
        tool = external_extract_tool()
        if tool == "bsdtar":
            code, output = run_vm_command(["bsdtar", "-C", str(target_dir), "-xf", str(source)], timeout=240)
            if code != 0:
                raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie rozpakowac ISO")
        elif tool in {"7z", "7zz"}:
            code, output = run_vm_command([tool, "x", f"-o{target_dir}", "-y", str(source)], timeout=240)
            if code != 0:
                raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie rozpakowac ISO")
        else:
            note = "Brak bsdtar/7z - ISO zostanie podpinane bez rozpakowania"
    else:
        raise HTTPException(status_code=400, detail="Rozpakowanie wspiera ZIP albo ISO")
    files = driver_file_rows(target_dir)
    return {
        "status": "extracted",
        "source": str(source),
        "extract_dir": str(target_dir),
        "files": files[:240],
        "categories": driver_category_summary(files),
        "file_count": len(files),
        "driver_iso": str(driver_iso) if suffix == ".zip" and 'driver_iso' in locals() and driver_iso else "",
        "note": note,
    }

def ensure_driver_extracted(source: Path):
    extract_dir = driver_extract_dir_for(source)
    rows = driver_file_rows(extract_dir)
    if rows:
        return extract_dir, rows
    result = extract_driver_package(source)
    rows = result.get("files") or []
    return extract_dir, rows

def safe_driver_categories(categories):
    allowed = {item["id"] for item in DRIVER_CATEGORIES} | {"unknown"}
    selected = []
    for value in categories or []:
        clean = re.sub(r"[^a-z0-9_-]+", "", str(value).lower())
        if clean in allowed and clean not in selected:
            selected.append(clean)
    return selected[:24]

def build_selected_driver_iso(source: Path, categories):
    selected = safe_driver_categories(categories)
    if not selected:
        return None
    extract_dir, files = ensure_driver_extracted(source)
    if not files:
        raise HTTPException(status_code=400, detail="Nie mam rozpakowanych plikow sterownika do filtrowania. Rozpakuj paczke albo doinstaluj extractor ISO.")
    selected_files = [row for row in files if row.get("category") in selected]
    if not selected_files:
        labels = ", ".join(selected)
        raise HTTPException(status_code=400, detail=f"Brak plikow sterownika dla kategorii: {labels}")
    digest_src = f"{source}:{','.join(selected)}:{len(selected_files)}"
    digest = hashlib.sha1(digest_src.encode("utf-8")).hexdigest()[:10]
    stage = (DRIVER_EXTRACT_DIR / f"selected-{safe_extract_name(source.name)}-{digest}").resolve()
    if DRIVER_EXTRACT_DIR.resolve() not in stage.parents:
        raise HTTPException(status_code=400, detail="Niepoprawna sciezka robocza sterownikow")
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)
    copied = 0
    for row in selected_files:
        rel = row.get("path") or ""
        src = safe_extract_member(extract_dir, rel)
        if not src.exists() or not src.is_file():
            continue
        dst = safe_extract_member(stage, rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    if copied == 0:
        raise HTTPException(status_code=400, detail="Nie udalo sie skopiowac wybranych sterownikow")
    selected_iso, note = build_driver_iso_from_dir(stage, f"{safe_extract_name(source.name)}-{digest}-selected")
    if not selected_iso:
        raise HTTPException(status_code=500, detail=note or "Nie udalo sie zbudowac wybranego ISO sterownikow")
    log_event(f"VM_DRIVER_SELECTED_ISO source={source.name} categories={','.join(selected)} files={copied} iso={selected_iso.name}")
    return selected_iso

def selected_driver_media(preset, requested: str, categories=None):
    requested = (requested or "").strip()
    if requested.lower() in {"none", "off", "disabled"}:
        return None
    if requested:
        target = allowed_driver_path(requested)
        selected_iso = build_selected_driver_iso(target, categories or [])
        if selected_iso:
            return prepare_libvirt_iso(selected_iso)
        if target.suffix.lower() == ".zip":
            result = extract_driver_package(target)
            if result.get("driver_iso"):
                return prepare_libvirt_iso(Path(result["driver_iso"]))
            raise HTTPException(status_code=400, detail=result.get("note") or "ZIP rozpakowany, ale nie mam narzedzia do zbudowania ISO dla VM")
        if target.suffix.lower() not in {".iso", ".img"}:
            raise HTTPException(status_code=400, detail="Do VM mozna podpiac sterowniki jako ISO/IMG")
        return prepare_libvirt_iso(target)
    if is_windows_preset(preset):
        virtio = find_virtio_win_iso()
        if virtio:
            return prepare_libvirt_iso(virtio)
    return None

def download_iso_worker(job_id: str, url: str, target: Path):
    job = ISO_DOWNLOADS[job_id]
    part = target.with_suffix(target.suffix + ".part")
    try:
        ensure_libvirt_file_access(target.parent, is_dir=True)
        req = urllib.request.Request(url, headers={"User-Agent": "NEXUS-ISO-VAULT/1.0"})
        with urllib.request.urlopen(req, timeout=60) as response:
            total = int(response.headers.get("Content-Length") or 0)
            content_type = (response.headers.get("Content-Type") or "").lower()
            if "text/html" in content_type:
                raise RuntimeError("Serwer zwrocil HTML zamiast obrazu ISO/IMG/QCOW2")
            job.update({"status": "running", "total": total, "downloaded": 0, "target": str(target)})
            with open(part, "wb") as fh:
                while True:
                    if job.get("status") == "cancel_requested":
                        raise RuntimeError("Pobieranie anulowane")
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    fh.write(chunk)
                    job["downloaded"] += len(chunk)
        part.replace(target)
        ensure_libvirt_file_access(target)
        job.update({"status": "done", "downloaded": target.stat().st_size, "size_label": fmt_size(target.stat().st_size), "finished_at": now_iso()})
        log_event(f"ISO_DOWNLOAD done {target.name} {url}")
    except Exception as exc:
        try:
            if part.exists():
                part.unlink()
        except Exception:
            pass
        if job.get("status") == "cancel_requested":
            job.update({"status": "cancelled", "error": "Anulowano", "finished_at": now_iso()})
        else:
            job.update({"status": "error", "error": str(exc), "finished_at": now_iso()})
        log_event(f"ISO_DOWNLOAD error {url}: {exc}")

CDROM_IMAGE_EXT = {".iso"}
VM_DISK_IMAGE_EXT = {".qcow2", ".raw", ".img"}

def allowed_media_path(path: str, allowed_exts, label: str):
    target = Path(path or "").resolve()
    for root in iso_roots():
        if target == root or root in target.parents:
            if target.exists() and target.is_file() and target.suffix.lower() in allowed_exts:
                return target
    raise HTTPException(status_code=400, detail=f"{label} musi lezec w Vault albo /var/lib/libvirt/images i miec rozszerzenie: {', '.join(sorted(allowed_exts))}")

def allowed_iso_path(path: str):
    return allowed_media_path(path, CDROM_IMAGE_EXT, "ISO/CD-ROM")

def allowed_vm_disk_path(path: str):
    return allowed_media_path(path, VM_DISK_IMAGE_EXT, "Dysk VM")

def ensure_libvirt_file_access(path: Path, is_dir: bool = False):
    try:
        target = Path(path)
        mode = 0o755 if is_dir or target.is_dir() else 0o644
        target.chmod(mode)
        if not (is_dir or target.is_dir()):
            shutil.chown(str(target), user="libvirt-qemu", group="kvm")
    except Exception:
        try:
            Path(path).chmod(0o755 if is_dir else 0o644)
        except Exception:
            pass

def prepare_libvirt_iso(source: Path):
    source = source.resolve()
    ensure_libvirt_file_access(LIBVIRT_IMAGE_DIR, is_dir=True)
    ensure_libvirt_file_access(LIBVIRT_ISO_DIR, is_dir=True)
    for root in [LIBVIRT_ISO_DIR.resolve(), LIBVIRT_IMAGE_DIR.resolve()]:
        if source == root or root in source.parents:
            ensure_libvirt_file_access(source)
            return source
    target = (LIBVIRT_ISO_DIR / safe_iso_filename(source.name)).resolve()
    if source.stat().st_size <= 0:
        raise HTTPException(status_code=400, detail="Wybrane ISO jest puste")
    if (not target.exists()) or target.stat().st_size != source.stat().st_size:
        tmp = target.with_suffix(target.suffix + ".copying")
        if tmp.exists():
            tmp.unlink()
        shutil.copyfile(source, tmp)
        tmp.replace(target)
    ensure_libvirt_file_access(target)
    log_event(f"VM_ISO prepared source={source} target={target}")
    return target

def looks_like_apple_install_media(path: str):
    text = str(path or "").lower()
    return any(token in text for token in (
        "macos", "mac-os", "osx", "os-x", "apple", "darwin",
        "highsierra", "high-sierra", "mojave", "catalina", "bigsur", "big-sur",
        "monterey", "ventura", "sonoma", "sequoia", "tahoe",
    ))

def looks_like_driver_media_path(path: str):
    name = Path(str(path or "")).name.lower()
    return any(token in name for token in (
        "virtio", "driver", "drivers", "selected-drivers", "spice", "qxl",
        "guest", "balloon", "vio", "netkvm", "vioscsi", "vioserial",
    ))

def inspect_iso_boot_profile(path: Path):
    profile = {
        "bootable_hint": False,
        "bios_boot_hint": False,
        "uefi_boot_hint": False,
        "eltorito": False,
        "platforms": [],
        "apple_hint": looks_like_apple_install_media(path),
        "warnings": [],
    }
    try:
        with open(path, "rb") as handle:
            for sector_no in range(16, 48):
                handle.seek(sector_no * 2048)
                sector = handle.read(2048)
                if len(sector) < 2048:
                    break
                descriptor_type = sector[0]
                if sector[1:6] != b"CD001":
                    continue
                if descriptor_type == 255:
                    break
                if descriptor_type != 0 or b"EL TORITO" not in sector[7:64].upper():
                    continue
                catalog_lba = struct.unpack_from("<I", sector, 71)[0]
                if catalog_lba <= 0:
                    continue
                handle.seek(catalog_lba * 2048)
                catalog = handle.read(2048)
                if len(catalog) < 64:
                    continue
                profile["eltorito"] = True
                platform_ids = set()
                validation_platform = catalog[1]
                platform_ids.add(validation_platform)
                default_entry = catalog[32:64]
                if default_entry and default_entry[0] == 0x88:
                    profile["bootable_hint"] = True
                offset = 64
                remaining_entries = 0
                active_platform = validation_platform
                while offset + 32 <= len(catalog):
                    entry = catalog[offset:offset + 32]
                    entry_type = entry[0]
                    if entry_type in {0x90, 0x91}:  # section header / final section header
                        active_platform = entry[1]
                        platform_ids.add(active_platform)
                        remaining_entries = struct.unpack_from("<H", entry, 2)[0]
                    elif remaining_entries:
                        if entry_type == 0x88:
                            profile["bootable_hint"] = True
                            platform_ids.add(active_platform)
                        remaining_entries -= 1
                    offset += 32
                profile["platforms"] = sorted(platform_ids)
                profile["bios_boot_hint"] = 0 in platform_ids and profile["bootable_hint"]
                profile["uefi_boot_hint"] = 0xEF in platform_ids and profile["bootable_hint"]
                break
    except Exception as exc:
        profile["warnings"].append(f"Nie udalo sie sprawdzic katalogu boot ISO: {exc}")
    if profile["apple_hint"]:
        profile["warnings"].append("Obraz wyglada na macOS/Apple. SeaBIOS/legacy zwykle go nie uruchomi; uzyj profilu macOS/Cupertino z UEFI/OpenCore.")
    elif not profile["eltorito"]:
        profile["warnings"].append("Nie znaleziono katalogu boot El Torito; BIOS moze pokazac 'No bootable device'.")
    elif not profile["bios_boot_hint"] and profile["uefi_boot_hint"]:
        profile["warnings"].append("ISO wyglada na UEFI-only. Dla SeaBIOS/legacy ustaw VM na UEFI albo wybierz obraz z bootem BIOS.")
    elif not profile["bootable_hint"]:
        profile["warnings"].append("ISO ma strukture CD, ale nie wykryto bootowalnego wpisu; moze sluzyc jako dane/sterowniki, nie instalator.")
    return profile

def vm_firmware_profile(vm_id: str):
    target = safe_vm_target(vm_id)
    try:
        root, _ = vm_dumpxml_root(target, inactive=True)
        os_node = root.find("os")
        type_node = os_node.find("type") if os_node is not None else None
        loader = os_node.find("loader") if os_node is not None else None
        boot_devs = [node.attrib.get("dev", "") for node in (os_node.findall("boot") if os_node is not None else [])]
        loader_path = (loader.text or "").strip() if loader is not None and loader.text else ""
        machine = (type_node.attrib.get("machine", "") if type_node is not None else "").lower()
        firmware = "uefi" if loader is not None and (loader.attrib.get("type") == "pflash" or "OVMF" in loader_path.upper()) else "bios"
        return {"firmware": firmware, "loader": loader_path, "boot_devs": boot_devs, "machine": machine}
    except Exception as exc:
        return {"firmware": "unknown", "loader": "", "boot_devs": [], "machine": "", "error": str(exc)}

def validate_cdrom_image(path: Path):
    target = allowed_iso_path(str(path)).resolve()
    size = target.stat().st_size
    warnings = []
    if size <= 0:
        raise HTTPException(status_code=400, detail="Wybrany obraz ISO jest pusty")
    if size < 256 * 1024:
        warnings.append("Obraz ISO jest bardzo maly; sprawdz, czy to nie jest uszkodzony placeholder.")
    try:
        with open(target, "rb") as handle:
            handle.seek(0x8001)
            primary = handle.read(5)
            handle.seek(0x8801)
            supplementary = handle.read(5)
        if primary != b"CD001" and supplementary != b"CD001":
            warnings.append("Nie znaleziono sygnatury ISO9660 CD001; podpinam jako ISO, ale obraz moze byc nietypowy.")
    except Exception as exc:
        warnings.append(f"Nie udalo sie sprawdzic sygnatury ISO: {exc}")
    boot_profile = inspect_iso_boot_profile(target)
    warnings.extend(boot_profile.get("warnings") or [])
    return {"path": str(target), "size": size, "size_label": fmt_size(size), "warnings": warnings, "boot_profile": boot_profile}

def existing_first(paths):
    for item in paths:
        try:
            path = Path(str(item)).resolve()
            if path.exists() and path.is_file():
                return path
        except Exception:
            continue
    return None

def resolve_media_filename(name: str, suffixes):
    clean = safe_upload_filename(name or "")
    if not clean:
        return None
    for root in iso_roots():
        candidate = (root / clean).resolve()
        try:
            if candidate.exists() and candidate.is_file() and candidate.suffix.lower() in suffixes:
                return candidate
        except Exception:
            continue
        try:
            wanted = clean.lower()
            for child in root.iterdir():
                if child.is_file() and child.name.lower() == wanted and child.suffix.lower() in suffixes:
                    return child.resolve()
        except Exception:
            continue
    return None

def safe_firmware_path(path: str, label: str):
    target = Path(path or "").resolve()
    allowed_roots = [Path("/usr/share").resolve(), BASE_DIR.resolve(), NEXUS_ISO_STORAGE_DIR.resolve(), LIBVIRT_IMAGE_DIR.resolve()]
    if not target.exists() or not target.is_file() or target.suffix.lower() != ".fd":
        raise HTTPException(status_code=400, detail=f"{label} musi wskazywac na istniejacy plik .fd")
    if not any(target == root or root in target.parents for root in allowed_roots):
        raise HTTPException(status_code=400, detail=f"{label} musi lezec w /usr/share, katalogu NEXUS albo /var/lib/libvirt/images")
    return target

def cupertino_ovmf_code_candidates():
    return [
        "/usr/share/OVMF/OVMF_CODE.fd",
        "/usr/share/OVMF/OVMF_CODE_4M.fd",
        "/usr/share/OVMF/OVMF_CODE.secboot.fd",
        "/usr/share/edk2/ovmf/OVMF_CODE.fd",
        "/usr/share/qemu/OVMF_CODE.fd",
    ]

def cupertino_ovmf_vars_candidates():
    return [
        "/usr/share/OVMF/OVMF_VARS.fd",
        "/usr/share/OVMF/OVMF_VARS_4M.fd",
        "/usr/share/OVMF/OVMF_VARS.ms.fd",
        "/usr/share/edk2/ovmf/OVMF_VARS.fd",
        "/usr/share/qemu/OVMF_VARS.fd",
    ]

def cupertino_opencore_candidates():
    return [
        NEXUS_ISO_STORAGE_DIR / "opencore.qcow2",
        NEXUS_ISO_STORAGE_DIR / "OpenCore.qcow2",
        LIBVIRT_IMAGE_DIR / "opencore.qcow2",
        LIBVIRT_IMAGE_DIR / "OpenCore.qcow2",
        LIBVIRT_ISO_DIR / "opencore.qcow2",
        LIBVIRT_ISO_DIR / "OpenCore.qcow2",
        ISO_DIR / "opencore.qcow2",
        ISO_DIR / "OpenCore.qcow2",
        BASE_DIR / "opencore.qcow2",
        BASE_DIR / "OpenCore.qcow2",
    ]

def qemu_img_info(path: Path):
    if not shutil.which("qemu-img"):
        return {"ok": False, "error": "Brak qemu-img"}
    code, output = run_vm_command(["qemu-img", "info", str(path)], timeout=30)
    if code != 0 and "lock" in (output or "").lower():
        code, output = run_vm_command(["qemu-img", "info", "-U", str(path)], timeout=30)
    return {"ok": code == 0, "output": output.strip()[:1600], "code": code}

def qemu_img_info_json(path: Path):
    path = Path(path).resolve()
    if not path.exists() or not path.is_file():
        return {"ok": False, "error": "Plik dysku nie istnieje", "path": str(path)}
    if not shutil.which("qemu-img"):
        return {"ok": False, "error": "Brak qemu-img", "path": str(path)}
    code, output = run_vm_command(["qemu-img", "info", "--output=json", str(path)], timeout=30)
    if code != 0 and "lock" in (output or "").lower():
        code, output = run_vm_command(["qemu-img", "info", "-U", "--output=json", str(path)], timeout=30)
    data = {}
    if code == 0:
        try:
            data = json.loads(output or "{}")
        except Exception:
            data = {}
    stat_size = path.stat().st_size
    virtual_size = int(data.get("virtual-size") or data.get("virtual_size") or 0)
    actual_size = int(data.get("actual-size") or data.get("actual_size") or stat_size)
    return {
        "ok": code == 0,
        "code": code,
        "path": str(path),
        "format": data.get("format") or path.suffix.lower().lstrip("."),
        "virtual_size": virtual_size,
        "actual_size": actual_size,
        "file_size": stat_size,
        "virtual_size_label": fmt_size(virtual_size) if virtual_size else "--",
        "actual_size_label": fmt_size(actual_size) if actual_size else fmt_size(stat_size),
        "file_size_label": fmt_size(stat_size),
        "thin_ratio": round((actual_size / virtual_size) * 100, 2) if virtual_size else None,
        "data": data,
        "output": output.strip()[:2000],
    }

def path_is_under(path: Path, parent: Path):
    try:
        Path(path).resolve().relative_to(Path(parent).resolve())
        return True
    except Exception:
        return False

def qemu_backing_path(info: dict):
    data = info.get("data") if isinstance(info, dict) else {}
    raw = ""
    if isinstance(data, dict):
        raw = data.get("full-backing-filename") or data.get("backing-filename") or ""
    if not raw:
        return None
    try:
        return Path(raw).resolve()
    except Exception:
        return None

def gpt_partition_offsets(raw: bytes):
    parts = []
    if len(raw) > 1024 and raw[512:520] == b"EFI PART":
        part_lba = struct.unpack_from("<Q", raw, 512 + 72)[0]
        num = struct.unpack_from("<I", raw, 512 + 80)[0]
        entsz = struct.unpack_from("<I", raw, 512 + 84)[0]
        for index in range(min(num, 128)):
            off = part_lba * 512 + index * entsz
            ent = raw[off:off + entsz]
            if not ent.strip(b"\x00"):
                continue
            first = struct.unpack_from("<Q", ent, 32)[0]
            last = struct.unpack_from("<Q", ent, 40)[0]
            if first and last >= first:
                parts.append((first * 512, (last - first + 1) * 512))
    if not parts and len(raw) > 512:
        for index in range(4):
            off = 446 + index * 16
            ent = raw[off:off + 16]
            ptype = ent[4]
            start = struct.unpack_from("<I", ent, 8)[0]
            size = struct.unpack_from("<I", ent, 12)[0]
            if ptype and start and size:
                parts.append((start * 512, size * 512))
    return parts

def fat16_find_file(raw: bytearray, part_offset: int, wanted_path: str):
    bs = raw[part_offset:part_offset + 512]
    if len(bs) < 64 or bs[510:512] != b"\x55\xaa":
        return None
    bps = struct.unpack_from("<H", bs, 11)[0]
    spc = bs[13]
    reserved = struct.unpack_from("<H", bs, 14)[0]
    nfats = bs[16]
    root_entries = struct.unpack_from("<H", bs, 17)[0]
    fatsz = struct.unpack_from("<H", bs, 22)[0]
    if bps not in {512, 1024, 2048, 4096} or not spc or not reserved or not nfats or not root_entries or not fatsz:
        return None
    root_secs = ((root_entries * 32) + (bps - 1)) // bps
    fat_off = part_offset + reserved * bps
    root_off = part_offset + (reserved + nfats * fatsz) * bps
    data_off = root_off + root_secs * bps

    def cluster_offset(cluster: int):
        return data_off + (cluster - 2) * spc * bps

    def next_cluster(cluster: int):
        return struct.unpack_from("<H", raw, fat_off + cluster * 2)[0]

    def cluster_chain(cluster: int):
        chain = []
        seen = set()
        while 2 <= cluster < 0xFFF8 and cluster not in seen:
            seen.add(cluster)
            chain.append(cluster)
            cluster = next_cluster(cluster)
        return chain

    def lfn_part(entry: bytes):
        chars = entry[1:11] + entry[14:26] + entry[28:32]
        return chars.decode("utf-16le", "ignore").rstrip("\uffff").rstrip("\x00")

    wanted = wanted_path.strip("/").lower()

    def scan_dir(blob: bytes, prefix: str = ""):
        lfn = []
        for pos in range(0, len(blob), 32):
            entry = blob[pos:pos + 32]
            if len(entry) < 32 or entry[0] == 0:
                break
            if entry[0] == 0xE5:
                lfn = []
                continue
            attr = entry[11]
            if attr == 0x0F:
                lfn.insert(0, lfn_part(entry))
                continue
            short = (entry[:8].decode("ascii", "ignore").rstrip() + (("." + entry[8:11].decode("ascii", "ignore").rstrip()) if entry[8:11].strip() else "")).strip()
            name = "".join(lfn) if lfn else short
            lfn = []
            if not name or name in {".", ".."}:
                continue
            cluster = struct.unpack_from("<H", entry, 26)[0]
            size = struct.unpack_from("<I", entry, 28)[0]
            current = f"{prefix}/{name}".strip("/")
            if current.lower() == wanted:
                chain = cluster_chain(cluster) if cluster >= 2 else []
                return {"entry_offset": root_off + pos if not prefix else None, "cluster": cluster, "size": size, "chain": chain, "bps": bps, "spc": spc, "data_off": data_off}
            if attr & 0x10 and cluster >= 2:
                chain = cluster_chain(cluster)
                child = b"".join(raw[cluster_offset(c):cluster_offset(c) + spc * bps] for c in chain)
                found = scan_dir(child, current)
                if found:
                    return found
        return None

    def scan_dir_with_entry_offsets(blob: bytes, base_offset: int, prefix: str = ""):
        lfn = []
        for pos in range(0, len(blob), 32):
            entry = blob[pos:pos + 32]
            if len(entry) < 32 or entry[0] == 0:
                break
            if entry[0] == 0xE5:
                lfn = []
                continue
            attr = entry[11]
            if attr == 0x0F:
                lfn.insert(0, lfn_part(entry))
                continue
            short = (entry[:8].decode("ascii", "ignore").rstrip() + (("." + entry[8:11].decode("ascii", "ignore").rstrip()) if entry[8:11].strip() else "")).strip()
            name = "".join(lfn) if lfn else short
            lfn = []
            if not name or name in {".", ".."}:
                continue
            cluster = struct.unpack_from("<H", entry, 26)[0]
            size = struct.unpack_from("<I", entry, 28)[0]
            current = f"{prefix}/{name}".strip("/")
            if current.lower() == wanted:
                chain = cluster_chain(cluster) if cluster >= 2 else []
                return {"entry_offset": base_offset + pos, "cluster": cluster, "size": size, "chain": chain, "bps": bps, "spc": spc, "data_off": data_off}
            if attr & 0x10 and cluster >= 2:
                chain = cluster_chain(cluster)
                for c in chain:
                    child_off = cluster_offset(c)
                    child = raw[child_off:child_off + spc * bps]
                    found = scan_dir_with_entry_offsets(child, child_off, current)
                    if found:
                        return found
        return None

    root_blob = raw[root_off:root_off + root_secs * bps]
    return scan_dir_with_entry_offsets(root_blob, root_off)

def patch_opencore_config_raw(raw_path: Path):
    raw = bytearray(Path(raw_path).read_bytes())
    for offset, _size in gpt_partition_offsets(raw):
        item = fat16_find_file(raw, offset, "EFI/OC/config.plist")
        if not item or not item.get("chain") or item.get("entry_offset") is None:
            continue
        cluster_size = item["spc"] * item["bps"]
        blob = b"".join(raw[item["data_off"] + (cluster - 2) * cluster_size:item["data_off"] + (cluster - 1) * cluster_size] for cluster in item["chain"])
        config_bytes = blob[:item["size"]]
        config = plistlib.loads(config_bytes)
        misc = config.setdefault("Misc", {})
        boot = misc.setdefault("Boot", {})
        security = misc.setdefault("Security", {})
        bless = misc.setdefault("BlessOverride", [])
        uefi = config.setdefault("UEFI", {})
        drivers = uefi.setdefault("Drivers", [])
        changed = False
        if boot.get("HideAuxiliary") is not False:
            boot["HideAuxiliary"] = False
            changed = True
        if security.get("ScanPolicy") != 0:
            security["ScanPolicy"] = 0
            changed = True
        for boot_path in (r"\System\Library\CoreServices\boot.efi", r"\System\Library\CoreServices\bootbase.efi"):
            if boot_path not in bless:
                bless.append(boot_path)
                changed = True
        if isinstance(drivers, list):
            driver_paths = []
            for driver_item in drivers:
                if isinstance(driver_item, dict):
                    path = str(driver_item.get("Path") or "")
                    driver_paths.append(path.lower())
                    if path.lower() == "openpartitiondxe.efi" and not driver_item.get("Enabled", False):
                        driver_item["Enabled"] = True
                        changed = True
                elif isinstance(driver_item, str):
                    driver_paths.append(driver_item.lower())
            if "openpartitiondxe.efi" not in driver_paths:
                partition_driver = {
                    "Arguments": "",
                    "Comment": "OpenPartitionDxe.efi - Apple Partition Map scanner for legacy macOS installers",
                    "Enabled": True,
                    "LoadEarly": False,
                    "Path": "OpenPartitionDxe.efi",
                }
                insert_at = 0
                for idx, driver_item in enumerate(drivers):
                    if isinstance(driver_item, dict) and str(driver_item.get("Path") or "").lower() == "opencanopy.efi":
                        insert_at = idx + 1
                        break
                drivers.insert(insert_at, partition_driver)
                changed = True
        quirks = uefi.setdefault("Quirks", {})
        if isinstance(quirks, dict) and quirks.get("UnblockFsConnect") is not True:
            quirks["UnblockFsConnect"] = True
            changed = True
        if not changed:
            return {"status": "already_patched", "path": "EFI/OC/config.plist"}
        new_bytes = plistlib.dumps(config, fmt=plistlib.FMT_XML, sort_keys=False)
        capacity = len(item["chain"]) * cluster_size
        if len(new_bytes) > capacity:
            raise RuntimeError(f"OpenCore config.plist po patchu ma {len(new_bytes)} B, a lancuch FAT ma {capacity} B")
        padded = new_bytes + b"\x00" * (capacity - len(new_bytes))
        cursor = 0
        for cluster in item["chain"]:
            off = item["data_off"] + (cluster - 2) * cluster_size
            raw[off:off + cluster_size] = padded[cursor:cursor + cluster_size]
            cursor += cluster_size
        struct.pack_into("<I", raw, item["entry_offset"] + 28, len(new_bytes))
        Path(raw_path).write_bytes(raw)
        return {"status": "patched", "path": "EFI/OC/config.plist", "old_size": item["size"], "new_size": len(new_bytes)}
    return {"status": "not_found", "path": "EFI/OC/config.plist"}

def patch_opencore_overlay_picker(image_path: Path):
    image_path = Path(image_path).resolve()
    if not shutil.which("qemu-img") or not image_path.exists():
        return {"status": "skipped", "reason": "qemu-img lub obraz niedostepny", "path": str(image_path)}
    with tempfile.TemporaryDirectory(prefix="nexus-opencore-patch-") as tmp:
        raw_path = Path(tmp) / "opencore.raw"
        patched_qcow2 = Path(tmp) / "opencore-patched.qcow2"
        code, output = run_vm_command(["qemu-img", "convert", "-O", "raw", str(image_path), str(raw_path)], timeout=120)
        if code != 0:
            return {"status": "warning", "stage": "convert-raw", "output": output.strip()[:1200], "path": str(image_path)}
        patch = patch_opencore_config_raw(raw_path)
        if patch.get("status") not in {"patched", "already_patched"}:
            return {"status": "warning", "stage": "patch-config", "patch": patch, "path": str(image_path)}
        if patch.get("status") == "patched":
            code, output = run_vm_command(["qemu-img", "convert", "-O", "qcow2", str(raw_path), str(patched_qcow2)], timeout=120)
            if code != 0:
                return {"status": "warning", "stage": "convert-qcow2", "output": output.strip()[:1200], "path": str(image_path)}
            shutil.move(str(patched_qcow2), str(image_path))
            ensure_libvirt_file_access(image_path)
            log_event(f"VM_CUPERTINO_OPENCORE_PICKER_PATCH image={image_path} status=patched")
        return {"status": patch.get("status"), "patch": patch, "path": str(image_path)}

def ensure_qcow2_overlay(overlay: Path, base_path: Path, label: str):
    base_path = Path(base_path).resolve()
    overlay = Path(overlay).resolve()
    if not base_path.exists():
        raise HTTPException(status_code=412, detail=f"Brak bazowego obrazu dla overlay {label}")
    ensure_libvirt_file_access(base_path)
    base_info = qemu_img_info_json(base_path)
    if not base_info.get("ok"):
        raise HTTPException(status_code=412, detail={"message": f"qemu-img nie potwierdzil bazowego obrazu {label}", "base": str(base_path), "info": base_info})
    base_format = (base_info.get("format") or "raw").lower()
    overlay.parent.mkdir(parents=True, exist_ok=True)
    ensure_libvirt_file_access(overlay.parent, is_dir=True)
    if overlay.exists():
        info = qemu_img_info_json(overlay)
        backing = qemu_backing_path(info)
        if info.get("ok") and backing and backing == base_path:
            ensure_libvirt_file_access(overlay)
            return {"path": overlay, "created": False, "base": str(base_path), "info": info}
        try:
            overlay.unlink()
        except Exception:
            pass
    command = ["qemu-img", "create", "-f", "qcow2", "-F", base_format, "-b", str(base_path), str(overlay)]
    code, output = run_vm_command(command, timeout=60)
    if code != 0:
        raise HTTPException(status_code=500, detail={"message": f"Nie udalo sie utworzyc overlay {label}", "command": command, "output": output.strip()})
    ensure_libvirt_file_access(overlay)
    info = qemu_img_info_json(overlay)
    log_event(f"VM_QCOW2_OVERLAY label={label} overlay={overlay} base={base_path} created=1")
    return {"path": overlay, "created": True, "base": str(base_path), "info": info, "output": output.strip()[:1200]}

def opencore_overlay_path(vm_id: str):
    return (OPENCORE_OVERLAY_DIR / f"{safe_vm_target(vm_id)}-opencore.qcow2").resolve()

def cupertino_media_overlay_path(vm_id: str, source_path: Path):
    source_path = Path(source_path).resolve()
    digest = hashlib.sha1(str(source_path).encode("utf-8")).hexdigest()[:12]
    stem = safe_vm_target(source_path.stem)[:42] or "installer"
    return (CUPERTINO_MEDIA_OVERLAY_DIR / f"{safe_vm_target(vm_id)}-{stem}-{digest}-media.qcow2").resolve()

def cupertino_base_opencore_path(path: Path):
    candidate = Path(path).resolve()
    if path_is_under(candidate, OPENCORE_OVERLAY_DIR) or path_is_under(candidate, CUPERTINO_MEDIA_OVERLAY_DIR):
        fallback = existing_first(cupertino_opencore_candidates())
        if fallback:
            return fallback.resolve()
    return candidate

def ensure_cupertino_opencore_overlay(vm_id: str, base_opencore: Path):
    base_opencore = cupertino_base_opencore_path(base_opencore)
    overlay = ensure_qcow2_overlay(opencore_overlay_path(vm_id), base_opencore, f"cupertino-opencore:{safe_vm_target(vm_id)}")
    picker_patch = patch_opencore_overlay_picker(overlay["path"])
    overlay["picker_patch"] = picker_patch
    return overlay

def ensure_cupertino_installer_overlay(vm_id: str, installer: Path):
    installer = Path(installer).resolve()
    return ensure_qcow2_overlay(cupertino_media_overlay_path(vm_id, installer), installer, f"cupertino-installer:{safe_vm_target(vm_id)}")

def qemu_disk_driver_attrs(fmt: str = "qcow2", bus: str = "", readonly: bool = False, trim: bool = True):
    fmt = (fmt or "qcow2").lower()
    bus = (bus or "").lower()
    attrs = {"name": "qemu", "type": fmt, "cache": "none"}
    if trim and fmt in {"qcow2", "raw"} and not readonly and bus not in {"ide"}:
        attrs.update({"discard": "unmap", "detect_zeroes": "unmap"})
    return attrs

def qemu_disk_arg(path: Path, fmt: str = "qcow2", bus: str = "virtio", readonly: bool = False, device: str = ""):
    attrs = qemu_disk_driver_attrs(fmt, bus, readonly)
    parts = [f"path={path}", f"format={fmt}", f"bus={bus}", "cache=none"]
    if device:
        parts.append(f"device={device}")
    if readonly:
        parts.append("readonly=on")
    if "discard" in attrs:
        parts.append("discard=unmap")
    if "detect_zeroes" in attrs:
        parts.append("detect_zeroes=unmap")
    return ",".join(parts)

def create_dynamic_disk(disk_path: Path, size_gb: int):
    disk_path = Path(disk_path).resolve()
    size_gb = max(1, int(size_gb or 1))
    if not shutil.which("qemu-img"):
        raise HTTPException(status_code=501, detail="Brak qemu-img do tworzenia dynamicznych dyskow qcow2")
    disk_path.parent.mkdir(parents=True, exist_ok=True)
    attempts = []
    commands = [
        ["qemu-img", "create", "-f", "qcow2", "-o", "compat=1.1,lazy_refcounts=on", str(disk_path), f"{size_gb}G"],
        ["qemu-img", "create", "-f", "qcow2", str(disk_path), f"{size_gb}G"],
    ]
    for cmd in commands:
        code, output = run_vm_command(cmd, timeout=60)
        attempts.append({"command": cmd, "code": code, "output": output.strip()[-1200:]})
        if code == 0:
            ensure_libvirt_file_access(disk_path)
            info = qemu_img_info_json(disk_path)
            log_event(f"VM_DYNAMIC_DISK_CREATE path={disk_path} size_gb={size_gb} actual={info.get('actual_size_label')}")
            return {
                "status": "created",
                "path": str(disk_path),
                "size_gb": size_gb,
                "thin_provisioned": True,
                "driver": "qcow2 discard=unmap detect_zeroes=unmap",
                "attempts": attempts,
                "info": info,
            }
        try:
            if disk_path.exists():
                disk_path.unlink()
        except Exception:
            pass
    raise HTTPException(status_code=500, detail={"message": "Nie udalo sie utworzyc dynamicznego dysku qcow2", "attempts": attempts})

def parse_domain_disk_trim(vm_id: str):
    target = safe_vm_target(vm_id)
    try:
        root = ET.fromstring(dump_domain_xml(target, inactive=True))
    except Exception:
        return {}
    rows = {}
    for disk in root.findall("./devices/disk"):
        source = disk.find("source")
        driver = disk.find("driver")
        target_node_el = disk.find("target")
        source_file = source.attrib.get("file", "") if source is not None else ""
        if not source_file:
            continue
        rows[str(Path(source_file).resolve())] = {
            "device": disk.attrib.get("device", ""),
            "target": target_node_el.attrib.get("dev", "") if target_node_el is not None else "",
            "bus": target_node_el.attrib.get("bus", "") if target_node_el is not None else "",
            "driver": dict(driver.attrib) if driver is not None else {},
            "discard": (driver.attrib.get("discard", "") if driver is not None else ""),
            "detect_zeroes": (driver.attrib.get("detect_zeroes", "") if driver is not None else ""),
            "trim_enabled": bool(driver is not None and driver.attrib.get("discard") == "unmap" and driver.attrib.get("detect_zeroes") == "unmap"),
        }
    return rows

def vm_storage_thin_report(vm_id: str = "", path: str = ""):
    paths = []
    trim_map = {}
    if vm_id:
        target = safe_vm_target(vm_id)
        paths.extend(vm_storage_paths(target))
        trim_map = parse_domain_disk_trim(target)
    if path:
        paths.append(allowed_vm_disk_path(path))
    unique = []
    seen = set()
    for item in paths:
        try:
            resolved = Path(item).resolve()
        except Exception:
            continue
        if str(resolved) not in seen:
            seen.add(str(resolved))
            unique.append(resolved)
    disks = []
    for item in unique:
        info = qemu_img_info_json(item)
        trim = trim_map.get(str(item.resolve()), {})
        disks.append({
            "path": str(item),
            "name": item.name,
            "format": info.get("format"),
            "virtual_size": info.get("virtual_size"),
            "actual_size": info.get("actual_size"),
            "file_size": info.get("file_size"),
            "virtual_size_label": info.get("virtual_size_label"),
            "actual_size_label": info.get("actual_size_label"),
            "file_size_label": info.get("file_size_label"),
            "thin_ratio": info.get("thin_ratio"),
            "thin_provisioned": (info.get("format") == "qcow2"),
            "trim": trim,
            "qemu_img": info,
        })
    return {
        "status": "ok",
        "vm_id": vm_id or "",
        "disks": disks,
        "guest_trim": {
            "linux": "W VM uruchom sudo fstrim -av albo wlacz fstrim.timer.",
            "windows": "Windows wysyla TRIM automatycznie, gdy dysk/kontroler raportuje obsluge discard.",
        },
        "policy": "Nowe dyski NEXUS sa qcow2 thin; dla nie-IDE XML dostaje discard=unmap i detect_zeroes=unmap.",
    }

def apply_vm_thin_policy(vm_id: str):
    target = safe_vm_target(vm_id)
    xml_text = dump_domain_xml(target, inactive=True)
    try:
        root = ET.fromstring(xml_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Nie udalo sie parsowac XML VM: {exc}")
    changed = []
    skipped = []
    for disk in root.findall("./devices/disk"):
        if disk.attrib.get("device") != "disk":
            continue
        source = disk.find("source")
        target_node_el = disk.find("target")
        source_file = source.attrib.get("file", "") if source is not None else ""
        bus = target_node_el.attrib.get("bus", "") if target_node_el is not None else ""
        dev = target_node_el.attrib.get("dev", "") if target_node_el is not None else ""
        readonly = disk.find("readonly") is not None
        suffix = Path(source_file).suffix.lower()
        if readonly or bus == "ide" or suffix not in {".qcow2", ".raw", ".img"}:
            skipped.append({"target": dev, "bus": bus, "source": source_file, "reason": "readonly/ide/non-disk"})
            continue
        fmt = "qcow2" if suffix == ".qcow2" else "raw"
        driver = ensure_child(disk, "driver")
        before = dict(driver.attrib)
        driver.attrib.clear()
        driver.attrib.update(qemu_disk_driver_attrs(fmt, bus, readonly=False))
        after = dict(driver.attrib)
        if before != after:
            changed.append({"target": dev, "bus": bus, "source": source_file, "before": before, "after": after})
    if changed:
        define_domain_xml_transaction(target, root, "thin-storage")
    return {
        "status": "updated" if changed else "noop",
        "vm_id": target,
        "changed": changed,
        "skipped": skipped,
        "requires_restart": vm_is_running_name(target),
        "report": vm_storage_thin_report(target),
    }

def cupertino_prerequisites(opencore_path: str = "", ovmf_code_path: str = "", ovmf_vars_path: str = ""):
    missing = []
    warnings = []
    ovmf_code = safe_firmware_path(ovmf_code_path, "OVMF_CODE") if ovmf_code_path else existing_first(cupertino_ovmf_code_candidates())
    ovmf_vars = safe_firmware_path(ovmf_vars_path, "OVMF_VARS") if ovmf_vars_path else existing_first(cupertino_ovmf_vars_candidates())
    if opencore_path:
        if not Path(str(opencore_path)).is_absolute() and not re.search(r"[\\/]", str(opencore_path)):
            opencore = resolve_media_filename(opencore_path, VM_DISK_IMAGE_EXT)
            if not opencore:
                candidate = NEXUS_ISO_STORAGE_DIR / opencore_path
                opencore = candidate.resolve() if candidate.exists() else None
        else:
            try:
                opencore = allowed_vm_disk_path(opencore_path)
            except HTTPException as exc:
                warnings.append(str(exc.detail))
                opencore = None
    else:
        opencore = existing_first(cupertino_opencore_candidates())
    if not ovmf_code:
        missing.append("OVMF_CODE.fd")
    if not ovmf_vars:
        missing.append("OVMF_VARS.fd")
    if not opencore:
        missing.append("opencore.qcow2")
    opencore_info = {}
    if opencore:
        ensure_libvirt_file_access(opencore)
        opencore_info = qemu_img_info(opencore)
        if not opencore_info.get("ok"):
            missing.append("poprawny opencore.qcow2")
            warnings.append(opencore_info.get("error") or opencore_info.get("output") or "qemu-img nie potwierdzil OpenCore")
    ready = not missing
    return {
        "status": "ready" if ready else "missing",
        "ok": ready,
        "ready": ready,
        "missing": missing,
        "warnings": warnings,
        "ovmf_code": str(ovmf_code or ""),
        "ovmf_vars": str(ovmf_vars or ""),
        "opencore": str(opencore or ""),
        "iso_storage": str(NEXUS_ISO_STORAGE_DIR),
        "expected_opencore": str(NEXUS_ISO_STORAGE_DIR / "opencore.qcow2"),
        "opencore_info": opencore_info,
        "legal_shield": {
            "mode": "BYOL",
            "smc_osk_stored": False,
            "note": "NEXUS nie przechowuje i nie wstrzykuje chronionych kluczy Apple. Uzytkownik dostarcza legalny bootloader/obraz.",
        },
    }

def vm_block_devices(vm_id: str):
    target = safe_vm_target(vm_id)
    code, output = run_vm_command(["virsh", "domblklist", target, "--details"], timeout=10)
    rows = []
    if code != 0:
        return rows
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[0].lower() in {"type", "-"}:
            continue
        source = " ".join(parts[3:])
        rows.append({
            "type": parts[0],
            "device": parts[1].lower(),
            "target": parts[2],
            "source": "" if source == "-" else source,
            "raw": line,
        })
    return rows

def vm_cdrom_targets(vm_id: str):
    return [row for row in vm_block_devices(vm_id) if row.get("device") == "cdrom"]

def xml_devices_node(root):
    devices = root.find("devices")
    if devices is None:
        devices = ET.SubElement(root, "devices")
    return devices

def xml_cdrom_rows(root):
    rows = []
    for disk in xml_devices_node(root).findall("disk"):
        if (disk.attrib.get("device") or "").lower() != "cdrom":
            continue
        target = disk.find("target")
        source = disk.find("source")
        driver = disk.find("driver")
        rows.append({
            "device": "cdrom",
            "target": target.attrib.get("dev", "") if target is not None else "",
            "bus": target.attrib.get("bus", "") if target is not None else "",
            "source": disk_source_text(disk),
            "driver_type": driver.attrib.get("type", "") if driver is not None else "",
        })
    return rows

def vm_cdrom_config_rows(vm_id: str):
    root, _ = vm_dumpxml_root(vm_id, inactive=True)
    return xml_cdrom_rows(root)

def cdrom_bus_for_target(dev: str, fallback: str = "ide"):
    dev = (dev or "").lower()
    if dev.startswith("hd"):
        return "ide"
    if dev.startswith("sd"):
        return "sata"
    return fallback or "ide"

def vm_cdrom_preferred_bus(vm_id: str, driver_media: bool = False):
    profile = vm_firmware_profile(vm_id)
    machine = (profile.get("machine") or "").lower()
    firmware = (profile.get("firmware") or "").lower()
    if driver_media or firmware == "uefi" or "q35" in machine:
        return "sata"
    return "ide"

def choose_cdrom_target(block_devices, config_cdroms=None, requested: str = "", preferred_bus: str = "ide"):
    requested = safe_block_target(requested)
    used = {str(row.get("target") or "").lower() for row in (block_devices or [])}
    used.update(str(row.get("target") or "").lower() for row in (config_cdroms or []) if row.get("target"))
    if requested:
        if requested in used:
            matching = [row for row in (config_cdroms or []) if str(row.get("target") or "").lower() == requested and row.get("device") == "cdrom"]
            if matching:
                return requested
            raise HTTPException(status_code=409, detail=f"Target CD-ROM {requested} jest juz zajety przez inne urzadzenie")
        return requested
    ide_targets = ["hda", "hdc", "hdd", "hdb"]
    sata_targets = ["sdb", "sdc", "sdd", "sde"]
    candidates = (ide_targets + sata_targets) if preferred_bus == "ide" else (sata_targets + ide_targets)
    for dev in candidates:
        if dev not in used:
            return dev
    raise HTTPException(status_code=409, detail="Brak wolnego targetu CD-ROM dla VM")

def normalize_vm_cdrom_bus_policy(vm_id: str, preferred_bus: str):
    target = safe_vm_target(vm_id)
    preferred_bus = (preferred_bus or "").lower()
    if preferred_bus not in {"sata", "ide"}:
        return {"status": "skipped", "changed": False, "reason": "unsupported-preferred-bus", "preferred_bus": preferred_bus}
    if preferred_bus != "sata":
        return {"status": "skipped", "changed": False, "reason": "legacy-ide-ok", "preferred_bus": preferred_bus}
    if vm_is_running_name(target):
        return {"status": "skipped", "changed": False, "reason": "vm-running-requires-restart-for-bus-rewire", "preferred_bus": preferred_bus}
    root, _ = vm_dumpxml_root(target, inactive=True)
    devices = xml_devices_node(root)
    used_targets = set()
    for disk in devices.findall("disk"):
        target_el = disk.find("target")
        if target_el is not None and target_el.attrib.get("dev"):
            used_targets.add(target_el.attrib.get("dev", "").lower())
    changed = []
    sata_targets = ["sdb", "sdc", "sdd", "sde", "sdf", "sdg"]
    for disk in devices.findall("disk"):
        if (disk.attrib.get("device") or "").lower() != "cdrom":
            continue
        target_el = disk.find("target")
        if target_el is None:
            target_el = ET.SubElement(disk, "target")
        old_dev = (target_el.attrib.get("dev") or "").lower()
        old_bus = (target_el.attrib.get("bus") or "").lower()
        if old_bus == "sata" and old_dev.startswith("sd"):
            continue
        used_targets.discard(old_dev)
        new_dev = next((candidate for candidate in sata_targets if candidate not in used_targets), "")
        if not new_dev:
            used_targets.add(old_dev)
            continue
        before = {"target": old_dev, "bus": old_bus}
        target_el.attrib["dev"] = new_dev
        target_el.attrib["bus"] = "sata"
        for address in list(disk.findall("address")):
            disk.remove(address)
        used_targets.add(new_dev)
        changed.append({"before": before, "after": {"target": new_dev, "bus": "sata"}, "source": disk_source_text(disk)})
    if not changed:
        return {"status": "noop", "changed": False, "preferred_bus": preferred_bus}
    define = define_domain_xml_transaction(target, root, "cdrom-bus-policy")
    log_event(f"VM_CDROM_BUS_POLICY vm={target} changed={len(changed)} preferred={preferred_bus}")
    return {"status": "updated", "changed": True, "preferred_bus": preferred_bus, "rewired": changed, "define": define}

def cdrom_device_xml(iso: Path = None, target_dev: str = "hdc", bus: str = "ide"):
    target_dev = safe_block_target(target_dev) or "hdc"
    bus = re.sub(r"[^a-z0-9_-]+", "", (bus or cdrom_bus_for_target(target_dev)).lower()) or cdrom_bus_for_target(target_dev)
    source_line = f"\n  <source file='{html.escape(str(iso), quote=True)}'/>" if iso else ""
    return f"""<disk type='file' device='cdrom'>
  <driver name='qemu' type='raw'/>{source_line}
  <target dev='{target_dev}' bus='{bus}'/>
  <readonly/>
</disk>
"""

def write_device_xml(label: str, target: str, xml_text: str):
    path = Path("/tmp") / f"nexus-device-{label}-{safe_vm_target(target)}-{uuid.uuid4().hex[:10]}.xml"
    path.write_text(xml_text, encoding="utf-8")
    return path

def ensure_vm_cdrom_slot(vm_id: str, target_dev: str = "", live: bool = True, config: bool = True, preferred_bus: str = "ide"):
    target = safe_vm_target(vm_id)
    target_dev = safe_block_target(target_dev)
    block_devices = vm_block_devices(target)
    root, _ = vm_dumpxml_root(target, inactive=True)
    config_cdroms = xml_cdrom_rows(root)
    existing = next((row for row in config_cdroms if target_dev and str(row.get("target") or "").lower() == target_dev), None)
    if not target_dev and config_cdroms:
        return {"changed": False, "target": config_cdroms[0].get("target"), "bus": config_cdroms[0].get("bus") or cdrom_bus_for_target(config_cdroms[0].get("target")), "config_cdroms": config_cdroms, "live_attempt": None}
    if existing:
        return {"changed": False, "target": existing.get("target"), "bus": existing.get("bus") or cdrom_bus_for_target(existing.get("target")), "config_cdroms": config_cdroms, "live_attempt": None}

    dev = choose_cdrom_target(block_devices, config_cdroms, target_dev, preferred_bus=preferred_bus)
    bus = cdrom_bus_for_target(dev, preferred_bus)
    disk = ET.SubElement(xml_devices_node(root), "disk", {"type": "file", "device": "cdrom"})
    ET.SubElement(disk, "driver", {"name": "qemu", "type": "raw"})
    ET.SubElement(disk, "target", {"dev": dev, "bus": bus})
    ET.SubElement(disk, "readonly")
    define_result = None
    if config:
        define_result = define_domain_xml_transaction(target, root, "ensure-cdrom")

    live_attempt = None
    if live and vm_is_running_name(target):
        xml_path = write_device_xml("empty-cdrom", target, cdrom_device_xml(None, dev, bus))
        try:
            code, output = run_vm_command(["virsh", "attach-device", target, str(xml_path), "--live"], timeout=30)
            live_attempt = {"mode": "attach-empty-cdrom", "target": dev, "bus": bus, "code": code, "output": output.strip()}
        finally:
            try:
                xml_path.unlink()
            except Exception:
                pass
    log_event(f"VM_CDROM_SLOT vm={target} target={dev} bus={bus} config={bool(define_result)} live_code={(live_attempt or {}).get('code')}")
    return {"changed": True, "target": dev, "bus": bus, "define": define_result, "config_cdroms": vm_cdrom_config_rows(target), "live_attempt": live_attempt}

def vm_interface_rows(vm_id: str):
    target = safe_vm_target(vm_id)
    code, output = run_vm_command(["virsh", "domiflist", target], timeout=10)
    rows = []
    if code != 0:
        return rows
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 5 or parts[0].lower() in {"interface", "-"}:
            continue
        rows.append({
            "interface": parts[0],
            "type": parts[1],
            "source": parts[2],
            "model": parts[3],
            "mac": parts[4],
            "raw": line,
        })
    return rows

def vm_is_running_name(vm_id: str):
    code, output = run_vm_command(["virsh", "domstate", safe_vm_target(vm_id)], timeout=8)
    return code == 0 and "running" in output.lower()

def vm_domain_state_label(vm_id: str):
    code, output = run_vm_command(["virsh", "domstate", safe_vm_target(vm_id)], timeout=8)
    if code != 0:
        raise HTTPException(status_code=404, detail=output.strip() or "Nie znaleziono VM")
    return (output or "").strip().lower()

def vm_iso_flags(vm_id: str, live=True, config=True):
    flags = []
    if live and vm_is_running_name(vm_id):
        flags.append("--live")
    if config:
        flags.append("--config")
    if not flags:
        flags.append("--current")
    return flags

def virsh_flag_variants(flags):
    variants = [list(flags or [])]
    flags_set = set(flags or [])
    if "--live" in flags_set and "--config" in flags_set:
        variants.extend([["--live"], ["--config"]])
    if not variants[0]:
        variants[0] = ["--current"]
    unique = []
    seen = set()
    for item in variants:
        key = tuple(item)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique

def vm_disk_format(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".qcow2":
        return "qcow2"
    if suffix == ".raw" or suffix == ".img":
        return "raw"
    raise HTTPException(status_code=400, detail="Dysk VM musi byc .qcow2, .raw albo .img")

def normalize_vm_disk_bus(bus: str):
    value = re.sub(r"[^a-z0-9_-]+", "", (bus or "ide").lower()) or "ide"
    if value not in {"ide", "sata", "virtio", "scsi", "usb"}:
        raise HTTPException(status_code=400, detail="Bus dysku musi byc: ide, sata, virtio, scsi albo usb")
    return value

def default_disk_targets_for_bus(bus: str):
    if bus == "virtio":
        return ["vdb", "vdc", "vdd", "vde", "vdf"]
    if bus == "scsi":
        return ["sdb", "sdc", "sdd", "sde", "sdf"]
    if bus == "sata":
        return ["sdb", "sdc", "sdd", "sde", "sdf"]
    if bus == "usb":
        return ["sdb", "sdc", "sdd", "sde", "sdf"]
    return ["hdb", "hdc", "hdd"]

def pick_free_disk_target(block_devices, bus: str, requested: str = ""):
    requested = re.sub(r"[^a-z0-9]+", "", (requested or "").lower())
    used = {str(row.get("target") or "").lower() for row in block_devices}
    if requested:
        if requested in used:
            raise HTTPException(status_code=409, detail=f"Target dysku {requested} jest juz zajety")
        return requested
    for dev in default_disk_targets_for_bus(bus):
        if dev not in used:
            return dev
    raise HTTPException(status_code=409, detail="Brak wolnego targetu dla dodatkowego dysku")

def disk_usage_by_domains(path: Path):
    wanted = str(path.resolve())
    code, output = run_vm_command(["virsh", "list", "--all", "--name"], timeout=10)
    if code != 0:
        return []
    used = []
    for name in [row.strip() for row in output.splitlines() if row.strip()]:
        for row in vm_block_devices(name):
            source = str(row.get("source") or "")
            if source == wanted:
                used.append({"vm_id": name, "device": row.get("device"), "target": row.get("target")})
    return used

def libvirt_vm_names():
    code, output = run_vm_command(["virsh", "list", "--all", "--name"], timeout=12)
    if code != 0:
        return []
    return [row.strip() for row in output.splitlines() if row.strip()]

def attach_vm_disk(vm_id: str, disk: Path, bus: str = "ide", requested_target: str = "", readonly: bool = False, live: bool = True, config: bool = True):
    target = safe_vm_target(vm_id)
    disk = allowed_vm_disk_path(str(disk))
    ensure_libvirt_file_access(disk)
    bus = normalize_vm_disk_bus(bus)
    fmt = vm_disk_format(disk)
    block_devices = vm_block_devices(target)
    disk_resolved = str(disk.resolve())
    for row in block_devices:
        if str(row.get("source") or "") == disk_resolved:
            raise HTTPException(status_code=409, detail=f"Ten plik jest juz podpiety jako {row.get('device')} {row.get('target')}")
    foreign_usage = [row for row in disk_usage_by_domains(disk) if row.get("vm_id") != target]
    if foreign_usage:
        owners = ", ".join(f"{row.get('vm_id')}:{row.get('target')}" for row in foreign_usage[:5])
        raise HTTPException(status_code=409, detail=f"Ten dysk jest juz uzywany przez inna VM ({owners}). Nie podpinam jednego qcow2 do dwoch maszyn.")
    dev = pick_free_disk_target(block_devices, bus, requested_target)
    flags = vm_iso_flags(target, live, config)
    xml_path = Path("/tmp") / f"nexus-disk-{target}-{dev}-{uuid.uuid4().hex[:10]}.xml"
    readonly_xml = "\n    <readonly/>" if readonly else ""
    driver_attrs = " ".join(f"{key}='{html.escape(str(value), quote=True)}'" for key, value in qemu_disk_driver_attrs(fmt, bus, readonly).items())
    xml_path.write_text(f"""<disk type='file' device='disk'>
  <driver {driver_attrs}/>
  <source file='{html.escape(str(disk), quote=True)}'/>
  <target dev='{dev}' bus='{bus}'/>{readonly_xml}
</disk>
""", encoding="utf-8")
    try:
        code, output = run_vm_command(["virsh", "attach-device", target, str(xml_path)] + flags, timeout=30)
    finally:
        try:
            xml_path.unlink()
        except Exception:
            pass
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie podpiac dysku VM")
    return {"mode": "attach-disk", "target": dev, "bus": bus, "disk": str(disk), "format": fmt, "readonly": readonly, "flags": flags, "output": output.strip(), "block_devices": vm_block_devices(target)}

def bad_cdrom_media_rows(vm_id: str):
    target = safe_vm_target(vm_id)
    rows = vm_block_devices(target)
    disk_sources = {str(row.get("source") or "") for row in rows if row.get("device") == "disk" and row.get("source")}
    bad = []
    for row in rows:
        if row.get("device") != "cdrom":
            continue
        source = str(row.get("source") or "")
        suffix = Path(source).suffix.lower()
        if not source:
            continue
        reason = ""
        if source in disk_sources:
            reason = "cdrom-points-to-active-disk"
        elif suffix in VM_DISK_IMAGE_EXT:
            reason = "cdrom-points-to-disk-image"
        if reason:
            bad.append({**row, "reason": reason})
    return bad

def detach_bad_cdrom_media(vm_id: str, live: bool = True, config: bool = True):
    target = safe_vm_target(vm_id)
    flags = vm_iso_flags(target, live, config)
    detached = []
    for row in bad_cdrom_media_rows(target):
        source = str(row.get("source") or "")
        dev = row.get("target") or ""
        if not dev:
            continue
        code, output = run_vm_command(["virsh", "detach-disk", target, dev] + flags, timeout=30)
        detached.append({"target": dev, "source": source, "reason": row.get("reason"), "code": code, "output": output.strip()})
    if detached:
        log_event(f"VM_BAD_CDROM_DETACH vm={target} count={len(detached)}")
    return detached

def attach_or_change_vm_iso(vm_id: str, iso: Path, live=True, config=True):
    return attach_or_change_vm_iso_target(vm_id, iso, live=live, config=config)

def vm_cdrom_media_analysis(vm_id: str):
    target = safe_vm_target(vm_id)
    firmware = vm_firmware_profile(target)
    rows = []
    for row in vm_cdrom_targets(target):
        item = dict(row)
        source = str(item.get("source") or "")
        item["validation"] = None
        item["warnings"] = []
        if source and Path(source).suffix.lower() == ".iso":
            try:
                validation = validate_cdrom_image(Path(source))
                warnings = list(validation.get("warnings") or [])
                boot_profile = validation.get("boot_profile") or {}
                if firmware.get("firmware") == "bios":
                    if boot_profile.get("apple_hint"):
                        warnings.append("VM jest w trybie BIOS/SeaBIOS; macOS wymaga profilu Cupertino/UEFI/OpenCore.")
                    elif boot_profile.get("uefi_boot_hint") and not boot_profile.get("bios_boot_hint"):
                        warnings.append("VM jest w trybie BIOS/SeaBIOS; to ISO wyglada na UEFI-only.")
                item["validation"] = validation
                item["warnings"] = warnings
            except Exception as exc:
                item["warnings"] = [str(exc)]
        rows.append(item)
    return rows

def vm_media_status(vm_id: str):
    target = safe_vm_target(vm_id)
    return {
        "vm_id": target,
        "state": vm_domain_state_label(target),
        "firmware": vm_firmware_profile(target),
        "block_devices": vm_block_devices(target),
        "cdroms": vm_cdrom_targets(target),
        "config_cdroms": vm_cdrom_config_rows(target),
        "cdrom_analysis": vm_cdrom_media_analysis(target),
        "bad_cdroms": bad_cdrom_media_rows(target),
    }

def safe_block_target(value: str):
    target = re.sub(r"[^a-z0-9]+", "", (value or "").lower())
    if target and not re.match(r"^(hd|sd|vd|xvd)[a-z][0-9]*$", target):
        raise HTTPException(status_code=400, detail="Niepoprawny target napedu/dysku")
    return target

def change_vm_cdrom_media(target: str, dev: str, iso: Path, flags, force: bool = True):
    attempts = []
    bus = cdrom_bus_for_target(dev)
    for flagset in virsh_flag_variants(flags):
        xml_path = write_device_xml("update-cdrom", target, cdrom_device_xml(iso, dev, bus))
        try:
            code, output = run_vm_command(["virsh", "update-device", target, str(xml_path)] + flagset, timeout=30)
            attempts.append({"mode": "update-device", "target": dev, "bus": bus, "flags": flagset, "operation": "update", "code": code, "output": output.strip()})
            if code == 0 and flagset == flags:
                return True, attempts
        finally:
            try:
                xml_path.unlink()
            except Exception:
                pass
    if any(row.get("mode") == "update-device" and row.get("code") == 0 for row in attempts):
        return True, attempts
    for operation in ["--update", "--insert"]:
        for flagset in virsh_flag_variants(flags):
            cmd = ["virsh", "change-media", target, dev, str(iso), operation, "--force"] + flagset
            code, output = run_vm_command(cmd, timeout=30)
            attempts.append({"mode": "change-media", "target": dev, "flags": flagset, "operation": operation, "code": code, "output": output.strip()})
            if code == 0 and flagset == flags:
                return True, attempts
        if any(row.get("mode") == "change-media" and row.get("operation") == operation and row.get("code") == 0 for row in attempts):
            return True, attempts
    if force:
        for flagset in virsh_flag_variants(flags):
            code, output = run_vm_command(["virsh", "change-media", target, dev, "--eject", "--force"] + flagset, timeout=30)
            attempts.append({"mode": "change-media", "target": dev, "flags": flagset, "operation": "--eject", "code": code, "output": output.strip()})
            code, output = run_vm_command(["virsh", "change-media", target, dev, str(iso), "--insert", "--force"] + flagset, timeout=30)
            attempts.append({"mode": "change-media", "target": dev, "flags": flagset, "operation": "--insert-after-eject", "code": code, "output": output.strip()})
            if code == 0 and flagset == flags:
                return True, attempts
        if any(row.get("operation") == "--insert-after-eject" and row.get("code") == 0 for row in attempts):
            return True, attempts
    return False, attempts

def attach_cdrom_device(target: str, dev: str, iso: Path, flags):
    bus = cdrom_bus_for_target(dev)
    attempts = []
    for flagset in virsh_flag_variants(flags):
        xml_path = write_device_xml("attach-cdrom", target, cdrom_device_xml(iso, dev, bus))
        try:
            code, output = run_vm_command(["virsh", "attach-device", target, str(xml_path)] + flagset, timeout=30)
            attempts.append({"mode": "attach-device", "target": dev, "bus": bus, "flags": flagset, "code": code, "output": output.strip()})
            if code == 0 and flagset == flags:
                return True, attempts
        finally:
            try:
                xml_path.unlink()
            except Exception:
                pass
    if any(row.get("mode") == "attach-device" and row.get("code") == 0 for row in attempts):
        return True, attempts
    for flagset in virsh_flag_variants(flags):
        cmd = ["virsh", "attach-disk", target, str(iso), dev, "--type", "cdrom", "--mode", "readonly"] + flagset
        code, output = run_vm_command(cmd, timeout=30)
        attempts.append({"mode": "attach-disk", "target": dev, "bus": bus, "flags": flagset, "code": code, "output": output.strip()})
        if code == 0 and flagset == flags:
            return True, attempts
    return any(row.get("mode") == "attach-disk" and row.get("code") == 0 for row in attempts), attempts

def cleanup_stale_installer_cdroms(target: str, keep_dev: str, selected_iso: Path, live: bool = True, config: bool = True, force: bool = True):
    target = safe_vm_target(target)
    keep_dev = safe_block_target(keep_dev)
    selected_iso = Path(selected_iso).resolve()
    flags = vm_iso_flags(target, live, config)
    rows_by_target = {}
    for row in (vm_cdrom_targets(target) + vm_cdrom_config_rows(target)):
        dev = str(row.get("target") or "").lower()
        if dev:
            rows_by_target.setdefault(dev, row)
            if row.get("source"):
                rows_by_target[dev] = row
    attempts = []
    for dev, row in sorted(rows_by_target.items()):
        if dev == keep_dev:
            continue
        source = str(row.get("source") or "")
        if not source or Path(source).suffix.lower() != ".iso":
            continue
        if looks_like_driver_media_path(source):
            continue
        try:
            if Path(source).resolve() == selected_iso:
                reason = "duplicate-selected-installer-iso"
            else:
                reason = "stale-installer-iso"
        except Exception:
            reason = "stale-installer-iso"
        for flagset in virsh_flag_variants(flags):
            cmd = ["virsh", "change-media", target, dev, "--eject"]
            if force:
                cmd.append("--force")
            cmd.extend(flagset)
            code, output = run_vm_command(cmd, timeout=30)
            attempts.append({"mode": "cleanup-stale-iso", "target": dev, "source": source, "reason": reason, "flags": flagset, "code": code, "ok": code == 0, "output": output.strip()})
            if code == 0:
                break
    if attempts:
        log_event(f"VM_ISO_CLEANUP vm={target} keep={keep_dev} count={len(attempts)}")
    return attempts

def ensure_vm_cdrom_boot_order(target: str, boot_dev: str):
    target = safe_vm_target(target)
    boot_dev = safe_block_target(boot_dev)
    if not boot_dev:
        return None
    root, _ = vm_dumpxml_root(target, inactive=True)
    os_node = root.find("os")
    removed_os_boot = []
    if os_node is not None:
        for boot in list(os_node.findall("boot")):
            removed_os_boot.append(dict(boot.attrib))
            os_node.remove(boot)
    devices = xml_devices_node(root)
    boot_disk = None
    primary_disk = None
    for disk in devices.findall("disk"):
        target_node_el = disk.find("target")
        dev = (target_node_el.attrib.get("dev", "") if target_node_el is not None else "").lower()
        device = (disk.attrib.get("device") or "").lower()
        clear_boot_order(disk)
        if device == "cdrom" and dev == boot_dev:
            boot_disk = disk
        elif device == "disk" and primary_disk is None:
            primary_disk = disk
    if boot_disk is None:
        return {"status": "skipped", "reason": f"Nie znaleziono CD-ROM {boot_dev} w XML persistent"}
    set_device_boot_order(boot_disk, 1)
    if primary_disk is not None:
        set_device_boot_order(primary_disk, 2)
    define = define_domain_xml_transaction(target, root, "iso-boot-order")
    return {"status": "updated", "boot_cdrom": boot_dev, "disk_order": bool(primary_disk is not None), "removed_os_boot": removed_os_boot, "define": define}

def installer_iso_candidates(vm_id: str):
    rows = []
    seen = set()
    for source_name, source_rows in (("active", vm_cdrom_targets(vm_id)), ("config", vm_cdrom_config_rows(vm_id))):
        for index, row in enumerate(source_rows or []):
            dev = str(row.get("target") or "").lower()
            source = str(row.get("source") or "")
            if not dev or not source or Path(source).suffix.lower() != ".iso":
                continue
            if looks_like_driver_media_path(source):
                continue
            key = (dev, source)
            if key in seen:
                continue
            seen.add(key)
            boot_order = None
            try:
                root, _ = vm_dumpxml_root(vm_id, inactive=(source_name == "config"))
                for disk in root.findall("./devices/disk"):
                    if (disk.attrib.get("device") or "").lower() != "cdrom":
                        continue
                    target_el = disk.find("target")
                    if target_el is None or (target_el.attrib.get("dev") or "").lower() != dev:
                        continue
                    boot = disk.find("boot")
                    if boot is not None:
                        boot_order = int(boot.attrib.get("order") or 999)
                    break
            except Exception:
                pass
            rows.append({"source_kind": source_name, "index": index, "target": dev, "source": source, "boot_order": boot_order})
    return rows

def normalize_vm_cdrom_policy(vm_id: str, live: bool = True, config: bool = True):
    target = safe_vm_target(vm_id)
    before = vm_media_status(target)
    preferred_bus = vm_cdrom_preferred_bus(target, False)
    bus_policy = normalize_vm_cdrom_bus_policy(target, preferred_bus)
    bad_before = bad_cdrom_media_rows(target)
    detached = detach_bad_cdrom_media(target, live=live, config=config)
    ensured_slot = None
    if not vm_cdrom_targets(target) and not vm_cdrom_config_rows(target):
        ensured_slot = ensure_vm_cdrom_slot(target, live=live, config=config, preferred_bus=preferred_bus)

    candidates = installer_iso_candidates(target)
    selected = None
    if candidates:
        selected = sorted(
            candidates,
            key=lambda row: (
                row.get("boot_order") if row.get("boot_order") is not None else 999,
                0 if row.get("source_kind") == "active" else 1,
                row.get("index", 99),
                row.get("target", ""),
            ),
        )[0]

    attach_result = None
    if selected:
        attach_result = attach_or_change_vm_iso_target(
            target,
            Path(selected["source"]),
            live=live,
            config=config,
            target_dev=selected["target"],
            force=True,
        )

    after = vm_media_status(target)
    result = {
        "status": "normalized",
        "vm_id": target,
        "before": before,
        "bad_before": bad_before,
        "bus_policy": bus_policy,
        "detached_bad": detached,
        "ensured_slot": ensured_slot,
        "selected_installer": selected,
        "attach_result": attach_result,
        "after": after,
    }
    log_event(f"VM_MEDIA_NORMALIZE vm={target} selected={(selected or {}).get('target')} iso={(selected or {}).get('source')} detached={len(detached)}")
    return result

def cdrom_source_matches(source: str, iso: Path):
    if not source:
        return False
    try:
        return Path(source).resolve() == Path(iso).resolve()
    except Exception:
        return str(source) == str(iso)

def verify_vm_iso_media(target: str, iso: Path, target_dev: str = ""):
    target_dev = safe_block_target(target_dev)
    active_cdroms = vm_cdrom_targets(target)
    config_cdroms = vm_cdrom_config_rows(target)
    active_match = [
        row for row in active_cdroms
        if cdrom_source_matches(row.get("source", ""), iso) and (not target_dev or str(row.get("target") or "").lower() == target_dev)
    ]
    config_match = [
        row for row in config_cdroms
        if cdrom_source_matches(row.get("source", ""), iso) and (not target_dev or str(row.get("target") or "").lower() == target_dev)
    ]
    return {
        "active": bool(active_match),
        "config": bool(config_match),
        "active_match": active_match,
        "config_match": config_match,
        "active_cdroms": active_cdroms,
        "config_cdroms": config_cdroms,
    }

def assert_vm_iso_media_result(target: str, iso: Path, target_dev: str, attempts, live: bool, config: bool):
    verify = verify_vm_iso_media(target, iso, target_dev)
    running = vm_is_running_name(target)
    if config and not verify["config"]:
        raise HTTPException(status_code=500, detail={
            "message": "ISO nie zapisalo sie w konfiguracji persistent VM. Nie udaje sukcesu, bo po resecie obraz znowu by zniknal.",
            "attempts": attempts,
            "verify": verify,
        })
    if live and running and not verify["active"]:
        raise HTTPException(status_code=500, detail={
            "message": "ISO zapisano w konfiguracji, ale aktywna VM nie przelaczyla napedu. Jesli VM nie miala hot-plugowalnego CD-ROM, wykonaj restart VM i obraz zostanie zachowany.",
            "attempts": attempts,
            "verify": verify,
        })
    return verify

def vm_media_transaction_begin(target: str, label: str):
    target = safe_vm_target(target)
    return {
        "vm_id": target,
        "label": label,
        "started_at": now_iso(),
        "original_xml": dump_domain_xml(target, inactive=True),
        "original_active_cdroms": vm_cdrom_targets(target),
        "running": vm_is_running_name(target),
    }

def define_domain_xml_raw(target: str, xml_text: str, label: str):
    target = safe_vm_target(target)
    tmp_xml = Path("/tmp") / f"nexus-xml-{label}-{target}-{uuid.uuid4().hex[:10]}.xml"
    try:
        tmp_xml.write_text(xml_text, encoding="utf-8")
        code, output = run_vm_command(["virsh", "define", str(tmp_xml)], timeout=30)
        return {"ok": code == 0, "code": code, "output": output.strip()}
    finally:
        try:
            if tmp_xml.exists():
                tmp_xml.unlink()
        except Exception:
            pass

def restore_cdrom_runtime_state(target: str, active_cdroms):
    target = safe_vm_target(target)
    attempts = []
    if not vm_is_running_name(target):
        return attempts
    for row in active_cdroms or []:
        dev = safe_block_target(row.get("target") or "")
        if not dev:
            continue
        source = str(row.get("source") or "")
        if source:
            command = ["virsh", "change-media", target, dev, source, "--insert", "--force", "--live"]
            operation = "restore-insert"
        else:
            command = ["virsh", "change-media", target, dev, "--eject", "--force", "--live"]
            operation = "restore-eject"
        code, output = run_vm_command(command, timeout=30)
        attempts.append({"operation": operation, "target": dev, "source": source, "code": code, "output": output.strip()})
    return attempts

def vm_media_transaction_rollback(ctx: dict, reason):
    target = safe_vm_target(ctx.get("vm_id") or "")
    rollback = {"vm_id": target, "label": ctx.get("label"), "reason": str(reason)[:500], "persistent": None, "live": []}
    try:
        rollback["persistent"] = define_domain_xml_raw(target, ctx.get("original_xml") or "", f"rollback-{ctx.get('label') or 'media'}")
    except Exception as exc:
        rollback["persistent"] = {"ok": False, "error": str(exc)}
    try:
        rollback["live"] = restore_cdrom_runtime_state(target, ctx.get("original_active_cdroms") or [])
    except Exception as exc:
        rollback["live_error"] = str(exc)
    log_event(f"VM_MEDIA_ROLLBACK vm={target} label={ctx.get('label')} persistent_ok={(rollback.get('persistent') or {}).get('ok')}")
    return rollback

def raise_media_transaction_error(exc, rollback):
    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            payload = dict(detail)
        else:
            payload = {"message": str(detail)}
        payload["rollback"] = rollback
        raise HTTPException(status_code=exc.status_code, detail=payload)
    raise HTTPException(status_code=500, detail={"message": str(exc), "rollback": rollback})

def attach_or_change_vm_iso_target(vm_id: str, iso: Path, live=True, config=True, target_dev: str = "", force: bool = True):
    target = safe_vm_target(vm_id)
    target_dev = safe_block_target(target_dev)
    iso = prepare_libvirt_iso(allowed_iso_path(str(iso)))
    validation = validate_cdrom_image(iso)
    firmware = vm_firmware_profile(target)
    boot_profile = validation.get("boot_profile") or {}
    if firmware.get("firmware") == "bios":
        if boot_profile.get("apple_hint"):
            validation.setdefault("warnings", []).append("Ta VM jest w trybie BIOS/SeaBIOS, a wybrane ISO wyglada na macOS. Samo montowanie zadziala, ale boot wymaga profilu macOS/Cupertino, UEFI i OpenCore.")
        elif boot_profile.get("uefi_boot_hint") and not boot_profile.get("bios_boot_hint"):
            validation.setdefault("warnings", []).append("Ta VM jest w trybie BIOS/SeaBIOS, a ISO wyglada na UEFI-only. Zmien firmware VM na UEFI albo wybierz obraz z bootem BIOS.")
    repaired = detach_bad_cdrom_media(target, live=live, config=config)
    flags = vm_iso_flags(target, live, config)
    block_devices = vm_block_devices(target)
    config_cdroms = vm_cdrom_config_rows(target)
    cdroms = vm_cdrom_targets(target) or config_cdroms
    attempts = []
    ensured_slot = None

    def finalize_iso_result(mode: str, dev: str):
        cleanup = []
        boot_order = None
        if not requested_driver_media:
            cleanup = cleanup_stale_installer_cdroms(target, dev, iso, live=live, config=config, force=force)
            boot_order = ensure_vm_cdrom_boot_order(target, dev) if config else None
        verify = assert_vm_iso_media_result(target, iso, dev, attempts + cleanup, live, config)
        return {
            "mode": mode,
            "target": dev,
            "iso": str(iso),
            "validation": validation,
            "firmware": vm_firmware_profile(target),
            "attempts": attempts,
            "cleanup": cleanup,
            "boot_order": boot_order,
            "repaired_bad_cdroms": repaired,
            "ensured_slot": ensured_slot,
            "bus_policy": bus_policy,
            "verify": verify,
            "verify_cdroms": verify["active_cdroms"],
        }

    requested_driver_media = looks_like_driver_media_path(str(iso))
    preferred_bus = vm_cdrom_preferred_bus(target, requested_driver_media)
    if target_dev and preferred_bus == "sata" and target_dev.startswith("hd"):
        attempts.append({"mode": "target-normalize", "from": target_dev, "to": "", "reason": "UEFI/q35 prefers SATA CD-ROM targets"})
        target_dev = ""
    bus_policy = normalize_vm_cdrom_bus_policy(target, preferred_bus)

    if not cdroms or (target_dev and not any(str(row.get("target") or "").lower() == target_dev for row in cdroms)):
        ensured_slot = ensure_vm_cdrom_slot(target, target_dev=target_dev, live=live, config=config, preferred_bus=preferred_bus)
        cdroms = vm_cdrom_targets(target) or vm_cdrom_config_rows(target)
        block_devices = vm_block_devices(target)
        attempts.append({"mode": "ensure-cdrom-slot", **ensured_slot})
    if bus_policy.get("changed"):
        cdroms = vm_cdrom_targets(target) or vm_cdrom_config_rows(target)
        block_devices = vm_block_devices(target)
        attempts.append({"mode": "cdrom-bus-policy", **bus_policy})

    active_cdrom_order = {
        str(row.get("target") or "").lower(): index
        for index, row in enumerate(vm_cdrom_targets(target) or cdroms)
        if row.get("target")
    }

    def cdrom_priority(cdrom):
        dev = (cdrom.get("target") or "").lower()
        source = (cdrom.get("source") or "").lower()
        source_is_driver = looks_like_driver_media_path(source)
        empty_score = 0 if not source else 1
        if requested_driver_media:
            role_score = 0 if source_is_driver else (1 if not source else 2)
            preferred = 0 if dev in {"hdc", "sdb", "sdc"} else 1
            return (role_score, empty_score, preferred, active_cdrom_order.get(dev, 99), dev)
        else:
            role_score = 3 if source_is_driver else 0
            return (role_score, active_cdrom_order.get(dev, 99), empty_score, dev)

    if target_dev:
        cdrom = next((row for row in cdroms if str(row.get("target") or "").lower() == target_dev), None)
        if cdrom:
            ok, media_attempts = change_vm_cdrom_media(target, target_dev, iso, flags, force=force)
            attempts.extend(media_attempts)
            if ok:
                return finalize_iso_result("change-media", target_dev)
        elif any(str(row.get("target") or "").lower() == target_dev for row in block_devices):
            raise HTTPException(status_code=409, detail=f"Target {target_dev} jest juz zajety przez inne urzadzenie")
        else:
            ok, attach_attempts = attach_cdrom_device(target, target_dev, iso, flags)
            attempts.extend(attach_attempts)
            if ok:
                return finalize_iso_result("attach-device", target_dev)

    for cdrom in sorted(cdroms, key=cdrom_priority):
        dev = cdrom.get("target") or ""
        if not dev:
            continue
        source = cdrom.get("source") or ""
        ok, media_attempts = change_vm_cdrom_media(target, dev, iso, flags, force=force)
        for row in media_attempts:
            row["previous"] = source
        attempts.extend(media_attempts)
        if ok:
            return finalize_iso_result("change-media", dev)

    used_targets = {str(row.get("target") or "").lower() for row in block_devices}
    fallback_targets = ["sdb", "sdc", "sdd", "hdb", "hdc"] if preferred_bus == "sata" else ["hda", "hdb", "hdc", "sdb", "sdc", "sdd"]
    for dev in fallback_targets:
        if dev in used_targets:
            attempts.append({"mode": "attach-disk", "target": dev, "code": 409, "output": "target already in use"})
            continue
        ok, attach_attempts = attach_cdrom_device(target, dev, iso, flags)
        attempts.extend(attach_attempts)
        if ok:
            return finalize_iso_result("attach-device", dev)
    raise HTTPException(status_code=500, detail={"message": "Nie udalo sie podmienic ani podpiac ISO do VM", "attempts": attempts})

def eject_vm_iso_target(vm_id: str, target_dev: str = "", live: bool = True, config: bool = True, force: bool = True):
    target = safe_vm_target(vm_id)
    target_dev = safe_block_target(target_dev)
    flags = vm_iso_flags(target, live, config)
    cdroms = vm_cdrom_targets(target)
    wanted = [target_dev] if target_dev else [row.get("target") for row in cdroms if row.get("source")]
    wanted = [dev for dev in wanted if dev]
    attempts = []
    if target_dev and not any(str(row.get("target") or "").lower() == target_dev for row in cdroms):
        raise HTTPException(status_code=404, detail=f"Nie znaleziono CD-ROM target {target_dev}")
    if not wanted:
        return {"mode": "eject", "ejected": [], "attempts": [], "verify_cdroms": vm_cdrom_targets(target), "verify_config_cdroms": vm_cdrom_config_rows(target)}
    for dev in wanted:
        for flagset in virsh_flag_variants(flags):
            cmd = ["virsh", "change-media", target, dev, "--eject"]
            if force:
                cmd.append("--force")
            cmd.extend(flagset)
            code, output = run_vm_command(cmd, timeout=30)
            attempts.append({"mode": "change-media", "target": dev, "flags": flagset, "operation": "eject", "code": code, "output": output.strip()})
            if code != 0 and target_dev:
                detach_code, detach_output = run_vm_command(["virsh", "detach-disk", target, dev] + flagset, timeout=30)
                attempts.append({"mode": "detach-disk", "target": dev, "flags": flagset, "operation": "fallback-detach", "code": detach_code, "output": detach_output.strip()})
    ejected = [row for row in attempts if row.get("code") == 0]
    if target_dev and not ejected:
        raise HTTPException(status_code=500, detail={"message": "Nie udalo sie wysunac ISO", "attempts": attempts})
    return {"mode": "eject", "ejected": ejected, "attempts": attempts, "verify_cdroms": vm_cdrom_targets(target), "verify_config_cdroms": vm_cdrom_config_rows(target)}

def vm_network_flags(vm_id: str, live=True, config=True):
    return vm_iso_flags(vm_id, live, config)

def set_vm_network(vm_id: str, enabled=True, network="default", model="virtio", live=True, config=True):
    target = safe_vm_target(vm_id)
    flags = vm_network_flags(target, live, config)
    attempts = []
    if enabled:
        net = re.sub(r"[^A-Za-z0-9_.-]+", "", network or "default") or "default"
        mdl = re.sub(r"[^A-Za-z0-9_.-]+", "", model or "virtio") or "virtio"
        cmd = ["virsh", "attach-interface", target, "--type", "network", "--source", net, "--model", mdl] + flags
        code, output = run_vm_command(cmd, timeout=30)
        attempts.append({"mode": "attach-interface", "code": code, "output": output.strip()})
        if code == 0 or "already exists" in output.lower():
            return {"enabled": True, "network": net, "model": mdl, "attempts": attempts, "interfaces": vm_interface_rows(target)}
        raise HTTPException(status_code=500, detail={"message": "Nie udalo sie wlaczyc internetu VM", "attempts": attempts})
    interfaces = vm_interface_rows(target)
    if not interfaces:
        return {"enabled": False, "attempts": [{"mode": "detach-interface", "code": 0, "output": "Brak interfejsow"}], "interfaces": []}
    for iface in interfaces:
        mac = iface.get("mac")
        if not mac:
            continue
        cmd = ["virsh", "detach-interface", target, "--type", "network", "--mac", mac] + flags
        code, output = run_vm_command(cmd, timeout=30)
        attempts.append({"mode": "detach-interface", "mac": mac, "code": code, "output": output.strip()})
        if code == 0:
            return {"enabled": False, "attempts": attempts, "interfaces": vm_interface_rows(target)}
    raise HTTPException(status_code=500, detail={"message": "Nie udalo sie odpiac internetu VM", "attempts": attempts})

def cleanup_failed_vm(name: str, disk: Path):
    try:
        run_vm_command(["virsh", "destroy", name], timeout=10)
    except Exception:
        pass
    try:
        run_vm_command(["virsh", "undefine", name, "--nvram"], timeout=20)
    except Exception:
        pass
    try:
        if disk.exists():
            disk.unlink()
    except Exception:
        pass
    try:
        overlay = opencore_overlay_path(name)
        if overlay.exists():
            overlay.unlink()
    except Exception:
        pass
    try:
        for overlay in CUPERTINO_MEDIA_OVERLAY_DIR.glob(f"{safe_vm_target(name)}-*-media.qcow2"):
            try:
                overlay.unlink()
            except Exception:
                pass
    except Exception:
        pass

def os_preset(os_id: str):
    for item in OS_CATALOG:
        if item["id"] == os_id:
            return item
    raise HTTPException(status_code=400, detail="Nieznany preset systemu")

def safe_domain_name(name: str):
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", (name or "").strip()).strip(".-")
    if not cleaned or len(cleaned) < 3:
        raise HTTPException(status_code=400, detail="Nazwa VM jest za krotka")
    if cleaned.startswith("-"):
        raise HTTPException(status_code=400, detail="Nazwa VM nie moze zaczynac sie od '-'")
    return cleaned[:64]

def is_windows_preset(preset):
    return "windows" in preset.get("family", "").lower() or preset.get("id", "").startswith("win")

def is_macos_preset(preset):
    value = f"{preset.get('id', '')} {preset.get('family', '')} {preset.get('name', '')}".lower()
    return "macos" in value or "apple" in value

def is_legacy_windows_preset(preset):
    return preset.get("id", "").lower() in {"win95", "win98", "winxp"}

def is_win9x_preset(preset):
    return preset.get("id", "").lower() in {"win95", "win98"}

def is_compat_windows_preset(preset):
    return preset.get("id", "").lower() in {"win95", "win98", "winxp", "win7", "win7pe-dreamos", "win10pe-project2015"}

def find_virtio_win_iso():
    names = ["virtio-win.iso", "virtio-win-latest.iso"]
    for root in iso_roots():
        for name in names:
            path = root / name
            if path.exists():
                return path.resolve()
        try:
            matches = sorted(root.glob("virtio-win*.iso"))
            if matches:
                return matches[0].resolve()
        except Exception:
            pass
    return None

def libvirt_network_arg(network: str, model: str):
    network = (network or "default").strip()
    if network.lower() in {"none", "off", "disabled"}:
        return "none"
    code, output = run_vm_command(["virsh", "net-info", network], timeout=8)
    if code == 0:
        if "Active: no" in output:
            run_vm_command(["virsh", "net-start", network], timeout=15)
        return f"network={network},model={model}"
    return f"user,model={model}"

def virt_install_command(data: VMCreateRequest, preset, iso: Path, disk: Path, driver_media: Path = None, effective=None):
    windows = is_windows_preset(preset)
    macos = is_macos_preset(preset)
    legacy_windows = is_legacy_windows_preset(preset)
    win9x = is_win9x_preset(preset)
    compat_windows = is_compat_windows_preset(preset)
    effective = effective or {}
    target_memory_mb = int(effective.get("target_memory_mb") or effective.get("memory_mb") or data.memory_mb)
    startup_memory_mb = int(effective.get("startup_memory_mb") or target_memory_mb)
    startup_memory_mb = max(128, min(startup_memory_mb, target_memory_mb))
    memory_arg = str(startup_memory_mb)
    if target_memory_mb > startup_memory_mb:
        memory_arg = f"{startup_memory_mb},maxmemory={target_memory_mb}"
    vcpus = int(effective.get("vcpus") or data.vcpus)
    requested_network = effective.get("network", data.network)
    requested_cpu = effective.get("cpu") or ""
    disk_bus = "sata" if macos else ("ide" if legacy_windows else ("sata" if windows else "virtio"))
    nic_model = "e1000e" if macos else ("pcnet" if win9x else ("e1000" if preset.get("id", "").lower() in {"winxp", "win7", "win7pe-dreamos"} else ("e1000e" if windows else "virtio")))
    video_model = "virtio" if macos else ("vga" if compat_windows else "virtio")
    input_model = "mouse,bus=ps2" if legacy_windows else "tablet,bus=usb"
    network_name = "none" if win9x else requested_network
    cpu_model = requested_cpu or ("qemu32" if win9x else "host-passthrough")
    boot_args = "uefi" if macos else "cdrom,hd"
    command = [
        "virt-install",
        "--name", safe_domain_name(data.name),
        "--memory", memory_arg,
        "--vcpus", str(vcpus),
        "--cpu", cpu_model,
        "--disk", qemu_disk_arg(disk, "qcow2", disk_bus, readonly=False),
        "--cdrom", str(iso),
        "--os-variant", preset.get("variant") or "generic",
        "--network", libvirt_network_arg(network_name, nic_model),
        "--graphics", "vnc,listen=127.0.0.1,port=-1",
        "--video", video_model,
        "--input", input_model,
        "--boot", boot_args,
        "--noautoconsole",
        "--wait", "0",
        "--check", "all=off",
    ]
    if driver_media:
        driver_cdrom_bus = "ide" if legacy_windows else "sata"
        command.extend(["--disk", qemu_disk_arg(driver_media, "raw", driver_cdrom_bus, readonly=True, device="cdrom")])
    return command

def safe_vm_target(target: str):
    target = (target or "").strip()
    if not target or target.startswith("-") or len(target) > 80:
        raise HTTPException(status_code=400, detail="Niepoprawny identyfikator VM")
    return target

def parse_vnc_endpoint(value: str):
    raw = (value or "").strip()
    if not raw or raw in {"-", "none"}:
        return None
    if raw.startswith("vnc://"):
        parsed = urllib.parse.urlparse(raw)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port
        if port is None:
            display = (parsed.path or "").strip("/")
            port = 5900 + int(display or "0")
        elif port < 100:
            port = 5900 + port
        return host, port
    if raw.startswith(":"):
        display = raw[1:].split(",", 1)[0]
        return "127.0.0.1", 5900 + int(display or "0")
    match = re.match(r"^([^,\s:]+):(\d+)", raw)
    if match:
        host, value_port = match.group(1), int(match.group(2))
        return host, 5900 + value_port if value_port < 100 else value_port
    return None

def is_local_vnc_host(host: str):
    host = (host or "").strip().lower()
    if host in {"", "localhost", "::1"} or host.startswith("127."):
        return True
    try:
        resolved = socket.gethostbyname(host)
        return resolved.startswith("127.")
    except Exception:
        return False

def ensure_libvirt_vnc_graphics(target: str):
    target = safe_vm_target(target)
    xml_path = Path("/tmp") / f"nexus-vnc-graphics-{uuid.uuid4().hex[:10]}.xml"
    xml_path.write_text(
        "<graphics type='vnc' autoport='yes' listen='127.0.0.1'>\n"
        "  <listen type='address' address='127.0.0.1'/>\n"
        "</graphics>\n",
        encoding="utf-8",
    )
    try:
        code, output = run_vm_command(["virsh", "update-device", target, str(xml_path), "--live", "--config"], timeout=15)
        if code != 0:
            code_cfg, output_cfg = run_vm_command(["virsh", "update-device", target, str(xml_path), "--config"], timeout=15)
            output = f"{output}\n{output_cfg}"
            code = code_cfg
        if code == 0:
            log_event(f"VM_VNC_AUTO_REPAIR ok vm={target}")
            return True, output
        log_event(f"VM_VNC_AUTO_REPAIR failed vm={target}: {output.strip()[:240]}")
        return False, output
    finally:
        try:
            xml_path.unlink()
        except Exception:
            pass

def libvirt_input_set(target: str, inactive: bool = False):
    command = ["virsh", "dumpxml", target]
    if inactive:
        command.append("--inactive")
    code, output = run_vm_command(command, timeout=15)
    if code != 0 and inactive:
        code, output = run_vm_command(["virsh", "dumpxml", target], timeout=15)
    if code != 0:
        if "failed to get domain" in output.lower() or "domain not found" in output.lower() or "nie znaleziono" in output.lower():
            raise HTTPException(status_code=404, detail=f"Nie znaleziono VM: {target}. Odswiez liste maszyn.")
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie odczytac XML VM")
    try:
        root = ET.fromstring(output)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Nie udalo sie parsowac XML VM: {exc}")
    devices = set()
    for node in root.findall(".//devices/input"):
        devices.add(((node.attrib.get("type") or "").lower(), (node.attrib.get("bus") or "").lower()))
    return devices

def attach_libvirt_input_device(target: str, dev_type: str, bus: str, flag: str):
    xml_path = Path("/tmp") / f"nexus-input-{dev_type}-{bus}-{uuid.uuid4().hex[:10]}.xml"
    xml_path.write_text(f"<input type='{dev_type}' bus='{bus}'/>\n", encoding="utf-8")
    try:
        code, output = run_vm_command(["virsh", "attach-device", target, str(xml_path), flag], timeout=20)
        return code, output
    finally:
        try:
            xml_path.unlink()
        except Exception:
            pass

def ensure_libvirt_input_devices(target: str, live: bool = True, config: bool = True):
    target = safe_vm_target(target)
    state_code, state_output = run_vm_command(["virsh", "domstate", target], timeout=8)
    running = state_code == 0 and "running" in state_output.lower()
    legacy_profile = ""
    try:
        legacy_profile = detect_vm_compat_profile(target)
    except Exception:
        legacy_profile = ""
    prefer_ps2_only = legacy_profile in {"win95", "win98", "freedos"}
    desired = []
    if not prefer_ps2_only:
        desired.append(("tablet", "usb", "USB tablet / dokladny kursor noVNC"))
    desired.extend([
        ("mouse", "ps2", "PS/2 mouse / fallback dla legacy Windows"),
        ("keyboard", "ps2", "PS/2 keyboard / stabilny focus konsoli"),
    ])
    persistent_inputs = libvirt_input_set(target, inactive=True) if config else set()
    live_inputs = libvirt_input_set(target, inactive=False) if live and running else set()
    added = []
    skipped = []
    warnings = []

    for dev_type, bus, label in desired:
        key = (dev_type, bus)
        changed = False
        if config and key not in persistent_inputs:
            code, output = attach_libvirt_input_device(target, dev_type, bus, "--config")
            if code == 0:
                added.append({"device": f"{dev_type}/{bus}", "scope": "config", "label": label})
                changed = True
            else:
                warnings.append(f"{dev_type}/{bus} config: {output.strip() or 'attach failed'}")
        if live and running and key not in live_inputs:
            code, output = attach_libvirt_input_device(target, dev_type, bus, "--live")
            if code == 0:
                added.append({"device": f"{dev_type}/{bus}", "scope": "live", "label": label})
                changed = True
            else:
                warnings.append(f"{dev_type}/{bus} live: {output.strip() or 'attach failed'}")
        if not changed:
            skipped.append({"device": f"{dev_type}/{bus}", "label": label})

    log_event(f"VM_INPUT_REPAIR vm={target} added={len(added)} skipped={len(skipped)} warnings={len(warnings)}")
    return {
        "status": "checked",
        "vm_id": target,
        "running": running,
        "compat_profile": legacy_profile,
        "ps2_only": prefer_ps2_only,
        "added": len(added),
        "skipped": len(skipped),
        "devices_added": added,
        "devices_present": skipped,
        "warnings": warnings[:8],
    }

VM_COMPAT_PROFILES = {
    "win95": {
        "label": "Windows 95 / OSR2 safe install",
        "memory_mb": 128,
        "vcpus": 1,
        "cpu": "qemu32",
        "acceptable_cpus": ["qemu32", "pentium3", "core2duo"],
        "disk_bus": "ide",
        "video": "vga",
        "network_model": "pcnet",
        "network_default": "off",
        "drop_virtio_media": True,
        "drop_usb_tablet": True,
        "drop_usb_controller": True,
        "drop_memballoon": True,
        "drop_acpi": True,
        "note": "Naprawia bledy NDIS/Windows Protection Error: siec OFF na czas instalacji, qemu32, IDE, VGA, PS/2.",
    },
    "win98": {
        "label": "Windows 98 / 98 SE safe install",
        "memory_mb": 256,
        "vcpus": 1,
        "cpu": "qemu32",
        "acceptable_cpus": ["qemu32", "pentium3", "core2duo"],
        "disk_bus": "ide",
        "video": "vga",
        "network_model": "pcnet",
        "network_default": "off",
        "drop_virtio_media": True,
        "drop_usb_tablet": True,
        "drop_usb_controller": True,
        "drop_memballoon": True,
        "drop_acpi": True,
        "note": "Stabilny profil instalacji Win98: najpierw bez sieci, potem wlacz pcnet/rtl8139 po sterownikach.",
    },
    "winxp": {
        "label": "Windows XP legacy IDE/e1000",
        "memory_mb": 1024,
        "vcpus": 1,
        "cpu": "qemu32",
        "disk_bus": "ide",
        "video": "vga",
        "network_model": "e1000",
        "network_default": "on",
        "drop_virtio_media": False,
        "drop_usb_tablet": False,
        "drop_usb_controller": False,
        "drop_memballoon": False,
        "drop_acpi": False,
        "note": "Profil XP bez VirtIO na dysku: IDE + e1000 + VGA, dobry do instalatorow bez F6.",
    },
    "win7": {
        "label": "Windows 7 safe SATA/e1000",
        "memory_mb": 1536,
        "vcpus": 1,
        "cpu": "host-passthrough",
        "disk_bus": "sata",
        "video": "vga",
        "network_model": "e1000",
        "network_default": "on",
        "drop_virtio_media": False,
        "drop_usb_tablet": False,
        "drop_usb_controller": False,
        "drop_memballoon": False,
        "drop_acpi": False,
        "note": "Profil zgodnosci Win7: SATA/e1000/VGA, VirtIO opcjonalnie jako osobne ISO.",
    },
    "freedos": {
        "label": "FreeDOS / DOS safe",
        "memory_mb": 64,
        "vcpus": 1,
        "cpu": "qemu32",
        "disk_bus": "ide",
        "video": "vga",
        "network_model": "pcnet",
        "network_default": "off",
        "drop_virtio_media": True,
        "drop_usb_tablet": True,
        "drop_usb_controller": True,
        "drop_memballoon": True,
        "drop_acpi": True,
        "note": "Minimalny DOS: IDE, VGA, PS/2, bez sieci.",
    },
    "reactos": {
        "label": "ReactOS experimental",
        "memory_mb": 512,
        "vcpus": 1,
        "cpu": "qemu32",
        "disk_bus": "ide",
        "video": "vga",
        "network_model": "rtl8139",
        "network_default": "on",
        "drop_virtio_media": True,
        "drop_usb_tablet": False,
        "drop_usb_controller": False,
        "drop_memballoon": True,
        "drop_acpi": False,
        "note": "ReactOS lubi prosty sprzet: qemu32, IDE, VGA i rtl8139.",
    },
}

def compat_profile(profile: str):
    key = re.sub(r"[^a-z0-9_-]+", "", (profile or "win95").lower()) or "win95"
    if key not in VM_COMPAT_PROFILES:
        raise HTTPException(status_code=400, detail="Nieznany profil kompatybilnosci")
    return key, VM_COMPAT_PROFILES[key]

def xml_find_child_index(root, tag: str):
    for idx, child in enumerate(list(root)):
        if child.tag == tag:
            return idx
    return None

def xml_indent(root):
    try:
        ET.indent(root, space="  ")
    except Exception:
        pass

def set_text_node(root, tag: str, text: str, unit: str = None):
    node = root.find(tag)
    if node is None:
        node = ET.Element(tag)
        insert_at = xml_find_child_index(root, "os")
        root.insert(insert_at if insert_at is not None else 0, node)
    node.text = str(text)
    if unit:
        node.attrib["unit"] = unit
    return node

def set_compat_cpu(root, model: str):
    for node in list(root.findall("cpu")):
        root.remove(node)
    if not model:
        return
    if model == "host-passthrough":
        cpu = ET.Element("cpu", {"mode": "host-passthrough", "check": "none"})
    else:
        cpu = ET.Element("cpu", {"mode": "custom", "match": "exact", "check": "none"})
        ET.SubElement(cpu, "model", {"fallback": "allow"}).text = model
    features_idx = xml_find_child_index(root, "features")
    clock_idx = xml_find_child_index(root, "clock")
    if features_idx is not None:
        root.insert(features_idx + 1, cpu)
    elif clock_idx is not None:
        root.insert(clock_idx, cpu)
    else:
        root.append(cpu)

def set_custom_cpu(root, model: str, fallback: str = "allow", hidden_kvm: bool = False):
    for node in list(root.findall("cpu")):
        root.remove(node)
    cpu = ET.Element("cpu", {"mode": "custom", "match": "exact", "check": "none"})
    ET.SubElement(cpu, "model", {"fallback": fallback}).text = model
    features_idx = xml_find_child_index(root, "features")
    clock_idx = xml_find_child_index(root, "clock")
    if features_idx is not None:
        root.insert(features_idx + 1, cpu)
    elif clock_idx is not None:
        root.insert(clock_idx, cpu)
    else:
        root.append(cpu)
    if hidden_kvm:
        features = root.find("features")
        if features is None:
            features = ET.Element("features")
            cpu_idx = xml_find_child_index(root, "cpu")
            root.insert(cpu_idx if cpu_idx is not None else 0, features)
        kvm = features.find("kvm")
        if kvm is None:
            kvm = ET.SubElement(features, "kvm")
        hidden = kvm.find("hidden")
        if hidden is None:
            hidden = ET.SubElement(kvm, "hidden")
        hidden.attrib["state"] = "on"

def domain_xml_text(root):
    xml_indent(root)
    text = ET.tostring(root, encoding="unicode")
    lowered = text.lower()
    if "isa-applesmc" in lowered or "osk=" in lowered:
        raise HTTPException(status_code=400, detail="Legal Shield: XML zawiera niedozwolona probe wstrzykniecia Apple SMC/OSK")
    return text

def dump_domain_xml(target: str, inactive: bool = True):
    command = ["virsh", "dumpxml", safe_vm_target(target)]
    if inactive:
        command.append("--inactive")
    code, output = run_vm_command(command, timeout=15)
    if code != 0 and inactive:
        code, output = run_vm_command(["virsh", "dumpxml", safe_vm_target(target)], timeout=15)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie odczytac XML VM")
    return output

def define_domain_xml_transaction(target: str, root, label: str):
    target = safe_vm_target(target)
    original_xml = dump_domain_xml(target, inactive=True)
    new_xml = domain_xml_text(root)
    tmp_xml = Path("/tmp") / f"nexus-xml-{label}-{target}-{uuid.uuid4().hex[:10]}.xml"
    rollback_xml = Path("/tmp") / f"nexus-xml-rollback-{target}-{uuid.uuid4().hex[:10]}.xml"
    try:
        tmp_xml.write_text(new_xml, encoding="utf-8")
        code, output = run_vm_command(["virsh", "define", str(tmp_xml)], timeout=30)
        if code != 0:
            raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie zapisac XML VM")
        verify_code, verify_output = run_vm_command(["virsh", "dumpxml", target, "--inactive"], timeout=15)
        if verify_code != 0:
            rollback_xml.write_text(original_xml, encoding="utf-8")
            run_vm_command(["virsh", "define", str(rollback_xml)], timeout=30)
            raise HTTPException(status_code=500, detail=verify_output.strip() or "XML zapisany, ale weryfikacja libvirt nie przeszla; wykonano rollback")
        log_event(f"VM_XML_TRANSACTION ok vm={target} label={label}")
        return {"define_output": output.strip(), "verify_output": verify_output[:1200], "rollback_ready": True}
    except HTTPException:
        raise
    except Exception as exc:
        try:
            rollback_xml.write_text(original_xml, encoding="utf-8")
            run_vm_command(["virsh", "define", str(rollback_xml)], timeout=30)
        except Exception as rollback_exc:
            log_event(f"VM_XML_TRANSACTION rollback failed vm={target}: {rollback_exc}")
        raise HTTPException(status_code=500, detail=f"Blad transakcji XML: {exc}")
    finally:
        for path in (tmp_xml, rollback_xml):
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass

def disk_source_text(disk):
    source = disk.find("source")
    if source is None:
        return ""
    return source.attrib.get("file") or source.attrib.get("dev") or source.attrib.get("name") or ""

def target_node(disk, fallback_dev: str, bus: str):
    target = disk.find("target")
    if target is None:
        target = ET.SubElement(disk, "target")
    target.attrib["dev"] = target.attrib.get("dev") or fallback_dev
    target.attrib["bus"] = bus
    return target

def normalize_legacy_disks(devices, bus: str, drop_virtio_media: bool):
    removed = []
    cdrom_index = 0
    disk_index = 0
    for disk in list(devices.findall("disk")):
        device = (disk.attrib.get("device") or "").lower()
        source = disk_source_text(disk).lower()
        if device == "cdrom":
            if drop_virtio_media and ("virtio" in source or "selected-drivers" in source):
                devices.remove(disk)
                removed.append(source or "driver-cdrom")
                continue
            dev = "hd" + chr(ord("b") + cdrom_index) if bus == "ide" else f"sd{chr(ord('b') + cdrom_index)}"
            target_node(disk, dev, bus)
            cdrom_index += 1
        elif device == "disk":
            dev = "hd" + chr(ord("a") + disk_index) if bus == "ide" else f"sd{chr(ord('a') + disk_index)}"
            target_node(disk, dev, bus)
            disk_index += 1
    return removed

def normalize_legacy_inputs(devices, drop_usb_tablet: bool):
    present = {(node.attrib.get("type"), node.attrib.get("bus")) for node in devices.findall("input")}
    if drop_usb_tablet:
        for node in list(devices.findall("input")):
            if (node.attrib.get("type") == "tablet" and node.attrib.get("bus") == "usb"):
                devices.remove(node)
    for dev_type, bus in (("mouse", "ps2"), ("keyboard", "ps2")):
        if (dev_type, bus) not in present:
            ET.SubElement(devices, "input", {"type": dev_type, "bus": bus})

def normalize_legacy_lowlevel(root, devices, profile: dict):
    removed = []
    if profile.get("drop_usb_controller"):
        for node in list(devices.findall("controller")):
            if (node.attrib.get("type") or "").lower() == "usb":
                devices.remove(node)
                removed.append("usb-controller")
        ET.SubElement(devices, "controller", {"type": "usb", "model": "none"})
        removed.append("usb-controller-disabled")
    if profile.get("drop_memballoon"):
        for node in list(devices.findall("memballoon")):
            devices.remove(node)
            removed.append("memballoon")
        ET.SubElement(devices, "memballoon", {"model": "none"})
        removed.append("memballoon-disabled")
    if profile.get("drop_acpi"):
        features = root.find("features")
        if features is not None:
            for tag in ("acpi", "apic"):
                node = features.find(tag)
                if node is not None:
                    features.remove(node)
                    removed.append(tag)
    return removed

def normalize_legacy_video(devices, model: str):
    video = devices.find("video")
    if video is None:
        video = ET.SubElement(devices, "video")
    model_node = video.find("model")
    if model_node is None:
        model_node = ET.SubElement(video, "model")
    model_node.attrib["type"] = model or "vga"
    model_node.attrib.setdefault("vram", "16384")
    model_node.attrib.setdefault("heads", "1")
    model_node.attrib.setdefault("primary", "yes")

def normalize_legacy_network(devices, profile: dict, network_mode: str):
    mode = (network_mode or "safe").lower()
    if mode == "safe":
        mode = profile.get("network_default", "off")
    removed = 0
    for node in list(devices.findall("interface")):
        devices.remove(node)
        removed += 1
    added = None
    if mode in {"on", "default", "pcnet", "rtl8139", "e1000"}:
        model = profile.get("network_model", "pcnet")
        if mode in {"pcnet", "rtl8139", "e1000"}:
            model = mode
        iface = ET.SubElement(devices, "interface", {"type": "network"})
        ET.SubElement(iface, "source", {"network": "default"})
        ET.SubElement(iface, "model", {"type": model})
        added = model
    return {"removed": removed, "added": added, "mode": mode}

def apply_vm_compat_profile(vm_id: str, profile_name: str = "win95", restart: bool = True, network: str = "safe"):
    target = safe_vm_target(vm_id)
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Latki kompatybilnosci sa wspierane dla libvirt/KVM")
    key, profile = compat_profile(profile_name)
    state_code, state_output = run_vm_command(["virsh", "domstate", target], timeout=8)
    was_running = state_code == 0 and "running" in state_output.lower()
    if was_running and restart:
        run_vm_command(["virsh", "destroy", target], timeout=20)

    code, output = run_vm_command(["virsh", "dumpxml", target, "--inactive"], timeout=15)
    if code != 0:
        code, output = run_vm_command(["virsh", "dumpxml", target], timeout=15)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie odczytac XML VM")
    try:
        root = ET.fromstring(output)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Nie udalo sie parsowac XML VM: {exc}")

    memory_mb = int(profile.get("memory_mb") or 256)
    set_text_node(root, "memory", str(memory_mb * 1024), "KiB")
    set_text_node(root, "currentMemory", str(memory_mb * 1024), "KiB")
    vcpu = set_text_node(root, "vcpu", str(int(profile.get("vcpus") or 1)))
    vcpu.attrib.setdefault("placement", "static")
    set_compat_cpu(root, profile.get("cpu") or "qemu32")

    devices = root.find("devices")
    if devices is None:
        devices = ET.SubElement(root, "devices")
    removed_media = normalize_legacy_disks(devices, profile.get("disk_bus", "ide"), bool(profile.get("drop_virtio_media")))
    normalize_legacy_inputs(devices, bool(profile.get("drop_usb_tablet")))
    removed_lowlevel = normalize_legacy_lowlevel(root, devices, profile)
    normalize_legacy_video(devices, profile.get("video", "vga"))
    network_result = normalize_legacy_network(devices, profile, network)

    define_result = define_domain_xml_transaction(target, root, f"compat-{key}")
    define_output = define_result.get("define_output", "")

    start_output = ""
    if was_running and restart:
        start_code, start_output = run_vm_command(["virsh", "start", target], timeout=30)
        if start_code != 0:
            raise HTTPException(status_code=500, detail=f"Latka zapisana, ale VM nie wystartowala: {start_output.strip()}")

    verify_code, verify_xml = run_vm_command(["virsh", "dumpxml", target, "--inactive"], timeout=15)
    log_event(f"VM_COMPAT_PROFILE vm={target} profile={key} restart={restart} network={network_result.get('mode')} removed_media={len(removed_media)}")
    return {
        "status": "patched",
        "vm_id": target,
        "profile": key,
        "label": profile.get("label"),
        "note": profile.get("note"),
        "was_running": was_running,
        "restarted": bool(was_running and restart),
        "memory_mb": memory_mb,
        "vcpus": int(profile.get("vcpus") or 1),
        "cpu": profile.get("cpu"),
        "disk_bus": profile.get("disk_bus"),
        "video": profile.get("video"),
        "network": network_result,
        "removed_media": removed_media,
        "removed_lowlevel": removed_lowlevel,
        "define_output": define_output.strip(),
        "start_output": start_output.strip(),
        "verify": {
            "ok": verify_code == 0,
            "has_qemu32": "qemu32" in verify_xml,
            "interfaces": vm_interface_rows(target),
            "cdroms": vm_cdrom_targets(target),
        },
    }

def vm_dumpxml_root(vm_id: str, inactive: bool = True):
    target = safe_vm_target(vm_id)
    command = ["virsh", "dumpxml", target]
    if inactive:
        command.append("--inactive")
    code, output = run_vm_command(command, timeout=15)
    if code != 0 and inactive:
        code, output = run_vm_command(["virsh", "dumpxml", target], timeout=15)
    if code != 0:
        if "failed to get domain" in output.lower() or "domain not found" in output.lower() or "nie znaleziono" in output.lower():
            raise HTTPException(status_code=404, detail=f"Nie znaleziono VM: {target}. Odswiez liste maszyn.")
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie odczytac XML VM")
    try:
        return ET.fromstring(output), output
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Nie udalo sie parsowac XML VM: {exc}")

def assert_libvirt_domain_exists(vm_id: str):
    target = safe_vm_target(vm_id)
    code, output = run_vm_command(["virsh", "dominfo", target], timeout=8)
    if code != 0:
        raise HTTPException(status_code=404, detail=f"Nie znaleziono VM: {target}. Odswiez liste maszyn.")
    return target, output

def vm_text_fingerprint(vm_id: str, cdroms=None):
    parts = [safe_vm_target(vm_id).lower()]
    for row in cdroms or []:
        parts.append(Path(str(row.get("source") or "")).name.lower())
        parts.append(str(row.get("source") or "").lower())
    return " ".join(parts)

def detect_vm_profile_from_text(text: str, include_iso_aliases: bool = False):
    text = re.sub(r"[\s_.]+", "-", (text or "").lower())
    if any(token in text for token in ("win-95", "win95", "windows95", "windows-95", "windows_95", "osr2")):
        return "win95"
    if any(token in text for token in ("win-98", "win98", "windows98", "windows-98", "windows_98", "98se", "98-se", "98_se")):
        return "win98"
    if any(token in text for token in ("win-xp", "winxp", "windowsxp", "windows-xp", "windows_xp", "grtmpoem", "xpsp", "xp-sp")):
        return "winxp"
    if any(token in text for token in ("win-7", "win7", "windows7", "windows-7", "windows_7")):
        return "win7"
    if "freedos" in text or "free-dos" in text:
        return "freedos"
    if "reactos" in text:
        return "reactos"
    if include_iso_aliases:
        if re.search(r"(^|[-/\\])xp([-_/\\. ]|$)", text) or "service-pack-2" in text or "service-pack-3" in text:
            return "winxp"
        if re.search(r"(^|[-/\\])w95([-_/\\. ]|$)", text):
            return "win95"
        if re.search(r"(^|[-/\\])w98([-_/\\. ]|$)", text):
            return "win98"
    return ""

def infer_create_profile_from_media(data: VMCreateRequest, iso: Path):
    text = " ".join([
        data.os_id or "",
        data.name or "",
        data.iso_path or "",
        str(iso or ""),
        Path(str(data.iso_path or "")).name,
        Path(str(iso or "")).name,
    ])
    return detect_vm_profile_from_text(text, include_iso_aliases=True)

def resolve_vm_create_effective(data: VMCreateRequest, preset, iso: Path):
    detected_profile = infer_create_profile_from_media(data, iso)
    effective_preset = preset
    warnings = []
    if detected_profile in {"win95", "win98"} and preset.get("id") != detected_profile:
        effective_preset = os_preset(detected_profile)
        warnings.append(f"ISO rozpoznane jako {detected_profile}; wymuszono bezpieczny profil Win9x.")

    profile = VM_COMPAT_PROFILES.get(effective_preset.get("id", ""), {})
    effective = {
        "detected_profile": detected_profile,
        "auto_profile": effective_preset.get("id") if is_win9x_preset(effective_preset) else "",
        "preset": effective_preset,
        "warnings": warnings,
        "memory_mb": int(data.memory_mb),
        "vcpus": int(data.vcpus),
        "disk_gb": int(data.disk_gb),
        "network": data.network,
        "cpu": "",
        "attach_driver_media": True,
    }
    if is_win9x_preset(effective_preset):
        effective["memory_mb"] = int(profile.get("memory_mb") or effective_preset.get("memory_mb") or 256)
        effective["vcpus"] = 1
        effective["disk_gb"] = max(int(data.disk_gb), int(effective_preset.get("disk_gb") or data.disk_gb))
        effective["network"] = "none"
        effective["cpu"] = profile.get("cpu") or "qemu32"
        effective["attach_driver_media"] = False
        warnings.append(
            f"Win9x safe-mode: CPU {effective['cpu']}, 1 vCPU, {effective['memory_mb']} MB RAM, IDE/VGA/PS2, siec OFF, bez VirtIO ISO."
        )
    if is_macos_preset(effective_preset):
        effective["memory_mb"] = max(int(data.memory_mb), int(effective_preset.get("memory_mb") or 4096), 4096)
        effective["vcpus"] = max(2, int(data.vcpus))
        recommended_disk = int(effective_preset.get("disk_gb") or 64)
        effective["disk_gb"] = int(data.disk_gb)
        effective["cpu"] = "Penryn"
        effective["attach_driver_media"] = False
        if effective["disk_gb"] < recommended_disk:
            warnings.append(
                f"Cupertino BYOL: uzywam Twojego dysku {effective['disk_gb']} GB zamiast rekomendowanych {recommended_disk} GB."
            )
        warnings.append("Cupertino BYOL: UEFI/OVMF + OpenCore SATA, CPU Penryn, bez wbudowanego SMC/OSK.")
    return effective

def ensure_child(parent, tag: str, attrib=None):
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag, attrib or {})
    elif attrib:
        node.attrib.update(attrib)
    return node

def clear_boot_order(device):
    for boot in list(device.findall("boot")):
        device.remove(boot)

def set_device_boot_order(device, order: int):
    clear_boot_order(device)
    ET.SubElement(device, "boot", {"order": str(order)})

def ensure_cupertino_qemu_commandline(root, legal_byol_ack: bool):
    if not legal_byol_ack:
        return {"enabled": False, "reason": "legal_byol_ack false"}
    qemu_ns = "http://libvirt.org/schemas/domain/qemu/1.0"
    ET.register_namespace("qemu", qemu_ns)
    existing = root.find(f"{{{qemu_ns}}}commandline")
    if existing is None:
        existing = ET.SubElement(root, f"{{{qemu_ns}}}commandline")
    values = [node.attrib.get("value", "") for node in existing.findall(f"{{{qemu_ns}}}arg")]
    safe_args = [("-smbios", "type=2")]
    added = []
    for key, value in safe_args:
        if key not in values:
            ET.SubElement(existing, f"{{{qemu_ns}}}arg", {"value": key})
            added.append(key)
        if value not in values:
            ET.SubElement(existing, f"{{{qemu_ns}}}arg", {"value": value})
            added.append(value)
    return {
        "enabled": True,
        "added": added,
        "legal_shield": "qemu:commandline active without embedded Apple SMC/OSK",
    }

def set_disk_source_file(disk, path: Path):
    source = ensure_child(disk, "source")
    source.attrib.clear()
    source.attrib["file"] = str(path)

def set_disk_driver(disk, image_type: str = "qcow2", bus: str = "", readonly: bool = False, trim: bool = True):
    driver = ensure_child(disk, "driver")
    driver.attrib.clear()
    driver.attrib.update(qemu_disk_driver_attrs(image_type, bus, readonly, trim=trim))

def set_disk_readonly(disk, readonly: bool):
    for node in list(disk.findall("readonly")):
        disk.remove(node)
    if readonly:
        ET.SubElement(disk, "readonly")

def path_same(a: str, b: Path):
    try:
        return Path(a or "").resolve() == Path(b).resolve()
    except Exception:
        return False

def ensure_cupertino_disk(devices, source_path: Path, device: str, target_dev: str, bus: str, order: int, image_type: str = "qcow2", readonly: bool = False, trim: bool = True):
    found = None
    for disk in devices.findall("disk"):
        if path_same(disk_source_text(disk), source_path):
            found = disk
            break
    if found is None:
        found = ET.SubElement(devices, "disk", {"type": "file", "device": device})
    found.attrib["type"] = "file"
    found.attrib["device"] = device
    set_disk_driver(found, image_type, bus, readonly, trim=trim)
    set_disk_source_file(found, source_path)
    target_node(found, target_dev, bus)
    set_disk_readonly(found, readonly)
    set_device_boot_order(found, order)
    return found

def remove_direct_pci_addresses(node):
    removed = 0
    for address in list(node.findall("address")):
        if (address.attrib.get("type") or "").lower() == "pci":
            node.remove(address)
            removed += 1
    return removed

def ensure_cupertino_q35_topology(devices):
    removed_addresses = 0
    removed_ide = 0
    for node in list(devices.findall("controller")):
        if (node.attrib.get("type") or "").lower() == "ide":
            devices.remove(node)
            removed_ide += 1
    pci_controllers = [node for node in devices.findall("controller") if (node.attrib.get("type") or "").lower() == "pci"]
    root_controller = None
    for node in pci_controllers:
        if str(node.attrib.get("index", "0")) == "0":
            if root_controller is None:
                root_controller = node
            else:
                devices.remove(node)
    if root_controller is None:
        root_controller = ET.Element("controller", {"type": "pci", "index": "0", "model": "pcie-root"})
        devices.insert(0, root_controller)
    root_controller.attrib["type"] = "pci"
    root_controller.attrib["index"] = "0"
    root_controller.attrib["model"] = "pcie-root"
    removed_addresses += remove_direct_pci_addresses(root_controller)

    for node in list(devices):
        removed_addresses += remove_direct_pci_addresses(node)
        if node.tag == "controller" and node is not root_controller and node.attrib.get("type") == "pci" and node.attrib.get("model") == "pci-root":
            node.attrib["model"] = "pcie-root-port"

    if not any(node.attrib.get("type") == "sata" and str(node.attrib.get("index", "0")) == "0" for node in devices.findall("controller")):
        devices.insert(1, ET.Element("controller", {"type": "sata", "index": "0"}))
    if not any(node.attrib.get("type") == "usb" and node.attrib.get("model") == "qemu-xhci" for node in devices.findall("controller")):
        devices.insert(2, ET.Element("controller", {"type": "usb", "model": "qemu-xhci"}))
    return {
        "root": root_controller.attrib.copy(),
        "removed_ide_controllers": removed_ide,
        "removed_pci_addresses": removed_addresses,
    }

def mutate_cupertino_xml(root, target: str, iso: Path, disk: Path, prereq: dict, legal_byol_ack: bool = False):
    target = safe_vm_target(target)
    root.attrib["type"] = "kvm"
    os_node = ensure_child(root, "os")
    type_node = ensure_child(os_node, "type", {"arch": "x86_64", "machine": "q35"})
    type_node.text = "hvm"
    for boot in list(os_node.findall("boot")):
        os_node.remove(boot)
    loader = ensure_child(os_node, "loader", {"readonly": "yes", "type": "pflash"})
    loader.text = prereq["ovmf_code"]
    nvram_dir = Path("/var/lib/libvirt/qemu/nvram")
    try:
        nvram_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    nvram = ensure_child(os_node, "nvram", {"template": prereq["ovmf_vars"]})
    if not (nvram.text or "").strip():
        nvram.text = str(nvram_dir / f"{target}_VARS.fd")

    features = ensure_child(root, "features")
    ensure_child(features, "acpi")
    ensure_child(features, "apic")
    set_custom_cpu(root, "Penryn", fallback="allow", hidden_kvm=True)

    clock = ensure_child(root, "clock", {"offset": "utc"})
    clock.attrib["offset"] = "utc"
    devices = ensure_child(root, "devices")
    ensure_child(devices, "emulator").text = "/usr/bin/qemu-system-x86_64"
    ensure_cupertino_q35_topology(devices)

    opencore = Path(prereq["opencore"]).resolve()
    ensure_libvirt_file_access(opencore)
    ensure_libvirt_file_access(iso)
    ensure_libvirt_file_access(disk)
    opencore_overlay = ensure_cupertino_opencore_overlay(target, opencore)["path"]
    installer_overlay = ensure_cupertino_installer_overlay(target, iso)["path"]

    # Re-map boot media deterministically: OpenCore -> installer overlay -> ISO marker -> target disk.
    # Q35 on this host rejects IDE controllers, so stale virt-install IDE CD-ROMs must go.
    for disk_node in list(devices.findall("disk")):
        source = disk_source_text(disk_node)
        target_node_ref = disk_node.find("target")
        bus = (target_node_ref.attrib.get("bus") if target_node_ref is not None else "").lower()
        device = (disk_node.attrib.get("device") or "").lower()
        source_path = Path(source).resolve() if source else None
        if (
            bus == "ide"
            or device == "cdrom"
            or not source
            or path_same(source, opencore)
            or path_same(source, opencore_overlay)
            or path_same(source, installer_overlay)
            or path_same(source, iso)
            or path_same(source, disk)
            or (source_path is not None and path_is_under(source_path, CUPERTINO_MEDIA_OVERLAY_DIR))
        ):
            devices.remove(disk_node)
    ensure_cupertino_disk(devices, opencore_overlay, "disk", "sda", "sata", 1, "qcow2", False, trim=False)
    ensure_cupertino_disk(devices, installer_overlay, "disk", "sdb", "sata", 2, "qcow2", False, trim=False)
    ensure_cupertino_disk(devices, iso, "cdrom", "sdc", "sata", 3, "raw", True, trim=False)
    ensure_cupertino_disk(devices, disk, "disk", "sdd", "sata", 4, "qcow2", False, trim=True)

    for iface in devices.findall("interface"):
        model = ensure_child(iface, "model")
        model.attrib["type"] = "e1000e"
    if not devices.findall("input"):
        ET.SubElement(devices, "input", {"type": "tablet", "bus": "usb"})
    elif not any(node.attrib.get("type") == "tablet" and node.attrib.get("bus") == "usb" for node in devices.findall("input")):
        ET.SubElement(devices, "input", {"type": "tablet", "bus": "usb"})
    video = ensure_child(devices, "video")
    model = ensure_child(video, "model")
    model.attrib.update({"type": "virtio", "vram": "262144", "heads": "1", "primary": "yes"})
    ensure_cupertino_qemu_commandline(root, legal_byol_ack)
    return root

def apply_cupertino_profile(vm_id: str, iso: Path, disk: Path, prereq: dict, restart: bool = True, legal_byol_ack: bool = False):
    target = safe_vm_target(vm_id)
    if not legal_byol_ack:
        raise HTTPException(status_code=403, detail="Cupertino Legal Shield: wymagane legal_byol_ack=True")
    if not prereq.get("ok"):
        raise HTTPException(status_code=412, detail={"message": "Cupertino prerequisites nie przeszly", **prereq})
    state_code, state_output = run_vm_command(["virsh", "domstate", target], timeout=8)
    was_running = state_code == 0 and "running" in state_output.lower()
    if was_running:
        run_vm_command(["virsh", "destroy", target], timeout=20)
    xml_text = dump_domain_xml(target, inactive=True)
    try:
        root = ET.fromstring(xml_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Nie udalo sie parsowac XML VM: {exc}")
    mutate_cupertino_xml(root, target, iso, disk, prereq, legal_byol_ack=legal_byol_ack)
    define_result = define_domain_xml_transaction(target, root, "cupertino")
    start_output = ""
    if restart:
        start_code, start_output = run_vm_command(["virsh", "start", target], timeout=60)
        if start_code != 0:
            rollback_xml = Path("/tmp") / f"nexus-cupertino-start-rollback-{target}-{uuid.uuid4().hex[:10]}.xml"
            try:
                rollback_xml.write_text(xml_text, encoding="utf-8")
                run_vm_command(["virsh", "define", str(rollback_xml)], timeout=30)
            finally:
                try:
                    rollback_xml.unlink()
                except Exception:
                    pass
            raise HTTPException(status_code=500, detail=f"Cupertino start nie przeszedl; XML przywrocony. Blad: {start_output.strip()}")
    log_event(f"VM_CUPERTINO_PATCH vm={target} restart={restart} opencore={Path(prereq.get('opencore','')).name}")
    return {
        "status": "patched",
        "vm_id": target,
        "was_running": was_running,
        "restarted": bool(restart),
        "cpu": "Penryn",
        "boot_order": ["opencore.qcow2", Path(str(iso)).name, Path(str(disk)).name],
        "legal_shield": prereq.get("legal_shield"),
        "define_output": define_result.get("define_output", ""),
        "start_output": start_output.strip(),
    }

def inspect_cupertino_domain(vm_id: str):
    target = safe_vm_target(vm_id)
    try:
        xml_text = dump_domain_xml(target, inactive=True)
    except HTTPException:
        return {"enabled": False, "ok": True, "missing": []}
    lowered = xml_text.lower()
    enabled = "opencore" in lowered or "<model fallback=" in lowered and "penryn" in lowered
    if not enabled:
        return {"enabled": False, "ok": True, "missing": []}
    missing = []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        root = None
    if "opencore" not in lowered:
        missing.append("opencore overlay")
    if root is not None:
        for controller in root.findall("./devices/controller"):
            if (controller.attrib.get("type") or "").lower() == "ide":
                missing.append("IDE controller unsupported for Cupertino/Q35")
        for disk_node in root.findall("./devices/disk"):
            source = disk_source_text(disk_node)
            target_node_ref = disk_node.find("target")
            driver = disk_node.find("driver")
            bus = (target_node_ref.attrib.get("bus") if target_node_ref is not None else "").lower()
            name = Path(source).name.lower() if source else ""
            if bus == "ide":
                missing.append("IDE disk target unsupported for Cupertino/Q35")
            if "opencore" in name:
                if name == "opencore.qcow2":
                    missing.append("OpenCore musi byc per-VM overlay, nie bazowy obraz")
                if disk_node.find("readonly") is not None:
                    missing.append("OpenCore overlay nie moze byc readonly")
                if driver is not None and (driver.attrib.get("discard") or driver.attrib.get("detect_zeroes")):
                    missing.append("OpenCore overlay musi byc bez discard/detect_zeroes")
    if "ovmf_code" not in lowered and "pflash" not in lowered:
        missing.append("OVMF pflash")
    if "isa-applesmc" in lowered or "osk=" in lowered:
        missing.append("Legal Shield violation: SMC/OSK")
    return {"enabled": True, "ok": not missing, "missing": sorted(set(missing))}

def enforce_cupertino_start_guard(vm_id: str):
    status = inspect_cupertino_domain(vm_id)
    if status.get("enabled") and not status.get("ok"):
        raise HTTPException(status_code=412, detail={"message": "Cupertino guard zatrzymal start VM", **status})
    return status

def vm_primary_disk_path(vm_id: str):
    target = safe_vm_target(vm_id)
    def is_primary_candidate(path: Path):
        name = path.name.lower()
        if "opencore" in name or name.endswith("-media.qcow2") or "-media-" in name:
            return False
        if path_is_under(path, OPENCORE_OVERLAY_DIR) or path_is_under(path, CUPERTINO_MEDIA_OVERLAY_DIR):
            return False
        return True
    paths = vm_storage_paths(target)
    for path in paths:
        if is_primary_candidate(path):
            return path
    for row in vm_block_devices(target):
        if row.get("device") != "disk":
            continue
        source = row.get("source") or ""
        if not source:
            continue
        try:
            path = allowed_vm_disk_path(source)
            if not is_primary_candidate(path):
                continue
            return path
        except Exception:
            continue
    raise HTTPException(status_code=412, detail=f"Nie znaleziono glownego dysku VM {target}")

def vm_installer_iso_path(vm_id: str, iso_path: str = ""):
    if iso_path:
        return prepare_libvirt_iso(allowed_iso_path(iso_path))
    for row in vm_cdrom_targets(vm_id):
        source = row.get("source") or ""
        if not source or Path(source).suffix.lower() != ".iso":
            continue
        name = Path(source).name.lower()
        if "virtio" in name or "driver" in name or "selected-drivers" in name:
            continue
        return prepare_libvirt_iso(allowed_iso_path(source))
    raise HTTPException(status_code=412, detail="Brak instalatora ISO. Podaj iso_path albo podepnij BaseSystem.iso jako CD-ROM.")

def auto_apply_cupertino_profile_for_start(vm_id: str):
    target = safe_vm_target(vm_id)
    status = inspect_cupertino_domain(target)
    if not status.get("enabled"):
        return None
    state = vm_domain_state_label(target)
    if "running" in state.lower():
        return {"status": "already_running", "state": state}
    prereq = cupertino_prerequisites("", "", "")
    if not prereq.get("ok"):
        raise HTTPException(status_code=412, detail={"message": "Cupertino prerequisites nie przeszly", **prereq})
    disk = vm_primary_disk_path(target)
    iso = vm_installer_iso_path(target, "")
    patch = apply_cupertino_profile(target, iso, disk, prereq, restart=False, legal_byol_ack=True)
    return {"status": "normalized", "state": state, "iso": str(iso), "disk": str(disk), "patch": patch}

def cupertino_bootloader_arg(value: str):
    raw = (value or "").strip()
    if not raw:
        return ""
    if raw.lower() == "opencore.qcow2":
        return raw
    return str(allowed_vm_disk_path(raw))

def detect_vm_compat_profile(vm_id: str, cdroms=None):
    name_profile = detect_vm_profile_from_text(safe_vm_target(vm_id), include_iso_aliases=False)
    if name_profile:
        return name_profile
    media_text = " ".join(
        f"{Path(str(row.get('source') or '')).name} {row.get('source') or ''}"
        for row in (cdroms or [])
    )
    media_profile = detect_vm_profile_from_text(media_text, include_iso_aliases=True)
    if media_profile:
        return media_profile
    return ""

def xml_has_cpu_model(root, model: str):
    text = ET.tostring(root, encoding="unicode").lower()
    return str(model or "").lower() in text

def xml_memory_mb(root):
    node = root.find("currentMemory") or root.find("memory")
    if node is None:
        return None
    try:
        value = int((node.text or "0").strip())
        unit = (node.attrib.get("unit") or "KiB").lower()
        if unit in {"mib", "mb"}:
            return value
        if unit in {"gib", "gb"}:
            return value * 1024
        return round(value / 1024)
    except Exception:
        return None

def xml_device_summary(root):
    devices = root.find("devices")
    inputs = []
    controllers = []
    videos = []
    balloons = []
    graphics = []
    features = []
    if devices is not None:
        for node in devices.findall("input"):
            inputs.append({"type": node.attrib.get("type", ""), "bus": node.attrib.get("bus", "")})
        for node in devices.findall("controller"):
            controllers.append({"type": node.attrib.get("type", ""), "model": node.attrib.get("model", "")})
        for node in devices.findall("video/model"):
            videos.append({"type": node.attrib.get("type", ""), "vram": node.attrib.get("vram", "")})
        for node in devices.findall("memballoon"):
            balloons.append({"model": node.attrib.get("model", "")})
        for node in devices.findall("graphics"):
            graphics.append({"type": node.attrib.get("type", ""), "listen": node.attrib.get("listen", ""), "port": node.attrib.get("port", ""), "autoport": node.attrib.get("autoport", "")})
    feature_node = root.find("features")
    if feature_node is not None:
        features = [child.tag for child in list(feature_node)]
    return {"inputs": inputs, "controllers": controllers, "videos": videos, "balloons": balloons, "graphics": graphics, "features": features}

def doctor_issue(issue_id, severity, title, detail, fix=None):
    return {
        "id": issue_id,
        "severity": severity,
        "title": title,
        "detail": detail,
        "fix": fix or {},
    }

def diagnose_vm(vm_id: str):
    target = safe_vm_target(vm_id)
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="VM Doctor jest teraz wspierany dla libvirt/KVM")
    target, dominfo_text = assert_libvirt_domain_exists(target)
    root, xml_text = vm_dumpxml_root(target, inactive=True)
    info = parse_dominfo(target)
    cdroms = vm_cdrom_targets(target)
    interfaces = vm_interface_rows(target)
    devices = xml_device_summary(root)
    profile = detect_vm_compat_profile(target, cdroms)
    bad_cdroms = bad_cdrom_media_rows(target)
    issues = []
    quick_actions = []
    xml_lower = xml_text.lower()
    memory_mb = xml_memory_mb(root)
    ps2_mouse = any(row.get("type") == "mouse" and row.get("bus") == "ps2" for row in devices["inputs"])
    ps2_keyboard = any(row.get("type") == "keyboard" and row.get("bus") == "ps2" for row in devices["inputs"])
    usb_tablet = any(row.get("type") == "tablet" and row.get("bus") == "usb" for row in devices["inputs"])
    vnc_local = any(row.get("type") == "vnc" and ((row.get("listen") or "") in {"", "127.0.0.1"} or row.get("autoport") == "yes") for row in devices["graphics"])
    has_virtio_media = any(any(token in str(row.get("source", "")).lower() for token in ("virtio", "selected-drivers", "vioscsi", "netkvm")) for row in cdroms)

    if not vnc_local:
        issues.append(doctor_issue("vnc", "critical", "Brak lokalnego VNC", "Konsola noVNC moze nie ruszyc, bo XML nie ma lokalnego graphics type='vnc'.", {"kind": "console"}))
    if bad_cdroms:
        details = "; ".join(f"{row.get('target')} -> {row.get('source')}" for row in bad_cdroms[:4])
        issues.append(doctor_issue("bad-cdrom-media", "critical", "CD-ROM wskazuje na dysk", f"To blokuje start QEMU lockiem obrazu. Bledne wpisy: {details}", {"endpoint": "/api/vms/media/repair", "body": {"vm_id": target, "live": True, "config": True}}))
        quick_actions.append({"label": "Odepnij bledne CD-ROM", "endpoint": "/api/vms/media/repair", "body": {"vm_id": target, "live": True, "config": True}})
    if not (ps2_mouse and ps2_keyboard):
        issues.append(doctor_issue("input-ps2", "warn", "Brakuje PS/2 input", "Dodaj PS/2 mouse/keyboard jako fallback dla starych instalatorow i noVNC.", {"endpoint": "/api/vms/input/repair", "body": {"vm_id": target, "backend": "auto", "live": True, "config": True}}))
        quick_actions.append({"label": "Napraw mysz/klawiature", "endpoint": "/api/vms/input/repair", "body": {"vm_id": target, "backend": "auto", "live": True, "config": True}})

    legacy_profiles = {"win95", "win98", "freedos"}
    semi_legacy_profiles = legacy_profiles | {"winxp", "reactos"}
    if profile in semi_legacy_profiles:
        prof = VM_COMPAT_PROFILES.get(profile, {})
        expected_cpus = []
        for cpu in [prof.get("cpu"), *(prof.get("acceptable_cpus") or [])]:
            if cpu and cpu not in expected_cpus:
                expected_cpus.append(cpu)
        if expected_cpus and not any(xml_has_cpu_model(root, cpu) for cpu in expected_cpus):
            issues.append(doctor_issue("cpu-profile", "critical", "Zly CPU dla legacy", f"Wykryto {profile}, a XML nie uzywa zadnego z CPU: {', '.join(expected_cpus)}.", {"endpoint": "/api/vms/compat/apply", "body": {"vm_id": target, "profile": profile, "restart": True, "network": "safe"}}))
        if profile in legacy_profiles and interfaces:
            issues.append(doctor_issue("legacy-network", "critical", "Siec wlaczona za wczesnie", "Win95/Win98/DOS potrafia wywalic instalacje na NDIS. Instaluj najpierw bez NIC.", {"endpoint": "/api/vms/compat/apply", "body": {"vm_id": target, "profile": profile, "restart": True, "network": "off"}}))
        if profile in legacy_profiles and has_virtio_media:
            issues.append(doctor_issue("virtio-media", "critical", "VirtIO ISO podpiete do legacy", "Win9x/DOS nie powinien dostawac paczki VirtIO podczas instalacji.", {"endpoint": "/api/vms/compat/apply", "body": {"vm_id": target, "profile": profile, "restart": True, "network": "off"}}))
        if profile in legacy_profiles and ("acpi" in devices["features"] or "apic" in devices["features"]):
            issues.append(doctor_issue("acpi-apic", "warn", "ACPI/APIC wlaczone", "Stare Windowsy sa stabilniejsze z ACPI/APIC OFF.", {"endpoint": "/api/vms/compat/apply", "body": {"vm_id": target, "profile": profile, "restart": True, "network": "off"}}))
        if profile in legacy_profiles and any(row.get("type") == "usb" and row.get("model") != "none" for row in devices["controllers"]):
            issues.append(doctor_issue("usb-controller", "warn", "USB controller aktywny", "Do instalacji Win95/98/DOS lepsze jest czyste PS/2 bez USB.", {"endpoint": "/api/vms/compat/apply", "body": {"vm_id": target, "profile": profile, "restart": True, "network": "off"}}))
        if profile in semi_legacy_profiles and any(row.get("model") not in {"", "none"} for row in devices["balloons"]):
            issues.append(doctor_issue("balloon", "warn", "VirtIO balloon aktywny", "Sterownik balloon moze byc nieobslugiwany przez legacy system.", {"endpoint": "/api/vms/compat/apply", "body": {"vm_id": target, "profile": profile, "restart": True, "network": "safe"}}))
        if profile in legacy_profiles and memory_mb and memory_mb > int(prof.get("memory_mb", 256) or 256) * 2:
            issues.append(doctor_issue("legacy-memory", "warn", "Za duzo RAM dla instalatora", f"{profile} ma {memory_mb} MB RAM; bezpieczny profil uzywa {prof.get('memory_mb')} MB.", {"endpoint": "/api/vms/compat/apply", "body": {"vm_id": target, "profile": profile, "restart": True, "network": "off"}}))
        quick_actions.append({"label": f"Zastosuj {profile.upper()} FIX", "endpoint": "/api/vms/compat/apply", "body": {"vm_id": target, "profile": profile, "restart": True, "network": "off" if profile in legacy_profiles else "safe"}})
    elif usb_tablet and not ps2_mouse:
        issues.append(doctor_issue("modern-input-only", "info", "Tylko tablet USB", "Dla nowych systemow to OK, ale PS/2 fallback pomaga przy BIOS/installerach.", {"endpoint": "/api/vms/input/repair", "body": {"vm_id": target, "backend": "auto", "live": True, "config": True}}))

    if not cdroms:
        issues.append(doctor_issue("no-cdrom", "info", "Brak CD-ROM", "Jesli to instalacja, podepnij ISO w VM CONFIG.", {"kind": "attach-iso"}))
    if "running" in str(info.get("state", "")).lower() and not find_qemu_pid(target):
        issues.append(doctor_issue("qemu-pid", "critical", "Brak procesu QEMU", "Libvirt twierdzi, ze VM dziala, ale nie znaleziono procesu qemu.", {"kind": "watchdog"}))

    weights = {"critical": 32, "warn": 14, "info": 4}
    penalty = sum(weights.get(item["severity"], 4) for item in issues)
    score = max(0, 100 - penalty)
    if any(item["severity"] == "critical" for item in issues):
        state = "critical"
    elif any(item["severity"] == "warn" for item in issues):
        state = "warn"
    else:
        state = "ok"
    return {
        "vm_id": target,
        "state": state,
        "score": score,
        "detected_profile": profile or "generic",
        "recommended_profile": profile,
        "summary": "OK" if not issues else f"{len(issues)} spraw do poprawy",
        "issues": issues,
        "quick_actions": quick_actions,
        "config": {
            "dominfo": info,
            "memory_mb": memory_mb,
            "cdroms": cdroms,
            "bad_cdroms": bad_cdroms,
            "interfaces": interfaces,
            "devices": devices,
            "has_qemu_pid": bool(find_qemu_pid(target)),
            "fingerprint": vm_text_fingerprint(target, cdroms)[:500],
            "dominfo_raw": dominfo_text[:1000],
        },
    }

def find_qemu_pid(identifier: str):
    needle = str(identifier or "")
    if not needle:
        return None
    if HAS_PSUTIL:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                name = proc.info.get("name") or ""
                cmdline = " ".join(proc.info.get("cmdline") or [])
                if "qemu-system" in name or "qemu-system" in cmdline:
                    if needle in cmdline:
                        return int(proc.info["pid"])
            except Exception:
                continue
    if shutil.which("pgrep"):
        code, output = run_vm_command(["pgrep", "-fa", "qemu-system"], timeout=5)
        if code == 0:
            for line in output.splitlines():
                if needle in line:
                    try:
                        return int(line.split(None, 1)[0])
                    except Exception:
                        continue
    return None

def vm_process_telemetry(pid):
    data = {"pid": pid, "cpu_percent": None, "mem_mb": None}
    if not pid or not HAS_PSUTIL:
        return data
    try:
        proc = psutil.Process(int(pid))
        data["cpu_percent"] = round(proc.cpu_percent(interval=0.03), 1)
        data["mem_mb"] = round(proc.memory_info().rss / 1024 / 1024, 1)
    except Exception:
        pass
    return data

def latest_guest_telemetry(vm_id: str):
    data = read_json(VM_GUEST_TELEMETRY_FILE, {})
    item = data.get(vm_id) or {}
    if not item:
        return None
    try:
        seen = datetime.datetime.fromisoformat(item.get("received_at", ""))
        age = max(0, int((datetime.datetime.now() - seen).total_seconds()))
    except Exception:
        age = 999999
    item["age_seconds"] = age
    item["online"] = age <= 90
    return item

def vm_billing_store():
    data = read_json(VM_BILLING_FILE, {})
    data.setdefault("enabled", True)
    data.setdefault("rate_per_hour", 10.0)
    data.setdefault("currency", "NXC")
    data.setdefault("tick_seconds", 60)
    data.setdefault("state_multipliers", {"running": 1.0, "paused": 0.25, "suspended": 0.0, "stopped": 0.0})
    data.setdefault("storage_rate_per_gb_hour", 0.0)
    data.setdefault("storage_billing_basis", "actual")
    data.setdefault("empty_balance_action", "shutdown")
    data.setdefault("hard_kill_after_minutes", 0)
    data.setdefault("scheduler", {"enabled": True, "last_tick": "", "last_status": "boot"})
    data.setdefault("wallets", {})
    data.setdefault("vm_owners", {})
    data.setdefault("vm_acl", {})
    data.setdefault("user_limits", {})
    data.setdefault("runtime", {})
    data.setdefault("ledger", [])
    multipliers = data.setdefault("state_multipliers", {})
    for state, value in {"running": 1.0, "paused": 0.25, "suspended": 0.0, "stopped": 0.0}.items():
        try:
            multipliers[state] = max(0.0, min(1.0, float(multipliers.get(state, value))))
        except Exception:
            multipliers[state] = value
    return data

def save_vm_billing(data):
    data["ledger"] = data.get("ledger", [])[-1000:]
    write_json(VM_BILLING_FILE, data)

def vm_wallet(data, username: str):
    user = normalize_username(username or "admin")
    wallets = data.setdefault("wallets", {})
    wallet = wallets.setdefault(user, {"balance": 0.0, "credited": 0.0, "spent": 0.0, "updated_at": now_iso()})
    wallet["balance"] = float(wallet.get("balance", 0) or 0)
    wallet["credited"] = float(wallet.get("credited", 0) or 0)
    wallet["spent"] = float(wallet.get("spent", 0) or 0)
    return wallet

def vm_is_running(item):
    status = str(item.get("status", "")).lower()
    return "running" in status or "uruch" in status

def vm_has_frozen_state(vm_id: str):
    target = safe_vm_target(vm_id)
    try:
        rows = read_json(HYPER_SLEEP_FILE, [])
        for row in rows:
            if row.get("vm_id") != target or row.get("status") != "frozen":
                continue
            path = Path(row.get("path", ""))
            if path.exists():
                return True
    except Exception:
        pass
    return False

def vm_billing_state(item):
    status = str(item.get("status", "")).lower()
    vm_id = str(item.get("id") or item.get("name") or "").strip()
    if "paused" in status or "pmsuspended" in status:
        return "paused"
    if "managed-save" in status or "managed save" in status or "saved" in status:
        return "suspended"
    if vm_id and vm_has_frozen_state(vm_id):
        return "suspended"
    if vm_is_running(item):
        return "running"
    return "stopped"

def vm_billing_storage_gb(vm_id: str, basis: str = "actual"):
    basis = (basis or "actual").lower()
    total = 0
    disks = []
    try:
        for path in vm_storage_paths(vm_id):
            info = qemu_img_info_json(path)
            if basis == "virtual":
                size = int(info.get("virtual_size") or info.get("file_size") or 0)
            elif basis == "file":
                size = int(info.get("file_size") or 0)
            else:
                size = int(info.get("actual_size") or info.get("file_size") or 0)
            total += max(0, size)
            disks.append({"path": str(path), "basis": basis, "size": size, "size_label": fmt_size(size)})
    except Exception as exc:
        log_event(f"VM_BILLING_STORAGE error vm={vm_id}: {exc}")
    return {"gb": round(total / 1024 / 1024 / 1024, 4), "bytes": total, "disks": disks}

def vm_billing_rates(data, state: str, storage_gb: float):
    base = float(data.get("rate_per_hour", 10.0) or 0)
    multipliers = data.get("state_multipliers") or {}
    multiplier = float(multipliers.get(state, 1.0 if state == "running" else 0.0) or 0)
    compute_rate = base * multiplier
    storage_rate = float(data.get("storage_rate_per_gb_hour", 0.0) or 0) * max(0.0, float(storage_gb or 0))
    return {
        "base_rate_per_hour": round(base, 6),
        "state_multiplier": round(multiplier, 4),
        "compute_rate_per_hour": round(compute_rate, 6),
        "storage_rate_per_hour": round(storage_rate, 6),
        "total_rate_per_hour": round(compute_rate + storage_rate, 6),
    }

def vm_empty_balance_action(vm_id: str, item: dict, data: dict, record: dict, owner: str):
    action = (data.get("empty_balance_action") or "shutdown").lower()
    if action in {"none", "off", "disabled"}:
        return {"action": action, "code": 0, "output": "empty balance action disabled"}
    vm_type = str(item.get("type") or "").lower()
    backend = detect_vm_backend()
    if "libvirt" in vm_type or backend == "libvirt":
        if action in {"managedsave", "suspend", "freeze"}:
            cmd = ["virsh", "managedsave", vm_id]
        elif action in {"destroy", "hard_stop", "hard-kill", "kill"}:
            cmd = ["virsh", "destroy", vm_id]
        else:
            cmd = ["virsh", "shutdown", vm_id]
    elif "qemu" in vm_type or backend == "proxmox":
        if action in {"destroy", "hard_stop", "hard-kill", "kill"}:
            cmd = ["qm", "stop", vm_id]
        elif action in {"managedsave", "suspend", "freeze"}:
            cmd = ["qm", "suspend", vm_id]
        else:
            cmd = ["qm", "shutdown", vm_id]
    else:
        return {"action": action, "code": 1, "output": "Nieznany backend VM"}
    code, output = run_vm_command(cmd, timeout=30)
    record["last_empty_action"] = action
    record["last_empty_output"] = (output or "").strip()[:500]
    record["last_empty_code"] = code
    record_alert(
        "VM zatrzymana przez NXC Token Vault",
        f"{vm_id}: saldo {owner} spadlo do {float(vm_wallet(data, owner).get('balance', 0) or 0):.4f}. Akcja={action}. code={code}",
        "critical" if code != 0 else "warn",
        f"vm-token-empty-{vm_id}",
    )
    try:
        send_webhook_event("billing.empty", {"vm_id": vm_id, "owner": owner, "action": action, "code": code, "output": (output or "")[:500]})
    except Exception as exc:
        log_event(f"WEBHOOK billing.empty error: {exc}")
    return {"action": action, "command": cmd, "code": code, "output": (output or "").strip()[:1000]}

def iso_dt(value):
    try:
        return datetime.datetime.fromisoformat(value)
    except Exception:
        return None

def vm_billing_owner(data, vm_id: str, fallback="admin"):
    owners = data.setdefault("vm_owners", {})
    owner = owners.get(vm_id) or fallback or "admin"
    try:
        owner = normalize_username(owner)
    except Exception:
        owner = "admin"
    owners[vm_id] = owner
    return owner

def human_duration(seconds: float):
    try:
        seconds = max(0, int(seconds or 0))
    except Exception:
        seconds = 0
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

def vm_billing_forecast(data, active=None):
    rate = float(data.get("rate_per_hour", 10.0) or 0)
    enabled = bool(data.get("enabled", True))
    active_rows = active if active is not None else [
        {"owner": row.get("owner", "admin"), "running": bool(row.get("running")), "state": row.get("state", "running" if row.get("running") else "stopped"), "charge_rate_per_hour": row.get("charge_rate_per_hour", 0)}
        for row in data.get("runtime", {}).values()
    ]
    owner_stats = {}
    for row in active_rows or []:
        owner = normalize_username(row.get("owner") or "admin")
        stats = owner_stats.setdefault(owner, {"running": 0, "billing_vms": 0, "hourly_burn": 0.0, "states": {}})
        state = row.get("state") or ("running" if row.get("running") else "stopped")
        stats["states"][state] = stats["states"].get(state, 0) + 1
        if row.get("running"):
            stats["running"] += 1
        charge_rate = float(row.get("charge_rate_per_hour", 0) or 0)
        if charge_rate > 0:
            stats["billing_vms"] += 1
            stats["hourly_burn"] += charge_rate
    rows = []
    for owner, wallet in data.get("wallets", {}).items():
        stats = owner_stats.get(owner, {"running": 0, "billing_vms": 0, "hourly_burn": 0.0, "states": {}})
        running = int(stats.get("running", 0))
        hourly_burn = float(stats.get("hourly_burn", 0) or 0) if enabled else 0
        balance = float(wallet.get("balance", 0) or 0)
        seconds_left = None
        if hourly_burn > 0:
            seconds_left = max(0, (balance / hourly_burn) * 3600)
        rows.append({
            "owner": owner,
            "running_vms": running,
            "billing_vms": int(stats.get("billing_vms", 0)),
            "hourly_burn": round(hourly_burn, 4),
            "balance": round(balance, 4),
            "seconds_left": round(seconds_left, 0) if seconds_left is not None else None,
            "time_left": human_duration(seconds_left) if seconds_left is not None else "bez aktywnego zuzycia",
            "states": stats.get("states", {}),
            "state": "empty" if hourly_burn > 0 and balance <= 0 else ("warning" if hourly_burn > 0 and seconds_left is not None and seconds_left <= 3600 else "ok"),
        })
    return sorted(rows, key=lambda item: (item["state"] != "empty", item["owner"]))

def vm_billing_public(data=None, active=None):
    data = data or vm_billing_store()
    wallets = {}
    for user, row in data.get("wallets", {}).items():
        wallets[user] = {
            "balance": round(float(row.get("balance", 0) or 0), 4),
            "credited": round(float(row.get("credited", 0) or 0), 4),
            "spent": round(float(row.get("spent", 0) or 0), 4),
            "updated_at": row.get("updated_at", ""),
        }
    return {
        "enabled": bool(data.get("enabled", True)),
        "rate_per_hour": float(data.get("rate_per_hour", 10.0) or 0),
        "currency": data.get("currency", "NXC"),
        "tick_seconds": int(data.get("tick_seconds", 60) or 60),
        "state_multipliers": data.get("state_multipliers", {}),
        "storage_rate_per_gb_hour": float(data.get("storage_rate_per_gb_hour", 0.0) or 0),
        "storage_billing_basis": data.get("storage_billing_basis", "actual"),
        "empty_balance_action": data.get("empty_balance_action", "shutdown"),
        "hard_kill_after_minutes": int(data.get("hard_kill_after_minutes", 0) or 0),
        "scheduler": data.get("scheduler", {}),
        "wallets": wallets,
        "active": active if active is not None else [],
        "forecast": vm_billing_forecast(data, active),
        "runtime": data.get("runtime", {}),
        "ledger": data.get("ledger", [])[-80:],
    }

def vm_inventory_for_billing():
    backend = detect_vm_backend()
    items = []
    try:
        if backend == "proxmox":
            code, output = run_vm_command(["qm", "list"], timeout=12)
            if code != 0:
                return []
            for line in output.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 3 and parts[0].isdigit():
                    items.append({"id": parts[0], "name": parts[1], "status": parts[2], "type": "QEMU/KVM"})
        elif backend == "libvirt":
            code, output = run_vm_command(["virsh", "list", "--all", "--name"], timeout=12)
            if code != 0:
                return []
            for name in [x.strip() for x in output.splitlines() if x.strip()]:
                state_code, state = run_vm_command(["virsh", "domstate", name], timeout=8)
                status = state.strip() if state_code == 0 else "unknown"
                info_code, info = run_vm_command(["virsh", "dominfo", name], timeout=8)
                if info_code == 0 and re.search(r"Managed save:\s*yes", info, re.I):
                    status = f"{status} / managed-save"
                items.append({"id": name, "name": name, "status": status, "type": "libvirt"})
    except Exception as exc:
        log_event(f"VM_BILLING_INVENTORY error: {exc}")
    return items

def vm_billing_live_public():
    return vm_billing_touch(vm_inventory_for_billing())

def purge_stale_vm_sidecars(present_ids):
    present = {safe_vm_target(item) for item in present_ids if str(item or "").strip()}
    purged = {"guest_telemetry": 0, "guest_agents": 0}
    for path, key in [(VM_GUEST_TELEMETRY_FILE, "guest_telemetry"), (VM_GUEST_AGENTS_FILE, "guest_agents")]:
        rows = read_json(path, {})
        if not isinstance(rows, dict):
            continue
        stale = [vm_id for vm_id in rows.keys() if vm_id not in present]
        if not stale:
            continue
        for vm_id in stale:
            rows.pop(vm_id, None)
        write_json(path, rows)
        purged[key] = len(stale)
    if any(purged.values()):
        log_event(f"VM_STALE_SIDECAR_PURGE present={len(present)} telemetry={purged['guest_telemetry']} agents={purged['guest_agents']}")
    return purged

def vm_billing_touch(items, fallback_owner="admin"):
    data = vm_billing_store()
    now = datetime.datetime.now()
    now_text = now.isoformat(timespec="seconds")
    runtime = data.setdefault("runtime", {})
    enabled = bool(data.get("enabled", True))
    summaries = []
    present_ids = {str(item.get("id") or item.get("name") or "").strip() for item in (items or []) if str(item.get("id") or item.get("name") or "").strip()}
    for stale_id in sorted(set(runtime.keys()) - present_ids):
        runtime.pop(stale_id, None)
        data.setdefault("vm_owners", {}).pop(stale_id, None)
    for item in items or []:
        vm_id = str(item.get("id") or item.get("name") or "").strip()
        if not vm_id:
            continue
        owner = vm_billing_owner(data, vm_id, fallback_owner)
        wallet = vm_wallet(data, owner)
        record = runtime.setdefault(vm_id, {"owner": owner, "total_seconds": 0.0, "tokens_spent": 0.0, "last_seen": now_text, "running": False, "state_seconds": {}})
        record["owner"] = owner
        running = vm_is_running(item)
        state = vm_billing_state(item)
        storage = vm_billing_storage_gb(vm_id, data.get("storage_billing_basis", "actual"))
        rates = vm_billing_rates(data, state, storage.get("gb", 0))
        charge_rate = float(rates.get("total_rate_per_hour", 0) or 0)
        delta_seconds = 0.0
        charged = 0.0
        last = iso_dt(record.get("last_seen"))
        if last and enabled and charge_rate > 0:
            delta_seconds = max(0.0, min((now - last).total_seconds(), 3600.0))
            charged = round((delta_seconds / 3600.0) * charge_rate, 6)
            if charged > 0:
                record["total_seconds"] = float(record.get("total_seconds", 0) or 0) + delta_seconds
                state_seconds = record.setdefault("state_seconds", {})
                state_seconds[state] = float(state_seconds.get(state, 0) or 0) + delta_seconds
                record["tokens_spent"] = float(record.get("tokens_spent", 0) or 0) + charged
                wallet["balance"] = float(wallet.get("balance", 0) or 0) - charged
                wallet["spent"] = float(wallet.get("spent", 0) or 0) + charged
                wallet["updated_at"] = now_text
        if state in {"running", "paused"} and enabled and charge_rate > 0 and float(wallet.get("balance", 0) or 0) <= 0:
            last_shutdown = iso_dt(record.get("shutdown_requested_at"))
            hard_after = int(data.get("hard_kill_after_minutes", 0) or 0)
            elapsed_empty = (now - last_shutdown).total_seconds() if last_shutdown else 0
            if last_shutdown and hard_after and elapsed_empty >= hard_after * 60 and not record.get("hard_kill_at"):
                vm_type = str(item.get("type") or "").lower()
                if "libvirt" in vm_type or detect_vm_backend() == "libvirt":
                    code, output = run_vm_command(["virsh", "destroy", vm_id], timeout=30)
                elif "qemu" in vm_type or detect_vm_backend() == "proxmox":
                    code, output = run_vm_command(["qm", "stop", vm_id], timeout=30)
                else:
                    code, output = 1, "Nieznany backend VM"
                record["hard_kill_at"] = now_text
                record["hard_kill_code"] = code
                record["hard_kill_output"] = (output or "").strip()[:500]
                record_alert("NXC HARD KILL", f"{vm_id}: saldo puste przez {hard_after} min. code={code}", "critical", f"nxc-hard-kill-{vm_id}")
            elif not last_shutdown or elapsed_empty > 300:
                record["shutdown_requested_at"] = now_text
                action_result = vm_empty_balance_action(vm_id, item, data, record, owner)
                record["last_shutdown_output"] = str(action_result.get("output", ""))[:240]
                record["last_shutdown_code"] = action_result.get("code")
        record["last_seen"] = now_text
        record["running"] = running
        record["state"] = state
        record["storage_gb"] = storage.get("gb", 0)
        record["charge_rate_per_hour"] = round(charge_rate, 6)
        record["rates"] = rates
        summaries.append({
            "vm_id": vm_id,
            "owner": owner,
            "running": running,
            "state": state,
            "storage_gb": storage.get("gb", 0),
            "rate_per_hour": rates.get("base_rate_per_hour", 0),
            "charge_rate_per_hour": round(charge_rate, 6),
            "compute_rate_per_hour": rates.get("compute_rate_per_hour", 0),
            "storage_rate_per_hour": rates.get("storage_rate_per_hour", 0),
            "state_multiplier": rates.get("state_multiplier", 0),
            "delta_seconds": round(delta_seconds, 2),
            "total_seconds": round(float(record.get("total_seconds", 0) or 0), 2),
            "tokens_spent": round(float(record.get("tokens_spent", 0) or 0), 4),
            "last_charge": charged,
            "balance": round(float(wallet.get("balance", 0) or 0), 4),
        })
    data.setdefault("scheduler", {})["last_tick"] = now_text
    data.setdefault("scheduler", {})["last_status"] = "ok"
    save_vm_billing(data)
    return vm_billing_public(data, summaries)

def vm_billing_preview_public(items=None, fallback_owner="admin"):
    data = vm_billing_store()
    summaries = []
    for item in items if items is not None else vm_inventory_for_billing():
        vm_id = str(item.get("id") or item.get("name") or "").strip()
        if not vm_id:
            continue
        owner = vm_billing_owner(data, vm_id, fallback_owner)
        wallet = vm_wallet(data, owner)
        running = vm_is_running(item)
        state = vm_billing_state(item)
        storage = vm_billing_storage_gb(vm_id, data.get("storage_billing_basis", "actual"))
        rates = vm_billing_rates(data, state, storage.get("gb", 0))
        record = data.get("runtime", {}).get(vm_id, {})
        summaries.append({
            "vm_id": vm_id,
            "owner": owner,
            "running": running,
            "state": state,
            "storage_gb": storage.get("gb", 0),
            "rate_per_hour": rates.get("base_rate_per_hour", 0),
            "charge_rate_per_hour": rates.get("total_rate_per_hour", 0),
            "compute_rate_per_hour": rates.get("compute_rate_per_hour", 0),
            "storage_rate_per_hour": rates.get("storage_rate_per_hour", 0),
            "state_multiplier": rates.get("state_multiplier", 0),
            "delta_seconds": 0,
            "total_seconds": round(float(record.get("total_seconds", 0) or 0), 2),
            "tokens_spent": round(float(record.get("tokens_spent", 0) or 0), 4),
            "last_charge": 0,
            "balance": round(float(wallet.get("balance", 0) or 0), 4),
            "dry_run": True,
        })
    return vm_billing_public(data, summaries)

def vm_billing_credit(username: str, amount: float, actor="system", note=""):
    data = vm_billing_store()
    user = normalize_username(username)
    wallet = vm_wallet(data, user)
    value = round(float(amount), 4)
    wallet["balance"] = float(wallet.get("balance", 0) or 0) + value
    wallet["credited"] = float(wallet.get("credited", 0) or 0) + value
    wallet["updated_at"] = now_iso()
    data.setdefault("ledger", []).append({
        "id": uuid.uuid4().hex[:12],
        "type": "credit",
        "username": user,
        "amount": value,
        "actor": actor,
        "note": note[:180],
        "created_at": now_iso(),
    })
    save_vm_billing(data)
    return data

def vm_billing_assign_owner(vm_id: str, username: str):
    data = vm_billing_store()
    owner = normalize_username(username or "admin")
    data.setdefault("vm_owners", {})[safe_vm_target(vm_id)] = owner
    vm_wallet(data, owner)
    save_vm_billing(data)

def vm_billing_can_start(vm_id: str, username="admin"):
    data = vm_billing_store()
    owner = vm_billing_owner(data, safe_vm_target(vm_id), username)
    wallet = vm_wallet(data, owner)
    if bool(data.get("enabled", True)) and float(data.get("rate_per_hour", 0) or 0) > 0 and float(wallet.get("balance", 0) or 0) <= 0:
        save_vm_billing(data)
        raise HTTPException(status_code=402, detail=f"Brak tokenow VM dla {owner}. Doladuj portfel w VM CONTROL.")
    save_vm_billing(data)

def vm_billing_current_owner(vm_id: str):
    data = vm_billing_store()
    target = safe_vm_target(vm_id)
    owner = data.get("vm_owners", {}).get(target) or data.get("runtime", {}).get(target, {}).get("owner") or "admin"
    return normalize_username(owner)

VM_OWNER_PERMISSIONS = {
    "vm.read", "vm.metrics.read", "vm.start", "vm.stop", "vm.reboot",
    "console.open", "console.clipboard", "snapshot.read", "snapshot.create",
    "vm.config.read", "vm.media.read", "vm.doctor.read", "vm.logs.read",
}
VM_VIEWER_PERMISSIONS = {
    "vm.read", "vm.metrics.read", "console.open", "snapshot.read",
    "vm.config.read", "vm.media.read", "vm.doctor.read", "vm.logs.read",
}
VM_DANGEROUS_PERMISSIONS = {
    "vm.delete", "disk.delete", "snapshot.restore", "snapshot.delete",
    "vm.disk.attach", "vm.iso.attach", "vm.network.change", "vm.cpu.change", "vm.memory.change",
}
VM_OPERATOR_PERMISSIONS = VM_OWNER_PERMISSIONS | {
    "vm.force_stop", "snapshot.restore", "snapshot.delete",
    "vm.disk.attach", "vm.iso.attach", "vm.network.change", "vm.cpu.change", "vm.memory.change",
}
VM_ADMIN_PERMISSIONS = VM_OWNER_PERMISSIONS | VM_DANGEROUS_PERMISSIONS | {
    "vm.create", "snapshot.create", "vm.force_stop", "vm.config.read", "vm.access.manage",
}
VM_ALLOWED_PERMISSIONS = VM_ADMIN_PERMISSIONS | {"storage.read", "storage.upload"}

def normalize_permissions(values, fallback=None):
    fallback = set(fallback or [])
    perms = set()
    for value in values or []:
        perm = re.sub(r"[^a-z0-9_.:-]+", "", str(value or "").strip().lower())
        if perm:
            perms.add(perm)
    if not perms:
        perms = set(fallback)
    return sorted(perm for perm in perms if perm in VM_ALLOWED_PERMISSIONS)

def vm_access_record(data, vm_id: str, username: str):
    target = safe_vm_target(vm_id)
    user = normalize_username(username)
    return (data.get("vm_acl") or {}).get(target, {}).get(user)

def vm_access_expired(record):
    if not record:
        return False
    expires = record.get("expires_at") or ""
    if not expires:
        return False
    try:
        return datetime.datetime.fromisoformat(expires) <= datetime.datetime.now()
    except Exception:
        return False

def vm_user_running_count(data, username: str):
    user = normalize_username(username)
    count = 0
    for row in (data.get("runtime") or {}).values():
        if normalize_username(row.get("owner") or "") == user and row.get("running"):
            count += 1
    return count

def vm_effective_access(vm_id: str, user: dict):
    data = vm_billing_store()
    target = safe_vm_target(vm_id)
    username = normalize_username(user.get("username", "user"))
    role = normalize_role(user.get("role", "user"))
    owner = vm_billing_current_owner(target)
    if role == "admin":
        return {"allowed": True, "source": "admin", "owner": owner, "permissions": sorted(VM_ADMIN_PERMISSIONS), "limits": {}, "record": None}
    if role == "operator":
        limits = (data.get("user_limits") or {}).get(username, {})
        return {"allowed": True, "source": "operator", "owner": owner, "permissions": sorted(VM_OPERATOR_PERMISSIONS), "limits": limits, "record": None}
    if owner == username:
        limits = (data.get("user_limits") or {}).get(username, {})
        permissions = VM_VIEWER_PERMISSIONS if role == "viewer" else VM_OWNER_PERMISSIONS
        return {"allowed": True, "source": "owner", "owner": owner, "permissions": sorted(permissions), "limits": limits, "record": None}
    record = vm_access_record(data, target, username)
    if not record or record.get("status") != "active" or vm_access_expired(record):
        return {"allowed": False, "source": "none", "owner": owner, "permissions": [], "limits": {}, "record": record}
    permissions = set(normalize_permissions(record.get("permissions") or []))
    if role == "viewer":
        permissions &= VM_VIEWER_PERMISSIONS
    elif role == "operator":
        permissions &= VM_OPERATOR_PERMISSIONS
    return {
        "allowed": True,
        "source": "acl",
        "owner": owner,
        "permissions": sorted(permissions),
        "limits": record.get("limits") or {},
        "record": record,
    }

def vm_authorization_audit(user, operation: str, vm_id: str, decision: str, reason: str = "", request: Request = None, meta=None):
    actor = normalize_username((user or {}).get("username", "anonymous")) if user else "anonymous"
    payload = {"operation": operation, "reason": reason, **(meta or {})}
    audit_event(actor, f"vm.auth.{operation}", safe_vm_target(vm_id), decision, request, payload)
    log_event(f"VM_AUTH {decision} actor={actor} vm={safe_vm_target(vm_id)} op={operation} reason={reason}")

def enforce_vm_limits(vm_id: str, user: dict, access: dict, operation: str, request: Request = None):
    limits = access.get("limits") or {}
    if not limits or normalize_role(user.get("role")) == "admin":
        return
    data = vm_billing_store()
    username = normalize_username(user.get("username", "user"))
    if operation == "vm.start":
        max_running = int(limits.get("max_running_vms") or 0)
        if max_running and vm_user_running_count(data, username) >= max_running:
            vm_authorization_audit(user, operation, vm_id, "DENY", "running_vm_limit", request, {"limit": max_running})
            raise HTTPException(status_code=403, detail="Limit uruchomionych VM zostal przekroczony")
    if operation in {"vm.start", "vm.memory.change", "vm.cpu.change"}:
        try:
            info = parse_dominfo(vm_id)
        except Exception:
            return
        max_vcpus = int(limits.get("max_vcpus") or 0)
        max_memory = int(limits.get("max_memory_mb") or 0)
        if max_vcpus and int(info.get("vcpus") or 0) > max_vcpus:
            vm_authorization_audit(user, operation, vm_id, "DENY", "vcpus_limit", request, {"limit": max_vcpus, "actual": info.get("vcpus")})
            raise HTTPException(status_code=403, detail="VM przekracza limit vCPU tego dostepu")
        if max_memory and int(info.get("used_memory_mb") or info.get("max_memory_mb") or 0) > max_memory:
            vm_authorization_audit(user, operation, vm_id, "DENY", "memory_limit", request, {"limit": max_memory, "actual": info.get("used_memory_mb") or info.get("max_memory_mb")})
            raise HTTPException(status_code=403, detail="VM przekracza limit RAM tego dostepu")

def authorize_vm_operation(vm_id: str, user: dict, operation: str, request: Request = None):
    target = safe_vm_target(vm_id)
    if normalize_status(user.get("status", "active")) != "active":
        vm_authorization_audit(user, operation, target, "DENY", "account_not_active", request)
        raise HTTPException(status_code=403, detail="Konto nie jest aktywne")
    access = vm_effective_access(target, user)
    if not access.get("allowed") or operation not in set(access.get("permissions") or []):
        vm_authorization_audit(user, operation, target, "DENY", "permission_missing", request, {"source": access.get("source"), "owner": access.get("owner")})
        raise HTTPException(status_code=404, detail="Zasob niedostepny")
    enforce_vm_limits(target, user, access, operation, request)
    vm_authorization_audit(user, operation, target, "ALLOW", "", request, {"source": access.get("source"), "owner": access.get("owner")})
    return access

def vm_item_accessible_for_user(item, user: dict):
    if not isinstance(user, dict) or normalize_role(user.get("role")) in {"admin", "operator"}:
        return True
    vm_id = str(item.get("id") or item.get("name") or "").strip()
    if not vm_id:
        return False
    access = vm_effective_access(vm_id, user)
    return bool(access.get("allowed") and "vm.read" in set(access.get("permissions") or []))

def filter_vm_items_for_user(items, user: dict):
    if not isinstance(user, dict) or normalize_role(user.get("role")) in {"admin", "operator"}:
        return items or []
    filtered = []
    for item in items or []:
        if vm_item_accessible_for_user(item, user):
            access = vm_effective_access(str(item.get("id") or item.get("name") or ""), user)
            item = dict(item)
            item["access_source"] = access.get("source")
            item["owner"] = access.get("owner")
            filtered.append(item)
    return filtered

def scope_vm_billing_for_user(billing: dict, user: dict, visible_items=None):
    if not isinstance(user, dict) or normalize_role(user.get("role")) in {"admin", "operator"}:
        return billing
    username = normalize_username(user.get("username", "user"))
    keep_ids = {
        str(item.get("id") or item.get("name") or "").strip()
        for item in (visible_items or [])
        if str(item.get("id") or item.get("name") or "").strip()
    }
    scoped = dict(billing or {})
    wallets = billing.get("wallets") or {}
    scoped["wallets"] = {
        username: wallets.get(username, {"balance": 0, "credited": 0, "spent": 0, "updated_at": ""})
    }
    scoped["runtime"] = {
        vm_id: row for vm_id, row in (billing.get("runtime") or {}).items()
        if vm_id in keep_ids or normalize_username(row.get("owner") or "admin") == username
    }
    scoped["active"] = [
        row for row in (billing.get("active") or [])
        if row.get("vm_id") in keep_ids or normalize_username(row.get("owner") or "admin") == username
    ]
    scoped["forecast"] = [
        row for row in (billing.get("forecast") or [])
        if normalize_username(row.get("owner") or "admin") == username
    ]
    scoped["ledger"] = [
        row for row in (billing.get("ledger") or [])
        if normalize_username(row.get("username") or username) == username or row.get("vm_id") in keep_ids
    ][-80:]
    return scoped

def require_destructive_confirmation(user: dict, action: str, target: str, confirm: str, request: Request = None, reason: str = ""):
    target = safe_vm_target(target)
    clean = (confirm or "").strip()
    allowed = {target, f"{action}:{target}", "CONFIRM-" + target}
    if clean not in allowed:
        actor = (user or {}).get("username", "anonymous")
        audit_event(actor, f"confirm.{action}", target, "DENY", request, {"reason": reason[:180], "required": target})
        raise HTTPException(status_code=409, detail={
            "message": "Ta operacja jest destrukcyjna i wymaga potwierdzenia nazwa VM.",
            "action": action,
            "target": target,
            "confirm_required": target,
        })
    audit_event((user or {}).get("username", "anonymous"), f"confirm.{action}", target, "OK", request, {"reason": reason[:180]})
    return True

def assert_vm_owner_or_admin(vm_id: str, user: dict):
    target = safe_vm_target(vm_id)
    access = authorize_vm_operation(target, user, "vm.read")
    return access.get("owner")

def grant_vm_access(data: VMAccessGrantRequest, admin: dict, request: Request = None):
    store = vm_billing_store()
    username = normalize_username(data.username)
    target = safe_vm_target(data.vm_id)
    if username not in load_users():
        raise HTTPException(status_code=404, detail="Nie znaleziono uzytkownika")
    code, output = run_vm_command(["virsh", "dominfo", target], timeout=8)
    if detect_vm_backend() == "libvirt" and code != 0:
        raise HTTPException(status_code=404, detail="Nie znaleziono VM")
    permissions = normalize_permissions(data.permissions, fallback=VM_OWNER_PERMISSIONS)
    limits = {}
    if data.max_vcpus:
        limits["max_vcpus"] = int(data.max_vcpus)
    if data.max_memory_mb:
        limits["max_memory_mb"] = int(data.max_memory_mb)
    if data.max_running_vms:
        limits["max_running_vms"] = int(data.max_running_vms)
    expires_at = ""
    if data.expires_minutes:
        expires_at = (datetime.datetime.now() + datetime.timedelta(minutes=int(data.expires_minutes))).isoformat(timespec="seconds")
    record = {
        "username": username,
        "vm_id": target,
        "permissions": permissions,
        "limits": limits,
        "status": "active",
        "expires_at": expires_at,
        "note": data.note[:240],
        "granted_by": admin.get("username", "admin"),
        "granted_at": now_iso(),
    }
    store.setdefault("vm_acl", {}).setdefault(target, {})[username] = record
    vm_wallet(store, username)
    store.setdefault("ledger", []).append({"id": uuid.uuid4().hex[:12], "type": "access_grant", "username": username, "vm_id": target, "actor": admin.get("username", "admin"), "created_at": now_iso(), "permissions": permissions, "limits": limits})
    save_vm_billing(store)
    audit_event(admin.get("username"), "vm.access.grant", target, "OK", request, {"username": username, "permissions": permissions, "limits": limits, "expires_at": expires_at})
    return record

def revoke_vm_access(data: VMAccessRevokeRequest, admin: dict, request: Request = None):
    store = vm_billing_store()
    username = normalize_username(data.username)
    target = safe_vm_target(data.vm_id)
    record = store.setdefault("vm_acl", {}).setdefault(target, {}).get(username)
    if not record:
        raise HTTPException(status_code=404, detail="Nie znaleziono przydzialu dostepu")
    record["status"] = "revoked"
    record["revoked_at"] = now_iso()
    record["revoked_by"] = admin.get("username", "admin")
    record["reason"] = data.reason[:240]
    if data.revoke_sessions:
        for ticket, row in list(VNC_SESSIONS.items()):
            if row.get("username") == username and row.get("vm_id") == target:
                VNC_SESSIONS.pop(ticket, None)
    store.setdefault("ledger", []).append({"id": uuid.uuid4().hex[:12], "type": "access_revoke", "username": username, "vm_id": target, "actor": admin.get("username", "admin"), "created_at": now_iso(), "reason": data.reason[:180]})
    save_vm_billing(store)
    audit_event(admin.get("username"), "vm.access.revoke", target, "OK", request, {"username": username, "reason": data.reason, "revoke_sessions": data.revoke_sessions})
    return record

def vm_status_flags(status: str):
    text = str(status or "").strip().lower()
    running = any(token in text for token in ("running", "uruch"))
    paused = any(token in text for token in ("paused", "pmsuspended", "suspended"))
    crashed = any(token in text for token in ("crash", "error", "panicked", "blocked"))
    return {
        "running": running,
        "paused": paused,
        "error": crashed,
        "normalized_status": "running" if running else "paused" if paused else "error" if crashed else "stopped",
    }

def vm_media_inventory(name: str):
    target = safe_vm_target(name)
    result = {"disks": [], "cdroms": [], "iso_loaded": []}
    code, output = run_vm_command(["virsh", "domblklist", "--details", target], timeout=6)
    if code != 0:
        result["error"] = output.strip()[:300]
        return result
    for line in output.splitlines():
        raw = line.strip()
        if not raw or raw.lower().startswith("type ") or raw.startswith("-"):
            continue
        parts = raw.split(None, 3)
        if len(parts) < 4:
            continue
        disk_type, device, target_dev, source = parts
        source = "" if source.strip() in {"", "-"} else source.strip()
        row = {
            "type": disk_type,
            "device": device,
            "target": target_dev,
            "source": source,
            "name": Path(source).name if source else "",
        }
        if device.lower() == "cdrom":
            result["cdroms"].append(row)
            if source:
                result["iso_loaded"].append(row["name"] or source)
        elif device.lower() == "disk":
            result["disks"].append(row)
    return result

def vm_ip_inventory(name: str):
    target = safe_vm_target(name)
    ips = []
    errors = []
    for source in ("agent", "lease"):
        code, output = run_vm_command(["virsh", "domifaddr", target, "--source", source], timeout=5)
        if code != 0:
            errors.append(output.strip()[:160])
            continue
        for line in output.splitlines():
            raw = line.strip()
            if not raw or raw.lower().startswith("name ") or raw.startswith("-"):
                continue
            parts = raw.split()
            if len(parts) >= 4 and parts[-2].lower().startswith("ipv"):
                ip = parts[-1].split("/", 1)[0].strip()
                if ip and ip not in ips:
                    ips.append(ip)
        if ips:
            break
    payload = {"ips": ips[:12], "source": "libvirt-agent-or-lease"}
    if not ips and errors:
        payload["error"] = errors[-1]
    return payload

def vm_vnc_inventory(name: str):
    target = safe_vm_target(name)
    payload = {"status": "missing", "local": False, "host": "", "port": None}
    for command in (["virsh", "domdisplay", "--include-password", target], ["virsh", "vncdisplay", target]):
        code, output = run_vm_command(command, timeout=5)
        if code != 0:
            continue
        for line in output.splitlines():
            parsed = parse_vnc_endpoint(line.strip())
            if not parsed:
                continue
            host, port = parsed
            payload.update({
                "status": "ready" if is_local_vnc_host(host) else "external-blocked",
                "local": is_local_vnc_host(host),
                "host": "127.0.0.1" if is_local_vnc_host(host) else host,
                "port": int(port),
            })
            return payload
    return payload

def enrich_vm_item(item):
    pid = item.get("pid") or find_qemu_pid(item.get("id") or item.get("name"))
    item.update(vm_process_telemetry(pid))
    guest = latest_guest_telemetry(item.get("id") or item.get("name") or "")
    if guest:
        item["guest_telemetry"] = guest
    item.update(vm_status_flags(item.get("status")))
    if item.get("type") == "libvirt":
        target = item.get("id") or item.get("name")
        try:
            item["media"] = vm_media_inventory(target)
            item["cdroms"] = item["media"].get("cdroms", [])
            item["disks"] = item["media"].get("disks", [])
            item["iso_loaded"] = item["media"].get("iso_loaded", [])
        except Exception as exc:
            item["media"] = {"error": str(exc)[:300], "cdroms": [], "disks": [], "iso_loaded": []}
            item["cdroms"] = []
            item["disks"] = []
            item["iso_loaded"] = []
        try:
            item["network"] = vm_ip_inventory(target)
            item["ips"] = item["network"].get("ips", [])
        except Exception as exc:
            item["network"] = {"ips": [], "error": str(exc)[:300]}
            item["ips"] = []
        try:
            item["vnc"] = vm_vnc_inventory(target)
        except Exception as exc:
            item["vnc"] = {"status": "error", "local": False, "error": str(exc)[:300]}
    item["console_hint"] = "VNC lokalny przez NEXUS websocket proxy"
    return item

def vm_vcpu_counts(name: str):
    target = safe_vm_target(name)
    code, output = run_vm_command(["virsh", "vcpucount", target], timeout=8)
    rows = {}
    if code != 0:
        return rows
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] in {"maximum", "current"}:
            try:
                rows[f"{parts[0]}_{parts[1]}"] = int(parts[2])
            except Exception:
                pass
    return rows

def parse_dominfo(name: str):
    code, output = run_vm_command(["virsh", "dominfo", safe_vm_target(name)], timeout=8)
    if code != 0:
        raise HTTPException(status_code=404, detail=output.strip() or "Nie znaleziono VM")
    info = {"vm_id": name}
    for row in output.splitlines():
        if ":" not in row:
            continue
        key, value = row.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "state":
            info["state"] = value
        elif key == "max memory":
            info["max_memory"] = value
            match = re.search(r"(\d+)", value)
            if match:
                info["max_memory_mb"] = round(int(match.group(1)) / 1024)
        elif key == "used memory":
            info["used_memory"] = value
            match = re.search(r"(\d+)", value)
            if match:
                info["used_memory_mb"] = round(int(match.group(1)) / 1024)
        elif key == "cpu(s)":
            try:
                info["vcpus"] = int(value)
            except Exception:
                info["vcpus"] = value
        elif key == "persistent":
            info["persistent"] = value
    info["vcpu_counts"] = vm_vcpu_counts(name)
    return info

def memory_unit_to_kib(value: str, unit: str = "KiB"):
    number = int(float(value or 0))
    unit = (unit or "KiB").lower()
    if unit in {"b", "bytes"}:
        return max(1, round(number / 1024))
    if unit in {"kb", "k", "kib"}:
        return number
    if unit in {"mb", "m", "mib"}:
        return number * 1024
    if unit in {"gb", "g", "gib"}:
        return number * 1024 * 1024
    if unit in {"tb", "t", "tib"}:
        return number * 1024 * 1024 * 1024
    return number

def kib_to_mb(value):
    try:
        return round(int(value or 0) / 1024)
    except Exception:
        return 0

def vm_memory_xml_state(vm_id: str, inactive: bool = True):
    root, _ = vm_dumpxml_root(vm_id, inactive=inactive)
    memory = root.find("memory")
    current = root.find("currentMemory")
    max_mem = root.find("maxMemory")
    memory_kib = memory_unit_to_kib(memory.text if memory is not None else "0", memory.attrib.get("unit", "KiB") if memory is not None else "KiB")
    current_kib = memory_unit_to_kib(current.text if current is not None else str(memory_kib), current.attrib.get("unit", "KiB") if current is not None else "KiB")
    max_kib = memory_unit_to_kib(max_mem.text if max_mem is not None else str(memory_kib), max_mem.attrib.get("unit", "KiB") if max_mem is not None else "KiB")
    return {
        "memory_kib": memory_kib,
        "current_kib": current_kib,
        "max_memory_kib": max(max_kib, memory_kib),
        "memory_mb": kib_to_mb(memory_kib),
        "current_memory_mb": kib_to_mb(current_kib),
        "max_memory_mb": kib_to_mb(max(max_kib, memory_kib)),
        "inactive": bool(inactive),
    }

def apply_vm_memory_thin_config(vm_id: str, target_mb: int, startup_mb: int):
    target = safe_vm_target(vm_id)
    target_mb = max(128, min(int(target_mb or 0), 262144))
    startup_mb = max(128, min(int(startup_mb or target_mb), target_mb))
    before = vm_memory_xml_state(target, inactive=True)
    attempts = []

    commands = [
        ["virsh", "setmaxmem", target, f"{target_mb}M", "--config"],
        ["virsh", "setmem", target, f"{startup_mb}M", "--config"],
    ]
    command_failed = False
    for command in commands:
        code, output = run_vm_command(command, timeout=30)
        attempts.append({
            "stage": "persistent",
            "mode": command[1],
            "command": command,
            "code": code,
            "ok": code == 0,
            "output": output.strip(),
        })
        if code != 0:
            command_failed = True
            break

    define_result = None
    if command_failed:
        root, _ = vm_dumpxml_root(target, inactive=True)
        set_text_node(root, "memory", str(target_mb * 1024), "KiB")
        set_text_node(root, "currentMemory", str(startup_mb * 1024), "KiB")
        define_result = define_domain_xml_transaction(target, root, "ram-thin")
        attempts.append({
            "stage": "persistent",
            "mode": "xml-rollback-transaction",
            "code": 0,
            "ok": True,
            "output": "Persistent RAM zapisany przez XML fallback.",
        })

    after = vm_memory_xml_state(target, inactive=True)
    persistent_ok = (
        int(after.get("memory_mb") or 0) >= target_mb
        and memory_value_matches_mb(after.get("current_memory_mb"), startup_mb)
    )
    if not persistent_ok:
        raise HTTPException(status_code=500, detail={
            "message": "RAM thin provisioning nie zapisal sie w konfiguracji persistent.",
            "vm_id": target,
            "target_memory_mb": target_mb,
            "startup_memory_mb": startup_mb,
            "before": before,
            "after": after,
            "attempts": attempts,
        })
    return {
        "status": "thin" if startup_mb < target_mb else "full",
        "vm_id": target,
        "target_memory_mb": target_mb,
        "startup_memory_mb": startup_mb,
        "persistent": True,
        "before": before,
        "after": after,
        "attempts": attempts,
        "define": define_result,
    }

def memory_value_matches_mb(value_mb, wanted_mb, tolerance_mb=1):
    try:
        return abs(int(value_mb or 0) - int(wanted_mb or 0)) <= tolerance_mb
    except Exception:
        return False

def vm_ram_update_cascade(vm_id: str, memory_mb: int, live: bool = True, config: bool = True):
    target = safe_vm_target(vm_id)
    memory_mb = max(128, min(int(memory_mb), 262144))
    before = parse_dominfo(target)
    before_config = vm_memory_xml_state(target, inactive=True)
    running = "running" in str(before.get("state", "")).lower()
    attempts = []
    live_ok = False
    persistent_ok = False

    if live and running:
        command = ["virsh", "setmem", target, f"{memory_mb}M", "--live"]
        code, output = run_vm_command(command, timeout=30)
        attempts.append({"stage": "live", "mode": "setmem", "command": command, "code": code, "ok": code == 0, "output": output.strip()})
        live_ok = code == 0
    elif live:
        attempts.append({"stage": "live", "mode": "skip", "ok": False, "code": 0, "output": "VM nie dziala; RAM live zostanie zastosowany po starcie z konfiguracji persistent."})

    if config:
        current_cfg_mb = int(before_config.get("current_memory_mb") or before.get("used_memory_mb") or memory_mb)
        max_cfg_mb = int(before_config.get("memory_mb") or before.get("max_memory_mb") or memory_mb)
        if memory_mb > max_cfg_mb:
            commands = [
                ["virsh", "setmaxmem", target, f"{memory_mb}M", "--config"],
                ["virsh", "setmem", target, f"{memory_mb}M", "--config"],
            ]
        else:
            commands = [
                ["virsh", "setmem", target, f"{memory_mb}M", "--config"],
                ["virsh", "setmaxmem", target, f"{memory_mb}M", "--config"],
            ]
        for command in commands:
            code, output = run_vm_command(command, timeout=30)
            attempts.append({"stage": "persistent", "mode": command[1], "command": command, "code": code, "ok": code == 0, "output": output.strip()})
            if code != 0:
                break
        try:
            after_config_probe = vm_memory_xml_state(target, inactive=True)
            persistent_ok = memory_value_matches_mb(after_config_probe.get("current_memory_mb"), memory_mb) and after_config_probe.get("memory_mb", 0) >= memory_mb
        except Exception as exc:
            attempts.append({"stage": "persistent", "mode": "verify", "ok": False, "code": 1, "output": str(exc)})
            persistent_ok = False
    else:
        persistent_ok = False

    after = parse_dominfo(target)
    after_config = vm_memory_xml_state(target, inactive=True)
    if live and running:
        live_ok = live_ok and memory_value_matches_mb(after.get("used_memory_mb"), memory_mb)
    if config:
        persistent_ok = persistent_ok and memory_value_matches_mb(after_config.get("current_memory_mb"), memory_mb) and after_config.get("memory_mb", 0) >= memory_mb

    if config and not persistent_ok:
        raise HTTPException(status_code=500, detail={
            "message": "RAM nie zapisal sie w konfiguracji persistent. Nie udaje sukcesu, bo po restarcie VM wrocilaby stara wartosc.",
            "vm_id": target,
            "target_memory_mb": memory_mb,
            "live": live_ok,
            "persistent": False,
            "attempts": attempts,
            "before": before,
            "before_config": before_config,
            "after": after,
            "after_config": after_config,
        })

    if live and running and live_ok:
        status = "success"
        message = "RAM zmieniony w locie i zapisany persistent." if config else "RAM zmieniony w locie."
    elif live and running and not live_ok and not config:
        status = "warning"
        message = "Ballooning live odrzucony. Nie zapisano persistent, bo config=false."
    elif config and persistent_ok:
        status = "warning" if live and running else "pending_restart"
        if live and running:
            message = "Ballooning live odrzucony albo niedostepny. RAM zapisany w konfiguracji persistent; zrestartuj Kapsule, aby zastosowac."
        elif running:
            message = "RAM zapisany w konfiguracji persistent; live=false, wiec zrestartuj Kapsule, aby zastosowac."
        else:
            message = "RAM zapisany w konfiguracji persistent; wejdzie przy kolejnym starcie Kapsuly."
    else:
        status = "noop"
        message = "Nie wykonano zapisu persistent; live nie bylo wymagane albo VM jest wylaczona."

    warnings = []
    if live and running and not live_ok:
        failed = next((row for row in attempts if row.get("stage") == "live" and not row.get("ok")), {})
        warnings.append(failed.get("output") or "Zmiana RAM live nie powiodla sie; persistent zapisany po restarcie.")
    return {
        "status": status,
        "vm_id": target,
        "target_memory_mb": memory_mb,
        "target_memory_kib": memory_mb * 1024,
        "live": bool(live_ok),
        "persistent": bool(persistent_ok),
        "requires_restart": bool(config and persistent_ok and (not live_ok) and running),
        "message": message,
        "warnings": warnings,
        "attempts": attempts,
        "before": before,
        "before_config": before_config,
        "after": after,
        "after_config": after_config,
    }

def safe_snapshot_name(name: str):
    raw = (name or "").strip() or f"snap-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw).strip(".-")
    if not clean:
        clean = f"snap-{uuid.uuid4().hex[:8]}"
    if clean.startswith("-"):
        clean = "snap-" + clean.lstrip("-")
    return clean[:80]

def safe_firewall_proto(proto: str):
    proto = (proto or "tcp").lower().strip()
    if proto not in {"tcp", "udp"}:
        raise HTTPException(status_code=400, detail="Port forwarding wspiera tcp albo udp")
    return proto

def parse_snapshot_info(output: str):
    item = {}
    for row in output.splitlines():
        if ":" not in row:
            continue
        key, value = row.split(":", 1)
        item[key.strip().lower().replace(" ", "_")] = value.strip()
    return item

def vm_log_file(vm_id: str):
    name = safe_vm_target(vm_id)
    return (Path("/var/log/libvirt/qemu") / f"{Path(name).name}.log").resolve()

def tail_text(path: Path, lines: int = 50):
    lines = max(1, min(int(lines or 50), 500))
    if not path.exists():
        raise HTTPException(status_code=404, detail="Brak pliku logow dla tej VM")
    try:
        return "\n".join(path.read_text(encoding="utf-8", errors="ignore").splitlines()[-lines:])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Nie udalo sie odczytac logow: {exc}")

def detect_vm_guest_ip(vm_id: str):
    target = safe_vm_target(vm_id)
    candidates = []
    for source in ["agent", "lease"]:
        code, output = run_vm_command(["virsh", "domifaddr", target, "--source", source], timeout=8)
        if code == 0:
            candidates.append(output)
    blob = "\n".join(candidates)
    for match in re.finditer(r"\b(\d{1,3}(?:\.\d{1,3}){3})/\d+\b", blob):
        ip = match.group(1)
        if not ip.startswith("127."):
            return ip
    return ""

def vm_storage_paths(vm_id: str):
    target = safe_vm_target(vm_id)
    paths = []
    code, output = run_vm_command(["virsh", "domblklist", target, "--details"], timeout=10)
    if code != 0:
        return paths
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 4 or parts[0].lower() in {"type", "-"}:
            continue
        device = parts[1].lower()
        source = parts[-1]
        if device != "disk" or source in {"-", ""}:
            continue
        try:
            path = Path(source).resolve()
            if path.exists() and path.is_file() and path.suffix.lower() in {".qcow2", ".raw", ".img"}:
                if path == LIBVIRT_IMAGE_DIR.resolve() or LIBVIRT_IMAGE_DIR.resolve() in path.parents:
                    paths.append(path)
        except Exception:
            continue
    return paths

def iptables_path():
    return shutil.which("iptables") or ""

def iptables_rule_args(item):
    proto = safe_firewall_proto(item.get("proto", "tcp"))
    host_port = str(int(item["host_port"]))
    vm_port = str(int(item["vm_port"]))
    guest_ip = item["guest_ip"]
    mark = item["comment"]
    return [
        ("nat", "PREROUTING", ["-p", proto, "--dport", host_port, "-m", "comment", "--comment", mark, "-j", "DNAT", "--to-destination", f"{guest_ip}:{vm_port}"]),
        ("filter", "FORWARD", ["-p", proto, "-d", guest_ip, "--dport", vm_port, "-m", "comment", "--comment", mark, "-j", "ACCEPT"]),
        ("nat", "POSTROUTING", ["-p", proto, "-d", guest_ip, "--dport", vm_port, "-m", "comment", "--comment", mark, "-j", "MASQUERADE"]),
    ]

def iptables_run(args, timeout=10):
    tool = iptables_path()
    if not tool:
        raise HTTPException(status_code=500, detail="Brak iptables na serwerze")
    return run_vm_command([tool] + args, timeout=timeout)

def iptables_ensure(table: str, chain: str, rule: list):
    base = ["-t", table] if table != "filter" else []
    code, _ = iptables_run(base + ["-C", chain] + rule, timeout=8)
    if code == 0:
        return
    code, output = iptables_run(base + ["-A", chain] + rule, timeout=8)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie dodac reguly iptables")

def iptables_delete(table: str, chain: str, rule: list):
    base = ["-t", table] if table != "filter" else []
    for _ in range(3):
        code, _ = iptables_run(base + ["-C", chain] + rule, timeout=8)
        if code != 0:
            return
        iptables_run(base + ["-D", chain] + rule, timeout=8)

def apply_port_forward_rule(item):
    run_vm_command(["sysctl", "-w", "net.ipv4.ip_forward=1"], timeout=8)
    for table, chain, rule in iptables_rule_args(item):
        iptables_ensure(table, chain, rule)

def delete_port_forward_rule(item):
    for table, chain, rule in iptables_rule_args(item):
        iptables_delete(table, chain, rule)

def send_webhook_event(event: str, payload: dict):
    rows = read_json(WEBHOOKS_FILE, [])
    sent = 0
    for row in rows:
        if not row.get("enabled", True):
            continue
        events = row.get("events") or []
        if events and event not in events and "*" not in events:
            continue
        url = (row.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            continue
        try:
            body = json.dumps({"event": event, "payload": payload, "created_at": now_iso()}, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "NEXUS-WEBHOOK/1.0"}, method="POST")
            urllib.request.urlopen(req, timeout=6).read()
            row["last_status"] = "ok"
            row["last_sent_at"] = now_iso()
            sent += 1
        except Exception as exc:
            row["last_status"] = f"error: {str(exc)[:180]}"
            row["last_error_at"] = now_iso()
    if rows:
        write_json(WEBHOOKS_FILE, rows)
    return sent

def record_alert(title: str, body: str, level: str = "warn", key: str = ""):
    alerts = read_json(ALERTS_FILE, [])
    now = now_iso()
    if key:
        for alert in alerts[:20]:
            if alert.get("key") == key:
                try:
                    created = datetime.datetime.fromisoformat(alert.get("created_at", now))
                    if (datetime.datetime.now() - created).total_seconds() < 600:
                        return alert
                except Exception:
                    pass
    item = {
        "id": uuid.uuid4().hex[:12],
        "key": key or uuid.uuid4().hex[:8],
        "title": title[:120],
        "body": body[:500],
        "level": level if level in {"info", "warn", "critical"} else "warn",
        "created_by": "vm-monitor",
        "created_at": now,
    }
    alerts.insert(0, item)
    write_json(ALERTS_FILE, alerts[:200])
    config = read_json(VM_ALERTS_CONFIG_FILE, {})
    webhook = (config.get("webhook_url") or "").strip()
    if webhook.startswith(("http://", "https://")):
        try:
            payload = json.dumps({"text": f"[{item['level'].upper()}] {item['title']}\n{item['body']}"}).encode("utf-8")
            req = urllib.request.Request(webhook, data=payload, headers={"Content-Type": "application/json", "User-Agent": "NEXUS-VM-MONITOR/1.0"})
            urllib.request.urlopen(req, timeout=5).read()
        except Exception as exc:
            log_event(f"VM_ALERT webhook error: {exc}")
    log_event(f"VM_ALERT {item['level'].upper()}: {item['title']}")
    try:
        send_webhook_event("alert", item)
    except Exception as exc:
        log_event(f"WEBHOOK alert error: {exc}")
    return item

def external_base_url(request: Request):
    scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("host") or request.url.netloc
    return f"{scheme}://{host}".rstrip("/")

def guest_agent_token(vm_id: str):
    target = safe_vm_target(vm_id)
    agents = read_json(VM_GUEST_AGENTS_FILE, {})
    row = agents.get(target)
    if not row:
        row = {"token": secrets.token_urlsafe(32), "created_at": now_iso()}
        agents[target] = row
        write_json(VM_GUEST_AGENTS_FILE, agents)
    return row["token"]

def linux_guest_agent_script(vm_id: str, token_value: str, endpoint: str):
    vm_json = json.dumps(vm_id)
    token_json = json.dumps(token_value)
    endpoint_json = json.dumps(endpoint)
    return f"""sudo tee /usr/local/bin/nexus-vm-agent.py >/dev/null <<'PY'
import json, os, platform, shutil, socket, time, urllib.request
VM_ID={vm_json}
TOKEN={token_json}
URL={endpoint_json}

def read_cpu():
    vals=list(map(int, open('/proc/stat').readline().split()[1:]))
    idle=vals[3]+vals[4]
    total=sum(vals)
    return idle,total

def mem():
    rows={{}}
    for line in open('/proc/meminfo'):
        k,v=line.split(':',1)
        rows[k]=int(v.strip().split()[0])
    total=rows.get('MemTotal',0)
    avail=rows.get('MemAvailable',0)
    used=max(0,total-avail)
    pct=(used/total*100) if total else 0
    return used/1024,total/1024,pct

def ips():
    result=[]
    try:
        name=socket.gethostname()
        for item in socket.getaddrinfo(name,None):
            ip=item[4][0]
            if ':' not in ip and not ip.startswith('127.') and ip not in result:
                result.append(ip)
    except Exception:
        pass
    return result

idle,total=read_cpu()
while True:
    time.sleep(5)
    idle2,total2=read_cpu()
    cpu=0 if total2==total else max(0,min(100,100*(1-(idle2-idle)/(total2-total))))
    idle,total=idle2,total2
    used,total_mem,mem_pct=mem()
    disk=shutil.disk_usage('/')
    payload={{
        'vm_id':VM_ID,'token':TOKEN,'hostname':socket.gethostname(),'os':platform.platform(),
        'cpu_percent':round(cpu,1),'memory_percent':round(mem_pct,1),
        'memory_used_mb':round(used,1),'memory_total_mb':round(total_mem,1),
        'disk_percent':round(((disk.total-disk.free)/disk.total)*100,1) if disk.total else 0,
        'disk_used_gb':round((disk.total-disk.free)/1024/1024/1024,2),
        'disk_total_gb':round(disk.total/1024/1024/1024,2),
        'uptime_seconds':float(open('/proc/uptime').read().split()[0]) if os.path.exists('/proc/uptime') else 0,
        'ips':ips()
    }}
    try:
        req=urllib.request.Request(URL, data=json.dumps(payload).encode(), headers={{'Content-Type':'application/json','User-Agent':'NEXUS-VM-GUEST/1.0'}})
        urllib.request.urlopen(req, timeout=4).read()
    except Exception:
        pass
PY
sudo tee /etc/systemd/system/nexus-vm-agent.service >/dev/null <<'SERVICE'
[Unit]
Description=NEXUS VM Guest Telemetry Agent
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 /usr/local/bin/nexus-vm-agent.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE
sudo systemctl daemon-reload && sudo systemctl enable --now nexus-vm-agent.service
"""

def windows_guest_agent_script(vm_id: str, token_value: str, endpoint: str):
    vm_ps = vm_id.replace("'", "''")
    token_ps = token_value.replace("'", "''")
    endpoint_ps = endpoint.replace("'", "''")
    return f"""$VmId='{vm_ps}'
$Token='{token_ps}'
$Url='{endpoint_ps}'
$Script=@"
`$VmId='$VmId'
`$Token='$Token'
`$Url='$Url'
while (`$true) {{
  try {{
    `$cpu=(Get-Counter '\\Processor(_Total)\\% Processor Time').CounterSamples.CookedValue
    `$os=Get-CimInstance Win32_OperatingSystem
    `$disk=Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
    `$ips=(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {{ `$_.IPAddress -notlike '127.*' }} | Select-Object -ExpandProperty IPAddress)
    `$total=[math]::Round(`$os.TotalVisibleMemorySize/1024,1)
    `$free=[math]::Round(`$os.FreePhysicalMemory/1024,1)
    `$used=[math]::Round(`$total-`$free,1)
    `$payload=@{{
      vm_id=`$VmId; token=`$Token; hostname=`$env:COMPUTERNAME; os=`$os.Caption;
      cpu_percent=[math]::Round(`$cpu,1); memory_percent=[math]::Round((`$used/`$total)*100,1);
      memory_used_mb=`$used; memory_total_mb=`$total;
      disk_percent=[math]::Round(((`$disk.Size-`$disk.FreeSpace)/`$disk.Size)*100,1);
      disk_used_gb=[math]::Round((`$disk.Size-`$disk.FreeSpace)/1GB,2); disk_total_gb=[math]::Round(`$disk.Size/1GB,2);
      uptime_seconds=[int]((Get-Date)-`$os.LastBootUpTime).TotalSeconds; ips=`$ips
    }} | ConvertTo-Json -Depth 4
    Invoke-RestMethod -Uri `$Url -Method Post -Body `$payload -ContentType 'application/json' -TimeoutSec 4 | Out-Null
  }} catch {{}}
  Start-Sleep -Seconds 5
}}
"@
New-Item -ItemType Directory -Force C:\\Nexus | Out-Null
Set-Content -Path C:\\Nexus\\nexus-vm-agent.ps1 -Value $Script -Encoding UTF8
$Action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-ExecutionPolicy Bypass -WindowStyle Hidden -File C:\\Nexus\\nexus-vm-agent.ps1'
$Trigger=New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName 'NEXUS VM Guest Telemetry Agent' -Action $Action -Trigger $Trigger -RunLevel Highest -Force
Start-Process powershell.exe -WindowStyle Hidden -ArgumentList '-ExecutionPolicy Bypass -File C:\\Nexus\\nexus-vm-agent.ps1'
"""

def detect_vnc_endpoint(backend: str, target: str):
    backend = detect_vm_backend() if backend == "auto" else backend
    target = safe_vm_target(target)
    candidates = []

    if backend == "libvirt":
        for command in (["virsh", "domdisplay", "--include-password", target], ["virsh", "vncdisplay", target]):
            code, output = run_vm_command(command, timeout=8)
            if code == 0:
                candidates.extend([line.strip() for line in output.splitlines() if line.strip()])
    elif backend == "proxmox":
        if not target.isdigit():
            raise HTTPException(status_code=400, detail="Proxmox wymaga numerycznego VMID")
        code, output = run_vm_command(["qm", "config", target], timeout=8)
        if code == 0:
            for line in output.splitlines():
                if line.lower().startswith("args:"):
                    match = re.search(r"(?:^|\s)-vnc\s+([^,\s]+)", line)
                    if match:
                        candidates.append(match.group(1))
                if line.lower().startswith("vnc:"):
                    candidates.append(line.split(":", 1)[1].strip())

    for candidate in candidates:
        parsed = parse_vnc_endpoint(candidate)
        if not parsed:
            continue
        host, port = parsed
        if not is_local_vnc_host(host):
            raise HTTPException(status_code=403, detail="VNC musi nasluchiwac lokalnie na VPS (127.0.0.1)")
        return {"host": "127.0.0.1", "port": int(port), "backend": backend, "vm_id": target}

    if backend == "libvirt":
        repaired, repair_output = ensure_libvirt_vnc_graphics(target)
        if repaired:
            repaired_candidates = []
            for command in (["virsh", "domdisplay", "--include-password", target], ["virsh", "vncdisplay", target]):
                code, output = run_vm_command(command, timeout=8)
                if code == 0:
                    repaired_candidates.extend([line.strip() for line in output.splitlines() if line.strip()])
            for candidate in repaired_candidates:
                parsed = parse_vnc_endpoint(candidate)
                if not parsed:
                    continue
                host, port = parsed
                if not is_local_vnc_host(host):
                    raise HTTPException(status_code=403, detail="VNC musi nasluchiwac lokalnie na VPS (127.0.0.1)")
                return {"host": "127.0.0.1", "port": int(port), "backend": backend, "vm_id": target}
            raise HTTPException(status_code=409, detail="VNC zostal dodany do konfiguracji VM, ale port nie jest jeszcze aktywny. Uruchom albo zrestartuj VM i kliknij PODGLAD ponownie.")
        raise HTTPException(status_code=404, detail=f"Nie znaleziono lokalnego VNC i auto-naprawa nie powiodla sie: {repair_output.strip()[:300]}")

    raise HTTPException(status_code=404, detail="Nie znaleziono lokalnego VNC dla tej VM. Ustaw graphics type='vnc' listen='127.0.0.1' albo args: -vnc 127.0.0.1:DISPLAY")

def cleanup_vnc_sessions():
    now = datetime.datetime.now().timestamp()
    for ticket, row in list(VNC_SESSIONS.items()):
        if float(row.get("expires_ts", 0) or 0) < now:
            VNC_SESSIONS.pop(ticket, None)

def create_vnc_session(vm_id: str, backend: str, user: dict):
    cleanup_vnc_sessions()
    ticket = secrets.token_urlsafe(32)
    expires = datetime.datetime.now() + datetime.timedelta(seconds=VNC_SESSION_TTL_SECONDS)
    VNC_SESSIONS[ticket] = {
        "vm_id": safe_vm_target(vm_id),
        "backend": backend,
        "username": user.get("username", "user"),
        "role": user.get("role", "user"),
        "status": normalize_status(user.get("status", "active")),
        "vnc_scope": user.get("vnc_scope", "user"),
        "permissions": user.get("permissions", []),
        "created_at": now_iso(),
        "expires_at": expires.isoformat(timespec="seconds"),
        "expires_ts": expires.timestamp(),
        "uses": 0,
    }
    return ticket, VNC_SESSIONS[ticket]

def validate_vnc_session(ticket: str, vm_id: str, backend: str):
    cleanup_vnc_sessions()
    row = VNC_SESSIONS.get(ticket or "")
    if not row:
        return None
    if int(row.get("uses", 0) or 0) > 0:
        VNC_SESSIONS.pop(ticket or "", None)
        return None
    if row.get("vm_id") != safe_vm_target(vm_id):
        return None
    if backend not in {"", "auto"} and row.get("backend") != backend:
        return None
    username = normalize_username(row.get("username", "user"))
    if not username.startswith("coop-"):
        account = load_users().get(username)
        if not account or normalize_status(account.get("status", "active")) != "active":
            VNC_SESSIONS.pop(ticket or "", None)
            return None
        row["role"] = normalize_role(account.get("role", row.get("role", "user")))
    row["uses"] = int(row.get("uses", 0) or 0) + 1
    row["last_used_at"] = now_iso()
    return {
        "username": username,
        "role": row.get("role", "user"),
        "status": normalize_status(row.get("status", "active")),
        "vnc_scope": row.get("vnc_scope", "user"),
        "permissions": row.get("permissions", []),
        "vnc_session": ticket,
        "last_seen": now_iso(),
    }

@app.get("/api/vms/list", dependencies=[Depends(verify_token)])
async def list_vms(user = Depends(verify_token)):
    backend = detect_vm_backend()
    if backend == "none":
        return {"backend": "none", "items": [], "message": "Nie wykryto qm ani virsh na tej maszynie"}

    items = []
    try:
        if backend == "proxmox":
            code, output = run_vm_command(["qm", "list"])
            if code != 0:
                return {"backend": backend, "items": [], "message": output.strip()}
            for line in output.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 3 and parts[0].isdigit():
                    item = {"id": parts[0], "name": parts[1], "status": parts[2], "type": "QEMU/KVM"}
                    if len(parts) >= 4:
                        item["configured_mem_mb"] = parts[3]
                    if len(parts) >= 5:
                        item["bootdisk_gb"] = parts[4]
                    if len(parts) >= 6 and parts[5].isdigit():
                        item["pid"] = int(parts[5])
                    items.append(enrich_vm_item(item))
        elif backend == "libvirt":
            code, output = run_vm_command(["virsh", "list", "--all", "--name"])
            if code != 0:
                return {"backend": backend, "items": [], "message": output.strip()}
            for name in [x.strip() for x in output.splitlines() if x.strip()]:
                state_code, state = run_vm_command(["virsh", "domstate", name], timeout=8)
                item = {"id": name, "name": name, "status": state.strip() if state_code == 0 else "unknown", "type": "libvirt"}
                info_code, info = run_vm_command(["virsh", "dominfo", name], timeout=8)
                if info_code == 0:
                    for row in info.splitlines():
                        if ":" not in row:
                            continue
                        key, value = row.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()
                        if key == "max memory":
                            item["configured_mem"] = value
                        elif key == "used memory":
                            item["used_mem"] = value
                        elif key == "cpu(s)":
                            item["vcpus"] = value
                        elif key == "cpu time":
                            item["cpu_time"] = value
                items.append(enrich_vm_item(item))
        present_ids = [str(item.get("id") or item.get("name") or "") for item in items]
        visible_items = filter_vm_items_for_user(items, user)
        billing = vm_billing_touch(items)
        return {
            "backend": backend,
            "items": visible_items,
            "message": "OK",
            "source": "qm list" if backend == "proxmox" else "virsh list --all --name",
            "generated_at": now_iso(),
            "stale_purged": purge_stale_vm_sidecars(present_ids) if backend == "libvirt" else {"guest_telemetry": 0, "guest_agents": 0},
            "scope": normalize_role(user.get("role")) if isinstance(user, dict) else "authorized",
            "billing": scope_vm_billing_for_user(billing, user, visible_items),
        }
    except Exception as exc:
        return {"backend": backend, "items": [], "message": str(exc)}

@app.get("/api/vms/my/list")
async def list_my_vms(user = Depends(verify_token)):
    payload = await list_vms(user)
    username = normalize_username(user.get("username", "user"))
    is_admin = normalize_role(user.get("role")) in {"admin", "operator"}
    billing = payload.get("billing") or vm_billing_public()
    runtime = billing.get("runtime") or {}
    store = vm_billing_store()
    owner_map = store.get("vm_owners", {})
    scoped_items = []
    for item in payload.get("items", []) or []:
        vm_id = str(item.get("id") or item.get("name") or "").strip()
        access = vm_effective_access(vm_id, user)
        owner = normalize_username((runtime.get(vm_id) or {}).get("owner") or owner_map.get(vm_id) or access.get("owner") or "admin")
        item["owner"] = owner
        item["access_source"] = access.get("source")
        item["permissions"] = access.get("permissions") or []
        item["owned_by_user"] = is_admin or owner == username
        if is_admin or (access.get("allowed") and "vm.read" in set(access.get("permissions") or [])):
            scoped_items.append(item)
    payload["items"] = scoped_items
    payload["scope"] = "admin" if is_admin else "authorized"
    payload["username"] = username
    if not is_admin:
        keep_ids = {str(item.get("id") or item.get("name") or "") for item in scoped_items}
        billing["wallets"] = {username: (billing.get("wallets") or {}).get(username, vm_wallet(store, username))}
        billing["runtime"] = {
            vm_id: row for vm_id, row in (billing.get("runtime") or {}).items()
            if vm_id in keep_ids or normalize_username(row.get("owner", "")) == username
        }
        billing["active"] = [
            row for row in (billing.get("active") or [])
            if row.get("vm_id") in keep_ids or normalize_username(row.get("owner", "")) == username
        ]
        billing["forecast"] = [
            row for row in (billing.get("forecast") or [])
            if normalize_username(row.get("owner", "")) == username
        ]
    payload["billing"] = billing
    return payload

@app.get("/api/vms/billing", dependencies=[Depends(verify_token)])
async def vm_billing_get():
    return vm_billing_live_public()

@app.get("/api/vms/billing/policy", dependencies=[Depends(verify_token)])
async def vm_billing_policy_get():
    billing = vm_billing_store()
    return {
        "status": "ok",
        "policy": {
            "enabled": bool(billing.get("enabled", True)),
            "currency": billing.get("currency", "NXC"),
            "rate_per_hour": float(billing.get("rate_per_hour", 10.0) or 0),
            "tick_seconds": int(billing.get("tick_seconds", 60) or 60),
            "state_multipliers": billing.get("state_multipliers", {}),
            "storage_rate_per_gb_hour": float(billing.get("storage_rate_per_gb_hour", 0.0) or 0),
            "storage_billing_basis": billing.get("storage_billing_basis", "actual"),
            "empty_balance_action": billing.get("empty_balance_action", "shutdown"),
            "hard_kill_after_minutes": int(billing.get("hard_kill_after_minutes", 0) or 0),
            "scheduler": billing.get("scheduler", {}),
        },
        "billing": vm_billing_preview_public(),
    }

@app.post("/api/vms/billing/policy", dependencies=[Depends(verify_admin)])
async def vm_billing_policy_set(data: VMBillingPolicyRequest, admin = Depends(verify_admin)):
    basis = (data.storage_billing_basis or "actual").lower()
    if basis not in {"actual", "virtual", "file"}:
        raise HTTPException(status_code=400, detail="storage_billing_basis: actual, virtual albo file")
    action = (data.empty_balance_action or "shutdown").lower()
    if action not in {"shutdown", "managedsave", "suspend", "freeze", "destroy", "hard_stop", "none"}:
        raise HTTPException(status_code=400, detail="empty_balance_action: shutdown, managedsave, destroy albo none")
    store = vm_billing_store()
    store["enabled"] = bool(data.enabled)
    store["rate_per_hour"] = round(float(data.rate_per_hour), 6)
    store["tick_seconds"] = int(data.tick_seconds)
    store["storage_rate_per_gb_hour"] = round(float(data.storage_rate_per_gb_hour), 8)
    store["storage_billing_basis"] = basis
    store["empty_balance_action"] = action
    store["hard_kill_after_minutes"] = int(data.hard_kill_after_minutes)
    store["state_multipliers"] = {
        "running": 1.0,
        "paused": round(float(data.paused_multiplier), 4),
        "suspended": round(float(data.suspended_multiplier), 4),
        "stopped": round(float(data.stopped_multiplier), 4),
    }
    store.setdefault("scheduler", {})["enabled"] = True
    store.setdefault("ledger", []).append({
        "id": uuid.uuid4().hex[:12],
        "type": "policy",
        "username": admin.get("username", "admin"),
        "amount": store["rate_per_hour"],
        "actor": admin.get("username", "admin"),
        "note": data.note[:180] or "NXC policy update",
        "created_at": now_iso(),
        "policy": {
            "tick_seconds": store["tick_seconds"],
            "state_multipliers": store["state_multipliers"],
            "storage_rate_per_gb_hour": store["storage_rate_per_gb_hour"],
            "storage_billing_basis": basis,
            "empty_balance_action": action,
        },
    })
    save_vm_billing(store)
    log_event(f"VM_BILLING_POLICY rate={store['rate_per_hour']} storage={store['storage_rate_per_gb_hour']} action={action} by={admin.get('username')}")
    return {"status": "saved", "billing": vm_billing_public(store), "preview": vm_billing_preview_public()}

@app.post("/api/vms/billing/tick", dependencies=[Depends(verify_admin)])
async def vm_billing_tick_api(data: VMBillingTickRequest, admin = Depends(verify_admin)):
    if data.dry_run:
        return {"status": "dry_run", "billing": vm_billing_preview_public(), "note": "Dry-run nie pobiera tokenow."}
    if data.confirm and data.confirm != "NXC-TICK":
        raise HTTPException(status_code=412, detail="Dla recznego execute wpisz confirm=NXC-TICK albo zostaw puste.")
    result = vm_billing_live_public()
    log_event(f"VM_BILLING_TICK manual by={admin.get('username')} active={len(result.get('active') or [])}")
    return {"status": "ticked", "billing": result}

@app.get("/api/public/pricing")
async def public_pricing():
    billing = vm_billing_live_public()
    rate = float(billing.get("rate_per_hour", 0) or 0)
    forecast = billing.get("forecast", []) or []
    active_vms = sum(int(row.get("running_vms", 0) or 0) for row in forecast)
    if not active_vms:
        active_vms = len(billing.get("active") or [])
    return {
        "status": "live",
        "currency": "NEXUS TOKEN",
        "symbol": "NXC",
        "rate_per_hour": rate,
        "state_multipliers": billing.get("state_multipliers", {}),
        "storage_rate_per_gb_hour": billing.get("storage_rate_per_gb_hour", 0),
        "storage_billing_basis": billing.get("storage_billing_basis", "actual"),
        "tick_seconds": billing.get("tick_seconds", 60),
        "one_token_minutes": round(60 / rate, 2) if rate > 0 else None,
        "one_hour_cost": rate,
        "active_vms": active_vms,
        "hourly_burn_total": round(sum(float(row.get("hourly_burn", 0) or 0) for row in forecast), 4),
        "forecast": forecast,
        "updated_at": now_iso(),
        "note": "Kurs tokenow za czas wlaczonych maszyn VM.",
    }

@app.post("/api/vms/billing/credit", dependencies=[Depends(verify_admin)])
async def vm_billing_credit_api(data: VMBillingCreditRequest, admin = Depends(verify_admin)):
    store = vm_billing_credit(data.username, data.amount, actor=admin.get("username", "admin"), note=data.note)
    log_event(f"VM_BILLING_CREDIT user={data.username} amount={data.amount} by={admin.get('username')}")
    return {"status": "credited", "billing": vm_billing_public(store)}

@app.post("/api/vms/billing/rate", dependencies=[Depends(verify_admin)])
async def vm_billing_rate_api(data: VMBillingRateRequest, admin = Depends(verify_admin)):
    store = vm_billing_store()
    store["rate_per_hour"] = round(float(data.rate_per_hour), 4)
    store.setdefault("ledger", []).append({
        "id": uuid.uuid4().hex[:12],
        "type": "rate",
        "username": admin.get("username", "admin"),
        "amount": store["rate_per_hour"],
        "actor": admin.get("username", "admin"),
        "note": "Zmiana stawki tokenow VM / h",
        "created_at": now_iso(),
    })
    save_vm_billing(store)
    log_event(f"VM_BILLING_RATE {store['rate_per_hour']} by={admin.get('username')}")
    return {"status": "updated", "billing": vm_billing_public(store)}

@app.get("/api/admin/vm-access", dependencies=[Depends(verify_admin)])
async def admin_vm_access(admin = Depends(verify_admin)):
    store = vm_billing_store()
    return {
        "status": "ok",
        "owners": store.get("vm_owners", {}),
        "acl": store.get("vm_acl", {}),
        "user_limits": store.get("user_limits", {}),
        "permissions": sorted(VM_ALLOWED_PERMISSIONS),
        "owner_default_permissions": sorted(VM_OWNER_PERMISSIONS),
        "admin_permissions": sorted(VM_ADMIN_PERMISSIONS),
    }

@app.post("/api/admin/vm-access/grant", dependencies=[Depends(verify_admin)])
async def admin_vm_access_grant(data: VMAccessGrantRequest, request: Request, admin = Depends(verify_admin)):
    record = grant_vm_access(data, admin, request)
    return {"status": "granted", "record": record, "access": vm_billing_store().get("vm_acl", {})}

@app.post("/api/admin/vm-access/revoke", dependencies=[Depends(verify_admin)])
async def admin_vm_access_revoke(data: VMAccessRevokeRequest, request: Request, admin = Depends(verify_admin)):
    record = revoke_vm_access(data, admin, request)
    return {"status": "revoked", "record": record, "access": vm_billing_store().get("vm_acl", {})}

@app.get("/api/vms/access/me", dependencies=[Depends(verify_token)])
async def vm_access_me(vm_id: str = "", user = Depends(verify_token)):
    if vm_id:
        target = safe_vm_target(vm_id)
        access = vm_effective_access(target, user)
        public = {k: access.get(k) for k in ("allowed", "source", "owner", "permissions", "limits")}
        public["vm_id"] = target
        return public
    store = vm_billing_store()
    username = normalize_username(user.get("username", "user"))
    rows = []
    for target in sorted(set(store.get("vm_owners", {}).keys()) | set(store.get("vm_acl", {}).keys())):
        access = vm_effective_access(target, user)
        if access.get("allowed") and "vm.read" in set(access.get("permissions") or []):
            rows.append({k: access.get(k) for k in ("source", "owner", "permissions", "limits")} | {"vm_id": target})
    return {"username": username, "items": rows}

@app.get("/api/vms/os-catalog", dependencies=[Depends(verify_token)])
async def vm_os_catalog():
    return {
        "catalog": OS_CATALOG,
        "sources": ISO_SOURCE_PRESETS,
        "compat_profiles": VM_COMPAT_PROFILES,
        "iso_roots": [str(root) for root in iso_roots()],
        "tools": {
            "backend": detect_vm_backend(),
            "virt_install": bool(shutil.which("virt-install")),
            "qemu_img": bool(shutil.which("qemu-img")),
            "virtio_win_iso": str(find_virtio_win_iso() or ""),
        },
    }

@app.get("/api/vms/compat/profiles", dependencies=[Depends(verify_token)])
async def vm_compat_profiles():
    return {"profiles": VM_COMPAT_PROFILES}

@app.get("/api/vms/cupertino/prerequisites", dependencies=[Depends(verify_token)])
async def vm_cupertino_prerequisites(vm_name: str = "", opencore_path: str = "", bootloader: str = "", ovmf_code_path: str = "", ovmf_vars_path: str = ""):
    prereq = cupertino_prerequisites(bootloader or opencore_path, ovmf_code_path, ovmf_vars_path)
    if vm_name:
        target = safe_vm_target(vm_name)
        code, output = run_vm_command(["virsh", "dominfo", target], timeout=8)
        prereq["vm_name"] = target
        prereq["vm_exists"] = code == 0
        if code != 0:
            prereq["status"] = "missing"
            prereq["ready"] = False
            prereq["ok"] = False
            prereq.setdefault("missing", []).append(f"VM:{target}")
            prereq["vm_error"] = output.strip()[:500]
    return prereq

@app.post("/api/vms/compat/apply", dependencies=[Depends(verify_admin)])
async def vm_compat_apply(data: VMCompatibilityRequest, admin = Depends(verify_admin)):
    result = apply_vm_compat_profile(data.vm_id, data.profile, data.restart, data.network)
    log_event(f"VM_COMPAT_APPLY vm={result.get('vm_id')} profile={result.get('profile')} by={admin.get('username')}")
    return result

@app.get("/api/vms/doctor", dependencies=[Depends(verify_token)])
async def vm_doctor(vm_id: str, request: Request, user = Depends(verify_token)):
    target = safe_vm_target(vm_id)
    authorize_vm_operation(target, user, "vm.doctor.read", request)
    return diagnose_vm(target)

@app.post("/api/vms/doctor/fix", dependencies=[Depends(verify_admin)])
async def vm_doctor_fix(data: VMDoctorFixRequest, admin = Depends(verify_admin)):
    target = safe_vm_target(data.vm_id)
    diagnosis = diagnose_vm(target)
    profile = (data.profile or diagnosis.get("recommended_profile") or "").strip()
    result = {"status": "checked", "vm_id": target, "diagnosis_before": diagnosis, "actions": []}
    legacy_profiles = {"win95", "win98", "freedos"}
    if profile:
        network = "off" if profile in legacy_profiles else "safe"
        compat = apply_vm_compat_profile(target, profile, data.restart, network)
        result["actions"].append({"kind": "compat", "profile": profile, "result": compat})
    if data.fix_input and (not profile or profile not in legacy_profiles):
        try:
            input_result = ensure_libvirt_input_devices(target, live=True, config=True)
            result["actions"].append({"kind": "input", "result": input_result})
        except Exception as exc:
            result["actions"].append({"kind": "input", "error": str(exc)})
    result["diagnosis_after"] = diagnose_vm(target)
    result["status"] = "fixed"
    log_event(f"VM_DOCTOR_FIX vm={target} profile={profile or 'none'} actions={len(result['actions'])} by={admin.get('username')}")
    return result

@app.get("/api/vms/iso/list", dependencies=[Depends(verify_token)])
async def vm_iso_list():
    items = scan_iso_files()
    return {
        "items": items,
        "cdrom_items": [item for item in items if item.get("cdrom_attachable")],
        "disk_items": [item for item in items if item.get("disk_attachable")],
        "downloads": list(ISO_DOWNLOADS.values()),
        "roots": [str(root) for root in iso_roots()],
    }

@app.get("/api/vms/upload/status", dependencies=[Depends(verify_admin)])
async def vm_chunk_upload_status(admin = Depends(verify_admin)):
    rows = sorted(vm_chunk_upload_store().values(), key=lambda row: row.get("created_at", ""), reverse=True)
    return {
        "status": "ok",
        "items": [public_vm_chunk_upload(row) for row in rows[:80]],
        "tmp_dir": str(VM_CHUNK_UPLOAD_DIR),
        "target_dir": str(NEXUS_ISO_STORAGE_DIR),
        "max_size": VM_CHUNK_UPLOAD_MAX_BYTES,
        "max_size_label": fmt_size(VM_CHUNK_UPLOAD_MAX_BYTES),
    }

@app.post("/api/vms/upload/init", dependencies=[Depends(verify_admin)])
async def vm_chunk_upload_init(data: VMChunkUploadInitRequest, admin = Depends(verify_admin)):
    filename = safe_iso_filename(data.filename)
    target = vm_upload_target_path(filename, overwrite=data.overwrite)
    disk = ensure_vm_upload_space(int(data.size))
    chunk_size = max(1024 * 1024, min(int(data.chunk_size or 5 * 1024 * 1024), 64 * 1024 * 1024))
    part_count = max(1, (int(data.size) + chunk_size - 1) // chunk_size)
    upload_id = uuid.uuid4().hex[:16]
    part_dir = (VM_CHUNK_UPLOAD_DIR / upload_id).resolve()
    part_dir.mkdir(parents=True, exist_ok=True)
    for directory in [Path("/var/lib/nexus"), NEXUS_ISO_STORAGE_DIR, VM_CHUNK_UPLOAD_DIR, part_dir]:
        ensure_libvirt_file_access(directory, is_dir=True)
    record = {
        "id": upload_id,
        "filename": filename,
        "size": int(data.size),
        "sha256": (data.sha256 or "").strip().lower(),
        "purpose": (data.purpose or "auto").strip().lower()[:32],
        "chunk_size": chunk_size,
        "part_count": part_count,
        "part_dir": str(part_dir),
        "target": str(target),
        "overwrite": bool(data.overwrite),
        "status": "open",
        "parts": {},
        "disk_guard": disk,
        "created_by": admin.get("username", "admin"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    async with VM_CHUNK_UPLOAD_LOCK:
        store = vm_chunk_upload_store()
        store[upload_id] = record
        save_vm_chunk_upload_store(store)
    log_event(f"VM_CHUNK_UPLOAD init id={upload_id} filename={filename} size={data.size} by={admin.get('username')}")
    return {
        "status": "open",
        "upload_id": upload_id,
        "filename": filename,
        "chunk_size": chunk_size,
        "part_count": part_count,
        "target": str(target),
        "parts_url": f"/api/vms/upload/{upload_id}/parts/{{part_number}}",
        "complete_url": "/api/vms/upload/complete",
        "disk_guard": disk,
    }

@app.put("/api/vms/upload/{upload_id}/parts/{part_number}", dependencies=[Depends(verify_admin)])
async def vm_chunk_upload_part(upload_id: str, part_number: int, request: Request, admin = Depends(verify_admin)):
    store, row = vm_upload_record(upload_id)
    if row.get("status") != "open":
        raise HTTPException(status_code=409, detail=f"Upload nie jest otwarty: {row.get('status')}")
    part_path = vm_upload_part_path(row, int(part_number))
    expected_start = int(part_number) * int(row.get("chunk_size") or 1)
    expected_max = max(0, min(int(row.get("chunk_size") or 1), int(row.get("size") or 0) - expected_start))
    if expected_max <= 0:
        raise HTTPException(status_code=400, detail="Numer czesci wychodzi poza rozmiar pliku")
    size = 0
    digest = hashlib.sha256()
    with open(part_path, "wb") as out:
        async for chunk in request.stream():
            if not chunk:
                continue
            size += len(chunk)
            if size > expected_max:
                try:
                    part_path.unlink()
                except Exception:
                    pass
                raise HTTPException(status_code=413, detail=f"Czesc {part_number} jest wieksza niz oczekiwano ({fmt_size(size)} > {fmt_size(expected_max)})")
            digest.update(chunk)
            out.write(chunk)
    ensure_libvirt_file_access(part_path)
    part_hash = digest.hexdigest()
    async with VM_CHUNK_UPLOAD_LOCK:
        store = vm_chunk_upload_store()
        row = store.get(upload_id)
        if not row or row.get("status") != "open":
            raise HTTPException(status_code=409, detail="Upload zostal zamkniety podczas wysylania czesci")
        parts = row.setdefault("parts", {})
        parts[str(part_number)] = {"size": size, "sha256": part_hash, "received_at": now_iso()}
        row["updated_at"] = now_iso()
        save_vm_chunk_upload_store(store)
    return {"status": "part_saved", "upload_id": upload_id, "part": int(part_number), "size": size, "sha256": part_hash, "progress": public_vm_chunk_upload(row)["progress"]}

@app.post("/api/vms/upload/complete", dependencies=[Depends(verify_admin)])
async def vm_chunk_upload_complete(data: VMChunkUploadCompleteRequest, request: Request, admin = Depends(verify_admin)):
    store, row = vm_upload_record(data.upload_id)
    if row.get("status") == "complete":
        return {"status": "complete", **public_vm_chunk_upload(row)}
    if row.get("status") != "open":
        raise HTTPException(status_code=409, detail=f"Upload nie jest gotowy do skladania: {row.get('status')}")
    target = Path(row.get("target") or "").resolve()
    if target.exists() and not row.get("overwrite"):
        raise HTTPException(status_code=409, detail="Plik docelowy juz istnieje. Rozpocznij upload z overwrite=true albo zmien nazwe.")
    part_count = int(row.get("part_count") or 0)
    parts = row.get("parts") or {}
    missing = [number for number in range(part_count) if str(number) not in parts]
    if missing:
        raise HTTPException(status_code=400, detail=f"Brakuje czesci: {', '.join(map(str, missing[:20]))}")
    assembling = target.with_name(f".{target.name}.{data.upload_id}.assembling")
    async with VM_CHUNK_UPLOAD_LOCK:
        store = vm_chunk_upload_store()
        row = store.get(data.upload_id)
        row["status"] = "assembling"
        row["updated_at"] = now_iso()
        save_vm_chunk_upload_store(store)
    digest = hashlib.sha256()
    total = 0
    try:
        with open(assembling, "wb") as out:
            for number in range(part_count):
                part_path = vm_upload_part_path(row, number)
                if not part_path.exists():
                    raise HTTPException(status_code=400, detail=f"Brakuje czesci {number}")
                with open(part_path, "rb") as src:
                    while True:
                        chunk = src.read(8 * 1024 * 1024)
                        if not chunk:
                            break
                        digest.update(chunk)
                        total += len(chunk)
                        out.write(chunk)
        expected_size = int(row.get("size") or 0)
        if total != expected_size:
            raise HTTPException(status_code=400, detail=f"Rozmiar po zlozeniu nie pasuje: {fmt_size(total)} zamiast {fmt_size(expected_size)}")
        actual = digest.hexdigest()
        expected_hash = (data.sha256 or row.get("sha256") or "").strip().lower()
        if expected_hash and not hmac.compare_digest(expected_hash, actual):
            raise HTTPException(status_code=400, detail=f"SHA256 nie pasuje: {actual}")
        ensure_libvirt_file_access(assembling)
        assembling.replace(target)
        ensure_libvirt_file_access(target)
        validation = validate_completed_vm_upload(target)
        cupertino = cupertino_prerequisites(str(target)) if target.name.lower() == "opencore.qcow2" else None
        try:
            shutil.rmtree(Path(row.get("part_dir") or ""), ignore_errors=True)
        except Exception:
            pass
        async with VM_CHUNK_UPLOAD_LOCK:
            store = vm_chunk_upload_store()
            row = store.get(data.upload_id, row)
            row.update({
                "status": "complete",
                "target": str(target),
                "actual_sha256": actual,
                "received_size": total,
                "validation": validation,
                "cupertino": cupertino,
                "updated_at": now_iso(),
                "finished_at": now_iso(),
            })
            save_vm_chunk_upload_store(store)
        audit_event(admin.get("username", "admin"), "vm.upload.complete", target.name, "OK", request, {"size": total, "sha256": actual})
        log_event(f"VM_CHUNK_UPLOAD complete id={data.upload_id} target={target} size={total} by={admin.get('username')}")
        return {"status": "complete", "path": str(target), "item": public_vm_chunk_upload(row), "validation": validation, "cupertino": cupertino}
    except HTTPException as exc:
        try:
            assembling.unlink()
        except Exception:
            pass
        async with VM_CHUNK_UPLOAD_LOCK:
            store = vm_chunk_upload_store()
            row = store.get(data.upload_id, row)
            row["status"] = "error"
            row["error"] = str(exc.detail)
            row["updated_at"] = now_iso()
            save_vm_chunk_upload_store(store)
        audit_event(admin.get("username", "admin"), "vm.upload.complete", target.name, "FAIL", request, {"error": str(exc.detail)})
        raise
    except Exception as exc:
        try:
            assembling.unlink()
        except Exception:
            pass
        async with VM_CHUNK_UPLOAD_LOCK:
            store = vm_chunk_upload_store()
            row = store.get(data.upload_id, row)
            row["status"] = "error"
            row["error"] = str(exc)
            row["updated_at"] = now_iso()
            save_vm_chunk_upload_store(store)
        audit_event(admin.get("username", "admin"), "vm.upload.complete", target.name, "FAIL", request, {"error": str(exc)})
        raise HTTPException(status_code=500, detail=f"Nie udalo sie zlozyc uploadu VM: {exc}")

@app.post("/api/vms/upload/cancel", dependencies=[Depends(verify_admin)])
async def vm_chunk_upload_cancel(data: VMChunkUploadCancelRequest, admin = Depends(verify_admin)):
    async with VM_CHUNK_UPLOAD_LOCK:
        store, row = vm_upload_record(data.upload_id)
        row["status"] = "cancelled"
        row["error"] = "Anulowano"
        row["updated_at"] = now_iso()
        row["finished_at"] = now_iso()
        save_vm_chunk_upload_store(store)
    try:
        shutil.rmtree(Path(row.get("part_dir") or ""), ignore_errors=True)
    except Exception:
        pass
    log_event(f"VM_CHUNK_UPLOAD cancel id={data.upload_id} by={admin.get('username')}")
    return {"status": "cancelled", "upload_id": data.upload_id}

@app.get("/api/vms/drivers/list", dependencies=[Depends(verify_token)])
async def vm_drivers_list():
    return {
        "items": scan_driver_packages(),
        "roots": [str(root) for root in driver_roots()],
        "tools": {
            "extractor": external_extract_tool(),
            "iso_builder": iso_build_tool(),
            "virtio_win_iso": str(find_virtio_win_iso() or ""),
        },
    }

@app.post("/api/vms/drivers/extract", dependencies=[Depends(verify_admin)])
async def vm_drivers_extract(data: VMDriverExtractRequest):
    result = extract_driver_package(Path(data.path))
    log_event(f"VM_DRIVER_EXTRACT source={result.get('source')} count={result.get('file_count')}")
    return result

@app.post("/api/vms/iso/download", dependencies=[Depends(verify_admin)])
async def vm_iso_download(data: ISODownloadRequest, background_tasks: BackgroundTasks):
    parsed = validate_iso_url(data.url)
    filename = safe_iso_filename(data.filename or Path(urllib.parse.unquote(parsed.path)).name)
    target = (LIBVIRT_ISO_DIR / filename).resolve()
    if LIBVIRT_ISO_DIR.resolve() not in target.parents:
        raise HTTPException(status_code=400, detail="Niepoprawna nazwa pliku ISO")
    if target.exists():
        raise HTTPException(status_code=409, detail="Taki obraz juz istnieje w ISO Vault")
    job_id = uuid.uuid4().hex[:12]
    ISO_DOWNLOADS[job_id] = {
        "id": job_id,
        "url": data.url,
        "filename": filename,
        "target": str(target),
        "status": "queued",
        "downloaded": 0,
        "total": 0,
        "created_at": now_iso(),
    }
    background_tasks.add_task(download_iso_worker, job_id, data.url, target)
    log_event(f"ISO_DOWNLOAD queued {filename} {data.url}")
    return ISO_DOWNLOADS[job_id]

@app.post("/api/vms/iso/cancel", dependencies=[Depends(verify_admin)])
async def vm_iso_cancel(data: ISOJobRequest):
    job = ISO_DOWNLOADS.get(data.id)
    if not job:
        raise HTTPException(status_code=404, detail="Nie znaleziono transferu ISO")
    if job.get("status") in {"done", "error"}:
        return job
    job["status"] = "cancel_requested"
    job["error"] = "Anulowano z TRANSFER CORE"
    job["finished_at"] = now_iso()
    try:
        target = Path(job.get("target") or "")
        part = target.with_suffix(target.suffix + ".part")
        if part.exists():
            part.unlink()
    except Exception:
        pass
    log_event(f"ISO_DOWNLOAD cancel {data.id}")
    return job

@app.post("/api/vms/create", dependencies=[Depends(verify_admin)])
async def vm_create(data: VMCreateRequest, admin = Depends(verify_admin)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Tworzenie VM jest teraz wspierane dla libvirt/KVM")
    if not shutil.which("virt-install") or not shutil.which("qemu-img"):
        raise HTTPException(status_code=500, detail="Brakuje virt-install albo qemu-img")
    name = safe_domain_name(data.name)
    preset = os_preset(data.os_id)
    iso = prepare_libvirt_iso(allowed_iso_path(data.iso_path))
    iso_validation = validate_cdrom_image(iso)
    effective = resolve_vm_create_effective(data, preset, iso)
    preset = effective["preset"]
    cupertino_preflight = None
    if is_macos_preset(preset):
        if not data.legal_byol_ack:
            raise HTTPException(status_code=412, detail="Cupertino Legal Shield: potwierdz BYOL. NEXUS nie dostarcza licencji, OSK ani chronionych komponentow Apple.")
        cupertino_preflight = cupertino_prerequisites(data.opencore_path, data.ovmf_code_path, data.ovmf_vars_path)
        if not cupertino_preflight.get("ok"):
            raise HTTPException(status_code=412, detail={"message": "Brakuje zasobow Cupertino BYOL", **cupertino_preflight})
    driver_media = None
    if effective.get("attach_driver_media", True):
        driver_media = selected_driver_media(preset, data.driver_path, data.driver_categories)
    code, _ = run_vm_command(["virsh", "dominfo", name], timeout=8)
    if code == 0:
        raise HTTPException(status_code=409, detail="VM o tej nazwie juz istnieje")
    ram_policy = plan_vm_memory_allocation(effective["memory_mb"], name, preset)
    effective["target_memory_mb"] = int(ram_policy["target_memory_mb"])
    effective["startup_memory_mb"] = int(ram_policy["startup_memory_mb"])
    memory_info = ram_policy
    disk_info = ensure_vm_disk_capacity(effective["disk_gb"], name)

    image_dir = LIBVIRT_IMAGE_DIR
    image_dir.mkdir(parents=True, exist_ok=True)
    ensure_libvirt_file_access(image_dir, is_dir=True)
    disk = (image_dir / f"{name}.qcow2").resolve()
    if disk.exists():
        raise HTTPException(status_code=409, detail="Dysk qcow2 o tej nazwie juz istnieje")

    dynamic_disk = create_dynamic_disk(disk, effective["disk_gb"])

    command = virt_install_command(data, preset, iso, disk, driver_media, effective=effective)
    code, output = run_vm_command(command, timeout=120)
    if code != 0:
        cleanup_failed_vm(name, disk)
        raise HTTPException(status_code=500, detail=output.strip() or "virt-install nie utworzyl VM")

    compat_patch = None
    cupertino_patch = None
    ram_thin_patch = None
    media_policy = None
    if is_win9x_preset(preset):
        try:
            compat_patch = apply_vm_compat_profile(name, preset.get("id"), restart=True, network="off")
        except HTTPException:
            cleanup_failed_vm(name, disk)
            raise
    if is_macos_preset(preset):
        try:
            cupertino_patch = apply_cupertino_profile(name, iso, disk, cupertino_preflight, restart=bool(data.start), legal_byol_ack=bool(data.legal_byol_ack))
        except HTTPException:
            cleanup_failed_vm(name, disk)
            raise
    try:
        ram_thin_patch = apply_vm_memory_thin_config(name, effective["target_memory_mb"], effective["startup_memory_mb"])
    except HTTPException:
        cleanup_failed_vm(name, disk)
        raise
    if not is_macos_preset(preset):
        try:
            media_policy = normalize_vm_cdrom_policy(name, live=bool(data.start), config=True)
        except Exception as exc:
            media_policy = {"status": "warning", "error": str(exc)}
            log_event(f"VM_CREATE media-policy warning vm={name}: {exc}")

    vm_billing_assign_owner(name, admin.get("username", "admin"))
    log_event(f"VM_CREATE name={name} os={data.os_id}->{preset.get('id')} ram_start={effective['startup_memory_mb']} ram_target={effective['target_memory_mb']} ram_policy={memory_info.get('status')} vcpus={effective['vcpus']} disk_gb={effective['disk_gb']} cpu={effective.get('cpu') or 'default'} available_mb={memory_info.get('available_mb')} swap_free_mb={memory_info.get('swap_free_mb')} iso={iso.name} driver={driver_media.name if driver_media else 'none'} disk={disk.name} code={code}")
    return {
        "status": "created",
        "backend": "libvirt",
        "vm_id": name,
        "name": name,
        "os": preset,
        "disk": str(disk),
        "iso": str(iso),
        "driver_media": str(driver_media or ""),
        "auto_profile": effective.get("auto_profile"),
        "detected_profile": effective.get("detected_profile"),
        "profile_warnings": effective.get("warnings", []),
        "effective_memory_mb": effective["target_memory_mb"],
        "effective_target_memory_mb": effective["target_memory_mb"],
        "effective_startup_memory_mb": effective["startup_memory_mb"],
        "requested_disk_gb": data.disk_gb,
        "effective_disk_gb": effective["disk_gb"],
        "effective_vcpus": effective["vcpus"],
        "effective_cpu": effective.get("cpu") or "",
        "effective_network": effective.get("network"),
        "compat_patch": compat_patch,
        "cupertino_preflight": cupertino_preflight,
        "cupertino_patch": cupertino_patch,
        "ram_policy": ram_policy,
        "ram_thin_patch": ram_thin_patch,
        "media_policy": media_policy,
        "iso_validation": iso_validation,
        "disk_guard": disk_info,
        "dynamic_disk": dynamic_disk,
        "output": output.strip(),
        "virtio_win_iso": str(find_virtio_win_iso() or ""),
    }

@app.post("/api/vms/start", dependencies=[Depends(verify_token)])
async def vm_start(data: VMStartRequest, request: Request, user = Depends(verify_token)):
    backend = detect_vm_backend() if data.backend == "auto" else data.backend
    if backend != "libvirt":
        raise HTTPException(status_code=400, detail="Cupertino start jest wspierany dla libvirt/KVM")
    target = safe_vm_target(data.vm_name or data.vm_id)
    authorize_vm_operation(target, user, "vm.start", request)
    if not data.legal_byol_ack:
        audit_event(user.get("username", "user"), "cupertino.start", target, "DENY", request, {"reason": "legal_byol_ack_false"})
        raise HTTPException(status_code=403, detail="Cupertino Legal Shield: wymagane legal_byol_ack=True")
    code, dominfo = run_vm_command(["virsh", "dominfo", target], timeout=8)
    if code != 0:
        raise HTTPException(status_code=404, detail=dominfo.strip() or f"Nie znaleziono VM {target}")
    bootloader = cupertino_bootloader_arg(data.bootloader)
    prereq = cupertino_prerequisites(bootloader, data.ovmf_code_path, data.ovmf_vars_path)
    if not prereq.get("ok"):
        raise HTTPException(status_code=412, detail={"message": "Cupertino prerequisites nie przeszly", **prereq})
    state = vm_domain_state_label(target)
    if "running" in state.lower():
        return {"status": "already_running", "vm_id": target, "state": state, "preflight": prereq}
    vm_billing_can_start(target, vm_billing_current_owner(target))
    disk = vm_primary_disk_path(target)
    iso = vm_installer_iso_path(target, data.iso_path)
    patch = apply_cupertino_profile(target, iso, disk, prereq, restart=True, legal_byol_ack=True)
    audit_event(user.get("username", "user"), "cupertino.start", target, "OK", request, {"bootloader": prereq.get("opencore"), "iso": str(iso), "disk": str(disk)})
    try:
        send_webhook_event("vm.action", {"backend": backend, "vm_id": target, "action": "cupertino-start", "actor": user.get("username"), "output": patch.get("start_output", "")[:500]})
    except Exception as exc:
        log_event(f"WEBHOOK cupertino.start error: {exc}")
    return {
        "status": "booting",
        "backend": backend,
        "vm_id": target,
        "state_before": state,
        "preflight": prereq,
        "disk": str(disk),
        "iso": str(iso),
        "patch": patch,
    }

@app.post("/api/vms/action", dependencies=[Depends(verify_admin)])
async def vm_action(data: VMActionRequest, request: Request, admin = Depends(verify_admin)):
    backend = detect_vm_backend() if data.backend == "auto" else data.backend
    action = data.action.lower().strip()
    if action not in {"start", "shutdown", "stop", "reboot"}:
        raise HTTPException(status_code=400, detail="Nieznana akcja VM")
    if backend not in {"proxmox", "libvirt"}:
        raise HTTPException(status_code=400, detail="Nie wykryto silnika VM")

    target = data.vm_id.strip()
    if not target or target.startswith("-"):
        raise HTTPException(status_code=400, detail="Niepoprawny identyfikator VM")
    if action == "stop":
        require_destructive_confirmation(admin, "vm.stop.hard", target, data.confirm, request, data.reason)
    cupertino_auto_patch = None
    if action == "start":
        if backend == "libvirt":
            cupertino_auto_patch = auto_apply_cupertino_profile_for_start(target)
            enforce_cupertino_start_guard(target)
        vm_billing_can_start(target, admin.get("username", "admin"))
        if backend == "libvirt":
            if not cupertino_auto_patch:
                detach_bad_cdrom_media(target, live=False, config=True)
    if backend == "libvirt":
        state = vm_domain_state_label(target)
        if action == "start" and "running" in state:
            return {"status": "already_running", "backend": backend, "vm_id": target, "action": action, "state": state, "cupertino_auto_patch": cupertino_auto_patch, "output": "VM juz dziala"}
        if action in {"shutdown", "stop"} and ("shut off" in state or "shutoff" in state):
            return {"status": "already_stopped", "backend": backend, "vm_id": target, "action": action, "state": state, "output": "VM juz jest wylaczona"}
        if action == "reboot" and not ("running" in state):
            return {"status": "not_running", "backend": backend, "vm_id": target, "action": action, "state": state, "output": "VM nie dziala, wiec reboot nie ma czego restartowac"}

    if backend == "proxmox":
        if not target.isdigit():
            raise HTTPException(status_code=400, detail="Proxmox wymaga numerycznego VMID")
        command_map = {
            "start": ["qm", "start", target],
            "shutdown": ["qm", "shutdown", target],
            "stop": ["qm", "stop", target],
            "reboot": ["qm", "reboot", target],
        }
    else:
        command_map = {
            "start": ["virsh", "start", target],
            "shutdown": ["virsh", "shutdown", target],
            "stop": ["virsh", "destroy", target],
            "reboot": ["virsh", "reboot", target],
        }

    code, output = run_vm_command(command_map[action], timeout=30)
    log_event(f"VM {backend}:{target} action={action} code={code}")
    if code != 0:
        if action == "start" and "already active" in output.lower():
            return {"status": "already_running", "backend": backend, "vm_id": target, "action": action, "cupertino_auto_patch": cupertino_auto_patch, "output": output.strip()}
        raise HTTPException(status_code=500, detail=output.strip() or "Akcja VM nie powiodla sie")
    try:
        send_webhook_event("vm.action", {"backend": backend, "vm_id": target, "action": action, "actor": admin.get("username", "admin"), "output": output.strip()[:500]})
    except Exception as exc:
        log_event(f"WEBHOOK vm.action error: {exc}")
    return {"status": "success", "backend": backend, "vm_id": target, "action": action, "cupertino_auto_patch": cupertino_auto_patch, "output": output.strip()}

@app.post("/api/vms/my/action")
async def vm_my_action(data: VMActionRequest, request: Request, user = Depends(verify_token)):
    backend = detect_vm_backend() if data.backend == "auto" else data.backend
    action = data.action.lower().strip()
    if action not in {"start", "shutdown", "stop", "reboot"}:
        raise HTTPException(status_code=400, detail="Nieznana akcja VM")
    if backend not in {"proxmox", "libvirt"}:
        raise HTTPException(status_code=400, detail="Nie wykryto silnika VM")

    target = safe_vm_target(data.vm_id)
    operation_map = {"start": "vm.start", "shutdown": "vm.stop", "stop": "vm.stop", "reboot": "vm.reboot"}
    access = authorize_vm_operation(target, user, operation_map[action], request)
    owner = access.get("owner") or vm_billing_current_owner(target)
    if action == "stop":
        require_destructive_confirmation(user, "vm.stop.hard", target, data.confirm, request, data.reason)
    cupertino_auto_patch = None
    if action == "start":
        if backend == "libvirt":
            cupertino_auto_patch = auto_apply_cupertino_profile_for_start(target)
            enforce_cupertino_start_guard(target)
        vm_billing_can_start(target, owner)
        if backend == "libvirt":
            if not cupertino_auto_patch:
                detach_bad_cdrom_media(target, live=False, config=True)
    if backend == "libvirt":
        state = vm_domain_state_label(target)
        if action == "start" and "running" in state:
            return {"status": "already_running", "backend": backend, "vm_id": target, "owner": owner, "action": action, "state": state, "cupertino_auto_patch": cupertino_auto_patch, "output": "VM juz dziala"}
        if action in {"shutdown", "stop"} and ("shut off" in state or "shutoff" in state):
            return {"status": "already_stopped", "backend": backend, "vm_id": target, "owner": owner, "action": action, "state": state, "output": "VM juz jest wylaczona"}
        if action == "reboot" and not ("running" in state):
            return {"status": "not_running", "backend": backend, "vm_id": target, "owner": owner, "action": action, "state": state, "output": "VM nie dziala, wiec reboot nie ma czego restartowac"}

    if backend == "proxmox":
        if not target.isdigit():
            raise HTTPException(status_code=400, detail="Proxmox wymaga numerycznego VMID")
        command_map = {
            "start": ["qm", "start", target],
            "shutdown": ["qm", "shutdown", target],
            "stop": ["qm", "stop", target],
            "reboot": ["qm", "reboot", target],
        }
    else:
        command_map = {
            "start": ["virsh", "start", target],
            "shutdown": ["virsh", "shutdown", target],
            "stop": ["virsh", "destroy", target],
            "reboot": ["virsh", "reboot", target],
        }

    code, output = run_vm_command(command_map[action], timeout=30)
    actor = user.get("username", "user")
    log_event(f"VM_USER_ACTION {backend}:{target} action={action} owner={owner} actor={actor} code={code}")
    if code != 0:
        if action == "start" and "already active" in output.lower():
            return {"status": "already_running", "backend": backend, "vm_id": target, "owner": owner, "action": action, "cupertino_auto_patch": cupertino_auto_patch, "output": output.strip()}
        raise HTTPException(status_code=500, detail=output.strip() or "Akcja VM nie powiodla sie")
    try:
        send_webhook_event("vm.action", {"backend": backend, "vm_id": target, "action": action, "owner": owner, "actor": actor, "output": output.strip()[:500]})
    except Exception as exc:
        log_event(f"WEBHOOK vm.user.action error: {exc}")
    return {"status": "success", "backend": backend, "vm_id": target, "owner": owner, "action": action, "cupertino_auto_patch": cupertino_auto_patch, "output": output.strip()}

@app.post("/api/vms/delete", dependencies=[Depends(verify_admin)])
async def vm_delete(data: VMDeleteRequest, request: Request, admin = Depends(verify_admin)):
    backend = detect_vm_backend() if data.backend == "auto" else data.backend
    target = safe_vm_target(data.vm_id)
    audit_event(
        admin.get("username", "admin"),
        "confirm.vm.delete",
        target,
        "AUTO",
        request,
        {"reason": data.reason or "button-confirm", "remove_storage": bool(data.remove_storage)},
    )
    removed_disks = []
    if backend == "proxmox":
        if not target.isdigit():
            raise HTTPException(status_code=400, detail="Proxmox wymaga numerycznego VMID")
        command = ["qm", "destroy", target]
        if data.remove_storage:
            command.append("--destroy-unreferenced-disks")
            command.append("1")
        code, output = run_vm_command(command, timeout=90)
        if code != 0:
            raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie usunac VM")
    elif backend == "libvirt":
        disks = vm_storage_paths(target) if data.remove_storage else []
        state_code, state = run_vm_command(["virsh", "domstate", target], timeout=8)
        if state_code == 0 and "running" in state.lower():
            run_vm_command(["virsh", "destroy", target], timeout=30)
        run_vm_command(["virsh", "managedsave-remove", target], timeout=30)
        code, output = run_vm_command(["virsh", "undefine", target, "--nvram"], timeout=30)
        if code != 0:
            code, output = run_vm_command(["virsh", "undefine", target], timeout=30)
        if code != 0:
            raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie usunac definicji VM")
        if data.remove_storage:
            for path in disks:
                try:
                    path.unlink()
                    removed_disks.append(str(path))
                except Exception as exc:
                    log_event(f"VM_DELETE disk error {path}: {exc}")
    else:
        raise HTTPException(status_code=400, detail="Nie wykryto silnika VM")

    forwards = read_json(VM_PORT_FORWARDS_FILE, [])
    remaining = []
    for item in forwards:
        if item.get("vm_id") == target:
            try:
                delete_port_forward_rule(item)
            except Exception as exc:
                log_event(f"VM_DELETE port rule error {item.get('id')}: {exc}")
        else:
            remaining.append(item)
    write_json(VM_PORT_FORWARDS_FILE, remaining)
    log_event(f"VM_DELETE backend={backend} vm={target} remove_storage={data.remove_storage} disks={len(removed_disks)}")
    return {"status": "deleted", "backend": backend, "vm_id": target, "removed_disks": removed_disks}

@app.get("/api/vms/snapshots", dependencies=[Depends(verify_token)])
async def vm_snapshots(vm_id: str, request: Request, user = Depends(verify_token)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Snapshoty sa teraz wspierane dla libvirt/KVM")
    target = safe_vm_target(vm_id)
    authorize_vm_operation(target, user, "snapshot.read", request)
    code, output = run_vm_command(["virsh", "snapshot-list", target, "--name"], timeout=15)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie pobrac snapshotow")
    items = []
    for name in [row.strip() for row in output.splitlines() if row.strip()]:
        item = {"name": name}
        info_code, info = run_vm_command(["virsh", "snapshot-info", target, name], timeout=8)
        if info_code == 0:
            item.update(parse_snapshot_info(info))
        items.append(item)
    return {"vm_id": target, "items": items}

@app.post("/api/vms/snapshots/create", dependencies=[Depends(verify_token)])
async def vm_snapshot_create(data: VMSnapshotRequest, request: Request, user = Depends(verify_token)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Snapshoty sa teraz wspierane dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    authorize_vm_operation(target, user, "snapshot.create", request)
    name = safe_snapshot_name(data.name)
    desc = (data.description or f"NEXUS snapshot {now_iso()}")[:240]
    command = ["virsh", "snapshot-create-as", "--domain", target, "--name", name, "--description", desc, "--atomic"]
    code, output = run_vm_command(command, timeout=300)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Snapshot nie zostal utworzony")
    log_event(f"VM_SNAPSHOT create vm={target} snapshot={name}")
    return {"status": "created", "vm_id": target, "snapshot": name, "output": output.strip()}

@app.post("/api/vms/snapshots/revert", dependencies=[Depends(verify_token)])
async def vm_snapshot_revert(data: VMSnapshotActionRequest, request: Request, user = Depends(verify_token)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Snapshoty sa teraz wspierane dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    authorize_vm_operation(target, user, "snapshot.restore", request)
    snapshot = safe_snapshot_name(data.snapshot)
    require_destructive_confirmation(user, "snapshot.revert", target, data.confirm or snapshot, request, snapshot)
    code, output = run_vm_command(["virsh", "snapshot-revert", target, snapshot, "--force"], timeout=300)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie przywrocic snapshotu")
    log_event(f"VM_SNAPSHOT revert vm={target} snapshot={snapshot}")
    return {"status": "reverted", "vm_id": target, "snapshot": snapshot, "output": output.strip()}

@app.post("/api/vms/snapshots/delete", dependencies=[Depends(verify_token)])
async def vm_snapshot_delete(data: VMSnapshotActionRequest, request: Request, user = Depends(verify_token)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Snapshoty sa teraz wspierane dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    authorize_vm_operation(target, user, "snapshot.delete", request)
    snapshot = safe_snapshot_name(data.snapshot)
    if (data.confirm or "").strip() not in {target, snapshot, f"snapshot.delete:{snapshot}", "CONFIRM-" + snapshot}:
        audit_event(user.get("username", "anonymous"), "confirm.snapshot.delete", target, "DENY", request, {"snapshot": snapshot})
        raise HTTPException(status_code=409, detail={"message": "Usuniecie snapshotu wymaga potwierdzenia nazwa snapshotu albo VM.", "confirm_required": snapshot})
    code, output = run_vm_command(["virsh", "snapshot-delete", target, snapshot], timeout=120)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie usunac snapshotu")
    log_event(f"VM_SNAPSHOT delete vm={target} snapshot={snapshot}")
    return {"status": "deleted", "vm_id": target, "snapshot": snapshot, "output": output.strip()}

@app.get("/api/vms/config", dependencies=[Depends(verify_token)])
async def vm_config(vm_id: str, request: Request, user = Depends(verify_token)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Edycja konfiguracji jest teraz wspierana dla libvirt/KVM")
    target = safe_vm_target(vm_id)
    authorize_vm_operation(target, user, "vm.config.read", request)
    info = parse_dominfo(target)
    info["memory_config"] = vm_memory_xml_state(target, inactive=True)
    info["storage"] = [str(path) for path in vm_storage_paths(target)]
    info["cdroms"] = vm_cdrom_targets(target)
    info["interfaces"] = vm_interface_rows(target)
    return info

@app.post("/api/vms/config", dependencies=[Depends(verify_token)])
async def vm_config_update(data: VMConfigRequest, request: Request, user = Depends(verify_token)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Edycja konfiguracji jest teraz wspierana dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    authorize_vm_operation(target, user, "vm.memory.change", request)
    authorize_vm_operation(target, user, "vm.cpu.change", request)
    before = parse_dominfo(target)
    memory_report = vm_ram_update_cascade(target, data.memory_mb, live=data.live, config=data.config)
    vcpu_counts = before.get("vcpu_counts") or {}
    max_config_vcpus = int(vcpu_counts.get("maximum_config") or before.get("vcpus") or 1)
    wanted_vcpus = int(data.vcpus)
    commands = []
    if wanted_vcpus > max_config_vcpus:
        commands.append(["virsh", "setvcpus", target, str(wanted_vcpus), "--maximum", "--config"])
    commands.append(["virsh", "setvcpus", target, str(wanted_vcpus), "--config"])
    warnings = list(memory_report.get("warnings") or [])
    cpu_attempts = []
    for command in commands:
        code, output = run_vm_command(command, timeout=30)
        cpu_attempts.append({"stage": "persistent", "command": command, "code": code, "ok": code == 0, "output": output.strip()})
        if code != 0:
            raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie zapisac konfiguracji VM")
    if data.live and "running" in str(before.get("state", "")).lower():
        for command in [
            ["virsh", "setvcpus", target, str(wanted_vcpus), "--live"],
        ]:
            code, output = run_vm_command(command, timeout=30)
            cpu_attempts.append({"stage": "live", "command": command, "code": code, "ok": code == 0, "output": output.strip()})
            if code != 0:
                warnings.append(output.strip() or "Zmiana live nie powiodla sie, zapisano konfiguracje po restarcie VM")
    after = parse_dominfo(target)
    status = "warning" if warnings or memory_report.get("status") in {"warning", "pending_restart"} else "updated"
    log_event(f"VM_CONFIG vm={target} ram={data.memory_mb} ram_live={memory_report.get('live')} ram_persistent={memory_report.get('persistent')} vcpus={wanted_vcpus} max_before={max_config_vcpus} live={data.live}")
    return {"status": status, "vm_id": target, "before": before, "after": after, "warnings": warnings, "memory": memory_report, "cpu_attempts": cpu_attempts}

async def vm_ram_update_common(data: VMRamUpdateRequest, request: Request, user):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Edycja RAM jest teraz wspierana dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    authorize_vm_operation(target, user, "vm.memory.change", request)
    result = vm_ram_update_cascade(target, data.memory_mb, live=data.live, config=data.config)
    log_event(f"VM_RAM_UPDATE vm={target} ram={data.memory_mb} live={result.get('live')} persistent={result.get('persistent')} by={user.get('username')}")
    return result

@app.post("/api/vm/ram/update", dependencies=[Depends(verify_token)])
async def vm_ram_update_single(data: VMRamUpdateRequest, request: Request, user = Depends(verify_token)):
    return await vm_ram_update_common(data, request, user)

@app.post("/api/vms/ram/update", dependencies=[Depends(verify_token)])
async def vm_ram_update_plural(data: VMRamUpdateRequest, request: Request, user = Depends(verify_token)):
    return await vm_ram_update_common(data, request, user)

@app.post("/api/vms/iso/attach", dependencies=[Depends(verify_token)])
async def vm_iso_attach(data: VMIsoAttachRequest, request: Request, user = Depends(verify_token)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Podmiana ISO jest teraz wspierana dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    authorize_vm_operation(target, user, "vm.iso.attach", request)
    iso = allowed_iso_path(data.iso_path)
    tx = vm_media_transaction_begin(target, "iso-attach")
    try:
        result = attach_or_change_vm_iso_target(target, iso, live=data.live, config=data.config, target_dev=data.target, force=data.force)
        result["transaction"] = {"status": "committed", "started_at": tx.get("started_at")}
        audit_event(user.get("username", "anonymous"), "vm.iso.attach", target, "OK", request, {"iso": str(iso), "target": result.get("target"), "mode": result.get("mode")})
        log_event(f"VM_ISO_ATTACH vm={target} iso={result.get('iso')} mode={result.get('mode')} target={result.get('target')} force={data.force} live={data.live} config={data.config} by={user.get('username')}")
        return {"status": "attached", "vm_id": target, **result}
    except Exception as exc:
        rollback = vm_media_transaction_rollback(tx, getattr(exc, "detail", str(exc)))
        audit_event(user.get("username", "anonymous"), "vm.iso.attach", target, "ROLLBACK", request, {"iso": str(iso), "error": str(getattr(exc, "detail", exc))[:500], "rollback": rollback})
        raise_media_transaction_error(exc, rollback)

@app.post("/api/vms/iso/eject", dependencies=[Depends(verify_token)])
async def vm_iso_eject(data: VMIsoEjectRequest, request: Request, user = Depends(verify_token)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Wysuwanie ISO jest teraz wspierane dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    authorize_vm_operation(target, user, "vm.iso.attach", request)
    tx = vm_media_transaction_begin(target, "iso-eject")
    try:
        result = eject_vm_iso_target(target, target_dev=data.target, live=data.live, config=data.config, force=data.force)
        result["transaction"] = {"status": "committed", "started_at": tx.get("started_at")}
        audit_event(user.get("username", "anonymous"), "vm.iso.eject", target, "OK", request, {"target": data.target or "all", "ejected": len(result.get("ejected") or [])})
        log_event(f"VM_ISO_EJECT vm={target} target={data.target or 'all'} force={data.force} live={data.live} config={data.config} by={user.get('username')}")
        return {"status": "ejected", "vm_id": target, **result}
    except Exception as exc:
        rollback = vm_media_transaction_rollback(tx, getattr(exc, "detail", str(exc)))
        audit_event(user.get("username", "anonymous"), "vm.iso.eject", target, "ROLLBACK", request, {"target": data.target or "all", "error": str(getattr(exc, "detail", exc))[:500], "rollback": rollback})
        raise_media_transaction_error(exc, rollback)

@app.get("/api/vms/media/status", dependencies=[Depends(verify_token)])
async def vm_media_status_api(vm_id: str, user = Depends(verify_token)):
    target = safe_vm_target(vm_id)
    authorize_vm_operation(target, user, "vm.media.read")
    return vm_media_status(target)

@app.get("/api/vms/storage/thin", dependencies=[Depends(verify_token)])
async def vm_storage_thin_status(vm_id: str = "", path: str = "", request: Request = None, user = Depends(verify_token)):
    target = safe_vm_target(vm_id) if vm_id else ""
    if target:
        authorize_vm_operation(target, user, "vm.config.read", request)
    elif normalize_role(user.get("role")) != "admin":
        raise HTTPException(status_code=403, detail="Sciezka dysku bez VM jest dostepna tylko dla admina")
    if path:
        allowed_vm_disk_path(path)
    return vm_storage_thin_report(target, path)

@app.post("/api/vms/storage/thin/apply", dependencies=[Depends(verify_admin)])
async def vm_storage_thin_apply(data: VMStorageThinRequest, admin = Depends(verify_admin)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Thin policy jest wspierane dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    result = apply_vm_thin_policy(target)
    log_event(f"VM_THIN_APPLY vm={target} changed={len(result.get('changed', []))} by={admin.get('username')}")
    return result

@app.post("/api/vms/storage/compact", dependencies=[Depends(verify_admin)])
async def vm_storage_compact(data: VMStorageCompactRequest, admin = Depends(verify_admin)):
    target = safe_vm_target(data.vm_id) if data.vm_id else ""
    disk = None
    if data.path:
        disk = allowed_vm_disk_path(data.path)
    elif target:
        disk = vm_primary_disk_path(target)
    if not disk:
        raise HTTPException(status_code=400, detail="Podaj VM albo sciezke dysku qcow2")
    if disk.suffix.lower() != ".qcow2":
        raise HTTPException(status_code=400, detail="Kompaktowanie wspiera tylko qcow2")
    owners = disk_usage_by_domains(disk)
    running_owners = []
    for owner in owners:
        try:
            if "running" in vm_domain_state_label(owner.get("vm_id", "")).lower():
                running_owners.append(owner)
        except Exception:
            pass
    output = Path(data.output_path).resolve() if data.output_path else disk.with_name(f"{disk.stem}-compact{disk.suffix}").resolve()
    if not any(output == root or root in output.parents for root in enterprise_roots()):
        raise HTTPException(status_code=403, detail="Output poza dozwolonym katalogiem NEXUS")
    before = qemu_img_info_json(disk)
    commands = {
        "guest_linux": ["sudo", "fstrim", "-av"],
        "guest_windows": ["Optimize-Volume", "-DriveLetter", "C", "-ReTrim", "-Verbose"],
        "host_stopped_copy": ["virt-sparsify", "--compress", str(disk), str(output)],
        "host_stopped_inplace": ["virt-sparsify", "--in-place", str(disk)],
    }
    can_execute = bool(shutil.which("virt-sparsify")) and not running_owners
    plan = {
        "status": "planned",
        "vm_id": target,
        "source": str(disk),
        "output": str(output),
        "before": before,
        "owners": owners,
        "running_owners": running_owners,
        "can_execute": can_execute,
        "commands": commands,
        "warning": "Najpierw wykonaj TRIM w gosciu. Host compact wykonuj tylko gdy VM jest wylaczona.",
        "confirm_required": "COMPACT-QCOW2",
    }
    if data.dry_run:
        return plan
    if data.confirm != "COMPACT-QCOW2":
        raise HTTPException(status_code=412, detail={"message": "Wpisz confirm=COMPACT-QCOW2, aby wykonac kompaktowanie", **plan})
    if running_owners:
        raise HTTPException(status_code=409, detail={"message": "Dysk jest uzywany przez uruchomiona VM. Wylacz VM przed kompaktowaniem.", **plan})
    if not shutil.which("virt-sparsify"):
        raise HTTPException(status_code=501, detail={"message": "Brak virt-sparsify", **plan})
    if data.output_path and output.exists():
        raise HTTPException(status_code=409, detail="Plik wyjsciowy juz istnieje")
    command = commands["host_stopped_copy"] if data.output_path else commands["host_stopped_inplace"]
    result = xops_command(command, timeout=60 * 60 * 4)
    after = qemu_img_info_json(disk)
    audit = xops_audit("storage.compact", "ok" if result.get("ok") else "error", {"source": str(disk), "output": str(output), "result": result}, admin.get("username", "admin"))
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail={"message": "Kompaktowanie qcow2 nie powiodlo sie", "result": result, "audit": audit, **plan})
    return {"status": "ok", "vm_id": target, "source": str(disk), "output": str(output) if data.output_path else "", "before": before, "after": after, "result": result, "audit": audit}

@app.post("/api/vms/disk/attach", dependencies=[Depends(verify_token)])
async def vm_disk_attach(data: VMDiskAttachRequest, request: Request, user = Depends(verify_token)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Podpinanie dyskow jest teraz wspierane dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    authorize_vm_operation(target, user, "vm.disk.attach", request)
    result = attach_vm_disk(target, data.disk_path, data.bus, data.target, data.readonly, data.live, data.config)
    log_event(f"VM_DISK_ATTACH vm={target} disk={result.get('disk')} bus={result.get('bus')} target={result.get('target')} live={data.live} config={data.config} by={user.get('username')}")
    return {"status": "attached", "vm_id": target, **result}

@app.post("/api/vms/network", dependencies=[Depends(verify_token)])
async def vm_network_update(data: VMNetworkRequest, request: Request, user = Depends(verify_token)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Siec VM jest teraz wspierana dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    authorize_vm_operation(target, user, "vm.network.change", request)
    result = set_vm_network(target, data.enabled, data.network, data.model, data.live, data.config)
    log_event(f"VM_NETWORK vm={target} enabled={data.enabled} network={data.network} model={data.model} by={user.get('username')}")
    return {"status": "updated", "vm_id": target, **result}

@app.post("/api/vms/input/repair", dependencies=[Depends(verify_admin)])
async def vm_input_repair(data: VMInputRepairRequest, admin = Depends(verify_admin)):
    backend = detect_vm_backend() if data.backend == "auto" else data.backend
    if backend != "libvirt":
        raise HTTPException(status_code=400, detail="Naprawa myszy jest teraz wspierana dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    result = ensure_libvirt_input_devices(target, live=data.live, config=data.config)
    log_event(f"VM_INPUT_REPAIR requested vm={target} by={admin.get('username')}")
    return result

@app.post("/api/vms/media/repair", dependencies=[Depends(verify_admin)])
async def vm_media_repair(data: VMMediaRepairRequest, admin = Depends(verify_admin)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Naprawa mediow VM jest teraz wspierana dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    result = normalize_vm_cdrom_policy(target, live=data.live, config=data.config)
    log_event(f"VM_MEDIA_REPAIR vm={target} selected={(result.get('selected_installer') or {}).get('target')} by={admin.get('username')}")
    return result

@app.post("/api/vms/media/repair-all", dependencies=[Depends(verify_admin)])
async def vm_media_repair_all(data: VMMediaRepairAllRequest, admin = Depends(verify_admin)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Naprawa mediow VM jest teraz wspierana dla libvirt/KVM")
    items = []
    errors = []
    for name in libvirt_vm_names():
        try:
            items.append(normalize_vm_cdrom_policy(name, live=data.live, config=data.config))
        except Exception as exc:
            errors.append({"vm_id": name, "error": str(exc)})
    log_event(f"VM_MEDIA_REPAIR_ALL count={len(items)} errors={len(errors)} by={admin.get('username')}")
    return {"status": "ok" if not errors else "partial", "items": items, "errors": errors}

@app.get("/api/vms/logs", dependencies=[Depends(verify_token)])
async def vm_logs(vm_id: str, lines: int = 50, request: Request = None, user = Depends(verify_token)):
    target = safe_vm_target(vm_id)
    authorize_vm_operation(target, user, "vm.logs.read", request)
    path = vm_log_file(target)
    return {"vm_id": target, "path": str(path), "lines": max(1, min(int(lines or 50), 500)), "logs": tail_text(path, lines)}

@app.get("/api/vms/ports", dependencies=[Depends(verify_token)])
async def vm_ports(user = Depends(verify_token)):
    items = read_json(VM_PORT_FORWARDS_FILE, [])
    if normalize_role(user.get("role")) not in {"admin", "operator"}:
        scoped = []
        for item in items:
            access = vm_effective_access(item.get("vm_id", ""), user)
            if access.get("allowed") and "vm.read" in set(access.get("permissions") or []):
                scoped.append(item)
        items = scoped
    return {"items": items, "iptables": bool(iptables_path())}

@app.post("/api/vms/ports/create", dependencies=[Depends(verify_token)])
async def vm_port_create(data: VMPortForwardRequest, request: Request, user = Depends(verify_token)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Port forwarding jest teraz wspierany dla libvirt/KVM")
    target = safe_vm_target(data.vm_id)
    authorize_vm_operation(target, user, "vm.network.change", request)
    proto = safe_firewall_proto(data.proto)
    guest_ip = (data.guest_ip or detect_vm_guest_ip(target)).strip()
    if not re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", guest_ip):
        raise HTTPException(status_code=400, detail="Nie wykrylem IP VM. Wpisz IP goscia recznie.")
    existing = read_json(VM_PORT_FORWARDS_FILE, [])
    for row in existing:
        if int(row.get("host_port", 0)) == data.host_port and row.get("proto") == proto:
            raise HTTPException(status_code=409, detail="Ten port hosta jest juz zajety w regule NEXUS")
    item = {
        "id": uuid.uuid4().hex[:12],
        "vm_id": target,
        "guest_ip": guest_ip,
        "vm_port": int(data.vm_port),
        "host_port": int(data.host_port),
        "proto": proto,
        "comment": f"NEXUS-PF-{uuid.uuid4().hex[:10]}",
        "created_at": now_iso(),
    }
    apply_port_forward_rule(item)
    existing.insert(0, item)
    write_json(VM_PORT_FORWARDS_FILE, existing[:200])
    log_event(f"VM_PORT create vm={target} {proto} host={data.host_port} guest={guest_ip}:{data.vm_port} by={user.get('username')}")
    return item

@app.post("/api/vms/ports/delete", dependencies=[Depends(verify_token)])
async def vm_port_delete(data: VMPortForwardDeleteRequest, request: Request, user = Depends(verify_token)):
    items = read_json(VM_PORT_FORWARDS_FILE, [])
    found = None
    remaining = []
    for item in items:
        if item.get("id") == data.id:
            found = item
        else:
            remaining.append(item)
    if not found:
        raise HTTPException(status_code=404, detail="Nie znaleziono reguly")
    authorize_vm_operation(found.get("vm_id", ""), user, "vm.network.change", request)
    delete_port_forward_rule(found)
    write_json(VM_PORT_FORWARDS_FILE, remaining)
    log_event(f"VM_PORT delete id={data.id} by={user.get('username')}")
    return {"status": "deleted", "id": data.id}

@app.get("/api/vms/alerts/config", dependencies=[Depends(verify_token)])
async def vm_alert_config():
    data = read_json(VM_ALERTS_CONFIG_FILE, {"disk_threshold": 90, "webhook_url": ""})
    data["image_dir"] = str(LIBVIRT_IMAGE_DIR)
    return data

@app.post("/api/vms/alerts/config", dependencies=[Depends(verify_admin)])
async def vm_alert_config_update(data: VMAlertConfigRequest):
    config = {"disk_threshold": data.disk_threshold, "webhook_url": data.webhook_url.strip()}
    write_json(VM_ALERTS_CONFIG_FILE, config)
    return config

@app.post("/api/vms/alerts/check", dependencies=[Depends(verify_admin)])
async def vm_alert_check():
    config = read_json(VM_ALERTS_CONFIG_FILE, {"disk_threshold": 90, "webhook_url": ""})
    threshold = int(config.get("disk_threshold") or 90)
    triggered = []
    for label, path in [("root", Path("/")), ("libvirt", LIBVIRT_IMAGE_DIR)]:
        try:
            snap = disk_guard_snapshot(path, label)
            if snap["used_pct"] >= threshold:
                triggered.append(record_alert(
                    "Dysk przekroczyl prog",
                    f"{label} {path}: {snap['used_pct']}% zajete, wolne {snap['free_gb']} GB, prog {threshold}%",
                    "critical" if snap["used_pct"] >= 95 else "warn",
                    f"vm-disk-{label}",
                ))
        except Exception as exc:
            triggered.append(record_alert("Nie udalo sie sprawdzic dysku", f"{label}: {exc}", "warn", f"vm-disk-check-error-{label}"))

    code, output = run_vm_command(["virsh", "list", "--all", "--name"], timeout=10) if detect_vm_backend() == "libvirt" else (1, "")
    if code == 0:
        for name in [row.strip() for row in output.splitlines() if row.strip()]:
            state_code, state = run_vm_command(["virsh", "domstate", name, "--reason"], timeout=8)
            state_text = state.strip().lower() if state_code == 0 else ""
            if "paused" in state_text:
                level = "critical" if "io-error" in state_text or "i/o" in state_text else "warn"
                triggered.append(record_alert("VM jest wstrzymana", f"{name}: {state.strip() or 'paused'}", level, f"vm-paused-{name}"))
                continue
            if "running" not in state_text:
                continue
            pid = find_qemu_pid(name)
            if not pid:
                triggered.append(record_alert("VM bez procesu QEMU", f"{name} jest running wedlug virsh, ale nie widze procesu qemu.", "critical", f"vm-qemu-missing-{name}"))
            elif HAS_PSUTIL:
                try:
                    proc = psutil.Process(pid)
                    if proc.status().lower() in {"zombie", "dead"}:
                        triggered.append(record_alert("QEMU w stanie zombie/dead", f"{name} pid={pid} status={proc.status()}", "critical", f"vm-qemu-zombie-{name}"))
                except Exception:
                    pass
    return {"status": "checked", "triggered": triggered, "threshold": threshold, "image_dir": str(LIBVIRT_IMAGE_DIR)}

@app.post("/api/vms/guest-agent", dependencies=[Depends(verify_admin)])
async def vm_guest_agent(data: VMGuestAgentRequest, request: Request):
    target = safe_vm_target(data.vm_id)
    token_value = guest_agent_token(target)
    endpoint = f"{external_base_url(request)}/api/vms/guest-telemetry"
    telemetry = latest_guest_telemetry(target)
    return {
        "vm_id": target,
        "endpoint": endpoint,
        "token_tail": token_value[-8:],
        "linux_command": linux_guest_agent_script(target, token_value, endpoint),
        "windows_command": windows_guest_agent_script(target, token_value, endpoint),
        "telemetry": telemetry,
    }

@app.get("/api/vms/guest-telemetry", dependencies=[Depends(verify_token)])
async def vm_guest_telemetry_get(vm_id: str):
    target = safe_vm_target(vm_id)
    return {"vm_id": target, "telemetry": latest_guest_telemetry(target)}

@app.post("/api/vms/guest-telemetry")
async def vm_guest_telemetry_post(data: VMGuestTelemetryRequest):
    target = safe_vm_target(data.vm_id)
    agents = read_json(VM_GUEST_AGENTS_FILE, {})
    token_value = (agents.get(target) or {}).get("token", "")
    if not token_value or not hmac.compare_digest(token_value, data.token):
        raise HTTPException(status_code=401, detail="Niepoprawny token agenta VM")
    telemetry = {
        "vm_id": target,
        "hostname": data.hostname[:120],
        "os": data.os[:160],
        "cpu_percent": round(float(data.cpu_percent or 0), 1),
        "memory_percent": round(float(data.memory_percent or 0), 1),
        "memory_used_mb": round(float(data.memory_used_mb or 0), 1),
        "memory_total_mb": round(float(data.memory_total_mb or 0), 1),
        "disk_percent": round(float(data.disk_percent or 0), 1),
        "disk_used_gb": round(float(data.disk_used_gb or 0), 2),
        "disk_total_gb": round(float(data.disk_total_gb or 0), 2),
        "uptime_seconds": round(float(data.uptime_seconds or 0), 1),
        "ips": [str(ip)[:64] for ip in (data.ips or [])][:12],
        "received_at": now_iso(),
    }
    rows = read_json(VM_GUEST_TELEMETRY_FILE, {})
    rows[target] = telemetry
    write_json(VM_GUEST_TELEMETRY_FILE, rows)
    return {"status": "ok", "vm_id": target}

@app.get("/api/vms/console", dependencies=[Depends(verify_token)])
async def vm_console(vm_id: str, backend: str = "auto", request: Request = None, user = Depends(verify_token)):
    target = safe_vm_target(vm_id)
    authorize_vm_operation(target, user, "console.open", request)
    selected_backend = detect_vm_backend() if backend == "auto" else backend
    endpoint = detect_vnc_endpoint(selected_backend, target)
    input_repair = None
    if endpoint.get("backend") == "libvirt":
        try:
            input_repair = ensure_libvirt_input_devices(target, live=True, config=True)
        except Exception as exc:
            input_repair = {
                "status": "warning",
                "vm_id": target,
                "warnings": [str(getattr(exc, "detail", exc))[:500]],
            }
            log_event(f"VM_INPUT_PREFLIGHT warning vm={target}: {input_repair['warnings'][0]}")
    ticket, session = create_vnc_session(target, endpoint["backend"], user)
    return {
        "status": "ready",
        "backend": endpoint["backend"],
        "vm_id": target,
        "ws_path": f"/ws/vnc/{urllib.parse.quote(target, safe='')}?backend={urllib.parse.quote(endpoint['backend'], safe='')}&session={urllib.parse.quote(ticket, safe='')}",
        "session_expires_at": session["expires_at"],
        "session_ttl_seconds": VNC_SESSION_TTL_SECONDS,
        "vnc_host": endpoint["host"],
        "vnc_port": endpoint["port"],
        "input_repair": input_repair,
        "note": "VNC jest tunelowany przez krotkotrwala sesje noVNC NEXUS; surowy port nie jest wystawiany publicznie.",
    }

@app.websocket("/ws/vnc/{vm_id}")
async def vnc_websocket_proxy(websocket: WebSocket, vm_id: str, token: str = "", session: str = "", backend: str = "auto"):
    user = validate_vnc_session(session, vm_id, backend) if session else None
    if not user:
        user = SESSIONS.get(token or "")
    if not user:
        await websocket.accept()
        await websocket.close(code=1008)
        return
    user = sync_session_user(user) if user.get("vnc_scope") != "coop" else user
    user["last_seen"] = datetime.datetime.now().isoformat(timespec="seconds")

    try:
        if user.get("vnc_scope") == "coop":
            if "console.open" not in set(user.get("permissions") or []):
                raise HTTPException(status_code=403, detail="Bilet CO-OP nie ma dostepu do konsoli")
        else:
            authorize_vm_operation(vm_id, user, "console.open")
    except HTTPException:
        await websocket.accept()
        await websocket.close(code=1008)
        return

    try:
        endpoint = detect_vnc_endpoint(backend, vm_id)
    except Exception:
        await websocket.accept()
        await websocket.close(code=1011)
        return

    await websocket.accept()
    try:
        reader, writer = await asyncio.open_connection(endpoint["host"], endpoint["port"])
    except Exception:
        await websocket.close(code=1011)
        return

    log_event(f"VNC_CONSOLE open backend={endpoint['backend']} vm={endpoint['vm_id']} user={user.get('username')}")

    async def tcp_to_ws():
        try:
            while True:
                data = await reader.read(65536)
                if not data:
                    break
                await websocket.send_bytes(data)
        except Exception:
            pass

    async def ws_to_tcp():
        try:
            while True:
                message = await websocket.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                payload = message.get("bytes")
                if payload is None:
                    text = message.get("text")
                    payload = text.encode("latin1") if text is not None else b""
                if payload:
                    writer.write(payload)
                    await writer.drain()
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    tasks = [asyncio.create_task(tcp_to_ws()), asyncio.create_task(ws_to_tcp())]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass
    try:
        await websocket.close()
    except Exception:
        pass
    log_event(f"VNC_CONSOLE close backend={endpoint['backend']} vm={endpoint['vm_id']} user={user.get('username')}")

@app.get("/api/system/logs", dependencies=[Depends(verify_token)])
async def get_logs():
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f: return {"logs": "".join(f.readlines()[-100:])}
    except: return {"logs": "Błąd"}

# --- PLIKI ---
@app.post("/api/files/list", dependencies=[Depends(verify_token)])
async def list_files(request: Request):
    t = Path((await request.json()).get("path", str(BASE_DIR))).resolve()
    if not t.exists() or not t.is_dir(): t = BASE_DIR
    items = [{"name": i.name, "is_dir": i.is_dir(), "path": str(i), "size": i.stat().st_size if i.is_file() else 0} for i in t.iterdir()]
    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return {"current_path": str(t), "items": items}
@app.post("/api/files/read", dependencies=[Depends(verify_token)])
async def read_file(request: Request): return {"content": Path((await request.json()).get("path")).read_text(encoding="utf-8")}
@app.post("/api/files/save", dependencies=[Depends(verify_admin)])
async def save_file(data: FileContent): Path(data.path).write_text(data.content, encoding="utf-8"); return {"status": "success"}
@app.post("/api/files/upload", dependencies=[Depends(verify_admin)])
async def upload_file(path: str = Form(...), file: UploadFile = File(...)):
    target_dir = Path(path).resolve()
    if not target_dir.exists() or not target_dir.is_dir():
        raise HTTPException(status_code=400, detail="Niepoprawny katalog docelowy")
    safe_name = Path(file.filename or "upload.bin").name
    if not safe_name:
        raise HTTPException(status_code=400, detail="Niepoprawna nazwa pliku")
    target = target_dir / safe_name
    with open(target, "wb") as b:
        shutil.copyfileobj(file.file, b)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=500, detail="Upload zakonczony, ale plik nie istnieje w katalogu docelowym")
    expected_size = getattr(file, "size", None)
    actual_size = target.stat().st_size
    if expected_size is not None and int(expected_size) != actual_size:
        raise HTTPException(status_code=500, detail=f"Kontrola uploadu nie przeszla: zapisano {actual_size} B z {expected_size} B")
    return {"status": "success", "verified": True, "path": str(target), "name": safe_name, "size": actual_size}
@app.get("/api/files/download", dependencies=[Depends(verify_token)])
async def download_file(path: str): return FileResponse(path, filename=Path(path).name)

# --- TERMINAL ---
@app.post("/api/admin/cmd", dependencies=[Depends(verify_admin)])
async def exec_cmd(data: CommandRequest):
    global terminal_cwd
    c = data.command.strip()
    if not c: return {"output": "", "cwd": str(terminal_cwd)}
    try: r = subprocess.run(c, shell=True, cwd=terminal_cwd, capture_output=True, text=True); return {"output": r.stdout + r.stderr, "cwd": str(terminal_cwd)}
    except Exception as e: return {"output": str(e)+"\n", "cwd": str(terminal_cwd)}

# --- 💾 DOPRACOWANY SYSTEM BACKUPÓW 💾 ---
@app.post("/api/admin/backup/create", dependencies=[Depends(verify_admin)])
async def create_backup():
    n = f"nexus-{datetime.datetime.now().strftime('%Y-%m-%d-%H%M')}.tar.gz"
    subprocess.run(f"tar -czf {BACKUP_DIR / n} --exclude=./nexus2_backups --exclude=./venv --exclude=./.git -C {BASE_DIR} .", shell=True, check=True)
    return {"status": "success"}

@app.post("/api/admin/backup/restore", dependencies=[Depends(verify_admin)])
async def restore_backup(request: Request): 
    subprocess.run(["tar", "-xzf", str(BACKUP_DIR / (await request.json()).get("filename")), "-C", str(BASE_DIR)], check=True)
    return {"status": "success"}

@app.post("/api/admin/backup/delete", dependencies=[Depends(verify_admin)])
async def delete_backup(request: Request):
    fn = (await request.json()).get("filename")
    p = BACKUP_DIR / fn
    if p.exists(): p.unlink()
    return {"status": "success"}

@app.get("/api/admin/backups", dependencies=[Depends(verify_admin)])
async def get_backups():
    blist = []
    for f in BACKUP_DIR.iterdir():
        if f.name.endswith('.tar.gz'):
            stat = f.stat()
            dt = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y %H:%M')
            size_mb = f"{round(stat.st_size / (1024*1024), 2)} MB"
            blist.append({"filename": f.name, "date": dt, "size": size_mb, "timestamp": stat.st_mtime})
    blist.sort(key=lambda x: x["timestamp"], reverse=True)
    return blist

def run_server_backup_job(job_id: str, archive: Path):
    job = SERVER_BACKUP_JOBS[job_id]
    part = archive.with_suffix(archive.suffix + ".part")
    excludes = [
        "/proc",
        "/sys",
        "/dev",
        "/run",
        "/tmp",
        "/var/tmp",
        "/mnt",
        "/media",
        "/lost+found",
        str(BACKUP_DIR),
        str(SERVER_BACKUP_DIR),
        "/swapfile",
    ]
    try:
        SERVER_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        if part.exists():
            part.unlink()
        command = [
            "tar",
            "--ignore-failed-read",
            "--warning=no-file-changed",
            "--numeric-owner",
            "-czf",
            str(part),
        ]
        for item in excludes:
            command.append(f"--exclude={item}")
        command.extend(["-C", "/", "."])
        job.update({"status": "running", "started_at": now_iso(), "archive": str(archive), "excludes": excludes})
        process = subprocess.run(command, capture_output=True, text=True, timeout=60 * 60 * 6)
        output = ((process.stdout or "") + (process.stderr or "")).strip()
        if process.returncode != 0:
            raise RuntimeError(output[-4000:] or f"tar exit {process.returncode}")
        part.replace(archive)
        job.update({
            "status": "done",
            "finished_at": now_iso(),
            "size": fmt_size(archive.stat().st_size),
            "size_bytes": archive.stat().st_size,
            "output": output[-2000:],
        })
        log_event(f"SERVER_BACKUP done {archive.name} {job.get('size')}")
    except Exception as exc:
        try:
            if part.exists():
                part.unlink()
        except Exception:
            pass
        job.update({"status": "error", "finished_at": now_iso(), "error": str(exc)[-4000:]})
        log_event(f"SERVER_BACKUP error {archive.name}: {exc}")

@app.post("/api/admin/server-backup/create", dependencies=[Depends(verify_admin)])
async def create_server_backup(background_tasks: BackgroundTasks):
    active = [job for job in SERVER_BACKUP_JOBS.values() if job.get("status") in {"queued", "running"}]
    if active:
        raise HTTPException(status_code=409, detail="Backup calego serwera juz trwa")
    archive = SERVER_BACKUP_DIR / f"server-full-{datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')}.tar.gz"
    job_id = uuid.uuid4().hex[:12]
    SERVER_BACKUP_JOBS[job_id] = {
        "id": job_id,
        "status": "queued",
        "archive": str(archive),
        "filename": archive.name,
        "created_at": now_iso(),
    }
    background_tasks.add_task(run_server_backup_job, job_id, archive)
    log_event(f"SERVER_BACKUP queued {archive.name}")
    return SERVER_BACKUP_JOBS[job_id]

@app.get("/api/admin/server-backups", dependencies=[Depends(verify_admin)])
async def list_server_backups():
    files = []
    for path in SERVER_BACKUP_DIR.glob("*.tar.gz"):
        try:
            files.append(backup_file_row(path))
        except Exception:
            pass
    files.sort(key=lambda item: item["timestamp"], reverse=True)
    jobs = sorted(SERVER_BACKUP_JOBS.values(), key=lambda item: item.get("created_at", ""), reverse=True)
    return {"root": str(SERVER_BACKUP_DIR), "files": files, "jobs": jobs}

@app.post("/api/admin/server-backup/delete", dependencies=[Depends(verify_admin)])
async def delete_server_backup(request: Request):
    filename = Path((await request.json()).get("filename", "")).name
    if not filename.endswith(".tar.gz"):
        raise HTTPException(status_code=400, detail="Niepoprawna nazwa backupu")
    target = (SERVER_BACKUP_DIR / filename).resolve()
    if SERVER_BACKUP_DIR.resolve() not in target.parents:
        raise HTTPException(status_code=400, detail="Niepoprawna sciezka")
    if target.exists():
        target.unlink()
    return {"status": "success"}

# --- GOOGLE DRIVE / RCLONE CLOUD DRIVE ---
def rclone_binary():
    return shutil.which("rclone")

def safe_rclone_remote(value: str):
    remote = re.sub(r"[^A-Za-z0-9_-]+", "", (value or CLOUD_DRIVE_DEFAULT_REMOTE).strip())[:40]
    return remote or CLOUD_DRIVE_DEFAULT_REMOTE

def safe_cloud_root(value: str):
    text = (value or CLOUD_DRIVE_DEFAULT_ROOT).strip().replace("\\", "/").strip("/")
    if not text or ":" in text or ".." in text.split("/"):
        return CLOUD_DRIVE_DEFAULT_ROOT
    return text[:160]

def cloud_source_map():
    return {
        "backups": BACKUP_DIR,
        "server_backups": SERVER_BACKUP_DIR,
        "isos": LIBVIRT_ISO_DIR,
        "media": MEDIA_DIR,
        "vm_images": LIBVIRT_IMAGE_DIR,
    }

def read_rclone_remotes():
    exe = rclone_binary()
    if not exe:
        return []
    code, output = run_vm_command([exe, "listremotes"], timeout=10)
    if code != 0:
        return []
    return [line.strip().rstrip(":") for line in output.splitlines() if line.strip()]

def rclone_configured(remote: str):
    return safe_rclone_remote(remote) in read_rclone_remotes()

def rclone_remote_path(remote: str, root: str, suffix: str = ""):
    remote = safe_rclone_remote(remote)
    root = safe_cloud_root(root)
    suffix = (suffix or "").strip().replace("\\", "/").strip("/")
    if suffix and (".." in suffix.split("/") or ":" in suffix):
        raise HTTPException(status_code=400, detail="Niepoprawna sciezka Drive")
    path = root if not suffix else f"{root}/{suffix}"
    return f"{remote}:{path}"

def safe_cloud_dest_folder(value: str):
    text = (value or "server-files").strip().replace("\\", "/").strip("/")
    if not text:
        return "server-files"
    parts = [part for part in text.split("/") if part]
    if any(part in {".", ".."} or ":" in part for part in parts):
        raise HTTPException(status_code=400, detail="Niepoprawny folder docelowy Google Drive")
    return "/".join(parts)[:240] or "server-files"

def allowed_cloud_push_path(value: str):
    raw = (value or "").strip()
    if raw.startswith("~"):
        raw = str(Path(raw).expanduser())
    target = Path(raw).resolve()
    if not target.exists():
        raise HTTPException(status_code=404, detail="Plik albo folder nie istnieje na serwerze")
    blocked_roots = [Path("/proc"), Path("/sys"), Path("/dev"), Path("/run")]
    if any(target == root or root in target.parents for root in blocked_roots):
        raise HTTPException(status_code=400, detail="Tej sciezki systemowej nie wysylam do Google Drive")
    blocked_files = {PASS_FILE.resolve(), GEMINI_KEY_FILE.resolve(), RCLONE_CONFIG_FILE.resolve()}
    if target in blocked_files:
        raise HTTPException(status_code=400, detail="Ta sciezka zawiera sekret i jest zablokowana")
    if any(part in {".ssh", ".gnupg"} for part in target.parts):
        raise HTTPException(status_code=400, detail="Foldery kluczy prywatnych sa zablokowane")
    return target

def write_google_drive_rclone_config(remote: str, token_json: str):
    remote = safe_rclone_remote(remote)
    token_json = (token_json or "").strip()
    try:
        token = json.loads(token_json)
    except Exception:
        raise HTTPException(status_code=400, detail="Token nie jest poprawnym JSON z rclone authorize")
    if not token.get("access_token") and not token.get("refresh_token"):
        raise HTTPException(status_code=400, detail="Token JSON nie zawiera access_token/refresh_token")
    RCLONE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.RawConfigParser()
    parser.optionxform = str
    if RCLONE_CONFIG_FILE.exists():
        parser.read(RCLONE_CONFIG_FILE)
    if not parser.has_section(remote):
        parser.add_section(remote)
    parser.set(remote, "type", "drive")
    parser.set(remote, "scope", "drive")
    parser.set(remote, "token", json.dumps(token, separators=(",", ":")))
    with open(RCLONE_CONFIG_FILE, "w", encoding="utf-8") as fh:
        parser.write(fh)
    try:
        os.chmod(RCLONE_CONFIG_FILE, 0o600)
    except Exception:
        pass
    log_event(f"CLOUD_DRIVE_CONFIG remote={remote}")
    return remote

def run_cloud_drive_sync(job_id: str, source_key: str, remote: str, root: str, mode: str):
    job = CLOUD_DRIVE_JOBS[job_id]
    exe = rclone_binary()
    if not exe:
        job.update({"status": "error", "finished_at": now_iso(), "error": "rclone nie jest zainstalowany"})
        return
    source_map = cloud_source_map()
    source = source_map.get(source_key)
    if not source or not source.exists():
        job.update({"status": "error", "finished_at": now_iso(), "error": "Niepoprawne zrodlo synchronizacji"})
        return
    if not rclone_configured(remote):
        job.update({"status": "error", "finished_at": now_iso(), "error": f"Remote {remote} nie jest skonfigurowany"})
        return
    dest = rclone_remote_path(remote, root, source_key)
    action = "copy" if mode not in {"sync", "move"} else mode
    if action == "move" and source_key not in {"backups", "server_backups"}:
        action = "copy"
    command = [
        exe,
        action,
        str(source),
        dest,
        "--create-empty-src-dirs",
        "--transfers", "4",
        "--checkers", "8",
        "--stats", "10s",
        "--log-level", "INFO",
    ]
    job.update({"status": "running", "started_at": now_iso(), "source_path": str(source), "dest": dest, "command": " ".join(command)})
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=60 * 60 * 12)
        output = ((process.stdout or "") + (process.stderr or "")).strip()
        if process.returncode != 0:
            raise RuntimeError(output[-5000:] or f"rclone exit {process.returncode}")
        job.update({"status": "done", "finished_at": now_iso(), "output": output[-5000:]})
        log_event(f"CLOUD_DRIVE_SYNC done source={source_key} dest={dest}")
    except Exception as exc:
        job.update({"status": "error", "finished_at": now_iso(), "error": str(exc)[-5000:]})
        log_event(f"CLOUD_DRIVE_SYNC error source={source_key}: {exc}")

def run_cloud_drive_push(job_id: str, source_path: str, remote: str, root: str, dest_folder: str, mode: str):
    job = CLOUD_DRIVE_JOBS[job_id]
    exe = rclone_binary()
    if not exe:
        job.update({"status": "error", "finished_at": now_iso(), "error": "rclone nie jest zainstalowany"})
        return
    try:
        source = allowed_cloud_push_path(source_path)
        if not rclone_configured(remote):
            job.update({"status": "error", "finished_at": now_iso(), "error": f"Remote {remote} nie jest skonfigurowany"})
            return
        action = "move" if mode == "move" else "copy"
        dest_suffix = f"{safe_cloud_dest_folder(dest_folder)}/{source.name}"
        dest = rclone_remote_path(remote, root, dest_suffix)
        command = [
            exe,
            "moveto" if source.is_file() and action == "move" else "copyto" if source.is_file() else action,
            str(source),
            dest,
            "--create-empty-src-dirs",
            "--transfers", "4",
            "--checkers", "8",
            "--stats", "10s",
            "--log-level", "INFO",
        ]
        job.update({
            "status": "running",
            "started_at": now_iso(),
            "source_path": str(source),
            "source": source.name,
            "dest": dest,
            "mode": action,
            "command": " ".join(command),
            "is_dir": source.is_dir(),
        })
        process = subprocess.run(command, capture_output=True, text=True, timeout=60 * 60 * 12)
        output = ((process.stdout or "") + (process.stderr or "")).strip()
        if process.returncode != 0:
            raise RuntimeError(output[-5000:] or f"rclone exit {process.returncode}")
        job.update({"status": "done", "finished_at": now_iso(), "output": output[-5000:]})
        log_event(f"CLOUD_DRIVE_PUSH done source={source} dest={dest}")
    except Exception as exc:
        job.update({"status": "error", "finished_at": now_iso(), "error": str(exc)[-5000:]})
        log_event(f"CLOUD_DRIVE_PUSH error source={source_path}: {exc}")

@app.get("/api/cloud-drive/status", dependencies=[Depends(verify_token)])
async def cloud_drive_status():
    exe = rclone_binary()
    version = ""
    if exe:
        code, output = run_vm_command([exe, "version"], timeout=10)
        version = "\n".join(output.splitlines()[:3]) if code == 0 else output[:300]
    remotes = read_rclone_remotes()
    remote = CLOUD_DRIVE_DEFAULT_REMOTE
    about = {}
    if exe and remote in remotes:
        code, output = run_vm_command([exe, "about", f"{remote}:", "--json"], timeout=30)
        if code == 0:
            try:
                about = json.loads(output)
            except Exception:
                about = {"raw": output[:500]}
        else:
            about = {"error": output[-500:]}
    sources = []
    for key, path in cloud_source_map().items():
        try:
            size = sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.exists() else 0
        except Exception:
            size = 0
        sources.append({"id": key, "path": str(path), "exists": path.exists(), "size_bytes": size, "size": fmt_size(size)})
    jobs = sorted(CLOUD_DRIVE_JOBS.values(), key=lambda item: item.get("created_at", ""), reverse=True)[:20]
    return {
        "installed": bool(exe),
        "binary": exe or "",
        "version": version,
        "config_path": str(RCLONE_CONFIG_FILE),
        "remotes": remotes,
        "default_remote": remote,
        "configured": remote in remotes,
        "root_folder": CLOUD_DRIVE_DEFAULT_ROOT,
        "about": about,
        "sources": sources,
        "jobs": jobs,
    }

@app.post("/api/cloud-drive/config", dependencies=[Depends(verify_admin)])
async def cloud_drive_config(data: CloudDriveConfigRequest):
    if not rclone_binary():
        raise HTTPException(status_code=503, detail="rclone nie jest zainstalowany na VPS")
    remote = write_google_drive_rclone_config(data.remote, data.token_json)
    return {"status": "saved", "remote": remote, "config_path": str(RCLONE_CONFIG_FILE), "root_folder": safe_cloud_root(data.root_folder)}

@app.get("/api/cloud-drive/list", dependencies=[Depends(verify_token)])
async def cloud_drive_list(path: str = "", remote: str = CLOUD_DRIVE_DEFAULT_REMOTE, root_folder: str = CLOUD_DRIVE_DEFAULT_ROOT):
    exe = rclone_binary()
    if not exe:
        raise HTTPException(status_code=503, detail="rclone nie jest zainstalowany")
    remote = safe_rclone_remote(remote)
    if not rclone_configured(remote):
        raise HTTPException(status_code=409, detail=f"Remote {remote} nie jest skonfigurowany")
    target = rclone_remote_path(remote, root_folder, path)
    code, output = run_vm_command([exe, "lsjson", target, "--max-depth", "1"], timeout=60)
    if code != 0:
        raise HTTPException(status_code=500, detail=output[-1000:])
    try:
        items = json.loads(output or "[]")
    except Exception:
        items = []
    for item in items:
        item["size_label"] = fmt_size(item.get("Size") or 0)
    return {"path": path, "target": target, "items": items}

@app.post("/api/cloud-drive/sync", dependencies=[Depends(verify_admin)])
async def cloud_drive_sync(data: CloudDriveSyncRequest, background_tasks: BackgroundTasks):
    source_key = data.source.strip()
    if source_key not in cloud_source_map():
        raise HTTPException(status_code=400, detail="Nieznane zrodlo synchronizacji")
    remote = safe_rclone_remote(data.remote)
    root = safe_cloud_root(data.root_folder)
    if not rclone_binary():
        raise HTTPException(status_code=503, detail="rclone nie jest zainstalowany")
    if not rclone_configured(remote):
        raise HTTPException(status_code=409, detail=f"Remote {remote} nie jest skonfigurowany")
    job_id = uuid.uuid4().hex[:12]
    CLOUD_DRIVE_JOBS[job_id] = {
        "id": job_id,
        "status": "queued",
        "source": source_key,
        "remote": remote,
        "root_folder": root,
        "mode": data.mode,
        "created_at": now_iso(),
    }
    background_tasks.add_task(run_cloud_drive_sync, job_id, source_key, remote, root, data.mode)
    log_event(f"CLOUD_DRIVE_SYNC queued source={source_key} remote={remote}")
    return CLOUD_DRIVE_JOBS[job_id]

@app.post("/api/cloud-drive/push", dependencies=[Depends(verify_admin)])
async def cloud_drive_push(data: CloudDrivePushRequest, background_tasks: BackgroundTasks):
    source = allowed_cloud_push_path(data.path)
    remote = safe_rclone_remote(data.remote)
    root = safe_cloud_root(data.root_folder)
    dest_folder = safe_cloud_dest_folder(data.dest_folder)
    mode = "move" if data.mode == "move" else "copy"
    if not rclone_binary():
        raise HTTPException(status_code=503, detail="rclone nie jest zainstalowany")
    if not rclone_configured(remote):
        raise HTTPException(status_code=409, detail=f"Remote {remote} nie jest skonfigurowany")
    job_id = uuid.uuid4().hex[:12]
    CLOUD_DRIVE_JOBS[job_id] = {
        "id": job_id,
        "status": "queued",
        "kind": "push",
        "source": source.name,
        "source_path": str(source),
        "remote": remote,
        "root_folder": root,
        "dest_folder": dest_folder,
        "mode": mode,
        "size": fmt_size(source.stat().st_size) if source.is_file() else "folder",
        "created_at": now_iso(),
    }
    background_tasks.add_task(run_cloud_drive_push, job_id, str(source), remote, root, dest_folder, mode)
    log_event(f"CLOUD_DRIVE_PUSH queued source={source} remote={remote} folder={dest_folder}")
    return CLOUD_DRIVE_JOBS[job_id]

@app.get("/api/cloud-drive/jobs", dependencies=[Depends(verify_token)])
async def cloud_drive_jobs():
    jobs = sorted(CLOUD_DRIVE_JOBS.values(), key=lambda item: item.get("created_at", ""), reverse=True)
    return {"jobs": jobs}

# --- ENTERPRISE MODULES: SHIELD / TIME MACHINE / CLOUD INIT / INTEGRATIONS / HARDWARE ---
def public_api_token(row):
    clean = dict(row)
    clean.pop("token_hash", None)
    return clean

def validate_api_access_token(raw: str, scope: str, vm_id: str = ""):
    digest = token_hash(raw or "")
    now = datetime.datetime.now()
    rows = read_json(API_TOKENS_FILE, [])
    for row in rows:
        if row.get("revoked"):
            continue
        if not hmac.compare_digest(row.get("token_hash", ""), digest):
            continue
        try:
            if datetime.datetime.fromisoformat(row.get("expires_at", "")) < now:
                raise HTTPException(status_code=403, detail="API token wygasl")
        except ValueError:
            pass
        scopes = row.get("scopes") or []
        if scope not in scopes and "*" not in scopes:
            raise HTTPException(status_code=403, detail="API token nie ma wymaganego scope")
        allowed_vm = row.get("vm_id") or ""
        if allowed_vm and vm_id and allowed_vm != vm_id:
            raise HTTPException(status_code=403, detail="API token nie ma dostepu do tej VM")
        row["last_used_at"] = now_iso()
        write_json(API_TOKENS_FILE, rows)
        return row
    raise HTTPException(status_code=401, detail="Niepoprawny API token")

def firewall_comment(rule_id: str):
    return f"NEXUS-SHIELD-{re.sub(r'[^A-Za-z0-9_-]+', '', rule_id)[:32]}"

def normalize_firewall_rule(data: ShieldFirewallRuleRequest):
    action = (data.action or "block").lower()
    if action not in {"allow", "block"}:
        raise HTTPException(status_code=400, detail="Akcja firewall musi byc allow albo block")
    proto = (data.proto or "all").lower()
    if proto not in {"all", "tcp", "udp", "icmp"}:
        raise HTTPException(status_code=400, detail="Proto: all/tcp/udp/icmp")
    source = (data.source or "").strip()
    if not re.fullmatch(r"([0-9]{1,3}\.){3}[0-9]{1,3}(/\d{1,2})?", source):
        raise HTTPException(status_code=400, detail="Na razie firewall przyjmuje IPv4 albo CIDR, np. 1.2.3.4/32")
    return action, source, proto, int(data.port or 0)

def apply_firewall_rule(row, delete=False):
    exe = iptables_path()
    if not exe:
        return {"applied": False, "output": "iptables/nft wrapper nie znaleziony"}
    chain = "INPUT"
    target = "ACCEPT" if row.get("action") == "allow" else "DROP"
    command = [exe, "-D" if delete else "-I", chain]
    if row.get("proto") and row.get("proto") != "all":
        command.extend(["-p", row["proto"]])
    if row.get("source"):
        command.extend(["-s", row["source"]])
    if int(row.get("port") or 0) > 0 and row.get("proto") in {"tcp", "udp"}:
        command.extend(["--dport", str(int(row["port"]))])
    command.extend(["-m", "comment", "--comment", firewall_comment(row["id"]), "-j", target])
    code, output = run_vm_command(command, timeout=15)
    return {"applied": code == 0, "code": code, "output": output.strip(), "command": " ".join(command)}

@app.get("/api/shield/status", dependencies=[Depends(verify_token)])
async def shield_status():
    rules = read_json(SHIELD_RULES_FILE, [])
    forwards = read_json(VM_PORT_FORWARDS_FILE, [])
    iface_rows = []
    try:
        for line in Path("/proc/net/dev").read_text().splitlines()[2:]:
            name, rest = line.split(":", 1)
            parts = rest.split()
            iface_rows.append({
                "name": name.strip(),
                "rx_bytes": int(parts[0]),
                "tx_bytes": int(parts[8]),
                "rx": fmt_size(int(parts[0])),
                "tx": fmt_size(int(parts[8])),
            })
    except Exception:
        pass
    return {"iptables": bool(iptables_path()), "rules": rules, "port_forwards": forwards, "interfaces": iface_rows}

@app.post("/api/shield/firewall/rules", dependencies=[Depends(verify_admin)])
async def shield_firewall_add(data: ShieldFirewallRuleRequest, admin = Depends(verify_admin)):
    action, source, proto, port = normalize_firewall_rule(data)
    rows = read_json(SHIELD_RULES_FILE, [])
    row = {"id": uuid.uuid4().hex[:12], "action": action, "source": source, "proto": proto, "port": port, "note": data.note[:180], "created_at": now_iso(), "created_by": admin.get("username", "admin"), "system": {}}
    if data.apply:
        row["system"] = apply_firewall_rule(row)
    rows.insert(0, row)
    write_json(SHIELD_RULES_FILE, rows[:500])
    record_alert("NEXUS SHIELD rule", f"{action.upper()} {source} proto={proto} port={port or '*'}", "info", f"shield-rule-{row['id']}")
    return row

@app.post("/api/shield/firewall/delete", dependencies=[Depends(verify_admin)])
async def shield_firewall_delete(data: ShieldRuleDeleteRequest):
    rows = read_json(SHIELD_RULES_FILE, [])
    row = next((item for item in rows if item.get("id") == data.id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Regula nie istnieje")
    result = apply_firewall_rule(row, delete=True) if data.remove_system else {"applied": False, "output": "usunieto tylko z panelu"}
    rows = [item for item in rows if item.get("id") != data.id]
    write_json(SHIELD_RULES_FILE, rows)
    return {"status": "deleted", "system": result}

@app.get("/api/time-machine/policies", dependencies=[Depends(verify_token)])
async def time_machine_policies():
    return {"items": read_json(TIME_MACHINE_FILE, [])}

@app.post("/api/time-machine/policies", dependencies=[Depends(verify_admin)])
async def time_machine_policy_save(data: TimeMachinePolicyRequest, admin = Depends(verify_admin)):
    target = safe_vm_target(data.vm_id)
    if not re.fullmatch(r"\d{2}:\d{2}", data.hour or ""):
        raise HTTPException(status_code=400, detail="Godzina w formacie HH:MM")
    rows = read_json(TIME_MACHINE_FILE, [])
    row = {"id": uuid.uuid4().hex[:12], "vm_id": target, "label": safe_snapshot_name(data.label or "auto"), "hour": data.hour, "max_keep": int(data.max_keep), "enabled": bool(data.enabled), "created_at": now_iso(), "created_by": admin.get("username", "admin")}
    rows.insert(0, row)
    write_json(TIME_MACHINE_FILE, rows[:200])
    return row

@app.post("/api/time-machine/run", dependencies=[Depends(verify_admin)])
async def time_machine_run(data: TimeMachineRunRequest):
    rows = read_json(TIME_MACHINE_FILE, [])
    policy = next((item for item in rows if item.get("id") == data.id), None)
    if not policy:
        raise HTTPException(status_code=404, detail="Polityka snapshotu nie istnieje")
    target = safe_vm_target(policy["vm_id"])
    snap = safe_snapshot_name(f"{policy.get('label','auto')}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}")
    code, output = run_vm_command(["virsh", "snapshot-create-as", "--domain", target, "--name", snap, "--description", f"NEXUS Time Machine {now_iso()}", "--atomic"], timeout=300)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Snapshot nie powstal")
    code_list, names = run_vm_command(["virsh", "snapshot-list", target, "--name"], timeout=30)
    removed = []
    if code_list == 0:
        prefix = safe_snapshot_name(policy.get("label", "auto"))
        candidates = [name.strip() for name in names.splitlines() if name.strip().startswith(prefix)]
        for old in sorted(candidates)[:-int(policy.get("max_keep", 3))]:
            run_vm_command(["virsh", "snapshot-delete", target, old], timeout=120)
            removed.append(old)
    policy["last_run"] = now_iso()
    policy["last_snapshot"] = snap
    write_json(TIME_MACHINE_FILE, rows)
    return {"status": "created", "vm_id": target, "snapshot": snap, "removed": removed}

@app.post("/api/time-machine/delete", dependencies=[Depends(verify_admin)])
async def time_machine_delete(data: TimeMachineRunRequest):
    rows = [item for item in read_json(TIME_MACHINE_FILE, []) if item.get("id") != data.id]
    write_json(TIME_MACHINE_FILE, rows)
    return {"status": "deleted"}

def run_time_machine_policy(policy: dict, rows: list):
    target = safe_vm_target(policy["vm_id"])
    snap = safe_snapshot_name(f"{policy.get('label','auto')}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}")
    code, output = run_vm_command(["virsh", "snapshot-create-as", "--domain", target, "--name", snap, "--description", f"NEXUS Time Machine {now_iso()}", "--atomic"], timeout=300)
    if code != 0:
        policy["last_error"] = (output or "Snapshot nie powstal").strip()[:500]
        policy["last_error_at"] = now_iso()
        write_json(TIME_MACHINE_FILE, rows)
        record_alert("TIME MACHINE snapshot failed", f"{target}: {policy['last_error']}", "warn", f"time-machine-{target}-failed")
        return {"status": "error", "vm_id": target, "error": policy["last_error"]}
    code_list, names = run_vm_command(["virsh", "snapshot-list", target, "--name"], timeout=30)
    removed = []
    if code_list == 0:
        prefix = safe_snapshot_name(policy.get("label", "auto"))
        candidates = [name.strip() for name in names.splitlines() if name.strip().startswith(prefix)]
        for old in sorted(candidates)[:-int(policy.get("max_keep", 3))]:
            run_vm_command(["virsh", "snapshot-delete", target, old], timeout=120)
            removed.append(old)
    policy["last_run"] = now_iso()
    policy["last_snapshot"] = snap
    policy.pop("last_error", None)
    write_json(TIME_MACHINE_FILE, rows)
    send_webhook_event("snapshot.created", {"vm_id": target, "snapshot": snap, "removed": removed})
    return {"status": "created", "vm_id": target, "snapshot": snap, "removed": removed}

async def time_machine_scheduler_loop():
    while True:
        try:
            rows = read_json(TIME_MACHINE_FILE, [])
            now = datetime.datetime.now()
            for policy in rows:
                if not policy.get("enabled", True):
                    continue
                hour = str(policy.get("hour") or "03:00")
                if not re.fullmatch(r"\d{2}:\d{2}", hour):
                    continue
                hh, mm = [int(x) for x in hour.split(":")]
                due = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
                last = iso_dt(policy.get("last_run"))
                if now >= due and (not last or last.date() < now.date()):
                    await asyncio.to_thread(run_time_machine_policy, policy, rows)
        except Exception as exc:
            log_event(f"TIME_MACHINE scheduler error: {exc}")
        await asyncio.sleep(60)

@app.on_event("startup")
async def start_time_machine_scheduler():
    global TIME_MACHINE_SCHEDULER_STARTED
    if TIME_MACHINE_SCHEDULER_STARTED:
        return
    TIME_MACHINE_SCHEDULER_STARTED = True
    asyncio.create_task(time_machine_scheduler_loop())

async def vm_billing_scheduler_loop():
    while True:
        sleep_seconds = 60
        try:
            store = vm_billing_store()
            sleep_seconds = max(10, min(3600, int(store.get("tick_seconds", 60) or 60)))
            if bool(store.get("scheduler", {}).get("enabled", True)):
                await asyncio.to_thread(vm_billing_live_public)
            try:
                policy = phase2_policy() if "phase2_policy" in globals() else {}
                armed = bool(policy.get("enabled")) and not bool(policy.get("dry_run")) and str(policy.get("confirm") or "") == "EXECUTE-AUTONOMY"
                if armed and (bool(policy.get("auto_suspend")) or bool(policy.get("ram_autoscale"))) and "phase2_autonomy_tick" in globals():
                    await phase2_autonomy_tick(execute=True, actor="nxc-scheduler")
            except Exception as exc:
                log_event(f"NXC autonomy tick skipped: {exc}")
        except Exception as exc:
            try:
                store = vm_billing_store()
                store.setdefault("scheduler", {})["last_status"] = f"error: {str(exc)[:180]}"
                store.setdefault("scheduler", {})["last_error_at"] = now_iso()
                save_vm_billing(store)
            except Exception:
                pass
            log_event(f"NXC billing scheduler error: {exc}")
        await asyncio.sleep(sleep_seconds)

@app.on_event("startup")
async def start_vm_billing_scheduler():
    global VM_BILLING_SCHEDULER_STARTED
    if VM_BILLING_SCHEDULER_STARTED:
        return
    VM_BILLING_SCHEDULER_STARTED = True
    asyncio.create_task(vm_billing_scheduler_loop())

@app.get("/api/cloud-init/recipes", dependencies=[Depends(verify_token)])
async def cloud_init_recipes():
    return {"items": read_json(CLOUD_INIT_FILE, [])}

@app.post("/api/cloud-init/recipes", dependencies=[Depends(verify_admin)])
async def cloud_init_recipe_save(data: CloudInitRecipeRequest, admin = Depends(verify_admin)):
    rows = read_json(CLOUD_INIT_FILE, [])
    row = {"id": uuid.uuid4().hex[:12], "name": data.name[:80], "kind": data.kind[:20], "body": data.body, "ssh_key": data.ssh_key, "created_at": now_iso(), "created_by": admin.get("username", "admin")}
    rows.insert(0, row)
    write_json(CLOUD_INIT_FILE, rows[:200])
    return row

@app.post("/api/cloud-init/delete", dependencies=[Depends(verify_admin)])
async def cloud_init_recipe_delete(data: TimeMachineRunRequest):
    rows = [item for item in read_json(CLOUD_INIT_FILE, []) if item.get("id") != data.id]
    write_json(CLOUD_INIT_FILE, rows)
    return {"status": "deleted"}

@app.post("/api/cloud-init/apply", dependencies=[Depends(verify_admin)])
async def cloud_init_apply(data: CloudInitApplyRequest):
    target = safe_vm_target(data.vm_id)
    rows = read_json(CLOUD_INIT_FILE, [])
    recipe = next((item for item in rows if item.get("id") == data.recipe_id), None)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe nie istnieje")
    script = recipe.get("body", "")
    if recipe.get("ssh_key"):
        script = f"mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo {json.dumps(recipe['ssh_key'])} >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys\n" + script
    payload = {"execute": "guest-exec", "arguments": {"path": "/bin/bash", "arg": ["-lc", script], "capture-output": True}}
    code, output = run_vm_command(["virsh", "qemu-agent-command", target, json.dumps(payload)], timeout=30)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "QEMU Guest Agent nie wykonal recipe")
    return {"status": "sent", "vm_id": target, "recipe": recipe.get("name"), "output": output.strip()}

@app.get("/api/integrations/tokens", dependencies=[Depends(verify_admin)])
async def integration_tokens():
    return {"items": [public_api_token(row) for row in read_json(API_TOKENS_FILE, [])]}

@app.post("/api/integrations/tokens", dependencies=[Depends(verify_admin)])
async def integration_token_create(data: ApiTokenCreateRequest, admin = Depends(verify_admin)):
    raw = "nxapi_" + secrets.token_urlsafe(32)
    scopes = [scope for scope in data.scopes if re.fullmatch(r"[a-z0-9_.:-]{2,64}", scope or "")][:20] or ["vm.action"]
    row = {"id": uuid.uuid4().hex[:12], "name": data.name[:80], "preview": raw[:10] + "..." + raw[-6:], "token_hash": token_hash(raw), "scopes": scopes, "vm_id": safe_vm_target(data.vm_id) if data.vm_id else "", "created_at": now_iso(), "created_by": admin.get("username", "admin"), "expires_at": (datetime.datetime.now() + datetime.timedelta(days=int(data.days))).isoformat(timespec="seconds"), "revoked": False}
    rows = read_json(API_TOKENS_FILE, [])
    rows.insert(0, row)
    write_json(API_TOKENS_FILE, rows[:500])
    return {"status": "created", "token": raw, "record": public_api_token(row)}

@app.post("/api/integrations/tokens/revoke", dependencies=[Depends(verify_admin)])
async def integration_token_revoke(data: ApiTokenRevokeRequest):
    rows = read_json(API_TOKENS_FILE, [])
    for row in rows:
        if row.get("id") == data.id:
            row["revoked"] = True
            row["revoked_at"] = now_iso()
    write_json(API_TOKENS_FILE, rows)
    return {"status": "revoked"}

@app.post("/api/external/vm/action")
async def external_vm_action(data: VMActionRequest, request: Request, x_api_token: str = Header(None)):
    token_row = validate_api_access_token(x_api_token or "", "vm.action", data.vm_id)
    backend = detect_vm_backend() if data.backend == "auto" else data.backend
    action = data.action.lower().strip()
    if action not in {"start", "shutdown", "stop", "reboot"}:
        raise HTTPException(status_code=400, detail="Nieznana akcja VM")
    target = safe_vm_target(data.vm_id)
    api_user = {"username": f"api-{token_row.get('id', token_row.get('name', 'token'))}", "role": "admin", "status": "active"}
    if action == "stop":
        require_destructive_confirmation(api_user, "vm.stop.hard", target, data.confirm, request, data.reason)
    if action == "start":
        if backend == "libvirt":
            enforce_cupertino_start_guard(target)
        vm_billing_can_start(target, token_row.get("name", "api"))
    if backend == "libvirt":
        command_map = {"start": ["virsh", "start", target], "shutdown": ["virsh", "shutdown", target], "stop": ["virsh", "destroy", target], "reboot": ["virsh", "reboot", target]}
    elif backend == "proxmox":
        command_map = {"start": ["qm", "start", target], "shutdown": ["qm", "shutdown", target], "stop": ["qm", "stop", target], "reboot": ["qm", "reboot", target]}
    else:
        raise HTTPException(status_code=400, detail="Nie wykryto silnika VM")
    code, output = run_vm_command(command_map[action], timeout=30)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Akcja VM nie powiodla sie")
    send_webhook_event("vm.action", {"backend": backend, "vm_id": target, "action": action, "actor": f"api:{token_row.get('name')}", "output": output.strip()[:500]})
    return {"status": "success", "backend": backend, "vm_id": target, "action": action, "output": output.strip()}

@app.get("/api/integrations/webhooks", dependencies=[Depends(verify_token)])
async def integration_webhooks():
    return {"items": read_json(WEBHOOKS_FILE, [])}

@app.post("/api/integrations/webhooks", dependencies=[Depends(verify_admin)])
async def integration_webhook_create(data: WebhookCreateRequest, admin = Depends(verify_admin)):
    parsed = urllib.parse.urlparse(data.url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="Webhook musi byc http/https")
    row = {"id": uuid.uuid4().hex[:12], "name": data.name[:80], "url": data.url, "events": data.events[:20] or ["vm.action", "billing.empty", "alert"], "enabled": bool(data.enabled), "created_at": now_iso(), "created_by": admin.get("username", "admin")}
    rows = read_json(WEBHOOKS_FILE, [])
    rows.insert(0, row)
    write_json(WEBHOOKS_FILE, rows[:200])
    return row

@app.post("/api/integrations/webhooks/delete", dependencies=[Depends(verify_admin)])
async def integration_webhook_delete(data: WebhookDeleteRequest):
    rows = [item for item in read_json(WEBHOOKS_FILE, []) if item.get("id") != data.id]
    write_json(WEBHOOKS_FILE, rows)
    return {"status": "deleted"}

@app.post("/api/integrations/webhooks/test", dependencies=[Depends(verify_admin)])
async def integration_webhook_test(data: WebhookDeleteRequest):
    row = next((item for item in read_json(WEBHOOKS_FILE, []) if item.get("id") == data.id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Webhook nie istnieje")
    payload = json.dumps({"event": "test", "source": "NEXUS CORE", "created_at": now_iso()}).encode("utf-8")
    try:
        req = urllib.request.Request(row["url"], data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=8) as response:
            return {"status": "sent", "code": response.status}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

def command_json(command, timeout=20):
    code, output = run_vm_command(command, timeout=timeout)
    if code != 0:
        return {"ok": False, "error": output[-1200:], "items": []}
    try:
        return {"ok": True, "data": json.loads(output)}
    except Exception:
        return {"ok": True, "raw": output[-4000:]}

@app.get("/api/hardware/telemetry", dependencies=[Depends(verify_token)])
async def hardware_telemetry():
    smart_scan = {"ok": False, "items": []}
    smart_devices = []
    if shutil.which("smartctl"):
        code, output = run_vm_command(["smartctl", "--scan", "-j"], timeout=15)
        if code == 0:
            try:
                smart_scan = {"ok": True, "data": json.loads(output)}
            except Exception:
                smart_scan = {"ok": True, "raw": output}
            for dev in (smart_scan.get("data", {}).get("devices") or [])[:8]:
                name = dev.get("name")
                if name:
                    smart_devices.append(command_json(["smartctl", "-a", "-j", name], timeout=25))
        else:
            smart_scan = {"ok": False, "error": output[-1200:]}
    sensors = command_json(["sensors", "-j"], timeout=15) if shutil.which("sensors") else {"ok": False, "error": "lm-sensors brak"}
    lscpu = command_json(["lscpu", "-J"], timeout=10) if shutil.which("lscpu") else {"ok": False, "error": "lscpu brak"}
    numa = {"ok": False, "error": "numactl brak"}
    if shutil.which("numactl"):
        code, output = run_vm_command(["numactl", "--hardware"], timeout=10)
        numa = {"ok": code == 0, "raw": output[-4000:]}
    return {"smart_scan": smart_scan, "smart_devices": smart_devices, "sensors": sensors, "lscpu": lscpu, "numa": numa, "checked_at": now_iso()}

# --- NEXT-GEN LABS: CO-OP / HYPER-SLEEP / CANVAS / FORGE / AI COMMANDER ---
def validate_coop_ticket(ticket: str):
    rows = read_json(COOP_SESSIONS_FILE, [])
    row = next((item for item in rows if item.get("ticket") == ticket and item.get("enabled", True)), None)
    if not row:
        raise HTTPException(status_code=404, detail="Sesja CO-OP nie istnieje")
    try:
        if datetime.datetime.fromisoformat(row.get("expires_at", "")) < datetime.datetime.now():
            raise HTTPException(status_code=403, detail="Sesja CO-OP wygasla")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=403, detail="Sesja CO-OP ma bledny termin")
    return row

@app.get("/api/coop/sessions", dependencies=[Depends(verify_token)])
async def coop_sessions():
    rows = read_json(COOP_SESSIONS_FILE, [])
    now = datetime.datetime.now()
    for row in rows:
        try:
            row["expired"] = datetime.datetime.fromisoformat(row.get("expires_at", "")) < now
        except Exception:
            row["expired"] = True
    return {"items": rows}

@app.post("/api/coop/sessions", dependencies=[Depends(verify_admin)])
async def coop_session_create(data: CoopSessionRequest, request: Request, admin = Depends(verify_admin)):
    target = safe_vm_target(data.vm_id)
    role = "view" if data.role == "view" else "control"
    ticket = secrets.token_urlsafe(24)
    row = {
        "id": uuid.uuid4().hex[:12],
        "ticket": ticket,
        "vm_id": target,
        "role": role,
        "created_at": now_iso(),
        "created_by": admin.get("username", "admin"),
        "expires_at": (datetime.datetime.now() + datetime.timedelta(minutes=int(data.minutes))).isoformat(timespec="seconds"),
        "enabled": True,
    }
    rows = read_json(COOP_SESSIONS_FILE, [])
    rows.insert(0, row)
    write_json(COOP_SESSIONS_FILE, rows[:200])
    row["link"] = f"{external_base_url(request)}/static/coop.html?ticket={urllib.parse.quote(ticket)}"
    return row

@app.post("/api/coop/sessions/revoke", dependencies=[Depends(verify_admin)])
async def coop_session_revoke(data: WebhookDeleteRequest):
    rows = read_json(COOP_SESSIONS_FILE, [])
    for row in rows:
        if row.get("id") == data.id:
            row["enabled"] = False
            row["revoked_at"] = now_iso()
    write_json(COOP_SESSIONS_FILE, rows)
    return {"status": "revoked"}

@app.get("/api/coop/session/{ticket}")
async def coop_session_public(ticket: str):
    row = validate_coop_ticket(ticket)
    return {"vm_id": row["vm_id"], "role": row.get("role", "view"), "expires_at": row.get("expires_at"), "server_time": now_iso()}

@app.get("/api/coop/console")
async def coop_console(ticket: str):
    row = validate_coop_ticket(ticket)
    target = safe_vm_target(row["vm_id"])
    endpoint = detect_vnc_endpoint("auto", target)
    input_repair = None
    if endpoint.get("backend") == "libvirt":
        try:
            input_repair = ensure_libvirt_input_devices(target, live=True, config=True)
        except Exception as exc:
            input_repair = {
                "status": "warning",
                "vm_id": target,
                "warnings": [str(getattr(exc, "detail", exc))[:500]],
            }
            log_event(f"VM_INPUT_PREFLIGHT warning coop vm={target}: {input_repair['warnings'][0]}")
    user = {"username": f"coop-{row.get('id','')}", "role": "user", "status": "active", "vnc_scope": "coop", "permissions": ["console.open"]}
    vnc_ticket, session = create_vnc_session(target, endpoint["backend"], user)
    return {
        "status": "ready",
        "vm_id": target,
        "role": row.get("role", "view"),
        "ws_path": f"/ws/vnc/{urllib.parse.quote(target, safe='')}?backend={urllib.parse.quote(endpoint['backend'], safe='')}&session={urllib.parse.quote(vnc_ticket, safe='')}",
        "session_expires_at": session["expires_at"],
        "input_repair": input_repair,
    }

@app.websocket("/ws/coop/{ticket}")
async def coop_cursor_socket(websocket: WebSocket, ticket: str):
    try:
        row = validate_coop_ticket(ticket)
    except HTTPException:
        await websocket.accept()
        await websocket.close(code=1008)
        return
    await websocket.accept()
    room = COOP_PEERS.setdefault(ticket, set())
    room.add(websocket)
    hello = {"type": "join", "peer": uuid.uuid4().hex[:8], "vm_id": row.get("vm_id"), "ts": now_iso()}
    try:
        await websocket.send_text(json.dumps(hello))
        while True:
            msg = await websocket.receive_text()
            for peer in list(room):
                if peer is websocket:
                    continue
                try:
                    await peer.send_text(msg)
                except Exception:
                    room.discard(peer)
    except Exception:
        pass
    finally:
        room.discard(websocket)

def hyper_sleep_row(state_id: str):
    rows = read_json(HYPER_SLEEP_FILE, [])
    return next((item for item in rows if item.get("id") == state_id), None)

@app.get("/api/hyper-sleep/states", dependencies=[Depends(verify_token)])
async def hyper_sleep_states():
    rows = read_json(HYPER_SLEEP_FILE, [])
    for row in rows:
        path = Path(row.get("path", ""))
        if path.exists():
            row["size"] = fmt_size(path.stat().st_size)
            row["exists"] = True
        else:
            row["exists"] = False
    return {"items": rows, "root": str(HYPER_SLEEP_DIR)}

@app.post("/api/hyper-sleep/freeze", dependencies=[Depends(verify_admin)])
async def hyper_sleep_freeze(data: HyperSleepRequest, admin = Depends(verify_admin)):
    target = safe_vm_target(data.vm_id)
    HYPER_SLEEP_DIR.mkdir(parents=True, exist_ok=True)
    state_id = uuid.uuid4().hex[:12]
    label = safe_snapshot_name(data.label or target)
    path = (HYPER_SLEEP_DIR / f"{target}-{label}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.save").resolve()
    code, output = run_vm_command(["virsh", "save", target, str(path)], timeout=60 * 30)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie zamrozic VM")
    ensure_libvirt_file_access(path)
    row = {"id": state_id, "vm_id": target, "label": label, "path": str(path), "size": fmt_size(path.stat().st_size), "created_at": now_iso(), "created_by": admin.get("username", "admin"), "status": "frozen"}
    rows = read_json(HYPER_SLEEP_FILE, [])
    rows.insert(0, row)
    write_json(HYPER_SLEEP_FILE, rows[:200])
    send_webhook_event("hyper_sleep.freeze", row)
    return row

@app.post("/api/hyper-sleep/wake", dependencies=[Depends(verify_admin)])
async def hyper_sleep_wake(data: HyperWakeRequest):
    rows = read_json(HYPER_SLEEP_FILE, [])
    row = next((item for item in rows if item.get("id") == data.id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Stan Hyper-Sleep nie istnieje")
    path = Path(row.get("path", "")).resolve()
    if not path.exists():
        raise HTTPException(status_code=404, detail="Plik stanu RAM nie istnieje")
    code, output = run_vm_command(["virsh", "restore", str(path)], timeout=60 * 10)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie wybudzic VM")
    row["status"] = "restored"
    row["restored_at"] = now_iso()
    write_json(HYPER_SLEEP_FILE, rows)
    send_webhook_event("hyper_sleep.wake", row)
    return row

@app.post("/api/hyper-sleep/delete", dependencies=[Depends(verify_admin)])
async def hyper_sleep_delete(data: HyperWakeRequest):
    rows = read_json(HYPER_SLEEP_FILE, [])
    row = next((item for item in rows if item.get("id") == data.id), None)
    if row:
        try:
            Path(row.get("path", "")).unlink(missing_ok=True)
        except Exception:
            pass
    write_json(HYPER_SLEEP_FILE, [item for item in rows if item.get("id") != data.id])
    return {"status": "deleted"}

@app.get("/api/canvas/topologies", dependencies=[Depends(verify_token)])
async def canvas_topologies():
    return {"items": read_json(CANVAS_FILE, [])}

@app.post("/api/canvas/topologies", dependencies=[Depends(verify_admin)])
async def canvas_save(data: CanvasSaveRequest, admin = Depends(verify_admin)):
    row = {"id": uuid.uuid4().hex[:12], "name": data.name[:80], "nodes": data.nodes[:100], "edges": data.edges[:200], "created_at": now_iso(), "created_by": admin.get("username", "admin")}
    rows = read_json(CANVAS_FILE, [])
    rows.insert(0, row)
    write_json(CANVAS_FILE, rows[:100])
    return row

@app.post("/api/canvas/deploy", dependencies=[Depends(verify_admin)])
async def canvas_deploy(data: CanvasDeployRequest):
    rows = read_json(CANVAS_FILE, [])
    row = next((item for item in rows if item.get("id") == data.id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Topologia nie istnieje")
    nodes = row.get("nodes", [])
    edges = row.get("edges", [])
    plan = {
        "networks": [n for n in nodes if n.get("type") in {"router", "network", "switch"}],
        "vms": [n for n in nodes if n.get("type") in {"linux", "windows", "vm", "database"}],
        "links": edges,
        "note": "Plan gotowy. Automatyczne tworzenie VM/switchy wymaga zatwierdzenia w HYPER-DECK.",
    }
    row["last_deploy_plan"] = plan
    row["last_deploy_at"] = now_iso()
    write_json(CANVAS_FILE, rows)
    return {"status": "planned", "topology": row["name"], "plan": plan}

def primary_vm_disk(vm_id: str):
    paths = vm_storage_paths(vm_id)
    if not paths:
        raise HTTPException(status_code=404, detail="Nie znaleziono dysku VM")
    return paths[0]

@app.get("/api/forge/templates", dependencies=[Depends(verify_token)])
async def forge_templates():
    return {"items": read_json(FORGE_FILE, [])}

@app.post("/api/forge/publish", dependencies=[Depends(verify_admin)])
async def forge_publish(data: ForgePublishRequest, admin = Depends(verify_admin)):
    target = safe_vm_target(data.vm_id)
    disk = primary_vm_disk(target)
    row = {"id": uuid.uuid4().hex[:12], "vm_id": target, "name": data.name[:120], "description": data.description[:500], "price": round(float(data.price), 4), "seller": admin.get("username", "admin"), "disk": str(disk), "created_at": now_iso(), "status": "published"}
    rows = read_json(FORGE_FILE, [])
    rows.insert(0, row)
    write_json(FORGE_FILE, rows[:200])
    return row

@app.post("/api/forge/buy", dependencies=[Depends(verify_admin)])
async def forge_buy(data: ForgeBuyRequest, admin = Depends(verify_admin)):
    item = next((row for row in read_json(FORGE_FILE, []) if row.get("id") == data.id and row.get("status") == "published"), None)
    if not item:
        raise HTTPException(status_code=404, detail="Template Forge nie istnieje")
    source_disk = Path(item.get("disk", "")).resolve()
    if not source_disk.exists():
        raise HTTPException(status_code=404, detail="Dysk bazowy template zniknal")
    new_name = safe_domain_name(data.name)
    target_disk = (LIBVIRT_IMAGE_DIR / f"{new_name}.qcow2").resolve()
    if target_disk.exists():
        raise HTTPException(status_code=409, detail="Dysk docelowy juz istnieje")
    buyer = admin.get("username", "admin")
    seller = item.get("seller", "admin")
    price = float(item.get("price", 0) or 0)
    billing = vm_billing_store()
    buyer_wallet = vm_wallet(billing, buyer)
    seller_wallet = vm_wallet(billing, seller)
    if price > 0 and buyer != seller and buyer_wallet["balance"] < price:
        raise HTTPException(status_code=402, detail="Brak tokenow na zakup template")
    code, output = run_vm_command(["qemu-img", "create", "-f", "qcow2", "-F", "qcow2", "-b", str(source_disk), str(target_disk)], timeout=120)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Nie utworzono dysku COW")
    ensure_libvirt_file_access(target_disk)
    clone_cmd = ["virt-clone", "--original", item["vm_id"], "--name", new_name, "--file", str(target_disk), "--preserve-data"]
    if shutil.which("virt-clone"):
        code, output = run_vm_command(clone_cmd, timeout=180)
    else:
        code, output = (1, "Brak virt-clone na hoście")
    if code != 0:
        try:
            target_disk.unlink()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=output.strip() or "Nie zdefiniowano klona VM")
    if price > 0 and buyer != seller:
        buyer_wallet["balance"] -= price
        buyer_wallet["spent"] += price
        seller_wallet["balance"] += price
        seller_wallet["credited"] += price
        billing.setdefault("ledger", []).append({"id": uuid.uuid4().hex[:12], "type": "forge", "buyer": buyer, "seller": seller, "amount": price, "template": item["id"], "created_at": now_iso()})
        save_vm_billing(billing)
    vm_billing_assign_owner(new_name, buyer)
    return {"status": "cloned", "vm_id": new_name, "disk": str(target_disk), "template": item["name"], "price": price}

def vm_names_for_commander():
    backend = detect_vm_backend()
    names = []
    if backend == "libvirt":
        code, output = run_vm_command(["virsh", "list", "--all", "--name"], timeout=10)
        if code == 0:
            names = [x.strip() for x in output.splitlines() if x.strip()]
    return names

def match_vm_name(text: str, names: list):
    low = text.lower()
    aliases = {"vista": "vista", "siodem": "win7", "siódem": "win7", "seven": "win7"}
    for name in names:
        nlow = name.lower()
        if nlow in low:
            return name
        for alias, needle in aliases.items():
            if alias in low and needle in nlow:
                return name
    return names[0] if names else ""

@app.post("/api/ai-commander/run", dependencies=[Depends(verify_admin)])
async def ai_commander_run(data: AiCommanderRequest, admin = Depends(verify_admin)):
    text = data.command.strip()
    names = vm_names_for_commander()
    target = match_vm_name(text, names)
    actions = []
    lower = text.lower()
    if target and any(word in lower for word in ["zabij", "destroy", "twardo", "stop"]):
        actions.append({"kind": "vm_action", "vm_id": target, "action": "stop", "command": ["virsh", "destroy", target]})
    elif target and any(word in lower for word in ["wylacz", "wyłącz", "shutdown"]):
        actions.append({"kind": "vm_action", "vm_id": target, "action": "shutdown", "command": ["virsh", "shutdown", target]})
    ram_match = re.search(r"ram.*?(\d+)\s*(gb|g|mb|m)", lower)
    if target and ram_match:
        value = int(ram_match.group(1))
        mb = value * 1024 if ram_match.group(2).startswith("g") else value
        actions.append({"kind": "ram", "vm_id": target, "memory_mb": mb, "command": ["virsh", "setmaxmem", target, f"{mb}M", "--config"]})
        actions.append({"kind": "ram", "vm_id": target, "memory_mb": mb, "command": ["virsh", "setmem", target, f"{mb}M", "--config"]})
    snap_match = re.search(r"snapshot(?:\s+o\s+nazwie|\s+nazwa|\s+named)?\s+[\"']?([^\"']{3,80})[\"']?", text, re.I)
    if target and ("snapshot" in lower or "migawk" in lower):
        snap = safe_snapshot_name((snap_match.group(1).strip() if snap_match else f"ai-{now_iso()}").replace(" ", "-"))
        actions.append({"kind": "snapshot", "vm_id": target, "snapshot": snap, "command": ["virsh", "snapshot-create-as", "--domain", target, "--name", snap, "--description", f"AI Commander {now_iso()}", "--atomic"]})
    results = []
    if data.execute:
        for action in actions:
            code, output = run_vm_command(action["command"], timeout=300)
            results.append({**{k: v for k, v in action.items() if k != "command"}, "code": code, "output": output[-1200:]})
            if code != 0:
                break
    row = {"id": uuid.uuid4().hex[:12], "command": text, "target": target, "actions": actions, "results": results, "executed": bool(data.execute), "created_at": now_iso(), "created_by": admin.get("username", "admin")}
    logs = read_json(AI_COMMANDER_FILE, [])
    logs.insert(0, row)
    write_json(AI_COMMANDER_FILE, logs[:200])
    return {"status": "executed" if data.execute else "planned", "target": target, "actions": actions, "results": results, "message": "Wykonano rozpoznane akcje." if results else "Nie rozpoznalem bezpiecznej akcji albo brak VM."}

@app.get("/api/ai-commander/log", dependencies=[Depends(verify_token)])
async def ai_commander_log():
    return {"items": read_json(AI_COMMANDER_FILE, [])[:80]}

# --- ENTERPRISE EXTRAS: ARCHIVER / BASTION / WORKERS / VAULT / GLOBAL TERMINAL ---
def enterprise_roots():
    roots = [BASE_DIR, BACKUP_DIR, LIBVIRT_IMAGE_DIR]
    safe = []
    for root in roots:
        try:
            root.mkdir(parents=True, exist_ok=True)
            safe.append(root.resolve())
        except Exception:
            pass
    return safe

def allowed_enterprise_path(value: str, must_exist: bool = True):
    raw = (value or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="Brak sciezki")
    path = Path(raw)
    if not path.is_absolute():
        path = BASE_DIR / raw
    target = path.resolve()
    if must_exist and not target.exists():
        raise HTTPException(status_code=404, detail="Sciezka nie istnieje")
    if not any(target == root or root in target.parents for root in enterprise_roots()):
        raise HTTPException(status_code=403, detail="Sciezka poza dozwolonymi katalogami NEXUS")
    return target

# --- XOPS: enterprise virtualization/network/storage control plane ---
def xops_audit(kind: str, status: str, payload: dict, user: str = "system"):
    row = {
        "id": uuid.uuid4().hex[:12],
        "kind": kind,
        "status": status,
        "payload": payload,
        "created_by": user,
        "created_at": now_iso(),
    }
    rows = read_json(XOPS_AUDIT_FILE, [])
    rows.insert(0, row)
    write_json(XOPS_AUDIT_FILE, rows[:500])
    return row

def xops_tail(text: str, limit: int = 4000):
    text = text or ""
    return text[-limit:]

def xops_tool_map():
    names = [
        "virsh", "qemu-img", "virt-sparsify", "tcpdump", "tc", "swtpm",
        "zpool", "zfs", "lsblk", "lscpu", "numactl", "sensors",
        "nvidia-smi", "lspci", "fail2ban-client", "apparmor_status",
    ]
    return {name: bool(shutil.which(name)) for name in names}

def xops_read(path: str, max_len: int = 2000):
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")[:max_len].strip()
    except Exception:
        return ""

def xops_command(args, timeout=10):
    try:
        code, output = run_vm_command(args, timeout=timeout)
        return {"command": args, "code": code, "ok": code == 0, "output": xops_tail(output)}
    except subprocess.TimeoutExpired:
        return {"command": args, "code": 124, "ok": False, "output": "Timeout"}
    except Exception as exc:
        return {"command": args, "code": 1, "ok": False, "output": str(exc)}

def xops_safe_iface(value: str):
    iface = (value or "").strip()
    if not iface or not re.match(r"^[A-Za-z0-9_.:-]{1,64}$", iface):
        raise HTTPException(status_code=400, detail="Niepoprawny interfejs sieciowy")
    return iface

def xops_vm_iface(vm_id: str = "", iface: str = ""):
    if iface:
        return xops_safe_iface(iface)
    if not vm_id:
        raise HTTPException(status_code=400, detail="Podaj VM ID albo iface")
    rows = vm_interface_rows(vm_id)
    for row in rows:
        value = row.get("interface") or ""
        if value and value != "-":
            return xops_safe_iface(value)
    raise HTTPException(status_code=404, detail="Nie znaleziono interfejsu VM")

def xops_feature_plan(profile: str, features: list):
    profile = (profile or "balanced").strip().lower()
    chosen = [str(item).strip().lower() for item in (features or []) if str(item).strip()]
    if not chosen:
        chosen = {
            "balanced": ["watchdog", "balloon", "qemu-guest-agent"],
            "high-performance": ["cpu-pinning", "numa", "iothreads", "io-polling", "balloon"],
            "windows11": ["vtpm", "uefi", "secure-boot", "virtio-drivers", "qemu-guest-agent"],
            "secure-lab": ["readonly-snapshot", "watchdog", "seccomp", "vault-export"],
            "forensic": ["ram-dump", "pcap-sample", "qemu-img-check", "clamav-hook"],
        }.get(profile, ["watchdog", "balloon"])
    snippets = {
        "watchdog": "<watchdog model='i6300esb' action='reset'/>",
        "balloon": "<memballoon model='virtio'/>",
        "qemu-guest-agent": "<channel type='unix'><target type='virtio' name='org.qemu.guest_agent.0'/></channel>",
        "vtpm": "<tpm model='tpm-crb'><backend type='emulator' version='2.0'/></tpm>",
        "uefi": "<loader readonly='yes' type='pflash'>/usr/share/OVMF/OVMF_CODE.fd</loader>",
        "secure-boot": "<feature name='secure-boot' enabled='yes'/>",
        "virtio-drivers": "Attach virtio-win ISO as second CD-ROM before Windows install.",
        "cpu-pinning": "<cputune><vcpupin vcpu='0' cpuset='0'/></cputune>",
        "numa": "<numatune><memory mode='preferred' nodeset='0'/></numatune>",
        "iothreads": "<iothreads>1</iothreads>",
        "io-polling": "Use io='threads', cache='none', discard='unmap' and host CPU isolation.",
        "readonly-snapshot": "Create external transient qcow2 overlay and discard it on shutdown.",
        "seccomp": "Enable QEMU seccomp/AppArmor profile at libvirt host level.",
        "vault-export": "Export artifacts through Vault one-time AES-GCM link.",
        "ram-dump": "virsh dump --memory-only VM file.dump",
        "pcap-sample": "tcpdump on VM tap interface with packet/time limits.",
        "qemu-img-check": "qemu-img check disk.qcow2 before import/start.",
        "clamav-hook": "Mount image read-only with guestfs and scan with clamscan.",
    }
    return [{"feature": item, "snippet": snippets.get(item, "Manual integration required"), "ready": item in snippets} for item in chosen]

@app.get("/api/xops/status", dependencies=[Depends(verify_token)])
async def xops_status():
    tools = xops_tool_map()
    probes = {
        "nested_amd": xops_read("/sys/module/kvm_amd/parameters/nested", 80),
        "nested_intel": xops_read("/sys/module/kvm_intel/parameters/nested", 80),
        "kernel": xops_read("/proc/cmdline", 500),
    }
    lscpu = xops_command(["lscpu"], timeout=8) if tools.get("lscpu") else {"ok": False, "output": "missing lscpu"}
    numa = xops_command(["numactl", "--hardware"], timeout=8) if tools.get("numactl") else {"ok": False, "output": "missing numactl"}
    gpu = xops_command(["nvidia-smi", "-L"], timeout=8) if tools.get("nvidia-smi") else (xops_command(["lspci"], timeout=8) if tools.get("lspci") else {"ok": False, "output": "missing gpu probes"})
    zfs = xops_command(["zpool", "list", "-H"], timeout=8) if tools.get("zpool") else {"ok": False, "output": "missing zpool"}
    disks = []
    for label, path in [("base", BASE_DIR), ("libvirt", LIBVIRT_IMAGE_DIR), ("backups", BACKUP_DIR)]:
        try:
            disks.append(disk_guard_snapshot(path, label))
        except Exception:
            pass
    return {
        "status": "live",
        "backend": detect_vm_backend(),
        "tools": tools,
        "memory": host_memory_snapshot(),
        "disks": disks,
        "probes": probes,
        "lscpu": xops_tail(lscpu.get("output", ""), 3000),
        "numa": xops_tail(numa.get("output", ""), 3000),
        "gpu": xops_tail(gpu.get("output", ""), 3000),
        "zfs": xops_tail(zfs.get("output", ""), 2000),
        "audit": read_json(XOPS_AUDIT_FILE, [])[:20],
    }

@app.post("/api/xops/vm/plan", dependencies=[Depends(verify_token)])
async def xops_vm_plan(data: XOpsPlanRequest):
    target = safe_vm_target(data.vm_id) if data.vm_id else ""
    plan = xops_feature_plan(data.profile, data.features)
    commands = []
    if target and data.memory_mb:
        commands.append(["virsh", "setmem", target, f"{data.memory_mb}M", "--live"])
    if target and data.vcpus:
        commands.append(["virsh", "setvcpus", target, str(data.vcpus), "--live"])
    return {
        "status": "planned",
        "vm_id": target,
        "profile": data.profile,
        "features": plan,
        "commands": commands,
        "note": "Plan pokazuje bezpieczna droge wdrozenia; akcje zmieniajace stan sa osobnymi endpointami.",
    }

@app.post("/api/xops/vm/balloon", dependencies=[Depends(verify_admin)])
async def xops_vm_balloon(data: XOpsBalloonRequest, admin = Depends(verify_admin)):
    target = safe_vm_target(data.vm_id)
    result = vm_ram_update_cascade(target, data.memory_mb, live=data.live, config=data.config)
    info = xops_command(["virsh", "dominfo", target], timeout=10)
    audit_status = "warn" if result.get("status") == "warning" else "ok"
    audit = xops_audit("vm.balloon", audit_status, {"vm_id": target, "memory_mb": data.memory_mb, "result": result}, admin.get("username", "admin"))
    return {"status": result.get("status", "ok"), "vm_id": target, "memory_mb": data.memory_mb, "result": result, "verify": info, "audit": audit}

@app.post("/api/xops/vm/watchdog", dependencies=[Depends(verify_admin)])
async def xops_vm_watchdog(data: XOpsWatchdogRequest, admin = Depends(verify_admin)):
    target = safe_vm_target(data.vm_id)
    action = (data.action or "reset").lower()
    if action not in {"reset", "shutdown", "poweroff", "pause", "none"}:
        raise HTTPException(status_code=400, detail="Action: reset/shutdown/poweroff/pause/none")
    flags = vm_iso_flags(target, data.live, data.config)
    xml_path = Path("/tmp") / f"nexus-watchdog-{uuid.uuid4().hex[:10]}.xml"
    xml_path.write_text(f"<watchdog model='i6300esb' action='{action}'/>\n", encoding="utf-8")
    try:
        result = xops_command(["virsh", "attach-device", target, str(xml_path)] + flags, timeout=30)
    finally:
        try:
            xml_path.unlink()
        except Exception:
            pass
    xml = xops_command(["virsh", "dumpxml", target], timeout=15)
    verified = "<watchdog" in xml.get("output", "")
    status = "ok" if (result.get("ok") or verified) else "error"
    audit = xops_audit("vm.watchdog", status, {"vm_id": target, "action": action, "result": result, "verified": verified}, admin.get("username", "admin"))
    if status != "ok":
        raise HTTPException(status_code=500, detail={"message": "Nie udalo sie podpiac watchdoga", "result": result, "audit": audit})
    return {"status": "ok", "vm_id": target, "action": action, "result": result, "verified": verified, "audit": audit}

@app.post("/api/xops/network/qos", dependencies=[Depends(verify_admin)])
async def xops_network_qos(data: XOpsQoSRequest, admin = Depends(verify_admin)):
    iface = xops_vm_iface(data.vm_id, data.iface)
    rate = int(data.rate_mbit)
    command = ["tc", "qdisc", "replace", "dev", iface, "root", "tbf", "rate", f"{rate}mbit", "burst", "64kbit", "latency", "400ms"]
    if not data.apply:
        return {"status": "planned", "iface": iface, "rate_mbit": rate, "command": command, "message": "Ustaw apply=true, aby nalozyc limit tc."}
    if not shutil.which("tc"):
        raise HTTPException(status_code=501, detail="Brak narzedzia tc")
    result = xops_command(command, timeout=15)
    verify = xops_command(["tc", "qdisc", "show", "dev", iface], timeout=10)
    audit = xops_audit("network.qos", "ok" if result.get("ok") else "error", {"iface": iface, "rate_mbit": rate, "result": result}, admin.get("username", "admin"))
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail={"message": "Nie udalo sie ustawic QoS", "result": result, "audit": audit})
    return {"status": "ok", "iface": iface, "rate_mbit": rate, "result": result, "verify": verify, "audit": audit}

@app.post("/api/xops/network/pcap", dependencies=[Depends(verify_admin)])
async def xops_network_pcap(data: XOpsPcapRequest, admin = Depends(verify_admin)):
    if not shutil.which("tcpdump"):
        raise HTTPException(status_code=501, detail="Brak tcpdump")
    iface = xops_vm_iface(data.vm_id, data.iface)
    command = ["tcpdump", "-i", iface, "-c", str(int(data.packets)), "-nn", "-tt"]
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=int(data.seconds) + 3)
        output = (proc.stdout or "") + (proc.stderr or "")
        result = {"command": command, "code": proc.returncode, "ok": proc.returncode == 0, "output": xops_tail(output, 8000)}
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        err = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        result = {"command": command, "code": 124, "ok": False, "output": xops_tail(out + err + "\nTimeout PCAP sample", 8000)}
    audit = xops_audit("network.pcap", "ok" if result.get("output") else "empty", {"iface": iface, "packets": data.packets, "seconds": data.seconds}, admin.get("username", "admin"))
    return {"status": "captured" if result.get("output") else "empty", "iface": iface, "result": result, "audit": audit}

@app.post("/api/xops/storage/check", dependencies=[Depends(verify_token)])
async def xops_storage_check(data: XOpsDiskRequest):
    path = allowed_enterprise_path(data.path)
    if not path.is_file():
        raise HTTPException(status_code=400, detail="Podaj plik dysku")
    if not shutil.which("qemu-img"):
        raise HTTPException(status_code=501, detail="Brak qemu-img")
    info = xops_command(["qemu-img", "info", str(path)], timeout=30)
    check = xops_command(["qemu-img", "check", str(path)], timeout=300)
    return {"status": "ok" if check.get("ok") else "error", "path": str(path), "size": fmt_size(path.stat().st_size), "info": info, "check": check}

@app.post("/api/xops/storage/shrink", dependencies=[Depends(verify_admin)])
async def xops_storage_shrink(data: XOpsShrinkRequest, admin = Depends(verify_admin)):
    path = allowed_enterprise_path(data.path)
    if not path.is_file():
        raise HTTPException(status_code=400, detail="Podaj plik dysku")
    output = Path(data.output_path).resolve() if data.output_path else path.with_name(f"{path.stem}-sparsified{path.suffix}").resolve()
    if output.exists() and not data.dry_run:
        raise HTTPException(status_code=409, detail="Plik wyjsciowy juz istnieje")
    if not any(output == root or root in output.parents for root in enterprise_roots()):
        raise HTTPException(status_code=403, detail="Output poza dozwolonym katalogiem")
    command = ["virt-sparsify", "--compress", str(path), str(output)]
    if data.dry_run:
        return {"status": "planned", "source": str(path), "output": str(output), "command": command, "source_size": fmt_size(path.stat().st_size)}
    if not shutil.which("virt-sparsify"):
        raise HTTPException(status_code=501, detail="Brak virt-sparsify")
    result = xops_command(command, timeout=60 * 60 * 4)
    audit = xops_audit("storage.shrink", "ok" if result.get("ok") else "error", {"source": str(path), "output": str(output), "result": result}, admin.get("username", "admin"))
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail={"message": "Shrink nie przeszedl", "result": result, "audit": audit})
    return {"status": "ok", "source": str(path), "output": str(output), "source_size": fmt_size(path.stat().st_size), "output_size": fmt_size(output.stat().st_size), "result": result, "audit": audit}

@app.post("/api/xops/forensics/ram-dump", dependencies=[Depends(verify_admin)])
async def xops_forensics_ram_dump(data: XOpsForensicsRequest, admin = Depends(verify_admin)):
    target = safe_vm_target(data.vm_id)
    forensics_dir = (BASE_DIR / "forensics").resolve()
    forensics_dir.mkdir(parents=True, exist_ok=True)
    output = Path(data.output_path).resolve() if data.output_path else forensics_dir / f"{target}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.dump"
    if not any(output == root or root in output.parents for root in [forensics_dir, BASE_DIR.resolve(), BACKUP_DIR.resolve()]):
        raise HTTPException(status_code=403, detail="Output forensic poza dozwolonym katalogiem")
    command = ["virsh", "dump", target, str(output), "--memory-only", "--live"]
    if data.dry_run:
        return {"status": "planned", "vm_id": target, "output": str(output), "command": command, "warning": "RAM dump moze byc bardzo duzy; wykonuj przy wolnym dysku."}
    result = xops_command(command, timeout=60 * 30)
    audit = xops_audit("forensics.ram_dump", "ok" if result.get("ok") else "error", {"vm_id": target, "output": str(output), "result": result}, admin.get("username", "admin"))
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail={"message": "RAM dump nie przeszedl", "result": result, "audit": audit})
    return {"status": "ok", "vm_id": target, "output": str(output), "size": fmt_size(output.stat().st_size), "result": result, "audit": audit}

@app.get("/api/xops/security/audit", dependencies=[Depends(verify_token)])
async def xops_security_audit():
    tools = xops_tool_map()
    fail2ban = xops_command(["fail2ban-client", "status"], timeout=8) if tools.get("fail2ban-client") else {"ok": False, "output": "missing fail2ban-client"}
    apparmor = xops_command(["apparmor_status"], timeout=8) if tools.get("apparmor_status") else {"ok": False, "output": "missing apparmor_status"}
    alerts = read_json(ALERTS_FILE, [])[:20]
    logs = []
    try:
        logs = [line for line in LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()[-300:] if any(word in line.upper() for word in ["ERROR", "FAIL", "WARN", "DENIED", "CRITICAL"])]
    except Exception:
        pass
    return {
        "status": "live",
        "fail2ban": fail2ban,
        "apparmor": apparmor,
        "alerts": alerts,
        "signals": logs[-40:],
        "audit": read_json(XOPS_AUDIT_FILE, [])[:80],
    }

def nextgen_read_int(path: str):
    try:
        return int(Path(path).read_text(encoding="utf-8", errors="ignore").strip())
    except Exception:
        return None

def nextgen_ksm_snapshot():
    base = "/sys/kernel/mm/ksm"
    values = {
        "run": nextgen_read_int(f"{base}/run"),
        "pages_shared": nextgen_read_int(f"{base}/pages_shared"),
        "pages_sharing": nextgen_read_int(f"{base}/pages_sharing"),
        "pages_unshared": nextgen_read_int(f"{base}/pages_unshared"),
        "pages_volatile": nextgen_read_int(f"{base}/pages_volatile"),
        "full_scans": nextgen_read_int(f"{base}/full_scans"),
        "sleep_millisecs": nextgen_read_int(f"{base}/sleep_millisecs"),
        "pages_to_scan": nextgen_read_int(f"{base}/pages_to_scan"),
    }
    sharing = int(values.get("pages_sharing") or 0)
    saved_mb = round(sharing * 4096 / (1024 * 1024), 1)
    return {
        "available": Path(base).exists(),
        "active": values.get("run") == 1,
        "values": values,
        "estimated_saved_mb": saved_mb,
        "state": "active" if values.get("run") == 1 else ("available" if Path(base).exists() else "missing"),
    }

def nextgen_netdev_snapshot():
    rows = []
    try:
        for line in Path("/proc/net/dev").read_text(encoding="utf-8", errors="ignore").splitlines()[2:]:
            if ":" not in line:
                continue
            iface, rest = line.split(":", 1)
            parts = rest.split()
            if len(parts) >= 16:
                rows.append({
                    "iface": iface.strip(),
                    "rx_bytes": int(parts[0]),
                    "rx_packets": int(parts[1]),
                    "tx_bytes": int(parts[8]),
                    "tx_packets": int(parts[9]),
                })
    except Exception:
        pass
    return sorted(rows, key=lambda item: item["rx_bytes"] + item["tx_bytes"], reverse=True)[:12]

def nextgen_ledger_status():
    lines = []
    try:
        lines.extend(LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()[-500:])
    except Exception:
        pass
    for source in [LOGIN_AUDIT_FILE, XOPS_AUDIT_FILE]:
        for row in read_json(source, [])[:120]:
            try:
                lines.append(json.dumps(row, sort_keys=True, ensure_ascii=False))
            except Exception:
                pass
    head = "0" * 64
    count = 0
    for line in lines[-500:]:
        head = hashlib.sha256(f"{head}|{line}".encode("utf-8", errors="ignore")).hexdigest()
        count += 1
    return {
        "algorithm": "sha256-chain",
        "events": count,
        "head": head,
        "tamper_evident": count > 0,
    }

def nextgen_recommendations(billing, ksm, disks):
    rows = []
    forecast = billing.get("forecast") or []
    for item in forecast:
        burn = float(item.get("hourly_burn", 0) or 0)
        if burn > 0:
            rows.append({
                "id": "finops-token-burn",
                "title": "Token burn active",
                "detail": f"{item.get('owner')} spala {burn} NXC/h przy {item.get('running_vms')} VM.",
                "level": "info",
            })
    if ksm.get("available") and not ksm.get("active"):
        rows.append({
            "id": "ksm-enable",
            "title": "KSM jest dostepny, ale nieaktywny",
            "detail": "Wlacz ksmtuned/KSM, aby deduplikowac RAM identycznych Windowsow.",
            "level": "warning",
        })
    for disk in disks:
        if float(disk.get("percent", 0) or 0) >= 85:
            rows.append({
                "id": f"disk-{disk.get('label')}",
                "title": "Dysk blisko limitu",
                "detail": f"{disk.get('label')} ma {disk.get('percent')}% zajetosci.",
                "level": "critical",
            })
    return rows[:10]

@app.get("/api/nextgen/status", dependencies=[Depends(verify_token)])
async def nextgen_status(user = Depends(verify_token)):
    tools = xops_tool_map()
    billing = vm_billing_live_public()
    ksm = nextgen_ksm_snapshot()
    disks = []
    for label, path in [("nexus-app", BASE_DIR), ("libvirt-images", LIBVIRT_IMAGE_DIR), ("backups", BACKUP_DIR)]:
        try:
            disks.append(disk_guard_snapshot(path, label))
        except Exception:
            pass
    ledger = nextgen_ledger_status()
    active_vms = sum(int(row.get("running_vms", 0) or 0) for row in billing.get("forecast", []) or [])
    hourly_burn_total = round(sum(float(row.get("hourly_burn", 0) or 0) for row in billing.get("forecast", []) or []), 4)
    readiness = [
        {"id": "spot", "title": "Spot Instances", "state": "design-ready", "score": 58, "detail": "Billing i token burn sa gotowe; preemption wymaga polityki zasobow."},
        {"id": "ksm", "title": "KSM Optimizer", "state": ksm.get("state"), "score": 92 if ksm.get("active") else (62 if ksm.get("available") else 15), "detail": f"Oszczedzone szacunkowo {ksm.get('estimated_saved_mb')} MB RAM."},
        {"id": "predictive", "title": "AI FinOps Advisor", "state": "advisory", "score": 44 if active_vms else 25, "detail": "Moze porownywac konfiguracje VM z realnym zuzyciem guest telemetry."},
        {"id": "cold", "title": "Cold Storage Auto-Archiver", "state": "tool-ready" if shutil.which("zstd") or shutil.which("qemu-img") else "missing-tools", "score": 64 if shutil.which("qemu-img") else 20, "detail": "qemu-img/ZSTD daja fundament do de-icing i archiwizacji."},
        {"id": "forensics", "title": "Forensic Quarantine", "state": "virsh-ready" if tools.get("virsh") else "missing-virsh", "score": 76 if tools.get("virsh") else 12, "detail": "XOPS ma RAM dump; kolejnym krokiem jest automatyczne odciecie NIC."},
        {"id": "ebpf", "title": "eBPF X-Ray", "state": "tool-ready" if shutil.which("bpftool") or shutil.which("bpftrace") else "pcap-fallback", "score": 42 if tools.get("tcpdump") else 18, "detail": "tcpdump dziala jako fallback przed pelnym eBPF."},
        {"id": "ledger", "title": "Private Audit Ledger", "state": "active" if ledger.get("tamper_evident") else "empty", "score": 84 if ledger.get("tamper_evident") else 28, "detail": f"Hash head: {ledger.get('head', '')[:14]}..."},
        {"id": "ovs", "title": "OVS / VXLAN", "state": "tool-ready" if shutil.which("ovs-vsctl") else "not-installed", "score": 70 if shutil.which("ovs-vsctl") else 16, "detail": "Wykrywa gotowosc pod SDN i live migration L2."},
        {"id": "edge", "title": "Edge Router", "state": "tool-ready" if shutil.which("haproxy") or shutil.which("nginx") else "planned", "score": 55 if shutil.which("nginx") else 22, "detail": "HAProxy/Nginx moga stac sie routerem kapsul."},
        {"id": "visuals", "title": "Visual Immersion 121-130", "state": "frontend-active", "score": 68, "detail": "Particle traffic, token burner i adaptive skin sa warstwa Managera."},
    ]
    return {
        "status": "live",
        "generated_at": now_iso(),
        "user": user.get("username", "user"),
        "backend": detect_vm_backend(),
        "active_vms": active_vms,
        "hourly_burn_total": hourly_burn_total,
        "billing": billing,
        "ksm": ksm,
        "memory": host_memory_snapshot(),
        "disks": disks,
        "netdev": nextgen_netdev_snapshot(),
        "ledger": ledger,
        "readiness": readiness,
        "recommendations": nextgen_recommendations(billing, ksm, disks),
        "policy": read_json(NEXTGEN_FILE, {"mode": "observe", "spot_enabled": False, "ksm_watch": True, "visual_intensity": 60}),
    }

@app.post("/api/nextgen/policy", dependencies=[Depends(verify_admin)])
async def nextgen_policy(data: NextGenPolicyRequest, admin = Depends(verify_admin)):
    state = data.dict()
    state["updated_at"] = now_iso()
    state["updated_by"] = admin.get("username", "admin")
    write_json(NEXTGEN_FILE, state)
    log_event(f"NEXTGEN POLICY mode={state['mode']} spot={state['spot_enabled']} by={state['updated_by']}")
    return {"status": "ok", "policy": state}

# --- PHASE 2: autonomy, tenants, SDN policy, serverless edge and local neural API ---
def phase2_default_policy():
    return {
        "enabled": False,
        "mode": "observe",
        "dry_run": True,
        "idle_cpu_threshold": 1.0,
        "idle_minutes": 30,
        "auto_suspend": False,
        "ram_autoscale": False,
        "ram_grow_threshold": 82.0,
        "ram_shrink_threshold": 32.0,
        "ram_step_mb": 512,
        "ram_min_mb": 512,
        "ram_cooldown_seconds": 120,
        "ram_last_action": {},
        "auto_heal": False,
        "rollback_snapshot": False,
        "iowait_threshold": 15.0,
        "disk_threshold": 90.0,
        "idle_seen": {},
        "updated_at": now_iso(),
        "updated_by": "system",
    }

def phase2_policy():
    policy = phase2_default_policy()
    stored = read_json(PHASE2_POLICY_FILE, {})
    if isinstance(stored, dict):
        policy.update(stored)
    if not isinstance(policy.get("idle_seen"), dict):
        policy["idle_seen"] = {}
    if not isinstance(policy.get("ram_last_action"), dict):
        policy["ram_last_action"] = {}
    return policy

def phase2_write_policy(policy: dict):
    write_json(PHASE2_POLICY_FILE, policy)
    return policy

def phase2_log(kind: str, payload: dict, level: str = "info"):
    row = {"time": now_iso(), "level": level, "kind": kind, "payload": payload}
    try:
        with open(NEXUS_LOG_DIR / "phase2.log", "a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        log_event(f"PHASE2_LOG error: {exc}")
    try:
        xops_audit(f"phase2.{kind}", level, payload)
    except Exception:
        pass
    return row

def phase2_clean_id(value: str, fallback="default"):
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", (value or fallback).strip()).strip(".-")
    return (clean or fallback)[:64]

def zt_network_name(tenant_id: str):
    clean = phase2_clean_id(tenant_id)
    return f"nexus-{clean[:42]}"

def zt_bridge_name(tenant_id: str):
    digest = hashlib.sha1(phase2_clean_id(tenant_id).encode("utf-8")).hexdigest()[:10]
    return f"nxt{digest}"[:15]

def zt_tenants():
    return read_json(PHASE2_TENANTS_FILE, [])

def zt_tenant_lookup(tenant_id: str):
    clean = phase2_clean_id(tenant_id)
    for row in zt_tenants():
        if row.get("tenant_id") == clean:
            return row
    raise HTTPException(status_code=404, detail=f"Nie znaleziono tenanta {clean}")

def zt_cidr_parts(cidr: str):
    raw = (cidr or "10.90.0.0/24").strip()
    try:
        network = ipaddress.ip_network(raw, strict=False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Niepoprawny CIDR tenanta: {raw}") from exc
    if network.version != 4:
        raise HTTPException(status_code=400, detail="Zero-Trust network obsluguje teraz IPv4 CIDR")
    if network.num_addresses < 4:
        raise HTTPException(status_code=400, detail="CIDR musi miec miejsce na gateway i DHCP")
    gateway = ipaddress.ip_address(int(network.network_address) + 1)
    start = ipaddress.ip_address(int(network.network_address) + 2) if network.num_addresses > 4 else gateway
    end = ipaddress.ip_address(int(network.broadcast_address) - 1)
    return {
        "cidr": str(network),
        "address": str(gateway),
        "netmask": str(network.netmask),
        "dhcp_start": str(start),
        "dhcp_end": str(end),
        "prefixlen": network.prefixlen,
    }

def zt_libvirt_network_xml(tenant: dict, nat: bool = True):
    tenant_id = phase2_clean_id(tenant.get("tenant_id"))
    cidr = zt_cidr_parts(tenant.get("cidr") or "10.90.0.0/24")
    name = zt_network_name(tenant_id)
    bridge = zt_bridge_name(tenant_id)
    forward = "  <forward mode='nat'/>\n" if nat else ""
    return (
        "<network>\n"
        f"  <name>{html.escape(name, quote=True)}</name>\n"
        f"  <bridge name='{html.escape(bridge, quote=True)}' stp='on' delay='0'/>\n"
        f"{forward}"
        f"  <ip address='{cidr['address']}' netmask='{cidr['netmask']}'>\n"
        "    <dhcp>\n"
        f"      <range start='{cidr['dhcp_start']}' end='{cidr['dhcp_end']}'/>\n"
        "    </dhcp>\n"
        "  </ip>\n"
        "</network>\n"
    )

def zt_libvirt_network_info(name: str):
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "", name or "")
    if not clean:
        return {"exists": False, "active": False, "autostart": False}
    code, output = run_vm_command(["virsh", "net-info", clean], timeout=8)
    info = {"name": clean, "exists": code == 0, "active": False, "autostart": False, "raw": output.strip()}
    if code == 0:
        for line in output.splitlines():
            if ":" not in line:
                continue
            key, value = [part.strip() for part in line.split(":", 1)]
            lk = key.lower()
            if lk == "active":
                info["active"] = value.lower().startswith("yes")
            elif lk == "autostart":
                info["autostart"] = value.lower().startswith("yes")
            elif lk == "bridge":
                info["bridge"] = value
    return info

def zt_tenant_network_plan(tenant: dict, nat: bool = True, autostart: bool = True):
    tenant_id = phase2_clean_id(tenant.get("tenant_id"))
    name = zt_network_name(tenant_id)
    bridge = zt_bridge_name(tenant_id)
    cidr = zt_cidr_parts(tenant.get("cidr") or "10.90.0.0/24")
    xml = zt_libvirt_network_xml(tenant, nat=nat)
    commands = [
        ["virsh", "net-define", f"/tmp/{name}.xml"],
        ["virsh", "net-start", name],
    ]
    if autostart:
        commands.insert(1, ["virsh", "net-autostart", name])
    vxlan_id = int(tenant.get("vxlan_id") or 0)
    vxlan = []
    if vxlan_id:
        vxlan = [
            ["ip", "link", "add", f"vx{vxlan_id}", "type", "vxlan", "id", str(vxlan_id), "dstport", "4789"],
            ["ip", "link", "set", f"vx{vxlan_id}", "master", bridge],
            ["ip", "link", "set", f"vx{vxlan_id}", "up"],
        ]
    return {
        "tenant_id": tenant_id,
        "network": name,
        "bridge": bridge,
        "cidr": cidr,
        "nat": bool(nat),
        "autostart": bool(autostart),
        "xml": xml,
        "commands": commands,
        "vxlan_ready_plan": vxlan,
        "current": zt_libvirt_network_info(name) if shutil.which("virsh") else {"exists": False, "tool": "missing virsh"},
        "note": "VXLAN jest przygotowany jako plan. Domyslnie live apply tworzy bezpieczna siec libvirt NAT i izoluje tenant bridges przez nft.",
    }

def zt_apply_tenant_network(tenant: dict, nat: bool = True, autostart: bool = True):
    if not shutil.which("virsh"):
        raise HTTPException(status_code=501, detail="Brak virsh na hoscie")
    plan = zt_tenant_network_plan(tenant, nat=nat, autostart=autostart)
    info = plan.get("current") or {}
    results = []
    name = plan["network"]
    if not info.get("exists"):
        tmp_path = Path(tempfile.gettempdir()) / f"{name}-{uuid.uuid4().hex[:8]}.xml"
        try:
            tmp_path.write_text(plan["xml"], encoding="utf-8")
            results.append(xops_command(["virsh", "net-define", str(tmp_path)], timeout=12))
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
    if autostart:
        results.append(xops_command(["virsh", "net-autostart", name], timeout=8))
    info_after_define = zt_libvirt_network_info(name)
    if not info_after_define.get("active"):
        results.append(xops_command(["virsh", "net-start", name], timeout=12))
    final = zt_libvirt_network_info(name)
    failed = [
        row for row in results
        if not row.get("ok") and "already active" not in (row.get("output") or "").lower() and "marked as autostarted" not in (row.get("output") or "").lower()
    ]
    if failed:
        raise HTTPException(status_code=500, detail={"message": "Nie udalo sie przygotowac sieci tenanta", "plan": plan, "results": results, "final": final})
    return {"status": "applied", "plan": plan, "results": results, "network": final}

def zt_all_bridge_names():
    bridges = []
    for tenant in zt_tenants():
        tenant_id = phase2_clean_id(tenant.get("tenant_id"))
        if tenant_id:
            bridges.append({"tenant_id": tenant_id, "network": zt_network_name(tenant_id), "bridge": zt_bridge_name(tenant_id), "cidr": tenant.get("cidr", "")})
    return bridges

def zt_firewall_isolation_plan():
    bridges = zt_all_bridge_names()
    commands = [
        ["nft", "add", "table", "inet", "nexus_zt"],
        ["nft", "add", "chain", "inet", "nexus_zt", "forward", "{", "type", "filter", "hook", "forward", "priority", "-50", ";", "policy", "accept", ";", "}"],
        ["nft", "flush", "chain", "inet", "nexus_zt", "forward"],
        ["nft", "add", "rule", "inet", "nexus_zt", "forward", "ct", "state", "established,related", "accept"],
    ]
    for left in bridges:
        for right in bridges:
            if left["bridge"] == right["bridge"]:
                continue
            commands.append(["nft", "add", "rule", "inet", "nexus_zt", "forward", "iifname", left["bridge"], "oifname", right["bridge"], "drop"])
    return {
        "table": "inet nexus_zt",
        "chain": "forward",
        "bridges": bridges,
        "commands": commands,
        "note": "Reguly blokują ruch bridge->bridge miedzy tenantami, ale nie odcinaja hosta ani wyjscia NAT/WAN.",
    }

def zt_apply_commands(commands, timeout=8):
    results = []
    for cmd in commands:
        result = xops_command(cmd, timeout=timeout)
        output = (result.get("output") or "").lower()
        if not result.get("ok") and ("file exists" in output or "object already exists" in output):
            result["ok"] = True
            result["noop"] = True
        results.append(result)
    failed = [row for row in results if not row.get("ok")]
    if failed:
        raise HTTPException(status_code=500, detail={"message": "Zero-Trust firewall apply nie powiodl sie", "failed": failed, "results": results})
    return results

def zt_vm_attach_plan(data: ZeroTrustVmAttachRequest, tenant: dict):
    target = safe_vm_target(data.vm_id)
    network = zt_network_name(tenant.get("tenant_id"))
    model = re.sub(r"[^A-Za-z0-9_.-]+", "", data.model or "virtio") or "virtio"
    flags = vm_network_flags(target, data.live, data.config)
    commands = []
    if data.replace_existing:
        for iface in vm_interface_rows(target):
            if iface.get("mac"):
                commands.append(["virsh", "detach-interface", target, "--type", "network", "--mac", iface["mac"]] + flags)
    commands.append(["virsh", "attach-interface", target, "--type", "network", "--source", network, "--model", model] + flags)
    return {"vm_id": target, "tenant_id": phase2_clean_id(tenant.get("tenant_id")), "network": network, "model": model, "flags": flags, "replace_existing": data.replace_existing, "commands": commands}

def zt_attach_vm_to_tenant(data: ZeroTrustVmAttachRequest, tenant: dict):
    network_state = zt_apply_tenant_network(tenant, nat=True, autostart=True)
    target = safe_vm_target(data.vm_id)
    flags = vm_network_flags(target, data.live, data.config)
    detach_results = []
    if data.replace_existing:
        for iface in vm_interface_rows(target):
            mac = iface.get("mac")
            if not mac:
                continue
            code, output = run_vm_command(["virsh", "detach-interface", target, "--type", "network", "--mac", mac] + flags, timeout=30)
            detach_results.append({"command": "detach-interface", "mac": mac, "code": code, "ok": code == 0, "output": output.strip()})
            if code != 0 and "not found" not in output.lower():
                raise HTTPException(status_code=500, detail={"message": "Nie udalo sie odpiac starego interfejsu VM", "results": detach_results})
    attached = set_vm_network(target, True, zt_network_name(tenant.get("tenant_id")), data.model, data.live, data.config)
    return {"status": "attached", "network_state": network_state, "detach_results": detach_results, "attached": attached, "interfaces": vm_interface_rows(target)}

def phase2_host_matrix():
    cpu = {"percent": 0, "iowait_percent": 0, "load_avg": ""}
    memory = host_memory_snapshot()
    if HAS_PSUTIL:
        try:
            cpu["percent"] = psutil.cpu_percent(interval=0.08)
            times = psutil.cpu_times_percent(interval=0.05)
            cpu["iowait_percent"] = round(float(getattr(times, "iowait", 0) or 0), 2)
        except Exception:
            pass
    try:
        cpu["load_avg"] = " / ".join(f"{value:.2f}" for value in os.getloadavg())
    except Exception:
        cpu["load_avg"] = "n/a"
    disks = []
    for label, path in [("nexus-app", BASE_DIR), ("libvirt-images", LIBVIRT_IMAGE_DIR), ("iso-storage", NEXUS_ISO_STORAGE_DIR), ("backups", BACKUP_DIR)]:
        try:
            disks.append(disk_guard_snapshot(path, label))
        except Exception:
            pass
    io = {}
    if HAS_PSUTIL:
        try:
            counters = psutil.disk_io_counters()
            if counters:
                io = {"read_bytes": counters.read_bytes, "write_bytes": counters.write_bytes, "read_count": counters.read_count, "write_count": counters.write_count}
        except Exception:
            pass
    return {
        "generated_at": now_iso(),
        "cpu": cpu,
        "memory": memory,
        "disks": disks,
        "io": io,
        "netdev": nextgen_netdev_snapshot(),
        "tools": {
            "virsh": bool(shutil.which("virsh")),
            "nft": bool(shutil.which("nft")),
            "iptables": bool(shutil.which("iptables")),
            "ovs-vsctl": bool(shutil.which("ovs-vsctl")),
            "bpftool": bool(shutil.which("bpftool")),
            "docker": bool(shutil.which("docker")),
            "qemu-img": bool(shutil.which("qemu-img")),
            "ollama": bool(shutil.which("ollama")),
        },
    }

def phase2_vm_matrix():
    billing = vm_billing_live_public()
    runtime = billing.get("runtime") or {}
    rows = []
    for item in vm_inventory_for_billing():
        vm_id = item.get("id") or item.get("name") or ""
        pid = find_qemu_pid(vm_id)
        telemetry = vm_process_telemetry(pid)
        rows.append({
            "vm_id": vm_id,
            "name": item.get("name") or vm_id,
            "status": item.get("status", "unknown"),
            "running": vm_is_running(item),
            "pid": pid,
            "cpu_percent": telemetry.get("cpu_percent"),
            "memory_mb": telemetry.get("mem_mb"),
            "billing": runtime.get(vm_id, {}),
            "guest": latest_guest_telemetry(vm_id),
        })
    return rows

def vm_dommemstat(vm_id: str):
    target = safe_vm_target(vm_id)
    code, output = run_vm_command(["virsh", "dommemstat", target], timeout=8)
    stats = {"ok": False, "raw": output.strip()[:1000], "code": code}
    if code != 0:
        return stats
    for line in output.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        try:
            stats[parts[0].strip()] = round(int(parts[1]) / 1024, 1)
        except Exception:
            pass
    actual = float(stats.get("actual") or 0)
    unused_present = "unused" in stats
    unused = float(stats.get("unused") or 0)
    available = float(stats.get("available") or 0)
    usable_total = available or actual
    if usable_total > 0 and unused_present:
        stats["memory_percent"] = round(max(0.0, min(100.0, ((usable_total - unused) / usable_total) * 100.0)), 1)
        stats["ok"] = True
    elif actual > 0:
        rss = float(stats.get("rss") or 0)
        stats["memory_percent"] = round(max(0.0, min(100.0, (rss / actual) * 100.0)), 1)
        stats["ok"] = True
    return stats

def phase2_ram_signal(vm_id: str):
    target = safe_vm_target(vm_id)
    guest = latest_guest_telemetry(target)
    if guest and guest.get("online") and float(guest.get("memory_total_mb") or 0) > 0:
        return {
            "source": "guest-agent",
            "memory_percent": round(float(guest.get("memory_percent") or 0), 1),
            "memory_used_mb": float(guest.get("memory_used_mb") or 0),
            "memory_total_mb": float(guest.get("memory_total_mb") or 0),
            "age_seconds": guest.get("age_seconds"),
        }
    stat = vm_dommemstat(target)
    if stat.get("ok") and "memory_percent" in stat:
        stat_total = float(stat.get("actual") or stat.get("available") or 0)
        stat_used = max(0.0, stat_total - float(stat.get("unused") or 0)) if "unused" in stat else float(stat.get("rss") or 0)
        return {
            "source": "dommemstat",
            "memory_percent": float(stat.get("memory_percent") or 0),
            "memory_used_mb": stat_used,
            "memory_total_mb": stat_total,
            "stats": stat,
        }
    return {"source": "none", "memory_percent": None, "memory_used_mb": 0, "memory_total_mb": 0, "stats": stat}

def phase2_ram_autoscale_one(vm_id: str, policy: dict, execute: bool = False):
    target = safe_vm_target(vm_id)
    info = parse_dominfo(target)
    if "running" not in str(info.get("state", "")).lower():
        return {"vm_id": target, "status": "skipped", "reason": "VM nie dziala", "info": info}
    config = vm_memory_xml_state(target, inactive=True)
    target_mb = int(config.get("memory_mb") or info.get("max_memory_mb") or 0)
    current_mb = int(info.get("used_memory_mb") or config.get("current_memory_mb") or target_mb or 0)
    if target_mb <= 0 or current_mb <= 0:
        return {"vm_id": target, "status": "skipped", "reason": "Brak danych RAM z libvirt", "info": info, "config": config}
    signal = phase2_ram_signal(target)
    percent = signal.get("memory_percent")
    if percent is None:
        return {"vm_id": target, "status": "observed", "reason": "Brak pewnego sygnalu RAM", "signal": signal, "info": info, "config": config}

    step_mb = round_down_memory_mb(int(policy.get("ram_step_mb") or 512), 128)
    config_floor_mb = int(config.get("current_memory_mb") or 0)
    minimum_mb = max(128, min(target_mb, max(round_down_memory_mb(int(policy.get("ram_min_mb") or 512), 128), config_floor_mb)))
    grow_threshold = float(policy.get("ram_grow_threshold", 82.0) or 82.0)
    shrink_threshold = float(policy.get("ram_shrink_threshold", 32.0) or 32.0)
    cooldown = int(policy.get("ram_cooldown_seconds", 120) or 120)
    last_actions = policy.setdefault("ram_last_action", {})
    last_dt = iso_dt(last_actions.get(target))
    if last_dt and (datetime.datetime.now() - last_dt).total_seconds() < cooldown:
        return {"vm_id": target, "status": "cooldown", "memory_percent": percent, "current_memory_mb": current_mb, "target_memory_mb": target_mb, "signal": signal}

    wanted_mb = current_mb
    action = "hold"
    if percent >= grow_threshold and current_mb < target_mb:
        wanted_mb = min(target_mb, round_down_memory_mb(current_mb + step_mb, 128))
        action = "grow"
    elif percent <= shrink_threshold and current_mb > minimum_mb:
        wanted_mb = max(minimum_mb, round_down_memory_mb(current_mb - step_mb, 128))
        action = "shrink"

    result = {
        "vm_id": target,
        "status": "planned" if action != "hold" else "observed",
        "action": action,
        "memory_percent": percent,
        "current_memory_mb": current_mb,
        "wanted_memory_mb": wanted_mb,
        "target_memory_mb": target_mb,
        "min_memory_mb": minimum_mb,
        "signal": signal,
    }
    if action == "hold":
        return result
    if not execute:
        result["dry_run"] = True
        return result

    code, output = run_vm_command(["virsh", "setmem", target, f"{wanted_mb}M", "--live"], timeout=30)
    result.update({"dry_run": False, "code": code, "ok": code == 0, "output": output.strip()})
    if code == 0:
        last_actions[target] = now_iso()
        result["status"] = "changed"
    else:
        result["status"] = "error"
    return result

def phase2_predictive_alerts(matrix: dict, policy: dict):
    alerts = []
    iowait = float((matrix.get("cpu") or {}).get("iowait_percent") or 0)
    if iowait >= float(policy.get("iowait_threshold", 15.0) or 15.0):
        alerts.append({"level": "critical", "title": "I/O wait przekracza prog", "detail": f"iowait={iowait}% threshold={policy.get('iowait_threshold')}"})
    for disk in matrix.get("disks") or []:
        pct = float(disk.get("used_pct", 0) or 0)
        if pct >= float(policy.get("disk_threshold", 90.0) or 90.0):
            alerts.append({"level": "critical", "title": "Dysk blisko limitu", "detail": f"{disk.get('label')} {pct}% zajete"})
    available = float((matrix.get("memory") or {}).get("available_mb", 0) or 0)
    total = float((matrix.get("memory") or {}).get("total_mb", 0) or 0)
    if total and available / total < 0.08:
        alerts.append({"level": "warn", "title": "Malo wolnej pamieci", "detail": f"available={round(available)}MB total={round(total)}MB"})
    return alerts

async def phase2_autonomy_tick(execute: bool = False, actor: str = "system"):
    policy = phase2_policy()
    matrix = phase2_host_matrix()
    vms = phase2_vm_matrix()
    now = datetime.datetime.now()
    idle_seen = policy.setdefault("idle_seen", {})
    actions = []
    ram_results = []
    threshold = float(policy.get("idle_cpu_threshold", 1.0) or 1.0)
    idle_seconds = int(policy.get("idle_minutes", 30) or 30) * 60
    can_execute = execute and bool(policy.get("enabled")) and not bool(policy.get("dry_run")) and str(policy.get("confirm") or "") == "EXECUTE-AUTONOMY"
    for vm in vms:
        vm_id = vm.get("vm_id")
        if not vm.get("running") or not vm_id:
            idle_seen.pop(vm_id, None)
            continue
        cpu_value = vm.get("cpu_percent")
        if cpu_value is None or float(cpu_value) > threshold:
            idle_seen.pop(vm_id, None)
            continue
        first = iso_dt(idle_seen.get(vm_id)) or now
        idle_seen.setdefault(vm_id, first.isoformat(timespec="seconds"))
        duration = (now - first).total_seconds()
        if duration >= idle_seconds:
            actions.append({"kind": "idle-suspend", "vm_id": vm_id, "idle_seconds": round(duration), "cpu_percent": cpu_value, "planned": "virsh save -> Hyper-Sleep"})
    if bool(policy.get("ram_autoscale")):
        for vm in vms:
            vm_id = vm.get("vm_id")
            if not vm.get("running") or not vm_id:
                continue
            try:
                ram_results.append(phase2_ram_autoscale_one(vm_id, policy, execute=can_execute))
            except Exception as exc:
                ram_results.append({"vm_id": vm_id, "status": "error", "error": str(exc)})
    alerts = phase2_predictive_alerts(matrix, policy)
    for alert in alerts:
        record_alert(alert["title"], alert["detail"], alert["level"], f"phase2-{hashlib.sha1(alert['detail'].encode()).hexdigest()[:8]}")
    results = []
    if can_execute and policy.get("auto_suspend"):
        for action in actions[:3]:
            try:
                result = await hyper_sleep_freeze(HyperSleepRequest(vm_id=action["vm_id"], label="phase2-idle"), admin={"username": actor})
                results.append({"vm_id": action["vm_id"], "status": "frozen", "state": result})
            except Exception as exc:
                results.append({"vm_id": action["vm_id"], "status": "error", "error": str(exc)})
    phase2_write_policy(policy)
    executed_any = bool(results or [r for r in ram_results if r.get("status") == "changed"])
    row = {"policy_mode": policy.get("mode"), "execute_requested": execute, "executed": executed_any, "alerts": alerts, "actions": actions, "ram_autoscale": ram_results, "results": results}
    phase2_log("autonomy_tick", row, "info")
    return {"status": "executed" if executed_any else "observed", "matrix": matrix, "vms": vms, **row}

def phase2_network_rule_plan(row: dict, tenant: dict = None):
    tenant_id = phase2_clean_id(row.get("tenant_id", "default"))
    chain = f"tenant_{tenant_id.replace('-', '_')[:48]}"
    bridge = zt_bridge_name(tenant_id)
    network = zt_network_name(tenant_id)
    proto = (row.get("proto") or "tcp").lower()
    action = (row.get("action") or "allow").lower()
    direction = (row.get("direction") or "ingress").lower()
    if proto not in {"tcp", "udp", "icmp", "all"}:
        raise HTTPException(status_code=400, detail="proto: tcp/udp/icmp/all")
    if action not in {"allow", "deny", "drop", "reject"}:
        raise HTTPException(status_code=400, detail="action: allow/deny/drop/reject")
    if direction not in {"ingress", "egress"}:
        raise HTTPException(status_code=400, detail="direction: ingress/egress")
    verdict = "accept" if action == "allow" else "drop"
    src = (row.get("source") or "0.0.0.0/0").strip()
    dst = (row.get("destination") or "").strip()
    port = int(row.get("port") or 0)
    commands = [
        ["nft", "add", "table", "inet", "nexus_zt"],
        ["nft", "add", "chain", "inet", "nexus_zt", chain, "{", "type", "filter", "hook", "forward", "priority", "-40", ";", "policy", "accept", ";", "}"],
    ]
    rule = ["nft", "add", "rule", "inet", "nexus_zt", chain]
    rule.extend(["oifname" if direction == "ingress" else "iifname", bridge])
    if proto == "icmp":
        rule.extend(["ip", "protocol", "icmp"])
    elif proto in {"tcp", "udp"}:
        rule.append(proto)
        if port:
            rule.extend(["dport" if direction == "ingress" else "sport", str(port)])
    if src and src != "0.0.0.0/0":
        rule.extend(["ip", "saddr", src])
    if dst:
        rule.extend(["ip", "daddr", dst])
    rule.append(verdict)
    commands.append(rule)
    return {
        "tenant": tenant_id,
        "network": network,
        "bridge": bridge,
        "chain": chain,
        "deny_by_default": bool((tenant or {}).get("deny_by_default", True)),
        "note": "Regula jest przypieta do bridge tenanta. Globalna izolacja inter-tenant siedzi w tabeli inet nexus_zt.",
        "commands": commands,
    }

def phase2_bearer_user(request: Request):
    token = request.headers.get("x-auth-token") or ""
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth.split(None, 1)[1].strip()
    user = SESSIONS.get(token or "")
    if not user:
        raise HTTPException(status_code=401, detail="Brak poprawnego tokenu NEXUS")
    return user

def edge_slug(value: str, fallback="edge-function"):
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "-", (value or fallback).strip().lower()).strip("-")
    return (clean or fallback)[:80]

def edge_public_function(row):
    out = dict(row)
    out.pop("code", None)
    out["endpoint"] = f"/edge/{row.get('slug')}"
    return out

def edge_functions():
    return read_json(EDGE_FUNCTIONS_FILE, [])

def save_edge_functions(rows):
    write_json(EDGE_FUNCTIONS_FILE, rows[:500])

def edge_secret_key(scope: str, name: str):
    return f"{edge_slug(scope, 'global')}::{re.sub(r'[^A-Za-z0-9_]+', '_', (name or '').upper()).strip('_')[:80]}"

def edge_secret_mask(value: str):
    value = str(value or "")
    if len(value) <= 6:
        return "*" * len(value)
    return value[:3] + "*" * max(3, len(value) - 6) + value[-3:]

def edge_secret_env(scope: str):
    raw = read_json(EDGE_SECRETS_FILE, {})
    env = {}
    for key, row in raw.items():
        try:
            item_scope, name = key.split("::", 1)
        except ValueError:
            continue
        if item_scope in {"global", edge_slug(scope, "global")}:
            env[f"NEXUS_SECRET_{name}"] = row.get("value", "")
    return env

def edge_record_run(function_row: dict, result: dict, elapsed_ms: float, status_code: int, path: str):
    run = {
        "id": uuid.uuid4().hex[:12],
        "function_id": function_row.get("id"),
        "slug": function_row.get("slug"),
        "runtime": function_row.get("runtime"),
        "path": path,
        "status_code": status_code,
        "elapsed_ms": round(float(elapsed_ms), 2),
        "ok": status_code < 500 and int(result.get("code", 0) or 0) == 0,
        "stdout": (result.get("stdout") or "")[-4000:],
        "stderr": (result.get("stderr") or "")[-4000:],
        "created_at": now_iso(),
    }
    rows = read_json(EDGE_RUNS_FILE, [])
    rows.insert(0, run)
    write_json(EDGE_RUNS_FILE, rows[:1000])
    return run

def edge_metrics(slug: str = ""):
    rows = read_json(EDGE_RUNS_FILE, [])
    if slug:
        rows = [row for row in rows if row.get("slug") == slug]
    now = datetime.datetime.now()
    recent = []
    for row in rows:
        dt = iso_dt(row.get("created_at"))
        if dt and (now - dt).total_seconds() <= 60:
            recent.append(row)
    latencies = [float(row.get("elapsed_ms", 0) or 0) for row in rows[:200]]
    return {
        "total_runs": len(rows),
        "rps_60s": round(len(recent) / 60.0, 3),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95) - 1] if len(latencies) >= 2 else (latencies[0] if latencies else 0),
        "errors": len([row for row in rows if not row.get("ok", True)]),
        "recent": rows[:80],
    }

def edge_runtime_command(runtime: str, code: str, event: dict, tmp: str):
    runtime = (runtime or "python").lower()
    if runtime == "python":
        exe = shutil.which("python3") or shutil.which("python")
        if not exe:
            raise HTTPException(status_code=501, detail="Brak python runtime")
        user_script = Path(tmp) / "user_function.py"
        runner = Path(tmp) / "runner.py"
        user_script.write_text(code, encoding="utf-8")
        runner.write_text(
            "import json, os, runpy\n"
            "event=json.loads(os.environ.get('NEXUS_EDGE_EVENT','{}'))\n"
            "ns=runpy.run_path('user_function.py')\n"
            "handler=ns.get('handler')\n"
            "if callable(handler):\n"
            "    result=handler(event)\n"
            "    print(json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result)\n",
            encoding="utf-8",
        )
        return [exe, "-I", str(runner)]
    if runtime in {"javascript", "js", "node"}:
        exe = shutil.which("node")
        if not exe:
            raise HTTPException(status_code=501, detail="Brak node runtime")
        user_script = Path(tmp) / "user_function.mjs"
        runner = Path(tmp) / "runner.mjs"
        user_script.write_text(code, encoding="utf-8")
        runner.write_text(
            "const event = JSON.parse(process.env.NEXUS_EDGE_EVENT || '{}');\n"
            "const mod = await import('./user_function.mjs');\n"
            "if (typeof mod.handler === 'function') {\n"
            "  const result = await mod.handler(event);\n"
            "  console.log(typeof result === 'string' ? result : JSON.stringify(result));\n"
            "}\n",
            encoding="utf-8",
        )
        return [exe, str(runner)]
    raise HTTPException(status_code=400, detail="Runtime: python/javascript")

def edge_output_response(stdout: str, stderr: str, exit_code: int, elapsed_ms: float):
    status = 200 if exit_code == 0 else 500
    body = stdout or stderr or ""
    headers = {"X-NEXUS-Edge-Latency-Ms": str(round(elapsed_ms, 2))}
    try:
        parsed = json.loads(stdout)
        if isinstance(parsed, dict) and any(key in parsed for key in ("body", "statusCode", "headers")):
            status = int(parsed.get("statusCode") or status)
            if isinstance(parsed.get("headers"), dict):
                headers.update({str(k): str(v) for k, v in parsed["headers"].items()})
            body = parsed.get("body", "")
            if not isinstance(body, str):
                body = json.dumps(body, ensure_ascii=False)
        elif isinstance(parsed, (dict, list)):
            body = json.dumps(parsed, ensure_ascii=False)
            headers.setdefault("Content-Type", "application/json; charset=utf-8")
    except Exception:
        headers.setdefault("Content-Type", "text/plain; charset=utf-8")
    return status, headers, body

async def execute_edge_function(row: dict, request: Request):
    body = await request.body()
    event = {
        "method": request.method,
        "path": str(request.url.path),
        "query": dict(request.query_params),
        "headers": {k: v for k, v in request.headers.items() if k.lower() not in {"authorization", "cookie", "x-auth-token"}},
        "body": body.decode("utf-8", errors="replace"),
    }
    started = datetime.datetime.now()
    with tempfile.TemporaryDirectory(prefix="nexus-edge-") as tmp:
        cmd = edge_runtime_command(row.get("runtime", "python"), row.get("code", ""), event, tmp)
        env = {"PATH": os.environ.get("PATH", ""), "HOME": tmp, "NEXUS_EDGE_EVENT": json.dumps(event, ensure_ascii=False)}
        env.update(edge_secret_env(row.get("slug", "")))
        try:
            proc = await asyncio.to_thread(subprocess.run, cmd, cwd=tmp, text=True, capture_output=True, timeout=int(row.get("timeout", 5)), env=env)
            result = {"code": proc.returncode, "stdout": proc.stdout[-12000:], "stderr": proc.stderr[-12000:]}
        except subprocess.TimeoutExpired as exc:
            result = {"code": 124, "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "", "stderr": "Timeout edge function"}
    elapsed = (datetime.datetime.now() - started).total_seconds() * 1000
    status, headers, response_body = edge_output_response(result.get("stdout", ""), result.get("stderr", ""), int(result.get("code", 1)), elapsed)
    edge_record_run(row, result, elapsed, status, str(request.url.path))
    return Response(content=response_body, status_code=status, headers=headers)

def neural_cache_key(payload: dict):
    clean = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()

def neural_openai_response(model: str, text: str, cache_hit=False):
    return {
        "id": "chatcmpl-nexus-" + uuid.uuid4().hex[:12],
        "object": "chat.completion",
        "created": int(datetime.datetime.now().timestamp()),
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "nexus": {"provider": "local", "cache_hit": cache_hit},
    }

def neural_call_ollama(payload: dict):
    model = payload.get("model") or "llama3"
    messages = payload.get("messages") or []
    req_payload = json.dumps({"model": model, "messages": messages, "stream": False, "options": {"temperature": float(payload.get("temperature", 0.2) or 0.2)}}).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=req_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8", errors="replace"))
    content = ((data.get("message") or {}).get("content") or "").strip()
    return neural_openai_response(model, content or json.dumps(data, ensure_ascii=False))

@app.get("/api/phase2/status", dependencies=[Depends(verify_token)])
async def phase2_status():
    policy = phase2_policy()
    matrix = phase2_host_matrix()
    billing = vm_billing_live_public()
    return {
        "status": "live",
        "policy": {k: v for k, v in policy.items() if k != "idle_seen"},
        "host": matrix,
        "vms": phase2_vm_matrix(),
        "billing": billing,
        "tenants": read_json(PHASE2_TENANTS_FILE, []),
        "network_rules": read_json(PHASE2_NETWORK_RULES_FILE, [])[:100],
        "nano_recipes": read_json(PHASE2_NANO_RECIPES_FILE, [])[:100],
        "forge_builds": read_json(PHASE2_FORGE_BUILDS_FILE, [])[:80],
        "predictive_alerts": phase2_predictive_alerts(matrix, policy),
        "edge": edge_metrics(),
    }

@app.get("/api/phase2/autonomy/policy", dependencies=[Depends(verify_token)])
async def phase2_autonomy_policy_get():
    policy = phase2_policy()
    return {"policy": {k: v for k, v in policy.items() if k != "idle_seen"}, "idle_seen": policy.get("idle_seen", {})}

@app.post("/api/phase2/autonomy/policy", dependencies=[Depends(verify_admin)])
async def phase2_autonomy_policy_set(data: Phase2AutonomyPolicyRequest, admin = Depends(verify_admin)):
    policy = phase2_policy()
    policy.update(data.dict())
    policy["updated_at"] = now_iso()
    policy["updated_by"] = admin.get("username", "admin")
    if not data.enabled or data.dry_run:
        policy["confirm"] = data.confirm
    phase2_write_policy(policy)
    phase2_log("policy_update", {k: v for k, v in policy.items() if k != "idle_seen"}, "info")
    return {"status": "saved", "policy": {k: v for k, v in policy.items() if k != "idle_seen"}}

@app.post("/api/phase2/autonomy/tick", dependencies=[Depends(verify_admin)])
async def phase2_autonomy_tick_api(data: StorageRetentionRunRequest, admin = Depends(verify_admin)):
    policy = phase2_policy()
    if data.confirm:
        policy["confirm"] = data.confirm
        phase2_write_policy(policy)
    return await phase2_autonomy_tick(execute=not data.dry_run, actor=admin.get("username", "admin"))

@app.get("/api/phase2/tenants", dependencies=[Depends(verify_token)])
async def phase2_tenants():
    return {"items": read_json(PHASE2_TENANTS_FILE, [])}

@app.post("/api/phase2/tenants", dependencies=[Depends(verify_admin)])
async def phase2_tenant_save(data: Phase2TenantRequest, admin = Depends(verify_admin)):
    tenant_id = phase2_clean_id(data.tenant_id)
    row = data.dict()
    row["tenant_id"] = tenant_id
    row["id"] = tenant_id
    row["owner"] = normalize_username(row.get("owner") or "admin")
    row["updated_at"] = now_iso()
    row["updated_by"] = admin.get("username", "admin")
    rows = [item for item in read_json(PHASE2_TENANTS_FILE, []) if item.get("tenant_id") != tenant_id]
    rows.insert(0, row)
    write_json(PHASE2_TENANTS_FILE, rows[:500])
    phase2_log("tenant_save", row, "info")
    return {"status": "saved", "tenant": row}

@app.post("/api/phase2/tenants/delete", dependencies=[Depends(verify_admin)])
async def phase2_tenant_delete(data: Phase2DeleteRequest, admin = Depends(verify_admin)):
    tenant_id = phase2_clean_id(data.id)
    write_json(PHASE2_TENANTS_FILE, [item for item in read_json(PHASE2_TENANTS_FILE, []) if item.get("tenant_id") != tenant_id])
    phase2_log("tenant_delete", {"tenant_id": tenant_id, "by": admin.get("username", "admin")}, "warn")
    return {"status": "deleted", "tenant_id": tenant_id}

@app.get("/api/zero-trust/status", dependencies=[Depends(verify_token)])
async def zero_trust_status():
    tenants = zt_tenants()
    networks = []
    for tenant in tenants:
        tenant_id = phase2_clean_id(tenant.get("tenant_id"))
        networks.append({
            "tenant_id": tenant_id,
            "cidr": tenant.get("cidr", ""),
            "vxlan_id": tenant.get("vxlan_id", 0),
            "network": zt_network_name(tenant_id),
            "bridge": zt_bridge_name(tenant_id),
            "libvirt": zt_libvirt_network_info(zt_network_name(tenant_id)) if shutil.which("virsh") else {"exists": False, "tool": "missing virsh"},
        })
    nft_table = None
    if shutil.which("nft"):
        nft_table = xops_command(["nft", "list", "table", "inet", "nexus_zt"], timeout=8)
    return {
        "status": "live",
        "mode": "deny-inter-tenant / allow-wan",
        "confirm_phrase": "APPLY-ZERO-TRUST",
        "tools": {"virsh": bool(shutil.which("virsh")), "nft": bool(shutil.which("nft")), "ip": bool(shutil.which("ip"))},
        "tenants": tenants,
        "networks": networks,
        "firewall_plan": zt_firewall_isolation_plan(),
        "nft": nft_table,
    }

@app.post("/api/zero-trust/tenant/network", dependencies=[Depends(verify_admin)])
async def zero_trust_tenant_network(data: ZeroTrustTenantNetworkRequest, admin = Depends(verify_admin)):
    tenant = zt_tenant_lookup(data.tenant_id)
    plan = zt_tenant_network_plan(tenant, nat=data.nat, autostart=data.autostart)
    if not data.apply:
        return {"status": "planned", "plan": plan}
    if data.confirm != "APPLY-ZERO-TRUST":
        raise HTTPException(status_code=403, detail="Aby utworzyc live siec tenanta wpisz confirm=APPLY-ZERO-TRUST")
    result = zt_apply_tenant_network(tenant, nat=data.nat, autostart=data.autostart)
    phase2_log("zero_trust_network_apply", {"tenant_id": phase2_clean_id(data.tenant_id), "result": result}, "info")
    return result

@app.post("/api/zero-trust/firewall/apply", dependencies=[Depends(verify_admin)])
async def zero_trust_firewall_apply(data: ZeroTrustFirewallApplyRequest, admin = Depends(verify_admin)):
    plan = zt_firewall_isolation_plan()
    if not data.apply:
        return {"status": "planned", "plan": plan}
    if data.confirm != "APPLY-ZERO-TRUST":
        raise HTTPException(status_code=403, detail="Aby wykonac live izolacje nft wpisz confirm=APPLY-ZERO-TRUST")
    if not shutil.which("nft"):
        raise HTTPException(status_code=501, detail="Brak nft na hoscie")
    results = zt_apply_commands(plan["commands"], timeout=8)
    phase2_log("zero_trust_firewall_apply", {"plan": plan, "results": results, "by": admin.get("username", "admin")}, "warn")
    return {"status": "applied", "plan": plan, "results": results}

@app.post("/api/zero-trust/vm/attach", dependencies=[Depends(verify_admin)])
async def zero_trust_vm_attach(data: ZeroTrustVmAttachRequest, admin = Depends(verify_admin)):
    tenant = zt_tenant_lookup(data.tenant_id)
    plan = zt_vm_attach_plan(data, tenant)
    if not data.apply:
        return {"status": "planned", "plan": plan}
    if data.confirm != "APPLY-ZERO-TRUST":
        raise HTTPException(status_code=403, detail="Aby przepiac VM do sieci tenanta wpisz confirm=APPLY-ZERO-TRUST")
    result = zt_attach_vm_to_tenant(data, tenant)
    phase2_log("zero_trust_vm_attach", {"vm_id": safe_vm_target(data.vm_id), "tenant_id": phase2_clean_id(data.tenant_id), "result": result, "by": admin.get("username", "admin")}, "warn")
    return result

@app.get("/api/vms/network/rules", dependencies=[Depends(verify_token)])
async def phase2_network_rules():
    tenants = {row.get("tenant_id"): row for row in read_json(PHASE2_TENANTS_FILE, [])}
    rows = read_json(PHASE2_NETWORK_RULES_FILE, [])
    return {"items": rows, "tenants": list(tenants.values()), "tools": {"nft": bool(shutil.which("nft")), "iptables": bool(shutil.which("iptables"))}}

@app.post("/api/vms/network/rules", dependencies=[Depends(verify_admin)])
async def phase2_network_rule_save(data: Phase2NetworkRuleRequest, admin = Depends(verify_admin)):
    tenants = {row.get("tenant_id"): row for row in read_json(PHASE2_TENANTS_FILE, [])}
    tenant = tenants.get(phase2_clean_id(data.tenant_id), {})
    row = data.dict()
    row["id"] = uuid.uuid4().hex[:12]
    row["tenant_id"] = phase2_clean_id(row.get("tenant_id"))
    row["created_at"] = now_iso()
    row["created_by"] = admin.get("username", "admin")
    plan = phase2_network_rule_plan(row, tenant)
    apply_results = []
    if data.apply:
        if data.confirm != "APPLY-ZERO-TRUST":
            raise HTTPException(status_code=403, detail="Aby wykonac live SDN/FW wpisz confirm=APPLY-ZERO-TRUST")
        if not shutil.which("nft"):
            raise HTTPException(status_code=501, detail="Brak nft na hoście")
        apply_results = zt_apply_commands(plan["commands"], timeout=8)
        row["applied_at"] = now_iso()
        row["apply_results"] = apply_results
    rows = read_json(PHASE2_NETWORK_RULES_FILE, [])
    rows.insert(0, row)
    write_json(PHASE2_NETWORK_RULES_FILE, rows[:1000])
    phase2_log("network_rule", {"rule": row, "plan": plan}, "info")
    return {"status": "applied" if data.apply else "planned", "rule": row, "plan": plan, "results": apply_results}

@app.post("/api/vms/network/rules/delete", dependencies=[Depends(verify_admin)])
async def phase2_network_rule_delete(data: Phase2DeleteRequest, admin = Depends(verify_admin)):
    write_json(PHASE2_NETWORK_RULES_FILE, [item for item in read_json(PHASE2_NETWORK_RULES_FILE, []) if item.get("id") != data.id])
    phase2_log("network_rule_delete", {"id": data.id, "by": admin.get("username", "admin")}, "warn")
    return {"status": "deleted", "id": data.id}

@app.get("/api/phase2/nano/recipes", dependencies=[Depends(verify_token)])
async def phase2_nano_recipes():
    return {"items": read_json(PHASE2_NANO_RECIPES_FILE, [])}

@app.post("/api/phase2/nano/recipes", dependencies=[Depends(verify_admin)])
async def phase2_nano_recipe_save(data: Phase2NanoRecipeRequest, admin = Depends(verify_admin)):
    kernel = allowed_enterprise_path(data.kernel_path)
    initrd = allowed_enterprise_path(data.initrd_path) if data.initrd_path else None
    rootfs = allowed_enterprise_path(data.rootfs_path) if data.rootfs_path else None
    row = data.dict()
    row.update({"id": uuid.uuid4().hex[:12], "kernel_path": str(kernel), "initrd_path": str(initrd or ""), "rootfs_path": str(rootfs or ""), "created_at": now_iso(), "created_by": admin.get("username", "admin")})
    rows = read_json(PHASE2_NANO_RECIPES_FILE, [])
    rows.insert(0, row)
    write_json(PHASE2_NANO_RECIPES_FILE, rows[:300])
    phase2_log("nano_recipe", row, "info")
    return {"status": "saved", "recipe": row}

@app.post("/api/phase2/nano/plan", dependencies=[Depends(verify_admin)])
async def phase2_nano_plan(data: Phase2NanoRecipeRequest):
    kernel = allowed_enterprise_path(data.kernel_path)
    args = ["qemu-system-x86_64", "-enable-kvm", "-m", str(data.memory_mb), "-smp", str(data.vcpus), "-kernel", str(kernel), "-append", data.cmdline]
    if data.initrd_path:
        args.extend(["-initrd", str(allowed_enterprise_path(data.initrd_path))])
    if data.rootfs_path:
        args.extend(["-drive", f"file={allowed_enterprise_path(data.rootfs_path)},format=raw,if=virtio"])
    return {"status": "planned", "target_boot_ms": "<100ms for unikernel/direct-kernel images", "command": args, "note": "Plan fast-boot. Uruchamianie live wymaga osobnego isolate/tenant runnera."}

@app.post("/api/phase2/forge/build", dependencies=[Depends(verify_admin)])
async def phase2_forge_build(data: Phase2ForgeBuildRequest, admin = Depends(verify_admin)):
    source = allowed_enterprise_path(data.source_path)
    output_name = safe_upload_filename(data.output_name or f"{edge_slug(data.name)}.qcow2")
    if not output_name.endswith(".qcow2"):
        output_name += ".qcow2"
    target = (LIBVIRT_IMAGE_DIR / output_name).resolve()
    tools = {"docker": bool(shutil.which("docker")), "qemu-img": bool(shutil.which("qemu-img")), "virt-builder": bool(shutil.which("virt-builder")), "virt-customize": bool(shutil.which("virt-customize"))}
    commands = [
        ["docker", "build", "-f", str(source / data.dockerfile if source.is_dir() else source), "-t", f"nexus-forge/{edge_slug(data.name)}:latest", str(source if source.is_dir() else source.parent)],
        ["qemu-img", "create", "-f", "qcow2", "-o", "compat=1.1,lazy_refcounts=on", str(target), f"{data.disk_gb}G"],
    ]
    row = {"id": uuid.uuid4().hex[:12], "name": data.name, "source_path": str(source), "output_path": str(target), "commands": commands, "tools": tools, "dry_run": data.dry_run, "auto_register": data.auto_register, "created_at": now_iso(), "created_by": admin.get("username", "admin"), "status": "planned"}
    if not data.dry_run:
        if not tools["qemu-img"]:
            raise HTTPException(status_code=501, detail="Brak qemu-img do utworzenia obrazu buildowego")
        created = create_dynamic_disk(target, data.disk_gb)
        row["status"] = "disk-created"
        row["dynamic_disk"] = created
        row["output"] = f"Dynamic qcow2 ready: {created.get('info', {}).get('actual_size_label', '--')} / {created.get('info', {}).get('virtual_size_label', '--')}"
    rows = read_json(PHASE2_FORGE_BUILDS_FILE, [])
    rows.insert(0, row)
    write_json(PHASE2_FORGE_BUILDS_FILE, rows[:200])
    phase2_log("forge_build", row, "info")
    return row

@app.get("/api/phase2/forge/builds", dependencies=[Depends(verify_token)])
async def phase2_forge_builds():
    return {"items": read_json(PHASE2_FORGE_BUILDS_FILE, [])[:200]}

@app.get("/api/phase2/branding", dependencies=[Depends(verify_token)])
async def phase2_branding():
    return read_json(PHASE2_BRANDING_FILE, {})

@app.post("/api/phase2/branding", dependencies=[Depends(verify_admin)])
async def phase2_branding_save(data: Phase2BrandingRequest, admin = Depends(verify_admin)):
    host = re.sub(r"[^A-Za-z0-9_.:-]+", "", data.host.strip().lower())
    if not host:
        raise HTTPException(status_code=400, detail="Niepoprawny host")
    rows = read_json(PHASE2_BRANDING_FILE, {})
    row = data.dict()
    row["host"] = host
    row["updated_at"] = now_iso()
    row["updated_by"] = admin.get("username", "admin")
    rows[host] = row
    write_json(PHASE2_BRANDING_FILE, rows)
    return {"status": "saved", "branding": row}

@app.get("/api/public/branding")
async def phase2_public_branding(request: Request, host: str = ""):
    rows = read_json(PHASE2_BRANDING_FILE, {})
    key = re.sub(r"[^A-Za-z0-9_.:-]+", "", (host or request.headers.get("host") or "").split(",")[0].strip().lower())
    row = rows.get(key) or rows.get(key.split(":")[0]) or {}
    return {"host": key, "branding": row if row.get("enabled", True) else {}}

@app.get("/api/edge/status", dependencies=[Depends(verify_token)])
async def edge_status():
    return {"status": "live", "tools": {"python": bool(shutil.which("python3") or shutil.which("python")), "node": bool(shutil.which("node")), "wasmtime": bool(shutil.which("wasmtime"))}, "functions": [edge_public_function(row) for row in edge_functions()], "metrics": edge_metrics()}

@app.get("/api/edge/functions", dependencies=[Depends(verify_token)])
async def edge_function_list():
    return {"items": [edge_public_function(row) for row in edge_functions()]}

@app.post("/api/edge/functions", dependencies=[Depends(verify_admin)])
async def edge_function_save(data: EdgeFunctionRequest, request: Request, admin = Depends(verify_admin)):
    runtime = (data.runtime or "python").lower()
    if runtime in {"js", "node"}:
        runtime = "javascript"
    if runtime not in {"python", "javascript"}:
        raise HTTPException(status_code=400, detail="Runtime: python/javascript")
    slug = edge_slug(data.slug or data.name)
    row = {"id": uuid.uuid4().hex[:12], "name": data.name[:120], "slug": slug, "runtime": runtime, "code": data.code, "timeout": data.timeout, "public": bool(data.public), "description": data.description[:500], "created_at": now_iso(), "created_by": admin.get("username", "admin")}
    rows = [item for item in edge_functions() if item.get("slug") != slug and item.get("id") != row["id"]]
    rows.insert(0, row)
    save_edge_functions(rows)
    for key, value in (data.secrets or {}).items():
        secret_key = edge_secret_key(slug, key)
        secrets_map = read_json(EDGE_SECRETS_FILE, {})
        secrets_map[secret_key] = {"scope": slug, "name": re.sub(r"[^A-Za-z0-9_]+", "_", str(key).upper()), "value": str(value), "updated_at": now_iso(), "updated_by": admin.get("username", "admin")}
        write_json(EDGE_SECRETS_FILE, secrets_map)
    phase2_log("edge_deploy", {"slug": slug, "runtime": runtime, "public": bool(data.public)}, "info")
    public_base = external_base_url(request)
    return {"status": "deployed", "function": edge_public_function(row), "url": f"{public_base}/edge/{slug}"}

@app.post("/api/edge/functions/delete", dependencies=[Depends(verify_admin)])
async def edge_function_delete(data: EdgeFunctionDeleteRequest, admin = Depends(verify_admin)):
    rows = edge_functions()
    write_json(EDGE_FUNCTIONS_FILE, [row for row in rows if row.get("id") != data.id and row.get("slug") != data.id])
    phase2_log("edge_delete", {"id": data.id, "by": admin.get("username", "admin")}, "warn")
    return {"status": "deleted", "id": data.id}

@app.post("/api/edge/secrets", dependencies=[Depends(verify_admin)])
async def edge_secret_set(data: EdgeSecretRequest, admin = Depends(verify_admin)):
    secrets_map = read_json(EDGE_SECRETS_FILE, {})
    key = edge_secret_key(data.scope, data.name)
    secrets_map[key] = {"scope": edge_slug(data.scope, "global"), "name": re.sub(r"[^A-Za-z0-9_]+", "_", data.name.upper()), "value": data.value, "updated_at": now_iso(), "updated_by": admin.get("username", "admin")}
    write_json(EDGE_SECRETS_FILE, secrets_map)
    return {"status": "saved", "secret": {"scope": secrets_map[key]["scope"], "name": secrets_map[key]["name"], "masked": edge_secret_mask(data.value)}}

@app.get("/api/edge/secrets", dependencies=[Depends(verify_admin)])
async def edge_secret_list():
    return {"items": [{"scope": row.get("scope"), "name": row.get("name"), "masked": edge_secret_mask(row.get("value", "")), "updated_at": row.get("updated_at")} for row in read_json(EDGE_SECRETS_FILE, {}).values()]}

@app.post("/api/edge/secrets/delete", dependencies=[Depends(verify_admin)])
async def edge_secret_delete(data: EdgeSecretDeleteRequest):
    secrets_map = read_json(EDGE_SECRETS_FILE, {})
    secrets_map.pop(edge_secret_key(data.scope, data.name), None)
    write_json(EDGE_SECRETS_FILE, secrets_map)
    return {"status": "deleted"}

@app.get("/api/edge/logs", dependencies=[Depends(verify_token)])
async def edge_logs(slug: str = ""):
    return {"metrics": edge_metrics(slug), "items": edge_metrics(slug).get("recent", [])}

@app.api_route("/edge/{slug:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def edge_gateway(slug: str, request: Request):
    clean_slug = edge_slug(slug.split("/")[0])
    row = next((item for item in edge_functions() if item.get("slug") == clean_slug), None)
    if not row:
        raise HTTPException(status_code=404, detail="Edge function nie istnieje")
    if not row.get("public", False):
        phase2_bearer_user(request)
    return await execute_edge_function(row, request)

@app.websocket("/ws/edge/logs/{slug}")
async def edge_logs_ws(websocket: WebSocket, slug: str):
    token = websocket.query_params.get("token", "")
    if token not in SESSIONS:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    seen = set()
    clean_slug = edge_slug(slug)
    try:
        while True:
            rows = [row for row in read_json(EDGE_RUNS_FILE, []) if not clean_slug or row.get("slug") == clean_slug]
            for row in reversed(rows[:100]):
                if row.get("id") in seen:
                    continue
                seen.add(row.get("id"))
                await websocket.send_json(row)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return

@app.get("/api/storage/presign-download", dependencies=[Depends(verify_token)])
async def object_storage_presign_download(object_id: str, request: Request, expires: int = 900, user = Depends(verify_token)):
    item = next((row for row in object_registry() if row.get("id") == object_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Obiekt nie istnieje")
    if user.get("role") != "admin" and item.get("owner") != user.get("username"):
        raise HTTPException(status_code=403, detail="Obiekt nie nalezy do uzytkownika")
    url = s3_presigned_url("GET", item.get("bucket", ""), item.get("key", ""), expires=expires, base_url=public_object_base(request))
    return {"method": "GET", "url": url, "expires_seconds": max(60, min(int(expires), 604800)), "object": object_status_row(item)}

@app.get("/api/storage/retention", dependencies=[Depends(verify_token)])
async def storage_retention_get():
    return {"policies": read_json(STORAGE_RETENTION_FILE, [])}

@app.post("/api/storage/retention", dependencies=[Depends(verify_admin)])
async def storage_retention_save(data: StorageRetentionPolicyRequest, admin = Depends(verify_admin)):
    kind = (data.kind or "data").lower().strip()
    row = data.dict()
    row["kind"] = kind
    row["id"] = kind
    row["updated_at"] = now_iso()
    row["updated_by"] = admin.get("username", "admin")
    rows = [item for item in read_json(STORAGE_RETENTION_FILE, []) if item.get("kind") != kind]
    rows.insert(0, row)
    write_json(STORAGE_RETENTION_FILE, rows[:100])
    return {"status": "saved", "policy": row}

@app.post("/api/storage/retention/run", dependencies=[Depends(verify_admin)])
async def storage_retention_run(data: StorageRetentionRunRequest, admin = Depends(verify_admin)):
    policies = [row for row in read_json(STORAGE_RETENTION_FILE, []) if row.get("enabled", True)]
    objects = object_registry()
    now = datetime.datetime.now()
    to_delete = []
    for policy in policies:
        cutoff = now - datetime.timedelta(days=int(policy.get("days", 30) or 30))
        count = 0
        for item in objects:
            if policy.get("kind") not in {"all", item.get("kind")}:
                continue
            created = iso_dt(item.get("created_at"))
            if created and created < cutoff and count < int(policy.get("max_delete", 25) or 25):
                to_delete.append({"object": item, "policy": policy})
                count += 1
    deleted = []
    if not data.dry_run:
        if data.confirm != "DELETE-OLD-OBJECTS":
            raise HTTPException(status_code=403, detail="Aby usunac stare obiekty wpisz confirm=DELETE-OLD-OBJECTS")
        remaining = objects[:]
        for pair in to_delete:
            item = pair["object"]
            policy = pair["policy"]
            if policy.get("delete_imported") and item.get("imported_path"):
                try:
                    Path(item["imported_path"]).unlink(missing_ok=True)
                except Exception:
                    pass
            if policy.get("delete_remote"):
                try:
                    delete_url = s3_presigned_url("DELETE", item.get("bucket", ""), item.get("key", ""), expires=120, base_url=MINIO_INTERNAL_BASE)
                    urllib.request.urlopen(urllib.request.Request(delete_url, method="DELETE"), timeout=20).read()
                except Exception as exc:
                    deleted.append({"id": item.get("id"), "remote_error": str(exc)})
                    continue
            remaining = [row for row in remaining if row.get("id") != item.get("id")]
            deleted.append({"id": item.get("id"), "filename": item.get("filename"), "kind": item.get("kind")})
        save_object_registry(remaining)
    return {"status": "deleted" if deleted else "planned", "dry_run": data.dry_run, "candidates": [object_status_row(pair["object"]) for pair in to_delete], "deleted": deleted}

@app.get("/api/neural/status", dependencies=[Depends(verify_token)])
async def neural_status():
    cache = read_json(NEURAL_CACHE_FILE, {})
    return {"status": "ready" if shutil.which("ollama") else "provider-missing", "provider": "ollama", "endpoint": "/v1/chat/completions", "cache_entries": len(cache), "note": "NEXUS Neural nie wysyla danych do OpenAI; uzywa lokalnego Ollama, jesli jest dostepny."}

@app.post("/api/neural/chat", dependencies=[Depends(verify_token)])
async def neural_chat(data: NeuralChatRequest):
    payload = data.dict()
    cache = read_json(NEURAL_CACHE_FILE, {})
    key = neural_cache_key(payload)
    if key in cache:
        cached = cache[key]
        cached["nexus"]["cache_hit"] = True
        return cached
    if not shutil.which("ollama"):
        raise HTTPException(status_code=503, detail="Brak lokalnego silnika Ollama. Zainstaluj Ollama/model, aby aktywowac NEXUS Neural.")
    try:
        response = neural_call_ollama(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama nie odpowiedziala: {exc}")
    cache[key] = response
    write_json(NEURAL_CACHE_FILE, dict(list(cache.items())[-1000:]))
    return response

@app.post("/v1/chat/completions")
async def neural_openai_compatible(request: Request):
    phase2_bearer_user(request)
    payload = await request.json()
    key = neural_cache_key(payload)
    cache = read_json(NEURAL_CACHE_FILE, {})
    if key in cache:
        cached = cache[key]
        cached["nexus"]["cache_hit"] = True
        return cached
    if not shutil.which("ollama"):
        raise HTTPException(status_code=503, detail="NEXUS Neural provider missing: install Ollama locally")
    try:
        response = neural_call_ollama(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama error: {exc}")
    cache[key] = response
    write_json(NEURAL_CACHE_FILE, dict(list(cache.items())[-1000:]))
    return response

@app.post("/api/neural/cache/clear", dependencies=[Depends(verify_admin)])
async def neural_cache_clear(admin = Depends(verify_admin)):
    count = len(read_json(NEURAL_CACHE_FILE, {}))
    write_json(NEURAL_CACHE_FILE, {})
    phase2_log("neural_cache_clear", {"count": count, "by": admin.get("username", "admin")}, "warn")
    return {"status": "cleared", "count": count}

def archiver_dest_root(value: str):
    mapping = {
        "drop": DROP_DIR,
        "media": MEDIA_DIR,
        "iso": LIBVIRT_ISO_DIR,
        "drivers": DRIVER_DIR,
        "vault": VAULT_DIR,
        "base": BASE_DIR,
    }
    return mapping.get((value or "drop").strip().lower(), DROP_DIR).resolve()

def archive_member_target(dest_root: Path, member: str):
    clean = str(member or "").replace("\\", "/").lstrip("/")
    target = (dest_root / clean).resolve()
    if target != dest_root and dest_root not in target.parents:
        raise HTTPException(status_code=400, detail="Niepoprawny wpis archiwum")
    return target

def archive_list(path: Path):
    suffix = path.suffix.lower()
    items = []
    if suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist()[:5000]:
                items.append({"name": info.filename, "size": info.file_size, "size_label": fmt_size(info.file_size), "is_dir": info.is_dir(), "modified": datetime.datetime(*info.date_time).isoformat(timespec="seconds")})
    elif suffix in {".tar", ".gz", ".tgz", ".bz2", ".xz"} or path.name.endswith((".tar.gz", ".tar.bz2", ".tar.xz")):
        with tarfile.open(path, "r:*") as tf:
            for info in tf.getmembers()[:5000]:
                items.append({"name": info.name, "size": info.size, "size_label": fmt_size(info.size), "is_dir": info.isdir(), "modified": datetime.datetime.fromtimestamp(info.mtime).isoformat(timespec="seconds") if info.mtime else ""})
    elif suffix == ".7z":
        try:
            import py7zr
            with py7zr.SevenZipFile(path, "r") as zf:
                for info in zf.list()[:5000]:
                    items.append({"name": info.filename, "size": getattr(info, "uncompressed", 0) or 0, "size_label": fmt_size(getattr(info, "uncompressed", 0) or 0), "is_dir": bool(getattr(info, "is_directory", False)), "modified": ""})
        except ImportError:
            raise HTTPException(status_code=501, detail="Brak py7zr: zainstaluj py7zr, aby czytac 7z")
    else:
        raise HTTPException(status_code=400, detail="Obslugiwane: zip, tar, tar.gz, tar.xz, 7z")
    return items

def append_archiver_job(row):
    rows = read_json(ARCHIVER_JOBS_FILE, [])
    rows.insert(0, row)
    write_json(ARCHIVER_JOBS_FILE, rows[:200])

@app.get("/api/archiver/status", dependencies=[Depends(verify_token)])
async def archiver_status():
    try:
        import py7zr  # noqa: F401
        has_py7zr = True
    except Exception:
        has_py7zr = False
    return {
        "tools": {"zipfile": True, "tarfile": True, "py7zr": has_py7zr, "genisoimage": bool(shutil.which("genisoimage") or shutil.which("mkisofs"))},
        "jobs": read_json(ARCHIVER_JOBS_FILE, [])[:50],
        "roots": [str(root) for root in enterprise_roots()],
    }

@app.post("/api/archiver/list", dependencies=[Depends(verify_token)])
async def archiver_list_endpoint(data: ArchiverListRequest):
    path = allowed_enterprise_path(data.path)
    if not path.is_file():
        raise HTTPException(status_code=400, detail="To nie jest plik archiwum")
    items = archive_list(path)
    return {"archive": str(path), "items": items, "count": len(items)}

@app.post("/api/archiver/extract", dependencies=[Depends(verify_admin)])
async def archiver_extract(data: ArchiverExtractRequest, admin = Depends(verify_admin)):
    path = allowed_enterprise_path(data.path)
    dest_root = archiver_dest_root(data.dest)
    dest_root.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    target = archive_member_target(dest_root, data.member)
    target.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            info = next((item for item in zf.infolist() if item.filename == data.member), None)
            if not info or info.is_dir():
                raise HTTPException(status_code=404, detail="Nie znaleziono pliku w ZIP")
            with zf.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)
    elif suffix in {".tar", ".gz", ".tgz", ".bz2", ".xz"} or path.name.endswith((".tar.gz", ".tar.bz2", ".tar.xz")):
        with tarfile.open(path, "r:*") as tf:
            info = tf.getmember(data.member)
            if not info or info.isdir():
                raise HTTPException(status_code=404, detail="Nie znaleziono pliku w TAR")
            src = tf.extractfile(info)
            if not src:
                raise HTTPException(status_code=404, detail="Nie da sie czytac wpisu TAR")
            with src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)
    elif suffix == ".7z":
        try:
            import py7zr
            with tempfile.TemporaryDirectory(prefix="nexus-7z-") as tmp:
                with py7zr.SevenZipFile(path, "r") as zf:
                    zf.extract(path=tmp, targets=[data.member])
                extracted = (Path(tmp) / data.member).resolve()
                if not extracted.exists() or not extracted.is_file():
                    raise HTTPException(status_code=404, detail="Nie wypakowano wpisu 7z")
                shutil.copy2(extracted, target)
        except ImportError:
            raise HTTPException(status_code=501, detail="Brak py7zr")
    else:
        raise HTTPException(status_code=400, detail="Nieobslugiwany format")
    if dest_root == LIBVIRT_ISO_DIR.resolve():
        ensure_libvirt_file_access(target)
    row = {"id": uuid.uuid4().hex[:12], "kind": "extract", "archive": str(path), "member": data.member, "target": str(target), "created_at": now_iso(), "created_by": admin.get("username", "admin")}
    append_archiver_job(row)
    return row

@app.post("/api/archiver/zip", dependencies=[Depends(verify_admin)])
async def archiver_zip(data: ArchiverZipRequest, admin = Depends(verify_admin)):
    if not data.paths:
        raise HTTPException(status_code=400, detail="Zaznacz pliki/foldery do ZIP")
    output = unique_target_path(DROP_DIR, data.output_name if data.output_name.lower().endswith(".zip") else f"{data.output_name}.zip")
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for raw in data.paths[:80]:
            source = allowed_enterprise_path(str(raw))
            if source.is_dir():
                for item in source.rglob("*"):
                    if item.is_file():
                        zf.write(item, arcname=str(Path(source.name) / item.relative_to(source)).replace("\\", "/"))
            else:
                zf.write(source, arcname=source.name)
    row = {"id": uuid.uuid4().hex[:12], "kind": "zip", "target": str(output), "size": fmt_size(output.stat().st_size), "created_at": now_iso(), "created_by": admin.get("username", "admin")}
    append_archiver_job(row)
    return row

@app.post("/api/archiver/iso", dependencies=[Depends(verify_admin)])
async def archiver_iso(data: ArchiverIsoRequest, admin = Depends(verify_admin)):
    if not data.paths:
        raise HTTPException(status_code=400, detail="Zaznacz pliki/foldery do ISO")
    tool = shutil.which("genisoimage") or shutil.which("mkisofs")
    if not tool:
        raise HTTPException(status_code=501, detail="Brak genisoimage/mkisofs na serwerze")
    output = (LIBVIRT_ISO_DIR / safe_iso_filename(data.output_name)).resolve()
    if LIBVIRT_ISO_DIR.resolve() not in output.parents:
        raise HTTPException(status_code=400, detail="Niepoprawna nazwa ISO")
    sources = [str(allowed_enterprise_path(str(raw))) for raw in data.paths[:80]]
    code, output_text = run_vm_command([tool, "-quiet", "-J", "-R", "-o", str(output)] + sources, timeout=60 * 30)
    if code != 0:
        raise HTTPException(status_code=500, detail=output_text[-1200:] or "Nie utworzono ISO")
    ensure_libvirt_file_access(output)
    row = {"id": uuid.uuid4().hex[:12], "kind": "iso", "target": str(output), "size": fmt_size(output.stat().st_size), "created_at": now_iso(), "created_by": admin.get("username", "admin")}
    append_archiver_job(row)
    return row

@app.get("/api/bastion/status", dependencies=[Depends(verify_token)])
async def bastion_status():
    return {
        "tools": {"guacd": bool(shutil.which("guacd")), "ssh": bool(shutil.which("ssh")), "websocat": bool(shutil.which("websocat"))},
        "targets": len(read_json(BASTION_FILE, [])),
        "note": "RDP/VNC wymaga Apache Guacamole/guacd; SSH uzywa systemowego klienta ssh jako bramy.",
    }

@app.get("/api/bastion/targets", dependencies=[Depends(verify_token)])
async def bastion_targets():
    return {"items": read_json(BASTION_FILE, [])}

@app.post("/api/bastion/targets", dependencies=[Depends(verify_admin)])
async def bastion_target_save(data: BastionTargetRequest, admin = Depends(verify_admin)):
    kind = (data.kind or "rdp").lower()
    if kind not in {"rdp", "vnc", "ssh", "nexus-link"}:
        raise HTTPException(status_code=400, detail="Typ: rdp/vnc/ssh/nexus-link")
    row = {"id": uuid.uuid4().hex[:12], "name": data.name[:120], "kind": kind, "host": data.host[:180], "port": data.port, "username": data.username[:80], "note": data.note[:300], "created_at": now_iso(), "created_by": admin.get("username", "admin")}
    rows = read_json(BASTION_FILE, [])
    rows.insert(0, row)
    write_json(BASTION_FILE, rows[:300])
    return row

@app.post("/api/bastion/delete", dependencies=[Depends(verify_admin)])
async def bastion_target_delete(data: BastionDeleteRequest):
    write_json(BASTION_FILE, [item for item in read_json(BASTION_FILE, []) if item.get("id") != data.id])
    return {"status": "deleted"}

@app.post("/api/bastion/launch", dependencies=[Depends(verify_token)])
async def bastion_launch(data: BastionDeleteRequest):
    row = next((item for item in read_json(BASTION_FILE, []) if item.get("id") == data.id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Cel Bastion nie istnieje")
    kind = row.get("kind", "rdp")
    if kind in {"rdp", "vnc"} and not shutil.which("guacd"):
        return {"status": "missing-guacd", "target": row, "message": "Zainstaluj Apache Guacamole/guacd, aby otwierac RDP/VNC w HTML5."}
    if kind == "ssh" and not shutil.which("ssh"):
        return {"status": "missing-ssh", "target": row, "message": "Brak klienta ssh na serwerze."}
    return {"status": "ready", "target": row, "message": f"Cel {kind.upper()} gotowy do podpiecia przez brame protokolu."}

@app.get("/api/workers/status", dependencies=[Depends(verify_token)])
async def workers_status():
    return {"tools": {"python3": bool(shutil.which("python3") or shutil.which("python")), "node": bool(shutil.which("node")), "docker": bool(shutil.which("docker")), "firecracker": bool(shutil.which("firecracker"))}, "runs": read_json(WORKER_RUNS_FILE, [])[:50]}

@app.get("/api/workers", dependencies=[Depends(verify_token)])
async def workers_list():
    return {"items": read_json(WORKERS_FILE, [])}

@app.post("/api/workers", dependencies=[Depends(verify_admin)])
async def workers_save(data: WorkerSaveRequest, admin = Depends(verify_admin)):
    runtime = (data.runtime or "python").lower()
    if runtime not in {"python", "javascript"}:
        raise HTTPException(status_code=400, detail="Runtime: python/javascript")
    row = {"id": uuid.uuid4().hex[:12], "name": data.name[:120], "runtime": runtime, "code": data.code, "created_at": now_iso(), "created_by": admin.get("username", "admin")}
    rows = read_json(WORKERS_FILE, [])
    rows.insert(0, row)
    write_json(WORKERS_FILE, rows[:200])
    return row

@app.post("/api/workers/run", dependencies=[Depends(verify_admin)])
async def workers_run(data: WorkerRunRequest, admin = Depends(verify_admin)):
    code = data.code or ""
    runtime = (data.runtime or "python").lower()
    if data.id:
        row = next((item for item in read_json(WORKERS_FILE, []) if item.get("id") == data.id), None)
        if not row:
            raise HTTPException(status_code=404, detail="Worker nie istnieje")
        code = row.get("code", "")
        runtime = row.get("runtime", runtime)
    if runtime not in {"python", "javascript"}:
        raise HTTPException(status_code=400, detail="Runtime: python/javascript")
    exe = shutil.which("python3") or shutil.which("python") if runtime == "python" else shutil.which("node")
    if not exe:
        raise HTTPException(status_code=501, detail=f"Brak runtime {runtime}")
    with tempfile.TemporaryDirectory(prefix="nexus-worker-") as tmp:
        script = Path(tmp) / ("worker.py" if runtime == "python" else "worker.js")
        script.write_text(code, encoding="utf-8")
        args = [exe, "-I", str(script)] if runtime == "python" else [exe, str(script)]
        try:
            proc = subprocess.run(args, cwd=tmp, text=True, capture_output=True, timeout=int(data.timeout), env={"PATH": os.environ.get("PATH", ""), "HOME": tmp})
            result = {"code": proc.returncode, "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-8000:]}
        except subprocess.TimeoutExpired as exc:
            result = {"code": 124, "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "", "stderr": "Timeout worker sandbox"}
    run = {"id": uuid.uuid4().hex[:12], "runtime": runtime, "result": result, "created_at": now_iso(), "created_by": admin.get("username", "admin")}
    runs = read_json(WORKER_RUNS_FILE, [])
    runs.insert(0, run)
    write_json(WORKER_RUNS_FILE, runs[:200])
    return run

def vault_public_row(row):
    out = dict(row)
    out.pop("file_path", None)
    try:
        out["expired"] = datetime.datetime.fromisoformat(row.get("expires_at", "")) < datetime.datetime.now()
    except Exception:
        out["expired"] = True
    return out

def vault_find(link_id: str):
    rows = read_json(VAULT_FILE, [])
    row = next((item for item in rows if item.get("id") == link_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Vault link nie istnieje")
    return rows, row

@app.get("/api/vault/links", dependencies=[Depends(verify_token)])
async def vault_links():
    return {"items": [vault_public_row(row) for row in read_json(VAULT_FILE, [])]}

@app.post("/api/vault/link", dependencies=[Depends(verify_admin)])
async def vault_link(data: VaultLinkRequest, request: Request, admin = Depends(verify_admin)):
    path = allowed_enterprise_path(data.path)
    if not path.is_file():
        raise HTTPException(status_code=400, detail="Vault link wymaga pliku")
    row = {"id": uuid.uuid4().hex[:16], "title": data.title or path.name, "file_path": str(path), "filename": path.name, "size": fmt_size(path.stat().st_size), "views": 0, "max_views": data.max_views, "destroy_after_read": data.destroy_after_read, "encrypted": False, "created_at": now_iso(), "created_by": admin.get("username", "admin"), "expires_at": (datetime.datetime.now() + datetime.timedelta(minutes=data.ttl_minutes)).isoformat(timespec="seconds"), "status": "active"}
    rows = read_json(VAULT_FILE, [])
    rows.insert(0, row)
    write_json(VAULT_FILE, rows[:500])
    return {**vault_public_row(row), "public_url": f"{external_base_url(request)}/vault/raw/{row['id']}"}

@app.post("/api/vault/upload", dependencies=[Depends(verify_token)])
async def vault_upload(request: Request, file: UploadFile = File(...), title: str = Form(""), max_views: int = Form(1), ttl_minutes: int = Form(1440), encrypted: str = Form("1"), user = Depends(verify_token)):
    target = unique_target_path(VAULT_DIR, file.filename or f"vault-{uuid.uuid4().hex[:8]}.bin")
    with open(target, "wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    row = {"id": uuid.uuid4().hex[:16], "title": title or target.name, "file_path": str(target), "filename": target.name, "size": fmt_size(target.stat().st_size), "views": 0, "max_views": max(1, min(int(max_views), 100)), "destroy_after_read": True, "encrypted": encrypted != "0", "created_at": now_iso(), "created_by": user.get("username", "user"), "expires_at": (datetime.datetime.now() + datetime.timedelta(minutes=max(1, min(int(ttl_minutes), 43200)))).isoformat(timespec="seconds"), "status": "active"}
    rows = read_json(VAULT_FILE, [])
    rows.insert(0, row)
    write_json(VAULT_FILE, rows[:500])
    return {**vault_public_row(row), "public_url": f"{external_base_url(request)}/static/vault.html?id={row['id']}", "raw_url": f"{external_base_url(request)}/vault/raw/{row['id']}"}

def vault_destroy_file(link_id: str):
    rows = read_json(VAULT_FILE, [])
    for item in rows:
        if item.get("id") == link_id:
            try:
                Path(item.get("file_path", "")).unlink(missing_ok=True)
            except Exception:
                pass
            item["destroyed_at"] = now_iso()
            item["status"] = "destroyed"
    write_json(VAULT_FILE, rows)

@app.get("/vault/raw/{link_id}")
async def vault_raw(link_id: str, background_tasks: BackgroundTasks):
    rows, row = vault_find(link_id)
    try:
        if datetime.datetime.fromisoformat(row.get("expires_at", "")) < datetime.datetime.now():
            row["status"] = "expired"
            write_json(VAULT_FILE, rows)
            raise HTTPException(status_code=410, detail="Vault link wygasl")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=410, detail="Vault link ma bledny TTL")
    if row.get("status") not in {"active", "spent"} or int(row.get("views", 0)) >= int(row.get("max_views", 1)):
        raise HTTPException(status_code=410, detail="Vault link zostal juz zuzyty")
    path = Path(row.get("file_path", "")).resolve()
    if not path.exists():
        raise HTTPException(status_code=404, detail="Plik Vault nie istnieje")
    row["views"] = int(row.get("views", 0)) + 1
    row["last_view_at"] = now_iso()
    if row["views"] >= int(row.get("max_views", 1)):
        row["status"] = "spent"
        if row.get("destroy_after_read", True):
            background_tasks.add_task(vault_destroy_file, link_id)
    write_json(VAULT_FILE, rows)
    return FileResponse(path, filename=row.get("filename") or path.name, media_type="application/octet-stream")

@app.post("/api/vault/delete", dependencies=[Depends(verify_admin)])
async def vault_delete(data: VaultDeleteRequest):
    rows, row = vault_find(data.id)
    try:
        Path(row.get("file_path", "")).unlink(missing_ok=True)
    except Exception:
        pass
    write_json(VAULT_FILE, [item for item in rows if item.get("id") != data.id])
    return {"status": "deleted"}

@app.post("/api/global-terminal/command", dependencies=[Depends(verify_token)])
async def global_terminal_command(data: GlobalTerminalCommandRequest, user = Depends(verify_token)):
    cmd = data.command.strip()
    username = user.get("username", "user")
    response = {"status": "ok", "message": "", "data": {}}
    if not cmd.startswith("/"):
        msgs = read_json(COMMUNITY_FILE, [])
        msgs.append({"author": username, "text": cmd[:200], "time": datetime.datetime.now().strftime("%H:%M:%S")})
        write_json(COMMUNITY_FILE, msgs[-300:])
        response["message"] = "Wiadomosc wyslana na czat."
    elif cmd in {"/help", "/?"}:
        response["message"] = "/balance, /pay USER AMOUNT, /tokens add USER AMOUNT, /vm list, /ai polecenie"
    elif cmd == "/balance":
        billing = vm_billing_store()
        response["data"] = vm_wallet(billing, username)
        response["message"] = f"Saldo {response['data'].get('balance', 0)} tokenow."
    elif cmd.startswith("/pay "):
        parts = cmd.split()
        if len(parts) < 3:
            raise HTTPException(status_code=400, detail="Uzycie: /pay user amount")
        target = normalize_username(parts[1])
        amount = float(parts[2].replace(",", "."))
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Kwota musi byc dodatnia")
        billing = vm_billing_store()
        src = vm_wallet(billing, username)
        dst = vm_wallet(billing, target)
        if src["balance"] < amount:
            raise HTTPException(status_code=402, detail="Brak tokenow")
        src["balance"] -= amount
        src["spent"] += amount
        dst["balance"] += amount
        dst["credited"] += amount
        billing.setdefault("ledger", []).append({"id": uuid.uuid4().hex[:12], "type": "terminal-pay", "from": username, "to": target, "amount": amount, "created_at": now_iso()})
        save_vm_billing(billing)
        response["message"] = f"Przelano {amount} tokenow do {target}."
    elif cmd.startswith("/tokens add "):
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Tylko admin moze dodawac tokeny")
        parts = cmd.split()
        if len(parts) < 4:
            raise HTTPException(status_code=400, detail="Uzycie: /tokens add user amount")
        target = normalize_username(parts[2])
        amount = float(parts[3].replace(",", "."))
        billing = vm_billing_store()
        wallet = vm_wallet(billing, target)
        wallet["balance"] += amount
        wallet["credited"] += amount
        billing.setdefault("ledger", []).append({"id": uuid.uuid4().hex[:12], "type": "terminal-credit", "user": target, "amount": amount, "created_at": now_iso(), "by": username})
        save_vm_billing(billing)
        response["message"] = f"Dodano {amount} tokenow dla {target}."
    elif cmd == "/vm list":
        response["data"] = {"vms": vm_names_for_commander()}
        response["message"] = "Lista VM gotowa."
    elif cmd.startswith("/ai "):
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="AI Commander wymaga admina")
        response["data"] = await ai_commander_run(AiCommanderRequest(command=cmd[4:].strip(), execute=False), admin=user)
        response["message"] = "Plan AI Commander gotowy."
    else:
        raise HTTPException(status_code=400, detail="Nieznana komenda. Wpisz /help")
    logs = read_json(GLOBAL_TERMINAL_FILE, [])
    logs.insert(0, {"id": uuid.uuid4().hex[:12], "command": cmd, "user": username, "response": response, "created_at": now_iso()})
    write_json(GLOBAL_TERMINAL_FILE, logs[:300])
    return response

@app.get("/api/global-terminal/log", dependencies=[Depends(verify_token)])
async def global_terminal_log():
    return {"items": read_json(GLOBAL_TERMINAL_FILE, [])[:80]}

# --- SKLEP WTYCZEK API ---
@app.get("/api/shop/plugins", dependencies=[Depends(verify_token)])
async def get_plugins():
    try: installed = json.loads(PLUGINS_STATE_FILE.read_text())
    except: installed = []
    return [ {**p, "installed": p["id"] in installed} for p in MARKETPLACE_CATALOG ]

@app.post("/api/admin/plugin/install", dependencies=[Depends(verify_admin)])
async def install_plugin(request: Request):
    p_id = (await request.json()).get("id")
    try: installed = json.loads(PLUGINS_STATE_FILE.read_text())
    except: installed = []
    if p_id not in installed:
        installed.append(p_id)
        PLUGINS_STATE_FILE.write_text(json.dumps(installed))
        log_event(f"Zainstalowano wtyczkę: {p_id}")
        (BASE_DIR / f"config_plugin_{p_id}.json").write_text(json.dumps({"status": "active", "date": str(datetime.datetime.now())}))
    return {"status": "success"}

# --- CZAT ---
@app.get("/api/community/messages", dependencies=[Depends(verify_token)])
async def get_messages():
    try: return json.loads(COMMUNITY_FILE.read_text())
    except: return []
@app.post("/api/community/message", dependencies=[Depends(verify_token)])
async def post_message(msg: ChatMessage):
    try: msgs = json.loads(COMMUNITY_FILE.read_text())
    except: msgs = []
    msgs.append({"time": datetime.datetime.now().strftime("%H:%M"), "author": msg.author, "text": msg.text})
    COMMUNITY_FILE.write_text(json.dumps(msgs[-30:]))
    return {"status": "success"}

MEDIA_AUDIO_EXT = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
MEDIA_VIDEO_EXT = {".mp4", ".webm", ".mov", ".mkv"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
VM_IMAGE_EXT = {".iso", ".img", ".qcow2", ".raw"}
OBJECT_BUCKETS = {
    "iso": "nexus-iso",
    "driver": "nexus-iso",
    "audio": "nexus-media",
    "video": "nexus-media",
    "image": "nexus-media",
    "backup": "nexus-backups",
    "drop": "nexus-uploads",
    "data": "nexus-uploads",
}
MINIO_ENV_FILE = Path("/etc/nexus/minio.env")
MINIO_INTERNAL_BASE = "http://127.0.0.1:9000"
S3_REGION = "us-east-1"

def smart_upload_destination(filename: str):
    ext = Path(filename or "").suffix.lower()
    if ext == ".zip" and DRIVER_NAME_RE.search(filename or ""):
        return DRIVER_DIR, "driver", "HYPER-DECK / Driver Vault"
    if ext in VM_IMAGE_EXT:
        return LIBVIRT_ISO_DIR, "iso", "HYPER-DECK / ISO Vault"
    if ext in MEDIA_AUDIO_EXT:
        return MEDIA_DIR, "audio", "NEXUS MEDIA DECK"
    if ext in MEDIA_VIDEO_EXT:
        return MEDIA_DIR, "video", "NEXUS MEDIA DECK"
    if ext in IMAGE_EXT:
        return VISUAL_DIR, "image", "VISUAL ARCHIVE"
    return DROP_DIR, "drop", "SECURE DROP / INBOX"

def read_minio_env():
    config = {}
    try:
        for line in MINIO_ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return config

def minio_credentials():
    config = read_minio_env()
    access = config.get("MINIO_ROOT_USER") or os.environ.get("MINIO_ROOT_USER", "")
    secret = config.get("MINIO_ROOT_PASSWORD") or os.environ.get("MINIO_ROOT_PASSWORD", "")
    if not access or not secret:
        return None
    return access, secret

def object_storage_enabled():
    return bool(minio_credentials())

def object_bucket_for(kind: str):
    return OBJECT_BUCKETS.get(kind or "data", "nexus-uploads")

def object_kind_for(filename: str, purpose: str = "auto"):
    purpose = (purpose or "auto").lower().strip()
    if purpose in OBJECT_BUCKETS:
        return purpose
    _, kind, _ = smart_upload_destination(filename)
    return kind if kind in OBJECT_BUCKETS else "data"

def safe_object_filename(name: str):
    base = Path(name or "upload.bin").name.strip()
    base = re.sub(r"[^A-Za-z0-9._+ -]+", "-", base).strip(" .")
    return base[:180] or f"object-{uuid.uuid4().hex[:8]}.bin"

def safe_object_user(value: str):
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value or "user").strip("-")[:48] or "user"

def object_key_for(user, filename: str, kind: str):
    safe_user = safe_object_user(user.get("username", "user") if isinstance(user, dict) else "user")
    clean_name = safe_object_filename(filename)
    date_part = datetime.datetime.now().strftime("%Y/%m/%d")
    return f"{safe_user}/{kind}/{date_part}/{uuid.uuid4().hex[:10]}-{clean_name}"

def s3_quote(value: str):
    return urllib.parse.quote(str(value), safe="/-_.~")

def s3_signing_key(secret: str, date: str, region: str = S3_REGION, service: str = "s3"):
    def sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()
    k_date = sign(("AWS4" + secret).encode("utf-8"), date)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    return sign(k_service, "aws4_request")

def s3_presigned_url(method: str, bucket: str, key: str, expires: int = 900, base_url: str = "", access_secret=None):
    creds = access_secret or minio_credentials()
    if not creds:
        raise HTTPException(status_code=503, detail="Object Storage nie jest skonfigurowany")
    access, secret = creds
    base = (base_url or MINIO_INTERNAL_BASE).rstrip("/")
    parsed = urllib.parse.urlparse(base)
    host = parsed.netloc
    if not parsed.scheme or not host:
        raise HTTPException(status_code=500, detail="Niepoprawny endpoint Object Storage")
    now = datetime.datetime.utcnow()
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    credential_scope = f"{date_stamp}/{S3_REGION}/s3/aws4_request"
    credential = f"{access}/{credential_scope}"
    canonical_uri = "/" + s3_quote(bucket) + "/" + s3_quote(key)
    params = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": credential,
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(max(60, min(int(expires), 604800))),
        "X-Amz-SignedHeaders": "host",
    }
    canonical_query = "&".join(f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(str(params[k]), safe='-_.~')}" for k in sorted(params))
    canonical_headers = f"host:{host}\n"
    canonical_request = "\n".join([method.upper(), canonical_uri, canonical_query, canonical_headers, "host", "UNSIGNED-PAYLOAD"])
    string_to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, credential_scope, hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()])
    signature = hmac.new(s3_signing_key(secret, date_stamp), string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{base}{canonical_uri}?{canonical_query}&X-Amz-Signature={signature}"

def public_object_base(request: Request):
    config = read_minio_env()
    public_base = config.get("NEXUS_MINIO_PUBLIC_BASE") or os.environ.get("NEXUS_MINIO_PUBLIC_BASE") or ""
    if public_base:
        return public_base.rstrip("/")
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}".rstrip("/")

def object_registry():
    return read_json(OBJECTS_FILE, [])

def save_object_registry(items):
    write_json(OBJECTS_FILE, items[-2000:])

def object_token_registry():
    return read_json(OBJECT_TOKENS_FILE, [])

def save_object_token_registry(items):
    write_json(OBJECT_TOKENS_FILE, items[-1000:])

def object_token_hash(value: str):
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()

def public_object_token(row):
    return {
        "id": row.get("id", ""),
        "name": row.get("name", ""),
        "purpose": row.get("purpose", "auto"),
        "owner": row.get("owner", ""),
        "preview": row.get("preview", ""),
        "created_at": row.get("created_at", ""),
        "expires_at": row.get("expires_at", ""),
        "last_used_at": row.get("last_used_at", ""),
        "revoked_at": row.get("revoked_at", ""),
        "max_size_mb": row.get("max_size_mb", 0),
        "uses": row.get("uses", 0),
        "bytes_uploaded": row.get("bytes_uploaded", 0),
        "bytes_uploaded_label": fmt_size(row.get("bytes_uploaded", 0) or 0),
        "active": bool(row.get("active", True)) and not row.get("revoked_at"),
    }

def clean_object_token_name(name: str):
    clean = re.sub(r"[^A-Za-z0-9._ -]+", "-", (name or "").strip()).strip(" .")
    return clean[:80] or "storage-token"

def object_token_expired(row):
    expires = row.get("expires_at") or ""
    if not expires:
        return False
    try:
        return datetime.datetime.fromisoformat(expires) < datetime.datetime.now()
    except Exception:
        return False

def validate_object_access_token(value: str):
    if not value:
        raise HTTPException(status_code=401, detail="Brak X-Storage-Token")
    digest = object_token_hash(value)
    rows = object_token_registry()
    row = next((item for item in rows if item.get("token_hash") == digest), None)
    if not row:
        raise HTTPException(status_code=401, detail="Niepoprawny storage token")
    if row.get("revoked_at") or row.get("active") is False:
        raise HTTPException(status_code=403, detail="Storage token jest odwolany")
    if object_token_expired(row):
        raise HTTPException(status_code=403, detail="Storage token wygasl")
    return row, rows

def touch_object_token(row, rows, byte_count=0):
    row["last_used_at"] = now_iso()
    row["uses"] = int(row.get("uses", 0) or 0) + 1
    row["bytes_uploaded"] = int(row.get("bytes_uploaded", 0) or 0) + int(byte_count or 0)
    save_object_token_registry(rows)

def register_completed_object(data: ObjectCompleteRequest, owner: str, request_kind: str = "auto"):
    if data.bucket not in set(OBJECT_BUCKETS.values()):
        raise HTTPException(status_code=400, detail="Nieznany bucket NEXUS Object Storage")
    head_url = s3_presigned_url("HEAD", data.bucket, data.key, expires=120, base_url=MINIO_INTERNAL_BASE)
    try:
        req = urllib.request.Request(head_url, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as response:
            actual_size = int(response.headers.get("Content-Length") or data.size or 0)
            etag = (response.headers.get("ETag") or data.etag or "").strip('"')
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"MinIO nie potwierdzil obiektu: {exc}")
    kind = object_kind_for(data.filename, request_kind or data.purpose)
    item = {
        "id": uuid.uuid4().hex[:16],
        "owner": owner,
        "bucket": data.bucket,
        "key": data.key,
        "filename": safe_object_filename(data.filename),
        "kind": kind,
        "size": actual_size,
        "content_type": data.content_type or "application/octet-stream",
        "etag": etag,
        "created_at": now_iso(),
        "imported_path": "",
    }
    rows = [row for row in object_registry() if not (row.get("bucket") == data.bucket and row.get("key") == data.key)]
    rows.append(item)
    save_object_registry(rows)
    return item

def object_status_row(item):
    return {
        **item,
        "size_label": fmt_size(item.get("size", 0) or 0),
    }

def object_import_destination(filename: str, kind: str):
    if kind == "iso":
        return LIBVIRT_ISO_DIR
    if kind == "driver":
        return DRIVER_DIR
    if kind in {"audio", "video"}:
        return MEDIA_DIR
    if kind == "image":
        return VISUAL_DIR
    return DROP_DIR

def usb_mount_registry():
    return read_json(USB_MOUNTS_FILE, [])

def save_usb_mount_registry(items):
    write_json(USB_MOUNTS_FILE, items[-500:])

def cloud_usb_label(value: str):
    clean = re.sub(r"[^A-Za-z0-9_ -]+", "_", (value or "NEXUS_USB").strip()).strip(" _")
    return (clean[:28] or "NEXUS_USB").upper()

def iso_builder_tool():
    for name in ("xorriso", "genisoimage", "mkisofs"):
        path = shutil.which(name)
        if path:
            return name
    return ""

def build_iso_command(source_dir: Path, target_iso: Path, label: str):
    tool = iso_builder_tool()
    if not tool:
        raise HTTPException(status_code=500, detail="Brak xorriso/genisoimage/mkisofs do zbudowania Cloud USB ISO")
    if tool == "xorriso":
        return ["xorriso", "-as", "mkisofs", "-o", str(target_iso), "-J", "-R", "-V", label, str(source_dir)]
    return [tool, "-o", str(target_iso), "-J", "-R", "-V", label, str(source_dir)]

def cloud_usb_object_rows(object_ids):
    ids = set(object_ids or [])
    if not ids:
        raise HTTPException(status_code=400, detail="Wybierz przynajmniej jeden obiekt z Object Storage")
    rows = [row for row in object_registry() if row.get("id") in ids]
    if not rows:
        raise HTTPException(status_code=404, detail="Nie znaleziono wybranych obiektow")
    return rows

def materialize_object_to(source, target: Path):
    imported = source.get("imported_path") or ""
    if imported and Path(imported).exists():
        shutil.copy2(imported, target)
        return
    get_url = s3_presigned_url("GET", source.get("bucket", ""), source.get("key", ""), expires=300, base_url=MINIO_INTERNAL_BASE)
    with urllib.request.urlopen(get_url, timeout=120) as response, open(target, "wb") as out:
        shutil.copyfileobj(response, out)

def free_cloud_usb_target(vm_id: str):
    mounts = usb_mount_registry()
    used = {row.get("target") for row in mounts if row.get("vm_id") == vm_id and row.get("status") == "attached"}
    for target in ["sdb", "sdc", "sdd", "sde", "hdb", "hdc"]:
        if target not in used:
            return target
    return "sdf"

def cloud_usb_tools_status():
    return {
        "lsusb": bool(shutil.which("lsusb")),
        "iso_builder": iso_builder_tool(),
        "mcopy": bool(shutil.which("mcopy")),
        "mkfs_vfat": bool(shutil.which("mkfs.vfat")),
    }

def validate_smart_upload_target(target: Path, root: Path, kind: str, expected_size=None):
    checks = []
    errors = []
    target = target.resolve()
    root = root.resolve()
    expected_root, expected_kind, expected_destination = smart_upload_destination(target.name)
    expected_root = expected_root.resolve()

    def add_check(name, ok, detail):
        row = {"name": name, "ok": bool(ok), "detail": detail}
        checks.append(row)
        if not ok:
            errors.append(f"{name}: {detail}")

    add_check("exists", target.exists(), str(target))
    add_check("is_file", target.is_file(), "plik regularny" if target.is_file() else "brak pliku regularnego")
    add_check("destination_root", target == root or root in target.parents, f"root={root}")
    add_check("expected_route", root == expected_root and kind == expected_kind, f"{target.name} -> {expected_destination}")
    if kind == "iso":
        add_check("libvirt_visible_path", target == LIBVIRT_IMAGE_DIR.resolve() or LIBVIRT_IMAGE_DIR.resolve() in target.parents, "ISO poza /root i w drzewie libvirt")
    if kind == "driver":
        add_check("driver_vault_path", target == DRIVER_DIR.resolve() or DRIVER_DIR.resolve() in target.parents, "paczka sterownikow w Driver Vault")
    if expected_size is not None:
        try:
            expected_int = int(expected_size)
        except Exception:
            expected_int = -1
        if expected_int >= 0:
            actual = target.stat().st_size if target.exists() else -1
            add_check("size_match", actual == expected_int, f"expected={expected_int} actual={actual}")
    actual_size = target.stat().st_size if target.exists() and target.is_file() else 0
    add_check("non_empty", actual_size > 0, f"size={actual_size}")
    if kind == "iso":
        try:
            mode_ok = bool(target.stat().st_mode & 0o044)
        except Exception:
            mode_ok = False
        add_check("libvirt_readable_mode", mode_ok, "plik czytelny dla grupy/innych")
    return checks, errors

def store_smart_upload(file: UploadFile):
    root, kind, destination = smart_upload_destination(file.filename or "upload.bin")
    target = unique_target_path(root, file.filename or "upload.bin")
    expected_size = getattr(file, "size", None)
    with open(target, "wb") as out:
        shutil.copyfileobj(file.file, out)
    if kind in {"iso", "driver"}:
        ensure_libvirt_file_access(target)
    checks, errors = validate_smart_upload_target(target, root, kind, expected_size)
    if errors:
        try:
            if target.exists():
                target.unlink()
        except Exception:
            pass
        raise RuntimeError("; ".join(errors))
    meta = file_meta(target, root, kind)
    meta.update({
        "destination": destination,
        "full_path": str(target),
        "public": False,
        "verified": True,
        "checks": checks,
    })
    return meta

@app.post("/api/upload/smart", dependencies=[Depends(verify_admin)])
async def smart_upload(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Brak plikow")
    results = []
    errors = []
    for file in files:
        if not file or not file.filename:
            continue
        try:
            results.append(store_smart_upload(file))
        except Exception as exc:
            errors.append({"name": Path(file.filename or "upload.bin").name, "error": str(exc)})
    if errors:
        log_event("SMART_UPLOAD errors " + json.dumps(errors, ensure_ascii=False))
        raise HTTPException(status_code=500, detail={"message": "Smart upload nie przeszedl kontroli miejsca docelowego", "errors": errors, "items": results})
    if not results:
        raise HTTPException(status_code=400, detail="Brak poprawnych plikow")
    log_event("SMART_UPLOAD " + ", ".join(f"{item['kind']}:{item['name']}" for item in results))
    return {"status": "success", "items": results}

@app.get("/api/storage/status", dependencies=[Depends(verify_token)])
async def object_storage_status(request: Request, user = Depends(verify_token)):
    creds = minio_credentials()
    buckets = sorted(set(OBJECT_BUCKETS.values()))
    code, _ = run_vm_command(["systemctl", "is-active", "minio"], timeout=5)
    items = [object_status_row(item) for item in object_registry()]
    if user.get("role") != "admin":
        username = user.get("username", "")
        items = [item for item in items if item.get("owner") == username]
    return {
        "enabled": bool(creds),
        "service": "active" if code == 0 else "inactive",
        "public_base": public_object_base(request),
        "internal_base": MINIO_INTERNAL_BASE,
        "buckets": buckets,
        "objects": sorted(items, key=lambda row: row.get("created_at", ""), reverse=True)[:200],
        "note": "MinIO S3 path-style: /bucket/key. Upload idzie do MinIO, FastAPI tylko podpisuje URL.",
    }

@app.get("/api/storage/tokens", dependencies=[Depends(verify_admin)])
async def object_storage_tokens(admin = Depends(verify_admin)):
    rows = object_token_registry()
    return {"tokens": [public_object_token(row) for row in sorted(rows, key=lambda item: item.get("created_at", ""), reverse=True)]}

@app.post("/api/storage/tokens", dependencies=[Depends(verify_admin)])
async def object_storage_token_create(data: ObjectTokenCreateRequest, admin = Depends(verify_admin)):
    purpose = (data.purpose or "auto").lower().strip()
    if purpose != "auto" and purpose not in OBJECT_BUCKETS:
        raise HTTPException(status_code=400, detail="Nieznany zakres tokenu")
    raw_token = "nxst_" + secrets.token_urlsafe(32)
    now = datetime.datetime.now()
    row = {
        "id": uuid.uuid4().hex[:16],
        "name": clean_object_token_name(data.name),
        "purpose": purpose,
        "owner": admin.get("username", "admin"),
        "token_hash": object_token_hash(raw_token),
        "preview": raw_token[:8] + "..." + raw_token[-6:],
        "created_at": now_iso(),
        "expires_at": (now + datetime.timedelta(days=data.expires_days)).isoformat(timespec="seconds"),
        "last_used_at": "",
        "revoked_at": "",
        "active": True,
        "max_size_mb": int(data.max_size_mb or 0),
        "uses": 0,
        "bytes_uploaded": 0,
    }
    rows = object_token_registry()
    rows.append(row)
    save_object_token_registry(rows)
    log_event(f"OBJECT_TOKEN_CREATE by={admin.get('username')} id={row['id']} purpose={purpose}")
    return {"status": "created", "token": raw_token, "record": public_object_token(row)}

@app.post("/api/storage/tokens/revoke", dependencies=[Depends(verify_admin)])
async def object_storage_token_revoke(data: ObjectTokenRevokeRequest, admin = Depends(verify_admin)):
    rows = object_token_registry()
    row = next((item for item in rows if item.get("id") == data.token_id), None)
    if not row:
        raise HTTPException(status_code=404, detail="Nie znaleziono tokenu")
    row["revoked_at"] = row.get("revoked_at") or now_iso()
    row["active"] = False
    save_object_token_registry(rows)
    log_event(f"OBJECT_TOKEN_REVOKE by={admin.get('username')} id={row.get('id')}")
    return {"status": "revoked", "record": public_object_token(row)}

@app.post("/api/storage/presign", dependencies=[Depends(verify_token)])
async def object_storage_presign(data: ObjectPresignRequest, request: Request, user = Depends(verify_token)):
    if not object_storage_enabled():
        raise HTTPException(status_code=503, detail="Object Storage / MinIO nie jest jeszcze aktywny")
    kind = object_kind_for(data.filename, data.purpose)
    bucket = object_bucket_for(kind)
    key = object_key_for(user, data.filename, kind)
    url = s3_presigned_url("PUT", bucket, key, expires=900, base_url=public_object_base(request))
    return {
        "method": "PUT",
        "url": url,
        "headers": {"Content-Type": data.content_type or "application/octet-stream"},
        "bucket": bucket,
        "key": key,
        "kind": kind,
        "filename": safe_object_filename(data.filename),
        "expires_seconds": 900,
        "destination": object_import_destination(data.filename, kind).as_posix(),
    }

@app.post("/api/storage/token/presign")
async def object_storage_token_presign(data: ObjectPresignRequest, request: Request, x_storage_token: str = Header(None)):
    if not object_storage_enabled():
        raise HTTPException(status_code=503, detail="Object Storage / MinIO nie jest jeszcze aktywny")
    row, rows = validate_object_access_token(x_storage_token)
    max_size_mb = int(row.get("max_size_mb", 0) or 0)
    if max_size_mb and int(data.size or 0) > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Token pozwala maksymalnie na {max_size_mb} MB")
    purpose = row.get("purpose") or "auto"
    if purpose == "auto":
        purpose = data.purpose or "auto"
    kind = object_kind_for(data.filename, purpose)
    if row.get("purpose") not in {"", "auto", kind}:
        raise HTTPException(status_code=403, detail="Token nie ma uprawnien do tego typu pliku")
    bucket = object_bucket_for(kind)
    token_user = {"username": f"token-{row.get('id', '')[:8]}"}
    key = object_key_for(token_user, data.filename, kind)
    url = s3_presigned_url("PUT", bucket, key, expires=900, base_url=public_object_base(request))
    touch_object_token(row, rows, 0)
    return {
        "method": "PUT",
        "url": url,
        "headers": {"Content-Type": data.content_type or "application/octet-stream"},
        "bucket": bucket,
        "key": key,
        "kind": kind,
        "filename": safe_object_filename(data.filename),
        "expires_seconds": 900,
    }

@app.post("/api/storage/complete", dependencies=[Depends(verify_token)])
async def object_storage_complete(data: ObjectCompleteRequest, user = Depends(verify_token)):
    if data.bucket not in set(OBJECT_BUCKETS.values()):
        raise HTTPException(status_code=400, detail="Nieznany bucket NEXUS Object Storage")
    safe_user = safe_object_user(user.get("username", "user"))
    if user.get("role") != "admin" and not data.key.startswith(f"{safe_user}/"):
        raise HTTPException(status_code=403, detail="Ten obiekt nie nalezy do Twojego prefixu")
    head_url = s3_presigned_url("HEAD", data.bucket, data.key, expires=120, base_url=MINIO_INTERNAL_BASE)
    try:
        req = urllib.request.Request(head_url, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as response:
            actual_size = int(response.headers.get("Content-Length") or data.size or 0)
            etag = (response.headers.get("ETag") or data.etag or "").strip('"')
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"MinIO nie potwierdzil obiektu: {exc}")
    kind = object_kind_for(data.filename, data.purpose)
    item = {
        "id": uuid.uuid4().hex[:16],
        "owner": user.get("username", "user"),
        "bucket": data.bucket,
        "key": data.key,
        "filename": safe_object_filename(data.filename),
        "kind": kind,
        "size": actual_size,
        "content_type": data.content_type or "application/octet-stream",
        "etag": etag,
        "created_at": now_iso(),
        "imported_path": "",
    }
    rows = [row for row in object_registry() if not (row.get("bucket") == data.bucket and row.get("key") == data.key)]
    rows.append(item)
    save_object_registry(rows)
    log_event(f"OBJECT_COMPLETE owner={item['owner']} bucket={data.bucket} key={data.key} size={actual_size}")
    return {"status": "done", "object": object_status_row(item)}

@app.post("/api/storage/token/complete")
async def object_storage_token_complete(data: ObjectCompleteRequest, x_storage_token: str = Header(None)):
    row, rows = validate_object_access_token(x_storage_token)
    prefix = f"token-{row.get('id', '')[:8]}/"
    if not data.key.startswith(prefix):
        raise HTTPException(status_code=403, detail="Klucz obiektu nie nalezy do tego tokenu")
    purpose = row.get("purpose") or data.purpose or "auto"
    item = register_completed_object(data, owner=f"token:{row.get('name', 'storage-token')}", request_kind=purpose)
    touch_object_token(row, rows, item.get("size", 0))
    log_event(f"OBJECT_TOKEN_COMPLETE token={row.get('id')} bucket={data.bucket} key={data.key} size={item.get('size', 0)}")
    return {"status": "done", "object": object_status_row(item)}

@app.get("/api/storage/objects", dependencies=[Depends(verify_token)])
async def object_storage_objects(user = Depends(verify_token)):
    rows = object_registry()
    if user.get("role") != "admin":
        rows = [row for row in rows if row.get("owner") == user.get("username")]
    return {"objects": [object_status_row(item) for item in sorted(rows, key=lambda row: row.get("created_at", ""), reverse=True)[:500]]}

@app.post("/api/storage/import", dependencies=[Depends(verify_admin)])
async def object_storage_import(data: ObjectImportRequest, admin = Depends(verify_admin)):
    rows = object_registry()
    item = next((row for row in rows if row.get("id") == data.object_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Nie znaleziono obiektu")
    bucket = item.get("bucket", "")
    key = item.get("key", "")
    filename = safe_object_filename(item.get("filename") or Path(key).name)
    kind = item.get("kind") or object_kind_for(filename, "auto")
    root = object_import_destination(filename, kind)
    root.mkdir(parents=True, exist_ok=True)
    target = unique_target_path(root, filename)
    get_url = s3_presigned_url("GET", bucket, key, expires=300, base_url=MINIO_INTERNAL_BASE)
    try:
        with urllib.request.urlopen(get_url, timeout=60) as response, open(target, "wb") as out:
            shutil.copyfileobj(response, out)
        if kind in {"iso", "driver"}:
            ensure_libvirt_file_access(target)
        checks, errors = validate_smart_upload_target(target, root, kind, item.get("size"))
        if errors:
            raise HTTPException(status_code=500, detail={"errors": errors, "checks": checks})
        item["imported_path"] = str(target)
        item["imported_at"] = now_iso()
        save_object_registry(rows)
        log_event(f"OBJECT_IMPORT by={admin.get('username')} bucket={bucket} key={key} target={target}")
        return {"status": "imported", "path": str(target), "checks": checks, "object": object_status_row(item)}
    except HTTPException:
        raise
    except Exception as exc:
        try:
            if target.exists():
                target.unlink()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Import obiektu nie powiodl sie: {exc}")

@app.get("/api/usb/status", dependencies=[Depends(verify_token)])
async def usb_status():
    return {"tools": cloud_usb_tools_status(), "mounts": usb_mount_registry()}

@app.get("/api/usb/host/list", dependencies=[Depends(verify_admin)])
async def usb_host_list():
    if not shutil.which("lsusb"):
        return {"items": [], "message": "Brak lsusb na serwerze"}
    code, output = run_vm_command(["lsusb"], timeout=8)
    items = []
    for line in output.splitlines():
        match = re.search(r"ID\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\s*(.*)$", line)
        if match:
            items.append({"vendor_id": match.group(1).lower(), "product_id": match.group(2).lower(), "name": match.group(3).strip(), "raw": line})
    return {"items": items, "message": "OK" if code == 0 else output.strip()}

@app.get("/api/usb/cloud/objects", dependencies=[Depends(verify_token)])
async def usb_cloud_objects(user = Depends(verify_token)):
    rows = object_registry()
    if user.get("role") != "admin":
        rows = [row for row in rows if row.get("owner") == user.get("username")]
    allowed = [row for row in rows if row.get("kind") in {"drop", "image", "audio", "video", "data", "backup"} or row.get("bucket") in {"nexus-uploads", "nexus-media"}]
    return {"objects": [object_status_row(row) for row in sorted(allowed, key=lambda item: item.get("created_at", ""), reverse=True)[:300]]}

@app.post("/api/usb/cloud/mount", dependencies=[Depends(verify_admin)])
async def usb_cloud_mount(data: CloudUSBMountRequest, admin = Depends(verify_admin)):
    if detect_vm_backend() != "libvirt":
        raise HTTPException(status_code=400, detail="Cloud USB attach jest teraz wspierany dla libvirt/KVM")
    vm_id = safe_vm_target(data.vm_id)
    label = cloud_usb_label(data.label)
    rows = cloud_usb_object_rows(data.object_ids)
    mount_id = uuid.uuid4().hex[:12]
    work_dir = CLOUD_USB_DIR / mount_id
    files_dir = work_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    for row in rows:
        name = safe_object_filename(row.get("filename") or Path(row.get("key", "object.bin")).name)
        target = unique_target_path(files_dir, name)
        materialize_object_to(row, target)
    image = work_dir / f"{label.lower()}-{mount_id}.iso"
    command = build_iso_command(files_dir, image, label)
    code, output = run_vm_command(command, timeout=300)
    if code != 0 or not image.exists():
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie zbudowac Cloud USB ISO")
    ensure_libvirt_file_access(image)
    target_dev = free_cloud_usb_target(vm_id)
    attach = ["virsh", "attach-disk", vm_id, str(image), target_dev, "--type", "cdrom", "--mode", "readonly", "--live"]
    code, attach_output = run_vm_command(attach, timeout=30)
    if code != 0:
        raise HTTPException(status_code=500, detail=attach_output.strip() or "Nie udalo sie podpiac Cloud USB do VM")
    record = {
        "id": mount_id,
        "vm_id": vm_id,
        "target": target_dev,
        "label": label,
        "image": str(image),
        "object_ids": data.object_ids,
        "files": [row.get("filename") for row in rows],
        "status": "attached",
        "created_at": now_iso(),
        "created_by": admin.get("username", "admin"),
    }
    mounts = usb_mount_registry()
    mounts.append(record)
    save_usb_mount_registry(mounts)
    log_event(f"CLOUD_USB_MOUNT vm={vm_id} target={target_dev} objects={len(rows)} by={admin.get('username')}")
    return {"status": "attached", "mount": record, "output": attach_output.strip()}

@app.post("/api/usb/cloud/detach", dependencies=[Depends(verify_admin)])
async def usb_cloud_detach(data: CloudUSBDetachRequest, admin = Depends(verify_admin)):
    mounts = usb_mount_registry()
    record = next((row for row in mounts if row.get("id") == data.mount_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Nie znaleziono Cloud USB")
    if record.get("status") != "attached":
        return {"status": "already_detached", "mount": record}
    code, output = run_vm_command(["virsh", "detach-disk", record.get("vm_id", ""), record.get("target", ""), "--live"], timeout=30)
    if code != 0:
        raise HTTPException(status_code=500, detail=output.strip() or "Nie udalo sie odpiac Cloud USB")
    record["status"] = "detached"
    record["detached_at"] = now_iso()
    record["detached_by"] = admin.get("username", "admin")
    save_usb_mount_registry(mounts)
    log_event(f"CLOUD_USB_DETACH vm={record.get('vm_id')} target={record.get('target')} by={admin.get('username')}")
    return {"status": "detached", "mount": record}

@app.get("/api/media/list", dependencies=[Depends(verify_token)])
async def media_list():
    items = []
    for path in sorted(MEDIA_DIR.rglob("*"))[:500]:
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        kind = "audio" if ext in MEDIA_AUDIO_EXT else "video" if ext in MEDIA_VIDEO_EXT else "image" if ext in IMAGE_EXT else ""
        if kind:
            items.append(file_meta(path, MEDIA_DIR, kind))
    return {"root": str(MEDIA_DIR), "items": items}

@app.get("/api/media/stream")
async def media_stream(path: str, token: str = ""):
    require_query_session(token)
    target = resolve_under(MEDIA_DIR, path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Brak pliku")
    return FileResponse(str(target), media_type=mimetypes.guess_type(target.name)[0] or "application/octet-stream", filename=target.name)

@app.get("/api/gallery/list", dependencies=[Depends(verify_token)])
async def gallery_list():
    items = []
    for source, root in [("visual", VISUAL_DIR), ("media", MEDIA_DIR)]:
        for path in sorted(root.rglob("*"))[:500]:
            if path.is_file() and path.suffix.lower() in IMAGE_EXT:
                item = file_meta(path, root, "image")
                item["source"] = source
                items.append(item)
    items.sort(key=lambda x: x["modified"], reverse=True)
    return {"items": items}

@app.get("/api/gallery/image")
async def gallery_image(source: str, path: str, token: str = ""):
    require_query_session(token)
    root = VISUAL_DIR if source == "visual" else MEDIA_DIR
    target = resolve_under(root, path)
    if not target.exists() or not target.is_file() or target.suffix.lower() not in IMAGE_EXT:
        raise HTTPException(status_code=404, detail="Brak obrazu")
    return FileResponse(str(target), media_type=mimetypes.guess_type(target.name)[0] or "image/jpeg")

@app.get("/api/bbs/posts", dependencies=[Depends(verify_token)])
async def bbs_posts():
    return read_json(BBS_FILE, [])

@app.post("/api/bbs/posts")
async def bbs_create_post(text: str = Form(...), file: UploadFile = File(None), user = Depends(verify_token)):
    posts = read_json(BBS_FILE, [])
    image = ""
    if file and file.filename:
        safe_name = f"{uuid.uuid4().hex}_{Path(file.filename).name}"
        target = BBS_UPLOAD_DIR / safe_name
        with open(target, "wb") as out:
            shutil.copyfileobj(file.file, out)
        image = safe_name
    post = {
        "id": uuid.uuid4().hex[:12],
        "author": user.get("username", "user"),
        "role": user.get("role", "user"),
        "text": text[:1200],
        "image": image,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "comments": [],
        "reputation": 0,
        "reputation_users": [],
    }
    posts.insert(0, post)
    write_json(BBS_FILE, posts[:300])
    return post

@app.get("/api/bbs/image/{name}")
async def bbs_image(name: str, token: str = ""):
    require_query_session(token)
    target = BBS_UPLOAD_DIR / Path(name).name
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Brak obrazu")
    return FileResponse(str(target), media_type=mimetypes.guess_type(target.name)[0] or "image/jpeg")

@app.post("/api/bbs/comment")
async def bbs_comment(data: BBSCommentRequest, user = Depends(verify_token)):
    posts = read_json(BBS_FILE, [])
    for post in posts:
        if post.get("id") == data.post_id:
            post.setdefault("comments", []).append({
                "id": uuid.uuid4().hex[:10],
                "author": user.get("username", "user"),
                "text": data.text[:800],
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
            write_json(BBS_FILE, posts)
            return post
    raise HTTPException(status_code=404, detail="Brak posta")

@app.post("/api/bbs/rep")
async def bbs_rep(data: BBSRepRequest, user = Depends(verify_token)):
    posts = read_json(BBS_FILE, [])
    username = user.get("username", "user")
    for post in posts:
        if post.get("id") == data.post_id:
            users = post.setdefault("reputation_users", [])
            if username in users:
                users.remove(username)
            else:
                users.append(username)
            post["reputation"] = len(users)
            write_json(BBS_FILE, posts)
            return {"reputation": post["reputation"]}
    raise HTTPException(status_code=404, detail="Brak posta")

@app.get("/api/kanban", dependencies=[Depends(verify_token)])
async def kanban_get():
    return read_json(KANBAN_FILE, {"columns": []})

@app.post("/api/kanban/card")
async def kanban_add_card(data: KanbanCardRequest, admin = Depends(verify_admin)):
    board = read_json(KANBAN_FILE, {"columns": []})
    card = {"id": uuid.uuid4().hex[:10], "title": data.title, "body": data.body, "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}
    for column in board.get("columns", []):
        if column.get("id") == data.column_id:
            column.setdefault("cards", []).append(card)
            write_json(KANBAN_FILE, board)
            return card
    raise HTTPException(status_code=404, detail="Brak kolumny")

@app.post("/api/kanban/state")
async def kanban_save(data: KanbanStateRequest, admin = Depends(verify_admin)):
    board = {"columns": data.columns}
    write_json(KANBAN_FILE, board)
    return {"status": "success"}

@app.get("/api/drop/list", dependencies=[Depends(verify_admin)])
async def drop_list():
    return read_json(SHARES_FILE, [])

@app.get("/api/drop/inbox", dependencies=[Depends(verify_admin)])
async def drop_inbox():
    items = []
    for path in sorted(DROP_DIR.rglob("*"))[:500]:
        if path.is_file():
            item = file_meta(path, DROP_DIR, "drop")
            item["full_path"] = str(path.resolve())
            item["destination"] = "SECURE DROP / INBOX"
            items.append(item)
    items.sort(key=lambda item: item["modified"], reverse=True)
    return {"root": str(DROP_DIR), "items": items}

@app.post("/api/drop/share")
async def drop_share(data: DropShareRequest, admin = Depends(verify_admin)):
    target = Path(data.path).resolve()
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Brak pliku")
    shares = read_json(SHARES_FILE, [])
    code = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8]
    item = {
        "code": code,
        "title": data.title or target.name,
        "path": str(target),
        "name": target.name,
        "size_label": fmt_size(target.stat().st_size),
        "downloads": 0,
        "created_by": admin.get("username", "admin"),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "url": f"/d/{code}",
    }
    shares.insert(0, item)
    write_json(SHARES_FILE, shares)
    return item

@app.get("/d/{code}")
async def drop_download(code: str):
    shares = read_json(SHARES_FILE, [])
    for item in shares:
        if item.get("code") == code:
            target = Path(item.get("path", ""))
            if not target.exists() or not target.is_file():
                raise HTTPException(status_code=404, detail="Plik wygasl")
            item["downloads"] = int(item.get("downloads", 0)) + 1
            write_json(SHARES_FILE, shares)
            return FileResponse(str(target), filename=item.get("name") or target.name)
    raise HTTPException(status_code=404, detail="Brak linku")

@app.post("/api/presence/heartbeat")
async def presence_heartbeat(data: PresenceHeartbeatRequest, x_auth_token: str = Header(None), user = Depends(verify_token)):
    session = SESSIONS.get(x_auth_token or "")
    if session:
        session["device_id"] = data.device_id[:80]
        session["label"] = data.label[:120] or "WEB"
        session["last_seen"] = now_iso()
    return {"status": "online", "server_time": now_iso()}

@app.get("/api/presence", dependencies=[Depends(verify_token)])
async def presence_list():
    now = datetime.datetime.now()
    sessions = []
    for _, session in list(SESSIONS.items()):
        try:
            last_seen = datetime.datetime.fromisoformat(session.get("last_seen", session.get("created_at", now_iso())))
        except Exception:
            last_seen = now
        age = max(0, int((now - last_seen).total_seconds()))
        if age <= 900:
            sessions.append({
                "username": session.get("username", "user"),
                "role": session.get("role", "user"),
                "device_id": session.get("device_id", "")[-16:],
                "label": session.get("label", "WEB"),
                "last_seen": session.get("last_seen", ""),
                "age_seconds": age,
                "active": age <= 90,
            })
    sessions.sort(key=lambda row: row["age_seconds"])
    return {"count": len(sessions), "active_count": len([s for s in sessions if s["active"]]), "sessions": sessions, "server_time": now_iso()}

@app.get("/api/alerts", dependencies=[Depends(verify_token)])
async def alerts_list():
    return read_json(ALERTS_FILE, [])

@app.post("/api/alerts")
async def alerts_create(data: AlertRequest, admin = Depends(verify_admin)):
    alerts = read_json(ALERTS_FILE, [])
    level = data.level.lower()
    if level not in ["info", "warn", "critical"]:
        level = "info"
    item = {
        "id": uuid.uuid4().hex[:12],
        "title": data.title[:120],
        "body": data.body[:500],
        "level": level,
        "created_by": admin.get("username", "admin"),
        "created_at": now_iso(),
    }
    alerts.insert(0, item)
    write_json(ALERTS_FILE, alerts[:200])
    log_event(f"ALERT {level.upper()}: {item['title']}")
    return item

@app.post("/api/push/subscribe")
async def push_subscribe(data: PushSubscriptionRequest, user = Depends(verify_token)):
    subs = read_json(PUSH_SUBS_FILE, [])
    sub = data.subscription or {}
    endpoint = sub.get("endpoint") or f"local:{user.get('username')}:{uuid.uuid4().hex[:8]}"
    item = {
        "endpoint": endpoint,
        "subscription": sub,
        "username": user.get("username", "user"),
        "created_at": now_iso(),
    }
    subs = [existing for existing in subs if existing.get("endpoint") != endpoint]
    subs.insert(0, item)
    write_json(PUSH_SUBS_FILE, subs[:100])
    return {"status": "saved", "subscriptions": len(subs), "server_push": False}

@app.get("/api/p2p/signals")
async def p2p_get_signals(room: str, peer: str, user = Depends(verify_token)):
    rooms = read_json(P2P_FILE, {})
    signals = rooms.get(room, [])
    return {"signals": [s for s in signals[-100:] if s.get("peer") != peer]}

@app.post("/api/p2p/signal")
async def p2p_signal(data: P2PSignalRequest, user = Depends(verify_token)):
    rooms = read_json(P2P_FILE, {})
    room = data.room[:80]
    signals = rooms.setdefault(room, [])
    signals.append({
        "id": uuid.uuid4().hex[:12],
        "peer": data.peer[:80],
        "username": user.get("username", "user"),
        "created_at": now_iso(),
        "payload": data.payload,
    })
    rooms[room] = signals[-200:]
    write_json(P2P_FILE, rooms)
    return {"status": "sent"}

@app.get("/api/briefing", dependencies=[Depends(verify_token)])
async def briefing_get():
    briefing = read_json(BRIEFING_FILE, {})
    if briefing.get("date") != today_key() and datetime.datetime.now().hour >= 8:
        briefing = build_briefing()
    return briefing if briefing else build_briefing()

@app.post("/api/briefing/generate")
async def briefing_generate(admin = Depends(verify_admin)):
    return build_briefing()

@app.get("/api/karma")
async def karma_get(user = Depends(verify_token)):
    data = read_json(KARMA_FILE, {})
    username = user.get("username", "user")
    user_data = data.get(username, {"login_dates": [], "exp": 0})
    streak = login_streak(user_data.get("login_dates", []))
    uptime = system_uptime_days()
    exp = int(user_data.get("exp", 0)) + min(uptime * 5, 500)
    level = max(1, exp // 100 + 1)
    return {
        "username": username,
        "exp": exp,
        "level": level,
        "next_level_exp": level * 100,
        "login_streak": streak,
        "uptime_days": uptime,
        "last_login": user_data.get("last_login", ""),
    }

def crypto_symbol(value: str):
    clean = re.sub(r"[^A-Za-z0-9._-]+", "", (value or "").strip().upper())
    if not clean:
        raise HTTPException(status_code=400, detail="Podaj symbol monety")
    return clean[:20]

def crypto_coin_public(row):
    amount = float(row.get("amount", 0) or 0)
    buy_price = float(row.get("buy_price_usd", 0) or 0)
    cost = amount * buy_price
    return {
        **row,
        "amount": amount,
        "buy_price_usd": buy_price,
        "cost_basis_usd": round(cost, 4),
        "cost_basis_label": f"${cost:,.2f}",
    }

@app.get("/api/crypto/coins")
async def crypto_coins_get(user = Depends(verify_token)):
    store = read_json(CRYPTO_PORTFOLIO_FILE, {})
    username = user.get("username", "user")
    coins = [crypto_coin_public(row) for row in store.get(username, [])]
    total = sum(row.get("cost_basis_usd", 0) for row in coins)
    return {"username": username, "coins": coins, "total_cost_usd": round(total, 4), "total_cost_label": f"${total:,.2f}"}

@app.post("/api/crypto/coins")
async def crypto_coin_add(data: CryptoCoinRequest, user = Depends(verify_token)):
    store = read_json(CRYPTO_PORTFOLIO_FILE, {})
    username = user.get("username", "user")
    coins = store.setdefault(username, [])
    symbol = crypto_symbol(data.symbol)
    existing = next((row for row in coins if row.get("symbol") == symbol), None)
    row = existing or {"id": uuid.uuid4().hex[:12], "symbol": symbol, "created_at": now_iso()}
    row.update({
        "symbol": symbol,
        "name": (data.name or symbol).strip()[:80],
        "amount": float(data.amount or 0),
        "buy_price_usd": float(data.buy_price_usd or 0),
        "note": (data.note or "").strip()[:240],
        "updated_at": now_iso(),
    })
    if not existing:
        coins.insert(0, row)
    store[username] = coins[:300]
    write_json(CRYPTO_PORTFOLIO_FILE, store)
    log_event(f"CRYPTO_COIN_SAVE user={username} symbol={symbol} amount={row['amount']}")
    return {"status": "saved", "coin": crypto_coin_public(row)}

@app.post("/api/crypto/coins/delete")
async def crypto_coin_delete(data: CryptoCoinDeleteRequest, user = Depends(verify_token)):
    store = read_json(CRYPTO_PORTFOLIO_FILE, {})
    username = user.get("username", "user")
    before = store.get(username, [])
    after = [row for row in before if row.get("id") != data.coin_id]
    if len(after) == len(before):
        raise HTTPException(status_code=404, detail="Nie znaleziono monety")
    store[username] = after
    write_json(CRYPTO_PORTFOLIO_FILE, store)
    log_event(f"CRYPTO_COIN_DELETE user={username} coin={data.coin_id}")
    return {"status": "deleted"}

@app.get("/api/web3/status")
async def web3_status(user = Depends(verify_token)):
    data = read_json(WEB3_FILE, {})
    try:
        __import__("eth_account")
        verifier = {"available": True, "dependency": "eth_account"}
    except Exception as exc:
        verifier = {"available": False, "dependency": "eth_account", "error": str(exc)}
    row = data.get(user.get("username", "user"), {"linked": False})
    row["signature_verifier"] = verifier
    row["endpoints"] = ["/api/web3/status", "/api/web3/nonce", "/api/web3/verify"]
    return row

@app.post("/api/web3/nonce")
async def web3_nonce(data: Web3NonceRequest, user = Depends(verify_token)):
    store = read_json(WEB3_FILE, {})
    username = user.get("username", "user")
    nonce = secrets.token_hex(16)
    challenge = f"NEXUS WEB3 AUTH\nuser={username}\naddress={data.address.lower()}\nnonce={nonce}\ntime={now_iso()}"
    record = store.setdefault(username, {})
    record.update({"address": data.address.lower(), "nonce": nonce, "challenge": challenge, "linked": False, "updated_at": now_iso()})
    write_json(WEB3_FILE, store)
    return {"challenge": challenge}

@app.post("/api/web3/verify")
async def web3_verify(data: Web3VerifyRequest, user = Depends(verify_token)):
    store = read_json(WEB3_FILE, {})
    username = user.get("username", "user")
    record = store.get(username, {})
    challenge = record.get("challenge", "")
    if not challenge or record.get("address", "").lower() != data.address.lower():
        raise HTTPException(status_code=400, detail="Brak aktywnego wyzwania Web3")
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct
        recovered = Account.recover_message(encode_defunct(text=challenge), signature=data.signature)
        verified = recovered.lower() == data.address.lower()
    except Exception as exc:
        raise HTTPException(status_code=501, detail=f"Brak weryfikatora eth_account: {exc}")
    if not verified:
        raise HTTPException(status_code=401, detail="Podpis Web3 nie pasuje do adresu")
    record.update({"linked": True, "verified_at": now_iso(), "signature_tail": data.signature[-12:]})
    write_json(WEB3_FILE, store)
    return {"status": "verified", "address": data.address.lower()}

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.environ.get("NEXUS_BIND", "0.0.0.0"),
        port=int(os.environ.get("NEXUS_PORT", "9090")),
    )
