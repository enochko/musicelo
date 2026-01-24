"""
De-duplicate songs and classify variants

Handles:
- Same song appearing multiple times (keep one)
- Variants (Japanese versions, remixes, etc.) - link to originals
- Language detection
- Variant type classification
"""

import pandas as pd
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional


class SongDeduplicator:
    """De-duplicate songs and classify variants"""
    
    def __init__(self):
        # Variant detection patterns
        self.variant_patterns = {
            'japanese_version': [
                r'japanese ver\.?',
                r'japan ver\.?',
                r'jpn ver\.?',
                r'日本語',
                r'\(jp\)',
                r'\(japanese\)',
            ],
            'english_version': [
                r'english ver\.?',
                r'eng ver\.?',
                r'\(en\)',
                r'\(english\)',
            ],
            'instrumental': [
                r'instrumental',
                r'inst\.?\s*$',
                r'\(inst\)',
            ],
            'remix': [
                r'remix',
                r'remixed by',
                r'mix\)',
                r'edit\)',
            ],
            'live': [
                r'\blive\b',
                r'concert',
                r'tour\s+ver',
            ],
            'acoustic': [
                r'acoustic',
                r'unplugged',
            ],
            'sped_up': [
                r'sped\s*up',
                r'speed\s*up',
                r'nightcore',
                r'fast',
            ],
            'slowed': [
                r'slowed',
                r'reverb',
                r'slow',
            ],
            'radio_edit': [
                r'radio\s+edit',
                r'radio\s+ver',
            ],
        }
        
        # Markers to remove when extracting canonical name
        self.remove_patterns = [
            r'\([^)]*\)',  # Anything in parentheses
            r'\[[^\]]*\]',  # Anything in brackets
            r'-\s*\d{4}',   # Year suffix like "- 2024"
            r'official\s+audio',
            r'official\s+video',
            r'm/?v',
        ]
    
    def detect_variant_type(self, title: str) -> Optional[str]:
        """
        Detect if song is a variant and what type
        
        Args:
            title: Song title
        
        Returns:
            Variant type or None if original
        """
        title_lower = title.lower()
        
        for variant_type, patterns in self.variant_patterns.items():
            for pattern in patterns:
                if re.search(pattern, title_lower):
                    return variant_type
        
        return None
    
    def extract_canonical_name(self, title: str) -> str:
        """
        Extract base song name without variant info
        
        Args:
            title: Full song title
        
        Returns:
            Canonical name (e.g., "Like OOH-AHH")
        """
        canonical = title
        
        # Remove variant markers
        for patterns in self.variant_patterns.values():
            for pattern in patterns:
                canonical = re.sub(pattern, '', canonical, flags=re.IGNORECASE)
        
        # Remove common suffixes/prefixes
        for pattern in self.remove_patterns:
            canonical = re.sub(pattern, '', canonical, flags=re.IGNORECASE)
        
        # Clean up whitespace
        canonical = re.sub(r'\s+', ' ', canonical).strip()
        
        # Remove trailing dashes or commas
        canonical = re.sub(r'[\s\-,]+$', '', canonical)
        
        return canonical
    
    def similarity(self, a: str, b: str) -> float:
        """Calculate string similarity (0.0 to 1.0)"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def detect_language(self, title: str, album: str, artists: str) -> str:
        """
        Detect song language
        
        Args:
            title: Song title
            album: Album name
            artists: Artist names
        
        Returns:
            Language: korean, japanese, english, or instrumental
        """
        title_lower = title.lower()
        album_lower = album.lower() if pd.notna(album) else ''
        
        # Instrumental
        if re.search(r'instrumental|inst\.?\s*$|\(inst\)', title_lower):
            return 'instrumental'
        
        # Japanese - check title markers
        if re.search(r'japanese ver|japan ver|jpn ver|日本語|\(jp\)', title_lower):
            return 'japanese'
        
        # Japanese - check album
        japanese_albums = ['#twice', 'bdz', '&twice', 'candy pop', 'wake me up', 
                          'one more time', 'brand new girl', '#twice2', '#twice3',
                          '#twice4', 'breakthrough', 'celebrate', 'doughnut', 'perfect world']
        if any(jp_album in album_lower for jp_album in japanese_albums):
            # But not if it's explicitly marked as another language
            if 'ver' not in title_lower:
                return 'japanese'
        
        # English - check title markers
        if re.search(r'english ver|eng ver|\(en\)', title_lower):
            return 'english'
        
        # English - check album
        english_albums = ['the feels', 'moonlight sunrise', 'strategy', 'i got you']
        if album_lower in english_albums:
            if 'ver' not in title_lower:
                return 'english'
        
        # Default to Korean
        return 'korean'
    
    def group_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Group songs that are duplicates or variants
        
        Strategy:
        - Same canonical_name + artists = same song (keep one)
        - Different variant_type = separate songs (link as variants)
        
        Args:
            df: DataFrame with raw tracks
        
        Returns:
            De-duplicated DataFrame with variant links
        """
        # Add canonical name and variant detection
        df['canonical_name'] = df['title'].apply(self.extract_canonical_name)
        df['variant_type'] = df['title'].apply(self.detect_variant_type)
        df['language'] = df.apply(
            lambda row: self.detect_language(
                row['title'],
                row.get('album', ''),
                row.get('artists', '')
            ),
            axis=1
        )
        
        # Mark originals
        df['is_original'] = df['variant_type'].isna()
        
        # Group by canonical name + artists
        grouped = df.groupby(['canonical_name', 'artists'])
        
        deduplicated = []
        
        for (canonical, artists), group in grouped:
            # Sort: originals first, then by playlist order
            group = group.sort_values(
                by=['is_original', 'position_in_playlist'],
                ascending=[False, True]
            )
            
            if len(group) == 1:
                # Single occurrence - keep as is
                song = group.iloc[0].to_dict()
                song['duplicate_count'] = 1
                song['original_video_id'] = None
                deduplicated.append(song)
            
            else:
                # Multiple occurrences
                # Find the original (first non-variant)
                originals = group[group['is_original'] == True]
                
                if len(originals) > 0:
                    # Have an original - use it as reference
                    original = originals.iloc[0]
                    original_video_id = original['video_id']
                else:
                    # No clear original - use first one
                    original = group.iloc[0]
                    original_video_id = original['video_id']
                
                # Process all songs in group
                for idx, row in group.iterrows():
                    song = row.to_dict()
                    song['duplicate_count'] = len(group)
                    
                    # Link variants to original
                    if song['video_id'] == original_video_id:
                        song['original_video_id'] = None  # This IS the original
                    else:
                        song['original_video_id'] = original_video_id
                    
                    deduplicated.append(song)
        
        result_df = pd.DataFrame(deduplicated)
        
        # Clean up duplicates with same video_id (keep first occurrence)
        result_df = result_df.drop_duplicates(subset=['video_id'], keep='first')
        
        return result_df
    
    def run(self, input_file: str = 'data/ytm_raw_tracks.csv', output_dir: str = 'data') -> pd.DataFrame:
        """
        De-duplicate and classify all songs
        
        Args:
            input_file: Path to raw tracks CSV
            output_dir: Directory for output files
        
        Returns:
            De-duplicated DataFrame
        """
        print("=" * 60)
        print("Song De-duplicator & Classifier")
        print("=" * 60)
        
        # Load raw data
        try:
            df = pd.read_csv(input_file)
            print(f"\n✅ Loaded {len(df)} raw tracks from: {input_file}")
        except FileNotFoundError:
            print(f"\n❌ Error: File not found: {input_file}")
            print("    Run script 01 first: python scripts/01_fetch_ytm_playlists.py")
            return pd.DataFrame()
        
        # De-duplicate
        print("\n🔍 De-duplicating and classifying...")
        df_dedup = self.group_duplicates(df)
        
        # Statistics
        originals = df_dedup[df_dedup['is_original'] == True]
        variants = df_dedup[df_dedup['is_original'] == False]
        
        print(f"\n{'='*60}")
        print(f"Results:")
        print(f"  Raw tracks: {len(df)}")
        print(f"  Unique songs: {len(df_dedup)}")
        print(f"  └─ Original songs: {len(originals)}")
        print(f"  └─ Variants: {len(variants)}")
        
        # Language breakdown
        if 'language' in df_dedup.columns:
            print(f"\n  Language distribution:")
            for lang, count in df_dedup['language'].value_counts().items():
                print(f"    {lang}: {count}")
        
        # Variant breakdown
        if len(variants) > 0 and 'variant_type' in variants.columns:
            print(f"\n  Variant types:")
            for vtype, count in variants['variant_type'].value_counts().items():
                if pd.notna(vtype):
                    print(f"    {vtype}: {count}")
        
        print(f"{'='*60}")
        
        # Save
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir) / 'ytm_deduplicated.csv'
        df_dedup.to_csv(output_file, index=False)
        print(f"\n💾 Saved de-duplicated data to: {output_file}")
        
        # Show examples
        if len(variants) > 0:
            print("\n📋 Example variants:")
            variant_examples = variants.groupby('variant_type').first()
            for vtype, row in variant_examples.iterrows():
                if pd.notna(vtype):
                    print(f"  {vtype}:")
                    print(f"    Title: {row['title']}")
                    print(f"    Original: {row['canonical_name']}")
        
        print("\n✅ De-duplication complete!")
        print("\nNext step:")
        print("  python scripts/03_extract_album_info.py")
        
        return df_dedup


def main():
    """Main entry point"""
    dedup = SongDeduplicator()
    df = dedup.run()


if __name__ == '__main__':
    main()
