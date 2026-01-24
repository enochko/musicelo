"""
MusicElo Configuration Module

Loads configuration from environment variables (.env file)
Provides centralized access to all settings
Validates required configuration on startup
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """
    Application configuration
    
    All settings loaded from environment variables
    Never hardcode secrets in code!
    """
    
    # =========================================================================
    # SPOTIFY API
    # =========================================================================
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    # =========================================================================
    # DATABASE
    # =========================================================================
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/musicelo.db')
    
    # =========================================================================
    # APPLICATION
    # =========================================================================
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # =========================================================================
    # GLICKO-2 PARAMETERS
    # =========================================================================
    GLICKO2_TAU = float(os.getenv('GLICKO2_TAU', '0.5'))
    GLICKO2_DEFAULT_RATING = float(os.getenv('GLICKO2_DEFAULT_RATING', '1500.0'))
    GLICKO2_DEFAULT_RD = float(os.getenv('GLICKO2_DEFAULT_RD', '350.0'))
    GLICKO2_DEFAULT_VOLATILITY = float(os.getenv('GLICKO2_DEFAULT_VOLATILITY', '0.06'))
    
    # Rating deviation increase per day of inactivity
    GLICKO2_RD_INCREASE_PER_DAY = float(os.getenv('GLICKO2_RD_INCREASE_PER_DAY', '0.5'))
    
    # =========================================================================
    # STREAMLIT
    # =========================================================================
    STREAMLIT_SERVER_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', '8501'))
    STREAMLIT_SERVER_ADDRESS = os.getenv('STREAMLIT_SERVER_ADDRESS', 'localhost')
    
    # =========================================================================
    # YOUTUBE MUSIC (Optional)
    # =========================================================================
    YTM_HEADERS_PATH = os.getenv('YTM_HEADERS_PATH', 'data/ytm_headers_auth.json')
    
    # =========================================================================
    # PATHS
    # =========================================================================
    # Project root directory
    PROJECT_ROOT = Path(__file__).parent
    
    # Data directory
    DATA_DIR = PROJECT_ROOT / 'data'
    
    # Ensure data directory exists
    DATA_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def validate(cls):
        """
        Validate that required configuration is present
        
        Raises:
            ValueError: If required configuration is missing
        """
        required = [
            ('SPOTIFY_CLIENT_ID', cls.SPOTIFY_CLIENT_ID),
            ('SPOTIFY_CLIENT_SECRET', cls.SPOTIFY_CLIENT_SECRET),
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file and ensure all required variables are set.\n"
                f"See .env.example for template."
            )
    
    @classmethod
    def get_database_path(cls) -> Path:
        """
        Get the database file path
        
        Returns:
            Path to database file
        """
        if cls.DATABASE_URL.startswith('sqlite:///'):
            # Extract path from SQLite URL
            db_path = cls.DATABASE_URL.replace('sqlite:///', '')
            return cls.PROJECT_ROOT / db_path
        else:
            # Non-SQLite database
            return None
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return cls.ENVIRONMENT == 'production'
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment"""
        return cls.ENVIRONMENT == 'development'
    
    @classmethod
    def display_config(cls):
        """Display current configuration (safe values only)"""
        print("=" * 60)
        print("MusicElo Configuration")
        print("=" * 60)
        print(f"Environment: {cls.ENVIRONMENT}")
        print(f"Debug Mode: {cls.DEBUG}")
        print(f"Database: {cls.DATABASE_URL}")
        print(f"Spotify Client ID: {cls.SPOTIFY_CLIENT_ID[:8]}..." if cls.SPOTIFY_CLIENT_ID else "Not set")
        print(f"Streamlit Port: {cls.STREAMLIT_SERVER_PORT}")
        print(f"\nGlicko-2 Parameters:")
        print(f"  - Tau: {cls.GLICKO2_TAU}")
        print(f"  - Default Rating: {cls.GLICKO2_DEFAULT_RATING}")
        print(f"  - Default RD: {cls.GLICKO2_DEFAULT_RD}")
        print(f"  - Default Volatility: {cls.GLICKO2_DEFAULT_VOLATILITY}")
        print("=" * 60)


# Validate configuration on import (fail fast if misconfigured)
if __name__ != '__main__':
    try:
        Config.validate()
    except ValueError as e:
        print(f"\n⚠️  Configuration Error:\n{e}\n")
        # Don't raise in import - let app handle gracefully
        pass


if __name__ == '__main__':
    # Display configuration when run directly
    try:
        Config.validate()
        Config.display_config()
    except ValueError as e:
        print(f"\n❌ Configuration validation failed:\n{e}")
        exit(1)
