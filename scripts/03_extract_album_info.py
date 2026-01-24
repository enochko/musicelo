"""
Extract album information and enrich song metadata

Creates albums table and links songs to albums
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime
from typing import Optional


class AlbumExtractor:
    """Extract and organize album information"""
    
    def __init__(self):
        # Known TWICE albums (will be expanded from data)
        self.album_type_keywords = {
            'single': ['single', 'digital single'],
            'ep': ['ep', 'mini'],
            'repackage': ['repackage', 'special'],
            'japanese': ['#twice', 'bdz', '&twice', 'candy pop', 'wake me up',
                        'one more time', 'brand new girl', 'breakthrough', 'celebrate'],
            'studio': [],  # Default fallback
        }
    
    def parse_album_type(self, album_name: str) -> str:
        """Determine album type from name"""
        if not album_name:
            return 'single'
        
        album_lower = album_name.lower()
        
        for album_type, keywords in self.album_type_keywords.items():
            if any(keyword in album_lower for keyword in keywords):
                return album_type
        
        # Default logic
        if 'twice' in album_lower or 'formula' in album_lower or 'eyes wide open' in album_lower:
            return 'studio'
        
        return 'ep'  # Default for unknown
    
    def detect_album_language(self, album_name: str) -> str:
        """Detect album's primary language"""
        if not album_name:
            return 'korean'
        
        album_lower = album_name.lower()
        
        # Japanese albums
        if any(jp in album_lower for jp in ['#twice', 'bdz', '&twice', 'candy pop', 
                                             'wake me up', 'breakthrough']):
            return 'japanese'
        
        # English singles
        if album_lower in ['the feels', 'moonlight sunrise', 'strategy', 'i got you']:
            return 'english'
        
        return 'korean'
    
    def run(self, input_file: str = 'data/ytm_deduplicated.csv', output_dir: str = 'data') -> tuple:
        """
        Extract album information
        
        Returns:
            (songs_df, albums_df) tuple
        """
        print("=" * 60)
        print("Album Information Extractor")
        print("=" * 60)
        
        # Load data
        try:
            df = pd.read_csv(input_file)
            print(f"\n✅ Loaded {len(df)} songs from: {input_file}")
        except FileNotFoundError:
            print(f"\n❌ Error: File not found: {input_file}")
            return None, None
        
        # Ensure language column exists (if not already added by deduplicator)
        if 'language' not in df.columns:
            print("  ⚠️  No language column found, using default 'korean'")
            df['language'] = 'korean'
        
        # Extract unique albums
        albums_data = []
        seen_albums = set()
        
        for _, row in df.iterrows():
            album_name = row.get('album', '')
            if pd.isna(album_name) or album_name == '':
                continue
            
            if album_name in seen_albums:
                continue
            
            seen_albums.add(album_name)
            
            album_info = {
                'album_name': album_name,
                'album_type': self.parse_album_type(album_name),
                'language': self.detect_album_language(album_name),
                'artist_name': row.get('artists', 'TWICE'),
            }
            
            albums_data.append(album_info)
        
        albums_df = pd.DataFrame(albums_data)
        
        print(f"\n✅ Extracted {len(albums_df)} unique albums")
        print(f"\n  Album type distribution:")
        for atype, count in albums_df['album_type'].value_counts().items():
            print(f"    {atype}: {count}")
        
        print(f"\n  Album language distribution:")
        for lang, count in albums_df['language'].value_counts().items():
            print(f"    {lang}: {count}")
        
        # Save outputs
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        albums_file = Path(output_dir) / 'albums.csv'
        albums_df.to_csv(albums_file, index=False)
        print(f"\n💾 Saved albums to: {albums_file}")
        
        songs_file = Path(output_dir) / 'ytm_enriched.csv'
        df.to_csv(songs_file, index=False)
        print(f"💾 Saved enriched songs to: {songs_file}")
        
        # Display sample
        print("\n📋 Sample albums:")
        sample_cols = ['album_name', 'album_type', 'language']
        print(albums_df[sample_cols].head(10).to_string(index=False))
        
        print("\n✅ Album extraction complete!")
        print("\nNext steps:")
        print("  1. Review data: streamlit run streamlit_app/pages/0_📋_Review_Data.py")
        print("  2. Initialize database: python scripts/05_init_database.py")
        
        return df, albums_df


def main():
    """Main entry point"""
    extractor = AlbumExtractor()
    songs_df, albums_df = extractor.run()


if __name__ == '__main__':
    main()
