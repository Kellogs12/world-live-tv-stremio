#!/usr/bin/env python3
"""
Cartoon & Animation Vault Stremio Catalog Addon Generator.
Generates an on-demand catalog addon for iconic animated series and movies:
Cartoon Network, Disney, Nickelodeon, Classic Cartoons, and Superhero Action Animation.
Uses Cinemeta API to pull complete IMDb metadata, posters, ratings, and descriptions.
Generates static catalog routes:
  - catalog/{type}/{id}.json
  - catalog/{type}/{id}/skip=0.json
"""

import json
import os
import shutil
import socket
import ssl
import sys
import time
import urllib.request
import urllib.error

socket.setdefaulttimeout(8.0)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://kellogs12.github.io/world-live-tv-stremio"
VAULT_DIR_NAME = "cartoon-vault"
VAULT_ID = "worldlive.cartoonvault"
VAULT_VERSION = "1.0.0"
VAULT_NAME = "🎨 Cartoon & Animation Vault"
VAULT_DESC = (
    "Comprehensive on-demand catalog of iconic animated series and movies: "
    "Cartoon Network, Disney, Nickelodeon, Classic Cartoons, and Superhero Action Animation."
)

CATALOG_DEFINITIONS = [
    {
        "type": "series",
        "id": "cn-shows",
        "name": "Cartoon Network Shows"
    },
    {
        "type": "series",
        "id": "disney-shows",
        "name": "Disney Animated Shows"
    },
    {
        "type": "series",
        "id": "nick-shows",
        "name": "Nickelodeon Shows"
    },
    {
        "type": "series",
        "id": "classics-shows",
        "name": "Classic & Vault Cartoons"
    },
    {
        "type": "series",
        "id": "action-shows",
        "name": "Superhero & Action Animation"
    },
    {
        "type": "movie",
        "id": "cartoon-movies",
        "name": "Animated Movies & Specials"
    }
]

SHOW_DEFINITIONS = {
    "cn-shows": [
        ("tt0760437", "Ben 10"),
        ("tt1192169", "Ben 10: Alien Force"),
        ("tt1622696", "Ben 10: Ultimate Alien"),
        ("tt2293002", "Ben 10: Omniverse"),
        ("tt1305826", "Adventure Time"),
        ("tt1710308", "Regular Show"),
        ("tt0115157", "Dexter's Laboratory"),
        ("tt0175058", "The Powerpuff Girls"),
        ("tt0220880", "Courage the Cowardly Dog"),
        ("tt0184111", "Ed, Edd n Eddy"),
        ("tt0118360", "Johnny Bravo"),
        ("tt0278238", "Samurai Jack"),
        ("tt0343314", "Teen Titans"),
        ("tt0419326", "Foster's Home for Imaginary Friends"),
        ("tt0292800", "The Grim Adventures of Billy & Mandy"),
        ("tt0312109", "Codename: Kids Next Door"),
        ("tt1942683", "The Amazing World of Gumball"),
        ("tt3061046", "Steven Universe"),
        ("tt4839610", "We Bare Bears"),
        ("tt1140100", "Chowder"),
        ("tt3718778", "Over the Garden Wall"),
        ("tt8146754", "Infinity Train"),
        ("tt1636691", "Generator Rex"),
        ("tt1173427", "Total Drama"),
        ("tt1178180", "The Marvelous Misadventures of Flapjack"),
        ("tt3061050", "Clarence"),
        ("tt0419315", "Camp Lazlo!"),
        ("tt0118289", "Cow and Chicken"),
        ("tt0218769", "I Am Weasel"),
        ("tt0361201", "Megas XLR"),
        ("tt1709198", "Sym-Bionic Titan"),
        ("tt7713450", "Craig of the Creek")
    ],
    "disney-shows": [
        ("tt0852863", "Phineas and Ferb"),
        ("tt1865718", "Gravity Falls"),
        ("tt8050756", "The Owl House"),
        ("tt8050740", "Amphibia"),
        ("tt0278866", "Kim Possible"),
        ("tt0092345", "DuckTales (1987)"),
        ("tt5531466", "DuckTales (2017)"),
        ("tt2758770", "Star vs. the Forces of Evil"),
        ("tt0108783", "Gargoyles"),
        ("tt0126170", "Recess"),
        ("tt0101076", "Darkwing Duck"),
        ("tt0098924", "TaleSpin"),
        ("tt0096557", "Chip 'n' Dale Rescue Rangers"),
        ("tt0103428", "Goof Troop"),
        ("tt5515212", "Big Hero 6: The Series"),
        ("tt4902964", "Rapunzel's Tangled Adventure"),
        ("tt0293737", "The Proud Family"),
        ("tt0429305", "American Dragon: Jake Long"),
        ("tt0364774", "Lilo & Stitch: The Series"),
        ("tt0465327", "The Emperor's New School"),
        ("tt2252938", "Wander Over Yonder"),
        ("tt2930604", "Star Wars Rebels"),
        ("tt0458290", "Star Wars: The Clone Wars"),
        ("tt7165904", "Big City Greens"),
        ("tt0112197", "Timon & Pumbaa"),
        ("tt0105935", "Aladdin"),
        ("tt0103477", "The Little Mermaid"),
        ("tt0134260", "Pepper Ann"),
        ("tt0118337", "Hercules"),
        ("tt0260602", "Buzz Lightyear of Star Command")
    ],
    "nick-shows": [
        ("tt0206512", "SpongeBob SquarePants"),
        ("tt0417299", "Avatar: The Last Airbender"),
        ("tt1695360", "The Legend of Korra"),
        ("tt0235918", "The Fairly OddParents"),
        ("tt0366005", "Danny Phantom"),
        ("tt0101188", "Rugrats"),
        ("tt0115200", "Hey Arnold!"),
        ("tt0106115", "Rocko's Modern Life"),
        ("tt0235923", "Invader Zim"),
        ("tt0320808", "The Adventures of Jimmy Neutron"),
        ("tt1877889", "Teenage Mutant Ninja Turtles (2012)"),
        ("tt4859164", "The Loud House"),
        ("tt0158417", "CatDog"),
        ("tt0165576", "The Wild Thornberrys"),
        ("tt0212686", "Rocket Power"),
        ("tt0131664", "The Angry Beavers"),
        ("tt0108709", "Aaahh!!! Real Monsters"),
        ("tt0318233", "My Life as a Teenage Robot"),
        ("tt0235916", "ChalkZone"),
        ("tt0268069", "As Told by Ginger"),
        ("tt0387714", "All Grown Up!"),
        ("tt0101178", "The Ren & Stimpy Show"),
        ("tt0892700", "The Penguins of Madagascar"),
        ("tt1545214", "Kung Fu Panda: Legends of Awesomeness"),
        ("tt0101084", "Doug"),
        ("tt0235928", "KaBlam!"),
        ("tt0118274", "Blue's Clues")
    ],
    "classics-shows": [
        ("tt0058855", "The Tom and Jerry Show (1965)"),
        ("tt0072573", "The New Tom & Jerry Show (1975)"),
        ("tt0131174", "Tom & Jerry Kids Show"),
        ("tt0053502", "The Flintstones"),
        ("tt0055683", "The Jetsons"),
        ("tt0063950", "Scooby-Doo, Where Are You!"),
        ("tt0306394", "What's New, Scooby-Doo?"),
        ("tt1660055", "Scooby-Doo! Mystery Incorporated"),
        ("tt0105941", "Animaniacs"),
        ("tt0112123", "Pinky and the Brain"),
        ("tt0098929", "Tiny Toon Adventures"),
        ("tt0112004", "Freakazoid!"),
        ("tt0085033", "Inspector Gadget"),
        ("tt0081933", "The Smurfs"),
        ("tt0054572", "Top Cat"),
        ("tt0054577", "The Yogi Bear Show"),
        ("tt0071000", "Hong Kong Phooey"),
        ("tt0094469", "Garfield and Friends"),
        ("tt0047754", "The Bugs Bunny Show"),
        ("tt0060018", "The Road Runner Show"),
        ("tt0053531", "Popeye the Sailor")
    ],
    "action-shows": [
        ("tt0103359", "Batman: The Animated Series"),
        ("tt0115378", "Superman: The Animated Series"),
        ("tt0147746", "Batman Beyond"),
        ("tt0275137", "Justice League"),
        ("tt0411008", "Justice League Unlimited"),
        ("tt1641384", "Young Justice"),
        ("tt0112175", "Spider-Man: The Animated Series (1994)"),
        ("tt0976192", "The Spectacular Spider-Man"),
        ("tt0103584", "X-Men: The Animated Series (1992)"),
        ("tt16026746", "X-Men '97"),
        ("tt0131613", "Teenage Mutant Ninja Turtles (1987)"),
        ("tt0372074", "Teenage Mutant Ninja Turtles (2003)"),
        ("tt0086817", "The Transformers (1984)"),
        ("tt0115115", "Beast Wars: Transformers"),
        ("tt0168366", "Pokémon"),
        ("tt0121220", "Dragon Ball Z"),
        ("tt0090422", "Dragon Ball"),
        ("tt4644488", "Dragon Ball Super"),
        ("tt0772145", "Wolverine and the X-Men"),
        ("tt1626038", "The Avengers: Earth's Mightiest Heroes"),
        ("tt0837143", "Iron Man: Armored Adventures"),
        ("tt0247729", "Static Shock"),
        ("tt1724587", "Green Lantern: The Animated Series"),
        ("tt6741278", "Invincible"),
        ("tt6517102", "Castlevania"),
        ("tt11126994", "Arcane")
    ],
    "cartoon-movies": [
        ("tt0345950", "The SpongeBob SquarePants Movie"),
        ("tt2279373", "The SpongeBob Movie: Sponge Out of Water"),
        ("tt4823776", "The SpongeBob Movie: Sponge on the Run"),
        ("tt1146431", "Ben 10: Secret of the Omnitrix"),
        ("tt2290147", "Ben 10: Destroy All Aliens"),
        ("tt1825918", "Phineas and Ferb the Movie: Across the 2nd Dimension"),
        ("tt1817232", "Phineas and Ferb the Movie: Candace Against the Universe"),
        ("tt0289408", "The Powerpuff Girls Movie"),
        ("tt0106364", "Batman: Mask of the Phantasm"),
        ("tt0233298", "Batman Beyond: Return of the Joker"),
        ("tt1569923", "Batman: Under the Red Hood"),
        ("tt0166792", "Scooby-Doo on Zombie Island"),
        ("tt0196931", "Scooby-Doo and the Witch's Ghost"),
        ("tt0129167", "The Iron Giant"),
        ("tt0113198", "A Goofy Movie"),
        ("tt0208185", "An Extremely Goofy Movie"),
        ("tt1232047", "Ed, Edd n Eddy's Big Picture Show"),
        ("tt10515852", "Steven Universe: The Movie"),
        ("tt0816671", "Teen Titans: Trouble in Tokyo"),
        ("tt7424200", "Teen Titans GO! To the Movies"),
        ("tt0268397", "Jimmy Neutron: Boy Genius"),
        ("tt0134067", "The Rugrats Movie"),
        ("tt0213203", "Rugrats in Paris"),
        ("tt5257726", "Hey Arnold: The Jungle Movie"),
        ("tt0265632", "Recess: School's Out"),
        ("tt0099472", "DuckTales: The Movie - Treasure of the Lost Lamp"),
        ("tt0103639", "Aladdin (1992)"),
        ("tt0110357", "The Lion King (1994)"),
        ("tt4633694", "Spider-Man: Into the Spider-Verse"),
        ("tt9362722", "Spider-Man: Across the Spider-Verse"),
        ("tt2820466", "Justice League: The Flashpoint Paradox"),
        ("tt2027128", "Justice League: Doom"),
        ("tt0092106", "The Transformers: The Movie (1986)")
    ]
}


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(',', ':'))
        f.write('\n')


def fetch_cinemeta_meta(stremio_type, imdb_id, default_title=""):
    url = f"https://v3-cinemeta.strem.io/meta/{stremio_type}/{imdb_id}.json"
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (CartoonVaultBuilder)'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=6.0, context=ctx) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                meta = data.get('meta')
                if meta and meta.get('name'):
                    return meta
        except urllib.error.URLError:
            try:
                unverified_ctx = ssl._create_unverified_context()
                with urllib.request.urlopen(req, timeout=6.0, context=unverified_ctx) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    meta = data.get('meta')
                    if meta and meta.get('name'):
                        return meta
            except Exception:
                pass
        except Exception:
            pass
        time.sleep(0.3)
    return None


def build_vault(base_dir=SCRIPT_DIR, refresh=False):
    vault_dir = os.path.join(base_dir, VAULT_DIR_NAME)
    catalog_dir = os.path.join(vault_dir, "catalog")
    assets_dir = os.path.join(vault_dir, "assets")
    cache_file = os.path.join(vault_dir, "catalog_cache.json")

    os.makedirs(catalog_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    # Copy icon
    icon_source = os.path.join(base_dir, "tv-icon.png")
    if os.path.exists(icon_source):
        shutil.copy(icon_source, os.path.join(assets_dir, "icon.png"))

    cache = {}
    if os.path.exists(cache_file) and not refresh:
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception as e:
            print(f"  [Notice] Could not load cache: {e}")

    total_titles = 0
    updated_cache = False

    for cat in CATALOG_DEFINITIONS:
        cat_id = cat["id"]
        cat_type = cat["type"]
        items = SHOW_DEFINITIONS.get(cat_id, [])
        print(f"Building Cartoon Vault catalog: {cat['name']} ({len(items)} items)...")

        cat_metas = []
        for imdb_id, default_title in items:
            cached_meta = cache.get(imdb_id)
            meta = None

            # If cache has incomplete info (e.g. empty description or default title), re-fetch
            needs_fetch = refresh or not cached_meta or not cached_meta.get("description")

            if not needs_fetch:
                meta = cached_meta
            else:
                raw_meta = fetch_cinemeta_meta(cat_type, imdb_id, default_title)
                if raw_meta:
                    genres = raw_meta.get('genres')
                    if not genres and raw_meta.get('genre'):
                        g = raw_meta.get('genre')
                        genres = [x.strip() for x in g.split(',')] if isinstance(g, str) else [g]

                    meta = {
                        "id": imdb_id,
                        "type": cat_type,
                        "name": raw_meta.get('name') or default_title,
                        "poster": raw_meta.get('poster') or f"https://images.metahub.space/poster/medium/{imdb_id}/img",
                        "posterShape": "poster",
                        "genres": genres or ["Animation"],
                        "imdbRating": str(raw_meta.get('imdbRating', '')),
                        "releaseInfo": str(raw_meta.get('releaseInfo') or raw_meta.get('year') or ''),
                        "description": raw_meta.get('description', '')
                    }
                    if raw_meta.get('background'):
                        meta["background"] = raw_meta.get('background')
                    if raw_meta.get('logo'):
                        meta["logo"] = raw_meta.get('logo')

                    cache[imdb_id] = meta
                    updated_cache = True
                elif cached_meta:
                    meta = cached_meta
                else:
                    meta = {
                        "id": imdb_id,
                        "type": cat_type,
                        "name": default_title,
                        "poster": f"https://images.metahub.space/poster/medium/{imdb_id}/img",
                        "posterShape": "poster",
                        "genres": ["Animation"],
                        "imdbRating": "",
                        "releaseInfo": "",
                        "description": f"{default_title} on demand."
                    }
                    cache[imdb_id] = meta
                    updated_cache = True

            cat_metas.append(meta)
            total_titles += 1

        catalog_response = {"metas": cat_metas}

        # Route 1: catalog/{type}/{id}.json
        route1_path = os.path.join(vault_dir, "catalog", cat_type, f"{cat_id}.json")
        write_json(route1_path, catalog_response)

        # Route 2: catalog/{type}/{id}/skip=0.json
        route2_path = os.path.join(vault_dir, "catalog", cat_type, cat_id, "skip=0.json")
        write_json(route2_path, catalog_response)

    if updated_cache:
        write_json(cache_file, cache)

    # Generate Manifest
    manifest = {
        "id": VAULT_ID,
        "version": VAULT_VERSION,
        "name": VAULT_NAME,
        "description": VAULT_DESC,
        "logo": f"{BASE_URL}/{VAULT_DIR_NAME}/assets/icon.png",
        "resources": ["catalog"],
        "types": ["series", "movie"],
        "idPrefixes": ["tt"],
        "catalogs": CATALOG_DEFINITIONS,
        "behaviorHints": {
            "configurable": False,
            "configurationRequired": False
        }
    }
    manifest_path = os.path.join(vault_dir, "manifest.json")
    write_json(manifest_path, manifest)

    print(f"✅ Cartoon & Animation Vault build complete! Total titles: {total_titles}")

    return {
        "code": VAULT_DIR_NAME,
        "name": "Cartoon & Animation Vault",
        "flag": "🎨",
        "region": "Cartoons",
        "description": VAULT_DESC,
        "channel_count": total_titles,
        "item_count": total_titles,
        "item_label": "Iconic Titles",
        "catalog_type": "On-Demand Catalog",
        "vpn_required": False
    }


def main():
    refresh = "--refresh" in sys.argv
    build_vault(SCRIPT_DIR, refresh=refresh)


if __name__ == "__main__":
    main()
