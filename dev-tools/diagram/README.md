# Dev Progress Diagram (React Flow)

A standalone, no-build-step React Flow diagram for tracking AutoCI development status across all components.

## How to view

1. Open `dev-tools/diagram/index.html` in VS Code.
2. Right-click → **Open with Live Server** (install the extension if you don't have it).
3. Browser opens at `http://127.0.0.1:5500/dev-tools/diagram/` (or similar).
4. Pan / zoom / explore.

No `npm install`. No build step. React + React Flow load via CDN (`esm.sh`) on first run — needs an internet connection for that.

## How to update progress

Edit `diagram.js`. Four things stay in sync:

1. **`NOW`** — what Claude and Charle are working on right now. Update at every sprint-step transition or whenever the parallel work for Charle changes.
2. **`SPRINTS`** — the sprint tracker. Each sprint has `status` (`done` / `in_progress` / `pending`), `progress` (0..1 bar fill), and a `substeps` list with their own statuses. Bump these as steps complete.
3. **`NODES_RAW`** — the node's status (so the visual graph reflects current state).
4. **`CHANGELOG`** — a one-line entry at the top describing what changed.

The changelog renders as a sidebar on the right of the diagram so "what changed recently" is visible at a glance. Keep entries short. Five `kind` values are styled distinctly:

- `shipped` — green dot. A node moved to ✅ done.
- `progress` — amber dot. A node is in flight.
- `cut` — red dot. Something was removed from scope (likely moved to ROADMAP).
- `decision` — purple dot. An architectural / scope decision worth remembering.
- `infra` — cyan dot. Infrastructure event (deploy, key rotation, MCP tool added).

Each node lives in `NODES_RAW` as a 6-tuple:

```js
[groupId, id, label, status, effort, phase]
```

- **status**: `'done'` | `'wip'` | `'todo'` | `'todoBig'` (red, for L/XL items) | `'retire'`
- **effort**: `'XS'` | `'S'` | `'M'` | `'L'` | `'XL'` | `''` for done items

Save → Live Server auto-reloads.

Also keep `CONTEXT/dev-progress-diagram.md` in sync — it's the markdown source of truth that this React Flow view mirrors. If the two drift, the markdown wins.

## How to add nodes

1. Add a row to `NODES_RAW` with the 6-tuple.
2. If it's a brand new category, add an entry to `GROUPS` first.
3. Optionally add edges to `EDGES_RAW` for the high-signal connections.

Layout is automatic within each group — nodes flow in `cols` columns based on order.

## Files

- `index.html` — entry point + header + legend
- `diagram.js` — node + edge data + React Flow component
- `styles.css` — dark theme + status-color classes
- `README.md` — this file

## Why standalone, not a Next.js page?

Charle wanted a Live-Server-friendly tool that doesn't require running the full backend or `npm run dev`. This folder is intentionally decoupled from the main app.
