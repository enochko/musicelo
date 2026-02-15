"""
Security utilities test suite

Run with: pytest tests/test_security.py -v
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from core.utils.security import (
    SecurityUtils, 
    escape_html, 
    validate_video_id,
    safe_youtube_embed
)

class TestHTMLEscaping:
    """Test HTML escaping for XSS prevention"""
    
    def test_escape_basic_html(self):
        """Should escape < and >"""
        assert escape_html("<script>") == "&lt;script&gt;"
        assert escape_html("</div>") == "&lt;/div&gt;"
        
    def test_escape_quotes(self):
        """Should escape quotes"""
        result = escape_html("it's")
        assert '&#x27;' in result or '&#39;' in result
        
        result = escape_html('Say "hello"')
        assert '&quot;' in result or '&#34;' in result
        
    def test_escape_ampersand(self):
        """Should escape ampersands"""
        assert escape_html("A & B") == "A &amp; B"
        
    def test_empty_string(self):
        """Should handle empty strings"""
        assert escape_html("") == ""
        
    def test_none_value(self):
        """Should handle None"""
        assert escape_html(None) == ""
        
    def test_normal_text(self):
        """Should not modify normal text"""
        assert escape_html("Hello World") == "Hello World"
        
    def test_combined_escaping(self):
        """Should escape multiple special characters"""
        malicious = '<script>alert("XSS & <img>")</script>'
        result = escape_html(malicious)
        assert '<' not in result
        assert '>' not in result
        assert '&lt;' in result
        assert '&gt;' in result


class TestVideoIDValidation:
    """Test YouTube video ID validation"""
    
    def test_valid_video_id(self):
        """Should accept valid 11-character video IDs"""
        assert validate_video_id("dQw4w9WgXcQ") == True
        assert validate_video_id("0123456789_") == True
        assert validate_video_id("aBcDeFgHiJk") == True
        
    def test_invalid_too_short(self):
        """Should reject IDs shorter than 11 characters"""
        assert validate_video_id("short") == False
        assert validate_video_id("1234567890") == False
        
    def test_invalid_too_long(self):
        """Should reject IDs longer than 11 characters"""
        assert validate_video_id("toolongid12345") == False
        assert validate_video_id("123456789012") == False
        
    def test_invalid_characters(self):
        """Should reject IDs with invalid characters"""
        assert validate_video_id("<script>123") == False
        assert validate_video_id("hello world") == False
        assert validate_video_id("test@email!") == False
        assert validate_video_id("../../etc/") == False
        
    def test_empty_string(self):
        """Should reject empty strings"""
        assert validate_video_id("") == False
        
    def test_none_value(self):
        """Should reject None"""
        assert validate_video_id(None) == False
        
    def test_whitespace(self):
        """Should reject IDs with whitespace"""
        assert validate_video_id("has spaces1") == False
        assert validate_video_id("  dQw4w9WgXcQ") == False
        assert validate_video_id("dQw4w9WgXcQ  ") == False


class TestSafeIframe:
    """Test safe YouTube embed generation"""
    
    def test_valid_embed(self):
        """Should generate valid iframe for valid ID"""
        iframe = safe_youtube_embed("dQw4w9WgXcQ")
        assert iframe is not None
        assert "dQw4w9WgXcQ" in iframe
        assert "<iframe" in iframe
        assert "</iframe>" in iframe
        assert "youtube.com/embed" in iframe
        
    def test_invalid_embed_returns_none(self):
        """Should return None for invalid IDs"""
        iframe = safe_youtube_embed("<script>alert('xss')</script>")
        assert iframe is None
        
        iframe = safe_youtube_embed("short")
        assert iframe is None
        
        iframe = safe_youtube_embed("toolong123456")
        assert iframe is None
        
    def test_autoplay_parameter(self):
        """Should include correct autoplay parameter"""
        iframe_with = safe_youtube_embed("dQw4w9WgXcQ", autoplay=True)
        assert "autoplay=1" in iframe_with
        
        iframe_without = safe_youtube_embed("dQw4w9WgXcQ", autoplay=False)
        assert "autoplay=0" in iframe_without
        
    def test_custom_dimensions(self):
        """Should include custom width and height"""
        iframe = safe_youtube_embed("dQw4w9WgXcQ", width="50%", height=300)
        assert 'width="50%"' in iframe
        assert 'height="300"' in iframe
        
    def test_no_script_injection(self):
        """Should not allow script injection via parameters"""
        iframe = safe_youtube_embed('"><script>alert("xss")</script><"')
        assert iframe is None
        
        # Even if we somehow got past validation (we won't)
        # The iframe should not contain unescaped script tags
        if iframe:
            assert '<script>' not in iframe


class TestSecurityUtils:
    """Test SecurityUtils class methods"""
    
    def test_sanitize_youtube_video_id(self):
        """Should sanitize and validate video IDs"""
        # Valid IDs
        assert SecurityUtils.sanitize_youtube_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        
        # Trim whitespace
        assert SecurityUtils.sanitize_youtube_video_id("  dQw4w9WgXcQ  ") == "dQw4w9WgXcQ"
        
        # Invalid IDs
        assert SecurityUtils.sanitize_youtube_video_id("<script>") is None
        assert SecurityUtils.sanitize_youtube_video_id("") is None
        assert SecurityUtils.sanitize_youtube_video_id(None) is None
        
    def test_sanitize_search_query(self):
        """Should sanitize search queries"""
        # Normal query
        assert SecurityUtils.sanitize_search_query("TWICE") == "TWICE"
        
        # Trim whitespace
        assert SecurityUtils.sanitize_search_query("  TWICE  ") == "TWICE"
        
        # Truncate long queries
        long_query = "x" * 300
        result = SecurityUtils.sanitize_search_query(long_query, max_length=200)
        assert len(result) == 200
        
        # Handle None
        assert SecurityUtils.sanitize_search_query(None) == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
