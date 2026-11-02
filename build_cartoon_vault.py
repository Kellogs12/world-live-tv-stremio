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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

socket.setdefaulttimeout(8.0)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://kellogs12.github.io/world-live-tv-stremio"
VAULT_DIR_NAME = "cartoon-vault"
VAULT_ID = "worldlive.cartoonvault"
VAULT_VERSION = "1.3.0"
VAULT_NAME = "🎨 Cartoon & Animation Vault"
VAULT_DESC = (
    "Comprehensive on-demand catalog of 661 iconic animated series, movie franchises, and sequels: "
    "Cartoon Network, Disney, Nickelodeon, Classic Vault Cartoons (ThunderCats, He-Man, Voltron), "
    "and Action Animation (Pokémon, Dragon Ball, Yu-Gi-Oh!, DC & Marvel)."
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
        ("tt6148376", "Ben 10 (2016)"),
        ("tt1294022", "Pokémon Chronicles"),
        ("tt29079338", "Pokémon Journeys: The Series"),
        ("tt26692417", "Pokémon Horizons: The Series"),
        ("tt11547516", "Pokémon: Twilight Wings"),
        ("tt26916286", "Pokémon Concierge"),
        ("tt1666278", "ThunderCats (2011)"),
        ("tt8435344", "ThunderCats Roar"),
        ("tt1305826", "Adventure Time"),
        ("tt11165358", "Adventure Time: Distant Lands"),
        ("tt15248880", "Adventure Time: Fionna & Cake"),
        ("tt1710308", "Regular Show"),
        ("tt0115157", "Dexter's Laboratory"),
        ("tt0175058", "The Powerpuff Girls"),
        ("tt4718304", "The Powerpuff Girls (2016)"),
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
        ("tt13714610", "Steven Universe Future"),
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
        ("tt7713450", "Craig of the Creek"),
        ("tt0482870", "Robotboy"),
        ("tt1291662", "The Secret Saturdays"),
        ("tt0386993", "Xiaolin Showdown"),
        ("tt0353115", "Mucha Lucha!"),
        ("tt0451461", "My Gym Partner's a Monkey"),
        ("tt0419348", "The Life and Times of Juniper Lee"),
        ("tt0407398", "Hi Hi Puffy AmiYumi"),
        ("tt0291672", "Time Squad"),
        ("tt0260653", "Sheep in the Big City"),
        ("tt0235589", "Mike, Lu & Og"),
        ("tt0497310", "Squirrel Boy"),
        ("tt0767914", "Class of 3000"),
        ("tt1118131", "Chop Socky Chooks"),
        ("tt1674117", "Hero: 108"),
        ("tt1043820", "Storm Hawks"),
        ("tt0439341", "6teen"),
        ("tt1504166", "Stoked"),
        ("tt2406986", "Grojband"),
        ("tt0374419", "Martin Mystery"),
        ("tt0283226", "Totally Spies!"),
        ("tt0417311", "Code Lyoko"),
        ("tt1518723", "Hot Wheels: Battle Force 5"),
        ("tt0454349", "Johnny Test"),
        ("tt1114855", "Bakugan Battle Brawlers"),
        ("tt1871731", "Ninjago: Masters of Spinjitzu"),
        ("tt0419322", "Evil Con Carne"),
        ("tt0312255", "Whatever Happened to... Robot Jones?"),
        ("tt0376390", "Duck Dodgers"),
        ("tt0306371", "Ozzy & Drix"),
        ("tt0424603", "Atomic Betty"),
        ("tt2130507", "Detentionaire"),
        ("tt1402156", "The League of Super Evil"),
        ("tt1746428", "Sidekick"),
        ("tt1830924", "Almost Naked Animals"),
        ("tt3787754", "Total Drama Presents: The Ridonculous Race"),
        ("tt2771780", "Teen Titans Go!"),
        ("tt0361243", "Star Wars: Clone Wars (2003)"),
        ("tt0286347", "Braceface"),
        ("tt0471989", "Being Ian"),
        ("tt0946601", "Ruby Gloom"),
        ("tt0831823", "Di-Gata Defenders"),
        ("tt0305011", "Clone High"),
        ("tt4847134", "Mighty Magiswords"),
        ("tt6965802", "OK K.O.! Let's Be Heroes"),
        ("tt0108937", "Space Ghost Coast to Coast"),
        ("tt0105928", "2 Stupid Dogs"),
        ("tt0115226", "The Real Adventures of Jonny Quest"),
        ("tt0279077", "FLCL")
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
        ("tt0088528", "Adventures of the Gummi Bears"),
        ("tt0213334", "Bonkers"),
        ("tt0136658", "Quack Pack"),
        ("tt5515212", "Big Hero 6: The Series"),
        ("tt4902964", "Rapunzel's Tangled Adventure"),
        ("tt0293737", "The Proud Family"),
        ("tt0429305", "American Dragon: Jake Long"),
        ("tt0364774", "Lilo & Stitch: The Series"),
        ("tt0465327", "The Emperor's New School"),
        ("tt2252938", "Wander Over Yonder"),
        ("tt2930604", "Star Wars Rebels"),
        ("tt0458290", "Star Wars: The Clone Wars"),
        ("tt12708542", "Star Wars: The Bad Batch"),
        ("tt7165904", "Big City Greens"),
        ("tt0112197", "Timon & Pumbaa"),
        ("tt0105935", "Aladdin"),
        ("tt0103477", "The Little Mermaid"),
        ("tt0128890", "Pepper Ann"),
        ("tt0138967", "Hercules"),
        ("tt0260602", "Buzz Lightyear of Star Command"),
        ("tt0423746", "Super Robot Monkey Team Hyperforce Go!"),
        ("tt0855673", "Yin Yang Yo!"),
        ("tt0795256", "Pucca"),
        ("tt0386176", "Dave the Barbarian"),
        ("tt0423621", "Brandy & Mr. Whiskers"),
        ("tt0450208", "The Buzz on Maggie"),
        ("tt0816401", "The Replacements"),
        ("tt0337761", "Fillmore!"),
        ("tt0275848", "Lloyd in Space"),
        ("tt0257325", "Teacher's Pet"),
        ("tt0237987", "The Weekenders"),
        ("tt2392143", "Motorcity"),
        ("tt2341339", "Randy Cunningham: 9th Grade Ninja"),
        ("tt1600757", "Kick Buttowski: Suburban Daredevil"),
        ("tt1812523", "Tron: Uprising"),
        ("tt2548200", "Slugterra"),
        ("tt0877105", "Galactik Football"),
        ("tt0497578", "A.T.O.M. - Alpha Teens On Machines"),
        ("tt0813808", "Oban Star-Racers"),
        ("tt0756486", "Get Ed"),
        ("tt0383718", "W.I.T.C.H."),
        ("tt0480499", "Team Galaxy"),
        ("tt0272388", "House of Mouse"),
        ("tt0283754", "The Legend of Tarzan"),
        ("tt1725902", "Fish Hooks"),
        ("tt5439480", "Milo Murphy's Law"),
        ("tt3293184", "Penn Zero: Part-Time Hero"),
        ("tt2219622", "The 7D"),
        ("tt1307224", "Kid vs. Kat"),
        ("tt1387904", "Jimmy Two-Shoes"),
        ("tt0144700", "101 Dalmatians: The Series"),
        ("tt0165052", "The New Adventures of Winnie the Pooh"),
        ("tt0124949", "Jungle Cubs"),
        ("tt0172049", "Rolie Polie Olie"),
        ("tt0198181", "Mickey Mouse Works"),
        ("tt2768802", "Mickey Mouse"),
        ("tt3824018", "Pickle and Peanut"),
        ("tt0115269", "Mighty Ducks: The Animated Series")
    ],
    "nick-shows": [
        ("tt0206512", "SpongeBob SquarePants"),
        ("tt0417299", "Avatar: The Last Airbender"),
        ("tt1695360", "The Legend of Korra"),
        ("tt0235918", "The Fairly OddParents"),
        ("tt0366005", "Danny Phantom"),
        ("tt1710310", "T.U.F.F. Puppy"),
        ("tt0101188", "Rugrats"),
        ("tt0115200", "Hey Arnold!"),
        ("tt0106115", "Rocko's Modern Life"),
        ("tt0235923", "Invader Zim"),
        ("tt0320808", "The Adventures of Jimmy Neutron"),
        ("tt1877889", "Teenage Mutant Ninja Turtles (2012)"),
        ("tt4859164", "The Loud House"),
        ("tt9165462", "The Casagrandes"),
        ("tt0154061", "CatDog"),
        ("tt0167743", "The Wild Thornberrys"),
        ("tt0244926", "Rocket Power"),
        ("tt0131664", "The Angry Beavers"),
        ("tt0108684", "Aaahh!!! Real Monsters"),
        ("tt0318233", "My Life as a Teenage Robot"),
        ("tt0235916", "ChalkZone"),
        ("tt0235911", "As Told by Ginger"),
        ("tt0387714", "All Grown Up!"),
        ("tt0101178", "The Ren & Stimpy Show"),
        ("tt0892700", "The Penguins of Madagascar"),
        ("tt1545214", "Kung Fu Panda: Legends of Awesomeness"),
        ("tt0101084", "Doug"),
        ("tt0122353", "KaBlam!"),
        ("tt0163929", "Blue's Clues"),
        ("tt0805837", "El Tigre: The Adventures of Manny Rivera"),
        ("tt1170236", "Making Fiends"),
        ("tt0443418", "The X's"),
        ("tt0421306", "Catscratch"),
        ("tt0853078", "Tak and the Power of Juju"),
        ("tt1059741", "Wayside"),
        ("tt0857277", "Back at the Barnyard"),
        ("tt0917551", "The Mighty B!"),
        ("tt1299440", "Fanboy & Chum Chum"),
        ("tt2869898", "Sanjay and Craig"),
        ("tt3219170", "Harvey Beaks"),
        ("tt0457246", "Kappa Mikey"),
        ("tt1492090", "Planet Sheen"),
        ("tt2782214", "Monsters vs. Aliens"),
        ("tt3481544", "Breadwinners"),
        ("tt3105674", "Rabbids Invasion"),
        ("tt0421482", "Winx Club"),
        ("tt1227695", "Three Delivery"),
        ("tt0446208", "Corneil and Bernie"),
        ("tt0457541", "Skyland"),
        ("tt1133691", "Edgar & Ellen"),
        ("tt3218114", "Pig Goat Banana Cricket"),
        ("tt6601082", "Rise of the Teenage Mutant Ninja Turtles"),
        ("tt0439349", "The Backyardigans"),
        ("tt0293734", "Oswald"),
        ("tt0229141", "Little Bill"),
        ("tt0235917", "Dora the Explorer"),
        ("tt0423657", "Go, Diego! Go!"),
        ("tt0775407", "Wonder Pets!"),
        ("tt1594381", "Team Umizoomi")
    ],
    "classics-shows": [
        ("tt0088631", "ThunderCats (1985)"),
        ("tt0126171", "She-Ra: Princess of Power (1985)"),
        ("tt0086824", "Voltron: Defender of the Universe (1984)"),
        ("tt0086719", "G.I. Joe: A Real American Hero (1983)"),
        ("tt0098763", "Captain Planet and the Planeteers"),
        ("tt0057730", "Jonny Quest (1964)"),
        ("tt0108903", "ReBoot"),
        ("tt3559124", "The Tom and Jerry Show"),
        ("tt0130417", "The New Tom & Jerry Show"),
        ("tt0198254", "Tom & Jerry Kids Show"),
        ("tt0053502", "The Flintstones"),
        ("tt0055683", "The Jetsons"),
        ("tt0063950", "Scooby-Doo, Where Are You!"),
        ("tt0074053", "The Scooby-Doo Show"),
        ("tt0306274", "What's New, Scooby-Doo?"),
        ("tt1660055", "Scooby-Doo! Mystery Incorporated"),
        ("tt0122365", "Wacky Races (1968)"),
        ("tt0105941", "Animaniacs"),
        ("tt0112123", "Pinky and the Brain"),
        ("tt0098929", "Tiny Toon Adventures"),
        ("tt0111970", "Freakazoid!"),
        ("tt0085033", "Inspector Gadget"),
        ("tt0081933", "The Smurfs"),
        ("tt0054572", "Top Cat"),
        ("tt0255768", "The Yogi Bear Show"),
        ("tt0070996", "Hong Kong Phooey"),
        ("tt0094469", "Garfield and Friends"),
        ("tt8543208", "Looney Tunes Cartoons"),
        ("tt0084972", "Alvin and the Chipmunks"),
        ("tt0145628", "Popeye the Sailor"),
        ("tt1726839", "The Looney Tunes Show"),
        ("tt0780438", "Tom and Jerry Tales"),
        ("tt1470837", "The Garfield Show"),
        ("tt0280277", "Mr. Bean: The Animated Series"),
        ("tt0213363", "Oggy and the Cockroaches"),
        ("tt2046005", "Zig & Sharko"),
        ("tt0983983", "Shaun the Sheep"),
        ("tt0169414", "Arthur"),
        ("tt0309141", "Cyberchase"),
        ("tt0179552", "The Adventures of Tintin"),
        ("tt0108847", "The Magic School Bus"),
        ("tt0103373", "Bobby's World"),
        ("tt0103408", "Eek! the Cat"),
        ("tt0112196", "The Tick (1994)"),
        ("tt0224455", "Angela Anaconda"),
        ("tt0229132", "Grizzly Tales for Gruesome Kids"),
        ("tt0094531", "A Pup Named Scooby-Doo"),
        ("tt0088628", "The 13 Ghosts of Scooby-Doo"),
        ("tt0068112", "The New Scooby-Doo Movies"),
        ("tt4215734", "Be Cool, Scooby-Doo!"),
        ("tt0112186", "The Sylvester & Tweety Mysteries"),
        ("tt0103562", "Taz-Mania"),
        ("tt0338580", "Baby Looney Tunes"),
        ("tt0063889", "Dastardly and Muttley in Their Flying Machines"),
        ("tt0063939", "The Pink Panther Show"),
        ("tt0065307", "Josie and the Pussycats"),
        ("tt0284712", "Captain Caveman and the Teen Angels"),
        ("tt0177447", "Jabberjaw"),
        ("tt0105988", "Droopy: Master Detective"),
        ("tt0088500", "Count Duckula"),
        ("tt4196822", "Danger Mouse"),
        ("tt0084996", "The Charlie Brown and Snoopy Show"),
        ("tt0051283", "The Huckleberry Hound Show"),
        ("tt0100366", "Pingu"),
        ("tt0262151", "Bob the Builder"),
        ("tt0086815", "Thomas & Friends"),
        ("tt0329829", "Fireman Sam"),
        ("tt0445882", "The Koala Brothers"),
        ("tt0449545", "Curious George"),
        ("tt0233033", "The Berenstain Bears"),
        ("tt0243061", "Dragon Tales"),
        ("tt1783822", "Babar and the Adventures of Badou")
    ],
    "action-shows": [
        ("tt0168366", "Pokémon (Pokemon: The Series)"),
        ("tt3218680", "Pokémon Origins"),
        ("tt6071336", "Pokémon Generations"),
        ("tt15356258", "Pokémon Evolutions"),
        ("tt0103359", "Batman: The Animated Series"),
        ("tt0115378", "Superman: The Animated Series"),
        ("tt0147746", "Batman Beyond"),
        ("tt0275137", "Justice League"),
        ("tt6025022", "Justice League Unlimited"),
        ("tt1641384", "Young Justice"),
        ("tt0112175", "Spider-Man: The Animated Series (1994)"),
        ("tt0976192", "The Spectacular Spider-Man"),
        ("tt0103584", "X-Men: The Animated Series (1992)"),
        ("tt16026746", "X-Men '97"),
        ("tt0131613", "Teenage Mutant Ninja Turtles (1987)"),
        ("tt0318913", "Teenage Mutant Ninja Turtles (2003)"),
        ("tt0086817", "The Transformers (1984)"),
        ("tt0115108", "Beast Wars: Transformers"),
        ("tt0121220", "Dragon Ball Z"),
        ("tt0088509", "Dragon Ball"),
        ("tt4644488", "Dragon Ball Super"),
        ("tt0139774", "Dragon Ball GT"),
        ("tt1409055", "Dragon Ball Z Kai"),
        ("tt0772145", "Wolverine and the X-Men"),
        ("tt1626038", "The Avengers: Earth's Mightiest Heroes"),
        ("tt0837143", "Iron Man: Armored Adventures"),
        ("tt0247729", "Static Shock"),
        ("tt1724587", "Green Lantern: The Animated Series"),
        ("tt6741278", "Invincible"),
        ("tt6517102", "Castlevania"),
        ("tt11126994", "Arcane"),
        ("tt0398417", "The Batman (2004)"),
        ("tt1213218", "Batman: The Brave and the Bold"),
        ("tt0775372", "Legion of Super Heroes"),
        ("tt0260662", "The Zeta Project"),
        ("tt0830298", "Fantastic Four: World's Greatest Heroes"),
        ("tt0259141", "Jackie Chan Adventures"),
        ("tt0127385", "Men in Black: The Series"),
        ("tt0177443", "Godzilla: The Series"),
        ("tt0247902", "Yu-Gi-Oh! Duel Monsters"),
        ("tt0493334", "Yu-Gi-Oh! GX"),
        ("tt1196094", "Yu-Gi-Oh! 5D's"),
        ("tt2363624", "Yu-Gi-Oh! Zexal"),
        ("tt3696476", "Yu-Gi-Oh! Arc-V"),
        ("tt5628740", "Yu-Gi-Oh! VRAINS"),
        ("tt0210418", "Digimon Adventure"),
        ("tt0243694", "Digimon Adventure 02"),
        ("tt0295080", "Digimon Tamers"),
        ("tt0316975", "Digimon Frontier"),
        ("tt1138300", "Digimon Data Squad"),
        ("tt2746566", "Digimon Fusion"),
        ("tt0328733", "Beyblade (2001)"),
        ("tt1674928", "Beyblade: Metal Fusion"),
        ("tt6348126", "Beyblade Burst"),
        ("tt0293731", "Medabots"),
        ("tt1524993", "Dinosaur King"),
        ("tt1696969", "Huntik: Secrets & Seekers"),
        ("tt2748608", "Max Steel (2013)"),
        ("tt0367409", "Shaman King"),
        ("tt0367413", "Sonic X"),
        ("tt0106140", "Sonic the Hedgehog (SatAM)"),
        ("tt0126173", "Swat Kats: The Radical Squadron"),
        ("tt0103559", "Street Sharks"),
        ("tt0147752", "Biker Mice from Mars"),
        ("tt0409591", "Naruto"),
        ("tt0988824", "Naruto: Shippuden"),
        ("tt0388629", "One Piece"),
        ("tt0434665", "Bleach"),
        ("tt0290223", "InuYasha"),
        ("tt0185133", "Yu Yu Hakusho"),
        ("tt0159193", "Mobile Suit Gundam Wing"),
        ("tt0159182", "Mobile Fighter G Gundam"),
        ("tt0266171", "Outlaw Star"),
        ("tt0105559", "Tenchi Muyo!"),
        ("tt0251439", "Trigun"),
        ("tt0182629", "Rurouni Kenshin"),
        ("tt0188359", "Cyborg 009"),
        ("tt0280240", "The Big O"),
        ("tt1355642", "Fullmetal Alchemist: Brotherhood"),
        ("tt0877057", "Death Note"),
        ("tt2098220", "Hunter x Hunter"),
        ("tt2560140", "Attack on Titan"),
        ("tt1214085", "Soul Eater"),
        ("tt0213338", "Cowboy Bebop"),
        ("tt0423731", "Samurai Champloo"),
        ("tt0103369", "Sailor Moon"),
        ("tt0455295", "Zatch Bell!"),
        ("tt0450373", "Bobobo-bo Bo-bobo"),
        ("tt0338621", "Kirby: Right Back at Ya!"),
        ("tt0218775", "Monster Rancher"),
        ("tt0850635", "Chaotic"),
        ("tt1579911", "Monsuno"),
        ("tt0247827", "X-Men: Evolution"),
        ("tt1722512", "Ultimate Spider-Man"),
        ("tt0290983", "Spider-Man: The New Animated Series"),
        ("tt0207120", "Spider-Man Unlimited"),
        ("tt0083481", "Spider-Man and His Amazing Friends"),
        ("tt2455546", "Avengers Assemble"),
        ("tt2455514", "Hulk and the Agents of S.M.A.S.H."),
        ("tt1388589", "The Super Hero Squad Show"),
        ("tt0187635", "Fantastic Four: The Animated Series"),
        ("tt0203268", "Silver Surfer"),
        ("tt2329077", "Beware the Batman"),
        ("tt1659175", "Transformers: Prime"),
        ("tt1055335", "Transformers: Animated"),
        ("tt0329938", "Transformers: Armada"),
        ("tt0388650", "Transformers: Energon"),
        ("tt0472252", "Transformers: Cybertron"),
        ("tt0126158", "He-Man and the Masters of the Universe (1983)"),
        ("tt0331744", "He-Man and the Masters of the Universe (2002)"),
        ("tt0090520", "SilverHawks"),
        ("tt0090506", "The Real Ghostbusters"),
        ("tt0056739", "Astro Boy"),
        ("tt0230804", "Sonic Underground"),
        ("tt3232262", "Sonic Boom"),
        ("tt0476918", "Loonatics Unleashed"),
        ("tt5580664", "Voltron: Legendary Defender"),
        ("tt7745956", "She-Ra and the Princesses of Power"),
        ("tt10482560", "Kipo and the Age of Wonderbeasts"),
        ("tt1807824", "Wakfu")
    ],
    "cartoon-movies": [
        # SpongeBob Movies (1–3)
        ("tt0345950", "The SpongeBob SquarePants Movie"),
        ("tt2279373", "The SpongeBob Movie: Sponge Out of Water"),
        ("tt4823776", "The SpongeBob Movie: Sponge on the Run"),
        # Ben 10 Movies (All 5)
        ("tt1146431", "Ben 10: Secret of the Omnitrix"),
        ("tt1037011", "Ben 10: Race Against Time"),
        ("tt1327701", "Ben 10: Alien Swarm"),
        ("tt2290147", "Ben 10: Destroy All Aliens"),
        ("tt13186528", "Ben 10 Versus the Universe: The Movie"),
        # Pokémon Movies (1–23 + Detective & Specials)
        ("tt0190641", "Pokémon: The First Movie - Mewtwo Strikes Back"),
        ("tt0210234", "Pokémon the Movie 2000"),
        ("tt0235679", "Pokémon 3: The Movie"),
        ("tt0287635", "Pokémon 4Ever: Celebi - Voice of the Forest"),
        ("tt0347791", "Pokémon Heroes: Latios and Latias"),
        ("tt0420076", "Pokémon: Jirachi - Wish Maker"),
        ("tt0435286", "Pokémon: Destiny Deoxys"),
        ("tt0875609", "Pokémon: Lucario and the Mystery of Mew"),
        ("tt1000095", "Pokémon Ranger and the Temple of the Sea"),
        ("tt1226251", "Pokémon: The Rise of Darkrai"),
        ("tt1160525", "Pokémon: Giratina and the Sky Warrior"),
        ("tt1468843", "Pokémon: Arceus and the Jewel of Life"),
        ("tt1690470", "Pokémon—Zoroark: Master of Illusions"),
        ("tt1961324", "Pokémon the Movie: Black—Victini and Reshiram"),
        ("tt1739212", "Pokémon the Movie: White—Victini and Zekrom"),
        ("tt2549540", "Pokémon the Movie: Kyurem vs. the Sword of Justice"),
        ("tt3257582", "Pokémon the Movie: Genesect and the Legend Awakened"),
        ("tt3918368", "Pokémon the Movie: Diancie and the Cocoon of Destruction"),
        ("tt4503906", "Pokémon the Movie: Hoopa and the Clash of Ages"),
        ("tt5889204", "Pokémon the Movie: Volcanion and the Mechanical Marvel"),
        ("tt6595896", "Pokémon the Movie: I Choose You!"),
        ("tt8108230", "Pokémon the Movie: The Power of Us"),
        ("tt8856470", "Pokémon: Mewtwo Strikes Back - Evolution"),
        ("tt11819890", "Pokémon the Movie: Secrets of the Jungle"),
        # Digimon, Yu-Gi-Oh! & Dragon Ball Movies
        ("tt0259974", "Digimon: The Movie"),
        ("tt0403703", "Yu-Gi-Oh!: The Movie - Pyramid of Light"),
        ("tt1587157", "Yu-Gi-Oh! Bonds Beyond Time"),
        ("tt4273562", "Yu-Gi-Oh!: The Dark Side of Dimensions"),
        ("tt2263944", "Dragon Ball Z: Battle of Gods"),
        ("tt3819668", "Dragon Ball Z: Resurrection 'F'"),
        ("tt7961060", "Dragon Ball Super: Broly"),
        ("tt14614892", "Dragon Ball Super: Super Hero"),
        # Cartoon Network, Nickelodeon & Disney TV Movies
        ("tt1825918", "Phineas and Ferb the Movie: Across the 2nd Dimension"),
        ("tt1817232", "Phineas and Ferb the Movie: Candace Against the Universe"),
        ("tt0289408", "The Powerpuff Girls Movie"),
        ("tt1232047", "Ed, Edd n Eddy's Big Picture Show"),
        ("tt10515852", "Steven Universe: The Movie"),
        ("tt10474606", "We Bare Bears: The Movie"),
        ("tt1000070", "Billy & Mandy's Big Boogey Adventure"),
        ("tt0837113", "Codename: Kids Next Door - Operation Z.E.R.O."),
        ("tt4920274", "Regular Show: The Movie"),
        ("tt0816671", "Teen Titans: Trouble in Tokyo"),
        ("tt7424200", "Teen Titans GO! To the Movies"),
        ("tt0268397", "Jimmy Neutron: Boy Genius"),
        ("tt0414177", "The Jimmy Timmy Power Hour"),
        ("tt0473050", "The Jimmy Timmy Power Hour 2: When Nerds Collide!"),
        ("tt0499605", "The Jimmy Timmy Power Hour 3: The Jerkinators!"),
        ("tt39055318", "The Fairly OddParents: Abra-Catastrophe!"),
        ("tt0419739", "The Fairly OddParents: Channel Chasers"),
        ("tt0134067", "The Rugrats Movie"),
        ("tt0213203", "Rugrats in Paris"),
        ("tt0337711", "Rugrats Go Wild"),
        ("tt0282120", "The Wild Thornberrys Movie"),
        ("tt0314166", "Hey Arnold! The Movie"),
        ("tt5257726", "Hey Arnold: The Jungle Movie"),
        ("tt0265632", "Recess: School's Out"),
        ("tt0389074", "Kim Possible: A Sitch in Time"),
        ("tt0446724", "Kim Possible Movie: So the Drama"),
        ("tt0099472", "DuckTales: The Movie - Treasure of the Lost Lamp"),
        ("tt0113198", "A Goofy Movie"),
        ("tt0208185", "An Extremely Goofy Movie"),
        # Scooby-Doo & Tom and Jerry Movies
        ("tt0166792", "Scooby-Doo on Zombie Island"),
        ("tt0196931", "Scooby-Doo and the Witch's Ghost"),
        ("tt0253658", "Scooby-Doo and the Alien Invaders"),
        ("tt0290057", "Scooby-Doo and the Cyber Chase"),
        ("tt0357139", "Scooby-Doo and the Legend of the Vampire"),
        ("tt0369903", "Scooby-Doo and the Monster of Mexico"),
        ("tt0867418", "Scooby-Doo! Pirates Ahoy!"),
        ("tt1599351", "Scooby-Doo! Abracadabra-Doo"),
        ("tt1731767", "Scooby-Doo! Camp Scare"),
        ("tt1777608", "Scooby-Doo! Legend of the Phantosaur"),
        ("tt3025994", "Scooby-Doo! Stage Fright"),
        ("tt3152592", "Scoob!"),
        ("tt0303151", "Tom and Jerry: The Magic Ring"),
        ("tt0433696", "Tom and Jerry: Blast Off to Mars!"),
        ("tt0487176", "Tom and Jerry: The Fast and the Furry"),
        ("tt0808508", "Tom and Jerry: Shiver Me Whiskers"),
        ("tt1114698", "Tom and Jerry: A Nutcracker Tale"),
        ("tt1722638", "Tom and Jerry Meet Sherlock Holmes"),
        # DC, Marvel, Transformers, TMNT & Lego Animated Movies & Sequels
        ("tt0106364", "Batman: Mask of the Phantasm"),
        ("tt0233298", "Batman Beyond: Return of the Joker"),
        ("tt0472219", "The Batman vs. Dracula"),
        ("tt1569923", "Batman: Under the Red Hood"),
        ("tt3139086", "Batman: Assault on Arkham"),
        ("tt1398941", "Superman/Batman: Public Enemies"),
        ("tt1494772", "Justice League: Crisis on Two Earths"),
        ("tt2027128", "Justice League: Doom"),
        ("tt2820466", "Justice League: The Flashpoint Paradox"),
        ("tt3060952", "Justice League: War"),
        ("tt2494376", "Justice League Dark"),
        ("tt11079148", "Justice League Dark: Apokolips War"),
        ("tt7167658", "The Death of Superman"),
        ("tt7167686", "Reign of the Supermen"),
        ("tt4633694", "Spider-Man: Into the Spider-Verse"),
        ("tt9362722", "Spider-Man: Across the Spider-Verse"),
        ("tt0491703", "Ultimate Avengers: The Movie"),
        ("tt1483025", "Planet Hulk"),
        ("tt0092106", "The Transformers: The Movie (1986)"),
        ("tt0453556", "TMNT (2007)"),
        ("tt1543920", "Turtles Forever"),
        ("tt1490017", "The Lego Movie"),
        ("tt3513498", "The Lego Movie 2: The Second Part"),
        ("tt4116284", "The Lego Batman Movie"),
        # Pixar Feature Films & Sequels
        ("tt0114709", "Toy Story"),
        ("tt0120363", "Toy Story 2"),
        ("tt0435761", "Toy Story 3"),
        ("tt1979376", "Toy Story 4"),
        ("tt0317705", "The Incredibles"),
        ("tt3606756", "Incredibles 2"),
        ("tt0198781", "Monsters, Inc."),
        ("tt1453405", "Monsters University"),
        ("tt0266543", "Finding Nemo"),
        ("tt2277860", "Finding Dory"),
        ("tt0317219", "Cars"),
        ("tt1216475", "Cars 2"),
        ("tt3606752", "Cars 3"),
        ("tt2096673", "Inside Out"),
        ("tt22022452", "Inside Out 2"),
        ("tt0120623", "A Bug's Life"),
        ("tt0382932", "Ratatouille"),
        ("tt0910970", "WALL·E"),
        ("tt1049413", "Up"),
        ("tt2380307", "Coco"),
        # DreamWorks Animation Franchises & Sequels
        ("tt0126029", "Shrek"),
        ("tt0298148", "Shrek 2"),
        ("tt0413267", "Shrek the Third"),
        ("tt0892791", "Shrek Forever After"),
        ("tt0448694", "Puss in Boots"),
        ("tt3915174", "Puss in Boots: The Last Wish"),
        ("tt0441773", "Kung Fu Panda"),
        ("tt1302011", "Kung Fu Panda 2"),
        ("tt2267968", "Kung Fu Panda 3"),
        ("tt21692408", "Kung Fu Panda 4"),
        ("tt0892769", "How to Train Your Dragon"),
        ("tt1646971", "How to Train Your Dragon 2"),
        ("tt2386490", "How to Train Your Dragon: The Hidden World"),
        ("tt0351283", "Madagascar"),
        ("tt0479952", "Madagascar: Escape 2 Africa"),
        ("tt1277953", "Madagascar 3: Europe's Most Wanted"),
        ("tt1911658", "Penguins of Madagascar"),
        ("tt0481499", "The Croods"),
        ("tt2850386", "The Croods: A New Age"),
        ("tt1001526", "Megamind"),
        ("tt0327084", "Over the Hedge"),
        ("tt0424095", "Flushed Away"),
        ("tt0312004", "Wallace & Gromit: The Curse of the Were-Rabbit"),
        ("tt0120630", "Chicken Run"),
        ("tt0120794", "The Prince of Egypt"),
        ("tt0138749", "The Road to El Dorado"),
        ("tt0166813", "Spirit: Stallion of the Cimarron"),
        ("tt0307453", "Shark Tale"),
        ("tt0389790", "Bee Movie"),
        ("tt0892782", "Monsters vs. Aliens"),
        ("tt1446192", "Rise of the Guardians"),
        # Blue Sky, Illumination & Sony Animation Franchises & Sequels
        ("tt0268380", "Ice Age"),
        ("tt0438097", "Ice Age: The Meltdown"),
        ("tt1080016", "Ice Age: Dawn of the Dinosaurs"),
        ("tt1667889", "Ice Age: Continental Drift"),
        ("tt3416828", "Ice Age: Collision Course"),
        ("tt1323594", "Despicable Me"),
        ("tt1690953", "Despicable Me 2"),
        ("tt3469046", "Despicable Me 3"),
        ("tt7510222", "Despicable Me 4"),
        ("tt2293640", "Minions"),
        ("tt5113044", "Minions: The Rise of Gru"),
        ("tt0837562", "Hotel Transylvania"),
        ("tt2510894", "Hotel Transylvania 2"),
        ("tt5220122", "Hotel Transylvania 3: Summer Vacation"),
        ("tt9848626", "Hotel Transylvania: Transformania"),
        ("tt0844471", "Cloudy with a Chance of Meatballs"),
        ("tt1985966", "Cloudy with a Chance of Meatballs 2"),
        ("tt1436562", "Rio"),
        ("tt2357291", "Rio 2"),
        ("tt0400717", "Open Season"),
        ("tt1107365", "Open Season 2"),
        ("tt1646926", "Open Season 3"),
        ("tt0423294", "Surf's Up"),
        ("tt0358082", "Robots"),
        ("tt0451079", "Horton Hears a Who!"),
        ("tt2452042", "The Peanuts Movie"),
        # Disney Classics & Sequels + Cult Favorites
        ("tt0110357", "The Lion King (1994)"),
        ("tt0120131", "The Lion King II: Simba's Pride"),
        ("tt0318403", "The Lion King 1½"),
        ("tt0103639", "Aladdin (1992)"),
        ("tt0107952", "The Return of Jafar"),
        ("tt0115491", "Aladdin and the King of Thieves"),
        ("tt0275847", "Lilo & Stitch"),
        ("tt0348124", "Stitch! The Movie"),
        ("tt0457993", "Lilo & Stitch 2: Stitch Has a Glitch"),
        ("tt0486761", "Leroy & Stitch"),
        ("tt0120917", "The Emperor's New Groove"),
        ("tt0401398", "Kronk's New Groove"),
        ("tt0230011", "Atlantis: The Lost Empire"),
        ("tt0344864", "Atlantis: Milo's Return"),
        ("tt0133240", "Treasure Planet"),
        ("tt0120855", "Tarzan"),
        ("tt0437503", "Tarzan II"),
        ("tt0313680", "Tarzan & Jane"),
        ("tt0119282", "Hercules"),
        ("tt0120762", "Mulan"),
        ("tt0279967", "Mulan II"),
        ("tt1772341", "Wreck-It Ralph"),
        ("tt5848272", "Ralph Breaks the Internet"),
        ("tt2245084", "Big Hero 6"),
        ("tt2294629", "Frozen"),
        ("tt4520988", "Frozen II"),
        ("tt0398286", "Tangled"),
        ("tt2948356", "Zootopia"),
        ("tt3521164", "Moana"),
        ("tt2953050", "Encanto"),
        ("tt0328880", "Brother Bear"),
        ("tt0465925", "Brother Bear 2"),
        ("tt0396555", "Meet the Robinsons"),
        ("tt0397892", "Bolt"),
        ("tt0097757", "The Little Mermaid"),
        ("tt0240684", "The Little Mermaid II: Return to the Sea"),
        ("tt0101414", "Beauty and the Beast"),
        ("tt0061852", "The Jungle Book"),
        ("tt0283426", "The Jungle Book 2"),
        ("tt0046183", "Peter Pan"),
        ("tt0280030", "Return to Never Land"),
        ("tt0055254", "One Hundred and One Dalmatians"),
        ("tt0324941", "101 Dalmatians II: Patch's London Adventure"),
        ("tt0100477", "The Rescuers Down Under"),
        ("tt0082406", "The Fox and the Hound"),
        ("tt0034492", "Bambi"),
        ("tt0447854", "Bambi II"),
        ("tt0042332", "Cinderella"),
        ("tt0076363", "The Many Adventures of Winnie the Pooh"),
        ("tt1449283", "Winnie the Pooh"),
        ("tt0107688", "The Nightmare Before Christmas"),
        ("tt0129167", "The Iron Giant"),
        ("tt0385880", "Monster House"),
        ("tt0327597", "Coraline"),
        ("tt0462538", "The Simpsons Movie"),
        ("tt0472033", "9"),
        ("tt1192628", "Rango"),
        ("tt0983193", "The Adventures of Tintin (2011)")
    ]
}

FALLBACK_METADATA = {
    "tt0168366": ("series", "Pokémon (Pokemon: The Series)", ["Animation", "Action", "Adventure"], "7.6", "1997–2023", "On his 10th birthday, Ash Ketchum starts his Pokémon (Pokemon) journey with Pikachu. Together with Brock, Misty, and friends, he battles Gym Leaders, Team Rocket, and legendary Pokémon across every region."),
    "tt1294022": ("series", "Pokémon Chronicles", ["Animation", "Action", "Adventure"], "7.2", "2002–2004", "Spin-off anthology series of the Pokémon (Pokemon) anime focusing on Brock, Misty, Richie, Tracey, Team Rocket, and legendary Pokémon adventures across Johto and Kanto."),
    "tt29079338": ("series", "Pokémon Journeys: The Series", ["Animation", "Action", "Adventure"], "7.5", "2019–2023", "Ash Ketchum and Pikachu team up with new research fellow Goh to travel across all eight Pokémon (Pokemon) regions while Ash battles his way to the Masters Eight Tournament."),
    "tt26692417": ("series", "Pokémon Horizons: The Series", ["Animation", "Action", "Adventure"], "7.4", "2023–", "Dual protagonists Liko and Roy join the Rising Volt Tacklers aboard an airship to unravel the mysteries of Liko's pendant, the Ancient Poké Ball, and the Pokémon (Pokemon) world."),
    "tt11547516": ("series", "Pokémon: Twilight Wings", ["Animation", "Adventure", "Family"], "7.6", "2020", "Set in the Galar region, this animated Pokémon (Pokemon) miniseries follows the dreams, challenges, and bonds of young trainers and Gym Leaders."),
    "tt26916286": ("series", "Pokémon Concierge", ["Animation", "Comedy", "Family"], "7.5", "2023–", "At the Pokémon (Pokemon) Resort, new concierge Haru and her Psyduck care for visiting Pokémon guests in this charming stop-motion animated series."),
    "tt3218680": ("series", "Pokémon Origins", ["Animation", "Action", "Adventure"], "8.0", "2013", "A faithful four-part animated adaptation of the original Pokémon (Pokemon) Red and Blue video games following Red and his Charmander as they battle rival Blue, Team Rocket, and Mewtwo."),
    "tt6071336": ("series", "Pokémon Generations", ["Animation", "Action", "Adventure"], "7.7", "2016", "An 18-part action-packed anthology series exploring untold stories, legendary battles, and villainous plots from across the first six generations of the Pokémon (Pokemon) games."),
    "tt15356258": ("series", "Pokémon Evolutions", ["Animation", "Action", "Adventure"], "7.6", "2021", "Celebrating 25 years of Pokémon (Pokemon), this eight-episode animated series journeys backward from Galar to Kanto through pivotal moments in Pokémon history."),
    "tt0088631": ("series", "ThunderCats (1985)", ["Animation", "Action", "Adventure"], "7.9", "1985–1989", "Fleeing their dying home planet of Thundera, young Lord Lion-O and the noble ThunderCats—Tygra, Panthro, Cheetara, WilyKit, WilyKat, and Snarf—wield the Sword of Omens against Mumm-Ra on Third Earth."),
    "tt1666278": ("series", "ThunderCats (2011)", ["Animation", "Action", "Adventure"], "7.8", "2011–2012", "After his home kingdom of Thundera is destroyed by the ancient devil priest Mumm-Ra, young Lord Lion-O leads the ThunderCats survivors as they fight evil on Third Earth."),
    "tt8435344": ("series", "ThunderCats Roar", ["Animation", "Action", "Comedy"], "4.2", "2020", "Lion-O and the ThunderCats—Tygra, Panthro, Cheetara, WilyKit, and WilyKat—escape the destruction of Thundera and battle Mumm-Ra on Third Earth."),
    "tt6148376": ("series", "Ben 10 (2016)", ["Animation", "Action", "Sci-Fi"], "4.5", "2016–2021", "Ten-year-old Ben Tennyson discovers the Omnitrix during a summer road trip with Grandpa Max and cousin Gwen, unlocking the power to transform into ten alien heroes."),
    "tt11165358": ("series", "Adventure Time: Distant Lands", ["Animation", "Adventure", "Fantasy"], "8.7", "2020–2021", "Four feature-length Adventure Time specials following BMO in outer space, Marceline and Princess Bubblegum, Peppermint Butler, and Finn and Jake's greatest adventure together."),
    "tt15248880": ("series", "Adventure Time: Fionna & Cake", ["Animation", "Action", "Adventure"], "8.9", "2023–", "Fionna Campbell and her magical cat Cake travel across the multiverse alongside former Ice King Simon Petrikov while evading a powerful cosmic auditor."),
    "tt13714610": ("series", "Steven Universe Future", ["Animation", "Action", "Adventure"], "8.2", "2019–2020", "After saving the universe and establishing Little Homeschool on Earth, teenage Steven Universe confronts his own unresolved trauma and newly awakening Diamond powers."),
    "tt4718304": ("series", "The Powerpuff Girls (2016)", ["Animation", "Action", "Comedy"], "3.6", "2016–2019", "Superhero sisters Blossom, Bubbles, and Buttercup juggle school and saving Townsville from monsters, supervillains, and giant threats."),
    "tt0108937": ("series", "Space Ghost Coast to Coast", ["Animation", "Comedy", "Talk-Show"], "7.9", "1994–2008", "Retired Hanna-Barbera superhero Space Ghost hosts a surreal late-night talk show from the Ghost Planet alongside his former arch-enemies Zorak and Moltar."),
    "tt0105928": ("series", "2 Stupid Dogs", ["Animation", "Comedy", "Family"], "7.2", "1993–1995", "Two dim-witted stray dogs—a tiny hyperactive dachshund and a massive laconic sheepdog—wander through misadventures in 1990s suburbia, paired with Secret Squirrel shorts."),
    "tt0115226": ("series", "The Real Adventures of Jonny Quest", ["Animation", "Action", "Adventure"], "7.4", "1996–1997", "Teenage Jonny Quest, Hadji, Jessie Bannon, Race Bannon, and Dr. Benton Quest investigate global phenomena and cyberspace mysteries inside the virtual world of QuestWorld."),
    "tt0279077": ("series", "FLCL", ["Animation", "Action", "Comedy"], "8.1", "2000–2001", "Twelve-year-old Naota Nandaba's boring suburban life is turned upside down when Vespa-riding alien Haruko Haruhara hits him with a bass guitar, causing giant robots to sprout from his forehead."),
    "tt0088528": ("series", "Adventures of the Gummi Bears", ["Animation", "Adventure", "Family"], "7.5", "1985–1991", "A secret colony of mythical Gummi Bears in Gummi Glen uses magical Gummiberry Juice to protect the kingdom of Dunwyn from the scheming Duke Igthorn and his ogres."),
    "tt0213334": ("series", "Bonkers", ["Animation", "Comedy", "Crime"], "6.8", "1993–1994", "Washed-up cartoon star Bonkers D. Bobcat joins the Hollywood Police Department's Toon Division alongside grumpy human detective Lucky Piquel."),
    "tt0136658": ("series", "Quack Pack", ["Animation", "Adventure", "Comedy"], "6.7", "1996", "Donald Duck works as a globe-trotting TV cameraman alongside Daisy Duck while raising his now-teenage nephews Huey, Dewey, and Louie."),
    "tt12708542": ("series", "Star Wars: The Bad Batch", ["Animation", "Action", "Adventure"], "7.8", "2021–2024", "Clone Force 99, an elite squad of genetically mutated clone troopers, navigates a rapidly changing galaxy in the immediate aftermath of the Clone Wars and Order 66."),
    "tt1710310": ("series", "T.U.F.F. Puppy", ["Animation", "Action", "Comedy"], "6.1", "2010–2015", "Dim-witted but enthusiastic dog Dudley Puppy is recruited into the Turbo Undercover Fighting Force (T.U.F.F.) and partnered with top feline agent Kitty Katswell to protect Petropolis."),
    "tt9165462": ("series", "The Casagrandes", ["Animation", "Comedy", "Family"], "6.2", "2019–2022", "Eleven-year-old Ronnie Anne Santiago and her brother Bobby adjust to life in Great Lakes City living above their family's bodega with their large, loving multigenerational Mexican-American family."),
    "tt0126171": ("series", "She-Ra: Princess of Power (1985)", ["Animation", "Action", "Adventure"], "7.0", "1985–1987", "Princess Adora, twin sister of Prince Adam (He-Man), transforms into She-Ra, Princess of Power, to lead the Great Rebellion against Hordak and the Evil Horde on Etheria."),
    "tt0086824": ("series", "Voltron: Defender of the Universe (1984)", ["Animation", "Action", "Sci-Fi"], "7.9", "1984–1985", "Five young space explorers pilot robotic lions that combine to form Voltron, the mighty super-robot defender of the peaceful planet Arus against King Zarkon's Robeasts."),
    "tt0086719": ("series", "G.I. Joe: A Real American Hero (1983)", ["Animation", "Action", "Adventure"], "7.9", "1983–1986", "Duke, Snake Eyes, Scarlett, and the elite G.I. Joe special mission force defend freedom around the world against Cobra Commander, Destro, and the ruthless terrorist organization Cobra."),
    "tt0098763": ("series", "Captain Planet and the Planeteers", ["Animation", "Action", "Adventure"], "6.6", "1990–1996", "Gaia, the spirit of the Earth, grants five magic elemental rings to youths from across the globe who combine their powers to summon environmental superhero Captain Planet."),
    "tt0122365": ("series", "Wacky Races (1968)", ["Animation", "Comedy", "Family"], "7.5", "1968–1969", "Eleven eccentric racers—including Penelope Pitstop, Peter Perfect, the Ant Hill Mob, and scheming villain Dick Dastardly with his snickering dog Muttley—compete in cross-country road rallies."),
    "tt0074053": ("series", "The Scooby-Doo Show", ["Animation", "Adventure", "Comedy"], "7.8", "1976–1978", "Scooby-Doo, Shaggy, Fred, Daphne, and Velma—frequently joined by Scooby's country cousin Scooby-Dum—solve spooky supernatural mysteries across the globe."),
    "tt0057730": ("series", "Jonny Quest (1964)", ["Animation", "Action", "Adventure"], "7.8", "1964–1965", "Eleven-year-old Jonny Quest accompanies his scientist father Dr. Benton Quest, bodyguard Race Bannon, adoptive brother Hadji, and bulldog Bandit on high-stakes global adventures."),
    "tt0108903": ("series", "ReBoot", ["Animation", "Action", "Sci-Fi"], "7.9", "1994–2001", "Inside the digital metropolis of Mainframe, Guardian Bob, Enzo, and Dot Matrix defend their system from incoming User games and the schemes of viruses Megabyte and Hexadecimal."),
    "tt0103373": ("series", "Bobby's World", ["Animation", "Comedy", "Family"], "7.3", "1990–1998", "Four-year-old Bobby Generic uses his boundless imagination to navigate family life with his Midwestern parents, siblings, Uncle Ted, and sheepdog Roger."),
    "tt0103408": ("series", "Eek! the Cat", ["Animation", "Comedy", "Family"], "7.2", "1992–1997", "Optimistic purple cat Eek lives by the motto 'It never hurts to help!'—even though helping others invariably lands him in hilarious slapstick disasters alongside Sharky the Sharkdog and the Terrible Thunderlizards."),
    "tt0112196": ("series", "The Tick (1994)", ["Animation", "Action", "Comedy"], "8.0", "1994–1996", "A nigh-invulnerable, blue-suited superhero with more enthusiasm than brains teams up with mild-mannered accountant sidekick Arthur to protect The City from bizarre supervillains."),
    "tt0331744": ("series", "He-Man and the Masters of the Universe (2002)", ["Animation", "Action", "Fantasy"], "7.7", "2002–2004", "Young Prince Adam of Eternia wields the Sword of Power to transform into He-Man, leading the Masters of the Universe against Skeletor, King Hiss, and the Snake Men."),
    "tt0159193": ("series", "Mobile Suit Gundam Wing", ["Animation", "Action", "Sci-Fi"], "7.9", "1995–1996", "In After Colony 195, five teenage pilots from the space colonies are sent to Earth in advanced Gundams to wage guerrilla warfare against the oppressive OZ organization."),
    "tt0159182": ("series", "Mobile Fighter G Gundam", ["Animation", "Action", "Sci-Fi"], "7.7", "1994–1995", "Every four years, the space colonies settle control of the universe through the Gundam Fight tournament on Earth, where martial artist Domon Kasshu pilots the Shining Gundam."),
    "tt0185133": ("series", "Yu Yu Hakusho", ["Animation", "Action", "Fantasy"], "8.5", "1992–1995", "After dying while saving a child's life, teenage delinquent Yusuke Urameshi is resurrected as Underworld Spirit Detective, battling demons alongside Kuwabara, Hiei, and Kurama."),
    "tt0266171": ("series", "Outlaw Star", ["Animation", "Action", "Sci-Fi"], "7.9", "1998", "Bounty hunter Gene Starwind and his partner Jim Hawking acquire the experimental grappler ship Outlaw Star and a mysterious bio-android named Melfina while searching for the Galactic Leyline."),
    "tt0105559": ("series", "Tenchi Muyo!", ["Animation", "Action", "Comedy"], "7.5", "1992–2005", "Ordinary teenager Tenchi Masaki accidentally awakens space pirate Ryoko and soon finds his rural Japanese shrine home filled with alien princesses, galaxy police, and a genius scientist."),
    "tt0251439": ("series", "Trigun", ["Animation", "Action", "Sci-Fi"], "8.2", "1998", "Across the desert planet Gunsmoke, pacifist gunman Vash the Stampede—known as the Humanoid Typhoon with a 60-billion-double-dollar bounty—tries to uphold peace and love while pursued by assassins."),
    "tt0182629": ("series", "Rurouni Kenshin", ["Animation", "Action", "Adventure"], "8.5", "1996–1998", "In Meiji-era Japan, former legendary assassin Himura Kenshin wanders the countryside with a reverse-blade sword, vowing never to kill again while protecting the innocent."),
    "tt0188359": ("series", "Cyborg 009", ["Animation", "Action", "Sci-Fi"], "7.4", "2001–2002", "Nine people kidnapped from around the world and turned into superhuman cyborgs by the Black Ghost organization rebel against their creators to protect humanity."),
    "tt0280240": ("series", "The Big O", ["Animation", "Action", "Mystery"], "7.7", "1999–2003", "In Paradigm City—a domed metropolis that lost its memories forty years ago—professional Negotiator Roger Smith and android Dorothy pilot the giant mecha Megadeus Big O."),
    "tt0243694": ("series", "Digimon Adventure 02", ["Animation", "Action", "Adventure"], "7.2", "2000–2001", "Three years after the original DigiDestined saved the Digital World, Davis, Yolei, Cody, T.K., and Kari use Armor Digivolution and DNA Digivolution to stop the Digimon Emperor."),
    "tt0316975": ("series", "Digimon Frontier", ["Animation", "Action", "Adventure"], "6.9", "2002–2003", "Five children board a Trailmon to the Digital World and inherit the Legendary Spirits of the ten Ancient Warriors, allowing them to transform directly into Digimon."),
    "tt2746566": ("series", "Digimon Fusion", ["Animation", "Action", "Adventure"], "6.3", "2010–2012", "Mikey Kudo and his friends are pulled into the Digital World, leading the Fusion Fighters and using the Fusion Loader to combine Shoutmon and ally Digimon against the Bagra Army."),
    "tt6348126": ("series", "Beyblade Burst", ["Animation", "Action", "Sport"], "6.7", "2016–2023", "Energetic blader Valt Aoi and his Beyblade Victory Valtryek train with the Beigoma Academy BeyClub to take on rival Shu Kurenai and become the world's top blader."),
    "tt3696476": ("series", "Yu-Gi-Oh! Arc-V", ["Animation", "Action", "Fantasy"], "6.5", "2014–2017", "Aspiring entertainment duelist Yuya Sakaki unlocks Pendulum Summoning and is drawn into an interdimensional war across the Standard, Fusion, Synchro, and Xyz dimensions."),
    "tt5628740": ("series", "Yu-Gi-Oh! VRAINS", ["Animation", "Action", "Sci-Fi"], "6.7", "2017–2019", "Inside the virtual reality network LINK VRAINS, teenage hacker Yusaku Fujiki transforms into Playmaker and teams up with sentient AI Ignis to battle the Knights of Hanoi."),
    "tt1524993": ("series", "Dinosaur King", ["Animation", "Action", "Adventure"], "6.4", "2007–2008", "Max, Rex, and Zoe—the D-Team—travel the globe with their dinosaur partners Chomp, Ace, and Paris to rescue prehistoric dinosaurs from the time-traveling Alpha Gang."),
    "tt1696969": ("series", "Huntik: Secrets & Seekers", ["Animation", "Action", "Adventure"], "7.5", "2009–2012", "High school student Lok Lambert joins the Huntik Foundation alongside Dante Vale, Sophie Casterwill, and Zhalia Moon, summoning ancient Titans to stop the sinister Organization."),
    "tt2748608": ("series", "Max Steel (2013)", ["Animation", "Action", "Sci-Fi"], "6.9", "2013–2016", "Sixteen-year-old Maxwell McGrath discovers he can generate volatile TURBO energy and bonds with alien Ultra-Link Steel to become the armored superhero Max Steel."),
    "tt1037011": ("movie", "Ben 10: Race Against Time", ["Action", "Adventure", "Sci-Fi"], "5.1", "2007", "Returning home from summer vacation, Ben Tennyson must stop the interdimensional alien warlord Eon from unlocking the Hands of Armageddon and taking over the Omnitrix."),
    "tt1327701": ("movie", "Ben 10: Alien Swarm", ["Action", "Adventure", "Sci-Fi"], "5.1", "2009", "Teenage Ben Tennyson, Gwen, and Kevin Levin team up with Elena Validus to stop a hive mind of techno-organic alien microchips from taking over the planet."),
    "tt13186528": ("movie", "Ben 10 Versus the Universe: The Movie", ["Animation", "Action", "Sci-Fi"], "5.9", "2020", "When Vilgax returns to destroy Earth and Ben is accidentally launched into deep space, Ben must stand trial before the Intergalactic Court and unlock the Omni-Naut armor."),
    "tt0287635": ("movie", "Pokémon 4Ever: Celebi - Voice of the Forest", ["Animation", "Action", "Adventure"], "6.0", "2001", "Ash, Pikachu, Misty, and Brock meet Sammy, a boy transported forty years forward in time by the mythical Pokémon (Pokemon) Celebi, and must protect it from the Iron-Masked Marauder."),
    "tt0347791": ("movie", "Pokémon Heroes: Latios and Latias", ["Animation", "Action", "Adventure"], "6.2", "2002", "In the water-canal city of Alto Mare, Ash and Pikachu befriend the legendary dragon Pokémon (Pokemon) Latios and Latias and defend the Soul Dew from Team Rocket thieves Annie and Oakley."),
    "tt0420076": ("movie", "Pokémon: Jirachi - Wish Maker", ["Animation", "Action", "Adventure"], "5.9", "2003", "Awakening for only seven days every thousand years when the Millennium Comet appears, the Wish Pokémon (Pokemon) Jirachi bonds with Max and must be saved from a rogue magician."),
    "tt0435286": ("movie", "Pokémon: Destiny Deoxys", ["Animation", "Action", "Adventure"], "6.1", "2004", "In high-tech LaRousse City, an epic clash erupts between the extraterrestrial DNA Pokémon (Pokemon) Deoxys and the sky guardian Rayquaza, trapping Ash and his friends in the crossfire."),
    "tt0875609": ("movie", "Pokémon: Lucario and the Mystery of Mew", ["Animation", "Action", "Adventure"], "6.8", "2005", "When Pikachu is spirited away to the Tree of Beginning by Mew, Ash awakens Sir Aaron's Aura Pokémon (Pokemon) Lucario to journey into the ancient crystal cavern."),
    "tt1000095": ("movie", "Pokémon Ranger and the Temple of the Sea", ["Animation", "Action", "Adventure"], "6.0", "2006", "Ash, May, and Pokémon (Pokemon) Ranger Jack Walker protect the Prince of the Sea, Manaphy, and the ancient Sea Temple Samiya from the pirate Phantom."),
    "tt1226251": ("movie", "Pokémon: The Rise of Darkrai", ["Animation", "Action", "Adventure"], "6.5", "2007", "In Alamos Town, a dimensional battle between the legendary Pokémon (Pokemon) Dialga and Palkia threatens to tear reality apart while the misunderstood Darkrai stands guard."),
    "tt1160525": ("movie", "Pokémon: Giratina and the Sky Warrior", ["Animation", "Action", "Adventure"], "6.2", "2008", "Ash, Dawn, and Brock help the Gratitude Pokémon (Pokemon) Shaymin return to the Gracidea flower garden while defending the Reverse World and Giratina from Zero."),
    "tt1468843": ("movie", "Pokémon: Arceus and the Jewel of Life", ["Animation", "Action", "Adventure"], "6.3", "2009", "When the Alpha Pokémon (Pokemon) Arceus awakens to judge humanity for an ancient betrayal, Dialga sends Ash, Dawn, and Brock back in time to change history."),
    "tt1690470": ("movie", "Pokémon—Zoroark: Master of Illusions", ["Animation", "Action", "Adventure"], "6.1", "2010", "Ash and his friends rescue the illusion-casting Pokémon (Pokemon) Zorua and Zoroark in Crown City before media mogul Grings Kodai can steal Celebi's time-ripple energy."),
    "tt1961324": ("movie", "Pokémon the Movie: Black—Victini and Reshiram", ["Animation", "Action", "Adventure"], "5.8", "2011", "In Eindoak Town, Ash, Iris, and Cilan befriend the Victory Pokémon (Pokemon) Victini and call upon the legendary dragon Reshiram to save the Sword of the Vale."),
    "tt1739212": ("movie", "Pokémon the Movie: White—Victini and Zekrom", ["Animation", "Action", "Adventure"], "5.9", "2011", "Ash and his companions encounter the Mythical Pokémon (Pokemon) Victini and awaken the legendary dragon Zekrom to stop Damon's plan to move the Sword of the Vale."),
    "tt2549540": ("movie", "Pokémon the Movie: Kyurem vs. the Sword of Justice", ["Animation", "Action", "Adventure"], "5.6", "2012", "Ash and his friends help the Colt Pokémon (Pokemon) Keldeo rescue the Swords of Justice—Cobalion, Terrakion, and Virizion—from the fearsome dragon Kyurem."),
    "tt3257582": ("movie", "Pokémon the Movie: Genesect and the Legend Awakened", ["Animation", "Action", "Adventure"], "5.6", "2013", "When an army of five revived Paleozoic Pokémon (Pokemon) Genesect attacks New Tork City, Mega Mewtwo Y intervenes alongside Ash and Pikachu to stop the destruction."),
    "tt3918368": ("movie", "Pokémon the Movie: Diancie and the Cocoon of Destruction", ["Animation", "Action", "Adventure"], "5.6", "2014", "Ash, Serena, Clemont, and Bonnie accompany the Jewel Pokémon (Pokemon) Diancie in search of the Life Pokémon Xerneas before the Destruction Pokémon Yveltal awakens."),
    "tt4503906": ("movie", "Pokémon the Movie: Hoopa and the Clash of Ages", ["Animation", "Action", "Adventure"], "5.8", "2015", "In Dahara City, the Mythical Pokémon (Pokemon) Hoopa's Prison Bottle is broken, unleashing Hoopa Unbound and summoning legendary Pokémon from across space and time."),
    "tt5889204": ("movie", "Pokémon the Movie: Volcanion and the Mechanical Marvel", ["Animation", "Action", "Adventure"], "5.9", "2016", "Bound together by a magnetic chain, Ash and the Steam Pokémon (Pokemon) Volcanion storm the clockwork Azoth Kingdom to rescue the artificial Soul-Heart Pokémon Magearna."),
    "tt6595896": ("movie", "Pokémon the Movie: I Choose You!", ["Animation", "Action", "Adventure"], "6.3", "2017", "Retelling the beginning of Ash Ketchum and Pikachu's bond, the duo sets out from Pallet Town with a Rainbow Wing to meet the legendary Pokémon (Pokemon) Ho-Oh at Mount Tensei."),
    "tt8108230": ("movie", "Pokémon the Movie: The Power of Us", ["Animation", "Action", "Adventure"], "6.5", "2018", "During the annual Wind Festival in Fula City, Ash and Pikachu unite a diverse group of townspeople and the Mythical Pokémon (Pokemon) Zeraora to save the city and Lugia."),
    "tt8856470": ("movie", "Pokémon: Mewtwo Strikes Back - Evolution", ["Animation", "Action", "Adventure"], "5.7", "2019", "A CGI remake of the classic first Pokémon (Pokemon) movie in which the genetically engineered psychic Pokémon Mewtwo invites Ash, Misty, and Brock to New Island."),
    "tt11819890": ("movie", "Pokémon the Movie: Secrets of the Jungle", ["Animation", "Action", "Adventure"], "6.3", "2020", "Deep in the Forest of Okoya, Ash and Pikachu meet Koko, a human boy raised by the Mythical Pokémon (Pokemon) Zarude, and join forces to defend the jungle's healing spring."),
    "tt1587157": ("movie", "Yu-Gi-Oh! Bonds Beyond Time", ["Animation", "Action", "Fantasy"], "6.5", "2010", "Three generations of Duel Monsters heroes—Yugi Muto, Jaden Yuki, and Yusei Fudo—unite across time to defeat Paradox and his Malefic dragons."),
    "tt4273562": ("movie", "Yu-Gi-Oh!: The Dark Side of Dimensions", ["Animation", "Action", "Fantasy"], "7.1", "2016", "Set after the original manga, Seto Kaiba excavates the Millennium Puzzle to duel the Pharaoh one last time while a mysterious boy named Aigami wields the Quantum Cube."),
    "tt2263944": ("movie", "Dragon Ball Z: Battle of Gods", ["Animation", "Action", "Adventure"], "7.2", "2013", "Awakening from a 39-year slumber, Beerus the God of Destruction travels to Earth in search of the prophesied Super Saiyan God, pushing Goku to a new realm of divine power."),
    "tt3819668": ("movie", "Dragon Ball Z: Resurrection 'F'", ["Animation", "Action", "Adventure"], "7.2", "2015", "Resurrected by Earth's Dragon Balls, galactic tyrant Frieza trains for the first time in his life to unlock his Golden Frieza form and exact revenge on Goku and Vegeta."),
    "tt7961060": ("movie", "Dragon Ball Super: Broly", ["Animation", "Action", "Adventure"], "7.7", "2018", "Goku and Vegeta encounter Broly, an exiled Saiyan warrior with limitless latent battle power brought to Earth by Frieza, leading to an earth-shattering clash."),
    "tt14614892": ("movie", "Dragon Ball Super: Super Hero", ["Animation", "Action", "Adventure"], "7.1", "2022", "When the Red Ribbon Army resurfaces with powerful new androids Gamma 1, Gamma 2, and Cell Max, Piccolo and Gohan unlock new transformations to defend Earth."),
    "tt0414177": ("movie", "The Jimmy Timmy Power Hour", ["Animation", "Adventure", "Comedy"], "7.3", "2004", "When Timmy Turner wishes to be in the greatest lab in the universe, he swaps dimensions with boy genius Jimmy Neutron between Retroville and Dimmsdale."),
    "tt0473050": ("movie", "The Jimmy Timmy Power Hour 2: When Nerds Collide!", ["Animation", "Adventure", "Comedy"], "7.2", "2006", "Jimmy Neutron and Timmy Turner clash over Cindy Vortex while Professor Calamitous and Anti-Cosmo team up to free the anti-fairies."),
    "tt0499605": ("movie", "The Jimmy Timmy Power Hour 3: The Jerkinators!", ["Animation", "Adventure", "Comedy"], "6.8", "2006", "Jimmy Neutron and Timmy Turner accidentally create an unstoppable villain named Shirley who threatens to erase both Retroville and Dimmsdale."),
    "tt39055318": ("movie", "The Fairly OddParents: Abra-Catastrophe!", ["Animation", "Adventure", "Comedy"], "7.5", "2003", "Celebrating one full year with his fairy godparents Cosmo and Wanda, Timmy Turner receives a magical Rule-Free Muffin that falls into the hands of Mr. Crocker."),
    "tt0419739": ("movie", "The Fairly OddParents: Channel Chasers", ["Animation", "Adventure", "Comedy"], "8.0", "2004", "Armed with a magic TV remote, Timmy Turner jumps inside the television universe across parody cartoon channels while pursued by evil babysitter Vicky."),
    "tt10474606": ("movie", "We Bare Bears: The Movie", ["Animation", "Adventure", "Comedy"], "6.9", "2020", "When their love of food trucks and viral videos gets out of hand, Grizz, Panda, and Ice Bear embark on a wild road trip to Canada while pursued by Agent Trout."),
    "tt1599351": ("movie", "Scooby-Doo! Abracadabra-Doo", ["Animation", "Comedy", "Family"], "6.9", "2010", "Mystery Inc. visits Velma's younger sister Madelyn at the Whirlen Merlin Magic Academy, where a giant mythical Gryphon is terrorizing the castle grounds."),
    "tt1777608": ("movie", "Scooby-Doo! Legend of the Phantosaur", ["Animation", "Adventure", "Comedy"], "7.0", "2011", "During a relaxing spa trip in New Mexico, Shaggy is hypnotized into becoming fearless while Mystery Inc. investigates a glowing prehistoric Phantosaur."),
    "tt3025994": ("movie", "Scooby-Doo! Stage Fright", ["Animation", "Comedy", "Mystery"], "6.9", "2013", "Fred and Daphne compete as finalists on the television singing show Talent Star in Chicago while a masked Phantom haunts the historic opera house."),
    "tt3152592": ("movie", "Scoob!", ["Animation", "Adventure", "Comedy"], "5.6", "2020", "Scooby-Doo and the Mystery Inc. gang team up with the Blue Falcon to stop Dick Dastardly from unleashing the ghost dog Cerberus and opening the Underworld."),
    "tt0808508": ("movie", "Tom and Jerry: Shiver Me Whiskers", ["Animation", "Adventure", "Comedy"], "6.5", "2006", "Aboard the pirate ship of Captain Red, Tom and Jerry find a treasure map to the Spanish Main guarded by a giant octopus and a ghost pirate crew."),
    "tt1114698": ("movie", "Tom and Jerry: A Nutcracker Tale", ["Animation", "Comedy", "Family"], "7.1", "2007", "In an empty opera house on Christmas Eve, Jerry's wish brings a magical toy kingdom to life until Tom and a band of alley cats invade to Tchaikovsky's Nutcracker score."),
    "tt1722638": ("movie", "Tom and Jerry Meet Sherlock Holmes", ["Animation", "Comedy", "Family"], "6.5", "2010", "In Victorian London, Tom and Jerry assist legendary detective Sherlock Holmes and Dr. Watson in clearing singer Red's name after Professor Moriarty steals the crown jewels."),
    "tt1979376": ("movie", "Toy Story 4", ["Animation", "Adventure", "Comedy"], "7.7", "2019", "When Bonnie creates a reluctant new toy named Forky out of a spork, Woody, Buzz Lightyear, and the gang embark on a road trip where Woody reunites with Bo Peep."),
    "tt3606756": ("movie", "Incredibles 2", ["Animation", "Action", "Adventure"], "7.5", "2018", "Elastigirl is recruited to lead a campaign to bring Supers back into the spotlight while Mr. Incredible stays home to care for Violet, Dash, and baby Jack-Jack's emerging powers."),
    "tt1453405": ("movie", "Monsters University", ["Animation", "Adventure", "Comedy"], "7.2", "2013", "Before becoming top scarers at Monsters, Inc., college rivals Mike Wazowski and James P. Sullivan must team up with a fraternity of misfits to win the Scare Games."),
    "tt2277860": ("movie", "Finding Dory", ["Animation", "Adventure", "Comedy"], "7.2", "2016", "Friendly but forgetful blue tang fish Dory suddenly remembers her childhood family and sets off across the ocean with Marlin and Nemo to the Marine Life Institute in California."),
    "tt1216475": ("movie", "Cars 2", ["Animation", "Adventure", "Comedy"], "6.2", "2011", "Star race car Lightning McQueen and his tow-truck best friend Mater head overseas for the World Grand Prix, where Mater gets caught up in international espionage with Finn McMissile."),
    "tt3606752": ("movie", "Cars 3", ["Animation", "Adventure", "Comedy"], "6.7", "2017", "Blindsided by a new generation of blazing-fast high-tech rookies led by Jackson Storm, Lightning McQueen teams up with eager young race technician Cruz Ramirez to make a comeback."),
    "tt2096673": ("movie", "Inside Out", ["Animation", "Adventure", "Comedy"], "8.1", "2015", "After young Riley is uprooted from her Midwest life and moved to San Francisco, her emotions—Joy, Fear, Anger, Disgust, and Sadness—conflict on how best to navigate a new city."),
    "tt22022452": ("movie", "Inside Out 2", ["Animation", "Adventure", "Comedy"], "7.6", "2024", "As Riley enters puberty and heads to high school hockey camp, Headquarters undergoes a sudden demolition to make room for new emotions led by Anxiety, Envy, Ennui, and Embarrassment."),
    "tt0120623": ("movie", "A Bug's Life", ["Animation", "Adventure", "Comedy"], "7.2", "1998", "A misfit ant named Flik, looking for tough warriors to save his colony from greedy grasshoppers led by Hopper, inadvertently recruits a troupe of circus bugs."),
    "tt2380307": ("movie", "Coco", ["Animation", "Adventure", "Family"], "8.4", "2017", "Aspiring young musician Miguel, confronted with his family's ancestral ban on music, enters the vibrant Land of the Dead to unlock the real story behind his family history."),
    "tt0413267": ("movie", "Shrek the Third", ["Animation", "Adventure", "Comedy"], "6.1", "2007", "Reluctant to become the next King of Far Far Away, Shrek sets out with Donkey and Puss in Boots to bring Princess Fiona's rebellious cousin Artie to the throne while Prince Charming plots a coup."),
    "tt0892791": ("movie", "Shrek Forever After", ["Animation", "Adventure", "Comedy"], "6.3", "2010", "Longing for the days when he felt like a real ogre, Shrek signs a deceptive pact with Rumpelstiltskin and wakes up in an alternate Far Far Away where he and Fiona never met."),
    "tt0448694": ("movie", "Puss in Boots", ["Animation", "Adventure", "Comedy"], "6.6", "2011", "Long before meeting Shrek, the notorious outlaw Puss in Boots teams up with mastermind Humpty Dumpty and street-savvy Kitty Softpaws to steal the legendary Golden Goose."),
    "tt3915174": ("movie", "Puss in Boots: The Last Wish", ["Animation", "Action", "Adventure"], "7.8", "2022", "Discovering that his passion for adventure has burned through eight of his nine lives, Puss in Boots embarks on an epic quest into the Dark Forest to find the mythical Wishing Star."),
    "tt2267968": ("movie", "Kung Fu Panda 3", ["Animation", "Action", "Adventure"], "7.1", "2016", "Reunited with his long-lost biological father Li Shan, Po travels to a secret panda village and must train a clumsy community of pandas to defeat the supernatural warrior Kai."),
    "tt21692408": ("movie", "Kung Fu Panda 4", ["Animation", "Action", "Adventure"], "6.3", "2024", "Tapped to become the Spiritual Leader of the Valley of Peace, Po teams up with a quick-witted corsac fox thief named Zhen to stop a shape-shifting sorceress known as The Chameleon."),
    "tt1646971": ("movie", "How to Train Your Dragon 2", ["Animation", "Action", "Adventure"], "7.8", "2014", "Five years after uniting dragons and Vikings on Berk, Hiccup and Toothless discover a secret ice cave, Hiccup's long-lost mother Valka, and the dragon-conquering warlord Drago Bludvist."),
    "tt2386490": ("movie", "How to Train Your Dragon: The Hidden World", ["Animation", "Action", "Adventure"], "7.4", "2019", "When Toothless discovers an untamed, elusive Light Fury and the ruthless Night Fury hunter Grimmel threatens Berk, Hiccup and Toothless journey to the mythical Hidden World."),
    "tt0479952": ("movie", "Madagascar: Escape 2 Africa", ["Animation", "Adventure", "Comedy"], "6.6", "2008", "Attempting to fly back to New York aboard a patched-up plane, Alex, Marty, Melman, Gloria, and the Penguins crash-land on the plains of Africa, where Alex meets his real lion family."),
    "tt1277953": ("movie", "Madagascar 3: Europe's Most Wanted", ["Animation", "Adventure", "Comedy"], "6.8", "2012", "Hunted across Monte Carlo by relentless animal-control officer Captain Chantel DuBois, Alex, Marty, Melman, and Gloria hide out by joining a traveling European circus."),
    "tt1911658": ("movie", "Penguins of Madagascar", ["Animation", "Adventure", "Comedy"], "6.6", "2014", "Elite undercover flightless birds Skipper, Kowalski, Rico, and Private join forces with the North Wind spy agency to stop villainous octopus Dr. Octavius Brine from taking over the world."),
    "tt0481499": ("movie", "The Croods", ["Animation", "Adventure", "Comedy"], "7.1", "2013", "After their cave is destroyed, a prehistoric family led by overprotective patriarch Grug embarks on a journey through a fantastical new world with an inventive nomad named Guy."),
    "tt2850386": ("movie", "The Croods: A New Age", ["Animation", "Adventure", "Comedy"], "6.9", "2020", "Searching for a safer habitat, the prehistoric Crood family discovers a walled-in paradise created by the more evolved Betterman family."),
    "tt0120794": ("movie", "The Prince of Egypt", ["Animation", "Adventure", "Drama"], "7.2", "1998", "Raised as an Egyptian prince alongside his adoptive brother Rameses, Moses discovers his Hebrew heritage and is called upon to lead his people out of slavery."),
    "tt0138749": ("movie", "The Road to El Dorado", ["Animation", "Adventure", "Comedy"], "6.9", "2000", "Two sixteenth-century Spanish con men, Tulio and Miguel, win a map to the legendary City of Gold and are mistaken for gods by the inhabitants of El Dorado."),
    "tt0120630": ("movie", "Chicken Run", ["Animation", "Adventure", "Comedy"], "7.1", "2000", "When a cockerel named Rocky apparently flies into a Yorkshire chicken farm, the hens led by Ginger see him as their only hope to escape before Mrs. Tweedy turns them into chicken pies."),
    "tt0166813": ("movie", "Spirit: Stallion of the Cimarron", ["Animation", "Adventure", "Family"], "7.2", "2002", "A wild Kiger mustang stallion captured by the U.S. Cavalry forms an unbreakable bond with a young Lakota warrior named Little Creek while fighting to reclaim his freedom."),
    "tt0307453": ("movie", "Shark Tale", ["Animation", "Adventure", "Comedy"], "6.0", "2004", "When a fast-talking whale-wash fish named Oscar falsely takes credit for slaying the son of a shark mob boss, he teams up with vegetarian great white shark Lenny to keep up the ruse."),
    "tt0389790": ("movie", "Bee Movie", ["Animation", "Adventure", "Comedy"], "6.1", "2007", "Fresh out of college, disillusioned honeybee Barry B. Benson befriends New York florist Vanessa and sues the human race after discovering that people have been eating bees' honey."),
    "tt0892782": ("movie", "Monsters vs. Aliens", ["Animation", "Action", "Adventure"], "6.4", "2009", "Struck by a radioactive meteor on her wedding day and growing to 49 feet tall, Susan Murphy (Ginormica) is recruited into a secret government team of monsters to stop alien invader Gallaxhar."),
    "tt1446192": ("movie", "Rise of the Guardians", ["Animation", "Action", "Adventure"], "7.2", "2012", "When the evil spirit Pitch Black launches an assault on the hopes and dreams of children, the immortal Guardians—Santa Claus, the Easter Bunny, the Tooth Fairy, and Sandman—recruit Jack Frost."),
    "tt0268380": ("movie", "Ice Age", ["Animation", "Adventure", "Comedy"], "7.5", "2002", "During the onset of the Ice Age, a woolly mammoth named Manny, a talkative sloth named Sid, and a saber-toothed tiger named Diego form an unlikely herd to return a lost human baby."),
    "tt0438097": ("movie", "Ice Age: The Meltdown", ["Animation", "Adventure", "Comedy"], "6.8", "2006", "Manny, Sid, and Diego discover that the warming climate is about to flood their valley and set out toward higher ground along with Ellie, a female mammoth who thinks she's a possum."),
    "tt1080016": ("movie", "Ice Age: Dawn of the Dinosaurs", ["Animation", "Adventure", "Comedy"], "6.9", "2009", "When Sid adopts three Tyrannosaurus eggs and is carried into a lush subterranean dinosaur world, Manny, Ellie, and Diego team up with one-eyed weasel Buck to rescue him."),
    "tt1667889": ("movie", "Ice Age: Continental Drift", ["Animation", "Adventure", "Comedy"], "6.5", "2012", "After Scrat's pursuit of his acorn triggers a continental cataclysm, Manny, Diego, and Sid are set adrift on an iceberg and clash with Captain Gutt's crew of seafaring pirates."),
    "tt3416828": ("movie", "Ice Age: Collision Course", ["Animation", "Adventure", "Comedy"], "5.7", "2016", "When Scrat accidentally launches a UFO into outer space and sends a giant asteroid hurtling toward Earth, Buck leads Manny, Sid, and Diego on a mission to stop the impact."),
    "tt1323594": ("movie", "Despicable Me", ["Animation", "Adventure", "Comedy"], "7.6", "2010", "When a criminal mastermind named Gru uses a trio of orphan girls—Margo, Edith, and Agnes—as pawns for a grand scheme to steal the Moon, he finds their love profoundly changing him."),
    "tt1690953": ("movie", "Despicable Me 2", ["Animation", "Adventure", "Comedy"], "7.3", "2013", "Now a devoted father to Margo, Edith, and Agnes, former supervillain Gru is recruited by the Anti-Villain League and partnered with Agent Lucy Wilde to stop El Macho."),
    "tt3469046": ("movie", "Despicable Me 3", ["Animation", "Adventure", "Comedy"], "6.2", "2017", "Gru meets his long-lost charming, cheerful, and more successful twin brother Dru, who wants to team up with him for one last criminal heist against former child star Balthazar Bratt."),
    "tt7510222": ("movie", "Despicable Me 4", ["Animation", "Adventure", "Comedy"], "6.2", "2024", "Gru, Lucy, Margo, Edith, Agnes, and baby Gru Jr. relocate to the safe-house town of Mayflower while evading escaped French supervillain Maxime Le Mal."),
    "tt2293640": ("movie", "Minions", ["Animation", "Adventure", "Comedy"], "6.4", "2015", "Evolving from single-celled yellow organisms at the dawn of time, Minions Kevin, Stuart, and Bob travel to 1968 London and are recruited by supervillain Scarlet Overkill."),
    "tt5113044": ("movie", "Minions: The Rise of Gru", ["Animation", "Adventure", "Comedy"], "6.5", "2022", "In the 1970s, twelve-year-old Gru schemes to join the supervillain group the Vicious 6 and relies on Kevin, Stuart, Bob, and Otto to rescue him when the heist goes wrong."),
    "tt0837562": ("movie", "Hotel Transylvania", ["Animation", "Comedy", "Family"], "7.0", "2012", "Count Dracula operates a lavish five-stake resort where monsters can relax away from the human world—until a carefree human backpacker stumbles in and falls for Dracula's daughter Mavis."),
    "tt2510894": ("movie", "Hotel Transylvania 2", ["Animation", "Comedy", "Family"], "6.6", "2015", "Now open to human guests, Hotel Transylvania sees Dracula secretly put his half-human, half-vampire grandson Dennis through a 'monster-in-training' boot camp with his monster pals."),
    "tt5220122": ("movie", "Hotel Transylvania 3: Summer Vacation", ["Animation", "Adventure", "Comedy"], "6.3", "2018", "Count Dracula and his monster family embark on a luxury monster cruise ship vacation, unaware that the ship's captain Ericka is the descendant of Abraham Van Helsing."),
    "tt9848626": ("movie", "Hotel Transylvania: Transformania", ["Animation", "Adventure", "Comedy"], "6.0", "2022", "When Van Helsing's mysterious Monsterfication Ray goes haywire, Johnny is turned into a dragon monster while Dracula and his pals are transformed into ordinary humans."),
    "tt0844471": ("movie", "Cloudy with a Chance of Meatballs", ["Animation", "Adventure", "Comedy"], "6.9", "2009", "Eccentric young inventor Flint Lockwood builds a machine that turns water in the atmosphere into raining cheeseburgers and pancakes over the island town of Swallow Falls."),
    "tt1985966": ("movie", "Cloudy with a Chance of Meatballs 2", ["Animation", "Adventure", "Comedy"], "6.3", "2013", "Flint Lockwood and his friends return to Swallow Falls after discovering that his FLDSMDFR machine is still running and creating an ecosystem of living foodimals."),
    "tt1436562": ("movie", "Rio", ["Animation", "Adventure", "Comedy"], "6.9", "2011", "Domesticated Spix's macaw Blu, who never learned to fly in Minnesota, is taken to Rio de Janeiro to meet the fiercely independent Jewel and escape animal smugglers."),
    "tt2357291": ("movie", "Rio 2", ["Animation", "Adventure", "Comedy"], "6.3", "2014", "Blu, Jewel, and their three kids leave their domesticated life in Rio de Janeiro for an expedition deep into the Amazon rainforest, where Jewel reunites with her long-lost flock."),
    "tt0400717": ("movie", "Open Season", ["Animation", "Adventure", "Comedy"], "6.1", "2006", "Pampered 900-pound grizzly bear Boog and fast-talking one-antlered mule deer Elliot find themselves stranded in the woods three days before hunting season opens."),
    "tt1107365": ("movie", "Open Season 2", ["Animation", "Adventure", "Comedy"], "5.5", "2008", "When Mr. Weenie is kidnapped by a group of pampered domestic pets led by Fifi the poodle, Boog, Elliot, McSquizzy, and the forest animals go undercover to rescue him."),
    "tt1646926": ("movie", "Open Season 3", ["Animation", "Adventure", "Comedy"], "5.1", "2010", "Boog swaps places with a look-alike circus grizzly bear named Doug and falls for Russian trapeze bear Ursa, prompting Elliot and the woodland crew to stage a rescue."),
    "tt0423294": ("movie", "Surf's Up", ["Animation", "Comedy", "Family"], "6.7", "2007", "A behind-the-scenes mockumentary following teenage rockhopper penguin Cody Maverick as he leaves Shiverpool, Antarctica to enter the Big Z Memorial Surf Off on Pen Gu Island."),
    "tt0358082": ("movie", "Robots", ["Animation", "Adventure", "Comedy"], "6.4", "2005", "In a world of sentient robots, idealistic young inventor Rodney Copperbottom travels to Robot City to meet his idol Bigweld and teams up with the Rusties to stop corporate tyrant Ratchet."),
    "tt0451079": ("movie", "Horton Hears a Who!", ["Animation", "Adventure", "Comedy"], "6.8", "2008", "Horton the Elephant hears a faint cry for help coming from a microscopic speck of dust floating through the air and vows to protect the tiny community of Whoville inside it."),
    "tt2452042": ("movie", "The Peanuts Movie", ["Animation", "Adventure", "Comedy"], "7.0", "2015", "Charlie Brown embarks on a quest to impress the Little Red-Haired Girl while his beagle Snoopy takes to the skies to pursue his arch-nemesis, the Red Baron."),
    "tt0120131": ("movie", "The Lion King II: Simba's Pride", ["Animation", "Adventure", "Family"], "6.5", "1998", "Simba and Nala's adventurous daughter Kiara falls in love with Kovu, a young lion from the banished Outsider pride raised to avenge Scar, sparking a struggle to unite the Pride Lands."),
    "tt0318403": ("movie", "The Lion King 1½", ["Animation", "Adventure", "Comedy"], "6.5", "2004", "Timon the meerkat and Pumbaa the warthog fast-forward and rewind through the events of The Lion King to reveal their own hilarious behind-the-scenes story."),
    "tt0107952": ("movie", "The Return of Jafar", ["Animation", "Adventure", "Family"], "5.9", "1994", "Escaping from his lamp in the Cave of Wonders as an all-powerful genie, Jafar returns to Agrabah to exact revenge on Aladdin, Jasmine, Genie, and a reformed Iago."),
    "tt0115491": ("movie", "Aladdin and the King of Thieves", ["Animation", "Adventure", "Family"], "6.4", "1996", "When the Forty Thieves crash Aladdin and Princess Jasmine's wedding in search of the Oracle, Aladdin discovers that the King of Thieves is his long-lost father Cassim."),
    "tt0401398": ("movie", "Kronk's New Groove", ["Animation", "Comedy", "Family"], "5.8", "2005", "Now the head chef and delivery boy at Mudka's Meat Hut, former henchman Kronk scrambles to acquire a house on the hill before his hard-to-please father Papi visits."),
    "tt0344864": ("movie", "Atlantis: Milo's Return", ["Animation", "Action", "Adventure"], "5.1", "2003", "Milo Thatch and Queen Kida reunite with their surface expedition crew to investigate ancient Atlantean monsters and artifacts awakening across the globe."),
    "tt0279967": ("movie", "Mulan II", ["Animation", "Adventure", "Comedy"], "5.7", "2004", "Newly engaged Mulan and General Li Shang escort three Chinese princesses to a diplomatic marriage alliance while Mushu schemes to keep Mulan from losing him as her guardian."),
    "tt0437503": ("movie", "Tarzan II", ["Animation", "Adventure", "Family"], "5.6", "2005", "Before becoming King of the Jungle, young Tarzan runs away from his gorilla troop after feeling like an outcast and meets the legendary hermit ape Zugor on Dark Mountain."),
    "tt0313680": ("movie", "Tarzan & Jane", ["Animation", "Adventure", "Comedy"], "5.3", "2002", "Celebrating their first anniversary in the African jungle, Jane reminisces with Terk and Tantor about three wild adventures from her first year living with Tarzan."),
    "tt5848272": ("movie", "Ralph Breaks the Internet", ["Animation", "Adventure", "Comedy"], "7.0", "2018", "Six years after saving the arcade, Wreck-It Ralph and Vanellope von Schweetz venture into the uncharted expanse of the Internet via a newly installed Wi-Fi router to find a replacement Sugar Rush wheel."),
    "tt2294629": ("movie", "Frozen", ["Animation", "Adventure", "Comedy"], "7.4", "2013", "When the newly crowned Queen Elsa accidentally uses her power to turn things into ice to curse her home in infinite winter, her sister Anna teams up with Kristoff, Sven, and Olaf."),
    "tt4520988": ("movie", "Frozen II", ["Animation", "Adventure", "Comedy"], "6.8", "2019", "Anna, Elsa, Kristoff, Olaf, and Sven leave Arendelle to travel to an ancient, autumn-bound enchanted forest to find the origin of Elsa's magical powers and save their kingdom."),
    "tt0328880": ("movie", "Brother Bear", ["Animation", "Adventure", "Family"], "6.9", "2003", "When an impulsive young Inuit hunter named Kenai avenges his brother by killing a bear, the Spirits magically transform him into a bear and pair him with a talkative cub named Koda."),
    "tt0465925": ("movie", "Brother Bear 2", ["Animation", "Adventure", "Family"], "6.1", "2006", "Kenai and Koda help Kenai's childhood friend Nita journey to Hokani Falls to burn an amulet and break a childhood bond before her wedding."),
    "tt0097757": ("movie", "The Little Mermaid", ["Animation", "Adventure", "Family"], "7.6", "1989", "Mermaid princess Ariel makes a Faustian bargain with the sea witch Ursula, trading her voice for human legs in hopes of winning the heart of Prince Eric on land."),
    "tt0240684": ("movie", "The Little Mermaid II: Return to the Sea", ["Animation", "Adventure", "Family"], "5.5", "2000", "Ariel and Eric's daughter Melody, kept away from the ocean to protect her from Ursula's vengeful sister Morgana, longs to swim in the sea and is transformed into a mermaid."),
    "tt0061852": ("movie", "The Jungle Book", ["Animation", "Adventure", "Family"], "7.6", "1967", "Bagheera the Panther and Baloo the Bear have a difficult time trying to convince a boy named Mowgli to leave the Indian jungle before the evil tiger Shere Khan arrives."),
    "tt0283426": ("movie", "The Jungle Book 2", ["Animation", "Adventure", "Family"], "5.4", "2003", "Now living in the Man-Village, Mowgli misses his carefree jungle life with Baloo and sneaks back into the wild, unaware that Shere Khan is waiting for revenge."),
    "tt0046183": ("movie", "Peter Pan", ["Animation", "Adventure", "Family"], "7.3", "1953", "Wendy and her two brothers are whisked away to the magical world of Neverland with the hero of their stories, Peter Pan, and Tinker Bell to face Captain Hook."),
    "tt0280030": ("movie", "Return to Never Land", ["Animation", "Adventure", "Family"], "5.8", "2002", "In World War II London, Wendy's pragmatic daughter Jane refuses to believe in Peter Pan—until Captain Hook mistakes her for Wendy and kidnaps her to Neverland."),
    "tt0055254": ("movie", "One Hundred and One Dalmatians", ["Animation", "Adventure", "Comedy"], "7.3", "1961", "When a litter of Dalmatian puppies are abducted by the minions of Cruella de Vil, the parents Pongo and Perdita must find them before she uses them for a fur coat."),
    "tt0324941": ("movie", "101 Dalmatians II: Patch's London Adventure", ["Animation", "Adventure", "Comedy"], "5.8", "2003", "Accidentally left behind when the Radcliffe family moves to the countryside, puppy Patch teams up with his TV hero Thunderbolt in London to rescue his siblings from Cruella de Vil."),
    "tt0100477": ("movie", "The Rescuers Down Under", ["Animation", "Adventure", "Family"], "6.8", "1990", "Rescue Aid Society mice Bernard and Miss Bianca fly to the Australian Outback aboard Wilbur the albatross to save a young boy named Cody and a giant golden eagle from poacher McLeach."),
    "tt0082406": ("movie", "The Fox and the Hound", ["Animation", "Adventure", "Drama"], "7.2", "1981", "An orphaned red fox named Tod and a hound puppy named Copper form a deep childhood friendship that is tested when they grow up into natural enemies."),
    "tt0034492": ("movie", "Bambi", ["Animation", "Adventure", "Drama"], "7.3", "1942", "The story of a young deer growing up in the forest alongside his friends Thumper the rabbit and Flower the skunk after his mother is shot by hunters."),
    "tt0447854": ("movie", "Bambi II", ["Animation", "Drama", "Family"], "6.1", "2006", "After the loss of his mother, young Bambi is raised through the winter by his stoic father, the Great Prince of the Forest, as both learn from one another."),
    "tt0042332": ("movie", "Cinderella", ["Animation", "Family", "Fantasy"], "7.3", "1950", "When Cinderella's cruel stepmother prevents her from attending the Royal Ball, she gets some unexpected help from the lovable mice Gus and Jaq and from her Fairy Godmother."),
    "tt0101414": ("movie", "Beauty and the Beast", ["Animation", "Family", "Fantasy"], "8.0", "1991", "A prince cursed to spend his days as a hideous monster sets out to regain his humanity by earning a young woman's love before the last petal falls from an enchanted rose."),
    "tt0107688": ("movie", "The Nightmare Before Christmas", ["Animation", "Family", "Fantasy"], "7.9", "1993", "Jack Skellington, king of Halloween Town, stumbles through a portal to Christmas Town and becomes so enchanted that he decides to kidnap Santa Claus and take over the holiday."),
    "tt0076363": ("movie", "The Many Adventures of Winnie the Pooh", ["Animation", "Comedy", "Family"], "7.5", "1977", "A collection of three classic animated shorts following honey-loving bear Winnie the Pooh, Christopher Robin, Piglet, Tigger, and Eeyore through the Hundred Acre Wood."),
    "tt1449283": ("movie", "Winnie the Pooh", ["Animation", "Adventure", "Comedy"], "7.1", "2011", "While searching for a replacement tail for Eeyore, Winnie the Pooh and his friends misread a note from Christopher Robin and set out to rescue him from the imaginary 'Backson'."),
    "tt0396555": ("movie", "Meet the Robinsons", ["Animation", "Adventure", "Comedy"], "6.8", "2007", "Orphaned twelve-year-old boy inventor Lewis is whisked away to the year 2037 by Wilbur Robinson to stop the Bowler Hat Guy from altering the future."),
    "tt0397892": ("movie", "Bolt", ["Animation", "Adventure", "Comedy"], "6.8", "2008", "The canine star of a fictional sci-fi action show who believes his superpowers are real embarks on a cross-country trek from New York to Hollywood with alley cat Mittens and hamster Rhino."),
    "tt0398286": ("movie", "Tangled", ["Animation", "Adventure", "Comedy"], "7.7", "2010", "The magically long-haired Rapunzel has spent her entire life in a hidden tower, but now that a runaway thief named Flynn Rider has stumbled upon her, she is about to discover the world."),
    "tt2948356": ("movie", "Zootopia", ["Animation", "Adventure", "Comedy"], "8.0", "2016", "In a city of anthropomorphic animals, rookie bunny cop Judy Hopps and cynical con-artist fox Nick Wilde must work together to uncover a conspiracy involving missing predators."),
    "tt3521164": ("movie", "Moana", ["Animation", "Adventure", "Comedy"], "7.6", "2016", "In Ancient Polynesia, when a terrible curse incurred by the Demigod Maui reaches Moana's island, she answers the Ocean's call to seek out Maui to set things right."),
    "tt2953050": ("movie", "Encanto", ["Animation", "Comedy", "Family"], "7.2", "2021", "A Colombian teenage girl has to face the frustration of being the only member of her family without magical powers—until she discovers that the magic surrounding the Encanto is in danger."),
    "tt1490017": ("movie", "The Lego Movie", ["Animation", "Action", "Adventure"], "7.7", "2014", "An ordinary LEGO construction worker named Emmet Brickowski, thought to be the prophesied 'Special', is recruited to join a quest to stop the evil tyrant Lord Business."),
    "tt3513498": ("movie", "The Lego Movie 2: The Second Part", ["Animation", "Action", "Adventure"], "6.6", "2019", "It's been five years since everything was awesome and the citizens are facing a huge new threat: LEGO DUPLO invaders from outer space, wrecking everything faster than they can rebuild."),
    "tt4116284": ("movie", "The Lego Batman Movie", ["Animation", "Action", "Comedy"], "7.3", "2017", "A cooler-than-ever Bruce Wayne must deal with the usual suspects as they plan to rule Gotham City, while discovering that he has accidentally adopted a teenage orphan who wishes to become Robin."),
    "tt3139086": ("movie", "Batman: Assault on Arkham", ["Animation", "Action", "Crime"], "7.4", "2014", "Batman works desperately to find a bomb planted by the Joker while Amanda Waller sends her newly formed Suicide Squad to break into Arkham Asylum to recover vital information."),
    "tt3060952": ("movie", "Justice League: War", ["Animation", "Action", "Sci-Fi"], "7.2", "2014", "The world's finest superheroes—Batman, Superman, Wonder Woman, Green Lantern, The Flash, Shazam, and Cyborg—meet for the first time to stop an alien invasion led by Darkseid."),
    "tt2494376": ("movie", "Justice League Dark", ["Animation", "Action", "Fantasy"], "7.1", "2017", "When innocent civilians begin committing unthinkable crimes across Metropolis and Gotham, Batman recruits John Constantine, Zatanna, Deadman, and Etrigan the Demon."),
    "tt11079148": ("movie", "Justice League Dark: Apokolips War", ["Animation", "Action", "Sci-Fi"], "7.8", "2020", "After a devastating invasion by Darkseid decimates Earth and the Justice League, the surviving heroes rally around Superman, John Constantine, Raven, and Damian Wayne for a final stand."),
    "tt7167658": ("movie", "The Death of Superman", ["Animation", "Action", "Sci-Fi"], "7.3", "2018", "When a hulking monster named Doomsday arrives on Earth and begins a mindless rampage across Metropolis, the Justice League falls and only Superman can stand in its way."),
    "tt7167686": ("movie", "Reign of the Supermen", ["Animation", "Action", "Sci-Fi"], "6.8", "2019", "After the death of Superman, four new superpowered figures—Superboy, Steel, the Eradicator, and Cyborg Superman—emerge in Metropolis claiming the mantle of the Man of Steel.")
}


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
        f.write('\n')


def fetch_cinemeta_meta(stremio_type, imdb_id, default_title=""):
    url = f"https://v3-cinemeta.strem.io/meta/{stremio_type}/{imdb_id}.json"
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (CartoonVaultBuilder)'})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=4.0, context=ctx) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                meta = data.get('meta')
                if meta and meta.get('name'):
                    return meta
        except urllib.error.URLError:
            try:
                unverified_ctx = ssl._create_unverified_context()
                with urllib.request.urlopen(req, timeout=4.0, context=unverified_ctx) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    meta = data.get('meta')
                    if meta and meta.get('name'):
                        return meta
            except Exception:
                break
        except Exception:
            break
        time.sleep(0.1)
    return None


def make_fallback_meta(cat_type, imdb_id, default_title):
    if imdb_id in FALLBACK_METADATA:
        _, fb_name, fb_genres, fb_rating, fb_release, fb_desc = FALLBACK_METADATA[imdb_id]
        return {
            "id": imdb_id,
            "type": cat_type,
            "name": fb_name or default_title,
            "poster": f"https://images.metahub.space/poster/small/{imdb_id}/img",
            "posterShape": "poster",
            "genres": fb_genres,
            "imdbRating": fb_rating,
            "releaseInfo": fb_release,
            "description": fb_desc,
            "background": f"https://images.metahub.space/background/medium/{imdb_id}/img",
            "logo": f"https://images.metahub.space/logo/medium/{imdb_id}/img"
        }
    return {
        "id": imdb_id,
        "type": cat_type,
        "name": default_title,
        "poster": f"https://images.metahub.space/poster/medium/{imdb_id}/img",
        "posterShape": "poster",
        "genres": ["Animation"],
        "imdbRating": "",
        "releaseInfo": "",
        "description": f"Iconic animated adventures of {default_title} following classic characters and unforgettable stories."
    }


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

    valid_ids = {imdb_id for items in SHOW_DEFINITIONS.values() for imdb_id, _ in items}
    if cache:
        cache = {k: v for k, v in cache.items() if k in valid_ids}

    # Ensure curated fallback metadata overrides missing/generic entries and keeps disambiguated titles
    for imdb_id in valid_ids:
        if imdb_id in FALLBACK_METADATA:
            fb_type, fb_name, fb_genres, fb_rating, fb_release, fb_desc = FALLBACK_METADATA[imdb_id]
            if imdb_id not in cache or not cache[imdb_id].get("description") or cache[imdb_id].get("description", "").endswith("on demand."):
                cache[imdb_id] = make_fallback_meta(fb_type, imdb_id, fb_name)
            elif imdb_id in ("tt0168366", "tt1666278", "tt0088631", "tt0188359"):
                cache[imdb_id]["name"] = fb_name
                cache[imdb_id]["description"] = fb_desc

    total_titles = 0

    for cat in CATALOG_DEFINITIONS:
        cat_id = cat["id"]
        cat_type = cat["type"]
        items = SHOW_DEFINITIONS.get(cat_id, [])
        print(f"Building Cartoon Vault catalog: {cat['name']} ({len(items)} items)...")

        cat_metas = []
        for imdb_id, default_title in items:
            cached_meta = cache.get(imdb_id)
            meta = None

            desc = cached_meta.get("description", "") if cached_meta else ""
            needs_fetch = refresh or not cached_meta or not desc or desc.endswith("on demand.")

            if not needs_fetch:
                meta = cached_meta
            else:
                raw_meta = fetch_cinemeta_meta(cat_type, imdb_id, default_title)
                if raw_meta:
                    genres = raw_meta.get('genres')
                    if not genres and raw_meta.get('genre'):
                        g = raw_meta.get('genre')
                        genres = [x.strip() for x in g.split(',')] if isinstance(g, str) else [g]

                    desc_val = raw_meta.get('description', '')
                    if not desc_val and imdb_id in FALLBACK_METADATA:
                        desc_val = FALLBACK_METADATA[imdb_id][5]
                    elif not desc_val:
                        desc_val = f"Iconic animated adventures of {default_title} following classic characters and unforgettable stories."

                    meta = {
                        "id": imdb_id,
                        "type": cat_type,
                        "name": raw_meta.get('name') or default_title,
                        "poster": raw_meta.get('poster') or f"https://images.metahub.space/poster/medium/{imdb_id}/img",
                        "posterShape": "poster",
                        "genres": genres or ["Animation"],
                        "imdbRating": str(raw_meta.get('imdbRating', '')),
                        "releaseInfo": str(raw_meta.get('releaseInfo') or raw_meta.get('year') or ''),
                        "description": desc_val
                    }
                    if raw_meta.get('background'):
                        meta["background"] = raw_meta.get('background')
                    if raw_meta.get('logo'):
                        meta["logo"] = raw_meta.get('logo')

                    cache[imdb_id] = meta
                elif cached_meta:
                    meta = cached_meta
                else:
                    meta = make_fallback_meta(cat_type, imdb_id, default_title)
                    cache[imdb_id] = meta

            cat_metas.append(meta)
            total_titles += 1

        catalog_response = {"metas": cat_metas}

        # Route 1: catalog/{type}/{id}.json
        route1_path = os.path.join(vault_dir, "catalog", cat_type, f"{cat_id}.json")
        write_json(route1_path, catalog_response)

        # Route 2: catalog/{type}/{id}/skip=0.json
        route2_path = os.path.join(vault_dir, "catalog", cat_type, cat_id, "skip=0.json")
        write_json(route2_path, catalog_response)

        # Route 3+: empty pagination termination files
        for skip_val in (100, 200, 300):
            skip_path = os.path.join(vault_dir, "catalog", cat_type, cat_id, f"skip={skip_val}.json")
            write_json(skip_path, {"metas": []})

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
