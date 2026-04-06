from sqlalchemy.orm import Session, sessionmaker

from app.repositories.player_repository import PlayerRepository
from app.schemas.players import PlayerListItem, PlayerQueryParams, PlayersQueryResponse


class PlayerQueryService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def query_players(self, params: PlayerQueryParams) -> PlayersQueryResponse:
        filters = self._build_filters(params)
        sort = (params.sort_by, params.sort_order)

        with self.session_factory() as session:
            repo = PlayerRepository(session)
            players = repo.list_players(
                limit=params.limit,
                offset=params.offset,
                filters=filters,
                sort=sort,
            )
            total = repo.count_players(filters=filters)

        return PlayersQueryResponse(
            items=[PlayerListItem.model_validate(player, from_attributes=True) for player in players],
            total=total,
            limit=params.limit,
            offset=params.offset,
        )

    @staticmethod
    def _build_filters(params: PlayerQueryParams) -> dict[str, object]:
        filters: dict[str, object] = {
            "name": params.name,
            "birth_date_from": params.birth_date_from,
            "birth_date_to": params.birth_date_to,
            "club_apps_min": params.club_apps_min,
            "club_apps_max": params.club_apps_max,
            "national_team_apps_min": params.national_team_apps_min,
            "national_team_apps_max": params.national_team_apps_max,
            "position": params.position,
            "contract_expires_before": params.contract_expires_before,
            "contract_expires_after": params.contract_expires_after,
            "agent_name": params.agent,
        }

        return {key: value for key, value in filters.items() if value is not None}
