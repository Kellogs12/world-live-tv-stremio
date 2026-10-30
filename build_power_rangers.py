#!/usr/bin/env python3
"""
Power Rangers Universe Stremio Catalog Addon Generator.
Generates a dedicated on-demand catalog addon for Power Rangers:
- Chronological Series (all 30 seasons)
- Eras of Power Rangers:
    * Saban Era (1993–2002)
    * Disney Era (2003–2009)
    * Neo-Saban Era (2011–2018)
    * Hasbro Era (2019–2023)
- Power Rangers Movies & Specials
Uses Cinemeta API to pull complete IMDb metadata, posters, ratings, and descriptions.
Generates static catalog routes:
  - catalog/{type}/{id}.json
  - catalog/{type}/{id}/skip=0.json
  - catalog/{type}/{id}/skip=100.json
"""

import json
import os
import shutil
import socket
import ssl
import sys
import time
import urllib.request
import urllib.error

socket.setdefaulttimeout(8.0)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://kellogs12.github.io/world-live-tv-stremio"
PR_DIR_NAME = "power-rangers"
PR_ID = "worldlive.powerrangers"
PR_VERSION = "1.0.0"
PR_NAME = "⚡ Power Rangers Universe"
PR_DESC = (
    "Complete on-demand universe of Power Rangers: Chronological Series (all 30 seasons), "
    "Eras (Saban, Disney, Neo-Saban, Hasbro), and Movies & Specials."
)

CATALOG_DEFINITIONS = [
    {
        "type": "series",
        "id": "pr-chronological",
        "name": "Chronological Series"
    },
    {
        "type": "series",
        "id": "pr-saban-era",
        "name": "Saban Era (1993–2002)"
    },
    {
        "type": "series",
        "id": "pr-disney-era",
        "name": "Disney Era (2003–2009)"
    },
    {
        "type": "series",
        "id": "pr-neosaban-era",
        "name": "Neo-Saban Era (2011–2018)"
    },
    {
        "type": "series",
        "id": "pr-hasbro-era",
        "name": "Hasbro Era (2019–2023)"
    },
    {
        "type": "movie",
        "id": "pr-movies",
        "name": "Power Rangers Movies & Specials"
    }
]

SHOW_DEFINITIONS = {
    "pr-chronological": [
        ("tt0106064", "Mighty Morphin Power Rangers"),       # Seasons 1–3 & Alien Rangers (1993–1996)
        ("tt0115319", "Power Rangers Zeo"),                 # Season 4 (1996–1997)
        ("tt0118436", "Power Rangers Turbo"),               # Season 5 (1997–1998)
        ("tt0120575", "Power Rangers in Space"),            # Season 6 (1998–1999)
        ("tt0175059", "Power Rangers Lost Galaxy"),         # Season 7 (1999–2000)
        ("tt0212686", "Power Rangers Lightspeed Rescue"),   # Season 8 (2000)
        ("tt0256278", "Power Rangers Time Force"),          # Season 9 (2001)
        ("tt0287871", "Power Rangers Wild Force"),          # Season 10 (2002–2003)
        ("tt0312189", "Power Rangers Ninja Storm"),         # Season 11 (2003–2004)
        ("tt0373587", "Power Rangers DinoThunder"),         # Season 12 (2004)
        ("tt0414762", "Power Rangers S.P.D."),              # Season 13 (2005)
        ("tt0451469", "Power Rangers Mystic Force"),        # Season 14 (2006)
        ("tt0784920", "Power Rangers Operation Overdrive"), # Season 15 (2007)
        ("tt1121628", "Power Rangers Jungle Fury"),         # Season 16 (2008)
        ("tt1304612", "Power Rangers RPM"),                 # Season 17 (2009)
        ("tt1704503", "Power Rangers Samurai"),             # Seasons 18–19 (Samurai / Super Samurai)
        ("tt2236126", "Power Rangers Megaforce"),           # Seasons 20–21 (Megaforce / Super Megaforce)
        ("tt3521854", "Power Rangers Dino Charge"),         # Seasons 22–23 (Dino Charge / Dino Super Charge)
        ("tt5335606", "Power Rangers Ninja Steel"),         # Seasons 24–25 (Ninja Steel / Super Ninja Steel)
        ("tt8022978", "Power Rangers Beast Morphers"),      # Seasons 26–27 (2019–2020)
        ("tt12360292", "Power Rangers Dino Fury"),          # Seasons 28–29 (2021–2022)
        ("tt29474102", "Power Rangers Cosmic Fury")         # Season 30 (2023)
    ],
    "pr-saban-era": [
        ("tt0106064", "Mighty Morphin Power Rangers"),
        ("tt0115319", "Power Rangers Zeo"),
        ("tt0118436", "Power Rangers Turbo"),
        ("tt0120575", "Power Rangers in Space"),
        ("tt0175059", "Power Rangers Lost Galaxy"),
        ("tt0212686", "Power Rangers Lightspeed Rescue"),
        ("tt0256278", "Power Rangers Time Force"),
        ("tt0287871", "Power Rangers Wild Force")
    ],
    "pr-disney-era": [
        ("tt0312189", "Power Rangers Ninja Storm"),
        ("tt0373587", "Power Rangers DinoThunder"),
        ("tt0414762", "Power Rangers S.P.D."),
        ("tt0451469", "Power Rangers Mystic Force"),
        ("tt0784920", "Power Rangers Operation Overdrive"),
        ("tt1121628", "Power Rangers Jungle Fury"),
        ("tt1304612", "Power Rangers RPM")
    ],
    "pr-neosaban-era": [
        ("tt1704503", "Power Rangers Samurai"),
        ("tt2236126", "Power Rangers Megaforce"),
        ("tt3521854", "Power Rangers Dino Charge"),
        ("tt5335606", "Power Rangers Ninja Steel")
    ],
    "pr-hasbro-era": [
        ("tt8022978", "Power Rangers Beast Morphers"),
        ("tt12360292", "Power Rangers Dino Fury"),
        ("tt29474102", "Power Rangers Cosmic Fury")
    ],
    "pr-movies": [
        ("tt0113820", "Mighty Morphin Power Rangers: The Movie"),
        ("tt0120389", "Turbo: A Power Rangers Movie"),
        ("tt6099542", "Power Rangers Samurai: Clash of the Red Rangers - The Movie"),
        ("tt2367036", "Power Rangers Monster Bash Halloween Special"),
        ("tt4962796", "Power Rangers Super Megaforce: The Legendary Battle"),
        ("tt3717490", "Power Rangers"),
        ("tt23219684", "Mighty Morphin Power Rangers: Once & Always")
    ]
}


# Map individual series IMDb ID to the master Mighty Morphin Power Rangers season range
SERIES_SEASONS = {
    "tt0106064": (1, 3, "Mighty Morphin Power Rangers"),
    "tt0115319": (4, 4, "Power Rangers Zeo"),
    "tt0118436": (5, 5, "Power Rangers Turbo"),
    "tt0120575": (6, 6, "Power Rangers in Space"),
    "tt0175059": (7, 7, "Power Rangers Lost Galaxy"),
    "tt0212686": (8, 8, "Power Rangers Lightspeed Rescue"),
    "tt0256278": (9, 9, "Power Rangers Time Force"),
    "tt0287871": (10, 10, "Power Rangers Wild Force"),
    "tt0312189": (11, 11, "Power Rangers Ninja Storm"),
    "tt0373587": (12, 12, "Power Rangers DinoThunder"),
    "tt0414762": (13, 13, "Power Rangers S.P.D."),
    "tt0451469": (14, 14, "Power Rangers Mystic Force"),
    "tt0784920": (15, 15, "Power Rangers Operation Overdrive"),
    "tt1121628": (16, 16, "Power Rangers Jungle Fury"),
    "tt1304612": (17, 17, "Power Rangers RPM"),
    "tt1704503": (18, 19, "Power Rangers Samurai"),
    "tt2236126": (20, 21, "Power Rangers Megaforce"),
    "tt3521854": (22, 23, "Power Rangers Dino Charge"),
    "tt5335606": (24, 25, "Power Rangers Ninja Steel"),
    "tt8022978": (26, 27, "Power Rangers Beast Morphers"),
    "tt12360292": (28, 29, "Power Rangers Dino Fury"),
    "tt29474102": (30, 30, "Power Rangers Cosmic Fury")
}


POSTER_OVERRIDES = {
    "tt12360292": "https://m.media-amazon.com/images/M/MV5BOTRiNjU2YzItN2QzMi00NmQ5LWFkYjUtNmI3YjkxM2I3MzE3XkEyXkFqcGc@._V1_.jpg"
}


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
        f.write('\n')


def fetch_cinemeta_meta(cat_type, imdb_id, title=""):
    """Fetch rich metadata for an IMDb ID from Cinemeta v3 API."""
    url = f"https://v3-cinemeta.strem.io/meta/{cat_type}/{imdb_id}.json"
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (PowerRangersUniverse/1.0)"}
            )
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                data = json.load(resp)
                meta = data.get("meta")
                if meta:
                    return meta
        except Exception as e:
            time.sleep(1.0 * (attempt + 1))
    return None


def build_power_rangers(base_dir, refresh=False):
    """Build the Power Rangers Universe on-demand catalog addon."""
    pr_dir = os.path.join(base_dir, PR_DIR_NAME)
    cache_file = os.path.join(pr_dir, "catalog_cache.json")
    assets_dir = os.path.join(pr_dir, "assets")

    # Load cache if available
    cache = {}
    if os.path.exists(cache_file) and not refresh:
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            print(f"Loaded {len(cache)} cached metadata entries for Power Rangers.")
        except Exception as e:
            print(f"Could not load cache: {e}")
            cache = {}

    # Clean catalog directory
    catalog_base_dir = os.path.join(pr_dir, "catalog")
    if os.path.exists(catalog_base_dir):
        shutil.rmtree(catalog_base_dir)

    os.makedirs(catalog_base_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    # Ensure icon exists
    root_icon = os.path.join(base_dir, "tv-icon.png")
    dest_icon = os.path.join(assets_dir, "icon.png")
    if not os.path.exists(dest_icon) and os.path.exists(root_icon):
        shutil.copy(root_icon, dest_icon)

    total_titles = 0
    updated_cache = False

    era_genre_map = {
        "pr-saban-era": "Saban Era",
        "pr-disney-era": "Disney Era",
        "pr-neosaban-era": "Neo-Saban Era",
        "pr-hasbro-era": "Hasbro Era",
        "pr-movies": "Movies & Specials",
        "pr-chronological": "Chronological Series"
    }

    for cat_def in CATALOG_DEFINITIONS:
        cat_id = cat_def["id"]
        cat_type = cat_def["type"]
        cat_name = cat_def["name"]
        items = SHOW_DEFINITIONS.get(cat_id, [])

        print(f"\nBuilding Power Rangers catalog: '{cat_name}' ({cat_id}) - {len(items)} titles...")
        cat_metas = []

        for imdb_id, default_title in items:
            cached_meta = cache.get(imdb_id)
            desc = cached_meta.get("description", "") if cached_meta else ""
            needs_fetch = refresh or not cached_meta or not desc

            if not needs_fetch:
                meta = dict(cached_meta)
            else:
                raw_meta = fetch_cinemeta_meta(cat_type, imdb_id, default_title)
                if raw_meta:
                    genres = raw_meta.get('genres')
                    if not genres and raw_meta.get('genre'):
                        g = raw_meta.get('genre')
                        genres = [x.strip() for x in g.split(',')] if isinstance(g, str) else [g]

                    meta = {
                        "id": imdb_id,
                        "type": cat_type,
                        "name": raw_meta.get('name') or default_title,
                        "poster": POSTER_OVERRIDES.get(imdb_id) or raw_meta.get('poster') or f"https://images.metahub.space/poster/medium/{imdb_id}/img",
                        "posterShape": "poster",
                        "genres": genres or ["Action", "Sci-Fi", "Adventure"],
                        "imdbRating": str(raw_meta.get('imdbRating', '')),
                        "releaseInfo": str(raw_meta.get('releaseInfo') or raw_meta.get('year') or ''),
                        "description": raw_meta.get('description', '')
                    }
                    if raw_meta.get('background'):
                        meta["background"] = raw_meta.get('background')
                    if raw_meta.get('logo'):
                        meta["logo"] = raw_meta.get('logo')

                    cache[imdb_id] = meta
                    updated_cache = True
                elif cached_meta:
                    meta = dict(cached_meta)
                else:
                    meta = {
                        "id": imdb_id,
                        "type": cat_type,
                        "name": default_title,
                        "poster": POSTER_OVERRIDES.get(imdb_id) or f"https://images.metahub.space/poster/medium/{imdb_id}/img",
                        "posterShape": "poster",
                        "genres": ["Action", "Sci-Fi", "Adventure"],
                        "imdbRating": "",
                        "releaseInfo": "",
                        "description": f"{default_title} on demand."
                    }
                    cache[imdb_id] = meta
                    updated_cache = True

            # Apply poster override if present
            if imdb_id in POSTER_OVERRIDES:
                meta["poster"] = POSTER_OVERRIDES[imdb_id]
                if cache.get(imdb_id) and cache[imdb_id].get("poster") != POSTER_OVERRIDES[imdb_id]:
                    cache[imdb_id]["poster"] = POSTER_OVERRIDES[imdb_id]
                    updated_cache = True

            # Ensure genre reflects Power Rangers and era
            era_genre = era_genre_map.get(cat_id)
            if era_genre and era_genre not in meta.get("genres", []):
                meta["genres"] = [era_genre] + [g for g in meta.get("genres", []) if g != era_genre]

            cat_metas.append(meta)
            total_titles += 1

        catalog_response = {"metas": cat_metas}

        # Route 1: catalog/{type}/{id}.json
        route1_path = os.path.join(pr_dir, "catalog", cat_type, f"{cat_id}.json")
        write_json(route1_path, catalog_response)

        # Route 2: catalog/{type}/{id}/skip=0.json
        route2_path = os.path.join(pr_dir, "catalog", cat_type, cat_id, "skip=0.json")
        write_json(route2_path, catalog_response)

        # Route 3: catalog/{type}/{id}/skip=100.json (empty page to stop infinite pagination cleanly)
        route3_path = os.path.join(pr_dir, "catalog", cat_type, cat_id, "skip=100.json")
        write_json(route3_path, {"metas": []})

    write_json(cache_file, cache)

    # -------------------------------------------------------------
    # Generate full meta resources: meta/{type}/{id}.json
    # Stremio uses meta to display the series/movie details, seasons,
    # and episode list. By generating meta for all series with complete
    # episode videos, we ensure every season and episode is fully viewable
    # and scraped for torrents without relying on incomplete external databases.
    # -------------------------------------------------------------
    print("\nBuilding full meta resources with complete episode lists for Power Rangers...")
    meta_base_dir = os.path.join(pr_dir, "meta")
    os.makedirs(os.path.join(meta_base_dir, "series"), exist_ok=True)
    os.makedirs(os.path.join(meta_base_dir, "movie"), exist_ok=True)

    # Fetch master MMPR meta which contains all 1,000+ canonical episodes across all 30 seasons
    master_raw = fetch_cinemeta_meta("series", "tt0106064", "Mighty Morphin Power Rangers")
    master_videos = master_raw.get("videos", []) if master_raw else []

    all_series_items = list(dict.fromkeys(
        iid for cat_id, items in SHOW_DEFINITIONS.items() if cat_id != "pr-movies" for iid, _ in items
    ))
    all_movie_items = [iid for iid, _ in SHOW_DEFINITIONS.get("pr-movies", [])]

    # Generate meta for series
    for imdb_id in all_series_items:
        base_meta = dict(cache.get(imdb_id, {}))
        meta_obj = {
            "id": imdb_id,
            "type": "series",
            "name": base_meta.get("name", "Power Rangers"),
            "poster": base_meta.get("poster"),
            "posterShape": "poster",
            "genres": base_meta.get("genres", ["Action", "Sci-Fi", "Adventure"]),
            "imdbRating": base_meta.get("imdbRating", ""),
            "releaseInfo": base_meta.get("releaseInfo", ""),
            "description": base_meta.get("description", "")
        }
        if base_meta.get("background"):
            meta_obj["background"] = base_meta.get("background")
        if base_meta.get("logo"):
            meta_obj["logo"] = base_meta.get("logo")

        # Map videos for this series from the master TVDB dataset
        if imdb_id in SERIES_SEASONS and master_videos:
            s_start, s_end, _ = SERIES_SEASONS[imdb_id]
            series_videos = []
            for v in master_videos:
                s_num = v.get("season", -1)
                if s_start <= s_num <= s_end:
                    # Keep canonical stream id (tt0106064:season:episode) so all torrent indexers match
                    # Normalize displayed season relative to the series (e.g. Season 1, 2)
                    rel_season = (s_num - s_start) + 1
                    v_item = dict(v)
                    v_item["season"] = rel_season
                    series_videos.append(v_item)
            meta_obj["videos"] = series_videos
        else:
            # Fallback to direct Cinemeta videos
            direct_raw = fetch_cinemeta_meta("series", imdb_id)
            meta_obj["videos"] = direct_raw.get("videos", []) if direct_raw else []

        meta_file_path = os.path.join(meta_base_dir, "series", f"{imdb_id}.json")
        write_json(meta_file_path, {"meta": meta_obj})

    # Generate meta for movies
    for imdb_id in all_movie_items:
        base_meta = dict(cache.get(imdb_id, {}))
        direct_raw = fetch_cinemeta_meta("movie", imdb_id)
        meta_obj = {
            "id": imdb_id,
            "type": "movie",
            "name": base_meta.get("name", "Power Rangers Movie"),
            "poster": base_meta.get("poster"),
            "posterShape": "poster",
            "genres": base_meta.get("genres", ["Action", "Sci-Fi", "Adventure"]),
            "imdbRating": base_meta.get("imdbRating", ""),
            "releaseInfo": base_meta.get("releaseInfo", ""),
            "description": base_meta.get("description", "")
        }
        if base_meta.get("background"):
            meta_obj["background"] = base_meta.get("background")
        if base_meta.get("logo"):
            meta_obj["logo"] = base_meta.get("logo")
        if direct_raw and direct_raw.get("videos"):
            meta_obj["videos"] = direct_raw.get("videos")

        meta_file_path = os.path.join(meta_base_dir, "movie", f"{imdb_id}.json")
        write_json(meta_file_path, {"meta": meta_obj})

    print(f"Generated complete meta files for {len(all_series_items)} series and {len(all_movie_items)} movies.")

    # Generate Manifest
    manifest = {
        "id": PR_ID,
        "version": PR_VERSION,
        "name": PR_NAME,
        "description": PR_DESC,
        "logo": f"{BASE_URL}/{PR_DIR_NAME}/assets/icon.png",
        "resources": [
            "catalog",
            {
                "name": "meta",
                "types": ["series", "movie"],
                "idPrefixes": ["tt"]
            }
        ],
        "types": ["series", "movie"],
        "idPrefixes": ["tt"],
        "catalogs": CATALOG_DEFINITIONS,
        "behaviorHints": {
            "configurable": False,
            "configurationRequired": False
        }
    }
    manifest_path = os.path.join(pr_dir, "manifest.json")
    write_json(manifest_path, manifest)

    unique_titles = len(set(
        iid for items in SHOW_DEFINITIONS.values() for iid, _ in items
    ))

    print(f"✅ Power Rangers Universe build complete! Unique titles: {unique_titles}, Total entries: {total_titles}")

    return {
        "code": PR_DIR_NAME,
        "name": "Power Rangers Universe",
        "flag": "⚡",
        "region": "Power Rangers",
        "description": PR_DESC,
        "channel_count": unique_titles,
        "item_count": unique_titles,
        "item_label": "Series & Movies",
        "catalog_type": "On-Demand Catalog",
        "vpn_required": False
    }


def main():
    refresh = "--refresh" in sys.argv
    build_power_rangers(SCRIPT_DIR, refresh=refresh)


if __name__ == "__main__":
    main()
