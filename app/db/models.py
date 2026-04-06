from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        Index("ix_players_transfermarkt_id", "transfermarkt_id", unique=True),
        Index("ix_players_full_name", "full_name"),
        Index("ix_players_birth_date", "birth_date"),
        Index("ix_players_position", "position"),
        Index("ix_players_contract_expires_at", "contract_expires_at"),
        Index("ix_players_agent_name", "agent_name"),
        Index("ix_players_last_scraped_at", "last_scraped_at"),
        Index("ix_players_next_refresh_at", "next_refresh_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transfermarkt_id: Mapped[str] = mapped_column(String(64), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    position: Mapped[str | None] = mapped_column(String(128), nullable=True)
    club_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    club_apps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    national_team_apps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    contract_expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    agent_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    last_scraped_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    sync_status: Mapped[str] = mapped_column(String(32), default="ok", nullable=False)
    sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_refresh_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
