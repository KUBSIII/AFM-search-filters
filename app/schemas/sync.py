from enum import Enum

from pydantic import BaseModel, Field


class SyncStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    ERROR = "error"


class SyncItemResponse(BaseModel):
    transfermarkt_id: str
    status: SyncStatus
    message: str | None = None
    player_id: int | None = None


class SyncSummaryResponse(BaseModel):
    processed: int
    ok: int
    partial: int
    error: int


class SyncBatchResponse(BaseModel):
    summary: SyncSummaryResponse
    results: list[SyncItemResponse]


class BatchSyncRequest(BaseModel):
    transfermarkt_ids: list[str] = Field(min_length=1)


class SearchSyncRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    limit: int = Field(default=5, ge=1, le=20)
