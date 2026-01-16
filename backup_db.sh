#!/bin/bash

###############################################################################
# Database Backup Script for WowDash
# 
# This script performs automated database backups using Django's management
# command. It's designed to be run via cron for periodic backups.
#
# Setup:
#   1. Make executable: chmod +x backup_db.sh
#   2. Add to crontab: crontab -e
#   3. Add line: 0 2 * * * /path/to/WowDash/backup_db.sh >> /var/log/wowdash_backup.log 2>&1
#
# The above cron example runs daily at 2:00 AM
###############################################################################

# Configuration
PROJECT_DIR="/path/to/WowDash"  # CHANGE THIS to your actual project path
PYTHON_ENV="$PROJECT_DIR/venv/bin/python"  # Path to Python in virtualenv
MANAGE_PY="$PROJECT_DIR/manage.py"
KEEP_BACKUPS=30  # Number of backups to keep

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if we're in the correct directory
if [ ! -f "$MANAGE_PY" ]; then
    log "${RED}ERROR: manage.py not found at $MANAGE_PY${NC}"
    log "Please update PROJECT_DIR in this script"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Check if virtual environment exists
if [ ! -f "$PYTHON_ENV" ]; then
    log "${YELLOW}WARNING: Virtual environment not found at $PYTHON_ENV${NC}"
    log "Attempting to use system Python..."
    PYTHON_ENV="python3"
fi

# Start backup
log "${GREEN}========================================${NC}"
log "${GREEN}Starting Database Backup${NC}"
log "${GREEN}========================================${NC}"

# Run the backup command
$PYTHON_ENV "$MANAGE_PY" backup_db --keep "$KEEP_BACKUPS"

# Check if backup was successful
if [ $? -eq 0 ]; then
    log "${GREEN}✓ Backup completed successfully!${NC}"
    exit 0
else
    log "${RED}✗ Backup failed!${NC}"
    exit 1
fi
