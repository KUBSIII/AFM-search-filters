from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.routes.players import get_player_query_service
from app.main import app
from app.repositories.player_repository import PlayerRepository
from app.scrapers.http_client import TransfermarktHttpClient
from app.services.player_query_service import PlayerQueryService


def _seed_data(session: Session) -> None:
    repo = PlayerRepository(session)
    rows = [
        {
            "transfermarkt_id": "8001",
            "full_name": "Alpha One",
            "birth_date": date(1998, 1, 1),
            "position": "Forward",
            "club_name": "A Club",
            "club_apps": 30,
            "national_team_apps": 15,
            "contract_expires_at": date(2028, 6, 30),
            "agent_name": "Agent Prime",
            "profile_url": "https://example.com/8001",
            "last_scraped_at": datetime(2026, 4, 10, tzinfo=timezone.utc),
            "sync_status": "ok",
        },
        {
            "transfermarkt_id": "8002",
            "full_name": "Beta Two",
            "birth_date": date(2000, 5, 1),
            "position": "Midfielder",
            "club_name": "B Club",
            "club_apps": 12,
            "national_team_apps": 3,
            "contract_expires_at": date(2026, 6, 30),
            "agent_name": "Agent Other",
            "profile_url": "https://example.com/8002",
            "last_scraped_at": datetime(2026, 4, 9, tzinfo=timezone.utc),
            "sync_status": "partial",
        },
        {
            "transfermarkt_id": "8003",
            "full_name": "Gamma Three",
            "birth_date": date(1996, 7, 15),
            "position": "Forward",
            "club_name": "C Club",
            "club_apps": 45,
            "national_team_apps": 20,
            "contract_expires_at": date(2029, 6, 30),
            "agent_name": "Agent Prime",
            "profile_url": "https://example.com/8003",
            "last_scraped_at": datetime(2026, 4, 11, tzinfo=timezone.utc),
            "sync_status": "ok",
        },
    ]

    for row in rows:
        repo.upsert_player(row)
    session.commit()


def _build_query_engine(tmp_path: Path):
    db_path = tmp_path / "query_api.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", future=True)

    from app.db.base import Base

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )

    with session_factory() as session:
        _seed_data(session)

    app.dependency_overrides[get_player_query_service] = lambda: PlayerQueryService(session_factory)

    return engine


def test_get_players_default_query(client, tmp_path: Path) -> None:
    engine = _build_query_engine(tmp_path)
    try:
        response = client.get("/players")
    finally:
        app.dependency_overrides.clear()
        engine.dispose()

    assert response.status_code == 200
    body = response.json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert body["total"] == 3
    assert [item["transfermarkt_id"] for item in body["items"]] == ["8003", "8001", "8002"]


def test_get_players_filters_and_sort(client, tmp_path: Path) -> None:
    engine = _build_query_engine(tmp_path)
    params = {
        "position": "forward",
        "agent": "agent prime",
        "club_apps_min": 20,
        "club_apps_max": 50,
        "national_team_apps_min": 10,
        "national_team_apps_max": 20,
        "contract_expires_after": "2027-01-01",
        "contract_expires_before": "2029-12-31",
        "sort_by": "club_apps",
        "sort_order": "desc",
        "limit": 10,
        "offset": 0,
    }

    try:
        response = client.get("/players", params=params)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["transfermarkt_id"] for item in body["items"]] == ["8003", "8001"]


def test_get_players_422_for_invalid_ranges(client) -> None:
    response = client.get("/players", params={"club_apps_min": 20, "club_apps_max": 10})
    assert response.status_code == 422


def test_get_players_422_for_invalid_sort_by(client) -> None:
    response = client.get("/players", params={"sort_by": "agent_name"})
    assert response.status_code == 422


def test_get_players_requires_no_auth(client, tmp_path: Path) -> None:
    engine = _build_query_engine(tmp_path)
    try:
        response = client.get("/players")
    finally:
        app.dependency_overrides.clear()
        engine.dispose()

    assert response.status_code == 200


def test_get_players_does_not_use_scraper(client, tmp_path: Path, monkeypatch) -> None:
    def _raise_if_called(*args, **kwargs):
        raise RuntimeError("scraper should not be called")

    monkeypatch.setattr(TransfermarktHttpClient, "get_text", _raise_if_called)

    engine = _build_query_engine(tmp_path)
    try:
        response = client.get("/players")
    finally:
        app.dependency_overrides.clear()
        engine.dispose()

    assert response.status_code == 200
