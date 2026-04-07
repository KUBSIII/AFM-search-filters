from pathlib import Path

from app.normalizers.player_normalizer import PlayerNormalizer
from app.scrapers.club_players_scraper import ClubPlayersScraper
from app.scrapers.http_client import TransfermarktHttpClient
from app.scrapers.player_profile_scraper import PlayerProfileScraper
from app.scrapers.player_search_scraper import PlayerSearchScraper
from app.scrapers.player_stats_scraper import PlayerStatsScraper


def _read_fixture(name: str) -> str:
    fixtures_dir = Path(__file__).parent / "fixtures"
    return (fixtures_dir / name).read_text(encoding="utf-8")


def test_parse_player_profile_complete() -> None:
    scraper = PlayerProfileScraper(http_client=TransfermarktHttpClient(5, 0, 0, 100))
    raw = scraper.parse_player_profile(
        _read_fixture("player_profile_complete.html"),
        transfermarkt_id="1001",
        profile_url="https://example.com/player/1001",
    )

    normalized = PlayerNormalizer().normalize_player(raw)

    assert raw["full_name"] == "Kylian Mbappe"
    assert normalized["sync_status"] == "ok"
    assert normalized["club_apps"] == 280
    assert normalized["national_team_apps"] == 78


def test_parse_player_profile_missing_fields_is_partial() -> None:
    scraper = PlayerProfileScraper(http_client=TransfermarktHttpClient(5, 0, 0, 100))
    raw = scraper.parse_player_profile(
        _read_fixture("player_profile_missing_fields.html"),
        transfermarkt_id="1002",
        profile_url="https://example.com/player/1002",
    )

    normalized = PlayerNormalizer().normalize_player(raw)

    assert normalized["sync_status"] == "partial"
    assert normalized["agent_name"] is None
    assert normalized["contract_expires_at"] is None


def test_parse_player_profile_changed_structure_is_supported() -> None:
    scraper = PlayerProfileScraper(http_client=TransfermarktHttpClient(5, 0, 0, 100))
    raw = scraper.parse_player_profile(
        _read_fixture("player_profile_changed_structure.html"),
        transfermarkt_id="1003",
        profile_url="https://example.com/player/1003",
    )

    normalized = PlayerNormalizer().normalize_player(raw)

    assert raw["full_name"] == "Resilient Player"
    assert normalized["position"] == "Right-Back"
    assert normalized["club_apps"] == 44


def test_parse_player_profile_info_table_structure_is_supported() -> None:
    scraper = PlayerProfileScraper(http_client=TransfermarktHttpClient(5, 0, 0, 100))
    raw = scraper.parse_player_profile(
        _read_fixture("player_profile_info_table.html"),
        transfermarkt_id="28003",
        profile_url="https://example.com/player/28003",
    )

    normalized = PlayerNormalizer().normalize_player(raw)

    assert normalized["birth_date"] is not None
    assert normalized["position"] == "Attack - Right Winger"
    assert normalized["club_name"] == "Inter Miami CF"
    assert normalized["agent_name"] == "Relatives"
    assert normalized["contract_expires_at"] is not None
    assert normalized["national_team_apps"] == 198


def test_parse_club_players_list() -> None:
    scraper = ClubPlayersScraper(http_client=TransfermarktHttpClient(5, 0, 0, 100))
    ids = scraper.parse_club_player_ids(_read_fixture("club_players_list.html"))
    assert ids == ["1001", "1002"]


def test_parse_player_search_results() -> None:
    scraper = PlayerSearchScraper(http_client=TransfermarktHttpClient(5, 0, 0, 100))
    ids = scraper.parse_player_ids_from_search(_read_fixture("player_search_results.html"), limit=2)

    assert ids == ["28003", "68290"]


def test_parse_stats_by_club_extracts_total_from_tfoot() -> None:
    scraper = PlayerStatsScraper(http_client=TransfermarktHttpClient(5, 0, 0, 100))
    club_apps = scraper.parse_club_apps(_read_fixture("player_stats_by_club.html"))

    assert club_apps == 478


def test_parse_stats_by_club_sums_tbody_when_no_tfoot() -> None:
    scraper = PlayerStatsScraper(http_client=TransfermarktHttpClient(5, 0, 0, 100))
    club_apps = scraper.parse_club_apps(_read_fixture("player_stats_no_footer.html"))

    assert club_apps == 144


def test_parse_stats_by_club_returns_none_for_empty_html() -> None:
    scraper = PlayerStatsScraper(http_client=TransfermarktHttpClient(5, 0, 0, 100))
    club_apps = scraper.parse_club_apps("<html><body></body></html>")

    assert club_apps is None

