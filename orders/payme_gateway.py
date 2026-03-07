"""
Payme checkout URL builder and helper utilities.
This module does not make network calls; it only prepares data for the bot/webapp.
"""
import base64
import json
import logging
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

from django.conf import settings

logger = logging.getLogger(__name__)


class PaymeIntegrationError(Exception):
    """Raised when Payme configuration or payload is invalid."""


def _to_tiyin(amount):
    """Convert decimal amount (sum) to tiyin (int)."""
    try:
        dec = Decimal(str(amount)).quantize(Decimal("0.01"))
        return int(dec * 100)
    except (InvalidOperation, ValueError) as exc:
        raise PaymeIntegrationError(f"Invalid amount: {amount}") from exc


def _get_lang(language):
    return language if language in ("uz", "ru", "en") else "uz"


def _build_detail(order, language):
    """Build optional detail payload for Payme receipt display."""
    lang = _get_lang(language)

    def _name(obj):
        if lang == "ru":
            return getattr(obj, "name_ru", None) or getattr(obj, "name", "")
        if lang == "en":
            return getattr(obj, "name_en", None) or getattr(obj, "name", "")
        return getattr(obj, "name_uz", None) or getattr(obj, "name", "")

    items = []
    title = _name(order.product)
    price_tiyin = _to_tiyin(order.total_price)
    items.append(
        {
            "title": title or f"Order #{order.get_order_number()}",
            "price": price_tiyin,
            "count": 1,
        }
    )

    detail = {
        "receipt_type": 0,
        "items": items,
    }
    return base64.b64encode(json.dumps(detail, ensure_ascii=False).encode()).decode()


def build_payme_checkout_url(order, language="uz", callback_url=None, center=None):
    """
    Build Payme checkout URL for the given order.

    If *center* is supplied and has a non-empty ``payme_merchant_id``, that
    value is used instead of the global ``PAYME_MERCHANT_ID`` setting.

    Raises PaymeIntegrationError if required config is missing.
    """
    # Resolve merchant_id: per-center override takes priority
    merchant_id = (
        (center.payme_merchant_id.strip() if center and center.payme_merchant_id else None)
        or settings.PAYME_MERCHANT_ID
    )
    if not merchant_id:
        raise PaymeIntegrationError("PAYME_MERCHANT_ID is not configured")

    amount_tiyin = _to_tiyin(order.total_due)
    lang = _get_lang(language)

    params = [
        f"m={merchant_id}",
        f"ac.order_id={order.id}",
        f"a={amount_tiyin}",
        f"lang={lang}",
    ]

    detail_encoded = _build_detail(order, lang)
    params.append(f"detail={detail_encoded}")

    cb = callback_url or settings.PAYME_RETURN_URL or ""
    if cb:
        params.append(f"callback={quote(cb, safe=':/')}")

    token = base64.b64encode(";".join(params).encode()).decode()
    # Payme checkout uses checkout.paycom.uz for hosted page; sandbox/test relies on merchant/test credentials
    base_url = "https://checkout.paycom.uz"
    checkout_url = f"{base_url}/{token}"
    logger.info("Generated Payme checkout URL for order %s", order.id)
    return checkout_url, amount_tiyin, detail_encoded