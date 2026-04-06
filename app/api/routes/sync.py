from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.security import require_sync_api_key
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.normalizers.player_normalizer import PlayerNormalizer
from app.schemas.sync import BatchSyncRequest, SearchSyncRequest, SyncBatchResponse
from app.scrapers.club_players_scraper import ClubPlayersScraper
from app.scrapers.http_client import TransfermarktHttpClient
from app.scrapers.player_profile_scraper import PlayerProfileScraper
from app.scrapers.player_search_scraper import PlayerSearchScraper
from app.services.player_sync_service import PlayerSyncService

router = APIRouter(tags=["sync"])


@lru_cache(maxsize=1)
def get_transfermarkt_http_client() -> TransfermarktHttpClient:
    settings = get_settings()
    return TransfermarktHttpClient(
        timeout_s=settings.tm_http_timeout_s,
        max_retries=settings.tm_max_retries,
        backoff_base_s=settings.tm_backoff_base_s,
        rate_limit_rps=settings.tm_rate_limit_rps,
    )


def get_player_sync_service() -> PlayerSyncService:
    client = get_transfermarkt_http_client()
    return PlayerSyncService(
        session_factory=SessionLocal,
        profile_scraper=PlayerProfileScraper(client),
        club_scraper=ClubPlayersScraper(client),
        search_scraper=PlayerSearchScraper(client),
        normalizer=PlayerNormalizer(),
    )


def _single_response_dict(result: object) -> dict[str, object]:
    status_value = getattr(result, "status", "error")
    summary = {"processed": 1, "ok": 0, "partial": 0, "error": 0}
    if status_value in summary:
        summary[status_value] += 1
    else:
        summary["error"] += 1

    return {
        "summary": summary,
        "results": [
            {
                "transfermarkt_id": getattr(result, "transfermarkt_id", ""),
                "status": status_value,
                "message": getattr(result, "message", None),
                "player_id": getattr(result, "player_id", None),
            }
        ],
    }


@router.post("/players/sync/search", response_model=SyncBatchResponse, dependencies=[Depends(require_sync_api_key)])
def sync_players_by_name(
    payload: SearchSyncRequest,
    service: PlayerSyncService = Depends(get_player_sync_service),
) -> SyncBatchResponse:
    try:
        transfermarkt_ids = service.fetch_player_ids_by_name(payload.name, limit=payload.limit)
    except Exception as exc:  # noqa: BLE001 - external integration
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if not transfermarkt_ids:
        return SyncBatchResponse.model_validate(
            {
                "summary": {"processed": 0, "ok": 0, "partial": 0, "error": 0},
                "results": [],
            }
        )

    result = service.sync_batch(transfermarkt_ids)
    return SyncBatchResponse.model_validate(result.to_dict())


@router.post("/players/sync/{transfermarkt_id}", response_model=SyncBatchResponse, dependencies=[Depends(require_sync_api_key)])
def sync_single_player(
    transfermarkt_id: str,
    service: PlayerSyncService = Depends(get_player_sync_service),
) -> SyncBatchResponse:
    result = service.sync_player(transfermarkt_id)
    return SyncBatchResponse.model_validate(_single_response_dict(result))


@router.post("/players/sync", response_model=SyncBatchResponse, dependencies=[Depends(require_sync_api_key)])
def sync_players_batch(
    payload: BatchSyncRequest,
    service: PlayerSyncService = Depends(get_player_sync_service),
) -> SyncBatchResponse:
    settings = get_settings()
    if len(payload.transfermarkt_ids) > settings.sync_max_batch:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Batch exceeds SYNC_MAX_BATCH={settings.sync_max_batch}",
        )

    result = service.sync_batch(payload.transfermarkt_ids)
    return SyncBatchResponse.model_validate(result.to_dict())


@router.post("/clubs/{club_id}/players/sync", response_model=SyncBatchResponse, dependencies=[Depends(require_sync_api_key)])
def sync_club_players(
    club_id: str,
    service: PlayerSyncService = Depends(get_player_sync_service),
) -> SyncBatchResponse:
    settings = get_settings()
    try:
        transfermarkt_ids = service.fetch_club_player_ids(club_id)
    except Exception as exc:  # noqa: BLE001 - external integration
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if len(transfermarkt_ids) > settings.sync_max_club_players:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Club roster exceeds SYNC_MAX_CLUB_PLAYERS={settings.sync_max_club_players}",
        )

    if not transfermarkt_ids:
        return SyncBatchResponse.model_validate(
            {
                "summary": {"processed": 0, "ok": 0, "partial": 0, "error": 0},
                "results": [],
            }
        )

    result = service.sync_batch(transfermarkt_ids)
    return SyncBatchResponse.model_validate(result.to_dict())

