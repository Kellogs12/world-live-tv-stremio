#!/usr/bin/env python3
"""
Unit and integration test suite for Power Rangers Universe Stremio Addon.
Verifies manifest, catalogs, static routes, Cinemeta cache, and no regressions.
"""

import json
import os
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
PR_DIR = os.path.join(PROJECT_DIR, "power-rangers")


class TestPowerRangers(unittest.TestCase):

    def setUp(self):
        self.manifest_path = os.path.join(PR_DIR, "manifest.json")
        self.cache_path = os.path.join(PR_DIR, "catalog_cache.json")
        self.countries_path = os.path.join(PROJECT_DIR, "countries.json")
        self.readme_path = os.path.join(PROJECT_DIR, "README.md")

    def test_manifest_schema(self):
        self.assertTrue(os.path.exists(self.manifest_path), "manifest.json must exist")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest.get("id"), "worldlive.powerrangers")
        self.assertEqual(manifest.get("name"), "⚡ Power Rangers Universe")
        self.assertTrue(any(
            r == "catalog" or (isinstance(r, dict) and r.get("name") == "catalog")
            for r in manifest.get("resources", [])
        ))
        meta_res = next(
            (r for r in manifest.get("resources", []) if isinstance(r, dict) and r.get("name") == "meta"),
            None
        )
        self.assertIsNotNone(meta_res, "meta resource dict must exist")
        self.assertNotIn("tt", meta_res.get("idPrefixes", []), "meta resource idPrefixes must not use catch-all 'tt'")
        self.assertEqual(len(meta_res.get("idPrefixes", [])), 29, "meta resource idPrefixes must list the 29 PR IMDb IDs")
        self.assertIn("series", manifest.get("types", []))
        self.assertIn("movie", manifest.get("types", []))
        self.assertIn("tt", manifest.get("idPrefixes", []))

        catalogs = manifest.get("catalogs", [])
        self.assertEqual(len(catalogs), 6, "Expected exactly 6 catalogs")
        cat_ids = [c["id"] for c in catalogs]
        expected_cat_ids = [
            "pr-chronological",
            "pr-saban-era",
            "pr-disney-era",
            "pr-neosaban-era",
            "pr-hasbro-era",
            "pr-movies"
        ]
        self.assertEqual(cat_ids, expected_cat_ids)

    def test_catalog_routes_and_schema(self):
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        catalogs = manifest.get("catalogs", [])

        for cat in catalogs:
            cat_id = cat["id"]
            cat_type = cat["type"]

            # Route 1: catalog/{type}/{id}.json
            route1 = os.path.join(PR_DIR, "catalog", cat_type, f"{cat_id}.json")
            self.assertTrue(os.path.exists(route1), f"Route 1 missing: {route1}")
            with open(route1, "r", encoding="utf-8") as f:
                data1 = json.load(f)
            metas1 = data1.get("metas", [])
            self.assertGreater(len(metas1), 0, f"Empty catalog: {cat_id}")

            # Route 2: catalog/{type}/{id}/skip=0.json
            route2 = os.path.join(PR_DIR, "catalog", cat_type, cat_id, "skip=0.json")
            self.assertTrue(os.path.exists(route2), f"Route 2 missing: {route2}")
            with open(route2, "r", encoding="utf-8") as f:
                data2 = json.load(f)
            metas2 = data2.get("metas", [])
            self.assertEqual(len(metas1), len(metas2), f"Mismatch between base and skip=0 for {cat_id}")

            # Route 3: catalog/{type}/{id}/skip=100.json
            route3 = os.path.join(PR_DIR, "catalog", cat_type, cat_id, "skip=100.json")
            self.assertTrue(os.path.exists(route3), f"Route 3 missing: {route3}")
            with open(route3, "r", encoding="utf-8") as f:
                data3 = json.load(f)
            self.assertEqual(data3.get("metas"), [], f"skip=100 should be empty list for {cat_id}")

            # Validate metadata fields
            for m in metas1:
                self.assertTrue(m["id"].startswith("tt"), f"Invalid ID format: {m.get('id')}")
                self.assertEqual(m["type"], cat_type)
                self.assertTrue(bool(m.get("name")), f"Missing name: {m}")
                self.assertTrue(bool(m.get("poster")), f"Missing poster: {m.get('name')}")
                self.assertTrue(m["poster"].startswith("http"), f"Invalid poster url: {m.get('poster')}")
                self.assertEqual(m.get("posterShape"), "poster")
                self.assertTrue(isinstance(m.get("genres"), list) and len(m["genres"]) > 0)
                self.assertTrue(bool(m.get("description")), f"Missing description: {m.get('name')}")

    def test_chronological_covers_all_eras(self):
        chrono_file = os.path.join(PR_DIR, "catalog", "series", "pr-chronological.json")
        with open(chrono_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        metas = data.get("metas", [])
        self.assertEqual(len(metas), 22, "Expected 22 series representing all 30 seasons")

        # Verify MMPR is first and Cosmic Fury is last
        self.assertEqual(metas[0]["id"], "tt0106064")
        self.assertIn("Mighty Morphin", metas[0]["name"])
        self.assertEqual(metas[-1]["id"], "tt29474102")
        self.assertIn("Cosmic Fury", metas[-1]["name"])

    def test_eras_coverage(self):
        saban_file = os.path.join(PR_DIR, "catalog", "series", "pr-saban-era.json")
        disney_file = os.path.join(PR_DIR, "catalog", "series", "pr-disney-era.json")
        neo_file = os.path.join(PR_DIR, "catalog", "series", "pr-neosaban-era.json")
        hasbro_file = os.path.join(PR_DIR, "catalog", "series", "pr-hasbro-era.json")

        with open(saban_file) as f:
            saban_metas = json.load(f)["metas"]
        with open(disney_file) as f:
            disney_metas = json.load(f)["metas"]
        with open(neo_file) as f:
            neo_metas = json.load(f)["metas"]
        with open(hasbro_file) as f:
            hasbro_metas = json.load(f)["metas"]

        self.assertEqual(len(saban_metas), 8, "Saban Era should have 8 series")
        self.assertEqual(len(disney_metas), 7, "Disney Era should have 7 series")
        self.assertEqual(len(neo_metas), 4, "Neo-Saban Era should have 4 series")
        self.assertEqual(len(hasbro_metas), 3, "Hasbro Era should have 3 series")

        # Eras combined must total 22 unique series
        all_era_ids = (
            [m["id"] for m in saban_metas] +
            [m["id"] for m in disney_metas] +
            [m["id"] for m in neo_metas] +
            [m["id"] for m in hasbro_metas]
        )
        self.assertEqual(len(all_era_ids), 22)
        self.assertEqual(len(set(all_era_ids)), 22, "Eras must not overlap")

    def test_movies_and_specials(self):
        movies_file = os.path.join(PR_DIR, "catalog", "movie", "pr-movies.json")
        with open(movies_file, "r", encoding="utf-8") as f:
            metas = json.load(f)["metas"]

        self.assertEqual(len(metas), 7, "Expected 7 movies and specials")
        movie_ids = [m["id"] for m in metas]
        self.assertIn("tt0113820", movie_ids)  # 1995 MMPR Movie
        self.assertIn("tt0120389", movie_ids)  # 1997 Turbo Movie
        self.assertIn("tt3717490", movie_ids)  # 2017 Power Rangers Movie
        self.assertIn("tt23219684", movie_ids) # 2023 Once & Always

    def test_dino_fury_poster_override(self):
        chrono_file = os.path.join(PR_DIR, "catalog", "series", "pr-chronological.json")
        with open(chrono_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        dino_fury = next(m for m in data.get("metas", []) if m["id"] == "tt12360292")
        self.assertEqual(
            dino_fury["poster"],
            "https://m.media-amazon.com/images/M/MV5BOTRiNjU2YzItN2QzMi00NmQ5LWFkYjUtNmI3YjkxM2I3MzE3XkEyXkFqcGc@._V1_.jpg"
        )

    def test_countries_json_entry(self):
        with open(self.countries_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        pr_entries = [c for c in data.get("countries", []) if c.get("code") == "power-rangers"]
        self.assertEqual(len(pr_entries), 1, "power-rangers must be listed in countries.json")
        entry = pr_entries[0]
        self.assertEqual(entry.get("name"), "Power Rangers Universe")
        self.assertEqual(entry.get("channel_count"), 29)
        self.assertEqual(entry.get("catalog_type"), "On-Demand Catalog")

    def test_meta_routes_and_episodes(self):
        meta_dir = os.path.join(PR_DIR, "meta")
        self.assertTrue(os.path.isdir(meta_dir), "meta directory must exist")

        # Test series meta files
        series_meta_dir = os.path.join(meta_dir, "series")
        self.assertTrue(os.path.isdir(series_meta_dir))
        series_files = os.listdir(series_meta_dir)
        self.assertEqual(len(series_files), 22, "Expected 22 series meta files")

        # Check MMPR
        with open(os.path.join(series_meta_dir, "tt0106064.json"), "r", encoding="utf-8") as f:
            mmpr = json.load(f)["meta"]
        self.assertEqual(mmpr["id"], "tt0106064")
        self.assertEqual(len(mmpr.get("videos", [])), 155, "MMPR should have 155 episodes")

        # Check Jungle Fury
        with open(os.path.join(series_meta_dir, "tt1121628.json"), "r", encoding="utf-8") as f:
            jf = json.load(f)["meta"]
        self.assertEqual(jf["id"], "tt1121628")
        self.assertEqual(len(jf.get("videos", [])), 32, "Jungle Fury should have 32 episodes")

        # Check Operation Overdrive
        with open(os.path.join(series_meta_dir, "tt0784920.json"), "r", encoding="utf-8") as f:
            oo = json.load(f)["meta"]
        self.assertEqual(len(oo.get("videos", [])), 32, "Operation Overdrive should have 32 episodes")

        # Test movie meta files
        movie_meta_dir = os.path.join(meta_dir, "movie")
        self.assertTrue(os.path.isdir(movie_meta_dir))
        movie_files = os.listdir(movie_meta_dir)
        self.assertEqual(len(movie_files), 7, "Expected 7 movie meta files")


if __name__ == "__main__":
    unittest.main()
