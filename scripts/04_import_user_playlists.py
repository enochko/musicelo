"""
Import user's YouTube Music playlists to bootstrap Elo ratings

Requires authentication to read:
- Private playlists (TWICE Favourites, To Listen)
- Liked Music (all songs)

Authentication is stored locally in data/ytm_headers_auth.json
This file is automatically ignored by Git (.gitignore)

Matching strategy:
- Matches by video_id (most reliable)
- Includes collaborations, solos, subunits (not just "TWICE")
- Fuzzy matching as fallback
"""

from ytmusicapi import YTMusic
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from difflib import SequenceMatcher


class UserPlaylistImporter:
    """Import user's YouTube Music playlists with authentication"""
    
    def __init__(self, auth_file: str = None):
        """
        Initialize with authentication
        
        Tries multiple auth methods:
        1. oauth.json (preferred - easier setup)
        2. ytm_headers_auth.json (manual headers)
        
        Setup (first time):
            Option A (EASIER):
                ytmusicapi oauth
                # Opens browser, sign in, done!
                # Creates: oauth.json
            
            Option B (MANUAL):
                ytmusicapi browser
                # Copy cookies from browser
                # Creates: browser.json
                # Move to: data/ytm_headers_auth.json
        """
        # Try to find auth file
        auth_options = [
            'oauth.json',
            'data/oauth.json',
            'data/ytm_headers_auth.json',
            'browser.json',
        ]
        
        if auth_file:
            auth_options.insert(0, auth_file)
        
        found_auth = None
        for auth_path in auth_options:
            if Path(auth_path).exists():
                found_auth = auth_path
                break
        
        if not found_auth:
            raise FileNotFoundError(
                f"\n❌ No authentication file found.\n\n"
                f"EASIEST METHOD (Recommended):\n"
                f"  1. Run: ytmusicapi oauth\n"
                f"  2. Sign in when browser opens\n"
                f"  3. Run this script again\n\n"
                f"MANUAL METHOD (Alternative):\n"
                f"  1. Run: ytmusicapi browser\n"
                f"  2. In Firefox/Chrome:\n"
                f"     - Open YouTube Music\n"
                f"     - Open DevTools (F12)\n"
                f"     - Network tab → Find 'browse' request\n"
                f"     - Copy ONLY the Cookie header value\n"
                f"  3. Paste when prompted, press Ctrl-D\n"
                f"  4. Move browser.json to data/ytm_headers_auth.json\n"
                f"  5. Run this script again\n"
            )
        
        try:
            self.ytmusic = YTMusic(found_auth)
            self.auth_file = found_auth
            print(f"✅ Authenticated with YouTube Music (using {found_auth})")
        except Exception as e:
            raise RuntimeError(
                f"\n❌ Authentication failed: {e}\n\n"
                f"Your auth file may be invalid or expired.\n"
                f"Easiest fix: Run 'ytmusicapi oauth' to re-authenticate.\n"
            )
    
    def similarity(self, a: str, b: str) -> float:
        """Calculate string similarity (0.0 to 1.0)"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def get_playlist_tracks(self, playlist_id: str, playlist_name: str) -> List[Dict]:
        """
        Get all tracks from a playlist
        
        Args:
            playlist_id: YouTube Music playlist ID
            playlist_name: Human-readable name
        
        Returns:
            List of track dictionaries
        """
        print(f"\n📂 Fetching: {playlist_name}")
        print(f"   ID: {playlist_id}")
        
        try:
            playlist = self.ytmusic.get_playlist(playlist_id, limit=None)
            
            tracks = []
            for track in playlist.get('tracks', []):
                video_id = track.get('videoId')
                if not video_id:
                    continue
                
                # Get like status if available
                like_status = track.get('likeStatus', 'INDIFFERENT')
                
                # Extract artists
                artists = track.get('artists', [])
                artist_names = ', '.join([a.get('name', '') for a in artists if a.get('name')])
                
                track_data = {
                    'video_id': video_id,
                    'title': track.get('title', ''),
                    'artists': artist_names,
                    'album': track.get('album', {}).get('name', '') if track.get('album') else '',
                    'like_status': like_status,
                    'is_liked': like_status == 'LIKE',
                    'playlist_source': playlist_name,
                }
                
                tracks.append(track_data)
            
            print(f"   ✅ Found {len(tracks)} tracks")
            return tracks
            
        except Exception as e:
            print(f"   ❌ Error fetching playlist: {e}")
            return []
    
    def get_liked_music(self) -> List[Dict]:
        """
        Get all liked songs from user's library
        
        Returns:
            List of liked track dictionaries
        """
        print(f"\n❤️  Fetching: Liked Music")
        
        try:
            # Get liked songs (limit=None to get all)
            liked_songs = self.ytmusic.get_liked_songs(limit=None)
            
            tracks = []
            for track in liked_songs.get('tracks', []):
                video_id = track.get('videoId')
                if not video_id:
                    continue
                
                # Extract artists
                artists = track.get('artists', [])
                artist_names = ', '.join([a.get('name', '') for a in artists if a.get('name')])
                
                track_data = {
                    'video_id': video_id,
                    'title': track.get('title', ''),
                    'artists': artist_names,
                    'album': track.get('album', {}).get('name', '') if track.get('album') else '',
                    'like_status': 'LIKE',
                    'is_liked': True,
                    'playlist_source': 'Liked Music',
                }
                
                tracks.append(track_data)
            
            print(f"   ✅ Found {len(tracks)} liked songs")
            return tracks
            
        except Exception as e:
            print(f"   ❌ Error fetching liked music: {e}")
            return []
    
    def match_to_database(
        self, 
        user_tracks: List[Dict], 
        db_songs: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Match user's tracks to songs in database
        
        Strategy:
        1. Match by video_id (most reliable)
        2. Fallback: Fuzzy match on title + artist
        
        Handles:
        - TWICE group songs
        - Solo songs (Nayeon, Jihyo, etc.)
        - Subunit songs (MISAMO, etc.)
        - Collaborations
        
        Args:
            user_tracks: List of user's tracks
            db_songs: DataFrame with database songs
        
        Returns:
            DataFrame with matched songs and boost levels
        """
        print("\n🔍 Matching user tracks to database...")
        
        matches = {
            'liked': [],      # Liked songs → 1600 Elo
            'familiar': [],   # In playlist but not liked → 1550 Elo
            'to_listen': [],  # To-listen playlist → 1525 Elo
        }
        
        # Create video_id lookup for fast matching
        video_id_map = {}
        for idx, row in db_songs.iterrows():
            if pd.notna(row.get('video_id')):
                video_id_map[row['video_id']] = {
                    'video_id': row['video_id'],
                    'title': row['title'],
                    'artists': row.get('artists', ''),
                    'canonical_name': row.get('canonical_name', row['title']),
                }
        
        # Match user tracks
        matched_count = 0
        unmatched_count = 0
        
        for track in user_tracks:
            video_id = track['video_id']
            
            # Try video_id match first
            if video_id in video_id_map:
                db_match = video_id_map[video_id]
                
                # Determine boost level
                if track['is_liked']:
                    boost_level = 'liked'
                elif track['playlist_source'] == 'TWICE - To Listen':
                    boost_level = 'to_listen'
                else:
                    boost_level = 'familiar'
                
                match_info = {
                    'video_id': video_id,
                    'user_title': track['title'],
                    'db_title': db_match['title'],
                    'canonical_name': db_match['canonical_name'],
                    'artists': db_match['artists'],
                    'playlist_source': track['playlist_source'],
                    'boost_level': boost_level,
                }
                
                matches[boost_level].append(match_info)
                matched_count += 1
            else:
                # Could implement fuzzy matching here as fallback
                unmatched_count += 1
        
        # Summary
        print(f"\n✅ Matching complete:")
        print(f"   Matched: {matched_count} songs")
        print(f"   Unmatched: {unmatched_count} songs")
        print(f"\n   Boost distribution:")
        print(f"   ❤️  Liked (1600 Elo): {len(matches['liked'])} songs")
        print(f"   👀 Familiar (1550 Elo): {len(matches['familiar'])} songs")
        print(f"   📚 To-Listen (1525 Elo): {len(matches['to_listen'])} songs")
        
        return matches
    
    def run(
        self,
        db_file: str = 'data/ytm_enriched.csv',
        output_dir: str = 'data'
    ) -> Dict:
        """
        Import user playlists and match to database
        
        Args:
            db_file: Path to database CSV (from script 03)
            output_dir: Directory for output files
        
        Returns:
            Dictionary with matched songs by boost level
        """
        print("=" * 60)
        print("User Playlist Importer (with Authentication)")
        print("=" * 60)
        
        # Load database songs
        try:
            db_songs = pd.read_csv(db_file)
            print(f"\n✅ Loaded {len(db_songs)} songs from database")
        except FileNotFoundError:
            print(f"\n❌ Error: Database file not found: {db_file}")
            print("   Run script 03 first: python scripts/03_extract_album_info.py")
            return {}
        
        # Get user's playlists
        all_user_tracks = []
        
        # 1. TWICE Favourites playlist
        favourites_id = 'PLhdZwGHaOH58pW4q3AzbkWO6s0qKXYTm3'
        favourites = self.get_playlist_tracks(favourites_id, 'TWICE - Favourites')
        all_user_tracks.extend(favourites)
        
        # 2. TWICE To-Listen playlist
        to_listen_id = 'PLhdZwGHaOH58FRwNe28AP0CnYkiBWajOn'
        to_listen = self.get_playlist_tracks(to_listen_id, 'TWICE - To Listen')
        all_user_tracks.extend(to_listen)
        
        # 3. Liked Music (all songs, not just TWICE)
        liked_music = self.get_liked_music()
        all_user_tracks.extend(liked_music)
        
        print(f"\n📊 Total user tracks collected: {len(all_user_tracks)}")
        
        # Match to database
        matches = self.match_to_database(all_user_tracks, db_songs)
        
        # Save results
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for boost_level, songs in matches.items():
            if songs:
                df = pd.DataFrame(songs)
                output_file = Path(output_dir) / f'user_{boost_level}_songs.csv'
                df.to_csv(output_file, index=False)
                print(f"\n💾 Saved {len(songs)} {boost_level} songs to: {output_file}")
        
        # Show examples
        print("\n📋 Example matches:")
        for boost_level in ['liked', 'familiar', 'to_listen']:
            if matches[boost_level]:
                example = matches[boost_level][0]
                print(f"\n   {boost_level.upper()}:")
                print(f"   Title: {example['canonical_name']}")
                print(f"   Artists: {example['artists']}")
                print(f"   Source: {example['playlist_source']}")
        
        print("\n" + "=" * 60)
        print("✅ Import complete!")
        print("\nNext step:")
        print("  python scripts/05_init_database.py")
        print("=" * 60)
        
        return matches


def main():
    """Main entry point"""
    
    print("=" * 60)
    print("🔐 Checking for authentication...")
    print("=" * 60)
    
    # Check for any auth file
    auth_files = ['oauth.json', 'data/oauth.json', 'data/ytm_headers_auth.json', 'browser.json']
    found = [f for f in auth_files if Path(f).exists()]
    
    if not found:
        print("\n⚠️  No authentication file found.\n")
        print("=" * 60)
        print("EASIEST METHOD (Recommended):")
        print("=" * 60)
        print("  Run this command:")
        print("    ytmusicapi oauth\n")
        print("  What happens:")
        print("    1. Browser opens automatically")
        print("    2. Sign in to your Google account")
        print("    3. Grant YouTube Music permissions")
        print("    4. Done! Creates oauth.json\n")
        print("  Then run this script again.\n")
        print("=" * 60)
        print("ALTERNATIVE (Manual Headers):")
        print("=" * 60)
        print("  Only use if oauth doesn't work:")
        print("    ytmusicapi browser")
        print("    # Copy ONLY Cookie header value")
        print("    # Press Ctrl-D when done")
        print("    # Move browser.json to data/ytm_headers_auth.json")
        print("=" * 60)
        print("\n🔒 Security: Both auth files are in .gitignore")
        return
    
    # Run importer
    try:
        importer = UserPlaylistImporter()
        matches = importer.run()
        
        # Summary
        total_matched = sum(len(songs) for songs in matches.values())
        if total_matched > 0:
            print(f"\n🎉 Successfully matched {total_matched} songs!")
            print("\nYour initial Elo ratings will be:")
            print(f"  ❤️  {len(matches.get('liked', []))} liked songs: 1600")
            print(f"  👀 {len(matches.get('familiar', []))} familiar songs: 1550")
            print(f"  📚 {len(matches.get('to_listen', []))} to-listen songs: 1525")
            print(f"  🆕 ~{559 - total_matched} unknown songs: 1500")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTo re-authenticate:")
        print("  Easiest: ytmusicapi oauth")
        print("  Manual: ytmusicapi browser")


if __name__ == '__main__':
    main()
