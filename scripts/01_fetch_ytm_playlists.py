"""
Fetch TWICE songs from YouTube Music community playlists

Primary data source since Spotify API is currently unavailable
Fetches from 3 comprehensive community playlists
"""

from ytmusicapi import YTMusic
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

class YouTubeMusicPlaylistFetcher:
    """Fetch songs from YouTube Music public playlists"""
    
    def __init__(self):
        # No authentication needed for public playlists
        try:
            self.ytmusic = YTMusic()
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize YTMusic: {e}")
            print("Continuing without authentication (public playlists only)")
            self.ytmusic = YTMusic()
        
        # Community playlists - comprehensive TWICE discography
        self.playlists = [
            {
                'id': 'PLGpL_nBYyJ5aYgEp0T54lkxSg6GRuQHQZ',
                'name': 'TWICE Complete Discography #1',
                'url': 'https://music.youtube.com/playlist?list=PLGpL_nBYyJ5aYgEp0T54lkxSg6GRuQHQZ'
            },
            {
                'id': 'PL5jXuaOqUMtVGZstkNWayKhybNyVrW9lA',
                'name': 'TWICE All Songs #2',
                'url': 'https://music.youtube.com/playlist?list=PL5jXuaOqUMtVGZstkNWayKhybNyVrW9lA'
            },
            {
                'id': 'PLHPHZDuwUETkXn8t5HvghLY1QXZLlEB21',
                'name': 'TWICE Comprehensive #3',
                'url': 'https://music.youtube.com/playlist?list=PLHPHZDuwUETkXn8t5HvghLY1QXZLlEB21'
            }
        ]
    
    def parse_duration(self, duration_str: str) -> int:
        """
        Convert duration string to seconds
        
        Args:
            duration_str: Duration like "3:45" or "1:23:45"
        
        Returns:
            Duration in seconds
        """
        if not duration_str:
            return 0
        
        parts = duration_str.split(':')
        parts.reverse()
        
        seconds = 0
        for i, part in enumerate(parts):
            try:
                seconds += int(part) * (60 ** i)
            except ValueError:
                continue
        
        return seconds
    
    def fetch_playlist(self, playlist_id: str, playlist_name: str) -> List[Dict]:
        """
        Fetch all tracks from a playlist
        
        Args:
            playlist_id: YouTube Music playlist ID
            playlist_name: Human-readable playlist name
        
        Returns:
            List of track dictionaries
        """
        print(f"\nFetching: {playlist_name}")
        print(f"ID: {playlist_id}")
        
        try:
            # Get playlist with all tracks (limit=None for all)
            playlist = self.ytmusic.get_playlist(playlist_id, limit=None)
            
            tracks = []
            for idx, track in enumerate(playlist.get('tracks', []), 1):
                # Extract video ID
                video_id = track.get('videoId')
                if not video_id:
                    print(f"  ⚠️  Skipping track {idx}: No video ID")
                    continue
                
                # Extract artist names
                artists = track.get('artists', [])
                artist_names = ', '.join([a.get('name', '') for a in artists if a.get('name')])
                
                # Extract album info
                album_info = track.get('album', {})
                album_name = album_info.get('name', '') if album_info else ''
                
                # Get thumbnails (use highest quality)
                thumbnails = track.get('thumbnails', [])
                thumbnail_url = thumbnails[-1].get('url', '') if thumbnails else ''
                
                # Parse duration
                duration_str = track.get('duration', '')
                duration_seconds = self.parse_duration(duration_str)
                
                track_data = {
                    # Identity
                    'video_id': video_id,
                    'title': track.get('title', ''),
                    
                    # Artists & Album
                    'artists': artist_names,
                    'album': album_name,
                    
                    # Duration
                    'duration': duration_str,
                    'duration_seconds': duration_seconds,
                    'duration_ms': duration_seconds * 1000,
                    
                    # Media
                    'thumbnail_url': thumbnail_url,
                    
                    # URLs
                    'youtube_music_url': f"https://music.youtube.com/watch?v={video_id}",
                    'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
                    
                    # Source tracking
                    'playlist_id': playlist_id,
                    'playlist_name': playlist_name,
                    'position_in_playlist': idx,
                    'fetched_at': datetime.utcnow().isoformat(),
                }
                
                tracks.append(track_data)
            
            print(f"  ✅ Found {len(tracks)} tracks")
            return tracks
            
        except Exception as e:
            print(f"  ❌ Error fetching playlist: {e}")
            print(f"     Playlist may be private or unavailable")
            return []
    
    def run(self, output_dir: str = 'data') -> pd.DataFrame:
        """
        Fetch all playlists and save to CSV
        
        Args:
            output_dir: Directory to save output files
        
        Returns:
            DataFrame with all tracks
        """
        print("=" * 60)
        print("YouTube Music Playlist Fetcher")
        print("=" * 60)
        print("\nFetching from 3 community playlists...")
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        all_tracks = []
        
        for pl in self.playlists:
            tracks = self.fetch_playlist(pl['id'], pl['name'])
            all_tracks.extend(tracks)
            
            # Rate limiting - be nice to YouTube
            time.sleep(2)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_tracks)
        
        if len(df) == 0:
            print("\n❌ No tracks fetched. Check playlist IDs and internet connection.")
            return df
        
        print(f"\n{'='*60}")
        print(f"Collection Summary:")
        print(f"  Total tracks collected: {len(df)}")
        print(f"  Unique video IDs: {df['video_id'].nunique()}")
        print(f"  Duplicate entries: {len(df) - df['video_id'].nunique()}")
        
        # Album breakdown
        if 'album' in df.columns:
            albums = df['album'].value_counts()
            print(f"  Unique albums: {len(albums)}")
        
        print(f"{'='*60}")
        
        # Save raw data
        output_file = Path(output_dir) / 'ytm_raw_tracks.csv'
        df.to_csv(output_file, index=False)
        print(f"\n💾 Saved raw data to: {output_file}")
        
        # Show sample
        print("\n📋 Sample tracks:")
        sample_cols = ['title', 'artists', 'album', 'duration']
        available_cols = [col for col in sample_cols if col in df.columns]
        print(df[available_cols].head(10).to_string(index=False))
        
        # Save playlist metadata
        playlist_metadata = pd.DataFrame(self.playlists)
        metadata_file = Path(output_dir) / 'ytm_playlist_sources.csv'
        playlist_metadata.to_csv(metadata_file, index=False)
        print(f"\n💾 Saved playlist metadata to: {metadata_file}")
        
        return df


def main():
    """Main entry point"""
    fetcher = YouTubeMusicPlaylistFetcher()
    df = fetcher.run()
    
    if len(df) > 0:
        print("\n✅ Data collection complete!")
        print("\nNext step:")
        print("  python scripts/02_deduplicate_and_classify.py")
    else:
        print("\n⚠️  No data collected. Please check:")
        print("  1. Internet connection")
        print("  2. Playlist IDs are correct")
        print("  3. ytmusicapi is installed: pip install ytmusicapi")


if __name__ == '__main__':
    main()
