# Ścieżka Developmentu do Gotowego Produktu

## Cel

Dowiezienie działającego narzędzia `AFM-search-filters`:

- synchronizacja danych zawodników z Transfermarkt do lokalnej bazy,
- filtrowanie/sortowanie/paginacja po lokalnym read modelu,
- prosty interfejs użytkownika (REST + opcjonalny panel HTML),
- stabilne działanie i przewidywalny proces odświeżania danych.

## Zakres Produktu (MVP)

MVP jest gotowe, jeśli spełnione są wszystkie warunki:

- można zsynchronizować 1 zawodnika i listę zawodników klubu,
- `GET /players` obsługuje wszystkie uzgodnione filtry,
- dane są trzymane w SQLite i nie ma live scrapingu na endpointach query,
- są testy parserów i testy integracyjne filtrów,
- endpointy sync są minimalnie zabezpieczone (`localhost` lub `X-API-Key`),
- projekt ma migracje (`Alembic`) i instrukcję uruchomienia.

---

## Plan Etapowy (z datami)

Data startu planu: **2026-04-06**.

### M0: Foundation (2026-04-06 -> 2026-04-08)

Deliverables:

- struktura projektu zgodna z architekturą,
- `pyproject.toml` i zależności,
- konfiguracja środowisk (`.env.example`),
- logging, podstawowa obsługa konfiguracji aplikacji,
- setup Alembic (`initial migration`).

Definition of Done:

- aplikacja startuje lokalnie jednym poleceniem,
- migracja tworzy bazę bez ręcznej ingerencji,
- README ma sekcję „Quick Start”.

### M1: Model danych + persystencja (2026-04-09 -> 2026-04-11)

Deliverables:

- model `players` z polami architektonicznymi,
- indeksy i unikalność `transfermarkt_id`,
- repozytorium do `upsert`, wyszukiwania i paginacji.

Definition of Done:

- migracje przechodzą czysto na pustej bazie,
- testy repozytorium przechodzą lokalnie.

### M2: Scraper + normalizer zawodnika (2026-04-12 -> 2026-04-15)

Deliverables:

- scraper profilu zawodnika,
- normalizer do stabilnego DTO,
- obsługa braków danych i błędów parsera,
- timeout/retry/backoff/rate limit.

Definition of Done:

- parser działa na fixture HTML,
- awaria scrapingu nie wywraca procesu (status `partial/error`).

### M3: Sync API (2026-04-16 -> 2026-04-18)

Deliverables:

- `POST /players/sync/{transfermarkt_id}`,
- `POST /clubs/{club_id}/players/sync`,
- `POST /players/sync` (batch),
- statusy sync (`ok`, `partial`, `error`) i metadane czasu.

Definition of Done:

- endpointy zwracają spójne odpowiedzi i kody HTTP,
- endpointy sync są zabezpieczone.

### M4: Query API (2026-04-19 -> 2026-04-22)

Deliverables:

- `GET /players` z filtrami:
  - `name`, zakresy dat, zakresy występów, `position`, `agent`,
  - `contract_expires_before/after`, paginacja i sortowanie,
- whitelist `sort_by`, stabilne sortowanie (`id` jako tie-break).

Definition of Done:

- testy integracyjne endpointu query przechodzą,
- brak zapytań do zewnętrznego źródła podczas query.

### M5: UI i ergonomia użycia (2026-04-23 -> 2026-04-25)

Deliverables:

- wersja minimalna: Swagger + wygodne przykłady requestów,
- opcjonalnie: prosty panel HTML (Jinja2/HTMX) do filtrów i tabeli.

Definition of Done:

- użytkownik nietechniczny wykona najczęstszy flow bez użycia curl.

### M6: Stabilizacja i release MVP (2026-04-26 -> 2026-04-30)

Deliverables:

- testy E2E głównych ścieżek,
- hardening błędów i logowania,
- eksport CSV,
- checklista release + wersja `v0.1.0`.

Definition of Done:

- pełny green na testach lokalnych,
- README zawiera troubleshooting i operacje maintenance,
- projekt gotowy do codziennego użycia.

---

## Backlog Techniczny (priorytety)

## P0 (must-have)

- SQLAlchemy 2.0 + Alembic,
- scraper i normalizer profilu zawodnika,
- sync endpointy,
- query endpoint z pełnym filtrowaniem,
- testy parserów + integracyjne query,
- minimalne security endpointów mutujących.

## P1 (should-have)

- panel HTML (Jinja2/HTMX),
- eksport CSV,
- incremental refresh (`next_refresh_at`),
- metryki techniczne (czas sync, liczba błędów).

## P2 (nice-to-have)

- cache per klub,
- lepsze raporty jakości danych,
- harmonogram automatycznego refreshu.

---

## Kryteria Jakości

## Testy

- parser fixture tests,
- integration tests (`sync`, `query`),
- smoke test startu aplikacji.

## Niezawodność

- retry/backoff na 429/5xx,
- odporność na brakujące pola,
- logi z kontekstem (`transfermarkt_id`, URL, typ błędu).

## Bezpieczeństwo

- blokada endpointów sync (localhost/API key),
- walidacja wszystkich wejść przez Pydantic,
- brak dynamicznego sortowania bez whitelisty.

---

## Standard pracy (żeby dowieźć bez chaosu)

Branching:

- `main` stabilna,
- feature branch per etap (`feature/m2-player-scraper` itd.),
- PR na każdy etap.

Definition of Ready dla taska:

- opis celu,
- kryteria akceptacji,
- lista plików/modułów do zmiany.

Definition of Done dla taska:

- kod + testy + migracje (jeśli dotyczy),
- aktualizacja dokumentacji,
- ręczna weryfikacja flow.

---

## Go-Live Checklist (MVP)

- `alembic upgrade head` działa na czystym środowisku,
- `POST /players/sync/{id}` działa i zapisuje dane,
- `POST /clubs/{club_id}/players/sync` działa dla przykładowego klubu,
- `GET /players` działa z filtrami i paginacją,
- endpointy mutujące są zabezpieczone,
- istnieje instrukcja backupu pliku SQLite,
- release tag `v0.1.0` utworzony.

---

## Co dalej po MVP

- harmonogram odświeżania danych (cron/APScheduler),
- rozszerzenie modelu o historię transferów i wartość rynkową,
- dashboard jakości danych i monitor błędów parsera.
