#!/bin/bash
# -----------------------------------------------------------------------------
# Media files backup for Wow-dash
# Uses rsync to an incremental snapshot — much smaller than a full tarball.
# Keeps last 2 snapshots. Run via cron weekly (Sunday 3:30 AM).
# -----------------------------------------------------------------------------

set -euo pipefail

MEDIA_SRC="/home/Wow-dash/media/"
BACKUP_ROOT="/home/Wow-dash/backups/media"
LOG="/var/log/wowdash/backup.log"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
SNAPSHOT_DIR="$BACKUP_ROOT/snapshot_$TIMESTAMP"
LATEST_LINK="$BACKUP_ROOT/latest"
KEEP=2

mkdir -p "$BACKUP_ROOT"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting media backup → $SNAPSHOT_DIR" | tee -a "$LOG"

# Incremental rsync: hard-links unchanged files from the previous snapshot,
# so each new snapshot only uses space for what actually changed.
if [ -L "$LATEST_LINK" ] && [ -d "$LATEST_LINK" ]; then
    rsync -a --delete --link-dest="$LATEST_LINK" "$MEDIA_SRC" "$SNAPSHOT_DIR/"
else
    rsync -a "$MEDIA_SRC" "$SNAPSHOT_DIR/"
fi

# Update the 'latest' symlink
ln -sfn "$SNAPSHOT_DIR" "$LATEST_LINK"

SNAP_SIZE=$(du -sh "$SNAPSHOT_DIR" | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Media backup done. Size: $SNAP_SIZE" | tee -a "$LOG"

# Rotate: keep only the $KEEP most recent snapshots
SNAPSHOTS=($(ls -dt "$BACKUP_ROOT"/snapshot_* 2>/dev/null))
COUNT=${#SNAPSHOTS[@]}
if [ "$COUNT" -gt "$KEEP" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Rotating old media snapshots (keeping $KEEP)..." | tee -a "$LOG"
    for OLD in "${SNAPSHOTS[@]:$KEEP}"; do
        rm -rf "$OLD"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')]   Removed: $(basename $OLD)" | tee -a "$LOG"
    done
fi

# Report free disk space
FREE=$(df -h / | awk 'NR==2{print $4" free ("$5" used)"}')
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Disk: $FREE" | tee -a "$LOG"
