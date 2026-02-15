"""
Security utilities for MusicElo

Functions for:
- HTML escaping (XSS prevention)
- YouTube video ID validation
- Input sanitization
"""

import re
import html
from typing import Optional


class SecurityUtils:
    """Security utilities for user-facing content"""
    
    # YouTube video ID regex (11 characters: A-Za-z0-9_-)
    YOUTUBE_VIDEO_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{11}$')
    
    @staticmethod
    def escape_html(text: str) -> str:
        """
        Escape HTML special characters to prevent XSS
        
        Converts: < > & " '
        
        Example:
            escape_html("<script>alert('xss')</script>")
            # Returns: "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        """
        if not text:
            return ""
        return html.escape(str(text), quote=True)
    
    @staticmethod
    def validate_youtube_video_id(video_id: str) -> bool:
        """
        Validate YouTube video ID format
        
        Valid format: Exactly 11 characters, alphanumeric plus _ and -
        
        Examples:
            validate_youtube_video_id("dQw4w9WgXcQ")  # True
            validate_youtube_video_id("invalid")      # False
            validate_youtube_video_id("<script>")     # False
        """
        if not video_id:
            return False
        
        return bool(SecurityUtils.YOUTUBE_VIDEO_ID_PATTERN.match(video_id))
    
    @staticmethod
    def sanitize_youtube_video_id(video_id: str) -> Optional[str]:
        """
        Sanitize and validate YouTube video ID
        
        Returns:
            Valid video ID or None if invalid
        """
        if not video_id:
            return None
        
        # Remove whitespace
        video_id = str(video_id).strip()
        
        # Validate
        if SecurityUtils.validate_youtube_video_id(video_id):
            return video_id
        
        return None
    
    @staticmethod
    def create_safe_youtube_embed(
        video_id: str,
        width: str = "100%",
        height: int = 400,
        autoplay: bool = False
    ) -> Optional[str]:
        """
        Create safe YouTube embed iframe
        
        Args:
            video_id: YouTube video ID
            width: iframe width (CSS value)
            height: iframe height (pixels)
            autoplay: Enable autoplay
        
        Returns:
            Safe iframe HTML or None if video_id invalid
        """
        # Validate video ID
        safe_id = SecurityUtils.sanitize_youtube_video_id(video_id)
        
        if not safe_id:
            return None
        
        # Build iframe with validated ID
        autoplay_param = "1" if autoplay else "0"
        
        iframe = f'''<iframe 
            width="{width}" 
            height="{height}" 
            src="https://www.youtube.com/embed/{safe_id}?autoplay={autoplay_param}" 
            frameborder="0" 
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
            allowfullscreen>
        </iframe>'''
        
        return iframe
    
    @staticmethod
    def sanitize_search_query(query: str, max_length: int = 200) -> str:
        """
        Sanitize search query for database
        
        Args:
            query: User search query
            max_length: Maximum query length
        
        Returns:
            Sanitized query
        """
        if not query:
            return ""
        
        # Convert to string and strip
        query = str(query).strip()
        
        # Truncate
        query = query[:max_length]
        
        # Remove SQL wildcards if not intended
        # (SQLAlchemy parameterization already prevents injection)
        
        return query


# Convenience functions
def escape_html(text: str) -> str:
    """Escape HTML - convenience function"""
    return SecurityUtils.escape_html(text)


def safe_youtube_embed(
    video_id: str, 
    width: str = "100%",
    height: int = 400,
    autoplay: bool = False
) -> Optional[str]:
    """Create safe YouTube embed - convenience function"""
    return SecurityUtils.create_safe_youtube_embed(
        video_id, 
        width=width, 
        height=height, 
        autoplay=autoplay
    )


def validate_video_id(video_id: str) -> bool:
    """Validate video ID - convenience function"""
    return SecurityUtils.validate_youtube_video_id(video_id)
