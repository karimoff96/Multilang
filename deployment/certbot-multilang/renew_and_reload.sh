#!/usr/bin/env bash
set -euo pipefail

LOG=${LOG:-/var/log/multilang_cert_renew.log}
PROJECT_DIR=${PROJECT_DIR:-/home/Wow-dash}
PYTHON_BIN=${PYTHON_BIN:-$PROJECT_DIR/venv/bin/python}
MANAGE_PY=${MANAGE_PY:-$PROJECT_DIR/manage.py}
CERT_NAME=${CERT_NAME:-multilang.uz-0001}
EMAIL=${EMAIL:-admin@multilang.uz}
RENEW_WINDOW_DAYS=${RENEW_WINDOW_DAYS:-30}
MAX_CERT_DOMAINS=${MAX_CERT_DOMAINS:-95}
NGINX_RELOAD_CMD=${NGINX_RELOAD_CMD:-systemctl reload nginx}
LOCK_FILE=${LOCK_FILE:-/var/lock/multilang_cert_renew.lock}
DRY_RUN=${DRY_RUN:-0}

if [ -z "${CERTBOT_BIN:-}" ]; then
  if [ -x /usr/local/bin/certbot ]; then
    CERTBOT_BIN=/usr/local/bin/certbot
  else
    CERTBOT_BIN=/usr/bin/certbot
  fi
fi

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1

log() {
  echo "[$(date -Iseconds)] $*"
}

run_cmd() {
  log "+ $*"
  if [ "$DRY_RUN" = "1" ]; then
    return 0
  fi
  "$@"
}

run_shell() {
  log "+ $*"
  if [ "$DRY_RUN" = "1" ]; then
    return 0
  fi
  bash -c "$*"
}

load_domain_list() {
  cd "$PROJECT_DIR"
  SENTRY_DSN= "$PYTHON_BIN" "$MANAGE_PY" shell -c '
import re
from django.conf import settings
from organizations.models import TranslationCenter

main_domain = getattr(settings, "MAIN_DOMAIN", "multilang.uz").strip(".")
ignored = {"www", "api", "static", "media"}
valid_subdomain = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")

domains = [main_domain, f"admin.{main_domain}"]
subdomains = (
    TranslationCenter.objects
    .filter(is_active=True)
    .exclude(subdomain__isnull=True)
    .exclude(subdomain="")
    .values_list("subdomain", flat=True)
    .order_by("subdomain")
)

for subdomain in subdomains:
    subdomain = (subdomain or "").strip().lower()
    if subdomain in ignored or not valid_subdomain.match(subdomain):
        continue
    domains.append(f"{subdomain}.{main_domain}")

print("\n".join(dict.fromkeys(domains)))
'
}

cert_has_domain() {
  local domain=$1
  local cert_path=$2
  openssl x509 -in "$cert_path" -noout -ext subjectAltName \
    | tr "," "\n" \
    | sed "s/^[[:space:]]*//" \
    | grep -Fxq "DNS:$domain"
}

log "--- Starting MultiLang certificate renewal ---"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  log "Another renewal process is already running; exiting."
  exit 0
fi

if [ ! -x "$CERTBOT_BIN" ]; then
  log "ERROR: certbot not found at $CERTBOT_BIN"
  exit 1
fi

if [ ! -x "$PYTHON_BIN" ] || [ ! -f "$MANAGE_PY" ]; then
  log "ERROR: Django project paths are invalid: PYTHON_BIN=$PYTHON_BIN MANAGE_PY=$MANAGE_PY"
  exit 1
fi

DOMAIN_LIST=$(load_domain_list)
if [ -z "$DOMAIN_LIST" ]; then
  log "ERROR: could not build domain list from active centers"
  exit 1
fi

DOMAINS=()
while IFS= read -r domain; do
  [ -n "$domain" ] && DOMAINS+=("$domain")
done <<< "$DOMAIN_LIST"

log "Desired certificate domains (${#DOMAINS[@]}): ${DOMAINS[*]}"

if [ "${#DOMAINS[@]}" -gt "$MAX_CERT_DOMAINS" ]; then
  log "ERROR: ${#DOMAINS[@]} domains exceeds MAX_CERT_DOMAINS=$MAX_CERT_DOMAINS. Use a DNS-01 wildcard certificate before adding more centers."
  exit 1
fi

CERT_PATH="/etc/letsencrypt/live/$CERT_NAME/fullchain.pem"
RENEW_WINDOW_SECONDS=$((RENEW_WINDOW_DAYS * 86400))
missing_domain=0
expiring=0

if [ ! -f "$CERT_PATH" ]; then
  log "Certificate file is missing: $CERT_PATH"
  missing_domain=1
else
  for domain in "${DOMAINS[@]}"; do
    if ! cert_has_domain "$domain" "$CERT_PATH"; then
      log "Certificate is missing domain: $domain"
      missing_domain=1
    fi
  done

  if ! openssl x509 -checkend "$RENEW_WINDOW_SECONDS" -noout -in "$CERT_PATH" >/dev/null 2>&1; then
    log "Certificate expires within $RENEW_WINDOW_DAYS days."
    expiring=1
  fi
fi

CERTBOT_DOMAIN_ARGS=()
for domain in "${DOMAINS[@]}"; do
  CERTBOT_DOMAIN_ARGS+=("-d" "$domain")
done

if [ "$missing_domain" = "1" ] || [ "$expiring" = "1" ]; then
  CERTBOT_ARGS=(
    certonly
    --cert-name "$CERT_NAME"
    --non-interactive
    --agree-tos
    --email "$EMAIL"
    --authenticator nginx
    "${CERTBOT_DOMAIN_ARGS[@]}"
  )

  if [ "$missing_domain" = "1" ]; then
    CERTBOT_ARGS+=(--expand)
  fi
  if [ "$expiring" = "1" ]; then
    CERTBOT_ARGS+=(--force-renewal)
  fi

  run_cmd "$CERTBOT_BIN" "${CERTBOT_ARGS[@]}"
  run_cmd nginx -t
  run_shell "$NGINX_RELOAD_CMD"
else
  # Keep this scoped to the certificate nginx actually serves. The old
  # multilang.uz manual-DNS lineage is retained by certbot but is not used here.
  run_cmd "$CERTBOT_BIN" renew --cert-name "$CERT_NAME" --deploy-hook "$NGINX_RELOAD_CMD" --quiet
fi

log "--- Completed MultiLang certificate renewal ---"
