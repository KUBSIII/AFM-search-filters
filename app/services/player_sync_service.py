from dataclasses import asdict, dataclass
import logging
from sqlalchemy.orm import Session, sessionmaker

from app.normalizers.player_normalizer import PlayerNormalizer
from app.repositories.player_repository import PlayerRepository
from app.scrapers.club_players_scraper import ClubPlayersScraper
from app.scrapers.player_profile_scraper import PlayerProfileScraper
from app.scrapers.player_search_scraper import PlayerSearchScraper
from app.scrapers.player_stats_scraper import PlayerStatsScraper

logger = logging.getLogger(__name__)


@dataclass
class SyncItemResult:
    transfermarkt_id: str
    status: str
    message: str | None = None
    player_id: int | None = None


@dataclass
class SyncBatchResult:
    summary: dict[str, int]
    results: list[SyncItemResult]

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary,
            "results": [asdict(result) for result in self.results],
        }


class PlayerSyncService:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        profile_scraper: PlayerProfileScraper,
        club_scraper: ClubPlayersScraper,
        search_scraper: PlayerSearchScraper,
        stats_scraper: PlayerStatsScraper,
        normalizer: PlayerNormalizer,
    ):
        self.session_factory = session_factory
        self.profile_scraper = profile_scraper
        self.club_scraper = club_scraper
        self.search_scraper = search_scraper
        self.stats_scraper = stats_scraper
        self.normalizer = normalizer

    def fetch_club_player_ids(self, club_id: str) -> list[str]:
        return self.club_scraper.fetch_club_player_ids(club_id)

    def fetch_player_ids_by_name(self, name: str, limit: int = 5) -> list[str]:
        return self.search_scraper.fetch_player_ids_by_name(name, limit=limit)

    def sync_player(self, transfermarkt_id: str) -> SyncItemResult:
        transfermarkt_id = str(transfermarkt_id)
        try:
            raw = self.profile_scraper.fetch_player_profile(transfermarkt_id)
            raw = self._enrich_with_stats(raw, transfermarkt_id)
            normalized = self.normalizer.normalize_player(raw)

            with self.session_factory() as session:
                repo = PlayerRepository(session)
                player = repo.upsert_player(normalized)
                session.commit()

            return SyncItemResult(
                transfermarkt_id=transfermarkt_id,
                status=str(normalized.get("sync_status", "ok")),
                message=normalized.get("sync_error") if isinstance(normalized.get("sync_error"), str) else None,
                player_id=player.id,
            )
        except Exception as exc:  # noqa: BLE001 - intentional full capture for batch resilience
            logger.exception("Failed to sync player %s", transfermarkt_id)
            self._mark_error_if_exists(transfermarkt_id, str(exc))
            return SyncItemResult(transfermarkt_id=transfermarkt_id, status="error", message=str(exc), player_id=None)

    def sync_batch(self, transfermarkt_ids: list[str]) -> SyncBatchResult:
        results: list[SyncItemResult] = []
        for transfermarkt_id in transfermarkt_ids:
            results.append(self.sync_player(str(transfermarkt_id)))

        return SyncBatchResult(summary=self._build_summary(results), results=results)

    def _enrich_with_stats(self, raw: dict[str, str | None], transfermarkt_id: str) -> dict[str, str | None]:
        """Fetch club_apps from the stats page if not already present in the profile."""
        if raw.get("club_apps"):
            return raw

        try:
            club_apps = self.stats_scraper.fetch_club_apps(transfermarkt_id)
            if club_apps is not None:
                raw["club_apps"] = str(club_apps)
                logger.info("Enriched player %s with club_apps=%d from stats page", transfermarkt_id, club_apps)
        except Exception as exc:  # noqa: BLE001 - non-critical enrichment
            logger.warning("Failed to fetch stats for player %s: %s", transfermarkt_id, exc)

        return raw

    def _mark_error_if_exists(self, transfermarkt_id: str, error_message: str) -> None:
        try:
            with self.session_factory() as session:
                repo = PlayerRepository(session)
                repo.mark_sync_error(transfermarkt_id, error_message)
                session.commit()
        except Exception as exc:  # noqa: BLE001 - logging only
            logger.warning("Failed to mark sync error for %s: %s", transfermarkt_id, exc)

    @staticmethod
    def _build_summary(results: list[SyncItemResult]) -> dict[str, int]:
        summary = {"processed": len(results), "ok": 0, "partial": 0, "error": 0}
        for result in results:
            if result.status in summary:
                summary[result.status] += 1
            else:
                summary["error"] += 1
        return summary
