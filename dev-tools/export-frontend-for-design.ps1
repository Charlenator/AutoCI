# Exports a curated copy of frontend/ for hand-off to a UI-focused Claude
# session (mockups / design pass). Strips node_modules, .next, lockfiles,
# build artifacts — keeps only the source + configs Claude needs to reason
# about layout, components, types, and Tailwind.
#
# Usage (from project root):
#   pwsh ./dev-tools/export-frontend-for-design.ps1
#   pwsh ./dev-tools/export-frontend-for-design.ps1 -Dest "..\autoci-design-bundle"
#
# Then zip the output dir and upload, or drag the folder into the Claude UI.

[CmdletBinding()]
param(
    [string]$Source = "frontend",
    [string]$Dest   = "frontend-design-export"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Source)) {
    throw "Source folder '$Source' not found. Run from project root."
}

# Reset destination
if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
New-Item -ItemType Directory -Path $Dest | Out-Null

# Copy src/ recursively, excluding heavy / generated dirs and tests
$srcRoot = Join-Path $Source "src"
$destSrc = Join-Path $Dest   "src"
$null = robocopy $srcRoot $destSrc /S `
    /XD "node_modules" ".next" "dist" "build" "__tests__" `
    /XF "*.test.tsx" "*.test.ts" "*.spec.tsx" "*.spec.ts" "*.tsbuildinfo" `
    /NFL /NDL /NJH /NJS /NP

# Copy public/ (favicons, svgs) — small static assets help with brand context
$pubSrc = Join-Path $Source "public"
if (Test-Path $pubSrc) {
    Copy-Item -Recurse $pubSrc (Join-Path $Dest "public")
}

# Copy root-level configs Claude needs to understand build / types / Tailwind
$rootFiles = @(
    "package.json",         # see deps; do NOT modify here
    "tsconfig.json",         # path aliases
    "next.config.ts",
    "next-env.d.ts",
    "postcss.config.mjs",
    "eslint.config.mjs"
)
foreach ($f in $rootFiles) {
    $p = Join-Path $Source $f
    if (Test-Path $p) { Copy-Item $p (Join-Path $Dest $f) }
}

# Drop a README pointing the design session at the prompt + constraints
$readme = @"
# AutoCI frontend — design-pass bundle

Curated extract of `frontend/` for a Claude UI-design session.

What's included:
- `src/` — all .tsx, .ts, .css source (tests stripped)
- `public/` — static assets
- Root configs: package.json, tsconfig.json, next.config.ts, postcss.config.mjs, eslint.config.mjs

What's NOT included (deliberately):
- node_modules/, .next/, build artifacts
- package-lock.json (too big, not useful for design)

Read `DESIGN_BRIEF.md` next door (in the parent project) for the prompt
and constraints. The TL;DR: replace visual treatment, keep prop shapes,
keep file paths, keep component names, keep export signatures.
"@
Set-Content -Path (Join-Path $Dest "README.md") -Value $readme -Encoding utf8

# Summary
$files = Get-ChildItem -Recurse -File $Dest
$totalKB = [math]::Round(($files | Measure-Object -Property Length -Sum).Sum / 1KB, 1)
Write-Host ""
Write-Host "Exported $($files.Count) files ($totalKB KB) to: $Dest"
Write-Host "Top-level layout:"
Get-ChildItem $Dest | ForEach-Object { Write-Host "  $($_.Name)" }
