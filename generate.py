#!/usr/bin/env python3
"""
Multi-Country Live TV Stremio Addon Generator
Reads sources.json, parses live streams / M3U feeds, and builds static Stremio Addon folders.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_FILE = os.path.join(SCRIPT_DIR, "sources.json")

def sanitize_id(text):
    """Convert channel name or id into safe slug for Stremio ID."""
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', str(text).strip().lower()).strip('-')
    return slug or "channel"

def fetch_m3u(url, timeout=10):
    """Download and parse an M3U8 playlist."""
    channels = []
    try:
        import ssl
        ctx = ssl.create_default_context()
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                content = resp.read().decode('utf-8', errors='ignore')
        except urllib.error.URLError:
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                content = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  [Notice] Could not fetch M3U {url}: {e} (Using fallback/curated channels)")
        return []

    current_meta = {}
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#EXTINF:"):
            # Parse EXTINF line
            info_part = line[8:]
            title = ""
            if "," in info_part:
                attrs_part, title = info_part.rsplit(",", 1)
            else:
                attrs_part = info_part

            tvg_id = ""
            tvg_name = ""
            tvg_logo = ""
            group = ""

            m_id = re.search(r'tvg-id="([^"]*)"', attrs_part)
            if m_id: tvg_id = m_id.group(1)

            m_name = re.search(r'tvg-name="([^"]*)"', attrs_part)
            if m_name: tvg_name = m_name.group(1)

            m_logo = re.search(r'tvg-logo="([^"]*)"', attrs_part)
            if m_logo: tvg_logo = m_logo.group(1)

            m_grp = re.search(r'group-title="([^"]*)"', attrs_part)
            if m_grp: group = m_grp.group(1)

            name = title.strip() or tvg_name.strip() or tvg_id.strip() or "Live Channel"
            current_meta = {
                "id": tvg_id or sanitize_id(name),
                "name": name,
                "logo": tvg_logo,
                "group": group
            }
        elif line.startswith("http://") or line.startswith("https://"):
            if current_meta:
                current_meta["url"] = line
                channels.append(current_meta)
                current_meta = {}

    return channels

def generate_addon_for_country(country, base_dir):
    code = country["code"]
    name = country["name"]
    flag = country.get("flag", "📺")
    desc = country.get("description", f"Live TV channels for {name}.")
    
    country_dir = os.path.join(base_dir, code)
    catalog_dir = os.path.join(country_dir, "catalog", "tv")
    meta_dir = os.path.join(country_dir, "meta", "tv")
    stream_dir = os.path.join(country_dir, "stream", "tv")
    assets_dir = os.path.join(country_dir, "assets")

    for d in [catalog_dir, meta_dir, stream_dir, assets_dir]:
        os.makedirs(d, exist_ok=True)

    print(f"\nProcessing {flag} {name} ({code})...")

    # Gather channels: start with fallbacks
    seen_ids = set()
    channels = []

    default_cat_id = country["catalogs"][0]["id"] if country.get("catalogs") else f"{code}-live"

    for fb in country.get("fallback_channels", []):
        cid = fb.get("id") or sanitize_id(fb["name"])
        unique_id = f"tv-{code}-{cid}"
        if unique_id in seen_ids:
            continue
        seen_ids.add(unique_id)
        channels.append({
            "id": unique_id,
            "raw_id": cid,
            "name": fb["name"],
            "catalog": fb.get("catalog", default_cat_id),
            "logo": fb.get("logo", ""),
            "url": fb["url"]
        })

    # Try fetching online M3U URLs
    for m3u_url in country.get("m3u_urls", []):
        fetched = fetch_m3u(m3u_url)
        print(f"  Fetched {len(fetched)} channels from {m3u_url[:45]}...")
        for ch in fetched:
            cid = sanitize_id(ch["id"])
            unique_id = f"tv-{code}-{cid}"
            if unique_id in seen_ids:
                continue
            seen_ids.add(unique_id)

            # Assign to catalog
            cat = default_cat_id
            grp_lower = ch.get("group", "").lower()
            for c_def in country.get("catalogs", []):
                if c_def["name"].lower() in grp_lower or c_def["id"].lower() in grp_lower:
                    cat = c_def["id"]
                    break

            channels.append({
                "id": unique_id,
                "raw_id": cid,
                "name": ch["name"],
                "catalog": cat,
                "logo": ch.get("logo", ""),
                "url": ch["url"]
            })

    print(f"  Total channels for {name}: {len(channels)}")

    # 1. Build meta and stream JSON files
    catalog_items = {cat["id"]: [] for cat in country.get("catalogs", [])}
    if default_cat_id not in catalog_items:
        catalog_items[default_cat_id] = []

    for ch in channels:
        ch_id = ch["id"]
        ch_name = ch["name"]
        ch_logo = ch["logo"]
        ch_url = ch["url"]
        cat_id = ch["catalog"]
        if cat_id not in catalog_items:
            cat_id = default_cat_id

        # meta JSON
        meta_json = {
            "meta": {
                "id": ch_id,
                "type": "tv",
                "name": ch_name,
                "poster": ch_logo,
                "posterShape": "square",
                "logo": ch_logo,
                "description": f"{ch_name} · Free Live Stream",
                "genres": [cat_id]
            }
        }
        with open(os.path.join(meta_dir, f"{ch_id}.json"), "w", encoding="utf-8") as f:
            json.dump(meta_json, f, indent=2)

        # stream JSON (Live + Live browser for Stremio Web)
        stream_json = {
            "streams": [
                {
                    "url": ch_url,
                    "name": "Live",
                    "title": ch_name
                },
                {
                    "url": ch_url,
                    "name": "Live (browser)",
                    "title": f"{ch_name}\nFor Stremio Web",
                    "behaviorHints": {
                        "proxyHeaders": {
                            "response": {
                                "content-type": "application/vnd.apple.mpegurl"
                            }
                        }
                    }
                }
            ]
        }
        with open(os.path.join(stream_dir, f"{ch_id}.json"), "w", encoding="utf-8") as f:
            json.dump(stream_json, f, indent=2)

        # Append to catalog metas
        catalog_items[cat_id].append({
            "id": ch_id,
            "type": "tv",
            "name": ch_name,
            "poster": ch_logo,
            "posterShape": "square",
            "description": f"{ch_name} · live stream"
        })

    # 2. Build catalog JSON files
    for cat_id, items in catalog_items.items():
        cat_file = os.path.join(catalog_dir, f"{cat_id}.json")
        with open(cat_file, "w", encoding="utf-8") as f:
            json.dump({"metas": items}, f, indent=2)

    # 3. Build manifest.json
    manifest = {
        "id": f"worldlive.{code}",
        "version": "1.0.0",
        "name": f"{flag} {name} Live TV",
        "description": desc,
        "resources": [
            "catalog",
            {"name": "meta", "types": ["tv"], "idPrefixes": [f"tv-{code}-"]},
            {"name": "stream", "types": ["tv"], "idPrefixes": [f"tv-{code}-"]}
        ],
        "types": ["tv"],
        "idPrefixes": [f"tv-{code}-"],
        "catalogs": [
            {"type": "tv", "id": cat["id"], "name": cat["name"]}
            for cat in country.get("catalogs", [])
        ],
        "behaviorHints": {
            "configurable": False,
            "configurationRequired": False
        }
    }
    with open(os.path.join(country_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return {
        "code": code,
        "name": name,
        "flag": flag,
        "region": country.get("region", "Global"),
        "description": desc,
        "channel_count": len(channels),
        "vpn_required": country.get("vpn_required", False)
    }

def main():
    if not os.path.exists(SOURCES_FILE):
        print(f"Error: {SOURCES_FILE} not found!")
        sys.exit(1)

    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    countries = config.get("countries", [])
    print(f"Building Stremio Live TV Addons for {len(countries)} countries...")

    summaries = []
    for c in countries:
        res = generate_addon_for_country(c, SCRIPT_DIR)
        summaries.append(res)

    # Save summary metadata for index.html to read dynamically or display
    summary_path = os.path.join(SCRIPT_DIR, "countries.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"countries": summaries}, f, indent=2)

    print("\n✅ Successfully generated all country addons!")
    for s in summaries:
        vpn_note = " (VPN needed outside country)" if s["vpn_required"] else ""
        print(f"  - {s['flag']} {s['name']}: {s['channel_count']} channels{vpn_note}")

if __name__ == "__main__":
    main()
