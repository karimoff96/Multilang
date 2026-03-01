#!/usr/bin/env python3
"""
SSL certificate expiry checker.
Sends a Telegram notification via the admin bot if cert expires within 30 days.
Run daily via cron:
  0 9 * * * /home/Wow-dash/venv/bin/python /home/Wow-dash/scripts/check_ssl_expiry.py
"""

import ssl
import socket
import datetime
import os
import sys
import requests

DOMAIN = "multilang.uz"
WARN_DAYS = 30
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")
ADMIN_CHAT_IDS_STR = os.getenv("ADMIN_TELEGRAM_IDS") or os.getenv("ADMIN_TELEGRAM_ID", "")


def get_cert_expiry(domain: str, port: int = 443) -> datetime.datetime:
    ctx = ssl.create_default_context()
    with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
        s.settimeout(10)
        s.connect((domain, port))
        cert = s.getpeercert()
    expiry_str = cert["notAfter"]  # e.g. 'May 30 16:06:33 2026 GMT'
    return datetime.datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z").replace(
        tzinfo=datetime.timezone.utc
    )


def send_telegram(token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)


def main():
    try:
        expiry = get_cert_expiry(DOMAIN)
    except Exception as e:
        print(f"ERROR checking cert: {e}", file=sys.stderr)
        sys.exit(1)

    now = datetime.datetime.now(datetime.timezone.utc)
    days_left = (expiry - now).days
    expiry_str = expiry.strftime("%Y-%m-%d")

    print(f"SSL cert for {DOMAIN}: expires {expiry_str} ({days_left} days left)")

    if days_left <= WARN_DAYS:
        msg = (
            f"⚠️ <b>SSL Certificate Expiry Warning</b>\n\n"
            f"Domain: <code>{DOMAIN}</code>\n"
            f"Expires: <b>{expiry_str}</b> ({days_left} days left)\n\n"
            f"Run on the server:\n"
            f"<pre>sudo certbot certonly --manual --preferred-challenges dns "
            f"-d {DOMAIN} -d *.{DOMAIN}</pre>\n"
            f"Then: <pre>sudo systemctl reload nginx</pre>"
        )

        if not ADMIN_BOT_TOKEN:
            print("WARNING: ADMIN_BOT_TOKEN not set, cannot send Telegram notification")
            return

        sent = False
        for chat_id in ADMIN_CHAT_IDS_STR.split(","):
            chat_id = chat_id.strip()
            if chat_id:
                try:
                    send_telegram(ADMIN_BOT_TOKEN, chat_id, msg)
                    print(f"Notification sent to {chat_id}")
                    sent = True
                except Exception as e:
                    print(f"Failed to send to {chat_id}: {e}", file=sys.stderr)

        if not sent:
            print("WARNING: No chat IDs configured (ADMIN_TELEGRAM_IDS)")
    else:
        print(f"OK — more than {WARN_DAYS} days remaining, no action needed.")


if __name__ == "__main__":
    main()
