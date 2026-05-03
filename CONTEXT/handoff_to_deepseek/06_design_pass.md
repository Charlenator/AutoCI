# Task 06 — Design pass: apply `style_guide.css`

## Goal

Apply the locked design system in [`CONTEXT/style_guide.css`](../style_guide.css)
across every UI surface. The style guide is the contract — read its
**IMPLEMENTATION RULES** block at the top before doing ANY of the
sub-tasks below. Don't paraphrase the rules; don't deviate.

This task assumes Tasks 01–05 are functionally complete (the components
exist, even if currently styled with plain Tailwind).

## Files this task touches

Most frontend `.tsx` and `.css` files. Each sub-task lists its specific
files. The big move:

- REPLACE: `frontend/src/app/globals.css` — entire content becomes the
  contents of `CONTEXT/style_guide.css`.
- RENAME (with both exports kept for back-compat): `TopNav.tsx` → `Sidebar.tsx`.
- REWRITE every component listed in `style_guide.css` to use the
  classes defined there.

## Acceptance criteria

- After all 11 sub-tasks: every styled element on every page comes from a
  class defined in `style_guide.css`. No new Tailwind utility colors
  outside the locked palette. No inline `style={{ color: "..." }}`
  anywhere except in places the style guide explicitly allows (e.g.
  dynamic score-bar widths).
- The IMPLEMENTATION RULES at the top of `style_guide.css` are followed
  verbatim. Most-violated risks: ad-hoc shadows (rule 4), gradients (12),
  emojis (11), `rounded-full` on rectangles (5), font families outside
  the two locked faces (2).
- Lighthouse a11y score on the chat page ≥ 95.
- `npm run lint && npm run build` passes.

---

## Sub-tasks

### 06.1 — Move the style guide into `globals.css`

**File**: `frontend/src/app/globals.css` (REPLACE), `frontend/src/app/layout.tsx` (verify font import only)

**Prompt to paste:**

```
Step 1 of the AutoCI design pass.

Read CONTEXT/style_guide.css end-to-end. The IMPLEMENTATION RULES at the
top are non-negotiable.

1. Replace the entire contents of frontend/src/app/globals.css with the
   contents of CONTEXT/style_guide.css. Keep the @tailwind directives at
   the top if Tailwind is currently in use:

     @tailwind base;
     @tailwind components;
     @tailwind utilities;
     /* ...the rest of style_guide.css... */

2. Confirm frontend/src/app/layout.tsx wires Geist Sans + Geist Mono via
   next/font (style_guide.css §1 references --font-sans and --font-mono;
   they need to resolve). If layout.tsx isn't already importing both,
   add them:

     import { Geist, Geist_Mono } from "next/font/google";
     const sans = Geist({ subsets: ["latin"], variable: "--font-sans" });
     const mono = Geist_Mono({ subsets: ["latin"], variable: "--font-mono" });

   Apply both className/variable to <body> so the CSS variables resolve.

3. Run `cd frontend && npm run build` and fix any build error. The build
   should succeed before you finish this sub-task.

DO NOT change any component yet. Subsequent sub-tasks update components
one by one.
```

---

### 06.2 — Sidebar (replaces TopNav)

**File**: `frontend/src/components/Sidebar.tsx` (RENAME from TopNav.tsx),
`frontend/src/app/layout.tsx` (rewire), three pages (drop `<TopNav>` if
they used it directly).

**Prompt to paste:**

```
Step 2 of the AutoCI design pass.

Re-read CONTEXT/style_guide.css §4 (Sidebar). The exact classes you must
emit: .sidebar, .brand, .brand-mark, .brand-name, .brand-sub, .workspace,
.workspace-dot, .workspace-meta, .workspace-name, .workspace-role,
.workspace-caret, .nav-section, .nav-label, .nav, .nav a, .nav a.active,
.nav-icon, .nav-meta, .sidebar-foot, .sources-btn, .sources-btn .count.

1. Rename frontend/src/components/TopNav.tsx → Sidebar.tsx. Keep a default
   export from Sidebar.tsx; in TopNav.tsx leave a one-line re-export shim
   (`export { default } from "./Sidebar";`) so existing imports don't
   break.

2. Sidebar.tsx renders the .sidebar layout per §4. Three nav items:
     - "RAG Chat" → /
     - "Candidate Search" → /candidates
     - "Continuous Improvement" → /cis    (note the rename from "Kaizen")
   The .nav-icon is a small <svg> (1.4px stroke, 16x16) using
   currentColor. Use Lucide-style stroked icons inline as <svg> markup.
   No icon library — paste the path data directly. (Suggested icons:
   message-circle for chat, users for candidates, target for CIS.)

3. The .sidebar-foot has the .sources-btn that opens
   KnowledgeSourcesPanel — preserve the existing onClick handler.

4. layout.tsx wraps every page in the .app + .shell layout from §3:
     <body>
       <div className="app">
         <Sidebar />
         <div className="shell">
           <Topbar />            {/* §5; updated in 06.3 */}
           <div className="main-wrap">
             <main className="main">{children}</main>
             <RightDrawer />     {/* §6 */}
           </div>
         </div>
       </div>
     </body>

5. Remove any old <TopNav> tab strip from individual pages.

After: visit / and confirm the sidebar renders, the workspace block + nav
look right, and active page styling is applied via the .active class.

Do not change page-level layouts beyond removing the old <TopNav>.
```

---

### 06.3 — Topbar

**File**: `frontend/src/components/Topbar.tsx` (NEW), `frontend/src/app/layout.tsx` (mount it)

**Prompt to paste:**

```
Step 3 of the design pass.

Re-read style_guide.css §5 (Top bar) and §17 (eyebrow utility).

Create frontend/src/components/Topbar.tsx that renders a 48px sticky
.topbar with:
  - Left: a .crumb showing "<current page name>" with .here on the last
    segment. Read the active path from next/navigation's usePathname()
    and map / → "Chat", /candidates → "Candidate Search", /cis →
    "Continuous Improvement".
  - Right (.topbar-right): a .session-pill mono showing live state — for
    chat pages a "session: <8-char-id>" if available; otherwise empty.
    Plus 1-2 .icon-btn for cost/settings (placeholders are fine — wire
    real handlers later).

Mount it inside .shell above .main-wrap (per the layout in 06.2).

Do not modify any other file.
```

---

### 06.4 — RightDrawer

**File**: `frontend/src/components/RightDrawer.tsx` (REWRITE)

**Prompt to paste:**

```
Step 4 of the design pass.

Re-read style_guide.css §6 (Right Drawer).

Rewrite RightDrawer.tsx to use the .right-drawer + .drawer-toggle +
.drawer-body classes. Preserve all existing functionality (the React Flow
canvas mount + open/close state). The drawer collapses to 48px and
expands to 360px.

For now, the drawer-body can show the .drawer-stub placeholder rendering
the React Flow canvas mount node. If RightDrawer currently has a graph
implementation, keep it working — only restyle.

Do not change RightDrawer's prop API.
```

---

### 06.5 — ChatPanel + Composer

**File**: `frontend/src/components/chat/ChatPanel.tsx` (REWRITE), `frontend/src/app/page.tsx` (verify wrapping)

**Prompt to paste:**

```
Step 5 of the design pass.

Re-read style_guide.css §8 (Chat page) and §13 (Composer).

Rewrite ChatPanel.tsx so its DOM matches the classes defined there. Map:
  - <ChatPanel> root → .chat-page (or just the .chat-col if the
    drawer wraps externally — pick the one that gives the correct flex)
  - chat header → .chat-header with .chat-title + .chat-subtitle
  - the empty state → .empty + .suggestions + .suggestion buttons (the
    suggestion buttons replace the current bullet list)
  - user messages → .user-msg + .user-bubble + .user-meta (mono timestamp)
  - assistant messages → .assistant-msg + .assistant-stamp (with .dot) +
    .assistant-bubble + .sources-row (footer of citation chips)
  - composer → .composer + .composer-shell + .composer-foot + .composer-hint

Preserve every existing behavior: fetch flow, citation drawer, knowledge
panel, query transformation card. The only thing that changes is markup
+ classes — no new state, no new props.

Use semantic <button>, <textarea>, <kbd>, <p>. Wire keyboard hint:
"Enter to send, Shift+Enter for newline" using <kbd> per §13.

Do not modify chat-types.ts.
```

---

### 06.6 — CitationChip + CitationDrawer + Citation + Evidence block

**Files**: `CitationChip.tsx`, `CitationDrawer.tsx`, `Citation.tsx` (all REWRITE)

**Prompt to paste:**

```
Step 6 of the design pass.

Re-read style_guide.css §9 (Citation chip), §11 (Citation drawer + card),
§12 (Evidence block).

Rewrite the three files to render the exact classes defined. Notes:

  CitationChip.tsx:
    - Always renders as <button>. The chip uses .cite-chip and adds .active
      when the parent says it's the focused citation.
    - Hover/active state is owned via the parent passing `active` prop
      (existing behavior; just rename classes).

  CitationDrawer.tsx:
    - Root: .cite-drawer with .cite-drawer-head (h2 + .badge with chunk
      count + close button) + .cite-drawer-body containing the cards.

  Citation.tsx:
    - One <article className="cite-card"> per citation. .cite-card-head
      with .cite-card-num + .cite-card-kind (mono uppercase) + .cite-card-label.
    - .cite-card-body contains:
        - <dl className="field-row"> rows for top-level fields (template,
          rows, corpus, similarity).
        - <pre className="sql-pre"> for SQL.
        - <table className="row-table"> for result rows.
        - For RAG citations: a <p className="chunk-text"> with the chunk text.
        - The B-evidence section uses the .evidence wrapper:
            .evidence-head with .marker (rust accent) + .evidence-title +
            .evidence-count.
            .evidence-body with the source-record table; same .row-table.

  Wire the focus ring: a card gets .focused when a chat-side citation chip
  is hovered/clicked. State lives on the parent (ChatPanel); pass an
  activeIndex through props (already exists).

Don't change any prop interfaces. Don't change citation logic — only
markup + classes.
```

---

### 06.7 — QueryTransformationCard

**File**: `frontend/src/components/chat/QueryTransformationCard.tsx` (REWRITE)

**Prompt to paste:**

```
Step 7 of the design pass.

Re-read style_guide.css §10 (Query Transformation Card). The QTC is the
ONE dark surface in the otherwise-light chat — see rule #7.

Rewrite QueryTransformationCard.tsx to emit:
  - root: .qtc with .open class when expanded
  - .qtc-head (button) — .qtc-head-l with .qtc-tag eyebrow + .qtc-route
    summary; .qtc-head-r with .qtc-conf (with <b>{confidence}</b>) and
    .qtc-toggle (the +/− glyph)
  - .qtc-body when expanded — three .qtc-block sections each with
    .qtc-label + content. Plain prose lines use .qtc-prose (sans, light
    color); explainers use .qtc-explain.
  - The "What we ran" pill is .qtc-pill (uppercase, ink-2 background).
  - SQL block: <pre className="qtc-pre">.
  - Vector retrieval block: <dl className="qtc-kv"> with dt/dd pairs.
  - Live web search line: append a second .qtc-pill with ".qtc-pill"
    using --debug-accent variant (amber). Add a small CSS rule for it if
    needed; otherwise re-use the existing .qtc-pill and the live-search
    text underneath in .qtc-detail.

Preserve every existing prop + computed value (route description, exact
query rendering, live-search summary). Just restyle.
```

---

### 06.8 — Candidate Search page (post-B8)

**File**: `frontend/src/app/candidates/page.tsx` + `CandidateTable.tsx` + `ScheduleMeetingModal.tsx` (REWRITE)

**Prompt to paste:**

```
Step 8 of the design pass. Pre-req: Task 04 (B8) is complete.

Re-read style_guide.css §14 (Candidate Search page).

Rewrite the candidates page + table + modal to emit:
  - candidates/page.tsx root: .cand-page with .filters (left rail) + .cand-main
  - .filters has .filter-group blocks (status, role, etc.) using .facet
    rows. For first pass, the filters can be static checkboxes that don't
    actually filter (or filter client-side); functional filtering wiring
    can land later.
  - .cand-header for title; .cand-toolbar for the search input + sort +
    "Export CSV" placeholder. Use .search-input with the inner <input>.
  - .cand-meta (mono) shows result count.
  - .cand-table-wrap > <table className="cand-table"> with columns:
      Candidate (.cand-name with .cand-avatar showing initials in a circle
        + name + .cand-sub for email)
      Skills (multiple .tag elements)
      Match (.score with .score-bar > <i style={{width: ...%}} />)
      Flags (.flag elements; .flag.ok for non-problem)
      CV (a row-action button with .row-btn)
      Actions (.row-actions with .row-btn.primary "Schedule Meeting")
  - ScheduleMeetingModal: use .modal-backdrop + .modal + .modal-head +
    .modal-summary (3 stats: total slots, days covered, selected) +
    .modal-body + slot grid (custom — reuse .source-card-style cards
    grouped by date with selectable buttons). Send button is .btn.btn-primary.

Preserve all existing functionality from B8. No new data flows.
```

---

### 06.9 — CIS page (post-Sprint C)

**File**: `frontend/src/app/cis/page.tsx` + `InterventionsTable.tsx` (REWRITE)

**Prompt to paste:**

```
Step 9 of the design pass. Pre-req: Task 05 (Sprint C) is complete.

Re-read style_guide.css §15 (CIS page).

Rewrite cis/page.tsx + InterventionsTable.tsx to emit:
  - .cis-page > .cis-side (left rail with tools) + .cis-main
  - In .cis-side, render each tool as .tool-card with .tool-card.picked
    when the K_TOOL_SELECTOR has selected it. .tool-card .nm + .desc.
  - .cis-header for title, .charter-bar below it (after charter is
    ready) with .charter-item k/v pairs.
  - .kpi-row with three .kpi tiles. Use .kpi.amber / .kpi.red flavors
    based on KPI status. Source values from /metrics/kpis once
    role_title is known.
  - .timeline as the main scroll area. One .phase per executed tool.
    .phase.active for the running phase, .phase.complete for prior.
    .phase-head (with .phase-step circle, .phase-name, .phase-sub,
    .phase-status pill) + .writeup body (with .writeup-head eyebrow,
    .writeup-headline, .writeup-tldr, .writeup-section blocks).
  - Evidence pills inside writeup sections are .evidence-pills + .evidence-pill.
  - HITL bar at the bottom of the active phase: .hitl with .hitl .lbl +
    .hitl-actions containing two .btn (Advance + Ask).
  - InterventionsTable.tsx renders .row-table at the bottom of the
    timeline with the columns from Task 05 §9, using .tag for skills-like
    pills, .flag for status, etc.

Preserve every Task 05 behavior. No new state.
```

---

### 06.10 — KnowledgeSourcesPanel

**File**: `frontend/src/components/chat/KnowledgeSourcesPanel.tsx` (REWRITE)

**Prompt to paste:**

```
Step 10 of the design pass.

Re-read style_guide.css §16 (Knowledge Sources Modal).

Rewrite KnowledgeSourcesPanel.tsx to render a slide-over modal:
  - .modal-backdrop > .modal
  - .modal-head with h2 + p subtitle
  - .modal-summary with 4 .summary-stat tiles (corpora count, total chunks,
    SQL tables, total rows) — values from /sources.
  - .modal-body with two .modal-section blocks:
      "Knowledge corpora" — list of .source-card per corpus (corpus name in
        mono, chunk count, description).
      "SQL tables" — list of .source-card per table (table name in mono,
        row count, description).

Preserve the existing /sources fetch + caching behavior.
```

---

### 06.11 — A11y + responsive sweep

**File**: any (audit pass)

**Prompt to paste:**

```
Step 11 of the design pass — final audit.

1. Run `cd frontend && npm run build`. Fix any error.

2. Run `cd frontend && npm run lint`. Fix any error or warning that's not
   a noise rule. Don't disable lint rules.

3. Open the deployed Vercel URL in Chrome. Run Lighthouse against /:
     - Performance ≥ 90
     - Accessibility ≥ 95
     - Best Practices ≥ 95
   If a11y < 95, open DevTools and audit the failures. Common fixes:
     - Add aria-label to icon-only buttons.
     - Ensure every form input has a <label htmlFor>.
     - Increase contrast where text fails WCAG AA.
   Don't suppress a11y warnings via aria-hidden unless the element really
   is decorative.

4. Sanity-check responsive behavior at 1280px, 1440px, and 1920px widths.
   The style guide rule §14 fixes container widths (chat 760, drawer 420,
   etc.) — they should stay fixed. The bug-prone surfaces are the
   sidebar (240) and the right drawer (360 expanded).

5. Confirm no emojis appear anywhere in the deployed UI (Ctrl+F the
   bundle if needed). Confirm no `bg-blue-600`, no `bg-blue-700`, no
   `rounded-full` on rectangles, no inline `style={{color: ...}}` outside
   the score-bar width and any documented exceptions.

Update KANBAN.md: 06.1-06.11 → "Done".
```

## Definition of done

- All 11 sub-tasks moved to KANBAN "Done"
- `npm run build` + `npm run lint` pass
- Lighthouse a11y ≥ 95 on the chat page
- No emojis, no `bg-blue-600/700`, no banned classes (per `style_guide.css`
  rule #18)

## Commit + push

Commit per logical group (e.g. one commit for sidebar + topbar, one for
chat surfaces, one for candidates, one for CIS, one for the audit fixes).
Push at the end:

```
git push origin main
```
