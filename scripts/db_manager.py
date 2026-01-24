#!/usr/bin/env python3
"""
Database Backup and Reset Utility

Manage database backups and resets for testing
"""

import shutil
from pathlib import Path
from datetime import datetime
import sys

DB_PATH = Path("data/musicelo.db")
BACKUP_DIR = Path("data/backups")


def backup_database():
    """Create timestamped backup of current database"""
    if not DB_PATH.exists():
        print("❌ No database found to backup")
        return False
    
    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"musicelo_{timestamp}.db"
    
    shutil.copy2(DB_PATH, backup_path)
    
    # Get file size
    size_mb = backup_path.stat().st_size / (1024 * 1024)
    
    print(f"✅ Database backed up to: {backup_path}")
    print(f"   Size: {size_mb:.2f} MB")
    print(f"   Timestamp: {timestamp}")
    
    return backup_path


def list_backups():
    """List all available backups"""
    if not BACKUP_DIR.exists():
        print("📂 No backups directory")
        return []
    
    backups = sorted(BACKUP_DIR.glob("musicelo_*.db"), reverse=True)
    
    if not backups:
        print("📂 No backups found")
        return []
    
    print(f"\n📚 Available backups ({len(backups)}):")
    for i, backup in enumerate(backups, 1):
        size_mb = backup.stat().st_size / (1024 * 1024)
        timestamp = backup.stem.replace("musicelo_", "")
        # Parse timestamp for readable format
        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        readable = dt.strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {i}. {backup.name} ({size_mb:.2f} MB) - {readable}")
    
    return backups


def restore_backup(backup_path: Path):
    """Restore database from backup"""
    if not backup_path.exists():
        print(f"❌ Backup not found: {backup_path}")
        return False
    
    # Backup current database before restoring
    if DB_PATH.exists():
        print("\n⚠️  Current database will be replaced!")
        response = input("   Create backup of current database first? (y/n): ")
        if response.lower() == 'y':
            backup_database()
    
    # Restore
    shutil.copy2(backup_path, DB_PATH)
    print(f"✅ Database restored from: {backup_path.name}")
    
    return True


def reset_to_fresh():
    """Reset to fresh database (re-run initialization)"""
    if DB_PATH.exists():
        # Backup current
        print("\n💾 Backing up current database...")
        backup_database()
        
        # Delete current
        DB_PATH.unlink()
        print("🗑️  Current database deleted")
    
    print("\n🔄 To create fresh database, run:")
    print("   python scripts/05_init_database.py")


def main():
    """Main menu"""
    print("=" * 60)
    print("🗄️  MusicElo Database Manager")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("  1. Backup current database")
        print("  2. List backups")
        print("  3. Restore from backup")
        print("  4. Reset to fresh (delete & re-initialize)")
        print("  5. Exit")
        
        choice = input("\nChoice (1-5): ").strip()
        
        if choice == "1":
            backup_database()
        
        elif choice == "2":
            list_backups()
        
        elif choice == "3":
            backups = list_backups()
            if backups:
                try:
                    num = int(input("\nEnter backup number to restore: "))
                    if 1 <= num <= len(backups):
                        restore_backup(backups[num - 1])
                    else:
                        print("❌ Invalid backup number")
                except ValueError:
                    print("❌ Invalid input")
        
        elif choice == "4":
            confirm = input("\n⚠️  This will DELETE your current database. Continue? (yes/no): ")
            if confirm.lower() == "yes":
                reset_to_fresh()
            else:
                print("Cancelled")
        
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    main()
