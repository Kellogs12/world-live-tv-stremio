# World Live TV & Cartoon Vault - Agent Guidelines

## 1. Stremio Catalog Curation & Metadata Verification
- **Strict Cinemeta ID Verification**: Never add an IMDb ID (`tt...`) to `SHOW_DEFINITIONS` or `build_cartoon_vault.py` without verifying it directly via Cinemeta (`https://v3-cinemeta.strem.io/meta/{type}/{id}.json`).
- **Catalog Genre Consistency**: Ensure that every catalog item resolves to the appropriate genre (e.g., `Animation` for cartoon catalogs, or official live-action adaptations). Never allow romance, adult crime, or unrelated movies into children/animation vaults.
- **Title & Type Matching**: Verify that the declared item type (`movie` vs `series`) matches Cinemeta's type. Mismatches can cause Cinemeta to pull an unrelated movie sharing a similar ID or fail to load.
- **Description Completeness**: If Cinemeta lacks a description for a valid canonical ID, always provide a rich curated description in `FALLBACK_METADATA` so no catalog tile displays an empty synopsis or a generic fallback.

## 2. Live Channel Feeds & Language Standards
- **English-First Invariant**: Live cartoon network channels (Cartoon Network, Disney Channel, Nickelodeon, NickToons, Boomerang) must stream with English audio as the primary audio track.
- **Multi-Stream Redundancy**: Provide multi-stream options (working HLS `.m3u8` feeds and Archive.org direct MP4 backups) to prevent channel dead-links.
- **Catalog Compatibility**: Preserve legacy catalog IDs (`cartoons-cn-disney`, `cartoons-nick`, `cartoons-classics`) alongside new featured catalogs (`cartoons-toonertia`, `cartoons-spelunkr`) to ensure zero disruptions for existing AIOStreams users.

## 3. Windows PowerShell & Python Execution Invariants
- **Standalone Scripts over Inline Commands**: Do not run complex inline Python `-c` commands with quotes in PowerShell. Always write scripts to standalone files in the scratch directory and execute them via `& 'C:\Program Files\GOG Galaxy\python\python.exe' path\to\script.py`.
- **Console UTF-8 Encoding**: Always include `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` in Python scripts to prevent Windows `cp1252` character mapping crashes on emojis.
- **Network & Git Calls**: Any command requiring external network connectivity (Cinemeta API verification, GitHub pull/push, stream testing) must use `BypassSandbox: true`.
