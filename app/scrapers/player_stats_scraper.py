import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, FeatureNotFound

from app.scrapers.http_client import TransfermarktHttpClient


class PlayerStatsScraper:
    """Scrapes the 'Stats by club' page to extract total club appearances."""

    def __init__(self, http_client: TransfermarktHttpClient, base_url: str = "https://www.transfermarkt.com"):
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")

    def fetch_club_apps(self, transfermarkt_id: str) -> int | None:
        url = self._build_stats_url(transfermarkt_id)
        html = self.http_client.get_text(url)
        return self.parse_club_apps(html)

    def parse_club_apps(self, html: str) -> int | None:
        soup = self._build_soup(html)

        # Strategy 1: Read the total from the <tfoot> row.
        total = self._extract_from_tfoot(soup)
        if total is not None:
            return total

        # Strategy 2: Sum individual club appearance rows from <tbody>.
        total = self._sum_from_tbody(soup)
        if total is not None:
            return total

        return None

    def _build_stats_url(self, transfermarkt_id: str) -> str:
        return urljoin(
            self.base_url + "/",
            f"player/leistungsdatenverein/spieler/{transfermarkt_id}",
        )

    @staticmethod
    def _build_soup(html: str) -> BeautifulSoup:
        try:
            return BeautifulSoup(html, "lxml")
        except FeatureNotFound:
            return BeautifulSoup(html, "html.parser")

    @classmethod
    def _extract_from_tfoot(cls, soup: BeautifulSoup) -> int | None:
        """Extract total appearances from the tfoot summary row."""
        for table in soup.select("table.items"):
            tfoot = table.find("tfoot")
            if not tfoot:
                continue

            for row in tfoot.find_all("tr"):
                cells = row.find_all("td")
                if not cells:
                    continue

                # The first cell usually contains "Total :" label.
                first_text = cells[0].get_text(strip=True).lower()
                if "total" not in first_text:
                    continue

                # The appearances count is in the first td.zentriert after the label.
                for cell in cells[1:]:
                    if "zentriert" in (cell.get("class") or []):
                        value = cls._parse_int_from_text(cell.get_text(strip=True))
                        if value is not None:
                            return value

        return None

    @classmethod
    def _sum_from_tbody(cls, soup: BeautifulSoup) -> int | None:
        """Fallback: sum appearance values from individual club rows."""
        total = 0
        found_any = False

        for table in soup.select("table.items"):
            tbody = table.find("tbody")
            if not tbody:
                continue

            for row in tbody.find_all("tr"):
                zentriert_cells = row.select("td.zentriert")
                if len(zentriert_cells) < 2:
                    continue

                # The first td.zentriert is usually the club logo,
                # the second td.zentriert contains the appearances link.
                apps_cell = zentriert_cells[1]
                value = cls._parse_int_from_text(apps_cell.get_text(strip=True))
                if value is not None:
                    total += value
                    found_any = True

            # Only process the first table.items (stats by club).
            if found_any:
                break

        return total if found_any else None

    @staticmethod
    def _parse_int_from_text(text: str) -> int | None:
        digits = re.sub(r"\D", "", text)
        if not digits:
            return None
        return int(digits)
