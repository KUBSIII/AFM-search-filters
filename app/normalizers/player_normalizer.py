import hashlib
import json
from datetime import date, datetime, timezone
import re


class PlayerNormalizer:
    def normalize_player(self, raw: dict[str, str | None]) -> dict[str, object]:
        issues: list[str] = []

        transfermarkt_id = str(raw.get("transfermarkt_id") or "").strip()
        full_name = str(raw.get("full_name") or "").strip() or f"Unknown-{transfermarkt_id}"
        profile_url = str(raw.get("profile_url") or "").strip() or f"https://www.transfermarkt.com/player/profil/spieler/{transfermarkt_id}"

        birth_date = self._parse_date(raw.get("birth_date"), "birth_date", issues)
        contract_expires_at = self._parse_date(raw.get("contract_expires_at"), "contract_expires_at", issues)

        club_apps = self._parse_int(raw.get("club_apps"), "club_apps", issues)
        national_team_apps = self._parse_int(raw.get("national_team_apps"), "national_team_apps", issues)

        position = self._normalize_text(raw.get("position"))
        club_name = self._normalize_text(raw.get("club_name"))
        agent_name = self._normalize_text(raw.get("agent_name"))

        required_maybe_missing = {
            "birth_date": birth_date,
            "position": position,
            "contract_expires_at": contract_expires_at,
            "agent_name": agent_name,
            "club_apps": club_apps,
            "national_team_apps": national_team_apps,
        }
        missing_fields = [name for name, value in required_maybe_missing.items() if value is None]

        status = "ok"
        if issues or missing_fields:
            status = "partial"

        issue_parts = issues[:]
        if missing_fields:
            issue_parts.append("missing:" + ",".join(missing_fields))

        last_scraped_at = datetime.now(timezone.utc)
        source_hash = hashlib.sha256(self._json_bytes(raw)).hexdigest()

        return {
            "transfermarkt_id": transfermarkt_id,
            "full_name": full_name,
            "birth_date": birth_date,
            "position": position,
            "club_name": club_name,
            "club_apps": club_apps,
            "national_team_apps": national_team_apps,
            "contract_expires_at": contract_expires_at,
            "agent_name": agent_name,
            "profile_url": profile_url,
            "last_scraped_at": last_scraped_at,
            "sync_status": status,
            "sync_error": "; ".join(issue_parts) if issue_parts else None,
            "last_success_at": last_scraped_at,
            "next_refresh_at": None,
            "source_hash": source_hash,
            "raw_payload_json": json.dumps(raw, ensure_ascii=False, sort_keys=True),
        }

    @staticmethod
    def _normalize_text(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @staticmethod
    def _parse_int(value: str | None, field_name: str, issues: list[str]) -> int | None:
        if value is None or not value.strip():
            return None

        digits = re.sub(r"[^0-9]", "", value)
        if not digits:
            issues.append(f"invalid_int:{field_name}")
            return None

        return int(digits)

    @staticmethod
    def _parse_date(value: str | None, field_name: str, issues: list[str]) -> date | None:
        if value is None:
            return None

        cleaned = value.strip()
        if not cleaned:
            return None

        for date_format in (
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d/%m/%Y",
            "%d %b %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%B %d, %Y",
        ):
            try:
                return datetime.strptime(cleaned, date_format).date()
            except ValueError:
                continue

        issues.append(f"invalid_date:{field_name}")
        return None

    @staticmethod
    def _json_bytes(raw: dict[str, str | None]) -> bytes:
        return json.dumps(raw, ensure_ascii=False, sort_keys=True).encode("utf-8")
