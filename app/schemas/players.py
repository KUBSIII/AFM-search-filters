from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


SortBy = Literal[
    "last_scraped_at",
    "id",
    "full_name",
    "birth_date",
    "club_apps",
    "national_team_apps",
    "contract_expires_at",
]

SortOrder = Literal["asc", "desc"]


class PlayerQueryParams(BaseModel):
    name: str | None = None
    birth_date_from: date | None = None
    birth_date_to: date | None = None
    club_apps_min: int | None = None
    club_apps_max: int | None = None
    national_team_apps_min: int | None = None
    national_team_apps_max: int | None = None
    position: str | None = None
    contract_expires_before: date | None = None
    contract_expires_after: date | None = None
    agent: str | None = None

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    sort_by: SortBy = "last_scraped_at"
    sort_order: SortOrder = "desc"

    @model_validator(mode="after")
    def validate_ranges(self) -> "PlayerQueryParams":
        if self.birth_date_from and self.birth_date_to and self.birth_date_from > self.birth_date_to:
            raise ValueError("birth_date_from must be <= birth_date_to")

        if self.club_apps_min is not None and self.club_apps_max is not None and self.club_apps_min > self.club_apps_max:
            raise ValueError("club_apps_min must be <= club_apps_max")

        if (
            self.national_team_apps_min is not None
            and self.national_team_apps_max is not None
            and self.national_team_apps_min > self.national_team_apps_max
        ):
            raise ValueError("national_team_apps_min must be <= national_team_apps_max")

        if (
            self.contract_expires_after
            and self.contract_expires_before
            and self.contract_expires_after > self.contract_expires_before
        ):
            raise ValueError("contract_expires_after must be <= contract_expires_before")

        return self


class PlayerListItem(BaseModel):
    id: int
    transfermarkt_id: str
    full_name: str
    birth_date: date | None
    position: str | None
    club_name: str | None
    club_apps: int | None
    national_team_apps: int | None
    contract_expires_at: date | None
    agent_name: str | None
    profile_url: str
    last_scraped_at: datetime
    sync_status: str
    sync_error: str | None
    last_success_at: datetime | None
    next_refresh_at: datetime | None
    source_hash: str | None


class PlayersQueryResponse(BaseModel):
    items: list[PlayerListItem]
    total: int
    limit: int
    offset: int
