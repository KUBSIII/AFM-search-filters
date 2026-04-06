import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup, FeatureNotFound

from app.scrapers.http_client import TransfermarktHttpClient

PLAYER_ID_PATTERN = re.compile(r"/(?:[^/]+/)?profil/spieler/(\d+)")


class PlayerSearchScraper:
    def __init__(self, http_client: TransfermarktHttpClient, base_url: str = "https://www.transfermarkt.com"):
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")

    def fetch_player_ids_by_name(self, name: str, limit: int = 5) -> list[str]:
        query = name.strip()
        if not query:
            raise ValueError("name must not be empty")

        url = f"{self.base_url}/schnellsuche/ergebnis/schnellsuche?query={quote_plus(query)}"
        html = self.http_client.get_text(url)
        return self.parse_player_ids_from_search(html, limit=limit)

    def parse_player_ids_from_search(self, html: str, limit: int = 5) -> list[str]:
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

            if len(ids) >= max(1, limit):
                break

        return ids

    @staticmethod
    def _build_soup(html: str) -> BeautifulSoup:
        try:
            return BeautifulSoup(html, "lxml")
        except FeatureNotFound:
            return BeautifulSoup(html, "html.parser")
