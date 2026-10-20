#!/usr/bin/env python3
"""
Unit and integration test suite for Telenovelas Live 24/7 Stremio Addon.
Verifies manifest, catalogs, dual streams, HLS headers, and countries.json integration.
"""

import json
import os
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
NOVELAS_DIR = os.path.join(PROJECT_DIR, "novelas")


class TestNovelas(unittest.TestCase):

    def setUp(self):
        self.manifest_path = os.path.join(NOVELAS_DIR, "manifest.json")
        self.catalog_dir = os.path.join(NOVELAS_DIR, "catalog", "tv")
        self.meta_dir = os.path.join(NOVELAS_DIR, "meta", "tv")
        self.stream_dir = os.path.join(NOVELAS_DIR, "stream", "tv")
        self.countries_path = os.path.join(PROJECT_DIR, "countries.json")

    def test_manifest_schema(self):
        self.assertTrue(os.path.exists(self.manifest_path), "novelas/manifest.json must exist")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest.get("id"), "worldlive.novelas")
        self.assertEqual(manifest.get("name"), "🎭 Telenovelas Live 24/7")
        self.assertEqual(manifest.get("types"), ["tv"])
        self.assertEqual(manifest.get("idPrefixes"), ["tv-novelas-"])

        # Check resources
        resources = manifest.get("resources", [])
        self.assertIn("catalog", resources)
        meta_res = next((r for r in resources if isinstance(r, dict) and r.get("name") == "meta"), None)
        self.assertIsNotNone(meta_res)
        self.assertEqual(meta_res.get("types"), ["tv"])
        self.assertEqual(meta_res.get("idPrefixes"), ["tv-novelas-"])

        stream_res = next((r for r in resources if isinstance(r, dict) and r.get("name") == "stream"), None)
        self.assertIsNotNone(stream_res)
        self.assertEqual(stream_res.get("types"), ["tv"])
        self.assertEqual(stream_res.get("idPrefixes"), ["tv-novelas-"])

        # Check catalogs
        catalogs = manifest.get("catalogs", [])
        self.assertEqual(len(catalogs), 3, "Expected 3 catalogs for novelas")
        cat_ids = [c["id"] for c in catalogs]
        self.assertEqual(cat_ids, [
            "novelas-clasicas",
            "novelas-telemundo-univision",
            "novelas-internacionales"
        ])

    def test_catalog_files_and_channels(self):
        catalogs = [
            ("novelas-clasicas", "Telenovelas Clásicas", 4),
            ("novelas-telemundo-univision", "Telemundo & Univision Hits", 3),
            ("novelas-internacionales", "Novelas Internacionales", 2)
        ]

        total_channels = 0
        all_channel_ids = set()

        for cat_id, cat_name, expected_count in catalogs:
            cat_file = os.path.join(self.catalog_dir, f"{cat_id}.json")
            self.assertTrue(os.path.exists(cat_file), f"Catalog file missing: {cat_file}")
            with open(cat_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            metas = data.get("metas", [])
            self.assertEqual(len(metas), expected_count, f"Channel count mismatch for {cat_id}")
            total_channels += len(metas)

            for m in metas:
                cid = m["id"]
                self.assertTrue(cid.startswith("tv-novelas-"), f"Invalid ID: {cid}")
                self.assertEqual(m["type"], "tv")
                self.assertTrue(bool(m["name"]), f"Missing channel name: {cid}")
                self.assertTrue(bool(m["poster"]), f"Missing poster: {cid}")
                self.assertEqual(m["posterShape"], "square")
                all_channel_ids.add(cid)

        self.assertEqual(total_channels, 9)
        self.assertEqual(len(all_channel_ids), 9, "Duplicate channels found across catalogs")

    def test_meta_and_dual_streams(self):
        stream_files = [f for f in os.listdir(self.stream_dir) if f.endswith(".json")]
        meta_files = [f for f in os.listdir(self.meta_dir) if f.endswith(".json")]

        self.assertEqual(len(stream_files), 9)
        self.assertEqual(len(meta_files), 9)

        for sf in stream_files:
            stream_path = os.path.join(self.stream_dir, sf)
            meta_path = os.path.join(self.meta_dir, sf)
            self.assertTrue(os.path.exists(meta_path), f"Matching meta missing for {sf}")

            with open(stream_path, "r", encoding="utf-8") as f:
                stream_data = json.load(f)
            streams = stream_data.get("streams", [])
            self.assertEqual(len(streams), 2, f"Expected exactly 2 streams for {sf}")

            # Stream 1: Live
            s1 = streams[0]
            self.assertEqual(s1.get("name"), "Live")
            self.assertTrue(s1.get("url", "").startswith("https://"))
            self.assertTrue(bool(s1.get("title")))

            # Stream 2: Live (browser)
            s2 = streams[1]
            self.assertEqual(s2.get("name"), "Live (browser)")
            self.assertEqual(s2.get("url"), s1.get("url"))
            self.assertIn("For Stremio Web", s2.get("title", ""))

            hints = s2.get("behaviorHints", {})
            proxy_headers = hints.get("proxyHeaders", {})
            response_headers = proxy_headers.get("response", {})
            self.assertEqual(
                response_headers.get("content-type"),
                "application/vnd.apple.mpegurl",
                f"Missing or invalid HLS content-type proxyHeader in {sf}"
            )

    def test_countries_json_entry(self):
        with open(self.countries_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        novelas_entries = [c for c in data.get("countries", []) if c.get("code") == "novelas"]
        self.assertEqual(len(novelas_entries), 1, "novelas must be listed in countries.json")
        entry = novelas_entries[0]
        self.assertEqual(entry.get("name"), "Telenovelas Live 24/7")
        self.assertEqual(entry.get("channel_count"), 9)
        self.assertFalse(entry.get("vpn_required"))


if __name__ == "__main__":
    unittest.main()
