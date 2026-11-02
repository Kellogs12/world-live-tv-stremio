#!/usr/bin/env python3
"""
Unit and integration test suite for Cartoon & Animation Vault and Cartoons Live TV (Toonertia / Spelunkr TV).
Verifies catalogs, schemas, Cinemeta cache, Pokémon series & movies, ThunderCats (1985, 2011, Roar),
movie sequels, Robotboy inclusion, Spelunkr TV / Toonertia live streams, and no regressions.
"""

import json
import os
import unittest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
VAULT_DIR = os.path.join(PROJECT_DIR, "cartoon-vault")
CARTOONS_LIVE_DIR = os.path.join(PROJECT_DIR, "cartoons")


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
                self.assertFalse(
                    m["description"].endswith("on demand."),
                    f"Fallback dummy description found on {m['id']} ({m['name']})"
                )

            total_items += len(metas1)

        self.assertEqual(total_items, 661, f"Expected 661 total items, got {total_items}")

    def test_pokemon_series_and_movies_completeness(self):
        # 1. Verify Pokémon original series + Origins, Generations, Evolutions are right at the top of action-shows
        action_route = os.path.join(VAULT_DIR, "catalog", "series", "action-shows.json")
        with open(action_route, "r", encoding="utf-8") as f:
            action_metas = json.load(f).get("metas", [])

        top_action_ids = [m["id"] for m in action_metas[:4]]
        self.assertEqual(
            top_action_ids,
            ["tt0168366", "tt3218680", "tt6071336", "tt15356258"],
            "Pokémon (tt0168366) and spin-offs must be at the very top of action-shows"
        )
        self.assertIn("Pokemon", action_metas[0]["name"])
        self.assertIn("Pokémon", action_metas[0]["name"])

        # 2. Verify Pokémon Chronicles, Journeys, Horizons, Twilight Wings, Concierge are near the top of cn-shows
        cn_route = os.path.join(VAULT_DIR, "catalog", "series", "cn-shows.json")
        with open(cn_route, "r", encoding="utf-8") as f:
            cn_metas = json.load(f).get("metas", [])
        top_cn_ids = {m["id"] for m in cn_metas[:12]}
        for pid in ["tt1294022", "tt29079338", "tt26692417", "tt11547516", "tt26916286"]:
            self.assertIn(pid, top_cn_ids, f"Pokémon series {pid} must be near the top of cn-shows")

        # 3. Verify all 24 Pokémon animated movies are in cartoon-movies
        movies_route = os.path.join(VAULT_DIR, "catalog", "movie", "cartoon-movies.json")
        with open(movies_route, "r", encoding="utf-8") as f:
            movie_ids = {m["id"] for m in json.load(f).get("metas", [])}
        expected_pokemon_movies = [
            "tt0190641", "tt0210234", "tt0235679", "tt0287635", "tt0347791",
            "tt0420076", "tt0435286", "tt0875609", "tt1000095", "tt1226251",
            "tt1160525", "tt1468843", "tt1690470", "tt1961324", "tt1739212",
            "tt2549540", "tt3257582", "tt3918368", "tt4503906", "tt5889204",
            "tt6595896", "tt8108230", "tt8856470", "tt11819890"
        ]
        for pmid in expected_pokemon_movies:
            self.assertIn(pmid, movie_ids, f"Pokémon movie {pmid} missing from cartoon-movies")

    def test_thundercats_completeness(self):
        # 1. Verify original 1985 ThunderCats (tt0088631) is #1 in classics-shows
        classics_route = os.path.join(VAULT_DIR, "catalog", "series", "classics-shows.json")
        with open(classics_route, "r", encoding="utf-8") as f:
            classics_metas = json.load(f).get("metas", [])
        self.assertEqual(classics_metas[0]["id"], "tt0088631", "ThunderCats (1985) must be first in classics-shows")
        self.assertEqual(classics_metas[0]["name"], "ThunderCats (1985)")

        # 2. Verify ThunderCats (2011) and ThunderCats Roar are near the top of cn-shows
        cn_route = os.path.join(VAULT_DIR, "catalog", "series", "cn-shows.json")
        with open(cn_route, "r", encoding="utf-8") as f:
            cn_metas = json.load(f).get("metas", [])
        top_15_cn = {m["id"]: m for m in cn_metas[:15]}
        self.assertIn("tt1666278", top_15_cn, "ThunderCats (2011) must be in top 15 of cn-shows")
        self.assertIn("tt8435344", top_15_cn, "ThunderCats Roar must be in top 15 of cn-shows")
        self.assertEqual(top_15_cn["tt1666278"]["name"], "ThunderCats (2011)")

    def test_movie_sequels_completeness(self):
        movies_route = os.path.join(VAULT_DIR, "catalog", "movie", "cartoon-movies.json")
        with open(movies_route, "r", encoding="utf-8") as f:
            movie_ids = {m["id"] for m in json.load(f).get("metas", [])}

        required_sequels = [
            # Pixar sequels
            "tt1979376", "tt3606756", "tt1453405", "tt2277860", "tt1216475", "tt3606752", "tt2096673", "tt22022452",
            # DreamWorks sequels
            "tt0413267", "tt0892791", "tt0448694", "tt3915174", "tt2267968", "tt21692408",
            "tt1646971", "tt2386490", "tt0479952", "tt1277953", "tt1911658", "tt0481499", "tt2850386",
            # Ice Age 1-5, Despicable Me 1-4, Minions 1-2, Hotel Transylvania 1-4, Cloudy 1-2, Rio 1-2, Open Season 1-3
            "tt0268380", "tt0438097", "tt1080016", "tt1667889", "tt3416828",
            "tt1323594", "tt1690953", "tt3469046", "tt7510222", "tt2293640", "tt5113044",
            "tt0837562", "tt2510894", "tt5220122", "tt9848626",
            "tt0844471", "tt1985966", "tt1436562", "tt2357291", "tt0400717", "tt1107365", "tt1646926",
            # Disney sequels
            "tt0120131", "tt0318403", "tt0107952", "tt0115491", "tt0401398", "tt0344864",
            "tt0279967", "tt0437503", "tt0313680", "tt5848272", "tt2294629", "tt4520988",
            "tt0328880", "tt0465925", "tt0097757", "tt0240684", "tt0061852", "tt0283426",
            "tt0046183", "tt0280030", "tt0055254", "tt0324941", "tt0100477", "tt0034492", "tt0447854",
            # Ben 10, Yu-Gi-Oh!, DBZ/Super, Jimmy Timmy, Fairly OddParents
            "tt1037011", "tt1327701", "tt13186528", "tt1587157", "tt4273562",
            "tt2263944", "tt3819668", "tt7961060", "tt14614892",
            "tt0414177", "tt0473050", "tt0499605", "tt39055318", "tt0419739", "tt10474606"
        ]
        for sid in required_sequels:
            self.assertIn(sid, movie_ids, f"Expected movie sequel {sid} in cartoon-movies")

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
            ("series", "classics-shows"): ["tt0780438", "tt1470837", "tt0280277", "tt0213363", "tt0983983", "tt0224455", "tt0233033"],
            ("series", "action-shows"): ["tt0247902", "tt1196094", "tt0210418", "tt1674928", "tt0409591", "tt1659175", "tt0103369"],
            ("movie", "cartoon-movies"): ["tt0253658", "tt0290057", "tt0357139", "tt0190641", "tt0259974", "tt0317705"]
        }
        for (cat_type, cat_id), req_ids in expected_by_cat.items():
            route = os.path.join(VAULT_DIR, "catalog", cat_type, f"{cat_id}.json")
            with open(route, "r", encoding="utf-8") as f:
                data = json.load(f)
            present_ids = {m["id"] for m in data.get("metas", [])}
            for rid in req_ids:
                self.assertIn(rid, present_ids, f"Expected 1999 Gen Z ID {rid} in {cat_id}")

    def test_classic_cartoons_verified_replacements(self):
        classics_route = os.path.join(VAULT_DIR, "catalog", "series", "classics-shows.json")
        with open(classics_route, "r", encoding="utf-8") as f:
            data = json.load(f)
        present_ids = {m["id"] for m in data.get("metas", [])}

        broken_ids = ["tt21153032", "tt0053488", "tt0060019", "tt0184175", "tt0364793"]
        for bid in broken_ids:
            self.assertNotIn(bid, present_ids, f"Broken IMDb ID {bid} must not be in classics-shows")

        verified_replacements = ["tt0068112", "tt8543208", "tt0084972", "tt0051283", "tt0233033"]
        for vid in verified_replacements:
            self.assertIn(vid, present_ids, f"Verified classic cartoon ID {vid} must be in classics-shows")

        action_route = os.path.join(VAULT_DIR, "catalog", "series", "action-shows.json")
        with open(action_route, "r", encoding="utf-8") as f:
            action_data = json.load(f)
        action_ids = {m["id"] for m in action_data.get("metas", [])}
        for bid in ["tt0249327", "tt0114327"]:
            self.assertNotIn(bid, action_ids, f"Unmapped dub IMDb ID {bid} must not be in action-shows")
        for vid in ["tt0247902", "tt0103369"]:
            self.assertIn(vid, action_ids, f"Canonical mapped IMDb ID {vid} must be in action-shows")

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
        self.assertEqual(len(all_ids), 661)

    def test_spelunkr_toonertia_live_tv_addon(self):
        manifest_path = os.path.join(CARTOONS_LIVE_DIR, "manifest.json")
        self.assertTrue(os.path.exists(manifest_path), "cartoons/manifest.json must exist")
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest.get("id"), "worldlive.cartoons")
        self.assertIn("spelunkr.tv/toonertia", manifest.get("description", ""))
        cat_ids = [c["id"] for c in manifest.get("catalogs", [])]
        self.assertEqual(cat_ids, [
            "cartoons-toonertia",
            "cartoons-spelunkr",
            "cartoons-live-networks",
            "cartoons-cn-disney",
            "cartoons-nick",
            "cartoons-classics"
        ])

        # Check Backward-compatible AIOStreams catalogs exist and have valid metas
        for legacy_cat, min_expected in [("cartoons-cn-disney", 4), ("cartoons-nick", 6), ("cartoons-classics", 8)]:
            legacy_path = os.path.join(CARTOONS_LIVE_DIR, "catalog", "tv", f"{legacy_cat}.json")
            self.assertTrue(os.path.exists(legacy_path), f"{legacy_cat}.json must exist for AIOStreams compatibility")
            with open(legacy_path, "r", encoding="utf-8") as f:
                l_metas = json.load(f).get("metas", [])
            self.assertGreaterEqual(len(l_metas), min_expected, f"{legacy_cat} should have at least {min_expected} channels")

        # Check Toonertia catalog (1 main channel + 41 individual blocks = 42 channels)
        toonertia_cat_path = os.path.join(CARTOONS_LIVE_DIR, "catalog", "tv", "cartoons-toonertia.json")
        with open(toonertia_cat_path, "r", encoding="utf-8") as f:
            t_metas = json.load(f).get("metas", [])
        self.assertEqual(len(t_metas), 42, "cartoons-toonertia should have 42 channels")
        self.assertEqual(t_metas[0]["id"], "tv-cartoons-toonertia-24-7-live")
        self.assertIn("TOONERTIA 24/7", t_metas[0]["name"])

        # Check main Toonertia stream file
        t_stream_path = os.path.join(CARTOONS_LIVE_DIR, "stream", "tv", "tv-cartoons-toonertia-24-7-live.json")
        self.assertTrue(os.path.exists(t_stream_path))
        with open(t_stream_path, "r", encoding="utf-8") as f:
            t_streams = json.load(f).get("streams", [])
        self.assertEqual(len(t_streams), 42, "Main Toonertia channel should have 41 IA MP4 streams + 1 externalUrl")
        self.assertTrue(t_streams[0]["url"].startswith("https://archive.org/download/"))
        self.assertEqual(t_streams[-1].get("externalUrl"), "https://spelunkr.tv/toonertia")

        # Check Spelunkr catalog (10 full channels + 30 featured VHS blocks = 40 channels)
        sp_cat_path = os.path.join(CARTOONS_LIVE_DIR, "catalog", "tv", "cartoons-spelunkr.json")
        with open(sp_cat_path, "r", encoding="utf-8") as f:
            sp_metas = json.load(f).get("metas", [])
        self.assertEqual(len(sp_metas), 40, "cartoons-spelunkr should have 40 channels")
        sp_ids = {m["id"] for m in sp_metas}
        for cid in ["toonertia", "latchkey-tv", "saturday-morning", "late-nite-swimclub", "meddling-kids",
                    "rocket-punch", "ovatv", "rubber-hose", "kersplat", "library-card"]:
            self.assertIn(f"tv-cartoons-spelunkr-{cid}", sp_ids)

    def test_countries_json_and_readme(self):
        with open(self.countries_path, "r", encoding="utf-8") as f:
            countries_data = json.load(f)

        vault_entries = [c for c in countries_data.get("countries", []) if c.get("code") == "cartoon-vault"]
        self.assertEqual(len(vault_entries), 1, "cartoon-vault must be listed in countries.json")
        entry = vault_entries[0]
        self.assertEqual(entry.get("channel_count"), 661)
        self.assertEqual(entry.get("item_count"), 661)

        cartoons_entries = [c for c in countries_data.get("countries", []) if c.get("code") == "cartoons"]
        self.assertEqual(len(cartoons_entries), 1, "cartoons must be listed in countries.json")
        self.assertEqual(cartoons_entries[0].get("channel_count"), 100)

        with open(self.readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()

        self.assertIn("Robotboy", readme_text)
        self.assertIn("661 iconic and cult-classic animated series and specials", readme_text)
        self.assertIn("spelunkr.tv/toonertia", readme_text)


if __name__ == "__main__":
    unittest.main()
