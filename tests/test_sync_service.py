from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import Player
from app.normalizers.player_normalizer import PlayerNormalizer
from app.scrapers.exceptions import TransfermarktRequestError
from app.services.player_sync_service import PlayerSyncService


class FakeProfileScraper:
    def __init__(self, payloads: dict[str, dict[str, str | None] | Exception]):
        self.payloads = payloads

    def fetch_player_profile(self, transfermarkt_id: str) -> dict[str, str | None]:
        payload = self.payloads[transfermarkt_id]
        if isinstance(payload, Exception):
            raise payload
        return payload


class FakeClubScraper:
    def __init__(self, ids: list[str]):
        self.ids = ids

    def fetch_club_player_ids(self, club_id: str) -> list[str]:
        return self.ids


class FakeSearchScraper:
    def __init__(self, result_ids: list[str]):
        self.result_ids = result_ids

    def fetch_player_ids_by_name(self, name: str, limit: int = 5) -> list[str]:
        return self.result_ids[:limit]


def _build_service(
    tmp_path: Path,
    payloads: dict[str, dict[str, str | None] | Exception],
    club_ids: list[str],
    search_ids: list[str] | None = None,
) -> tuple[PlayerSyncService, sessionmaker[Session]]:
    db_path = tmp_path / "service_sync_test.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )

    service = PlayerSyncService(
        session_factory=session_factory,
        profile_scraper=FakeProfileScraper(payloads),
        club_scraper=FakeClubScraper(club_ids),
        search_scraper=FakeSearchScraper(search_ids or []),
        normalizer=PlayerNormalizer(),
    )

    return service, session_factory


def test_sync_player_ok(tmp_path: Path) -> None:
    service, session_factory = _build_service(
        tmp_path,
        payloads={
            "5001": {
                "transfermarkt_id": "5001",
                "full_name": "Service Player",
                "birth_date": "1999-03-01",
                "position": "Forward",
                "club_name": "Club A",
                "club_apps": "12",
                "national_team_apps": "3",
                "contract_expires_at": "2027-06-30",
                "agent_name": "Agent A",
                "profile_url": "https://example.com/player/5001",
            }
        },
        club_ids=["5001"],
    )

    result = service.sync_player("5001")

    assert result.status == "ok"
    assert result.player_id is not None

    with session_factory() as session:
        row = session.query(Player).filter(Player.transfermarkt_id == "5001").one()
        assert row.full_name == "Service Player"


def test_sync_player_partial(tmp_path: Path) -> None:
    service, _ = _build_service(
        tmp_path,
        payloads={
            "5002": {
                "transfermarkt_id": "5002",
                "full_name": "Partial Player",
                "birth_date": "2000-01-01",
                "position": "Midfielder",
                "club_name": "Club B",
                "club_apps": "8",
                "national_team_apps": None,
                "contract_expires_at": None,
                "agent_name": None,
                "profile_url": "https://example.com/player/5002",
            }
        },
        club_ids=["5002"],
    )

    result = service.sync_player("5002")

    assert result.status == "partial"
    assert result.message is not None


def test_sync_batch_mixed_result(tmp_path: Path) -> None:
    service, session_factory = _build_service(
        tmp_path,
        payloads={
            "5003": {
                "transfermarkt_id": "5003",
                "full_name": "OK Player",
                "birth_date": "1998-01-01",
                "position": "Defender",
                "club_name": "Club C",
                "club_apps": "20",
                "national_team_apps": "4",
                "contract_expires_at": "2028-06-30",
                "agent_name": "Agent C",
                "profile_url": "https://example.com/player/5003",
            },
            "5004": TransfermarktRequestError("upstream unavailable"),
        },
        club_ids=["5003", "5004"],
    )

    result = service.sync_batch(["5003", "5004"])

    assert result.summary == {"processed": 2, "ok": 1, "partial": 0, "error": 1}

    with session_factory() as session:
        rows = session.query(Player).all()
        assert len(rows) == 1


def test_sync_club_returns_ids(tmp_path: Path) -> None:
    service, _ = _build_service(
        tmp_path,
        payloads={},
        club_ids=["9001", "9002"],
    )

    assert service.fetch_club_player_ids("10") == ["9001", "9002"]


def test_sync_search_returns_ids(tmp_path: Path) -> None:
    service, _ = _build_service(
        tmp_path,
        payloads={},
        club_ids=[],
        search_ids=["28003", "68290", "342229"],
    )

    assert service.fetch_player_ids_by_name("Messi", limit=2) == ["28003", "68290"]

