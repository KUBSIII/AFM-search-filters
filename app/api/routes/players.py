from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError

from app.db.session import SessionLocal
from app.schemas.players import PlayerQueryParams, PlayersQueryResponse, SortBy, SortOrder
from app.services.player_query_service import PlayerQueryService

router = APIRouter(tags=["players"])


def get_player_query_service() -> PlayerQueryService:
    return PlayerQueryService(session_factory=SessionLocal)


def get_player_query_params(
    name: str | None = Query(default=None),
    birth_date_from: str | None = Query(default=None),
    birth_date_to: str | None = Query(default=None),
    club_apps_min: int | None = Query(default=None),
    club_apps_max: int | None = Query(default=None),
    national_team_apps_min: int | None = Query(default=None),
    national_team_apps_max: int | None = Query(default=None),
    position: str | None = Query(default=None),
    contract_expires_before: str | None = Query(default=None),
    contract_expires_after: str | None = Query(default=None),
    agent: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort_by: SortBy = Query(default="last_scraped_at"),
    sort_order: SortOrder = Query(default="desc"),
) -> PlayerQueryParams:
    try:
        return PlayerQueryParams(
            name=name,
            birth_date_from=birth_date_from,
            birth_date_to=birth_date_to,
            club_apps_min=club_apps_min,
            club_apps_max=club_apps_max,
            national_team_apps_min=national_team_apps_min,
            national_team_apps_max=national_team_apps_max,
            position=position,
            contract_expires_before=contract_expires_before,
            contract_expires_after=contract_expires_after,
            agent=agent,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/players", response_model=PlayersQueryResponse)
def get_players(
    params: PlayerQueryParams = Depends(get_player_query_params),
    service: PlayerQueryService = Depends(get_player_query_service),
) -> PlayersQueryResponse:
    return service.query_players(params)
