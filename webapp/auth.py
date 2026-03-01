"""
Telegram WebApp initData validation utilities.

Reference: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
import hmac
import hashlib
import json
import time
from urllib.parse import parse_qsl


def validate_telegram_init_data(init_data: str, bot_token: str) -> dict | None:
    """
    Validate Telegram WebApp initData string against the bot token.

    Returns the parsed `user` dict from initData on success, or None on failure.

    Steps per Telegram docs:
      1. Parse initData query string, extract `hash` field.
      2. Build check_string: remaining fields sorted alphabetically, joined with '\n'.
      3. secret_key = HMAC-SHA256(key=b'WebAppData', msg=bot_token)
      4. computed_hash = HMAC-SHA256(key=secret_key, msg=check_string)
      5. Compare computed_hash with received hash (constant-time).
    """
    try:
        # Use keep_blank_values=True and strict_parsing=False so real
        # Telegram initData (which can have encoded chars) parses safely
        parsed = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None

        # Reject data older than 24 hours to prevent replay attacks
        auth_date = parsed.get("auth_date")
        if auth_date:
            try:
                if time.time() - int(auth_date) > 86400:
                    return None
            except (ValueError, TypeError):
                pass

        check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

        secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
        computed_hash = hmac.new(
            secret_key, check_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            return None

        user_json = parsed.get("user", "{}")
        return json.loads(user_json)

    except Exception:
        return None


def get_validated_telegram_user(init_data: str, center):
    """
    Validate initData against *center*'s bot token.

    Returns (telegram_user_id: int, user_dict: dict) on success,
    or (None, None) on failure.

    `center` must be a TranslationCenter instance with a non-empty `bot_token`.
    """
    if not center or not center.bot_token:
        return None, None

    user_dict = validate_telegram_init_data(init_data, center.bot_token)
    if user_dict is None:
        return None, None

    tg_id = user_dict.get("id")
    if not tg_id:
        return None, None

    return int(tg_id), user_dict
