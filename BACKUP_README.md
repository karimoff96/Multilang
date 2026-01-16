# Database Backup System

This project includes an automated database backup system that supports both PostgreSQL and SQLite databases.

## Features

- ✅ Automatic compression of backups (gzip)
- ✅ Automatic rotation of old backups
- ✅ Support for both PostgreSQL and SQLite
- ✅ Configurable retention period
- ✅ Cron-ready for scheduled backups
- ✅ Detailed logging

## Manual Backup

To manually create a backup:

```bash
# Basic backup (keeps last 30 backups by default)
python manage.py backup_db

# Keep only last 7 backups
python manage.py backup_db --keep 7

# Specify custom backup directory
python manage.py backup_db --backup-dir /custom/path/backups
```

Backups are stored in `backups/database/` directory by default.

## Automated Backups with Cron

### Step 1: Configure the backup script

Edit `backup_db.sh` and update the `PROJECT_DIR` variable:

```bash
PROJECT_DIR="/path/to/WowDash"  # Change this to your actual project path
```

### Step 2: Make the script executable

```bash
chmod +x backup_db.sh
```

### Step 3: Set up cron job

Open your crontab:

```bash
crontab -e
```

Add one of the following lines based on your backup schedule:

```bash
# Daily backup at 2:00 AM
0 2 * * * /path/to/WowDash/backup_db.sh >> /var/log/wowdash_backup.log 2>&1

# Every 12 hours (at midnight and noon)
0 0,12 * * * /path/to/WowDash/backup_db.sh >> /var/log/wowdash_backup.log 2>&1

# Every 6 hours
0 */6 * * * /path/to/WowDash/backup_db.sh >> /var/log/wowdash_backup.log 2>&1

# Weekly backup (every Sunday at 3:00 AM)
0 3 * * 0 /path/to/WowDash/backup_db.sh >> /var/log/wowdash_backup.log 2>&1
```

### Step 4: Create log directory (optional)

```bash
sudo mkdir -p /var/log
sudo touch /var/log/wowdash_backup.log
sudo chown $USER:$USER /var/log/wowdash_backup.log
```

## Cron Schedule Format

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, 0 and 7 are Sunday)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

## PostgreSQL Requirements

For PostgreSQL backups, ensure `pg_dump` is installed and accessible:

```bash
# Ubuntu/Debian
sudo apt-get install postgresql-client

# CentOS/RHEL
sudo yum install postgresql
```

## Backup Location

Backups are stored in:
- Default: `WowDash/backups/database/`
- Custom: Specified with `--backup-dir` option

## Backup Files

- PostgreSQL: `backup_postgres_YYYYMMDD_HHMMSS.sql.gz`
- SQLite: `backup_sqlite_YYYYMMDD_HHMMSS.db.gz`

## Restoring Backups

### SQLite

```bash
# Decompress backup
gunzip backups/database/backup_sqlite_20260116_020000.db.gz

# Stop the application first, then:
cp backups/database/backup_sqlite_20260116_020000.db db.sqlite3
```

### PostgreSQL

```bash
# Decompress backup
gunzip backups/database/backup_postgres_20260116_020000.sql.gz

# Restore to database
psql -h localhost -U your_user -d your_database < backups/database/backup_postgres_20260116_020000.sql
```

## Monitoring Backups

Check the cron log to monitor backup status:

```bash
tail -f /var/log/wowdash_backup.log
```

Check existing backups:

```bash
ls -lh backups/database/
```

## Troubleshooting

### Cron job not running

1. Check if cron service is running:
   ```bash
   sudo systemctl status cron
   ```

2. Check cron logs:
   ```bash
   grep CRON /var/log/syslog
   ```

3. Verify script permissions:
   ```bash
   ls -l backup_db.sh
   ```

### Permission issues

Make sure the user running the cron job has:
- Read access to the database file (SQLite)
- Write access to the backup directory
- Execute permissions on the backup script

### PostgreSQL connection issues

Ensure your `.env` file has correct database credentials:
```
USE_POSTGRES=True
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

## Security Recommendations

1. **Restrict backup directory permissions:**
   ```bash
   chmod 700 backups/database/
   ```

2. **Consider encrypting backups** for sensitive data

3. **Store backups off-site** for disaster recovery

4. **Test restoration regularly** to ensure backups are valid

5. **Monitor disk space** to prevent backup failures due to full disk
