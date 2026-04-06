from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.db.models import Player


class PlayerRepository:
    def __init__(self, session: Session):
        self.session = session

    def upsert_player(self, player_data: dict[str, Any]) -> Player:
        transfermarkt_id = player_data.get("transfermarkt_id")
        if not transfermarkt_id:
            raise ValueError("transfermarkt_id is required")

        player = self.get_by_transfermarkt_id(str(transfermarkt_id))
        payload = dict(player_data)
        payload.setdefault("last_scraped_at", datetime.now(timezone.utc))
        payload.setdefault("sync_status", "ok")

        if player is None:
            player = Player(**payload)
            self.session.add(player)
        else:
            for key, value in payload.items():
                if key == "id":
                    continue
                if hasattr(player, key):
                    setattr(player, key, value)

        self.session.flush()
        return player

    def mark_sync_error(self, transfermarkt_id: str, error_message: str) -> Player | None:
        player = self.get_by_transfermarkt_id(transfermarkt_id)
        if player is None:
            return None

        now = datetime.now(timezone.utc)
        player.sync_status = "error"
        player.sync_error = error_message
        player.last_scraped_at = now
        self.session.flush()
        return player

    def get_by_transfermarkt_id(self, transfermarkt_id: str) -> Player | None:
        stmt = select(Player).where(Player.transfermarkt_id == transfermarkt_id)
        return self.session.scalar(stmt)

    def list_players(
        self,
        limit: int,
        offset: int,
        filters: dict[str, Any] | None = None,
        sort: tuple[str, str] | None = None,
    ) -> list[Player]:
        stmt = select(Player)
        stmt = self._apply_filters(stmt, filters or {})
        stmt = self._apply_sort(stmt, sort)
        stmt = stmt.offset(max(offset, 0)).limit(max(limit, 1))
        return list(self.session.scalars(stmt))

    def count_players(self, filters: dict[str, Any] | None = None) -> int:
        stmt = select(func.count(Player.id))
        stmt = self._apply_filters(stmt, filters or {})
        return int(self.session.scalar(stmt) or 0)

    def _apply_filters(self, stmt: Select[Any], filters: dict[str, Any]) -> Select[Any]:
        name = filters.get("name")
        if name:
            stmt = stmt.where(Player.full_name.ilike(f"%{name}%"))

        position = filters.get("position")
        if position:
            stmt = stmt.where(Player.position == position)

        agent = filters.get("agent_name")
        if agent:
            stmt = stmt.where(Player.agent_name == agent)

        birth_date_from = filters.get("birth_date_from")
        if isinstance(birth_date_from, date):
            stmt = stmt.where(Player.birth_date >= birth_date_from)

        birth_date_to = filters.get("birth_date_to")
        if isinstance(birth_date_to, date):
            stmt = stmt.where(Player.birth_date <= birth_date_to)

        club_apps_min = filters.get("club_apps_min")
        if club_apps_min is not None:
            stmt = stmt.where(Player.club_apps >= int(club_apps_min))

        club_apps_max = filters.get("club_apps_max")
        if club_apps_max is not None:
            stmt = stmt.where(Player.club_apps <= int(club_apps_max))

        return stmt

    def _apply_sort(self, stmt: Select[Any], sort: tuple[str, str] | None) -> Select[Any]:
        sort_field = "id"
        sort_order = "asc"

        if sort is not None:
            sort_field = sort[0]
            sort_order = sort[1].lower()

        allowed_fields = {
            "id": Player.id,
            "full_name": Player.full_name,
            "birth_date": Player.birth_date,
            "club_apps": Player.club_apps,
            "contract_expires_at": Player.contract_expires_at,
            "last_scraped_at": Player.last_scraped_at,
        }

        column = allowed_fields.get(sort_field, Player.id)
        order_expr = column.desc() if sort_order == "desc" else column.asc()

        if column is Player.id:
            return stmt.order_by(order_expr)

        return stmt.order_by(order_expr, Player.id.asc())
