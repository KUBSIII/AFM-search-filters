from dataclasses import dataclass

from app.api.routes.sync import get_player_sync_service
from app.main import app


@dataclass
class DummyResult:
    transfermarkt_id: str
    status: str
    message: str | None = None
    player_id: int | None = None


class DummyService:
    def __init__(self):
        self.club_ids = ["7001", "7002"]

    def sync_player(self, transfermarkt_id: str):
        return DummyResult(transfermarkt_id=transfermarkt_id, status="ok", player_id=11)

    def sync_batch(self, transfermarkt_ids: list[str]):
        results = []
        for player_id in transfermarkt_ids:
            if player_id == "bad":
                results.append(DummyResult(transfermarkt_id=player_id, status="error", message="boom"))
            else:
                results.append(DummyResult(transfermarkt_id=player_id, status="ok", player_id=10))

        summary = {
            "processed": len(results),
            "ok": sum(1 for item in results if item.status == "ok"),
            "partial": sum(1 for item in results if item.status == "partial"),
            "error": sum(1 for item in results if item.status == "error"),
        }
        return type("Batch", (), {"to_dict": lambda self: {"summary": summary, "results": [item.__dict__ for item in results]}})()

    def fetch_club_player_ids(self, club_id: str):
        return self.club_ids


def _auth_headers() -> dict[str, str]:
    return {"X-API-Key": "test-api-key"}


def test_sync_endpoints_require_api_key(client) -> None:
    response = client.post("/players/sync/123")
    assert response.status_code == 401


def test_sync_single_player_ok(client) -> None:
    app.dependency_overrides[get_player_sync_service] = lambda: DummyService()
    try:
        response = client.post("/players/sync/123", headers=_auth_headers())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == {"processed": 1, "ok": 1, "partial": 0, "error": 0}
    assert body["results"][0]["transfermarkt_id"] == "123"


def test_sync_batch_partial_success_200(client) -> None:
    app.dependency_overrides[get_player_sync_service] = lambda: DummyService()
    payload = {"transfermarkt_ids": ["7010", "bad", "7012"]}
    try:
        response = client.post("/players/sync", json=payload, headers=_auth_headers())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == {"processed": 3, "ok": 2, "partial": 0, "error": 1}


def test_sync_batch_respects_limit(client) -> None:
    app.dependency_overrides[get_player_sync_service] = lambda: DummyService()
    payload = {"transfermarkt_ids": ["1", "2", "3", "4"]}
    try:
        response = client.post("/players/sync", json=payload, headers=_auth_headers())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_sync_club_respects_limit(client) -> None:
    class ManyClubService(DummyService):
        def __init__(self):
            self.club_ids = ["1", "2", "3", "4"]

    app.dependency_overrides[get_player_sync_service] = lambda: ManyClubService()
    try:
        response = client.post("/clubs/10/players/sync", headers=_auth_headers())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_sync_club_summary(client) -> None:
    app.dependency_overrides[get_player_sync_service] = lambda: DummyService()
    try:
        response = client.post("/clubs/20/players/sync", headers=_auth_headers())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == {"processed": 2, "ok": 2, "partial": 0, "error": 0}
