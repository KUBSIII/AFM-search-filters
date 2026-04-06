from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

command = pytest.importorskip("alembic.command")
Config = pytest.importorskip("alembic.config").Config


def test_alembic_upgrade_creates_players_schema(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    db_path = tmp_path / "migration_test.db"
    db_url = f"sqlite+pysqlite:///{db_path}"

    alembic_cfg = Config(str(project_root / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(project_root / "app/db/migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    command.upgrade(alembic_cfg, "head")

    engine = create_engine(db_url, future=True)
    inspector = inspect(engine)

    assert "players" in inspector.get_table_names()

    columns = {column["name"] for column in inspector.get_columns("players")}
    required_columns = {
        "id",
        "transfermarkt_id",
        "full_name",
        "birth_date",
        "position",
        "club_name",
        "club_apps",
        "national_team_apps",
        "contract_expires_at",
        "agent_name",
        "profile_url",
        "last_scraped_at",
        "sync_status",
        "sync_error",
        "last_success_at",
        "next_refresh_at",
        "source_hash",
        "raw_payload_json",
    }
    assert required_columns.issubset(columns)

    indexes = {index["name"] for index in inspector.get_indexes("players")}
    required_indexes = {
        "ix_players_transfermarkt_id",
        "ix_players_full_name",
        "ix_players_birth_date",
        "ix_players_position",
        "ix_players_contract_expires_at",
        "ix_players_agent_name",
        "ix_players_last_scraped_at",
        "ix_players_next_refresh_at",
    }
    assert required_indexes.issubset(indexes)

    engine.dispose()
