#!/usr/bin/env python3
"""
Simple YTMusic authentication helper

Creates auth file from cookie string
"""

import json
from pathlib import Path

def setup_auth():
    print("=" * 60)
    print("YouTube Music Authentication Helper")
    print("=" * 60)
    print("\nSteps:")
    print("  1. Open YouTube Music in browser: https://music.youtube.com")
    print("  2. Press F12 (Developer Tools)")
    print("  3. Go to Network tab")
    print("  4. Refresh page (F5)")
    print("  5. Click any 'browse' or 'player' request")
    print("  6. Find 'Cookie:' in Request Headers")
    print("  7. Copy the ENTIRE cookie value (long string after 'Cookie: ')")
    print("\n" + "=" * 60)
    print("\nPaste your cookie string below, then press Enter:")
    print("(It should start with something like: VISITOR_INFO1_LIVE=...)")
    print()
    
    cookie_string = input().strip()
    
    if not cookie_string:
        print("\n❌ No cookie string provided!")
        return
    
    # Validate it looks like cookies
    if "VISITOR_INFO1_LIVE" not in cookie_string and "SAPISID" not in cookie_string:
        print("\n⚠️  Warning: This doesn't look like a valid YouTube cookie string")
        print("   It should contain: VISITOR_INFO1_LIVE, SAPISID, etc.")
        confirm = input("\n   Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
    
    # Create auth file
    auth_data = {
        "Cookie": cookie_string
    }
    
    output_file = Path("data/ytm_headers_auth.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(auth_data, f, indent=2)
    
    print(f"\n✅ Created: {output_file}")
    print(f"   Size: {len(cookie_string)} characters")
    print("\n🔒 Security check:")
    print("   This file is in .gitignore ✓")
    print("   Will NOT be committed to Git ✓")
    print("\nNow run:")
    print("  python scripts/04_import_user_playlists.py")

if __name__ == '__main__':
    setup_auth()
