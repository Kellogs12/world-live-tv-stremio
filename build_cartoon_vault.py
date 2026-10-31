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
    "Cartoon Network, Disney, Nickelodeon, Classic Cartoons, and Action Animation."
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
        ("tt7713450", "Craig of the Creek"),
        ("tt0482870", "Robotboy"),  # Note: corrected from tt0487823
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
        ("tt1666278", "ThunderCats (2011)"),
        ("tt0361243", "Star Wars: Clone Wars (2003)"),
        ("tt0286347", "Braceface"),
        ("tt0471989", "Being Ian"),
        ("tt0946601", "Ruby Gloom"),
        ("tt0831823", "Di-Gata Defenders"),
        ("tt0305011", "Clone High"),
        ("tt4847134", "Mighty Magiswords"),
        ("tt6965802", "OK K.O.! Let's Be Heroes")
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
        ("tt0101188", "Rugrats"),
        ("tt0115200", "Hey Arnold!"),
        ("tt0106115", "Rocko's Modern Life"),
        ("tt0235923", "Invader Zim"),
        ("tt0320808", "The Adventures of Jimmy Neutron"),
        ("tt1877889", "Teenage Mutant Ninja Turtles (2012)"),
        ("tt4859164", "The Loud House"),
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
        ("tt3559124", "The Tom and Jerry Show"),
        ("tt0130417", "The New Tom & Jerry Show"),
        ("tt0198254", "Tom & Jerry Kids Show"),
        ("tt0053502", "The Flintstones"),
        ("tt0055683", "The Jetsons"),
        ("tt0063950", "Scooby-Doo, Where Are You!"),
        ("tt0306274", "What's New, Scooby-Doo?"),
        ("tt1660055", "Scooby-Doo! Mystery Incorporated"),
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
        ("tt0053488", "The Bugs Bunny Show"),
        ("tt0060019", "The Road Runner Show"),
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
        ("tt0224455", "Angela Anaconda"),
        ("tt0229132", "Grizzly Tales for Gruesome Kids"),
        ("tt0094531", "A Pup Named Scooby-Doo"),
        ("tt0088628", "The 13 Ghosts of Scooby-Doo"),
        ("tt21153032", "The Scooby-Doo Show"),
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
        ("tt0184175", "The Woody Woodpecker Show"),
        ("tt0100366", "Pingu"),
        ("tt0262151", "Bob the Builder"),
        ("tt0086815", "Thomas & Friends"),
        ("tt0329829", "Fireman Sam"),
        ("tt0445882", "The Koala Brothers"),
        ("tt0449545", "Curious George"),
        ("tt0364793", "The Berenstain Bears"),
        ("tt0243061", "Dragon Tales"),
        ("tt1783822", "Babar and the Adventures of Badou")
    ],
    "action-shows": [
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
        ("tt0168366", "Pokémon"),
        ("tt0121220", "Dragon Ball Z"),
        ("tt0088509", "Dragon Ball"),
        ("tt4644488", "Dragon Ball Super"),
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
        ("tt0493334", "Yu-Gi-Oh! GX"),
        ("tt0328733", "Beyblade (2001)"),
        ("tt0293731", "Medabots"),
        ("tt0367409", "Shaman King"),
        ("tt0367413", "Sonic X"),
        ("tt0106140", "Sonic the Hedgehog (SatAM)"),
        ("tt0126173", "Swat Kats: The Radical Squadron"),
        ("tt0103559", "Street Sharks"),
        ("tt0147752", "Biker Mice from Mars"),
        ("tt0249327", "Yu-Gi-Oh! Duel Monsters"),
        ("tt1196094", "Yu-Gi-Oh! 5D's"),
        ("tt2363624", "Yu-Gi-Oh! Zexal"),
        ("tt0210418", "Digimon Adventure"),
        ("tt0295080", "Digimon Tamers"),
        ("tt1138300", "Digimon Data Squad"),
        ("tt1674928", "Beyblade: Metal Fusion"),
        ("tt0139774", "Dragon Ball GT"),
        ("tt1409055", "Dragon Ball Z Kai"),
        ("tt0409591", "Naruto"),
        ("tt0988824", "Naruto: Shippuden"),
        ("tt0388629", "One Piece"),
        ("tt0434665", "Bleach"),
        ("tt0290223", "InuYasha"),
        ("tt1355642", "Fullmetal Alchemist: Brotherhood"),
        ("tt0877057", "Death Note"),
        ("tt2098220", "Hunter x Hunter"),
        ("tt2560140", "Attack on Titan"),
        ("tt1214085", "Soul Eater"),
        ("tt0213338", "Cowboy Bebop"),
        ("tt0423731", "Samurai Champloo"),
        ("tt0114327", "Sailor Moon"),
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
        ("tt0126158", "He-Man and the Masters of the Universe"),
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
        ("tt0092106", "The Transformers: The Movie (1986)"),
        ("tt0253658", "Scooby-Doo and the Alien Invaders"),
        ("tt0290057", "Scooby-Doo and the Cyber Chase"),
        ("tt0357139", "Scooby-Doo and the Legend of the Vampire"),
        ("tt0369903", "Scooby-Doo and the Monster of Mexico"),
        ("tt0867418", "Scooby-Doo! Pirates Ahoy!"),
        ("tt1731767", "Scooby-Doo! Camp Scare"),
        ("tt0303151", "Tom and Jerry: The Magic Ring"),
        ("tt0433696", "Tom and Jerry: Blast Off to Mars!"),
        ("tt0487176", "Tom and Jerry: The Fast and the Furry"),
        ("tt1000070", "Billy & Mandy's Big Boogey Adventure"),
        ("tt0837113", "Codename: Kids Next Door - Operation Z.E.R.O."),
        ("tt4920274", "Regular Show: The Movie"),
        ("tt0389074", "Kim Possible: A Sitch in Time"),
        ("tt0446724", "Kim Possible Movie: So the Drama"),
        ("tt0348124", "Stitch! The Movie"),
        ("tt0457993", "Lilo & Stitch 2: Stitch Has a Glitch"),
        ("tt0486761", "Leroy & Stitch"),
        ("tt0314166", "Hey Arnold! The Movie"),
        ("tt0282120", "The Wild Thornberrys Movie"),
        ("tt0337711", "Rugrats Go Wild"),
        ("tt0190641", "Pokémon: The First Movie - Mewtwo Strikes Back"),
        ("tt0210234", "Pokémon the Movie 2000"),
        ("tt0235679", "Pokémon 3: The Movie"),
        ("tt0259974", "Digimon: The Movie"),
        ("tt0403703", "Yu-Gi-Oh!: The Movie - Pyramid of Light"),
        ("tt0472219", "The Batman vs. Dracula"),
        ("tt1398941", "Superman/Batman: Public Enemies"),
        ("tt1494772", "Justice League: Crisis on Two Earths"),
        ("tt0491703", "Ultimate Avengers: The Movie"),
        ("tt1483025", "Planet Hulk"),
        ("tt0453556", "TMNT (2007)"),
        ("tt1543920", "Turtles Forever"),
        ("tt0133240", "Treasure Planet"),
        ("tt0230011", "Atlantis: The Lost Empire"),
        ("tt0120917", "The Emperor's New Groove"),
        ("tt0275847", "Lilo & Stitch"),
        ("tt0120855", "Tarzan"),
        ("tt0119282", "Hercules"),
        ("tt0120762", "Mulan"),
        ("tt0317705", "The Incredibles"),
        ("tt0198781", "Monsters, Inc."),
        ("tt0266543", "Finding Nemo"),
        ("tt0317219", "Cars"),
        ("tt0382932", "Ratatouille"),
        ("tt0910970", "WALL·E"),
        ("tt1049413", "Up"),
        ("tt0114709", "Toy Story"),
        ("tt0120363", "Toy Story 2"),
        ("tt0435761", "Toy Story 3"),
        ("tt0126029", "Shrek"),
        ("tt0298148", "Shrek 2"),
        ("tt0441773", "Kung Fu Panda"),
        ("tt1302011", "Kung Fu Panda 2"),
        ("tt0892769", "How to Train Your Dragon"),
        ("tt1001526", "Megamind"),
        ("tt0351283", "Madagascar"),
        ("tt0327084", "Over the Hedge"),
        ("tt0424095", "Flushed Away"),
        ("tt0312004", "Wallace & Gromit: The Curse of the Were-Rabbit"),
        ("tt0385880", "Monster House"),
        ("tt0327597", "Coraline"),
        ("tt0462538", "The Simpsons Movie"),
        ("tt0472033", "9"),
        ("tt1192628", "Rango"),
        ("tt0983193", "The Adventures of Tintin (2011)"),
        ("tt1772341", "Wreck-It Ralph"),
        ("tt2245084", "Big Hero 6")
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

    valid_ids = {imdb_id for items in SHOW_DEFINITIONS.values() for imdb_id, _ in items}
    if cache:
        cache = {k: v for k, v in cache.items() if k in valid_ids}

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

            # If cache has incomplete info (e.g. empty description or fallback dummy description), re-fetch
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

        # Route 3: catalog/{type}/{id}/skip=100.json (empty page to stop infinite pagination cleanly)
        route3_path = os.path.join(vault_dir, "catalog", cat_type, cat_id, "skip=100.json")
        write_json(route3_path, {"metas": []})

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
