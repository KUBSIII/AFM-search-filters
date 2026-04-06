from datetime import date, datetime, timezone

from sqlalchemy import select

from app.db.models import Player
from app.repositories.player_repository import PlayerRepository


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def test_upsert_insert_and_get(db_session) -> None:
    repo = PlayerRepository(db_session)

    player = repo.upsert_player(
        {
            "transfermarkt_id": "1001",
            "full_name": "Leo Test",
            "profile_url": "https://example.com/player/1001",
            "position": "Forward",
            "club_apps": 10,
            "birth_date": date(1990, 1, 1),
            "last_scraped_at": now_utc(),
        }
    )
    db_session.commit()

    fetched = repo.get_by_transfermarkt_id("1001")

    assert player.id is not None
    assert fetched is not None
    assert fetched.full_name == "Leo Test"


def test_upsert_updates_existing_player(db_session) -> None:
    repo = PlayerRepository(db_session)

    repo.upsert_player(
        {
            "transfermarkt_id": "2002",
            "full_name": "Initial Name",
            "profile_url": "https://example.com/player/2002",
            "club_apps": 5,
            "last_scraped_at": now_utc(),
        }
    )
    db_session.commit()

    repo.upsert_player(
        {
            "transfermarkt_id": "2002",
            "full_name": "Updated Name",
            "profile_url": "https://example.com/player/2002",
            "club_apps": 12,
            "sync_status": "partial",
            "last_scraped_at": now_utc(),
        }
    )
    db_session.commit()

    rows = db_session.scalars(select(Player).where(Player.transfermarkt_id == "2002")).all()

    assert len(rows) == 1
    assert rows[0].full_name == "Updated Name"
    assert rows[0].club_apps == 12
    assert rows[0].sync_status == "partial"


def test_list_count_filters_and_sort(db_session) -> None:
    repo = PlayerRepository(db_session)

    seed_data = [
        {
            "transfermarkt_id": "3001",
            "full_name": "Alpha Forward",
            "profile_url": "https://example.com/player/3001",
            "position": "Forward",
            "agent_name": "Agent A",
            "club_apps": 15,
            "birth_date": date(1995, 1, 1),
            "last_scraped_at": now_utc(),
        },
        {
            "transfermarkt_id": "3002",
            "full_name": "Beta Midfielder",
            "profile_url": "https://example.com/player/3002",
            "position": "Midfielder",
            "agent_name": "Agent B",
            "club_apps": 22,
            "birth_date": date(1992, 6, 1),
            "last_scraped_at": now_utc(),
        },
        {
            "transfermarkt_id": "3003",
            "full_name": "Gamma Forward",
            "profile_url": "https://example.com/player/3003",
            "position": "Forward",
            "agent_name": "Agent A",
            "club_apps": 9,
            "birth_date": date(1998, 2, 1),
            "last_scraped_at": now_utc(),
        },
    ]

    for player_data in seed_data:
        repo.upsert_player(player_data)
    db_session.commit()

    filtered = repo.list_players(
        limit=10,
        offset=0,
        filters={"position": "Forward", "agent_name": "Agent A", "club_apps_min": 10},
        sort=("club_apps", "desc"),
    )
    total = repo.count_players(filters={"name": "Forward"})

    assert len(filtered) == 1
    assert filtered[0].transfermarkt_id == "3001"
    assert total == 2


def test_case_insensitive_exact_filters_and_additional_ranges(db_session) -> None:
    repo = PlayerRepository(db_session)

    repo.upsert_player(
        {
            "transfermarkt_id": "4001",
            "full_name": "Case Target",
            "profile_url": "https://example.com/player/4001",
            "position": "Forward",
            "agent_name": "Agent X",
            "club_apps": 45,
            "national_team_apps": 18,
            "contract_expires_at": date(2028, 6, 30),
            "last_scraped_at": now_utc(),
        }
    )
    repo.upsert_player(
        {
            "transfermarkt_id": "4002",
            "full_name": "Case Other",
            "profile_url": "https://example.com/player/4002",
            "position": "Forwarder",
            "agent_name": "Agent XY",
            "club_apps": 40,
            "national_team_apps": 2,
            "contract_expires_at": date(2026, 6, 30),
            "last_scraped_at": now_utc(),
        }
    )
    db_session.commit()

    items = repo.list_players(
        limit=10,
        offset=0,
        filters={
            "position": "forward",
            "agent_name": "agent x",
            "national_team_apps_min": 10,
            "national_team_apps_max": 20,
            "contract_expires_after": date(2027, 1, 1),
            "contract_expires_before": date(2029, 1, 1),
        },
        sort=("national_team_apps", "desc"),
    )

    assert len(items) == 1
    assert items[0].transfermarkt_id == "4001"


def test_sort_tie_breaks_by_id(db_session) -> None:
    repo = PlayerRepository(db_session)

    for player_id in ["5001", "5002", "5003"]:
        repo.upsert_player(
            {
                "transfermarkt_id": player_id,
                "full_name": "Tie",
                "profile_url": f"https://example.com/player/{player_id}",
                "club_apps": 10,
                "last_scraped_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
            }
        )
    db_session.commit()

    items = repo.list_players(limit=10, offset=0, sort=("club_apps", "desc"))

    ids = [item.id for item in items]
    assert ids == sorted(ids)
