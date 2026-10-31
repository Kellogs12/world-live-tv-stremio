#!/usr/bin/env python3
"""
Unit and integration test suite for Cartoon & Animation Vault Stremio Addon.
Verifies catalogs, schemas, Cinemeta cache, Robotboy inclusion, and no regressions.
"""

import json
import os
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
VAULT_DIR = os.path.join(PROJECT_DIR, "cartoon-vault")


class TestCartoonVault(unittest.TestCase):

    def setUp(self):
        self.manifest_path = os.path.join(VAULT_DIR, "manifest.json")
        self.cache_path = os.path.join(VAULT_DIR, "catalog_cache.json")
        self.countries_path = os.path.join(PROJECT_DIR, "countries.json")
        self.readme_path = os.path.join(PROJECT_DIR, "README.md")

    def test_manifest_schema(self):
        self.assertTrue(os.path.exists(self.manifest_path), "manifest.json must exist")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest.get("id"), "worldlive.cartoonvault")
        self.assertIn("Cartoon & Animation Vault", manifest.get("name", ""))
        self.assertIn("catalog", manifest.get("resources", []))
        self.assertIn("series", manifest.get("types", []))
        self.assertIn("movie", manifest.get("types", []))
        self.assertIn("tt", manifest.get("idPrefixes", []))

        catalogs = manifest.get("catalogs", [])
        self.assertEqual(len(catalogs), 6, "Expected exactly 6 catalogs")
        cat_ids = [c["id"] for c in catalogs]
        expected_cat_ids = [
            "cn-shows", "disney-shows", "nick-shows",
            "classics-shows", "action-shows", "cartoon-movies"
        ]
        self.assertEqual(cat_ids, expected_cat_ids)

    def test_catalog_files_and_schema(self):
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        catalogs = manifest.get("catalogs", [])
        total_items = 0

        for cat in catalogs:
            cat_id = cat["id"]
            cat_type = cat["type"]

            # Route 1: catalog/{type}/{id}.json
            route1 = os.path.join(VAULT_DIR, "catalog", cat_type, f"{cat_id}.json")
            self.assertTrue(os.path.exists(route1), f"Route 1 missing: {route1}")
            with open(route1, "r", encoding="utf-8") as f:
                data1 = json.load(f)
            metas1 = data1.get("metas", [])
            self.assertGreater(len(metas1), 0, f"Empty catalog: {cat_id}")

            # Route 2: catalog/{type}/{id}/skip=0.json
            route2 = os.path.join(VAULT_DIR, "catalog", cat_type, cat_id, "skip=0.json")
            self.assertTrue(os.path.exists(route2), f"Route 2 missing: {route2}")
            with open(route2, "r", encoding="utf-8") as f:
                data2 = json.load(f)
            metas2 = data2.get("metas", [])
            self.assertEqual(len(metas1), len(metas2), f"Mismatch between base and skip=0 for {cat_id}")

            # Route 3: catalog/{type}/{id}/skip=100.json
            route3 = os.path.join(VAULT_DIR, "catalog", cat_type, cat_id, "skip=100.json")
            self.assertTrue(os.path.exists(route3), f"Route 3 missing: {route3}")
            with open(route3, "r", encoding="utf-8") as f:
                data3 = json.load(f)
            self.assertEqual(data3.get("metas"), [], f"skip=100 should be empty list for {cat_id}")

            # Validate each meta
            for m in metas1:
                self.assertTrue(m["id"].startswith("tt"), f"Invalid ID format: {m.get('id')}")
                self.assertEqual(m["type"], cat_type)
                self.assertTrue(bool(m.get("name")), f"Missing name: {m}")
                self.assertTrue(bool(m.get("poster")), f"Missing poster: {m.get('name')}")
                self.assertTrue(m["poster"].startswith("http"), f"Invalid poster url: {m.get('poster')}")
                self.assertEqual(m.get("posterShape"), "poster")
                self.assertTrue(isinstance(m.get("genres"), list) and len(m["genres"]) > 0)
                self.assertTrue(bool(m.get("description")), f"Missing description: {m.get('name')}")

            total_items += len(metas1)

        self.assertEqual(total_items, 460, f"Expected 460 total items, got {total_items}")

    def test_robotboy_presence_and_metadata(self):
        cn_route = os.path.join(VAULT_DIR, "catalog", "series", "cn-shows.json")
        with open(cn_route, "r", encoding="utf-8") as f:
            data = json.load(f)

        robotboy_items = [m for m in data.get("metas", []) if m.get("id") == "tt0482870"]
        self.assertEqual(len(robotboy_items), 1, "Robotboy (tt0482870) must be present in cn-shows")

        rb = robotboy_items[0]
        self.assertEqual(rb["name"], "Robotboy")
        self.assertEqual(rb["type"], "series")
        self.assertEqual(rb["releaseInfo"], "2005–2008")
        self.assertEqual(rb["imdbRating"], "5.8")
        self.assertIn("Professor Moshimo", rb["description"])
        self.assertTrue(rb["poster"].startswith("http"))

    def test_genz_1999_era_shows_presence(self):
        expected_by_cat = {
            ("series", "cn-shows"): ["tt0454349", "tt1114855", "tt1871731", "tt2130507", "tt1402156"],
            ("series", "disney-shows"): ["tt0272388", "tt1725902", "tt1307224", "tt1387904"],
            ("series", "nick-shows"): ["tt1492090", "tt0421482", "tt0439349", "tt0235917"],
            ("series", "classics-shows"): ["tt0780438", "tt1470837", "tt0280277", "tt0213363", "tt0983983", "tt0224455"],
            ("series", "action-shows"): ["tt0249327", "tt1196094", "tt0210418", "tt1674928", "tt0409591", "tt1659175"],
            ("movie", "cartoon-movies"): ["tt0253658", "tt0290057", "tt0357139", "tt0190641", "tt0259974", "tt0317705"]
        }
        for (cat_type, cat_id), req_ids in expected_by_cat.items():
            route = os.path.join(VAULT_DIR, "catalog", cat_type, f"{cat_id}.json")
            with open(route, "r", encoding="utf-8") as f:
                data = json.load(f)
            present_ids = {m["id"] for m in data.get("metas", [])}
            for rid in req_ids:
                self.assertIn(rid, present_ids, f"Expected 1999 Gen Z ID {rid} in {cat_id}")

    def test_no_duplicate_titles_across_catalogs(self):
        import sys
        sys.path.insert(0, PROJECT_DIR)
        from build_cartoon_vault import SHOW_DEFINITIONS

        all_ids = []
        for cat, items in SHOW_DEFINITIONS.items():
            ids = [i[0] for i in items]
            self.assertEqual(len(ids), len(set(ids)), f"Duplicate IDs within catalog: {cat}")
            all_ids.extend(ids)

        self.assertEqual(len(all_ids), len(set(all_ids)), "Duplicate IDs found across different catalogs")
        self.assertEqual(len(all_ids), 460)

    def test_countries_json_and_readme(self):
        with open(self.countries_path, "r", encoding="utf-8") as f:
            countries_data = json.load(f)

        vault_entries = [c for c in countries_data.get("countries", []) if c.get("code") == "cartoon-vault"]
        self.assertEqual(len(vault_entries), 1, "cartoon-vault must be listed in countries.json")
        entry = vault_entries[0]
        self.assertEqual(entry.get("channel_count"), 460)
        self.assertEqual(entry.get("item_count"), 460)

        with open(self.readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()

        self.assertIn("Robotboy", readme_text)
        self.assertIn("460 iconic and cult-classic animated series and specials", readme_text)


if __name__ == "__main__":
    unittest.main()
