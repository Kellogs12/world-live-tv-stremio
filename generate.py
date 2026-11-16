#!/usr/bin/env python3
"""
Multi-Country Live TV Stremio Addon Generator
Modeled on the proven AU Live TV architecture (marvel-dc-stremio/livetv.py).
Reads sources.json, fetches & cleans M3U feeds and Spelunkr TV (spelunkr.tv/toonertia)
manifests, removes stale files, and builds static Stremio Addons.
"""

import concurrent.futures
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
    name = re.sub(r'\s*\[[^\]]*(Geo-blocked|Not 24/7)[^\]]*\]', '', name, flags=re.I)
    name = re.sub(r'\s*\((1080p|720p|576p|540p|480p|360p|240p)\)', '', name, flags=re.I)
    name = re.sub(r'\s+(via\s+\S+\s+)?(temp\s+)?find\b.*$', '', name, flags=re.I)
    name = re.sub(r'\s+via\s+\w+\s+source$', '', name, flags=re.I)
    name = re.sub(r'\s+alt$', '', name, flags=re.I)
    name = re.sub(r'\s+(alt\s+)?geo$', '', name, flags=re.I)
    name = re.sub(r'\s*\((australia|au|us|uk|ca|nz|substitute)\)', '', name, flags=re.I)
    return ' '.join(name.split())


def is_excluded_iptv_entry(entry):
    """Return True if an iptv-org entry is geo-blocked, non-24/7, radio, or explicit NSFW/adult."""
    raw_name = entry.get("name", "")
    grp = entry.get("group-title", "")
    if re.search(r'\[[^\]]*(Geo-blocked|Not 24/7)[^\]]*\]|\bradio\b', raw_name, re.I):
        return True
    if re.search(r'\b(xxx|porn|erotica|nsfw|hentai|18\+)\b|\badult\b(?!\s*(swim|animation|edu|learning))', f"{raw_name} {grp}", re.I):
        return True
    return False


def clean_xumo_url(url):
    """Strip expired session/IP parameters from Xumo URLs while keeping ads.xumo_channelId."""
    m = re.search(r'(ads\.xumo_channelId=\d+)', url)
    base = url.split('?')[0]
    return f"{base}?{m.group(1)}" if m else base


def parse_m3u(text):
    """Return [{'name', 'url', <tvg attributes>, optional 'http-user-agent'/'http-referrer'}] from an extended M3U playlist."""
    out, info = [], None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('#EXTINF:'):
            head, _, name = line[8:].partition(',')
            info = dict(re.findall(r'([\w-]+)="([^"]*)"', head))
            info['name'] = ' '.join(name.split())
        elif line.startswith('#EXTVLCOPT:') and info is not None:
            opt = line[11:].strip()
            if '=' in opt:
                k, _, v = opt.partition('=')
                k = k.strip().lower()
                if k in ('http-user-agent', 'http-referrer') and v.strip():
                    info[k] = v.strip()
        elif line and not line.startswith('#') and info is not None:
            if line.startswith('https://'):
                info['url'] = line
                out.append(info)
            info = None
    return out


def fetch_m3u(url, timeout=20):
    """Download and parse an M3U8 playlist with strict TLS verification."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (world-live-tv-stremio builder)'}
        )
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            content = resp.read().decode('utf-8', errors='replace')
        return parse_m3u(content)
    except Exception as e:
        print(f"  [Notice] Could not fetch M3U {url}: {e}")
        return []


def fetch_json_url(url, timeout=8, user_agent='Mozilla/5.0 (world-live-tv-stremio builder)'):
    """Fetch JSON from a URL with strict TLS verification."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={'User-Agent': user_agent})
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


def extract_req_headers(entry):
    """Build Stremio proxyHeaders.request dict from M3U #EXTVLCOPT fields."""
    headers = {}
    if entry.get("http-user-agent"):
        headers["User-Agent"] = entry["http-user-agent"]
    if entry.get("http-referrer"):
        headers["Referer"] = entry["http-referrer"]
    return headers


_STREAM_PROBE_CACHE = {}
_LOGO_PROBE_CACHE = {}


def probe_stream_url(url, req_headers=None, timeout=4.0):
    """Return True if stream URL responds with HTTP 200 and a valid HLS/DASH manifest."""
    headers = {"User-Agent": "Mozilla/5.0 (world-live-tv-stremio probe)"}
    if req_headers:
        headers.update(req_headers)
    req = urllib.request.Request(url, headers=headers)
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            if getattr(resp, "status", 200) >= 400:
                return False
            chunk = resp.read(512).decode("utf-8", errors="ignore")
            return "#EXTM3U" in chunk or "<MPD" in chunk
    except Exception:
        return False


def filter_live_streams(items, max_workers=80):
    """Concurrently probe M3U entries (cached & deduplicated) and keep reachable HLS/DASH streams."""
    if not items:
        return []
    keys = []
    uncached = {}
    for item in items:
        hdrs = extract_req_headers(item)
        key = (item["url"], tuple(sorted(hdrs.items())))
        keys.append(key)
        if key not in _STREAM_PROBE_CACHE and key not in uncached:
            uncached[key] = hdrs
    if uncached:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            fut_to_key = {
                pool.submit(probe_stream_url, k[0], hdrs): k
                for k, hdrs in uncached.items()
            }
            for fut in concurrent.futures.as_completed(fut_to_key):
                k = fut_to_key[fut]
                try:
                    _STREAM_PROBE_CACHE[k] = fut.result()
                except Exception:
                    _STREAM_PROBE_CACHE[k] = False
    return [item for item, k in zip(items, keys) if _STREAM_PROBE_CACHE.get(k, False)]


def probe_logo_url(url, timeout=3.0):
    """Return True if an HTTPS logo URL responds cleanly as an image."""
    if not url or not url.startswith("https://"):
        return False
    ctx = ssl.create_default_context()
    headers = {"User-Agent": "Mozilla/5.0 (world-live-tv-stremio logo check)"}
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                status = getattr(resp, "status", 200)
                if status >= 400:
                    return False
                ctype = (resp.headers.get("Content-Type") or "").lower() if resp.headers else ""
                if ctype.startswith("image/") or (not ctype and re.search(r'\.(png|jpe?g|webp|svg|gif)(\?|$)', url, re.I)):
                    return True
                return False
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code == 405:
                continue
            return False
        except Exception:
            return False
    return False


def validate_logos(urls, max_workers=80):
    """Concurrently validate unique HTTPS logo URLs into _LOGO_PROBE_CACHE."""
    pending = {u for u in urls if u and u.startswith("https://") and u not in _LOGO_PROBE_CACHE}
    if not pending:
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        fut_to_url = {pool.submit(probe_logo_url, u): u for u in pending}
        for fut in concurrent.futures.as_completed(fut_to_url):
            u = fut_to_url[fut]
            try:
                _LOGO_PROBE_CACHE[u] = fut.result()
            except Exception:
                _LOGO_PROBE_CACHE[u] = False


def build_stream_entries(ch_name, sources):
    """Build Stremio stream objects (native + browser HLS) for [(url, label, req_headers)]."""
    streams = []
    for idx, (url, label, req_headers) in enumerate(sources):
        lbl = label if idx == 0 else f"{label} #{idx + 1}"
        native = {"url": url, "name": lbl, "title": ch_name}
        if req_headers:
            native["behaviorHints"] = {"proxyHeaders": {"request": req_headers}}
        streams.append(native)

        if not url.lower().split("?")[0].endswith(".mpd"):
            hints = {"response": HLS_HINT["proxyHeaders"]["response"]}
            if req_headers:
                hints["request"] = req_headers
            streams.append({
                "url": url,
                "name": f"{lbl} (browser)",
                "title": f"{ch_name}\nFor Stremio Web without the streaming server",
                "behaviorHints": {"proxyHeaders": hints},
            })
    return streams


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
    m3u_cache = {}
    m3u_sources = country.get("m3u_sources", [])
    for src in m3u_sources:
        u = src["url"]
        if u not in m3u_cache:
            m3u_cache[u] = fetch_m3u(u)
            print(f"  Fetched {len(m3u_cache[u])} https channels from {u}")
        prefetched_m3u.append((src, m3u_cache[u]))

    # Preserve existing files on offline runs or when any source in a multi-source setup fails
    if m3u_sources and any(len(rl) == 0 for _, rl in prefetched_m3u) and os.path.exists(os.path.join(country_dir, "manifest.json")):
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
    norm_to_entry = {}

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

    def add_channel(cat_id, raw_id, ch_name, ch_url, ch_logo="", ch_desc="", custom_streams=None, source_label="Live", req_headers=None):
        if not custom_streams and (not ch_url or not (ch_url.startswith("https://") or ch_url.startswith("http://"))):
            return
        if re.search(r'\btest stream\b', ch_name, re.I):
            return
        if cat_id not in channels_by_cat:
            cat_id = default_cat_id
        norm_name = ch_name.casefold().strip()
        # Preserve legacy cartoon catalogs (cartoons-cn-disney, cartoons-nick, cartoons-classics) alongside featured ones
        norm_key = (cat_id, norm_name) if code == "cartoons" else norm_name
        if norm_key in norm_to_entry:
            existing = norm_to_entry[norm_key]
            if not existing.get("custom_streams") and ch_url:
                urls = {u for u, _, _ in existing["sources"]}
                if ch_url not in urls and len(existing["sources"]) < 5:
                    existing["sources"].append((ch_url, source_label, req_headers or {}))
            return

        uid = make_id(raw_id or ch_name)
        logo = ch_logo if (ch_logo and ch_logo.startswith("https://")) else icon_url
        desc_text = ch_desc or f"{ch_name} · Free live stream"
        entry = {
            "id": uid,
            "name": ch_name,
            "url": ch_url,
            "logo": logo,
            "description": desc_text,
            "sources": [(ch_url, source_label, req_headers or {})] if ch_url else [],
        }
        if custom_streams:
            entry["custom_streams"] = custom_streams
        norm_to_entry[norm_key] = entry
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
    fallbacks = country.get("fallback_channels", [])
    probe_live = ("--skip-probe" not in sys.argv) and (not country.get("vpn_required") or "--probe-all" in sys.argv)
    if probe_live and code not in ("cartoons", "marathons") and fallbacks:
        fb_candidates = [
            fb for fb in fallbacks
            if not fb.get("custom_streams")
            and fb.get("url", "").startswith("https://")
            and "archive.org" not in fb.get("url", "")
            and not fb.get("url", "").lower().split("?")[0].endswith(".mp4")
        ]
        if fb_candidates:
            reachable_fb = filter_live_streams(fb_candidates)
            print(f"    Probed fallback: {len(reachable_fb)}/{len(fb_candidates)} reachable streams")
            if reachable_fb:
                dead_urls = {fb["url"] for fb in fb_candidates} - {fb["url"] for fb in reachable_fb}
                fallbacks = [fb for fb in fallbacks if fb.get("url") not in dead_urls]
            else:
                print("    [Notice] Fallback probe returned 0 reachable; keeping configured fallbacks")

    for fb in fallbacks:
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
                ch_desc=fb.get("description") or f"{fb['name']} · Live TV",
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
            xumo_list = [dict(c, url=clean_xumo_url(c["url"])) for c in raw_list]
            if probe_live and xumo_list:
                probed = filter_live_streams(xumo_list)
                print(f"    Probed xumo: {len(probed)}/{len(xumo_list)} reachable streams")
                if probed:
                    xumo_list = probed
                else:
                    print("    [Notice] Xumo probe returned 0 reachable; keeping fetched list")
            for c in sorted(xumo_list, key=lambda x: clean_name(x["name"]).casefold()):
                cname = clean_name(c["name"])
                curl = c["url"]
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

        elif src_type == "iptv_org":
            name_filter = src.get("name_filter")
            candidates = []
            for c in raw_list:
                raw_name = c.get("name", "")
                if is_excluded_iptv_entry(c):
                    continue
                if name_filter and not (
                    re.search(name_filter, raw_name) or re.search(name_filter, c.get("group-title", ""))
                ):
                    continue
                candidates.append(c)
            if "--skip-probe" not in sys.argv:
                before = len(candidates)
                candidates = filter_live_streams(candidates)
                print(f"    Probed iptv-org: {len(candidates)}/{before} reachable streams")
            for c in sorted(candidates, key=lambda x: clean_name(x["name"]).casefold()):
                cname = clean_name(c["name"])
                grp = c.get("group-title", "").replace(";", ", ").strip()
                desc_str = f"Live TV ({grp}) · iptv-org" if grp else f"Live TV ({catalog_names.get(cat_id, name)}) · iptv-org"
                add_channel(
                    cat_id=cat_id,
                    raw_id="iptv-" + (c.get("tvg-id") or cname),
                    ch_name=cname,
                    ch_url=c["url"],
                    ch_logo=c.get("tvg-logo", ""),
                    ch_desc=desc_str,
                    source_label="iptv-org",
                    req_headers=extract_req_headers(c)
                )

        else:
            generic_list = list(raw_list)
            if probe_live and generic_list:
                probed = filter_live_streams(generic_list)
                print(f"    Probed {src_type}: {len(probed)}/{len(generic_list)} reachable streams")
                if probed:
                    generic_list = probed
                else:
                    print(f"    [Notice] {src_type} probe returned 0 reachable; keeping fetched list")
            for c in sorted(generic_list, key=lambda x: clean_name(x["name"]).casefold()):
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
    if "--skip-probe" not in sys.argv:
        logo_urls = [
            ch["logo"] for items in channels_by_cat.values() for ch in items
            if ch["logo"] and ch["logo"] != icon_url
        ]
        validate_logos(logo_urls)
        for items in channels_by_cat.values():
            for ch in items:
                if ch["logo"] != icon_url and not _LOGO_PROBE_CACHE.get(ch["logo"], False):
                    ch["logo"] = icon_url

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
                    "streams": build_stream_entries(ch["name"], ch["sources"])
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
            "configurationRequired": False,
            "adult": False
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


IPTV_ORG_COUNTRY_M3U = "https://iptv-org.github.io/iptv/index.country.m3u"

WORLD_LIVE_REGIONS = [
    ("au", "Australia"),
    ("nz", "New Zealand"),
    ("us", "United States"),
    ("uk", "United Kingdom"),
    ("ca", "Canada"),
    ("global", "Global"),
    ("sports", "Sports"),
    ("novelas", "Novelas"),
]


def build_world_live_addon(base_dir, regions=WORLD_LIVE_REGIONS, global_m3u_url=None):
    """Aggregate curated live regions + all reachable iptv-org countries into Discover-only world-live/."""
    wl_dir = os.path.join(base_dir, "world-live")
    cat_id = "world-live-channels"
    cat_dir = os.path.join(wl_dir, "catalog", "tv", cat_id)
    meta_dir = os.path.join(wl_dir, "meta", "tv")
    stream_dir = os.path.join(wl_dir, "stream", "tv")
    assets_dir = os.path.join(wl_dir, "assets")
    icon_url = f"{BASE_URL}/world-live/assets/icon.png"

    for stale in (os.path.join(wl_dir, "catalog"), meta_dir, stream_dir):
        if os.path.exists(stale):
            shutil.rmtree(stale)
    for d in (cat_dir, meta_dir, stream_dir, assets_dir):
        os.makedirs(d, exist_ok=True)
    if os.path.exists(ICON_FILE):
        shutil.copy(ICON_FILE, os.path.join(assets_dir, "icon.png"))

    country_entries = {}
    norm_lookup = {}
    used_ids = set()

    def unique_wl_id(raw_key):
        cid = f"tv-worldlive-{slug(raw_key)}"
        n, base = 2, cid
        while cid in used_ids:
            cid, n = f"{base}-{n}", n + 1
        used_ids.add(cid)
        return cid

    # 1. Load already-built curated regions from disk
    for code, label in regions:
        c_cat_dir = os.path.join(base_dir, code, "catalog", "tv")
        c_meta_dir = os.path.join(base_dir, code, "meta", "tv")
        c_stream_dir = os.path.join(base_dir, code, "stream", "tv")
        if not os.path.isdir(c_cat_dir):
            continue

        seen_orig = set()
        bucket = country_entries.setdefault(label, [])
        nmap = norm_lookup.setdefault(label, {})
        for fname in sorted(os.listdir(c_cat_dir)):
            if not fname.endswith(".json"):
                continue
            with open(os.path.join(c_cat_dir, fname), "r", encoding="utf-8") as cf:
                metas = json.load(cf).get("metas", [])
            for m in metas:
                orig_id = m.get("id")
                if not orig_id or orig_id in seen_orig:
                    continue
                seen_orig.add(orig_id)
                new_id = unique_wl_id(f"{code}-{orig_id}")
                poster = m.get("poster", "")
                if not poster.startswith("https://"):
                    poster = icon_url

                desc_text = m.get("description", f"{label} Live TV")
                meta_src = os.path.join(c_meta_dir, f"{orig_id}.json")
                if os.path.exists(meta_src):
                    with open(meta_src, "r", encoding="utf-8") as mf:
                        desc_text = json.load(mf).get("meta", {}).get("description", desc_text)

                streams_list = []
                stream_src = os.path.join(c_stream_dir, f"{orig_id}.json")
                if os.path.exists(stream_src):
                    with open(stream_src, "r", encoding="utf-8") as sf:
                        streams_list = json.load(sf).get("streams", [])

                ch_name = m.get("name", orig_id)
                rec = {
                    "id": new_id,
                    "name": ch_name,
                    "poster": poster,
                    "description": desc_text,
                    "streams": streams_list,
                }
                bucket.append(rec)
                nmap.setdefault(ch_name.casefold().strip(), rec)

    # 2. Ingest ALL countries from iptv-org index.country.m3u
    if global_m3u_url:
        raw_global = fetch_m3u(global_m3u_url, timeout=30)
        print(f"\nFetched {len(raw_global)} https channels from {global_m3u_url}")
        candidates = []
        filtered_out = 0
        for c in raw_global:
            grp = c.get("group-title", "").split(";")[0].strip()
            if not grp or grp.casefold() == "unknown" or is_excluded_iptv_entry(c):
                filtered_out += 1
                continue
            c["_country_label"] = "Global" if grp.casefold() == "international" else grp
            candidates.append(c)

        if "--skip-probe" not in sys.argv:
            reachable = filter_live_streams(candidates, max_workers=80)
            print(f"  Global iptv-org: {len(candidates)} clean ({filtered_out} geo/NSFW/radio/unknown excluded) -> {len(reachable)} reachable streams")
        else:
            reachable = candidates

        for c in sorted(reachable, key=lambda x: clean_name(x["name"]).casefold()):
            label = c["_country_label"]
            cname = clean_name(c["name"])
            bucket = country_entries.setdefault(label, [])
            nmap = norm_lookup.setdefault(label, {})
            nkey = cname.casefold().strip()
            req_hdrs = extract_req_headers(c)
            extra = build_stream_entries(cname, [(c["url"], "iptv-org", req_hdrs)])

            if nkey in nmap:
                existing_urls = {s.get("url") for s in nmap[nkey]["streams"] if s.get("url")}
                if c["url"] not in existing_urls and len(nmap[nkey]["streams"]) < 10:
                    nmap[nkey]["streams"].extend(extra)
                continue

            new_id = unique_wl_id(f"{label}-{c.get('tvg-id') or cname}")
            logo = c.get("tvg-logo", "")
            if not logo.startswith("https://"):
                logo = icon_url
            rec = {
                "id": new_id,
                "name": cname,
                "poster": logo,
                "description": f"Live TV ({label}) · iptv-org",
                "streams": extra,
            }
            bucket.append(rec)
            nmap[nkey] = rec

    # 3. Validate HTTPS logos across world-live before writing static JSONs
    if "--skip-probe" not in sys.argv:
        logo_candidates = [
            rec["poster"]
            for items in country_entries.values()
            for rec in items
            if rec["poster"] and rec["poster"] != icon_url
        ]
        unique_logos = {u for u in logo_candidates if u.startswith("https://")}
        validate_logos(unique_logos, max_workers=80)
        ok_logos = sum(1 for u in unique_logos if _LOGO_PROBE_CACHE.get(u, False))
        print(f"  Logo validation: {ok_logos}/{len(unique_logos)} reachable HTTPS logos (dead logos fallback to icon)")
        for items in country_entries.values():
            for rec in items:
                if rec["poster"] != icon_url and not _LOGO_PROBE_CACHE.get(rec["poster"], False):
                    rec["poster"] = icon_url

    # 4. Order genres: pinned regions first, then all remaining countries alphabetically
    pinned_labels = [label for _, label in regions]
    other_labels = sorted((l for l in country_entries if l not in pinned_labels), key=str.casefold)
    ordered_labels = [l for l in pinned_labels + other_labels if country_entries.get(l)]

    genre_options = []
    total_channels = 0
    for label in ordered_labels:
        items = country_entries[label]
        genre_options.append(label)
        total_channels += len(items)
        metas_out = []
        for rec in items:
            meta_obj = {
                "id": rec["id"],
                "type": "tv",
                "name": rec["name"],
                "poster": rec["poster"],
                "posterShape": "square",
                "logo": rec["poster"],
                "description": rec["description"],
                "genres": [label],
            }
            metas_out.append({k: meta_obj[k] for k in ("id", "type", "name", "poster", "posterShape", "description")})
            write_json(os.path.join(meta_dir, f"{rec['id']}.json"), {"meta": meta_obj})
            write_json(os.path.join(stream_dir, f"{rec['id']}.json"), {"streams": rec["streams"]})
        write_json(os.path.join(cat_dir, f"genre={label}.json"), {"metas": metas_out})

    manifest = {
        "id": "worldlive.world",
        "version": VERSION,
        "name": "🌍 World Live TV (by Country)",
        "description": "All live channels organized by country in Discover (keeps your Stremio main page clean).",
        "logo": icon_url,
        "resources": [
            "catalog",
            {"name": "meta", "types": ["tv"], "idPrefixes": ["tv-worldlive-"]},
            {"name": "stream", "types": ["tv"], "idPrefixes": ["tv-worldlive-"]},
        ],
        "types": ["tv"],
        "idPrefixes": ["tv-worldlive-"],
        "catalogs": [
            {
                "type": "tv",
                "id": cat_id,
                "name": "Live TV by Country",
                "extra": [
                    {
                        "name": "genre",
                        "options": genre_options,
                        "isRequired": True,
                    }
                ],
            }
        ],
        "behaviorHints": {
            "configurable": False,
            "configurationRequired": False,
            "adult": False,
        },
    }
    write_json(os.path.join(wl_dir, "manifest.json"), manifest)
    print(f"\nBuilt World Live TV (Discover by Country): {total_channels} channels across {len(genre_options)} countries/regions")
    return {
        "code": "world-live",
        "name": "World Live TV (By Country)",
        "flag": "🗺️",
        "region": "Global",
        "description": f"Unified Discover catalog sortable across {len(genre_options)} countries/regions without cluttering your Stremio Home Board.",
        "channel_count": total_channels,
        "vpn_required": False,
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
            if entry not in active_codes and entry not in ("cartoon-vault", "power-rangers", "world-live"):
                print(f"Removing retired country directory: {entry}")
                shutil.rmtree(full_p)

    countries = config.get("countries", [])
    print(f"Building Stremio Live TV Addons v{VERSION} for {len(countries)} countries...")

    summaries = []
    for c in countries:
        res = generate_addon_for_country(c, SCRIPT_DIR)
        summaries.append(res)

    summaries.append(build_world_live_addon(SCRIPT_DIR, global_m3u_url=IPTV_ORG_COUNTRY_M3U))

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
