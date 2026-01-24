# 🛠️ MusicElo Setup Guide

Complete step-by-step instructions to get MusicElo running on your machine.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Spotify API Configuration](#spotify-api-configuration)
4. [Environment Setup](#environment-setup)
5. [Data Collection](#data-collection)
6. [GitHub Setup](#github-setup)
7. [Running the Application](#running-the-application)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

1. **Python 3.11+**
   - Check version: `python --version` or `python3 --version`
   - Download: [python.org](https://www.python.org/downloads/)

2. **Conda or Miniforge** (Recommended)
   - **macOS** (you have this!): Miniforge already installed
   - **Windows**: [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
   - **Linux**: [Miniforge](https://github.com/conda-forge/miniforge)

3. **Git**
   - macOS: Pre-installed or `brew install git`
   - Windows: [Git for Windows](https://git-scm.com/download/win)
   - Linux: `sudo apt install git`

4. **Text Editor**
   - VSCode (recommended): [code.visualstudio.com](https://code.visualstudio.com/)
   - Or any editor you prefer

### Required Accounts

1. **Spotify Developer Account** (Free)
   - Sign up: [developer.spotify.com](https://developer.spotify.com/dashboard)
   - No premium subscription needed

2. **GitHub Account** (Free)
   - Sign up: [github.com](https://github.com)

3. **Optional: Streamlit Account** (Free - for deployment)
   - Sign up: [share.streamlit.io](https://share.streamlit.io)

---

## Initial Setup

### 1. Create Project Directory

```bash
# Navigate to where you want the project
cd ~/Documents  # Or your preferred location

# Clone repository (after creating on GitHub)
git clone https://github.com/YOUR_USERNAME/musicelo.git
cd musicelo

# OR: Download the provided files and navigate to the folder
cd musicelo
```

### 2. Verify File Structure

```bash
# Check that you have these folders
ls -la

# You should see:
# .gitignore
# .env.example
# README.md
# requirements.txt
# config.py
# core/
# streamlit_app/
# scripts/
# docs/
# data/
```

---

## Spotify API Configuration

### Step 1: Create Spotify App

1. **Go to Spotify Dashboard**
   - Visit: [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
   - Log in with your Spotify account

2. **Create New App**
   - Click **"Create app"**
   - Fill in:
     - **App name**: `MusicElo` (or any name)
     - **App description**: `Personal music ranking system`
     - **Redirect URI**: `http://localhost:8501` (required but not used)
     - **APIs used**: Check "Web API"
   - Agree to terms and click **"Save"**

3. **Get Credentials**
   - Click on your new app
   - Click **"Settings"**
   - You'll see:
     - **Client ID**: `abc123...` (looks like random letters/numbers)
     - **Client Secret**: Click "View client secret"
   - **IMPORTANT**: Keep these secret! Never share or commit to Git

### Step 2: Save Credentials Securely

```bash
# In the musicelo folder:
cp .env.example .env

# Open .env in your text editor
# Replace the placeholder values:
SPOTIFY_CLIENT_ID=your_actual_client_id_here
SPOTIFY_CLIENT_SECRET=your_actual_client_secret_here

# Save and close
```

**Security Check**: 
```bash
# Verify .env is in .gitignore
cat .gitignore | grep .env

# You should see:
# .env
# *.env
```

✅ **Your API keys are now secure and will NOT be committed to Git!**

---

## Environment Setup

### Option 1: Using Conda (Recommended)

```bash
# 1. Create new environment
conda create -n musicelo python=3.11

# 2. Activate environment
conda activate musicelo

# You should see (musicelo) in your terminal prompt

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify installation
python -c "import streamlit; import pandas; import spotipy; print('✅ All packages installed!')"
```

### Option 2: Using venv (Alternative)

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate environment
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Daily Workflow

```bash
# When starting work:
conda activate musicelo  # Or: source venv/bin/activate

# When done:
conda deactivate  # Or: deactivate
```

---

## Data Collection

### Quick Start: Use Sample Data

For testing, you can skip data collection and use the provided sample:

```bash
# Copy sample data
cp data/sample_discography.csv data/twice_complete_discography.csv

# Initialize database
python scripts/05_init_database.py

# Start app
streamlit run streamlit_app/app.py
```

### Full Setup: Collect Your Own Data

#### Step 1: Fetch Spotify Discography

```bash
# Make sure environment is activated
conda activate musicelo

# Run Spotify fetcher
python scripts/01_fetch_spotify_discography.py

# Expected output:
# ============================================================
# TWICE Spotify Discography Fetcher
# ============================================================
# Found artist: TWICE (ID: ...)
# Found 50 albums/singles
# [1/50] Processing: The Story Begins (album)
# ...
# ✅ Saved 250 unique tracks to: data/spotify_discography_raw.csv
```

**Troubleshooting**:
- `SpotifyException: No token provided`: Check your `.env` file has correct credentials
- `ModuleNotFoundError: No module named 'spotipy'`: Run `pip install -r requirements.txt`

#### Step 2: Match YouTube Music URLs

```bash
python scripts/02_fetch_youtube_urls.py

# This takes 5-10 minutes
# Expected output:
# [250/250] FANCY
# ✅ Matched: 245/250 tracks
# ❌ Failed: 5 tracks
# ⚠️ Saved failed matches to: data/youtube_music_failed.csv
```

**Note**: Some tracks may fail to match automatically. You can:
- Manually add URLs later in the Review Data page
- Skip for now (you can still rank songs without playback)

#### Step 3: Import Your Playlists (Optional)

This bootstraps Elo ratings based on your existing favorites.

**First time only**: Set up YouTube Music authentication

```bash
# Generate authentication headers
ytmusicapi browser

# Follow the instructions:
# 1. Open YouTube Music in your browser
# 2. Open Developer Tools (F12)
# 3. Go to Network tab
# 4. Refresh page
# 5. Find any request to music.youtube.com
# 6. Copy request headers
# 7. Paste into terminal when prompted

# Save output to:
# data/ytm_headers_auth.json
```

**Then run**:

```bash
python scripts/03_import_user_playlists.py

# Expected output:
# Found 15 playlists:
# 1. TWICE Favourites (48 songs)
# 2. TWICE To-Listen (23 songs)
# ...
# ✅ Playlist data exported!
```

#### Step 4: Merge Everything

```bash
python scripts/04_merge_and_initialize.py

# Expected output:
# ============================================================
# Data Merger & Initializer
# ============================================================
# ✅ Spotify: 250 tracks
# ✅ YouTube Music: 245 URLs
# ❤️ Liked songs: 15
# 👀 Familiar songs: 33
# 📚 To-listen: 23
#
# 📊 Initial Elo distribution:
# elo_source
# user_liked        15  1600.0
# user_familiar     33  1550.0
# to_listen         23  1525.0
# title_track       42  1525.0
# unknown          137  1500.0
#
# ✅ Merged dataset saved: data/twice_complete_discography.csv
```

#### Step 5: Review Data (Optional but Recommended)

```bash
# Launch review interface
streamlit run streamlit_app/pages/0_📋_Review_Data.py

# Opens in browser: http://localhost:8501
# Review:
# - Missing YouTube URLs
# - Duplicate songs
# - Incorrect metadata
```

#### Step 6: Initialize Database

```bash
python scripts/05_init_database.py

# Expected output:
# ============================================================
# Database Initialization
# ============================================================
# Creating database: data/musicelo.db
# Loading data from: data/twice_complete_discography.csv
# ✅ Created songs table
# ✅ Created comparisons table
# ✅ Created playlists table
# ✅ Created parameters table
# ✅ Inserted 250 songs
# ✅ Database initialized successfully!
```

---

## GitHub Setup

### Create Repository

1. **Create on GitHub**:
   - Go to [github.com/new](https://github.com/new)
   - Repository name: `musicelo`
   - Description: `Personal music ranking system using Glicko-2 ratings`
   - Visibility: Public (for portfolio) or Private
   - **Do NOT initialize** with README (you already have one)
   - Click "Create repository"

2. **Link Local Repository**:

```bash
# In the musicelo folder:

# Initialize git (if not already)
git init

# Verify .gitignore is working
git status

# You should NOT see:
# - .env file
# - *.db files
# - data/*.csv files

# If you see these, fix .gitignore and run: git status

# Add all files
git add .

# First commit
git commit -m "Initial commit: MusicElo project setup"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/musicelo.git

# Push to GitHub
git push -u origin main
```

### Verify Security

```bash
# Check what's on GitHub
git ls-files

# Verify these are NOT listed:
# - .env
# - data/musicelo.db
# - data/*.csv (your actual data files)

# If they appear, you have a problem!
# See: docs/TROUBLESHOOTING.md#leaked-secrets
```

### Daily Git Workflow

```bash
# After making changes:
git status                    # See what changed
git add .                     # Stage changes
git commit -m "Add feature X" # Commit with message
git push                      # Push to GitHub
```

---

## Running the Application

### Start the App

```bash
# Activate environment
conda activate musicelo

# Launch Streamlit
streamlit run streamlit_app/app.py

# Opens automatically in browser: http://localhost:8501
```

### Navigation

The app has multiple pages:

1. **📋 Review Data** - Check imported songs
2. **⚔️ Duel Mode** - Focused pairwise comparisons
3. **🎧 Playlist Mode** - Passive ranking while listening
4. **📊 Rankings** - View current ratings
5. **📈 Analytics** - Explore preferences

### Stopping the App

- Press `Ctrl+C` in terminal
- Or just close the terminal window

---

## Troubleshooting

### Common Issues

#### "Module not found" errors

```bash
# Make sure environment is activated
conda activate musicelo

# Reinstall dependencies
pip install -r requirements.txt
```

#### "No Spotify credentials" error

```bash
# Check .env file exists
ls -la .env

# Verify it has your credentials
cat .env | grep SPOTIFY_CLIENT_ID

# Make sure no extra spaces or quotes
# ✅ CORRECT:
# SPOTIFY_CLIENT_ID=abc123def456

# ❌ WRONG:
# SPOTIFY_CLIENT_ID = "abc123def456"
# SPOTIFY_CLIENT_ID='abc123def456'
```

#### Database errors

```bash
# Delete and recreate database
rm data/musicelo.db
python scripts/05_init_database.py
```

#### Streamlit won't start

```bash
# Check if port is in use
lsof -ti:8501

# Kill process if needed
kill -9 $(lsof -ti:8501)

# Try different port
streamlit run streamlit_app/app.py --server.port 8502
```

### Getting Help

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review error messages carefully
3. Search GitHub issues
4. Open a new issue with:
   - Error message
   - Steps to reproduce
   - Your setup (OS, Python version)

---

## Next Steps

Once setup is complete:

1. **Read [USER_GUIDE.md](USER_GUIDE.md)** - Learn how to use MusicElo effectively
2. **Start ranking** - Do 50-100 comparisons in Duel Mode
3. **Review rankings** - Check if they match your intuition
4. **Try Playlist Mode** - Passive ranking while listening
5. **Explore Analytics** - Discover your music preferences

---

## Configuration Reference

### Environment Variables

All settings in `.env`:

```bash
# Required
SPOTIFY_CLIENT_ID=<your_id>
SPOTIFY_CLIENT_SECRET=<your_secret>

# Optional (defaults shown)
DATABASE_URL=sqlite:///data/musicelo.db
GLICKO2_TAU=0.5
GLICKO2_DEFAULT_RATING=1500.0
GLICKO2_DEFAULT_RD=350.0
GLICKO2_DEFAULT_VOLATILITY=0.06
```

### Glicko-2 Parameters

Adjust in `.env` if you want different behavior:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `GLICKO2_TAU` | 0.5 | Volatility constraint (0.3-1.2). Lower = more stable |
| `GLICKO2_DEFAULT_RATING` | 1500.0 | Starting rating |
| `GLICKO2_DEFAULT_RD` | 350.0 | Starting uncertainty |
| `GLICKO2_DEFAULT_VOLATILITY` | 0.06 | Starting volatility |

---

## Security Checklist

Before pushing to GitHub:

- [ ] `.env` is in `.gitignore`
- [ ] `.env` is NOT in `git status`
- [ ] `data/*.db` is in `.gitignore`
- [ ] `data/*.csv` is in `.gitignore`
- [ ] No API keys in code files
- [ ] `config.py` loads from environment
- [ ] `.env.example` has placeholders only

Run: `git diff --cached | grep -i "api_key\|secret\|password"`
Expected: Nothing

---

**Setup complete!** 🎉

You're now ready to start ranking your music. See [USER_GUIDE.md](USER_GUIDE.md) for usage instructions.
