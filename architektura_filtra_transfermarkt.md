# Architektura filtra zawodników dla `transfermarkt-api`

## Repo referencyjne

Bazujemy na API: <https://github.com/felipeall/transfermarkt-api>

## Cel

Chcemy zbudować prosty filtr zawodników oparty o dane:

- imię i nazwisko,
- data urodzenia,
- liczba występów w klubie,
- liczba występów w kadrze,
- pozycja,
- data wygaśnięcia kontraktu,
- agent.

Założenia:

- projekt będzie używany wewnętrznie,
- to narzędzie **single-user / private-use**,
- nie planujemy publicznego deploymentu,
- bazujemy na repo: `felipeall/transfermarkt-api`.

---

## Werdykt architektoniczny

**Nie przepisywałbym tego na inny stack.**

Najrozsądniejsze rozwiązanie:

- **Python 3.11+**
- **FastAPI**
- **Pydantic v2**
- **SQLAlchemy 2.0 + Alembic**
- **SQLite**
- `httpx`
- `BeautifulSoup + lxml`
- `pytest`
- `Poetry`

To repo już jest osadzone w Pythonie/FastAPI, więc najlepsza decyzja to **ewolucja obecnego projektu**, a nie zmiana technologii.

---

## Najważniejsza decyzja

### Nie filtrować danych "na żywo" po scrapingu

To byłby błąd projektowy.

Dla takich pól jak:

- kontrakt,
- agent,
- występy klubowe,
- występy reprezentacyjne,
- pozycja,
- data urodzenia,

nie należy odpalać scrapingu przy każdym zapytaniu użytkownika.

### Dlaczego

Bo scraping:

- jest wolny,
- jest kruchy,
- zależy od HTML,
- może wymagać wejścia w profil zawodnika,
- utrudnia stabilne filtrowanie i sortowanie.

### Poprawne podejście

Budujemy **lokalny cache / read model** w bazie danych i:

- scraping służy do **zasilania bazy**,
- filtrowanie działa **wyłącznie po bazie**.

To powinien być prosty lokalny monolit z podziałem na warstwy.

---

## Zalecana architektura

### 1. Warstwa pobierania danych (`scrapers`)

Ta warstwa zna Transfermarkt i HTML.

Przykładowe moduły:

```text
scrapers/
  player_search_scraper.py
  player_profile_scraper.py
  club_players_scraper.py
```

Odpowiedzialność:

- wyszukanie zawodnika,
- pobranie listy zawodników klubu,
- wejście w profil zawodnika,
- zebranie surowych danych z HTML.

Ta warstwa powinna zwracać **surowe DTO**, bez logiki biznesowej.

Wymagania techniczne warstwy scrapingu:

- `timeout` na każde żądanie,
- retry z backoff (np. 429/5xx),
- prosty rate limit per host,
- spójny `User-Agent`,
- czytelne logowanie błędów HTTP/parsingu.

---

### 2. Warstwa normalizacji (`normalizers`)

Ta warstwa zamienia chaos z HTML na spójny model danych.

Przykład:

```text
normalizers/
  player_normalizer.py
```

Odpowiedzialność:

- parsowanie dat,
- parsowanie liczb,
- normalizacja pozycji,
- ujednolicanie nazw pól,
- obsługa braków danych,
- przygotowanie formatu gotowego do zapisu w bazie.

Przykładowe pola po normalizacji:

- `full_name`
- `birth_date`
- `position`
- `club_apps`
- `national_team_apps`
- `contract_expires_at`
- `agent_name`
- `profile_url`
- `last_scraped_at`

To bardzo ważna warstwa, bo scraper będzie psuł się częściej niż reszta systemu.

---

### 3. Warstwa persystencji (`db`, `repositories`)

Dla tego projektu **SQLite w zupełności wystarczy**.

Nie ma sensu zaczynać od Postgresa, bo:

- system jest single-user,
- nie ma wymagań HA,
- nie ma potrzeby stawiania infrastruktury,
- lokalne filtrowanie będzie szybkie.

Dodatkowo:

- włącz `WAL` (`PRAGMA journal_mode=WAL`),
- ustaw `busy_timeout`,
- prowadź migracje przez **Alembic** od początku.

#### Proponowana tabela `players`

- `id`
- `transfermarkt_id` (unique)
- `full_name`
- `birth_date` (nullable)
- `position` (nullable)
- `club_name` (nullable)
- `club_apps` (nullable)
- `national_team_apps` (nullable)
- `contract_expires_at` (nullable)
- `agent_name` (nullable)
- `profile_url`
- `last_scraped_at`
- `sync_status` (`ok` / `partial` / `error`)
- `sync_error` (nullable)
- `last_success_at` (nullable)
- `next_refresh_at` (nullable)
- `source_hash` (nullable)
- `raw_payload_json` (opcjonalnie)

#### Indeksy

- `transfermarkt_id` — unique
- `full_name`
- `birth_date`
- `position`
- `contract_expires_at`
- `agent_name`
- `last_scraped_at`
- `next_refresh_at`

`raw_payload_json` warto zachować pomocniczo do debugowania parsera.

---

### 4. Warstwa aplikacyjna (`services`)

Tutaj jest logika biznesowa.

Przykładowe serwisy:

```text
services/
  player_sync_service.py
  player_query_service.py
```

#### `player_sync_service`

Odpowiada za:

- pobranie danych zawodnika,
- normalizację,
- zapis lub update w bazie,
- sync pojedynczego zawodnika,
- sync zawodników klubu,
- batch refresh,
- oznaczanie statusu syncu i błędów.

#### `player_query_service`

Odpowiada za:

- budowanie filtrów,
- sortowanie,
- paginację,
- odczyt z bazy.

Ważne: **query service nie powinien znać HTML ani scrapingu**.

Dodatkowo:

- whitelist dla `sort_by`,
- bezpieczne domyślne sortowanie,
- deterministyczny tie-break (np. po `id`).

---

### 5. Warstwa HTTP (`api/routes`)

Warstwa HTTP ma być cienka.

Przykładowa struktura:

```text
api/
  routes/
    players.py
    sync.py
```

#### Endpointy techniczne

```http
POST /players/sync/{transfermarkt_id}
POST /clubs/{club_id}/players/sync
POST /players/sync
```

Cel:

- odświeżanie lokalnego cache,
- batch import,
- ręczny refresh danych.

Minimalne zabezpieczenia endpointów sync:

- dostęp tylko z localhost albo
- prosty `X-API-Key`.

#### Główny endpoint filtrowania

```http
GET /players
```

Parametry przykładowe:

- `name`
- `birth_date_from`
- `birth_date_to`
- `club_apps_min`
- `club_apps_max`
- `national_team_apps_min`
- `national_team_apps_max`
- `position`
- `contract_expires_before`
- `contract_expires_after`
- `agent`
- `limit`
- `offset`
- `sort_by`
- `sort_order`

Ten endpoint powinien działać **tylko po SQLite**, bez live scrapingu.

---

## UI / sposób użycia

Masz trzy rozsądne opcje.

### Opcja 1 — samo REST + Swagger

Najmniej pracy. Wystarczające, jeśli użytkownik jest techniczny.

### Opcja 2 — prosty HTML w FastAPI (Jinja2 / HTMX)

To najlepszy kompromis, jeśli chcesz wygodne narzędzie bez ciężkiego frontendu.

Daje:

- formularz filtrów,
- tabelę wyników,
- szybkie wdrożenie,
- mały koszt utrzymania,
- brak potrzeby budowania SPA.

### Opcja 3 — Streamlit

Da się, ale mieszałbym to dopiero wtedy, jeśli chcesz bardzo szybko zbudować osobne wewnętrzne UI. Jeśli rozwijacie repo jako API, lepiej trzymać UI blisko FastAPI albo zostać przy samym REST.

### Rekomendacja

- **na start:** samo REST,
- **jeśli chcesz wygodę:** FastAPI + Jinja2/HTMX.

---

## Proponowana struktura projektu

```text
app/
  api/
    routes/
      players.py
      sync.py
  schemas/
    player.py
    filters.py
  services/
    player_query_service.py
    player_sync_service.py
  scrapers/
    player_search_scraper.py
    player_profile_scraper.py
    club_players_scraper.py
  normalizers/
    player_normalizer.py
  repositories/
    player_repository.py
  db/
    models.py
    session.py
    migrations/      # Alembic
  utils/
  main.py
```

---

## Rozdział odpowiedzialności

### `scrapers`

- zna HTML,
- zna selektory,
- zna adresy Transfermarktu,
- zwraca surowe dane.

### `normalizers`

- czyści dane,
- mapuje na stabilny model,
- ujednolica typy,
- obsługuje braki.

### `repositories`

- tylko baza danych,
- brak logiki biznesowej,
- CRUD i query builder.

### `services`

- sync,
- odświeżanie,
- filtrowanie,
- orkiestracja przepływu danych.

### `api/routes`

- cienki layer HTTP,
- walidacja request/response,
- delegacja do serwisów.

To jest **czysty, prosty monolit**, dokładnie odpowiedni do tego use case'u.

---

## Czego nie robić

Na tym etapie nie brałbym:

- React / Next.js jako obowiązkowego frontendu,
- mikroserwisów,
- Celery / Redis,
- Elasticsearch / OpenSearch,
- Dockera jako wymagania do lokalnego developmentu,
- Postgresa na start,
- async orchestration tylko dlatego, że „brzmi nowocześnie”.

To byłby klasyczny overengineering.

---

## Główne ryzyka

### 1. Kruchość scrapingu

To największe ryzyko projektu.

Zmiana HTML = ryzyko awarii parsera.

Dlatego:

- trzymaj selektory w jednym miejscu,
- nie rozrzucaj parserów po całym kodzie,
- testuj parsery na fixture'ach HTML,
- loguj brakujące pola,
- dodaj bezpieczne fallbacki.

### 2. Niepełne dane

Nie każdy zawodnik będzie miał komplet informacji.

Dlatego pola takie jak:

- agent,
- kontrakt,
- występy reprezentacyjne,

powinny być nullable.

### 3. Wolny sync przy większej skali

Jeśli będziesz zaciągał wielu zawodników, sync będzie trwał.

Na start wystarczy:

- batch sync,
- retry,
- prosty rate limit,
- zapis `last_scraped_at`,
- możliwość odświeżenia tylko wybranych rekordów.

Bez workerów i bez kolejki na dzień 1.

---

## Plan wdrożenia MVP

### Etap 1

- tabela `players`,
- model ORM,
- migracje Alembic,
- scraper profilu zawodnika,
- normalizer,
- `POST /players/sync/{id}`,
- `GET /players` z filtrami,
- timeout/retry/rate limit,
- podstawowe testy parsera.

### Etap 2

- sync listy zawodników klubu,
- paginacja,
- sortowanie,
- prosty panel HTML,
- statusy syncu (`ok`/`partial`/`error`).

### Etap 3

- incremental refresh (`next_refresh_at`),
- testy parserów na fixture'ach,
- eksport CSV,
- ewentualny cache per klub / per zapytanie źródłowe.

---

## Finalna rekomendacja

Gdybym miał to prowadzić jako senior developer, rekomendacja byłaby taka:

> Zostajemy przy Python/FastAPI. Budujemy jeden lokalny monolit z warstwą scrapingu, warstwą normalizacji i lokalną bazą SQLite. Filtrowanie działa wyłącznie na danych zapisanych w bazie. Sync danych jest osobnym procesem technicznym. Nie dokładamy ciężkiej infrastruktury, bo ten projekt ma być prywatnym, szybkim i tanim w utrzymaniu narzędziem.

To jest najzdrowsza architektura dla tego przypadku.
