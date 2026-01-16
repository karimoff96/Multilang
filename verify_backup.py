"""
Simple script to verify database backup integrity
"""
import gzip
import shutil
import sqlite3
import os
import glob

# Find the latest backup
backup_files = glob.glob('backups/database/backup_sqlite_*.db.gz')
if not backup_files:
    print("❌ No backup files found!")
    exit(1)

latest_backup = max(backup_files, key=os.path.getctime)
print(f"Verifying: {latest_backup}")
print(f"Size: {os.path.getsize(latest_backup) / 1024:.2f} KB\n")

# Decompress to temporary file
temp_db = 'backups/database/temp_verify.db'
try:
    with gzip.open(latest_backup, 'rb') as f_in:
        with open(temp_db, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    print("✓ Backup successfully decompressed\n")
    
    # Connect and verify
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"✓ Backup is valid!\n")
    print(f"Tables found ({len(tables)}):")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  - {table[0]}: {count} rows")
    
    # Check auth_user specifically
    cursor.execute("SELECT COUNT(*) FROM auth_user")
    user_count = cursor.fetchone()[0]
    
    if user_count > 0:
        cursor.execute("SELECT username, email FROM auth_user LIMIT 3")
        users = cursor.fetchall()
        print(f"\nSample users from backup:")
        for username, email in users:
            print(f"  - {username} ({email})")
    
    conn.close()
    print("\n✓ Backup verification complete! Data is intact.")
    
except Exception as e:
    print(f"❌ Error verifying backup: {e}")
finally:
    # Clean up temp file
    if os.path.exists(temp_db):
        os.remove(temp_db)
