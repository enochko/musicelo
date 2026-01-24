# 🎵 MusicElo

**Advanced music ranking system using Glicko-2 ratings with mood-based recommendations**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=Streamlit&logoColor=white)](https://streamlit.io)

MusicElo is a personal music ranking application that helps you discover your true preferences through pairwise comparisons. Instead of arbitrary 5-star ratings, it uses the sophisticated Glicko-2 algorithm (an advanced variant of the Elo system used in chess) to calculate accurate, confidence-weighted ratings for your music library.

---

## ✨ Features

### Core Functionality
- **🎯 Pairwise Comparison System**: Compare songs head-to-head with support for wins, losses, and draws
- **📊 Glicko-2 Rating Algorithm**: Advanced rating system with uncertainty quantification
- **🎧 Dual Ranking Modes**:
  - **Focused Duel Mode**: Intensive side-by-side comparisons for initial ranking
  - **Playlist Mode**: Passive ranking while listening to music naturally
- **🎨 Smart UI/UX**: 
  - Hide ratings during comparison to avoid bias
  - Show audio features to help recall songs
  - Instant feedback on rating changes

### Intelligence & Recommendations
- **🎵 Mood-Based Playlists**: Generate playlists by mood, energy, or emotional state
- **🔄 Transition Playlists**: Gradual mood shifts (e.g., Sad → Happy)
- **🤖 ML Recommendations** *(Phase 2)*: Predict ratings for unranked songs
- **📈 Rich Analytics**: Visualize preferences, trends, and listening patterns

### Data & Integration
- **🎼 Spotify Integration**: Automatic metadata enrichment (valence, energy, danceability, etc.)
- **▶️ YouTube Music Player**: Embedded playback with automatic URL matching
- **📚 Playlist Import**: Bootstrap ratings from your existing favorites
- **💾 Complete Export**: CSV export for backup and analysis

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- [Conda](https://docs.conda.io/en/latest/miniconda.html) or [Miniforge](https://github.com/conda-forge/miniforge) installed
- Spotify Developer Account (free) - [Sign up here](https://developer.spotify.com/dashboard)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/musicelo.git
cd musicelo

# 2. Create conda environment
conda create -n musicelo python=3.11
conda activate musicelo

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env with your Spotify credentials (see docs/SETUP.md)

# 5. Initialize the database
python scripts/05_init_database.py

# 6. Launch the app
streamlit run streamlit_app/app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📖 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) folder:

- **[SETUP.md](docs/SETUP.md)** - Complete setup guide (Conda, Spotify API, GitHub)
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design decisions
- **[DATA_COLLECTION.md](docs/DATA_COLLECTION.md)** - Data pipeline and bootstrapping process
- **[GLICKO2_GUIDE.md](docs/GLICKO2_GUIDE.md)** - Understanding the Glicko-2 rating system
- **[USER_GUIDE.md](docs/USER_GUIDE.md)** - How to use MusicElo effectively
- **[API_REFERENCE.md](docs/API_REFERENCE.md)** - Code API documentation
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Deploy to Streamlit Cloud

---

## 🎮 Usage

### Initial Ranking (Week 1)

1. **Import your music library**:
   ```bash
   python scripts/01_fetch_spotify_discography.py  # Fetch from Spotify
   python scripts/03_import_user_playlists.py      # Import your playlists
   python scripts/04_merge_and_initialize.py       # Merge data
   ```

2. **Start comparing**: Open the app and use **Duel Mode** to do ~50-100 initial comparisons

3. **Review rankings**: Check the Rankings page to see your emerging preferences

### Ongoing Use (Week 2+)

1. **Passive ranking**: Use **Playlist Mode** while working/studying
2. **Refine over time**: Your rankings improve with each comparison
3. **Generate playlists**: Create mood-based playlists from your top-rated songs
4. **Analyze preferences**: Explore your music taste patterns

---

## 🏗️ Project Structure

```
musicelo/
├── core/                      # Core business logic (framework-agnostic)
│   ├── database/              # SQLAlchemy models and operations
│   │   ├── models.py          # Database schema
│   │   └── operations.py      # CRUD operations
│   ├── services/              # Business logic services
│   │   ├── glicko2_service.py # Rating calculations
│   │   ├── spotify_service.py # Spotify API integration
│   │   └── recommendation_service.py
│   └── utils/                 # Helper functions
│
├── streamlit_app/             # Streamlit UI (swappable frontend)
│   ├── app.py                 # Main app entry point
│   └── pages/                 # Multi-page app
│       ├── 0_📋_Review_Data.py
│       ├── 1_⚔️_Duel_Mode.py
│       ├── 2_🎧_Playlist_Mode.py
│       ├── 3_📊_Rankings.py
│       └── 4_📈_Analytics.py
│
├── scripts/                   # Data pipeline & utilities
│   ├── 01_fetch_spotify_discography.py
│   ├── 02_fetch_youtube_urls.py
│   ├── 03_import_user_playlists.py
│   ├── 04_merge_and_initialize.py
│   └── 05_init_database.py
│
├── tests/                     # Unit tests
├── data/                      # Data files (not committed)
├── docs/                      # Documentation
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── config.py                  # Configuration loader
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🧠 Why Glicko-2?

**Standard Elo limitations**:
- Treats all ratings as equally certain
- Doesn't account for rating volatility
- Poor handling of infrequent comparisons

**Glicko-2 improvements**:
- **Rating Deviation (RD)**: Quantifies uncertainty in ratings
  - New song: RD = 350 (very uncertain)
  - 100+ comparisons: RD = 50 (very confident)
- **Volatility (σ)**: Tracks consistency vs. erratic performance
- **Time decay**: Ratings become less certain when not compared recently
- **Better for sparse data**: Perfect for personal music libraries

See [GLICKO2_GUIDE.md](docs/GLICKO2_GUIDE.md) for details.

---

## 🎯 Roadmap

### Phase 1: MVP ✅ (Weeks 1-2)
- [x] Glicko-2 rating system
- [x] SQLite database with metadata
- [x] Duel comparison mode
- [x] YouTube Music player integration
- [x] Basic rankings view
- [x] Draw support

### Phase 2: Enhanced UX (Weeks 3-4)
- [x] Playlist ranking mode
- [ ] Smart pairing algorithms
- [ ] Keyboard shortcuts
- [ ] Filter rankings by mood/category
- [ ] Session statistics

### Phase 3: Intelligence (Weeks 5-8)
- [ ] Mood-based playlist generation
- [ ] Transition playlists
- [ ] Playlist feedback system
- [ ] Advanced visualizations

### Phase 4: Machine Learning (Weeks 9-12)
- [ ] Preference prediction model
- [ ] Song clustering
- [ ] Anomaly detection
- [ ] Insight generation

### Phase 5: Polish (Ongoing)
- [ ] Mobile-responsive design
- [ ] Spotify Web Playback SDK
- [ ] Multi-artist support
- [ ] Export to streaming services

---

## 🤝 Contributing

This is a personal project, but feedback and suggestions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Glicko-2 System**: Developed by Professor Mark Glickman
- **Spotify Web API**: For comprehensive music metadata
- **Streamlit**: For rapid Python web app development
- **ytmusicapi**: For YouTube Music integration

---

## 📬 Contact

**Project Link**: [https://github.com/YOUR_USERNAME/musicelo](https://github.com/YOUR_USERNAME/musicelo)

**Website**: [musicelo.com](https://musicelo.com)

---

## 🎵 Built for TWICE fans, useful for any music lover

Initially developed to rank the complete TWICE discography (~250+ songs), but the system works for any artist or personal music library. The framework-agnostic architecture makes it easy to extend and customize.

**Enjoy ranking your music!** 🎧✨
