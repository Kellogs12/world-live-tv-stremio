# World Live TV for Stremio

Self-hosted, static multi-country Live TV channel add-ons for [Stremio](https://stremio.com). Completely free, runs 100% on GitHub Pages with automated weekly updates via GitHub Actions.

---

## 🌍 Included Add-ons & Lineups

- 🏆 **Live Sports 24/7 (`/sports/`)**: Priority live sports across 5 dedicated catalogs:
  - **Formula 1 & Motorsports**: ORF 1 (official FTA Formula 1 live broadcaster), TV Formula, SPEEDVISION (24/7 premier motorsport network), NASCAR Channel (official 24/7 stock car racing), Motorvision (international motorsport & rally), RACER Select (MAVTV motorsports), Red Bull TV (motorsports & F1 specials), BBC Top Gear.
  - **AFL & Australian Sports**: 7AFL (official 7plus AFL FAST stream), Channel 7 Melbourne (live AFL match coverage), Channel 7mate Melbourne (live AFL), LIV Golf Replays, Trace Sport Stars, Racing.com (Channel 78 live racing), Sky Racing 1, 2, Thoroughbred Central.
  - **UFC, Boxing & Combat Sports**: UFC official FAST channel, HBO Boxing (classic championship fights), PFL MMA (Professional Fighters League), GLORY Kickboxing, TVS Boxing, Swerve Combat.
  - **NFL, NBA & MLB Major Leagues**: The NBA Channel, MLB Channel (Major League Baseball 1080p), FOX Sports (live NFL analysis & FS1 studio shows), NBC Sports NOW (ProFootballTalk & NFL coverage), CBS Sports HQ (24/7 live scores and game highlights), Fubo Sports Network, WNBL Basketball.
  - **Soccer, Golf & International Sports**: FIFA+ (official FIFA live matches & tournament coverage), CBS Sports Golazo Network (24/7 dedicated live soccer network), beIN SPORTS XTRA (international soccer, Ligue 1, Copa Libertadores), beIN SPORTS XTRA en Español, PGA TOUR, TennisChannel 2, Cricket Gold.
- 🎨 **Cartoons & Kids TV (`/cartoons/`)**: 24/7 famous cartoons, animation, and kids networks across 3 catalogs:
  - **Cartoon Network & Disney Channel**: Cartoon Network HD & SD (Dexter's Lab, Ben 10, Adventure Time, Powerpuff Girls, Courage the Cowardly Dog, Gumball), Disney Channel (Phineas and Ferb, Gravity Falls, DuckTales, Kim Possible), 9Go! (24/7 kids animation block for Cartoon Network classics and anime).
  - **Nickelodeon & NickToons (24/7)**: SpongeBob SquarePants 24/7, Nickelodeon Live, NickToons (Avatar, Fairly OddParents, Danny Phantom, Invader Zim), NickToons 90s (Rugrats, Hey Arnold!, Rocko's Modern Life, CatDog), Nick Jr Club (PAW Patrol, Blue's Clues), NickTeen (iCarly, Victorious, Big Time Rush).
  - **Classic Cartoons & Action Animation**: Cartoon Classics (Popeye, Betty Boop, Classic Looney Tunes), Transformers TV (24/7 animated series), Power Rangers (24/7 action series), Kartoon Channel!, Toon Goggles, ABC Kids (Bluey, Play School), Adult Animation, Xumo Free Kids TV.
- 🇦🇺 **Australia (`/au/`)**: ABC, SBS, Seven, Nine, 10, C31, 7AFL, and Samsung TV Plus AU.
- 🇺🇸 **United States (`/us/`)**: CBS News, ABC News Live, NBC News Now, Scripps News, Fox Weather, Bloomberg, Reuters, and Xumo Free Live TV US.
- 🇬🇧 **United Kingdom (`/uk/`)**: BBC News, Sky News, GB News, and Rakuten TV UK.
- 🇳🇿 **New Zealand (`/nz/`)**: TVNZ 1, TVNZ 2, TVNZ Duke, Three, Bravo, Rush, and Whakaata Māori.
- 🇨🇦 **Canada (`/ca/`)**: Reuters 60, BBC News, CBS News 24/7, and Sky News.
- 🌐 **Global News & Sports (`/global/`)**: Sky News International, BBC News, Al Jazeera, DW, France 24, Euronews, The NBA Channel, UFC, HBO Boxing, FIFA+, beIN SPORTS XTRA, MLB Channel, 7AFL.

---

## 🚀 How to Deploy Your Own

### 1. Create a New GitHub Repository
1. Go to [github.com/new](https://github.com/new).
2. Name your repository (e.g. `world-live-tv-stremio`).
3. Set visibility to **Public** (required for free GitHub Pages).
4. Do **not** initialize with README or license.

### 2. Push this Project
In your terminal, navigate to this directory and push:
```bash
git init
git add .
git commit -m "Initial commit of World Live TV Stremio Addon"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/world-live-tv-stremio.git
git push -u origin main
```

### 3. Enable GitHub Pages
1. Go to your repository **Settings** &rarr; **Pages**.
2. Under **Build and deployment**:
   - Source: **Deploy from a branch**
   - Branch: **`main`** / Folder: **`/ (root)`**
3. Click **Save**.
4. In about 60 seconds, your site is live at:
   `https://<YOUR_USERNAME>.github.io/world-live-tv-stremio/`

---

## ⚙️ Automated GitHub Actions Workflow

This project includes `.github/workflows/update.yml`:
- **Weekly Auto-Update:** Runs every Monday at 02:00 UTC to re-download fresh M3U channel playlists and update stream tokens.
- **Manual Trigger:** Go to **Actions** &rarr; **Update Live TV Channels** &rarr; click **Run workflow** to update immediately.
- **GitHub Pages Sync:** Any updated channel lists are automatically committed and deployed to your live GitHub Pages site.

---

## ➕ Adding More Countries

To add another country:
1. Open `sources.json`.
2. Add a new country object with its `code`, `name`, `flag`, and stream playlists / channels.
3. Run `python3 generate.py` (or push to GitHub to let GitHub Actions do it!).

---

## 📺 Stremio Features

- **Dual Streams:** Every channel includes **Live** (for Stremio Android, Desktop, TV) and **Live (browser)** with `proxyHeaders` for **Stremio Web**.
- **AIOStreams Support:** Can be added as a Custom addon in AIOStreams.
- **Modular Addons:** Users install only the countries they watch, avoiding catalog clutter.
