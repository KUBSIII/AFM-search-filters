# AFM Search Filters

Internal FastAPI service for building a local read model of Transfermarkt players.

## Scope (M0-M4)

- FastAPI bootstrap with health endpoint
- SQLite persistence layer with SQLAlchemy 2.0
- Alembic migrations for `players` table
- Scraper + normalizer pipeline for Transfermarkt data
- Sync API (`POST /players/sync*`, `POST /clubs/{club_id}/players/sync`) secured with `X-API-Key`
- Query API (`GET /players`) with filters, sorting and pagination

## Quick Start (Docker - Recommended)

1. Create env file:

```powershell
Copy-Item .env.example .env
```

2. Build and run:

```powershell
docker compose up --build
```

3. Open:

- `http://127.0.0.1:8001/ui` (web console for filters + sync)
- `http://127.0.0.1:8001/docs`
- `http://127.0.0.1:8001/health`
- `http://127.0.0.1:8001/players`

Notes:

- Migrations run automatically on container start (`alembic upgrade head`).
- SQLite DB is persisted in Docker volume `afm_data` under `/app/data/afm_search.db`.

### Docker Useful Commands

```powershell
# Stop
docker compose down

# Stop + remove volume (hard reset DB)
docker compose down -v

# Rebuild image
docker compose build --no-cache
```

## Quick Start (Poetry - Local Fallback)

If you don't want Docker:

```powershell
Copy-Item .env.example .env
py -m poetry install
py -m poetry run alembic upgrade head
py -m poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Query API

`GET /players` is read-only and does not require auth.

Supported params:

- `name`
- `birth_date_from`, `birth_date_to`
- `club_apps_min`, `club_apps_max`
- `national_team_apps_min`, `national_team_apps_max`
- `position` (exact, case-insensitive)
- `contract_expires_before`, `contract_expires_after`
- `agent` (exact, case-insensitive)
- `limit` (`1..200`, default `50`)
- `offset` (`>=0`, default `0`)
- `sort_by` (`last_scraped_at`, `id`, `full_name`, `birth_date`, `club_apps`, `national_team_apps`, `contract_expires_at`)
- `sort_order` (`asc`, `desc`, default `desc`)

Response shape:

```json
{
  "items": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

## Sync API

All mutating sync endpoints require `X-API-Key` header.

- `POST /players/sync/{transfermarkt_id}`
- `POST /players/sync/search` (sync by player name)
- `POST /players/sync`
- `POST /clubs/{club_id}/players/sync`

Example:

```powershell
$headers = @{"X-API-Key"="change-me"}
$body = @{ transfermarkt_ids = @("1001", "1002") } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8001/players/sync -Headers $headers -Body $body -ContentType "application/json"
```

## Environment Variables

- `APP_ENV` - environment name
- `APP_HOST` - host (for local run)
- `APP_PORT` - port (for local run)
- `DB_URL` - SQLAlchemy DB URL
- `LOG_LEVEL` - logging level
- `SYNC_API_KEY` - API key for sync endpoints
- `TM_HTTP_TIMEOUT_S` - outbound request timeout
- `TM_MAX_RETRIES` - retry count for 429/5xx/transport errors
- `TM_BACKOFF_BASE_S` - retry backoff base seconds
- `TM_RATE_LIMIT_RPS` - outbound request rate limit
- `SYNC_MAX_BATCH` - max IDs in `POST /players/sync`
- `SYNC_MAX_CLUB_PLAYERS` - max roster size in club sync

## Tests

```powershell
py -m poetry run pytest
```

## Local Operational Checklist

- [ ] `.env` exists
- [ ] app starts (`docker compose up --build` or local Poetry run)
- [ ] `/health` returns 200
- [ ] `/players` returns `items + total + limit + offset`
- [ ] sync endpoints work with `X-API-Key`
- [ ] tests are green




