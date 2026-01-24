# 🚀 MusicElo Quick Start

Get up and running in 5 minutes!

## Step 1: Setup Environment (2 minutes)

```bash
# Clone or download project
cd musicelo

# Create conda environment
conda create -n musicelo python=3.11
conda activate musicelo

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Spotify API (2 minutes)

1. Go to https://developer.spotify.com/dashboard
2. Create new app (any name)
3. Copy Client ID and Client Secret
4. Configure:

```bash
cp .env.example .env
# Edit .env and add your credentials
```

## Step 3: Run! (1 minute)

```bash
# Initialize with sample data
python scripts/05_init_database.py

# Launch app
streamlit run streamlit_app/app.py
```

Opens at: http://localhost:8501

## Next Steps

- Read [docs/SETUP.md](docs/SETUP.md) for full instructions
- Read [docs/USER_GUIDE.md](docs/USER_GUIDE.md) to learn how to use effectively
- Start ranking your music!

## Troubleshooting

**"No module named X"**: `pip install -r requirements.txt`  
**"Spotify credentials"**: Check .env file has correct keys  
**Database error**: Delete data/musicelo.db and rerun step 3

See [docs/SETUP.md](docs/SETUP.md) for detailed help.
