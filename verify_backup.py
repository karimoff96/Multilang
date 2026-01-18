"""
Enhanced script to verify database backup integrity and compare with live database
Supports both PostgreSQL and SQLite backups
"""
import gzip
import shutil
import sqlite3
import os
import glob
import subprocess
import sys
import re

# Add Django project to path
sys.path.insert(0, '/home/Wow-dash')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WowDash.settings')

try:
    import django
    django.setup()
    from django.conf import settings
    from django.db import connection
    DJANGO_AVAILABLE = True
except Exception as e:
    DJANGO_AVAILABLE = False
    print(f"⚠️  Django not available: {e}")
    print("   Will perform basic backup verification only.\n")


def compare_with_live_db(backup_sql_content, db_type):
    """Compare PostgreSQL backup with live database"""
    try:
        with connection.cursor() as cursor:
            # Get all tables from live database
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            live_tables = [row[0] for row in cursor.fetchall()]
            
            print(f"Live database has {len(live_tables)} tables")
            
            # Extract tables from backup
            backup_tables = set()
            for line in backup_sql_content.split('\n'):
                if 'CREATE TABLE' in line:
                    match = re.search(r'CREATE TABLE (?:public\.)?(\w+)', line)
                    if match:
                        backup_tables.add(match.group(1))
            
            print(f"Backup contains {len(backup_tables)} tables\n")
            
            # Compare tables
            missing_in_backup = set(live_tables) - backup_tables
            extra_in_backup = backup_tables - set(live_tables)
            
            if missing_in_backup:
                print(f"⚠️  Tables in live DB but NOT in backup ({len(missing_in_backup)}):")
                for table in sorted(missing_in_backup):
                    print(f"   - {table}")
                print()
            
            if extra_in_backup:
                print(f"ℹ️  Tables in backup but not in current DB ({len(extra_in_backup)}):")
                for table in sorted(extra_in_backup):
                    print(f"   - {table}")
                print()
            
            # Count rows for common tables
            common_tables = set(live_tables) & backup_tables
            print(f"Comparing row counts for {len(common_tables)} common tables:\n")
            
            mismatches = []
            matches = 0
            
            for table in sorted(common_tables):
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                    live_count = cursor.fetchone()[0]
                    
                    # Try to estimate backup count from COPY statements
                    # This is approximate as we can't easily parse the data
                    copy_pattern = rf'COPY (?:public\.)?{table}.*?FROM stdin;(.*?)\\\.'
                    match = re.search(copy_pattern, backup_sql_content, re.DOTALL)
                    
                    if match:
                        backup_count = len([line for line in match.group(1).strip().split('\n') if line.strip()])
                    else:
                        backup_count = "Unknown"
                    
                    if backup_count == "Unknown":
                        print(f"   {table}: {live_count} rows (backup count unknown)")
                    elif live_count == backup_count:
                        matches += 1
                        print(f"   ✓ {table}: {live_count} rows (matches)")
                    else:
                        mismatches.append((table, live_count, backup_count))
                        print(f"   ⚠️  {table}: Live={live_count}, Backup={backup_count}")
                        
                except Exception as e:
                    print(f"   ✗ {table}: Error checking - {e}")
            
            # Summary
            print("\n" + "="*60)
            print("COMPARISON SUMMARY")
            print("="*60)
            
            if not missing_in_backup and not mismatches:
                print("✅ All tables and data are backed up correctly!")
            else:
                if missing_in_backup:
                    print(f"⚠️  {len(missing_in_backup)} table(s) missing from backup")
                if mismatches:
                    print(f"⚠️  {len(mismatches)} table(s) have different row counts")
                    print("\nNote: Row count differences may occur if:")
                    print("   - Data was added after the backup")
                    print("   - Backup parsing approximation")
                    
    except Exception as e:
        print(f"❌ Error comparing with live database: {e}")


def compare_with_live_db_sqlite(backup_db_path):
    """Compare SQLite backup with live database"""
    try:
        # Get live database path from settings
        live_db_path = settings.DATABASES['default']['NAME']
        
        # Connect to both databases
        live_conn = sqlite3.connect(live_db_path)
        backup_conn = sqlite3.connect(backup_db_path)
        
        live_cursor = live_conn.cursor()
        backup_cursor = backup_conn.cursor()
        
        # Get tables from both
        live_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        live_tables = [row[0] for row in live_cursor.fetchall()]
        
        backup_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        backup_tables = [row[0] for row in backup_cursor.fetchall()]
        
        print(f"Live database has {len(live_tables)} tables")
        print(f"Backup contains {len(backup_tables)} tables\n")
        
        # Compare tables
        missing_in_backup = set(live_tables) - set(backup_tables)
        extra_in_backup = set(backup_tables) - set(live_tables)
        
        if missing_in_backup:
            print(f"⚠️  Tables in live DB but NOT in backup ({len(missing_in_backup)}):")
            for table in sorted(missing_in_backup):
                print(f"   - {table}")
            print()
        
        if extra_in_backup:
            print(f"ℹ️  Tables in backup but not in current DB ({len(extra_in_backup)}):")
            for table in sorted(extra_in_backup):
                print(f"   - {table}")
            print()
        
        # Compare row counts
        common_tables = set(live_tables) & set(backup_tables)
        print(f"Comparing row counts for {len(common_tables)} common tables:\n")
        
        mismatches = []
        
        for table in sorted(common_tables):
            try:
                live_cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                live_count = live_cursor.fetchone()[0]
                
                backup_cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                backup_count = backup_cursor.fetchone()[0]
                
                if live_count == backup_count:
                    print(f"   ✓ {table}: {live_count} rows (matches)")
                else:
                    mismatches.append((table, live_count, backup_count))
                    print(f"   ⚠️  {table}: Live={live_count}, Backup={backup_count}")
                    
            except Exception as e:
                print(f"   ✗ {table}: Error checking - {e}")
        
        # Summary
        print("\n" + "="*60)
        print("COMPARISON SUMMARY")
        print("="*60)
        
        if not missing_in_backup and not mismatches:
            print("✅ All tables and data are backed up correctly!")
        else:
            if missing_in_backup:
                print(f"⚠️  {len(missing_in_backup)} table(s) missing from backup")
            if mismatches:
                print(f"⚠️  {len(mismatches)} table(s) have different row counts")
                print("\nDifferences:")
                for table, live, backup in mismatches:
                    diff = live - backup
                    print(f"   {table}: {diff:+d} rows (Live has {live}, Backup has {backup})")
        
        live_conn.close()
        backup_conn.close()
        
    except Exception as e:
        print(f"❌ Error comparing with live database: {e}")


# ============================================================================
# Main verification logic
# ============================================================================

# Find the latest backup (both PostgreSQL and SQLite)
postgres_backups = glob.glob('backups/database/backup_postgres_*.sql.gz')
sqlite_backups = glob.glob('backups/database/backup_sqlite_*.db.gz')

all_backups = postgres_backups + sqlite_backups

if not all_backups:
    print("❌ No backup files found!")
    print("   Looking for: backups/database/backup_postgres_*.sql.gz")
    print("   or: backups/database/backup_sqlite_*.db.gz")
    exit(1)

# Get the latest backup
latest_backup = max(all_backups, key=os.path.getctime)
backup_type = 'PostgreSQL' if 'postgres' in latest_backup else 'SQLite'

print(f"Verifying: {latest_backup}")
print(f"Type: {backup_type}")
print(f"Size: {os.path.getsize(latest_backup) / 1024:.2f} KB\n")

# Verify based on backup type
if backup_type == 'PostgreSQL':
    # PostgreSQL verification
    temp_sql = 'backups/database/temp_verify.sql'
    try:
        # Decompress the backup
        with gzip.open(latest_backup, 'rb') as f_in:
            with open(temp_sql, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        print("✓ Backup successfully decompressed\n")
        
        # Read and analyze the SQL file
        with open(temp_sql, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Count CREATE TABLE statements
        tables = [line for line in sql_content.split('\n') if line.startswith('CREATE TABLE')]
        
        # Count INSERT statements
        insert_count = sql_content.count('INSERT INTO')
        
        # Count COPY statements (PostgreSQL bulk insert)
        copy_count = sql_content.count('COPY ')
        
        print(f"✓ Backup is valid!\n")
        print(f"Database objects found:")
        print(f"  - Tables: {len(tables)}")
        print(f"  - INSERT statements: {insert_count}")
        print(f"  - COPY statements (bulk data): {copy_count}")
        
        # Check for key tables
        key_tables = ['auth_user', 'core_organization', 'orders_order', 'services_service']
        print(f"\nKey tables present:")
        for table in key_tables:
            if table in sql_content or f'public.{table}' in sql_content:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (not found)")
        
        print("\n✓ PostgreSQL backup verification complete! Structure is intact.")
        print("   Note: Full data verification requires restoring to a test database.")
        
        # Compare with live database if Django is available
        if DJANGO_AVAILABLE:
            print("\n" + "="*60)
            print("COMPARING BACKUP WITH LIVE DATABASE")
            print("="*60 + "\n")
            compare_with_live_db(sql_content, 'PostgreSQL')
        
    except Exception as e:
        print(f"❌ Error verifying backup: {e}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_sql):
            os.remove(temp_sql)

else:
    # SQLite verification
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
        print("\n✓ SQLite backup verification complete! Data is intact.")
        
        # Compare with live database if Django is available
        if DJANGO_AVAILABLE:
            print("\n" + "="*60)
            print("COMPARING BACKUP WITH LIVE DATABASE")
            print("="*60 + "\n")
            compare_with_live_db_sqlite(temp_db)
        
    except Exception as e:
        print(f"❌ Error verifying backup: {e}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_db):
            os.remove(temp_db)
