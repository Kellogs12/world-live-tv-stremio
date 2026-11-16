import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

import generate


class _DummyResp(io.BytesIO):
    def __init__(self, body: bytes, status: int = 200):
        super().__init__(body)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


SAMPLE_M3U = """#EXTM3U
#EXTINF:-1 tvg-id="Alpha.ca" tvg-logo="https://example.com/a.png" group-title="News",Alpha News (1080p)
#EXTVLCOPT:http-user-agent=CustomUA/1.0
#EXTVLCOPT:http-referrer=https://ref.example.com/
https://cdn.example.com/alpha/master.m3u8
#EXTINF:-1 tvg-id="Blocked.ca" group-title="General",Blocked TV [Geo-blocked]
https://cdn.example.com/blocked.m3u8
#EXTINF:-1 tvg-id="Insecure.ca" group-title="General",Insecure TV
http://cdn.example.com/insecure.m3u8
#EXTINF:-1 tvg-id="Dash.ca" group-title="Business",Dash TV (720p)
https://cdn.example.com/dash/manifest.mpd
"""


class TestIptvOrgIntegration(unittest.TestCase):
    def test_parse_m3u_extracts_vlcopt_and_enforces_https(self):
        parsed = generate.parse_m3u(SAMPLE_M3U)
        self.assertEqual(len(parsed), 3)
        self.assertEqual(parsed[0]["http-user-agent"], "CustomUA/1.0")
        self.assertEqual(parsed[0]["http-referrer"], "https://ref.example.com/")
        self.assertNotIn("Insecure TV", [p["name"] for p in parsed])

    def test_clean_name_strips_iptv_org_tags(self):
        self.assertEqual(generate.clean_name("Alpha News (1080p) [Not 24/7]"), "Alpha News")
        self.assertEqual(generate.clean_name("Beta TV [Geo-blocked] (720p)"), "Beta TV")

    def test_build_stream_entries_headers_and_mpd(self):
        streams = generate.build_stream_entries("Alpha News", [
            ("https://primary.example.com/live.m3u8", "Live", {}),
            ("https://backup.example.com/live.m3u8", "iptv-org", {"User-Agent": "UA", "Referer": "https://r.example"}),
            ("https://dash.example.com/manifest.mpd", "iptv-org", {}),
        ])
        # Primary + browser, Backup + browser, DASH (no browser HLS hint) = 5 streams
        self.assertEqual(len(streams), 5)
        self.assertEqual(streams[2]["behaviorHints"]["proxyHeaders"]["request"]["User-Agent"], "UA")
        self.assertEqual(streams[3]["behaviorHints"]["proxyHeaders"]["response"]["content-type"], "application/vnd.apple.mpegurl")
        self.assertNotIn("behaviorHints", streams[4])

    def test_generate_merges_duplicate_names_and_filters_geoblocked(self):
        country = {
            "code": "ca",
            "name": "Canada",
            "flag": "🇨🇦",
            "region": "Americas",
            "catalogs": [
                {"id": "ca-news", "name": "News"},
                {"id": "ca-iptv", "name": "Canada Live TV (iptv-org)"},
            ],
            "fallback_channels": [
                {"id": "alpha", "name": "Alpha News", "catalog": "ca-news", "url": "https://primary.example.com/a.m3u8"}
            ],
            "m3u_sources": [
                {"url": "https://iptv-org.github.io/iptv/countries/ca.m3u", "catalog": "ca-iptv", "type": "iptv_org"}
            ],
        }
        parsed = generate.parse_m3u(SAMPLE_M3U)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(generate, "fetch_m3u", return_value=parsed), \
                 patch.object(generate, "filter_live_streams", side_effect=lambda items: items):
                summary = generate.generate_addon_for_country(country, tmpdir)

            # Alpha News merged into ca-news; Dash TV added to ca-iptv; Blocked TV filtered out
            self.assertEqual(summary["channel_count"], 2)
            with open(os.path.join(tmpdir, "ca", "stream", "tv", "tv-ca-alpha.json"), "r", encoding="utf-8") as f:
                alpha_streams = json.load(f)["streams"]
            urls = [s["url"] for s in alpha_streams]
            self.assertIn("https://primary.example.com/a.m3u8", urls)
            self.assertIn("https://cdn.example.com/alpha/master.m3u8", urls)

    def test_probe_stream_url_and_clean_xumo_url(self):
        with patch("urllib.request.urlopen", return_value=_DummyResp(b"#EXTM3U\n#EXT-X-VERSION:3")):
            self.assertTrue(generate.probe_stream_url("https://example.com/live.m3u8"))
        with patch("urllib.request.urlopen", return_value=_DummyResp(b"<html>403 Forbidden</html>")):
            self.assertFalse(generate.probe_stream_url("https://example.com/bad.m3u8"))
        with patch("urllib.request.urlopen", side_effect=OSError("timeout")):
            self.assertFalse(generate.probe_stream_url("https://example.com/down.m3u8"))

        cleaned = generate.clean_xumo_url("https://cdn.example.com/hls/master.m3u8?token=abc&ads.xumo_channelId=99991247&ip=1.2.3.4")
        self.assertEqual(cleaned, "https://cdn.example.com/hls/master.m3u8?ads.xumo_channelId=99991247")

    def test_partial_m3u_outage_preserves_existing_country(self):
        country = {
            "code": "us",
            "name": "United States",
            "flag": "🇺🇸",
            "region": "Americas",
            "catalogs": [{"id": "us-xumo", "name": "Xumo"}],
            "m3u_sources": [
                {"url": "https://down.example.com/xumo.m3u", "catalog": "us-xumo", "type": "xumo"},
                {"url": "https://up.example.com/us.m3u", "catalog": "us-iptv", "type": "iptv_org"},
            ],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            us_dir = os.path.join(tmpdir, "us")
            os.makedirs(os.path.join(us_dir, "catalog", "tv"), exist_ok=True)
            generate.write_json(os.path.join(us_dir, "manifest.json"), {"id": "worldlive.us"})
            generate.write_json(os.path.join(us_dir, "catalog", "tv", "us-xumo.json"), {
                "metas": [{"id": "tv-us-1"}, {"id": "tv-us-2"}]
            })
            with patch.object(generate, "fetch_m3u", side_effect=[[], [{"name": "New", "url": "https://ok.example/a.m3u8"}]]):
                summary = generate.generate_addon_for_country(country, tmpdir)
            self.assertEqual(summary["channel_count"], 2)
            self.assertTrue(os.path.exists(os.path.join(us_dir, "catalog", "tv", "us-xumo.json")))

    def test_build_world_live_addon_genre_slices_and_index_filter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            au_cat = os.path.join(tmpdir, "au", "catalog", "tv")
            au_meta = os.path.join(tmpdir, "au", "meta", "tv")
            au_stream = os.path.join(tmpdir, "au", "stream", "tv")
            generate.write_json(os.path.join(au_cat, "au-fta.json"), {
                "metas": [{"id": "tv-au-abc", "type": "tv", "name": "ABC TV", "poster": "http://insecure.example/logo.png", "posterShape": "square", "description": "ABC"}]
            })
            generate.write_json(os.path.join(au_meta, "tv-au-abc.json"), {"meta": {"description": "ABC Full"}})
            generate.write_json(os.path.join(au_stream, "tv-au-abc.json"), {"streams": [{"url": "https://abc.example/live.m3u8", "name": "Live", "title": "ABC"}]})

            summary = generate.build_world_live_addon(tmpdir, regions=[("au", "Australia")])
            self.assertEqual(summary["channel_count"], 1)
            with open(os.path.join(tmpdir, "world-live", "manifest.json"), "r", encoding="utf-8") as mf:
                manifest = json.load(mf)
            self.assertEqual(manifest["idPrefixes"], ["tv-worldlive-"])
            self.assertFalse(manifest["behaviorHints"]["adult"])
            extra = manifest["catalogs"][0]["extra"][0]
            self.assertTrue(extra["isRequired"])
            self.assertEqual(extra["options"], ["Australia"])

            genre_path = os.path.join(tmpdir, "world-live", "catalog", "tv", "world-live-channels", "genre=Australia.json")
            self.assertTrue(os.path.exists(genre_path))
            with open(genre_path, "r", encoding="utf-8") as gf:
                metas = json.load(gf)["metas"]
            self.assertTrue(metas[0]["poster"].startswith("https://"))

        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "index.html"), "r", encoding="utf-8") as hf:
            html = hf.read()
        self.assertIn('data-filter="Marathons"', html)

    def test_global_country_grouping_nsfw_and_logo_fallback(self):
        self.assertTrue(generate.is_excluded_iptv_entry({"name": "Canal [Not 24/7;Geo-blocked]", "group-title": "France"}))
        self.assertTrue(generate.is_excluded_iptv_entry({"name": "Spicy TV", "group-title": "XXX"}))
        self.assertFalse(generate.is_excluded_iptv_entry({"name": "Pluto TV Adult Animation", "group-title": "Germany"}))

        global_entries = [
            {"name": "ZDF", "group-title": "Germany", "tvg-logo": "https://ok.example/zdf.png", "url": "https://cdn.example/zdf.m3u8"},
            {"name": "NHK World", "group-title": "Japan", "tvg-logo": "https://dead.example/404.png", "url": "https://cdn.example/nhk.m3u8"},
            {"name": "Adult Only", "group-title": "XXX", "tvg-logo": "", "url": "https://cdn.example/xxx.m3u8"},
            {"name": "Intl Feed", "group-title": "International", "tvg-logo": "", "url": "https://cdn.example/intl.m3u8"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            au_cat = os.path.join(tmpdir, "au", "catalog", "tv")
            generate.write_json(os.path.join(au_cat, "au-fta.json"), {
                "metas": [{"id": "tv-au-abc", "type": "tv", "name": "ABC TV", "poster": "https://ok.example/abc.png", "posterShape": "square", "description": "ABC"}]
            })

            def fake_logo_probe(u, timeout=3.0):
                return "dead.example" not in u

            with patch.object(generate, "fetch_m3u", return_value=global_entries), \
                 patch.object(generate, "filter_live_streams", side_effect=lambda items, max_workers=80: items), \
                 patch.object(generate, "probe_logo_url", side_effect=fake_logo_probe):
                generate._LOGO_PROBE_CACHE.clear()
                summary = generate.build_world_live_addon(
                    tmpdir,
                    regions=[("au", "Australia"), ("global", "Global")],
                    global_m3u_url="https://iptv-org.github.io/iptv/index.country.m3u",
                )

            self.assertEqual(summary["channel_count"], 4)
            with open(os.path.join(tmpdir, "world-live", "manifest.json"), "r", encoding="utf-8") as mf:
                opts = json.load(mf)["catalogs"][0]["extra"][0]["options"]
            # Pinned regions first (Australia, Global), then alphabetical (Germany, Japan)
            self.assertEqual(opts, ["Australia", "Global", "Germany", "Japan"])
            with open(os.path.join(tmpdir, "world-live", "catalog", "tv", "world-live-channels", "genre=Japan.json"), "r", encoding="utf-8") as jf:
                nhk = json.load(jf)["metas"][0]
            self.assertEqual(nhk["poster"], f"{generate.BASE_URL}/world-live/assets/icon.png")


if __name__ == "__main__":
    unittest.main()
