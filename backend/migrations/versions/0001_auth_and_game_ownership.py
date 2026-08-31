"""Add authentication tables and game ownership.

Revision ID: 0001_auth_and_game_ownership
Revises:
Create Date: 2026-08-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_auth_and_game_ownership"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"], unique=False)
    op.create_index("ix_sessions_token_hash", "sessions", ["token_hash"], unique=True)
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"], unique=False)
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("normalized_email", sa.String(), nullable=False),
        sa.Column("client_ip", sa.String(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_login_attempts_normalized_email", "login_attempts", ["normalized_email"], unique=False)
    op.create_index("ix_login_attempts_client_ip", "login_attempts", ["client_ip"], unique=False)
    op.create_index("ix_login_attempts_attempted_at", "login_attempts", ["attempted_at"], unique=False)

    # This intentionally fails when legacy games exist: ownership cannot be inferred safely.
    op.add_column("games", sa.Column("user_id", sa.Integer(), nullable=False))
    op.create_foreign_key("fk_games_user_id_users", "games", "users", ["user_id"], ["id"])
    op.create_index("ix_games_user_id", "games", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_games_user_id", table_name="games")
    op.drop_constraint("fk_games_user_id_users", "games", type_="foreignkey")
    op.drop_column("games", "user_id")

    op.drop_index("ix_login_attempts_attempted_at", table_name="login_attempts")
    op.drop_index("ix_login_attempts_client_ip", table_name="login_attempts")
    op.drop_index("ix_login_attempts_normalized_email", table_name="login_attempts")
    op.drop_table("login_attempts")

    op.drop_index("ix_sessions_expires_at", table_name="sessions")
    op.drop_index("ix_sessions_token_hash", table_name="sessions")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_table("users")
