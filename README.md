# World Live TV for Stremio

Self-hosted, static multi-country Live TV channel add-ons for [Stremio](https://stremio.com). Completely free, runs 100% on GitHub Pages with automated weekly updates via GitHub Actions.

---

## 🌍 Included Countries & Lineups

- 🇦🇺 **Australia (`/au/`)**: ABC, SBS, Seven, Nine, 10, C31, Samsung TV Plus AU, Plex AU.
- 🇬🇧 **United Kingdom (`/uk/`)**: BBC One, BBC Two, BBC News, ITV1, Channel 4, Channel 5, Sky News, GB News, Pluto TV UK.
- 🇺🇸 **United States (`/us/`)**: CBS News, ABC News Live, NBC News Now, Scripps News, LiveNOW from FOX, WeatherNation, Bloomberg, PBS, Pluto TV US, Samsung US.
- 🇳🇿 **New Zealand (`/nz/`)**: TVNZ 1, TVNZ 2, TVNZ Duke, Three, Bravo, Rush, Whakaata Māori.
- 🇨🇦 **Canada (`/ca/`)**: CBC News, CBC Toronto, Global News, CPAC, Pluto CA, Samsung CA.
- 🇮🇪 **Ireland (`/ie/`)**: RTÉ News Now, TG4, Free-to-Air.
- 🌐 **Global News & Sports (`/global/`)**: Sky News International, BBC News, Al Jazeera English, DW English, France 24, Euronews, NHK World, Red Bull TV, NASA TV.

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
