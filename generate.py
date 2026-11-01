#!/usr/bin/env python3
"""
Multi-Country Live TV Stremio Addon Generator
Modeled on the proven AU Live TV architecture (marvel-dc-stremio/livetv.py).
Reads sources.json, fetches & cleans M3U feeds and Spelunkr TV (spelunkr.tv/toonertia)
manifests, removes stale files, and builds static Stremio Addons.
"""

import json
import os
import re
import shutil
import socket
import ssl
import sys
import urllib.parse
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

socket.setdefaulttimeout(5.0)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
SOURCES_FILE = os.path.join(SCRIPT_DIR, "sources.json")
ICON_FILE = os.path.join(SCRIPT_DIR, "tv-icon.png")
BASE_URL = "https://kellogs12.github.io/world-live-tv-stremio"
VERSION = "1.3.0"

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


def fetch_json_url(url, timeout=8):
    """Fetch JSON from a URL with SSL fallback."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (world-live-tv-stremio builder)'}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.URLError:
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return json.loads(resp.read().decode('utf-8'))


def build_ia_mp4_url(ia_id, filename):
    """Construct direct Internet Archive MP4 URL matching Spelunkr TV's player logic."""
    encoded_file = urllib.parse.quote(str(filename), safe="/-_.!~*'()")
    return f"https://archive.org/download/{ia_id}/{encoded_file}"


def format_duration(seconds):
    """Format duration in seconds as human-readable string (e.g. '2h 06m' or '45m')."""
    if not seconds or not isinstance(seconds, (int, float)) or seconds <= 0:
        return ""
    total_mins = int(round(seconds / 60.0))
    hrs, mins = divmod(total_mins, 60)
    if hrs > 0:
        return f"{hrs}h {mins:02d}m"
    return f"{mins}m"


def load_spelunkr_data(spelunkr_cfg, base_dir, refresh=False):
    """Load Spelunkr TV lineup and channel manifests (from live API or local spelunkr_cache.json)."""
    cache_rel = spelunkr_cfg.get("cache_file", "spelunkr_cache.json")
    cache_path = os.path.join(base_dir, cache_rel)
    cached_data = None

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
        except Exception as e:
            print(f"  [Notice] Could not read {cache_path}: {e}")

    if cached_data and not refresh:
        return cached_data

    api_url = spelunkr_cfg.get("api_url", "https://data.spelunkr.tv/lineup.json")
    target_channels = spelunkr_cfg.get("channels", ["toonertia"])
    try:
        lineup = fetch_json_url(api_url)
        channels_by_id = {c["id"]: c for c in lineup.get("channels", [])}
        out = {
            "source": spelunkr_cfg.get("url", "https://spelunkr.tv/toonertia"),
            "api": api_url,
            "channels": {}
        }
        for cid in target_channels:
            ch_meta = channels_by_id.get(cid)
            if not ch_meta:
                continue
            versions = ch_meta.get("versions", [])
            if not versions:
                continue
            manifest_rel = versions[-1].get("manifest", "")
            if not manifest_rel:
                continue
            manifest_url = f"https://data.spelunkr.tv/{manifest_rel.lstrip('/')}"
            manifest = fetch_json_url(manifest_url)
            items = [
                it for it in manifest.get("items", [])
                if it.get("id") and (it.get("mp4") or it.get("file"))
            ]
            out["channels"][cid] = {
                "id": cid,
                "dial": ch_meta.get("dial"),
                "name": ch_meta.get("name", cid.upper()),
                "emoji": ch_meta.get("emoji", "📺"),
                "description": ch_meta.get("description", ""),
                "family": ch_meta.get("family", "cartoons"),
                "color": ch_meta.get("color", "#00ccff"),
                "logo": f"https://spelunkr.tv/og/{cid}.png",
                "web_url": f"https://spelunkr.tv/{cid}",
                "manifest_path": manifest_rel,
                "items": items
            }
        if out["channels"]:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)
            return out
    except Exception as e:
        print(f"  [Notice] Using cached Spelunkr TV manifests ({e})")

    return cached_data or {"channels": {}}


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
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
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

    print(f"\nProcessing {flag} {name} ({code})...")

    # Pre-fetch M3U sources before removing existing generated files so offline runs don't wipe M3U-backed countries
    prefetched_m3u = []
    m3u_sources = country.get("m3u_sources", [])
    for src in m3u_sources:
        raw_list = fetch_m3u(src["url"])
        print(f"  Fetched {len(raw_list)} https channels from {src['url']}")
        prefetched_m3u.append((src, raw_list))

    if m3u_sources and all(len(rl) == 0 for _, rl in prefetched_m3u) and os.path.exists(os.path.join(country_dir, "manifest.json")):
        existing_total = 0
        if os.path.exists(catalog_dir):
            for fname in os.listdir(catalog_dir):
                if fname.endswith(".json"):
                    try:
                        with open(os.path.join(catalog_dir, fname), "r", encoding="utf-8") as cf:
                            existing_total += len(json.load(cf).get("metas", []))
                    except Exception:
                        pass
        if existing_total > 0:
            print(f"  [Offline Notice] Preserving existing {existing_total} channels for {name} ({code})")
            return {
                "code": code,
                "name": name,
                "flag": flag,
                "region": country.get("region", "Global"),
                "description": desc,
                "channel_count": existing_total,
                "vpn_required": country.get("vpn_required", False)
            }

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

    raw_to_id = {}
    seen_ids = set()
    seen_names_per_cat = {}

    def make_id(raw):
        clean_raw = str(raw).strip().lower()
        if clean_raw in raw_to_id:
            return raw_to_id[clean_raw]
        cid = id_prefix + slug(raw)
        n, base = 2, cid
        while cid in seen_ids:
            cid, n = f"{base}-{n}", n + 1
        seen_ids.add(cid)
        raw_to_id[clean_raw] = cid
        return cid

    default_cat_id = country["catalogs"][0]["id"] if country.get("catalogs") else f"{code}-live"
    catalog_names = {c["id"]: c["name"] for c in country.get("catalogs", [])}
    channels_by_cat = {c["id"]: [] for c in country.get("catalogs", [])}

    def add_channel(cat_id, raw_id, ch_name, ch_url, ch_logo="", ch_desc="", custom_streams=None):
        if not custom_streams and (not ch_url or not ch_url.startswith("https://")):
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
        entry = {
            "id": uid,
            "name": ch_name,
            "url": ch_url,
            "logo": logo,
            "description": desc_text
        }
        if custom_streams:
            entry["custom_streams"] = custom_streams
        channels_by_cat[cat_id].append(entry)

    # 0. Process Spelunkr TV source (e.g., spelunkr.tv/toonertia) if configured
    spelunkr_cfg = country.get("spelunkr_source")
    if spelunkr_cfg:
        refresh_sp = "--refresh-spelunkr" in sys.argv
        sp_data = load_spelunkr_data(spelunkr_cfg, base_dir, refresh=refresh_sp)
        sp_channels = sp_data.get("channels", {})
        primary_cid = spelunkr_cfg.get("primary_channel", "toonertia")
        toonertia_cat = "cartoons-toonertia" if "cartoons-toonertia" in channels_by_cat else default_cat_id
        spelunkr_cat = "cartoons-spelunkr" if "cartoons-spelunkr" in channels_by_cat else default_cat_id

        # A. Build Primary Channel (Toonertia 24/7 + all 41 Toonami VHS broadcast blocks)
        if primary_cid in sp_channels:
            tch = sp_channels[primary_cid]
            t_items = tch.get("items", [])
            t_logo = tch.get("logo") or "https://spelunkr.tv/og/toonertia.png"
            t_web = tch.get("web_url") or "https://spelunkr.tv/toonertia"
            t_dial = tch.get("dial", 53)

            # Build multi-stream list for the main TOONERTIA 24/7 channel
            main_streams = []
            for idx, item in enumerate(t_items, 1):
                mp4_file = item.get("mp4") or item.get("file")
                if not item.get("id") or not mp4_file:
                    continue
                mp4_url = build_ia_mp4_url(item["id"], mp4_file)
                yr = f" ({item['year']})" if item.get("year") else ""
                dur = format_duration(item.get("outS") or item.get("duration"))
                dur_str = f" · {dur}" if dur else ""
                main_streams.append({
                    "url": mp4_url,
                    "name": f"Toonertia #{idx}",
                    "title": f"{item.get('title', f'Block #{idx}')}{yr}{dur_str}"
                })
            main_streams.append({
                "externalUrl": t_web,
                "name": "Spelunkr TV Web",
                "title": "Launch Synchronized 24/7 Toonertia Player (spelunkr.tv/toonertia)"
            })

            add_channel(
                cat_id=toonertia_cat,
                raw_id="toonertia-24-7-live",
                ch_name=f"🚀 TOONERTIA 24/7 (Ch. {t_dial} · spelunkr.tv/toonertia)",
                ch_url=main_streams[0]["url"] if main_streams else t_web,
                ch_logo=t_logo,
                ch_desc=(
                    f"{tch.get('description', '')} "
                    f"Source: spelunkr.tv/toonertia ({len(t_items)} full Toonami VHS broadcast blocks, 1997–2007)."
                ).strip(),
                custom_streams=main_streams
            )
            if "cartoons-cn-disney" in channels_by_cat:
                add_channel(
                    cat_id="cartoons-cn-disney",
                    raw_id="toonertia-24-7-live",
                    ch_name=f"🚀 TOONERTIA 24/7 (Ch. {t_dial} · spelunkr.tv/toonertia)",
                    ch_url=main_streams[0]["url"] if main_streams else t_web,
                    ch_logo=t_logo,
                    ch_desc=(
                        f"{tch.get('description', '')} "
                        f"Source: spelunkr.tv/toonertia ({len(t_items)} full Toonami VHS broadcast blocks, 1997–2007)."
                    ).strip(),
                    custom_streams=main_streams
                )

            # Add each individual Toonertia VHS Broadcast Block as a dedicated channel card
            for idx, item in enumerate(t_items, 1):
                mp4_file = item.get("mp4") or item.get("file")
                if not item.get("id") or not mp4_file:
                    continue
                mp4_url = build_ia_mp4_url(item["id"], mp4_file)
                raw_title = item.get("title", f"Toonami Block #{idx}")
                yr = item.get("year") or ""
                dur = format_duration(item.get("outS") or item.get("duration"))
                meta_parts = [p for p in (f"Year: {yr}" if yr else "", f"Runtime: {dur}" if dur else "") if p]
                meta_suffix = f" ({' · '.join(meta_parts)})" if meta_parts else ""

                block_streams = [
                    {
                        "url": mp4_url,
                        "name": "Toonertia VHS",
                        "title": f"{raw_title}{meta_suffix}\nDirect VHS Broadcast Stream (spelunkr.tv/toonertia)"
                    },
                    {
                        "externalUrl": t_web,
                        "name": "Spelunkr TV Web",
                        "title": "Open Synchronized 24/7 Toonertia Feed (spelunkr.tv/toonertia)"
                    }
                ]
                add_channel(
                    cat_id=toonertia_cat,
                    raw_id=f"toonertia-block-{idx}-{item['id']}",
                    ch_name=f"Toonertia #{idx}: {raw_title}",
                    ch_url=mp4_url,
                    ch_logo=t_logo,
                    ch_desc=f"Toonertia VHS Broadcast Block #{idx}: {raw_title}{meta_suffix} · Powered by spelunkr.tv/toonertia",
                    custom_streams=block_streams
                )

        # B. Build All 10 Spelunkr TV Cartoon, Anime & Kids 24/7 Channels in cartoons-spelunkr
        CHANNEL_SUBTITLES = {
            "toonertia": "Toonami VHS Broadcasts 24/7",
            "latchkey-tv": "After-School CN, Nick & Toon Disney VHS",
            "saturday-morning": "80s/90s/00s Saturday Morning Cartoons VHS",
            "late-nite-swimclub": "Adult Swim Late-Night VHS Broadcasts",
            "meddling-kids": "Scooby-Doo & Hanna-Barbera Vault 24/7",
            "rocket-punch": "70s–90s Mecha Anime 24/7",
            "ovatv": "Classic Anime OVAs & Saturday Anime",
            "rubber-hose": "Golden Age Classic Cartoons 24/7",
            "kersplat": "90s Nick & Kids Game Shows 24/7",
            "library-card": "Arthur, Magic School Bus & PBS Kids Classics"
        }

        for cid in spelunkr_cfg.get("channels", []):
            ch_obj = sp_channels.get(cid)
            if not ch_obj:
                continue
            c_items = ch_obj.get("items", [])
            if not c_items:
                continue
            c_logo = ch_obj.get("logo") or f"https://spelunkr.tv/og/{cid}.png"
            c_web = ch_obj.get("web_url") or f"https://spelunkr.tv/{cid}"
            c_dial = ch_obj.get("dial")
            c_emoji = ch_obj.get("emoji", "📺")
            c_name = ch_obj.get("name", cid.upper())
            subtitle = CHANNEL_SUBTITLES.get(cid, "Spelunkr TV 24/7")
            dial_str = f"Ch. {c_dial}" if c_dial is not None else "24/7"

            ch_streams = []
            # Include up to 50 direct MP4 streams per channel so stream JSON stays fast while giving huge variety
            for idx, item in enumerate(c_items[:50], 1):
                mp4_file = item.get("mp4") or item.get("file")
                if not item.get("id") or not mp4_file:
                    continue
                mp4_url = build_ia_mp4_url(item["id"], mp4_file)
                yr = f" ({item['year']})" if item.get("year") else ""
                dur = format_duration(item.get("outS") or item.get("duration"))
                dur_str = f" · {dur}" if dur else ""
                ch_streams.append({
                    "url": mp4_url,
                    "name": f"{c_name} #{idx}",
                    "title": f"{item.get('title', f'Broadcast #{idx}')}{yr}{dur_str}"
                })
            ch_streams.append({
                "externalUrl": c_web,
                "name": "Spelunkr TV Web",
                "title": f"Watch {c_name} 24/7 Synchronized Feed on spelunkr.tv/{cid}"
            })

            add_channel(
                cat_id=spelunkr_cat,
                raw_id=f"spelunkr-{cid}",
                ch_name=f"{c_emoji} {c_name} ({dial_str}) — {subtitle}",
                ch_url=ch_streams[0]["url"] if ch_streams else c_web,
                ch_logo=c_logo,
                ch_desc=f"{ch_obj.get('description', '')} ({len(c_items)} broadcasts on spelunkr.tv/{cid})".strip(),
                custom_streams=ch_streams
            )
            # Cross-list matching channels to legacy AIOStreams catalogs
            if cid == "latchkey-tv" and "cartoons-cn-disney" in channels_by_cat:
                add_channel("cartoons-cn-disney", f"spelunkr-{cid}", f"{c_emoji} {c_name} ({dial_str}) — {subtitle}", ch_streams[0]["url"] if ch_streams else c_web, c_logo, f"{ch_obj.get('description', '')} (spelunkr.tv/{cid})", custom_streams=ch_streams)
            elif cid == "kersplat" and "cartoons-nick" in channels_by_cat:
                add_channel("cartoons-nick", f"spelunkr-{cid}", f"{c_emoji} {c_name} ({dial_str}) — {subtitle}", ch_streams[0]["url"] if ch_streams else c_web, c_logo, f"{ch_obj.get('description', '')} (spelunkr.tv/{cid})", custom_streams=ch_streams)
            elif cid in ("rubber-hose", "meddling-kids", "saturday-morning") and "cartoons-classics" in channels_by_cat:
                add_channel("cartoons-classics", f"spelunkr-{cid}", f"{c_emoji} {c_name} ({dial_str}) — {subtitle}", ch_streams[0]["url"] if ch_streams else c_web, c_logo, f"{ch_obj.get('description', '')} (spelunkr.tv/{cid})", custom_streams=ch_streams)

        # C. Add Featured VHS Broadcast Blocks (Cartoon Network, Kids' WB Pokémon, Nick, Fox Kids, etc.)
        for fb_block in spelunkr_cfg.get("featured_blocks", []):
            b_cid = fb_block.get("channel")
            b_idx = fb_block.get("index", 0)
            b_prefix = fb_block.get("prefix", "Spelunkr VHS")
            ch_obj = sp_channels.get(b_cid)
            if not ch_obj:
                continue
            c_items = ch_obj.get("items", [])
            if b_idx < 0 or b_idx >= len(c_items):
                continue
            item = c_items[b_idx]
            mp4_file = item.get("mp4") or item.get("file")
            if not item.get("id") or not mp4_file:
                continue
            mp4_url = build_ia_mp4_url(item["id"], mp4_file)
            c_logo = ch_obj.get("logo") or f"https://spelunkr.tv/og/{b_cid}.png"
            c_web = ch_obj.get("web_url") or f"https://spelunkr.tv/{b_cid}"
            raw_title = item.get("title", "VHS Broadcast Block")
            yr = item.get("year") or ""
            dur = format_duration(item.get("outS") or item.get("duration"))
            meta_parts = [p for p in (f"Year: {yr}" if yr else "", f"Runtime: {dur}" if dur else "") if p]
            meta_suffix = f" ({' · '.join(meta_parts)})" if meta_parts else ""

            b_streams = [
                {
                    "url": mp4_url,
                    "name": b_prefix,
                    "title": f"{raw_title}{meta_suffix}\nDirect VHS Broadcast Stream (spelunkr.tv/{b_cid})"
                },
                {
                    "externalUrl": c_web,
                    "name": "Spelunkr TV Web",
                    "title": f"Open {ch_obj.get('name', b_cid)} 24/7 Feed (spelunkr.tv/{b_cid})"
                }
            ]
            add_channel(
                cat_id=spelunkr_cat,
                raw_id=f"spelunkr-{b_cid}-{b_idx}-{item['id']}",
                ch_name=f"{b_prefix}: {raw_title}",
                ch_url=mp4_url,
                ch_logo=c_logo,
                ch_desc=f"{b_prefix} Broadcast Recording: {raw_title}{meta_suffix} · Powered by spelunkr.tv/{b_cid}",
                custom_streams=b_streams
            )

    # 1. Add curated / fallback channels
    for fb in country.get("fallback_channels", []):
        cat_targets = fb.get("catalogs") or [fb.get("catalog", default_cat_id)]
        c_streams = fb.get("custom_streams")
        if fb.get("id") == "cartoon-classics" and not c_streams:
            c_streams = [
                {
                    "url": "https://archive.org/download/popeye_patriotic_popeye/popeye_patriotic_popeye_512kb.mp4",
                    "name": "Popeye (1957)",
                    "title": "Patriotic Popeye (1957) · Classic Golden Age Animation"
                },
                {
                    "url": "https://archive.org/download/woody_woodpecker_pantry_panic/woody_woodpecker_pantry_panic_512kb.mp4",
                    "name": "Woody Woodpecker",
                    "title": "Woody Woodpecker: Pantry Panic (1941) · Walter Lantz"
                },
                {
                    "url": "https://archive.org/download/bb_snow_white/bb_snow_white_512kb.mp4",
                    "name": "Betty Boop",
                    "title": "Betty Boop: Snow White (1933) · Fleischer Studios"
                },
                {
                    "url": "https://archive.org/download/FLIP_FROG-FIDDLESTICKS/FLIP_FROG-FIDDLESTICKS_256k_512kb.mp4",
                    "name": "Flip the Frog",
                    "title": "Flip the Frog: Fiddlesticks (1930) · Ub Iwerks"
                },
                {
                    "url": "https://archive.org/download/superman_1941/superman_1941_512kb.mp4",
                    "name": "Superman (1941)",
                    "title": "Superman: The Mad Scientist (1941) · Fleischer Studios"
                },
                {
                    "externalUrl": "https://spelunkr.tv/rubber-hose",
                    "name": "Spelunkr TV Web",
                    "title": "Open Synchronized 24/7 Rubber Hose Stream (spelunkr.tv/rubber-hose)"
                }
            ]
        elif fb.get("id") == "cartoon-network-hd" and not c_streams:
            c_streams = [
                {
                    "url": fb["url"],
                    "name": "CN HD (English)",
                    "title": "Cartoon Network HD (720p Live English Broadcast)"
                },
                {
                    "url": "http://api.toonamiaftermath.com:3000/est/playlist.m3u8",
                    "name": "Toonami Aftermath EST",
                    "title": "Toonami Aftermath 24/7 (Classic Cartoon Network & Toonami in English)"
                },
                {
                    "externalUrl": "https://spelunkr.tv/toonertia",
                    "name": "Spelunkr TV Web",
                    "title": "Open Synchronized 24/7 Toonami VHS Feed (spelunkr.tv/toonertia)"
                }
            ]
        elif fb.get("id") == "cartoon-network-sd" and not c_streams:
            c_streams = [
                {
                    "url": fb["url"],
                    "name": "CN SD (English)",
                    "title": "Cartoon Network SD (480p Live English Broadcast)"
                },
                {
                    "url": "http://api.toonamiaftermath.com:3000/pst/playlist.m3u8",
                    "name": "Toonami Aftermath PST",
                    "title": "Toonami Aftermath Pacific 24/7 (Classic Cartoon Network in English)"
                },
                {
                    "url": "https://archive.org/download/full-1st-ever-toonami-block-3-17-96/Full%201st%20Ever%20Toonami%20Block%203-17-96.ia.mp4",
                    "name": "Toonami Launch Block",
                    "title": "Toonami 1997 First Broadcast Block (Moltar Bumpers & Commercials)"
                }
            ]
        elif fb.get("id") == "disney-channel" and not c_streams:
            c_streams = [
                {
                    "url": "https://archive.org/download/ocwoc-020c-chip-n-dale-rescue-rangers-x-3-bonkers-toon-disney-2003/OCWOC%20020c%20-%20Chip%20%27n%20Dale%20Rescue%20Rangers%20%28x3%29%2C%20Bonkers%20%28Toon%20Disney%2C%202003%29.ia.mp4",
                    "name": "Toon Disney VHS",
                    "title": "Toon Disney 2000s Broadcast Block · Chip 'n Dale & Bonkers (English)"
                },
                {
                    "url": "https://archive.org/download/talespin-darkwing-duck-disney-afternoon-1991/Talespin%20%26%20Darkwing%20Duck%20%28Disney%20Afternoon%201991%29.ia.mp4",
                    "name": "Disney Afternoon VHS",
                    "title": "Disney Afternoon (1991) · TaleSpin & Darkwing Duck (English)"
                },
                {
                    "url": "https://archive.org/download/kcal-9-1995/KCAL9-1995-60fps.mp4",
                    "name": "Disney Classics VHS",
                    "title": "Disney Broadcast (1995) · Bonkers, Aladdin & Gargoyles (English)"
                },
                {
                    "externalUrl": "https://spelunkr.tv/latchkey-tv",
                    "name": "Spelunkr TV Web",
                    "title": "Open Synchronized 24/7 Toon Disney & CN Feed (spelunkr.tv/latchkey-tv)"
                }
            ]
        for c_target in cat_targets:
            add_channel(
                cat_id=c_target,
                raw_id=fb.get("id") or fb["name"],
                ch_name=fb["name"],
                ch_url=fb["url"],
                ch_logo=fb.get("logo", ""),
                ch_desc=f"{fb['name']} · Live TV",
                custom_streams=c_streams
            )

    # 2. Process prefetched M3U sources
    for src, raw_list in prefetched_m3u:
        cat_id = src.get("catalog", default_cat_id)
        src_type = src.get("type", "generic")

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

    for cat_def in country.get("catalogs", []):
        cid = cat_def["id"]
        cname = cat_def["name"]
        items = channels_by_cat.get(cid, [])
        if not items:
            continue

        active_catalogs.append({"type": "tv", "id": cid, "name": cname})
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
            if ch.get("custom_streams"):
                write_json(os.path.join(stream_dir, f"{ch['id']}.json"), {
                    "streams": ch["custom_streams"]
                })
            else:
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

    total_channels = len(seen_ids)
    manifest_name = f"{flag} {name}" if ("tv" in name.lower() or "sports" in name.lower() or "live" in name.lower()) else f"{flag} {name} Live TV"
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
            if entry not in active_codes and entry not in ("cartoon-vault", "power-rangers"):
                print(f"Removing retired country directory: {entry}")
                shutil.rmtree(full_p)

    countries = config.get("countries", [])
    print(f"Building Stremio Live TV Addons v{VERSION} for {len(countries)} countries...")

    summaries = []
    for c in countries:
        res = generate_addon_for_country(c, SCRIPT_DIR)
        summaries.append(res)

    # Build Cartoon & Animation Vault on-demand catalog addon
    try:
        from build_cartoon_vault import build_vault
        print("\nBuilding Cartoon & Animation Vault on-demand catalog...")
        vault_summary = build_vault(SCRIPT_DIR)
        summaries.append(vault_summary)
    except Exception as e:
        print(f"  [Warning] Could not build cartoon vault: {e}")

    # Build Power Rangers Universe on-demand catalog addon
    try:
        from build_power_rangers import build_power_rangers
        print("\nBuilding Power Rangers Universe on-demand catalog...")
        pr_summary = build_power_rangers(SCRIPT_DIR)
        summaries.append(pr_summary)
    except Exception as e:
        print(f"  [Warning] Could not build power rangers: {e}")

    summary_path = os.path.join(SCRIPT_DIR, "countries.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({"countries": summaries}, f, indent=2, ensure_ascii=False)

    print("\n✅ Successfully generated all country addons!")
    for s in summaries:
        vpn_note = " (VPN needed outside country)" if s["vpn_required"] else ""
        print(f"  - {s['flag']} {s['name']}: {s['channel_count']} channels{vpn_note}")


if __name__ == "__main__":
    main()
