# AFM Search Filters

Internal FastAPI service for building a local read model of Transfermarkt players.

## Scope (M0-M3)

- FastAPI bootstrap with health endpoint
- SQLite persistence layer with SQLAlchemy 2.0
- Alembic migrations for `players` table
- Player repository contract (`upsert`, `get`, `list`, `count`)
- Transfermarkt scraping layer (profile + club roster IDs)
- Player normalizer (`ok` / `partial` / `error` metadata)
- Sync API endpoints secured with `X-API-Key`
- Test suite for health, migrations, repository, scraper, service and sync API

## Requirements

- Python 3.11+
- Poetry 1.8+

## Quick Start (PowerShell)

1. Create environment file:

```powershell
Copy-Item .env.example .env
```

2. Install dependencies:

```powershell
poetry install
```

3. Run migrations:

```powershell
poetry run alembic upgrade head
```

4. Start API:

```powershell
poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

5. Verify health endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Sync API

All mutating sync endpoints require header `X-API-Key`.

- `POST /players/sync/{transfermarkt_id}`
- `POST /players/sync`
- `POST /clubs/{club_id}/players/sync`

Example batch request:

```powershell
$headers = @{"X-API-Key"="change-me"}
$body = @{ transfermarkt_ids = @("1001", "1002") } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/players/sync -Headers $headers -Body $body -ContentType "application/json"
```

## Environment Variables

- `APP_ENV` - application environment label (default: `development`)
- `APP_HOST` - host for local server (default: `127.0.0.1`)
- `APP_PORT` - port for local server (default: `8000`)
- `DB_URL` - SQLAlchemy DB URL (default: `sqlite+pysqlite:///./afm_search.db`)
- `LOG_LEVEL` - logging level (default: `INFO`)
- `SYNC_API_KEY` - required API key for sync endpoints
- `TM_HTTP_TIMEOUT_S` - timeout for outbound Transfermarkt requests
- `TM_MAX_RETRIES` - retry count for 429/5xx and transport errors
- `TM_BACKOFF_BASE_S` - exponential backoff base in seconds
- `TM_RATE_LIMIT_RPS` - request rate limit per second
- `SYNC_MAX_BATCH` - max IDs in `POST /players/sync`
- `SYNC_MAX_CLUB_PLAYERS` - max roster size accepted in club sync

## Database Operations (PowerShell)

Initialize DB schema:

```powershell
poetry run alembic upgrade head
```

Show migration history:

```powershell
poetry run alembic history
```

Reset local DB (destructive):

```powershell
Remove-Item .\afm_search.db -ErrorAction SilentlyContinue
poetry run alembic upgrade head
```

## Tests

Run all tests:

```powershell
poetry run pytest
```

## Local Operational Checklist

- [ ] `.env` created from `.env.example`
- [ ] dependencies installed with Poetry
- [ ] migration applied (`alembic upgrade head`)
- [ ] `/health` returns 200
- [ ] sync endpoints respond with `X-API-Key`
- [ ] tests are green (`pytest`)

## SQLite Backup (PowerShell)

Create backup:

```powershell
New-Item -ItemType Directory -Path .\backups -Force | Out-Null
Copy-Item .\afm_search.db (".\backups\afm_search_{0}.db" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
```

Restore backup:

```powershell
Copy-Item .\backups\<backup_name>.db .\afm_search.db
```

## Next Sprint Entry (M4)

- `GET /players` query API with filters/sort/pagination only from SQLite
- integration tests for query behavior and deterministic sorting
