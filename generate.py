#!/usr/bin/env python3
"""
Multi-Country Live TV Stremio Addon Generator
Modeled on the proven AU Live TV architecture (marvel-dc-stremio/livetv.py).
Reads sources.json, fetches & cleans M3U feeds, removes stale files, and builds static Stremio Addons.
"""

import json
import os
import re
import shutil
import socket
import ssl
import sys
import urllib.request
import urllib.error

socket.setdefaulttimeout(5.0)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_FILE = os.path.join(SCRIPT_DIR, "sources.json")
ICON_FILE = os.path.join(SCRIPT_DIR, "tv-icon.png")
BASE_URL = "https://kellogs12.github.io/world-live-tv-stremio"
VERSION = "1.2.0"

HLS_HINT = {
    "proxyHeaders": {
        "response": {
            "content-type": "application/vnd.apple.mpegurl"
        }
    }
}


def slug(text):
    """Convert channel name or id into safe slug for Stremio ID."""
    s = re.sub(r'[^a-z0-9]+', '-', str(text).strip().lower())
    s = re.sub(r'-+', '-', s).strip('-')
    return s or "channel"


def clean_name(name):
    """Clean channel display names from M3U playlists."""
    name = re.sub(r'\s+(via\s+\S+\s+)?(temp\s+)?find\b.*$', '', name, flags=re.I)
    name = re.sub(r'\s+via\s+\w+\s+source$', '', name, flags=re.I)
    name = re.sub(r'\s+alt$', '', name, flags=re.I)
    name = re.sub(r'\s+(alt\s+)?geo$', '', name, flags=re.I)
    name = re.sub(r'\s*\((australia|au|us|uk|ca|nz|substitute)\)', '', name, flags=re.I)
    return ' '.join(name.split())


def clean_xumo_url(url):
    """Strip expired session/IP parameters from Xumo URLs while keeping ads.xumo_channelId."""
    m = re.search(r'(ads\.xumo_channelId=\d+)', url)
    base = url.split('?')[0]
    return f"{base}?{m.group(1)}" if m else base


def parse_m3u(text):
    """Return [{'name', 'url', <tvg attributes>}] from an extended M3U playlist."""
    out, info = [], None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('#EXTINF:'):
            head, _, name = line[8:].partition(',')
            info = dict(re.findall(r'([\w-]+)="([^"]*)"', head))
            info['name'] = ' '.join(name.split())
        elif line and not line.startswith('#') and info is not None:
            if line.startswith('https://'):
                info['url'] = line
                out.append(info)
            info = None
    return out


def fetch_m3u(url, timeout=20):
    """Download and parse an M3U8 playlist."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (world-live-tv-stremio builder)'}
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                content = resp.read().decode('utf-8', errors='replace')
        except urllib.error.URLError:
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                content = resp.read().decode('utf-8', errors='replace')
        return parse_m3u(content)
    except Exception as e:
        print(f"  [Notice] Could not fetch M3U {url}: {e}")
        return []


def host_resolves(host, cache={}):
    """Check if hostname resolves in DNS (cached)."""
    if host in cache:
        return cache[host]
    try:
        socket.getaddrinfo(host, 443)
        cache[host] = True
    except Exception:
        cache[host] = False
    return cache[host]


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(',', ':'))
        f.write('\n')


def generate_addon_for_country(country, base_dir):
    code = country["code"]
    name = country["name"]
    flag = country.get("flag", "📺")
    desc = country.get("description", f"Live TV channels for {name}.")
    id_prefix = f"tv-{code}-"
    icon_url = f"{BASE_URL}/{code}/assets/icon.png"

    country_dir = os.path.join(base_dir, code)
    catalog_dir = os.path.join(country_dir, "catalog", "tv")
    meta_dir = os.path.join(country_dir, "meta", "tv")
    stream_dir = os.path.join(country_dir, "stream", "tv")
    assets_dir = os.path.join(country_dir, "assets")

    # Remove stale generated directories before rebuilding
    for stale in [os.path.join(country_dir, "catalog"),
                  os.path.join(country_dir, "meta"),
                  os.path.join(country_dir, "stream")]:
        if os.path.exists(stale):
            shutil.rmtree(stale)

    for d in [catalog_dir, meta_dir, stream_dir, assets_dir]:
        os.makedirs(d, exist_ok=True)

    if os.path.exists(ICON_FILE):
        shutil.copy(ICON_FILE, os.path.join(assets_dir, "icon.png"))

    print(f"\nProcessing {flag} {name} ({code})...")

    seen_ids = set()
    seen_names_per_cat = {}

    def make_id(raw):
        cid = id_prefix + slug(raw)
        n, base = 2, cid
        while cid in seen_ids:
            cid, n = f"{base}-{n}", n + 1
        seen_ids.add(cid)
        return cid

    default_cat_id = country["catalogs"][0]["id"] if country.get("catalogs") else f"{code}-live"
    catalog_names = {c["id"]: c["name"] for c in country.get("catalogs", [])}
    channels_by_cat = {c["id"]: [] for c in country.get("catalogs", [])}

    def add_channel(cat_id, raw_id, ch_name, ch_url, ch_logo="", ch_desc=""):
        if not ch_url or not ch_url.startswith("https://"):
            return
        if re.search(r'\btest stream\b', ch_name, re.I):
            return
        if cat_id not in channels_by_cat:
            cat_id = default_cat_id
        seen_names = seen_names_per_cat.setdefault(cat_id, set())
        norm_name = ch_name.casefold().strip()
        if norm_name in seen_names:
            return
        seen_names.add(norm_name)

        uid = make_id(raw_id or ch_name)
        logo = ch_logo if (ch_logo and ch_logo.startswith("https://")) else icon_url
        desc_text = ch_desc or f"{ch_name} · Free live stream"
        channels_by_cat[cat_id].append({
            "id": uid,
            "name": ch_name,
            "url": ch_url,
            "logo": logo,
            "description": desc_text
        })

    # 1. Add curated / fallback channels first
    for fb in country.get("fallback_channels", []):
        add_channel(
            cat_id=fb.get("catalog", default_cat_id),
            raw_id=fb.get("id") or fb["name"],
            ch_name=fb["name"],
            ch_url=fb["url"],
            ch_logo=fb.get("logo", ""),
            ch_desc=f"{fb['name']} · Live TV"
        )

    # 2. Fetch and process M3U sources
    for src in country.get("m3u_sources", []):
        m3u_url = src["url"]
        cat_id = src.get("catalog", default_cat_id)
        src_type = src.get("type", "generic")

        raw_list = fetch_m3u(m3u_url)
        print(f"  Fetched {len(raw_list)} https channels from {m3u_url}")

        if src_type == "mjh_au":
            fta_items = []
            free_items = []
            for c in raw_list:
                number = int(c['tvg-chno']) if c.get('tvg-chno', '').isdigit() else None
                if (number and number >= 300) or re.search(r'\bradio\b|in 90 seconds', c['name'], re.I):
                    continue
                if number is not None:
                    fta_items.append((number, c))
                else:
                    free_items.append(c)
            for number, c in sorted(fta_items, key=lambda p: p[0]):
                add_channel(
                    cat_id="au-fta",
                    raw_id=c.get("channel-id") or c["name"],
                    ch_name=c["name"],
                    ch_url=c["url"],
                    ch_logo=c.get("tvg-logo", ""),
                    ch_desc=f"Channel {number} · live free-to-air"
                )
            for c in free_items:
                add_channel(
                    cat_id="au-free",
                    raw_id=c.get("channel-id") or c["name"],
                    ch_name=c["name"],
                    ch_url=c["url"],
                    ch_logo=c.get("tvg-logo", ""),
                    ch_desc="Free live network channel"
                )

        elif src_type == "mjh_nz":
            fta_items = []
            other_items = []
            for c in raw_list:
                if re.search(r'\bradio\b|rnz|tahuhu|star\b', c['name'], re.I):
                    continue
                number = int(c['tvg-chno']) if c.get('tvg-chno', '').isdigit() else None
                if number is not None:
                    fta_items.append((number, c))
                else:
                    other_items.append(c)
            for number, c in sorted(fta_items, key=lambda p: p[0]):
                add_channel(
                    cat_id=cat_id,
                    raw_id=c.get("channel-id") or c["name"],
                    ch_name=c["name"],
                    ch_url=c["url"],
                    ch_logo=c.get("tvg-logo", ""),
                    ch_desc=f"Channel {number} · NZ Freeview"
                )
            for c in other_items:
                add_channel(
                    cat_id=cat_id,
                    raw_id=c.get("channel-id") or c["name"],
                    ch_name=c["name"],
                    ch_url=c["url"],
                    ch_logo=c.get("tvg-logo", ""),
                    ch_desc="NZ Freeview live channel"
                )

        elif src_type == "xumo":
            for c in sorted(raw_list, key=lambda x: clean_name(x["name"]).casefold()):
                cname = clean_name(c["name"])
                curl = clean_xumo_url(c["url"])
                grp = c.get("group-title", "").replace("XUMO🇺🇸:", "").strip()
                desc_str = f"Free live channel ({grp})" if grp else "Free live channel from Xumo"
                add_channel(
                    cat_id=cat_id,
                    raw_id="xumo-" + (c.get("tvg-id") or cname),
                    ch_name=cname,
                    ch_url=curl,
                    ch_logo=c.get("tvg-logo", ""),
                    ch_desc=desc_str
                )

        elif src_type == "plex":
            for c in sorted(raw_list, key=lambda x: x["name"].casefold()):
                add_channel(
                    cat_id=cat_id,
                    raw_id="plex-" + (c.get("channel-id") or c.get("tvg-id") or c["name"]),
                    ch_name=c["name"],
                    ch_url=c["url"],
                    ch_logo=c.get("tvg-logo", ""),
                    ch_desc="Free live channel from Plex"
                )

        elif src_type == "samsung":
            for c in sorted(raw_list, key=lambda x: clean_name(x["name"]).casefold()):
                host = re.sub(r'^https?://([^/:]+).*', r'\1', c["url"])
                if not host_resolves(host):
                    continue
                cname = clean_name(c["name"])
                add_channel(
                    cat_id=cat_id,
                    raw_id="ss-" + cname,
                    ch_name=cname,
                    ch_url=c["url"],
                    ch_logo=c.get("tvg-logo", ""),
                    ch_desc="Free live channel from Samsung TV Plus"
                )

        else:
            for c in sorted(raw_list, key=lambda x: clean_name(x["name"]).casefold()):
                host = re.sub(r'^https?://([^/:]+).*', r'\1', c["url"])
                if not host_resolves(host):
                    continue
                cname = clean_name(c["name"])
                add_channel(
                    cat_id=cat_id,
                    raw_id=c.get("tvg-id") or cname,
                    ch_name=cname,
                    ch_url=c["url"],
                    ch_logo=c.get("tvg-logo", ""),
                    ch_desc=f"Free live channel ({catalog_names.get(cat_id, name)})"
                )

    # 3. Write meta, stream, and catalog JSON files
    active_catalogs = []
    total_channels = 0

    for cat_def in country.get("catalogs", []):
        cid = cat_def["id"]
        cname = cat_def["name"]
        items = channels_by_cat.get(cid, [])
        if not items:
            continue

        active_catalogs.append({"type": "tv", "id": cid, "name": cname})
        total_channels += len(items)
        metas = []

        for ch in items:
            meta = {
                "id": ch["id"],
                "type": "tv",
                "name": ch["name"],
                "poster": ch["logo"] or icon_url,
                "posterShape": "square",
                "logo": ch["logo"] or icon_url,
                "description": ch["description"],
                "genres": [cname]
            }
            metas.append(meta)

            write_json(os.path.join(meta_dir, f"{ch['id']}.json"), {"meta": meta})
            write_json(os.path.join(stream_dir, f"{ch['id']}.json"), {
                "streams": [
                    {
                        "url": ch["url"],
                        "name": "Live",
                        "title": ch["name"]
                    },
                    {
                        "url": ch["url"],
                        "name": "Live (browser)",
                        "title": f"{ch['name']}\nFor Stremio Web without the streaming server",
                        "behaviorHints": HLS_HINT
                    }
                ]
            })

        write_json(
            os.path.join(catalog_dir, f"{cid}.json"),
            {
                "metas": [
                    {k: m[k] for k in ("id", "type", "name", "poster", "posterShape", "description")}
                    for m in metas
                ]
            }
        )
        print(f"    Catalog '{cname}' ({cid}): {len(items)} channels")

    manifest_name = f"{flag} {name}" if ("tv" in name.lower() or "sports" in name.lower()) else f"{flag} {name} Live TV"
    manifest = {
        "id": f"worldlive.{code}",
        "version": VERSION,
        "name": manifest_name,
        "description": desc,
        "logo": icon_url,
        "resources": [
            "catalog",
            {"name": "meta", "types": ["tv"], "idPrefixes": [id_prefix]},
            {"name": "stream", "types": ["tv"], "idPrefixes": [id_prefix]}
        ],
        "types": ["tv"],
        "idPrefixes": [id_prefix],
        "catalogs": active_catalogs,
        "behaviorHints": {
            "configurable": False,
            "configurationRequired": False
        }
    }
    write_json(os.path.join(country_dir, "manifest.json"), manifest)
    print(f"  Total channels for {name}: {total_channels}")

    return {
        "code": code,
        "name": name,
        "flag": flag,
        "region": country.get("region", "Global"),
        "description": desc,
        "channel_count": total_channels,
        "vpn_required": country.get("vpn_required", False)
    }


def main():
    if not os.path.exists(SOURCES_FILE):
        print(f"Error: {SOURCES_FILE} not found!")
        sys.exit(1)

    with open(SOURCES_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Remove old Ireland folder if no longer in sources.json
    active_codes = {c["code"] for c in config.get("countries", [])}
    for entry in os.listdir(SCRIPT_DIR):
        full_p = os.path.join(SCRIPT_DIR, entry)
        if os.path.isdir(full_p) and os.path.exists(os.path.join(full_p, "manifest.json")):
            if entry not in active_codes:
                print(f"Removing retired country directory: {entry}")
                shutil.rmtree(full_p)

    countries = config.get("countries", [])
    print(f"Building Stremio Live TV Addons v{VERSION} for {len(countries)} countries...")

    summaries = []
    for c in countries:
        res = generate_addon_for_country(c, SCRIPT_DIR)
        summaries.append(res)

    summary_path = os.path.join(SCRIPT_DIR, "countries.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"countries": summaries}, f, indent=2)

    print("\n✅ Successfully generated all country addons!")
    for s in summaries:
        vpn_note = " (VPN needed outside country)" if s["vpn_required"] else ""
        print(f"  - {s['flag']} {s['name']}: {s['channel_count']} channels{vpn_note}")


if __name__ == "__main__":
    main()
