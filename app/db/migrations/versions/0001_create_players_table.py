"""create players table"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_create_players_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("transfermarkt_id", sa.String(length=64), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("position", sa.String(length=128), nullable=True),
        sa.Column("club_name", sa.String(length=255), nullable=True),
        sa.Column("club_apps", sa.Integer(), nullable=True),
        sa.Column("national_team_apps", sa.Integer(), nullable=True),
        sa.Column("contract_expires_at", sa.Date(), nullable=True),
        sa.Column("agent_name", sa.String(length=255), nullable=True),
        sa.Column("profile_url", sa.String(length=1024), nullable=False),
        sa.Column("last_scraped_at", sa.DateTime(), nullable=False),
        sa.Column("sync_status", sa.String(length=32), server_default=sa.text("'ok'"), nullable=False),
        sa.Column("sync_error", sa.Text(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("next_refresh_at", sa.DateTime(), nullable=True),
        sa.Column("source_hash", sa.String(length=128), nullable=True),
        sa.Column("raw_payload_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_players_transfermarkt_id", "players", ["transfermarkt_id"], unique=True)
    op.create_index("ix_players_full_name", "players", ["full_name"], unique=False)
    op.create_index("ix_players_birth_date", "players", ["birth_date"], unique=False)
    op.create_index("ix_players_position", "players", ["position"], unique=False)
    op.create_index("ix_players_contract_expires_at", "players", ["contract_expires_at"], unique=False)
    op.create_index("ix_players_agent_name", "players", ["agent_name"], unique=False)
    op.create_index("ix_players_last_scraped_at", "players", ["last_scraped_at"], unique=False)
    op.create_index("ix_players_next_refresh_at", "players", ["next_refresh_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_players_next_refresh_at", table_name="players")
    op.drop_index("ix_players_last_scraped_at", table_name="players")
    op.drop_index("ix_players_agent_name", table_name="players")
    op.drop_index("ix_players_contract_expires_at", table_name="players")
    op.drop_index("ix_players_position", table_name="players")
    op.drop_index("ix_players_birth_date", table_name="players")
    op.drop_index("ix_players_full_name", table_name="players")
    op.drop_index("ix_players_transfermarkt_id", table_name="players")
    op.drop_table("players")
