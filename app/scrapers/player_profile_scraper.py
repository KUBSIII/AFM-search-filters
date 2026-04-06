import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, FeatureNotFound

from app.scrapers.exceptions import TransfermarktParseError
from app.scrapers.http_client import TransfermarktHttpClient
from app.scrapers.selectors import PLAYER_NAME_SELECTORS, PROFILE_LABEL_ALIASES


class PlayerProfileScraper:
    def __init__(self, http_client: TransfermarktHttpClient, base_url: str = "https://www.transfermarkt.com"):
        self.http_client = http_client
        self.base_url = base_url.rstrip("/")

    def fetch_player_profile(self, transfermarkt_id: str) -> dict[str, str | None]:
        profile_url = self._build_profile_url(transfermarkt_id)
        html = self.http_client.get_text(profile_url)
        return self.parse_player_profile(html, transfermarkt_id=transfermarkt_id, profile_url=profile_url)

    def parse_player_profile(
        self,
        html: str,
        *,
        transfermarkt_id: str,
        profile_url: str,
    ) -> dict[str, str | None]:
        soup = self._build_soup(html)
        labels = self._extract_labeled_values(soup)

        full_name = self._extract_full_name(soup)
        if not full_name:
            full_name = f"Unknown-{transfermarkt_id}"

        payload: dict[str, str | None] = {
            "transfermarkt_id": transfermarkt_id,
            "profile_url": profile_url,
            "full_name": full_name,
        }

        for field, aliases in PROFILE_LABEL_ALIASES.items():
            payload[field] = self._find_label_value(labels, aliases)

        payload["raw_payload"] = json.dumps(labels, ensure_ascii=False)
        payload["raw_html"] = html

        if not payload["full_name"]:
            raise TransfermarktParseError("Unable to parse player name")

        return payload

    def _build_profile_url(self, transfermarkt_id: str) -> str:
        return urljoin(self.base_url + "/", f"player/profil/spieler/{transfermarkt_id}")

    @staticmethod
    def _build_soup(html: str) -> BeautifulSoup:
        try:
            return BeautifulSoup(html, "lxml")
        except FeatureNotFound:
            return BeautifulSoup(html, "html.parser")

    @staticmethod
    def _extract_full_name(soup: BeautifulSoup) -> str | None:
        for selector in PLAYER_NAME_SELECTORS:
            node = soup.select_one(selector)
            if not node:
                continue
            if node.name == "meta":
                content = node.get("content")
                if content:
                    return content.strip()
                continue
            text = node.get_text(" ", strip=True)
            if text:
                return text
        return None

    @classmethod
    def _extract_labeled_values(cls, soup: BeautifulSoup) -> dict[str, str]:
        values: dict[str, str] = {}

        # Classic table format.
        for row in soup.select("table tr"):
            header = row.find("th")
            value = row.find("td")
            if header and value:
                key = cls._normalize_key(header.get_text(" ", strip=True))
                val = value.get_text(" ", strip=True)
                if key and val:
                    values[key] = val

        # Definition list format.
        for dt in soup.select("dt"):
            dd = dt.find_next_sibling("dd")
            if not dd:
                continue
            key = cls._normalize_key(dt.get_text(" ", strip=True))
            val = dd.get_text(" ", strip=True)
            if key and val and key not in values:
                values[key] = val

        # Legacy list format with explicit label/value classes.
        for item in soup.select("li"):
            label = item.select_one(".label")
            value = item.select_one(".value")
            if not label or not value:
                continue
            key = cls._normalize_key(label.get_text(" ", strip=True))
            val = value.get_text(" ", strip=True)
            if key and val and key not in values:
                values[key] = val

        # Transfermarkt data-header format.
        for item in soup.select("li.data-header__label"):
            content = item.select_one(".data-header__content")
            if not content:
                continue
            key_parts = [frag.strip() for frag in item.find_all(string=True, recursive=False) if frag.strip()]
            key = cls._normalize_key(" ".join(key_parts))
            val = content.get_text(" ", strip=True)
            if key and val and key not in values:
                values[key] = val

        # Transfermarkt info-table format: alternating label/value spans.
        info_nodes = soup.select(".info-table .info-table__content")
        if len(info_nodes) >= 2:
            for i in range(0, len(info_nodes) - 1, 2):
                key = cls._normalize_key(info_nodes[i].get_text(" ", strip=True))
                val = info_nodes[i + 1].get_text(" ", strip=True)
                if key and val and key not in values:
                    values[key] = val

        return values

    @staticmethod
    def _normalize_key(raw_key: str) -> str:
        key = raw_key.strip().lower()
        key = key.split(":", 1)[0].strip()
        key = re.sub(r"\s+", " ", key)
        key = key.strip("/ ")
        return key

    @staticmethod
    def _find_label_value(labels: dict[str, str], aliases: list[str]) -> str | None:
        for alias in aliases:
            key = alias.strip().lower()
            if key in labels:
                return labels[key]
        return None
