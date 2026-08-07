"""IAM core tables

Revision ID: 0001_iam
Revises:
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_iam"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "iam_users",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("username", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="USER"),
        sa.Column("status", sa.Text(), nullable=False, server_default="PENDING"),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("approved_by", sa.Text()),
        sa.Column("rejected_at", sa.DateTime(timezone=True)),
        sa.Column("rejected_by", sa.Text()),
        sa.Column("suspended_at", sa.DateTime(timezone=True)),
        sa.Column("suspended_by", sa.Text()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("password_changed_at", sa.DateTime(timezone=True)),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("role IN ('ADMIN','USER')", name="ck_iam_users_role"),
        sa.CheckConstraint("status IN ('PENDING','ACTIVE','SUSPENDED','REJECTED','DELETED')", name="ck_iam_users_status"),
    )
    op.create_index("idx_iam_users_status", "iam_users", ["status"])
    op.create_table(
        "iam_sessions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("token_hash", sa.Text(), nullable=False, unique=True),
        sa.Column("refresh_hash", sa.Text()),
        sa.Column("username", sa.Text(), sa.ForeignKey("iam_users.username", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("ip", sa.Text()),
        sa.Column("user_agent", sa.Text()),
    )
    op.create_index("idx_iam_sessions_username", "iam_sessions", ["username"])
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("actor", sa.Text()),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("target", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("ip", sa.Text()),
        sa.Column("user_agent", sa.Text()),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_audit_log_created_at", "audit_log", ["created_at"])


def downgrade():
    op.drop_index("idx_audit_log_created_at", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("idx_iam_sessions_username", table_name="iam_sessions")
    op.drop_table("iam_sessions")
    op.drop_index("idx_iam_users_status", table_name="iam_users")
    op.drop_table("iam_users")
