#!/usr/bin/env python3
"""
Unit and integration test suite for 24/7 Marathons & Archive TV Stremio Addon.
Verifies manifest, 7 aesthetic catalogs, 30 channels, meta/stream files, and countries.json integration.
"""

import json
import os
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
MARATHONS_DIR = os.path.join(PROJECT_DIR, "marathons")


class TestMarathons(unittest.TestCase):

    def setUp(self):
        self.manifest_path = os.path.join(MARATHONS_DIR, "manifest.json")
        self.catalog_dir = os.path.join(MARATHONS_DIR, "catalog", "tv")
        self.meta_dir = os.path.join(MARATHONS_DIR, "meta", "tv")
        self.stream_dir = os.path.join(MARATHONS_DIR, "stream", "tv")
        self.countries_path = os.path.join(PROJECT_DIR, "countries.json")

    def test_manifest_schema(self):
        self.assertTrue(os.path.exists(self.manifest_path), "marathons/manifest.json must exist")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest.get("id"), "worldlive.marathons")
        self.assertEqual(manifest.get("name"), "📼 24/7 Marathons & Archive TV")
        self.assertEqual(manifest.get("types"), ["tv"])
        self.assertEqual(manifest.get("idPrefixes"), ["tv-marathons-"])

        resources = manifest.get("resources", [])
        self.assertIn("catalog", resources)
        meta_res = next((r for r in resources if isinstance(r, dict) and r.get("name") == "meta"), None)
        self.assertIsNotNone(meta_res)
        self.assertEqual(meta_res.get("types"), ["tv"])
        self.assertEqual(meta_res.get("idPrefixes"), ["tv-marathons-"])

        stream_res = next((r for r in resources if isinstance(r, dict) and r.get("name") == "stream"), None)
        self.assertIsNotNone(stream_res)
        self.assertEqual(stream_res.get("types"), ["tv"])
        self.assertEqual(stream_res.get("idPrefixes"), ["tv-marathons-"])

        catalogs = manifest.get("catalogs", [])
        self.assertEqual(len(catalogs), 7, "Expected 7 aesthetic catalogs for marathons")
        cat_ids = [c["id"] for c in catalogs]
        self.assertEqual(cat_ids, [
            "marathons-toonami-anime",
            "marathons-cult-scifi",
            "marathons-classic-tv",
            "marathons-crime-mystery",
            "marathons-space-ambience",
            "marathons-westerns",
            "marathons-music-tv"
        ])

    def test_catalog_files_and_channels(self):
        expected_catalogs = [
            ("marathons-toonami-anime", "Toonami & Retro Anime 24/7", 6),
            ("marathons-cult-scifi", "Cult Sci-Fi, B-Movies & Mystery", 5),
            ("marathons-classic-tv", "Classic Sitcoms & Golden Age TV", 6),
            ("marathons-crime-mystery", "True Crime & Detective Marathons", 5),
            ("marathons-space-ambience", "Space, Nature & Ambient Relaxation", 2),
            ("marathons-westerns", "Westerns & Frontier Classics", 2),
            ("marathons-music-tv", "24/7 Music Video Television", 4)
        ]

        total_channels = 0
        all_channel_ids = set()

        for cat_id, cat_name, expected_count in expected_catalogs:
            cat_file = os.path.join(self.catalog_dir, f"{cat_id}.json")
            self.assertTrue(os.path.exists(cat_file), f"Catalog file missing: {cat_file}")
            with open(cat_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            metas = data.get("metas", [])
            self.assertEqual(len(metas), expected_count, f"Channel count mismatch for {cat_id}")
            total_channels += len(metas)

            for m in metas:
                cid = m["id"]
                self.assertTrue(cid.startswith("tv-marathons-"), f"Invalid ID prefix: {cid}")
                self.assertEqual(m["type"], "tv")
                self.assertTrue(bool(m["name"]), f"Missing channel name: {cid}")
                self.assertTrue(bool(m["poster"]), f"Missing poster: {cid}")
                self.assertEqual(m["posterShape"], "square")
                self.assertTrue(bool(m.get("description")), f"Missing description: {cid}")
                all_channel_ids.add(cid)

        self.assertEqual(total_channels, 30)
        self.assertEqual(len(all_channel_ids), 30, "Duplicate channels found across catalogs")

    def test_meta_and_streams(self):
        stream_files = [f for f in os.listdir(self.stream_dir) if f.endswith(".json")]
        meta_files = [f for f in os.listdir(self.meta_dir) if f.endswith(".json")]

        self.assertEqual(len(stream_files), 30)
        self.assertEqual(len(meta_files), 30)

        for sf in stream_files:
            stream_path = os.path.join(self.stream_dir, sf)
            meta_path = os.path.join(self.meta_dir, sf)
            self.assertTrue(os.path.exists(meta_path), f"Matching meta missing for {sf}")

            with open(stream_path, "r", encoding="utf-8") as f:
                s_data = json.load(f)
            streams = s_data.get("streams", [])
            self.assertGreaterEqual(len(streams), 1, f"No streams in {sf}")
            for st in streams:
                if "url" in st:
                    self.assertTrue(st["url"].startswith("http://") or st["url"].startswith("https://"),
                                    f"Invalid stream URL protocol in {sf}: {st['url']}")

    def test_countries_json_integration(self):
        self.assertTrue(os.path.exists(self.countries_path))
        with open(self.countries_path, "r", encoding="utf-8") as f:
            c_data = json.load(f)

        countries = c_data.get("countries", [])
        m_entry = next((c for c in countries if c.get("code") == "marathons"), None)
        self.assertIsNotNone(m_entry, "marathons entry missing in countries.json")
        self.assertEqual(m_entry.get("channel_count"), 30)
        self.assertEqual(m_entry.get("flag"), "📼")
        self.assertFalse(m_entry.get("vpn_required"))


if __name__ == "__main__":
    unittest.main()
