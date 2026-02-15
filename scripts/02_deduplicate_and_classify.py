"""
Improved De-duplication and Classification

Key improvements:
1. KEEPS parentheses in display titles
2. Better variant detection (album-aware)
3. True deduplication (same video_id = same song)
4. Member tags preserved (DAHYUN, MINA, etc.)
"""

import pandas as pd
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImprovedSongProcessor:
    """Process songs with proper variant detection and deduplication"""
    
    def __init__(self):
        # Remix/mix markers (these indicate variants)
        self.remix_markers = [
            'house', 'moombahton', 'remix', 'mix', 'version 1.0', 'version 2.0',
            'sped up', 'slowed', 'acoustic', 'radio edit', 'extended',
            'instrumental', 'inst'
        ]
        
        # Language markers (these indicate language variants)
        self.language_markers = {
            'japanese': ['japanese ver', 'japan ver', 'jpn ver', '日本語', 'jp'],
            'english': ['english ver', 'eng ver', 'en'],
            'korean': ['korean ver', 'kor ver', 'kr']
        }
        
        # These are informational, NOT variant markers
        self.info_markers = [
            'dahyun', 'mina', 'nayeon', 'jihyo', 'sana', 'momo', 
            'chaeyoung', 'tzuyu', 'jeongyeon',  # Member names
            'rewind', 'heart shaker',  # English subtitles
        ]
    
    def extract_parenthetical_content(self, title: str) -> List[Tuple[str, str]]:
        """
        Extract content from parentheses
        
        Returns: List of (original, normalized) tuples
        Example: "CHESS (DAHYUN)" → [("DAHYUN", "dahyun")]
        """
        pattern = r'\(([^)]+)\)'
        matches = re.findall(pattern, title)
        return [(m, m.lower().strip()) for m in matches]
    
    def classify_parenthetical(self, content: str, album: str) -> Optional[str]:
        """
        Classify what a parenthetical means
        
        Returns:
        - 'remix': It's a remix/mix variant
        - 'language': It's a language variant  
        - 'feature': It's a feature credit (keep as original)
        - 'info': It's informational (keep in title)
        - None: Unknown/ambiguous
        """
        content_lower = content.lower()
        
        # Check remix markers
        for marker in self.remix_markers:
            if marker in content_lower:
                return 'remix'
        
        # Check language markers
        for lang, markers in self.language_markers.items():
            for marker in markers:
                if marker in content_lower:
                    return 'language'
        
        # Feature credit
        if 'feat' in content_lower or 'ft' in content_lower:
            return 'feature'
        
        # Info markers (member names, subtitles)
        for marker in self.info_markers:
            if marker in content_lower:
                return 'info'
        
        # Check album context for remixes
        # e.g., if album is "Strategy 2.0", treat as remix album
        if '2.0' in album or 'remix' in album.lower():
            # Likely a remix even if not explicitly marked
            return 'remix'
        
        return None
    
    def extract_base_title(self, title: str) -> str:
        """
        Extract base title for grouping (removes only variant markers)
        
        Example:
        - "Strategy (House)" → "Strategy"
        - "CHESS (DAHYUN)" → "CHESS (DAHYUN)"  ← Keeps member name
        - "알고 싶지 않아 (REWIND)" → "알고 싶지 않아 (REWIND)"  ← Keeps subtitle
        """
        base_title = title
        
        # Extract parentheticals
        parens = self.extract_parenthetical_content(title)
        
        # Remove only remix/language variant markers
        for original, normalized in parens:
            classification = self.classify_parenthetical(normalized, "")
            
            if classification in ['remix', 'language']:
                # Remove this parenthetical
                base_title = base_title.replace(f"({original})", "").strip()
        
        # Clean up extra spaces
        base_title = re.sub(r'\s+', ' ', base_title).strip()
        
        return base_title
    
    def detect_variant_type(self, title: str, album: str, language: str) -> Optional[str]:
        """
        Detect variant type from title and album context
        
        Returns: variant_type or None if original
        """
        title_lower = title.lower()
        album_lower = album.lower() if pd.notna(album) else ""
        
        # Extract parentheticals
        parens = self.extract_parenthetical_content(title)
        
        for original, normalized in parens:
            classification = self.classify_parenthetical(normalized, album)
            
            if classification == 'remix':
                # Determine specific remix type
                if 'house' in normalized:
                    return 'remix_house'
                elif 'moombahton' in normalized:
                    return 'remix_moombahton'
                elif 'sped up' in normalized:
                    return 'sped_up'
                elif 'slowed' in normalized:
                    return 'slowed'
                elif 'acoustic' in normalized:
                    return 'acoustic'
                elif 'inst' in normalized:
                    return 'instrumental'
                else:
                    return 'remix'
            
            elif classification == 'language':
                # Determine language variant
                for lang, markers in self.language_markers.items():
                    for marker in markers:
                        if marker in normalized:
                            return f'{lang}_version'
        
        # Check album context
        if '2.0' in album or 'remix' in album_lower:
            if 'instrumental' not in title_lower:
                return 'remix'
        
        return None
    
    def detect_language(self, title: str, album: str, artist: str) -> str:
        """
        Detect song language
        
        Priority:
        1. Explicit language markers in title
        2. Album language markers
        3. Default to Korean for TWICE
        """
        title_lower = title.lower()
        album_lower = album.lower() if pd.notna(album) else ""
        
        # Check for instrumental
        if 'inst' in title_lower or 'instrumental' in title_lower:
            return 'instrumental'
        
        # Check explicit language markers
        parens = self.extract_parenthetical_content(title)
        for original, normalized in parens:
            for lang, markers in self.language_markers.items():
                for marker in markers:
                    if marker in normalized:
                        return lang
        
        # Check album markers
        if 'japanese' in album_lower or 'japan' in album_lower or '#twice' in album_lower:
            return 'japanese'
        elif 'english' in album_lower:
            return 'english'
        
        # Default for TWICE
        if 'twice' in artist.lower():
            return 'korean'
        
        return 'korean'
    
    def create_canonical_name(self, title: str, album: str) -> str:
        """
        Create canonical name (keeps important info, removes variants)
        
        This is used for grouping, NOT for display
        """
        # Get base title (removes variant markers)
        canonical = self.extract_base_title(title)
        
        # Normalize spaces and punctuation
        canonical = re.sub(r'\s+', ' ', canonical)
        canonical = canonical.strip()
        
        return canonical
    
    def process_songs(self, input_file: Path, output_file: Path):
        """
        Process songs from raw YTM data
        
        Key changes:
        1. Keeps full titles (display_title)
        2. Creates canonical_name for grouping
        3. Detects variants properly
        4. Preserves all metadata
        """
        logger.info(f"Loading raw tracks from {input_file}")
        df = pd.read_csv(input_file)
        
        logger.info(f"Processing {len(df)} tracks...")
        
        # Fill NaN albums with empty string
        df['album'] = df['album'].fillna('')
        
        logger.info(f"Processing {len(df)} tracks...")
        
        # Add new columns
        df['display_title'] = df['title']  # Keep original title
        df['canonical_name'] = ''
        df['variant_type'] = None
        df['is_original'] = True
        df['language'] = 'korean'
        df['original_video_id'] = None
        
        # Process each song
        for idx, row in df.iterrows():
            title = row['title']
            album = row.get('album', '')
            artist = row.get('artists', 'TWICE')
            
            # Create canonical name (for grouping)
            canonical = self.create_canonical_name(title, album)
            df.at[idx, 'canonical_name'] = canonical
            
            # Detect variant type
            variant_type = self.detect_variant_type(title, album, row.get('language', 'korean'))
            df.at[idx, 'variant_type'] = variant_type
            df.at[idx, 'is_original'] = (variant_type is None)
            
            # Detect language
            language = self.detect_language(title, album, artist)
            df.at[idx, 'language'] = language
        
        # Group by video_id (same video_id = exact same song)
        logger.info("Removing exact duplicates (same video_id)...")
        df_unique = df.drop_duplicates(subset=['video_id'], keep='first')
        
        logger.info(f"Removed {len(df) - len(df_unique)} exact duplicates")
        
        # Now link variants to originals
        logger.info("Linking variants to originals...")
        
        # Group by canonical_name + artists
        groups = df_unique.groupby(['canonical_name', 'artists'])
        
        variants_linked = 0
        for (canonical, artists), group in groups:
            if len(group) == 1:
                continue
            
            # Find the original (no variant_type)
            originals = group[group['is_original'] == True]
            
            if len(originals) == 0:
                # No clear original, pick first one
                original_id = group.iloc[0]['video_id']
            elif len(originals) == 1:
                original_id = originals.iloc[0]['video_id']
            else:
                # Multiple originals, pick the one from standard album (not remix album)
                standard_albums = originals[~originals['album'].str.contains('2.0|Remix', case=False, na=False)]
                if len(standard_albums) > 0:
                    original_id = standard_albums.iloc[0]['video_id']
                else:
                    original_id = originals.iloc[0]['video_id']
            
            # Link variants to original
            for idx, variant in group[group['is_original'] == False].iterrows():
                df_unique.at[idx, 'original_video_id'] = original_id
                variants_linked += 1
        
        logger.info(f"Linked {variants_linked} variants to originals")
        
        # Summary statistics
        logger.info("\n=== Processing Summary ===")
        logger.info(f"Total unique songs: {len(df_unique)}")
        logger.info(f"  Originals: {df_unique['is_original'].sum()}")
        logger.info(f"  Variants: {(~df_unique['is_original']).sum()}")
        logger.info(f"\nLanguage breakdown:")
        for lang, count in df_unique['language'].value_counts().items():
            logger.info(f"  {lang}: {count}")
        logger.info(f"\nVariant types:")
        for vtype, count in df_unique['variant_type'].value_counts().items():
            if pd.notna(vtype):
                logger.info(f"  {vtype}: {count}")
        
        # Save
        logger.info(f"\nSaving to {output_file}")
        df_unique.to_csv(output_file, index=False)
        logger.info("✅ Done!")
        
        return df_unique


def main():
    """Main entry point"""
    processor = ImprovedSongProcessor()
    
    input_file = Path('data/ytm_raw_tracks.csv')
    output_file = Path('data/ytm_deduplicated.csv')
    
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print("   Run script 01 first: python scripts/01_fetch_ytm_playlists.py")
        return
    
    processor.process_songs(input_file, output_file)


if __name__ == '__main__':
    main()
