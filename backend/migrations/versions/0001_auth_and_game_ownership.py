"""Add authentication tables and game ownership.

Brings any database to the current schema regardless of how it was built:

- empty database: creates auth tables and games
- pre-auth database (create_all era, no auth tables): creates auth tables and
  alters games to add the owner column
- database already built by create_all with the new models: creates nothing and
  only records the revision

Ownership cannot be inferred safely for legacy games, so altering a games table
that still holds rows without a user_id fails by design (batch recreate violates
the NOT NULL constraint during the row copy).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0001_auth_and_game_ownership"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _has_column(table: str, column: str) -> bool:
    return column in [col["name"] for col in sa.inspect(op.get_bind()).get_columns(table)]


def _create_auth_tables() -> None:
    if not _has_table("users"):
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
    if not _has_table("sessions"):
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
    if not _has_table("login_attempts"):
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


def _add_game_ownership() -> None:
    if not _has_table("games"):
        op.create_table(
            "games",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("rng_seed", sa.Integer(), nullable=False),
            sa.Column("initial_capital", sa.Float(), nullable=False),
            sa.Column("current_turn", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("game_length_turns", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_games_user_id_users"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_games_user_id", "games", ["user_id"], unique=False)
        return

    if _has_column("games", "user_id"):
        return

    row_count = op.get_bind().execute(sa.text("SELECT COUNT(*) FROM games")).scalar_one()
    if row_count:
        raise RuntimeError(
            f"games table holds {row_count} legacy row(s) without an owner; "
            "ownership cannot be inferred safely, so assign or archive them "
            "manually before running this migration"
        )
    # Drop residue from any previously failed batch recreate (SQLite DDL here
    # does not roll back automatically).
    op.get_bind().execute(sa.text("DROP TABLE IF EXISTS _alembic_tmp_games"))

    # Batch mode recreates the table because SQLite cannot ADD COLUMN with
    # NOT NULL directly. Only reachable for an empty legacy games table, so the
    # recreate never has to assign owners.
    with op.batch_alter_table("games", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=False))
        batch_op.create_foreign_key("fk_games_user_id_users", "users", ["user_id"], ["id"])
        batch_op.create_index("ix_games_user_id", ["user_id"])


def _remove_game_ownership() -> None:
    if not _has_table("games") or not _has_column("games", "user_id"):
        return
    with op.batch_alter_table("games", recreate="always") as batch_op:
        batch_op.drop_index("ix_games_user_id")
        batch_op.drop_constraint("fk_games_user_id_users", type_="foreignkey")
        batch_op.drop_column("user_id")


def upgrade() -> None:
    _create_auth_tables()
    _add_game_ownership()


def downgrade() -> None:
    _remove_game_ownership()

    if _has_table("login_attempts"):
        op.drop_index("ix_login_attempts_attempted_at", table_name="login_attempts")
        op.drop_index("ix_login_attempts_client_ip", table_name="login_attempts")
        op.drop_index("ix_login_attempts_normalized_email", table_name="login_attempts")
        op.drop_table("login_attempts")

    if _has_table("sessions"):
        op.drop_index("ix_sessions_expires_at", table_name="sessions")
        op.drop_index("ix_sessions_token_hash", table_name="sessions")
        op.drop_index("ix_sessions_user_id", table_name="sessions")
        op.drop_table("sessions")

    if _has_table("users"):
        op.drop_table("users")
