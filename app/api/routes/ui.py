from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(tags=["ui"])


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui")


@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def ui_page() -> HTMLResponse:
    return HTMLResponse(_UI_HTML)


_UI_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AFM Search Console</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
      :root {
        --bg-1: #f3f9f5;
        --bg-2: #d9efe5;
        --ink: #102018;
        --muted: #3d5b4b;
        --accent: #0f7a4e;
        --accent-2: #0a4f80;
        --card: #ffffffd9;
        --border: #b9d8c8;
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        color: var(--ink);
        font-family: "Space Grotesk", sans-serif;
        background:
          radial-gradient(circle at 10% 10%, #d7f4e6 0%, transparent 35%),
          radial-gradient(circle at 90% 20%, #dbe8ff 0%, transparent 35%),
          linear-gradient(130deg, var(--bg-1), var(--bg-2));
      }

      .shell {
        max-width: 1200px;
        margin: 24px auto;
        padding: 0 16px 32px;
      }

      .hero {
        padding: 18px 20px;
        border: 1px solid var(--border);
        border-radius: 16px;
        background: var(--card);
        backdrop-filter: blur(4px);
      }

      .hero h1 {
        margin: 0 0 6px;
        font-size: 30px;
      }

      .hero p {
        margin: 0;
        color: var(--muted);
      }

      .grid {
        margin-top: 16px;
        display: grid;
        gap: 16px;
        grid-template-columns: 1fr;
      }

      @media (min-width: 980px) {
        .grid {
          grid-template-columns: 1fr 2fr;
          align-items: start;
        }
      }

      .card {
        border: 1px solid var(--border);
        border-radius: 16px;
        background: var(--card);
        padding: 16px;
      }

      .card h2 {
        margin: 0 0 10px;
        font-size: 18px;
      }

      .row {
        margin-bottom: 10px;
      }

      .row label {
        display: block;
        font-size: 12px;
        margin-bottom: 4px;
        color: var(--muted);
      }

      .row input,
      .row select,
      .row textarea {
        width: 100%;
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 8px 10px;
        font-family: inherit;
        background: #fff;
      }

      .row textarea {
        min-height: 72px;
        resize: vertical;
      }

      .grid-2 {
        display: grid;
        gap: 10px;
        grid-template-columns: 1fr 1fr;
      }

      .btn-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }

      button {
        border: none;
        border-radius: 10px;
        padding: 9px 12px;
        color: #fff;
        cursor: pointer;
        font-weight: 600;
        font-family: inherit;
      }

      .btn-primary { background: var(--accent); }
      .btn-secondary { background: var(--accent-2); }
      .btn-neutral { background: #4d5c54; }

      .mono {
        font-family: "IBM Plex Mono", monospace;
        font-size: 12px;
      }

      #sync-output {
        margin-top: 8px;
        padding: 10px;
        border: 1px dashed var(--border);
        border-radius: 10px;
        min-height: 64px;
        white-space: pre-wrap;
      }

      .summary {
        margin: 10px 0 8px;
        color: var(--muted);
        font-size: 14px;
      }

      .table-wrap {
        overflow: auto;
        border: 1px solid var(--border);
        border-radius: 12px;
      }

      table {
        width: 100%;
        border-collapse: collapse;
        min-width: 920px;
      }

      thead th {
        text-align: left;
        font-size: 12px;
        padding: 10px;
        border-bottom: 1px solid var(--border);
        background: #eef8f2;
      }

      tbody td {
        font-size: 13px;
        padding: 10px;
        border-bottom: 1px solid #e8f0eb;
      }

      .muted {
        color: var(--muted);
      }

      .pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
      }

      .pill-ok { background: #d9f7e7; color: #0f7a4e; }
      .pill-partial { background: #fff3d7; color: #8a6000; }
      .pill-error { background: #ffe0e0; color: #9d2020; }
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <h1>AFM Search Console</h1>
        <p>Sync data from Transfermarkt and filter players from local SQLite read model.</p>
      </section>

      <section class="grid">
        <aside class="card">
          <h2>Sync Controls</h2>

          <div class="row">
            <label for="api-key">X-API-Key</label>
            <input id="api-key" type="password" placeholder="change-me" />
          </div>

          <div class="row">
            <label for="sync-player-id">Single Player ID</label>
            <input id="sync-player-id" type="text" placeholder="e.g. 28003" />
          </div>

          <div class="btn-row">
            <button class="btn-secondary" id="sync-player-btn" type="button">Sync Player</button>
          </div>

          <div class="row" style="margin-top:12px;">
            <label for="sync-search-name">Search Name</label>
            <input id="sync-search-name" type="text" placeholder="e.g. Messi" />
          </div>

          <div class="grid-2">
            <div class="row">
              <label for="sync-search-limit">Search Limit</label>
              <input id="sync-search-limit" type="number" min="1" max="20" value="3" />
            </div>
            <div class="row"></div>
          </div>

          <div class="btn-row">
            <button class="btn-secondary" id="sync-search-btn" type="button">Sync By Name</button>
          </div>

          <div class="row" style="margin-top:12px;">
            <label for="sync-club-id">Club ID</label>
            <input id="sync-club-id" type="text" placeholder="e.g. 418" />
          </div>

          <div class="btn-row">
            <button class="btn-secondary" id="sync-club-btn" type="button">Sync Club</button>
          </div>

          <div class="row" style="margin-top:12px;">
            <label for="sync-batch-ids">Batch IDs (comma-separated)</label>
            <textarea id="sync-batch-ids" placeholder="28003, 68290, 342229"></textarea>
          </div>

          <div class="btn-row">
            <button class="btn-secondary" id="sync-batch-btn" type="button">Sync Batch</button>
          </div>

          <div id="sync-output" class="mono muted">No sync action yet.</div>
        </aside>

        <section class="card">
          <h2>Player Filters</h2>
          <form id="filters-form">
            <div class="grid-2">
              <div class="row">
                <label for="name">Name</label>
                <input id="name" name="name" type="text" />
              </div>
              <div class="row">
                <label for="position">Position</label>
                <input id="position" name="position" type="text" />
              </div>
            </div>

            <div class="grid-2">
              <div class="row">
                <label for="agent">Agent</label>
                <input id="agent" name="agent" type="text" />
              </div>
              <div class="row">
                <label for="sort_by">Sort By</label>
                <select id="sort_by" name="sort_by">
                  <option value="last_scraped_at">last_scraped_at</option>
                  <option value="id">id</option>
                  <option value="full_name">full_name</option>
                  <option value="birth_date">birth_date</option>
                  <option value="club_apps">club_apps</option>
                  <option value="national_team_apps">national_team_apps</option>
                  <option value="contract_expires_at">contract_expires_at</option>
                </select>
              </div>
            </div>

            <div class="grid-2">
              <div class="row">
                <label for="birth_date_from">Birth Date From</label>
                <input id="birth_date_from" name="birth_date_from" type="date" />
              </div>
              <div class="row">
                <label for="birth_date_to">Birth Date To</label>
                <input id="birth_date_to" name="birth_date_to" type="date" />
              </div>
            </div>

            <div class="grid-2">
              <div class="row">
                <label for="contract_expires_after">Contract Expires After</label>
                <input id="contract_expires_after" name="contract_expires_after" type="date" />
              </div>
              <div class="row">
                <label for="contract_expires_before">Contract Expires Before</label>
                <input id="contract_expires_before" name="contract_expires_before" type="date" />
              </div>
            </div>

            <div class="grid-2">
              <div class="row">
                <label for="club_apps_min">Club Apps Min</label>
                <input id="club_apps_min" name="club_apps_min" type="number" min="0" />
              </div>
              <div class="row">
                <label for="club_apps_max">Club Apps Max</label>
                <input id="club_apps_max" name="club_apps_max" type="number" min="0" />
              </div>
            </div>

            <div class="grid-2">
              <div class="row">
                <label for="national_team_apps_min">National Apps Min</label>
                <input id="national_team_apps_min" name="national_team_apps_min" type="number" min="0" />
              </div>
              <div class="row">
                <label for="national_team_apps_max">National Apps Max</label>
                <input id="national_team_apps_max" name="national_team_apps_max" type="number" min="0" />
              </div>
            </div>

            <div class="grid-2">
              <div class="row">
                <label for="limit">Limit</label>
                <input id="limit" name="limit" type="number" min="1" max="200" value="50" />
              </div>
              <div class="row">
                <label for="offset">Offset</label>
                <input id="offset" name="offset" type="number" min="0" value="0" />
              </div>
            </div>

            <div class="grid-2">
              <div class="row">
                <label for="sort_order">Sort Order</label>
                <select id="sort_order" name="sort_order">
                  <option value="desc">desc</option>
                  <option value="asc">asc</option>
                </select>
              </div>
              <div class="row"></div>
            </div>

            <div class="btn-row">
              <button class="btn-primary" type="submit">Apply Filters</button>
              <button class="btn-neutral" id="reset-btn" type="button">Reset</button>
            </div>
          </form>

          <div class="summary mono" id="results-summary">No query executed yet.</div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Position</th>
                  <th>Club</th>
                  <th>Club Apps</th>
                  <th>National Apps</th>
                  <th>Contract</th>
                  <th>Agent</th>
                  <th>Sync</th>
                </tr>
              </thead>
              <tbody id="players-tbody"></tbody>
            </table>
          </div>
        </section>
      </section>
    </main>

    <script>
      const filtersForm = document.getElementById("filters-form");
      const summaryEl = document.getElementById("results-summary");
      const tbody = document.getElementById("players-tbody");
      const syncOutput = document.getElementById("sync-output");

      function toQueryString(formData) {
        const params = new URLSearchParams();
        for (const [key, value] of formData.entries()) {
          if (value !== "") {
            params.append(key, value);
          }
        }
        return params.toString();
      }

      function syncBadge(status) {
        if (status === "ok") return '<span class="pill pill-ok">ok</span>';
        if (status === "partial") return '<span class="pill pill-partial">partial</span>';
        return '<span class="pill pill-error">error</span>';
      }

      function renderPlayers(items) {
        if (!items.length) {
          tbody.innerHTML = '<tr><td colspan="9" class="muted">No players found.</td></tr>';
          return;
        }
        tbody.innerHTML = items.map((player) => `
          <tr>
            <td class="mono">${player.transfermarkt_id}</td>
            <td>${player.full_name}</td>
            <td>${player.position ?? "-"}</td>
            <td>${player.club_name ?? "-"}</td>
            <td>${player.club_apps ?? "-"}</td>
            <td>${player.national_team_apps ?? "-"}</td>
            <td>${player.contract_expires_at ?? "-"}</td>
            <td>${player.agent_name ?? "-"}</td>
            <td>${syncBadge(player.sync_status)}</td>
          </tr>
        `).join("");
      }

      async function fetchPlayers() {
        const queryString = toQueryString(new FormData(filtersForm));
        const url = queryString ? `/players?${queryString}` : "/players";
        summaryEl.textContent = "Loading...";

        try {
          const response = await fetch(url);
          const payload = await response.json();
          if (!response.ok) {
            throw new Error(payload.detail || "Failed to fetch players");
          }
          renderPlayers(payload.items || []);
          summaryEl.textContent = `total=${payload.total} limit=${payload.limit} offset=${payload.offset}`;
        } catch (error) {
          tbody.innerHTML = '<tr><td colspan="9" class="muted">Query failed.</td></tr>';
          summaryEl.textContent = String(error);
        }
      }

      async function runSync(url, body) {
        const apiKey = document.getElementById("api-key").value.trim();
        if (!apiKey) {
          syncOutput.textContent = "Provide X-API-Key first.";
          return;
        }

        syncOutput.textContent = "Sync in progress...";
        try {
          const response = await fetch(url, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-API-Key": apiKey,
            },
            body: body ? JSON.stringify(body) : undefined,
          });
          const payload = await response.json();
          syncOutput.textContent = JSON.stringify(payload, null, 2);
          await fetchPlayers();
        } catch (error) {
          syncOutput.textContent = String(error);
        }
      }

      filtersForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await fetchPlayers();
      });

      document.getElementById("reset-btn").addEventListener("click", async () => {
        filtersForm.reset();
        document.getElementById("limit").value = "50";
        document.getElementById("offset").value = "0";
        document.getElementById("sort_by").value = "last_scraped_at";
        document.getElementById("sort_order").value = "desc";
        await fetchPlayers();
      });

      document.getElementById("sync-player-btn").addEventListener("click", async () => {
        const playerId = document.getElementById("sync-player-id").value.trim();
        if (!playerId) {
          syncOutput.textContent = "Provide a player ID.";
          return;
        }
        await runSync(`/players/sync/${encodeURIComponent(playerId)}`);
      });

      document.getElementById("sync-search-btn").addEventListener("click", async () => {
        const name = document.getElementById("sync-search-name").value.trim();
        const limitRaw = document.getElementById("sync-search-limit").value;
        const limit = Number(limitRaw || "3");

        if (!name) {
          syncOutput.textContent = "Provide a player name.";
          return;
        }

        await runSync("/players/sync/search", { name, limit });
      });

      document.getElementById("sync-club-btn").addEventListener("click", async () => {
        const clubId = document.getElementById("sync-club-id").value.trim();
        if (!clubId) {
          syncOutput.textContent = "Provide a club ID.";
          return;
        }
        await runSync(`/clubs/${encodeURIComponent(clubId)}/players/sync`);
      });

      document.getElementById("sync-batch-btn").addEventListener("click", async () => {
        const raw = document.getElementById("sync-batch-ids").value;
        const ids = raw.split(",").map((value) => value.trim()).filter(Boolean);
        if (!ids.length) {
          syncOutput.textContent = "Provide at least one batch ID.";
          return;
        }
        await runSync("/players/sync", { transfermarkt_ids: ids });
      });

      fetchPlayers();
    </script>
  </body>
</html>
"""



