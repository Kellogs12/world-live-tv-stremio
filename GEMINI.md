# Project Context & Environment Guide: Stremio & AIOStreams

This repository (`world-live-tv-stremio`) and its associated Stremio / AIOStreams ecosystem power a streamlined streaming setup.

## 1. System Architecture & Repositories

- **Main Repository:** `https://github.com/Kellogs12/world-live-tv-stremio.git` (branch `main`)
- **Live GitHub Pages URL:** `https://kellogs12.github.io/world-live-tv-stremio/`
- **Secondary Repository (DO NOT TOUCH):** `https://github.com/Kellogs12/marvel-dc-stremio.git` (Marvel & DC catalogs only)

## 2. AIOStreams Configuration

- **AIOStreams Instance URL:** `https://aiostreamsfortheweebsstable.midnightignite.me`
- **User UUID:** `a2459246-1f42-4ba0-9dce-79eae1bc35f0`
- **Password:** `@L^qk9#qVC`
- **AIOStreams Stremio Manifest URL:**
  `https://aiostreamsfortheweebsstable.midnightignite.me/stremio/a2459246-1f42-4ba0-9dce-79eae1bc35f0/eyJpIjoiOFhJNGYxcENaWUpWZzAyWDdZTlpyUT09IiwiZSI6IjVEU1NpQ0JHcU4wSUpva1VEWG5KM1h2dkdVOEt2WFRmT0dlc1FSeDMxZkE9IiwidCI6ImEifQ/manifest.json`
- **Stremio Account Email:** `keeganlabutte4ever@gmail.com`

### AIOStreams Optimizations Applied:
- **Formatter:** `prism` (Modern badges: `🔥4K UHD`, `🚀 FHD`, Dolby Vision, HDR10, Atmos 7.1, file size, `⚡Ready (RD/TB)`)
- **Instant Debrid Filter:** `excludeUncachedFromServices: ['realdebrid', 'torbox']` (Filters out uncached P2P dead torrents)
- **Scraper Timeouts:** 5.0s on core scrapers (`Torrentio`, `Meteor`, `Comet`, `MediaFusion`, `Jackettio`, `Debridio`), 3.5s on secondary (`StremThru Torz`, `TorrentGalaxy`, `Sootio`, `Zilean`)
- **Catalog Layout:** 48 curated catalogs organized into:
  1. Flagship Streaming (Netflix Top 10, Disney+, HBO Max, Apple TV+, Prime)
  2. Curated Universes (Marvel MCU, X-Men, DC DCEU, Batman, Star Wars, Power Rangers)
  3. Vault & Anime (Cartoon Vault, Kitsu Anime)
  4. Live 24/7 Channels (Sports, Cartoons, Telenovelas)
  5. Personal Debrid Cloud (RealDebrid, TorBox)

## 3. Power Rangers Universe Implementation

- **Manifest:** `https://kellogs12.github.io/world-live-tv-stremio/power-rangers/manifest.json`
- **Root Problem Solved:** Default Cinemeta was missing episode listings for standalone series IDs. Scrapers index torrents only under master TVDB/IMDb series ID `tt0106064` (Seasons 1..30).
- **Solution:** Built static `meta/series/{id}.json` and `meta/movie/{id}.json` for all 22 series and 7 movies. Mapped all 977 episodes with full titles, descriptions, thumbnails, and canonical stream IDs (`tt0106064:{season}:{ep}`).
- **Integration:** Integrated directly inside AIOStreams with priority routing over generic TMDB fallbacks.

## 4. Maintenance & Testing Commands

- **Run all tests:**
  ```bash
  python3 -m unittest discover -s tests
  ```
- **Rebuild all catalogs:**
  ```bash
  python3 generate.py
  ```
