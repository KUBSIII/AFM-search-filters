# AFM Search Filters

Internal FastAPI service for building a local read model of Transfermarkt players.

## Scope of v1

- FastAPI bootstrap with health endpoint
- SQLite persistence layer with SQLAlchemy 2.0
- Alembic migrations for `players` table
- Player repository contract (`upsert`, `get`, `list`, `count`)
- Test suite for health check, migrations, and repository behavior

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

## Environment Variables

- `APP_ENV` - application environment label (default: `development`)
- `APP_HOST` - host for local server (default: `127.0.0.1`)
- `APP_PORT` - port for local server (default: `8000`)
- `DB_URL` - SQLAlchemy DB URL (default: `sqlite+pysqlite:///./afm_search.db`)
- `LOG_LEVEL` - logging level (default: `INFO`)

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

## Next Sprint Entry (v2)

- Scraper layer (`player_profile_scraper`, `club_players_scraper`)
- Normalizer layer for stable DTOs
- Sync endpoints (`POST /players/sync/{id}`, `POST /clubs/{club_id}/players/sync`)
