#!/usr/bin/env bash
set -euo pipefail

LOG=/var/log/multilang_cert_renew.log
CERTBOT_BIN=${CERTBOT_BIN:-/usr/bin/certbot}
NGINX_RELOAD_CMD=${NGINX_RELOAD_CMD:-systemctl reload nginx}

{
  echo "--- $(date -Iseconds) Starting cert renewal ---"
  if [ ! -x "$CERTBOT_BIN" ]; then
    echo "ERROR: certbot not found at $CERTBOT_BIN" >&2
    exit 1
  fi

  # Use --deploy-hook to reload nginx only when a cert is renewed
  $CERTBOT_BIN renew --deploy-hook "$NGINX_RELOAD_CMD" --quiet
  rc=$?
  echo "--- $(date -Iseconds) certbot exit code: $rc ---"
  if [ $rc -ne 0 ]; then
    echo "certbot renew failed with exit code $rc" >&2
    exit $rc
  fi
  echo "--- $(date -Iseconds) Completed cert renewal ---"
} >>"$LOG" 2>&1
