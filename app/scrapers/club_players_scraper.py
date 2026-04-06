import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, FeatureNotFound

from app.scrapers.exceptions import TransfermarktParseError
from app.scrapers.http_client import TransfermarktHttpClient

PLAYER_ID_PATTERN = re.compile(r"/(?:profil/)?spieler/(\d+)")


class ClubPlayersScraper:
    def __init__(self, http_client: TransfermarktHttpClient, base_url: str = "https://www.transfermarkt.com"):
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")

    def fetch_club_player_ids(self, club_id: str) -> list[str]:
        url = f"{self.base_url}/club/kader/verein/{club_id}"
        html = self.http_client.get_text(url)
        return self.parse_club_player_ids(html)

    def parse_club_player_ids(self, html: str) -> list[str]:
        soup = self._build_soup(html)
        ids: list[str] = []
        seen: set[str] = set()

        for link in soup.select("a[href]"):
            href = link.get("href", "")
            match = PLAYER_ID_PATTERN.search(href)
            if not match:
                continue
            player_id = match.group(1)
            if player_id in seen:
                continue
            seen.add(player_id)
            ids.append(player_id)

        if not ids:
            raise TransfermarktParseError("No player ids found on club page")

        return ids

    def build_player_profile_url(self, transfermarkt_id: str) -> str:
        return urljoin(self.base_url + "/", f"player/profil/spieler/{transfermarkt_id}")

    @staticmethod
    def _build_soup(html: str) -> BeautifulSoup:
        try:
            return BeautifulSoup(html, "lxml")
        except FeatureNotFound:
            return BeautifulSoup(html, "html.parser")
