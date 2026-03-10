import json
import logging
import time
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order, PaymeTransaction
from bot.main import send_order_status_notification

logger = logging.getLogger(__name__)


PAYME_ERROR_INVALID_AMOUNT = -31001
PAYME_ERROR_CANNOT_PERFORM = -31008
PAYME_ERROR_INVALID_ACCOUNT = -31050
PAYME_ERROR_TRANSACTION_NOT_FOUND = -31003


def _rpc_error(code, message, rpc_id=None, data=None):
    return {
        "jsonrpc": "2.0",
        "id": rpc_id,
        "error": {
            "code": code,
            "message": message,
            "data": data,
        },
    }


def _rpc_result(result, rpc_id=None):
    return {"jsonrpc": "2.0", "id": rpc_id, "result": result}


def _now_ms():
    return int(time.time() * 1000)


def _validate_account(params):
    account = params.get("account") or {}
    order_id = account.get("order_id") or account.get("orderid") or account.get("order")
    if not order_id:
        raise ValueError("order_id missing")
    return int(order_id)


def _validate_amount(order, params):
    amount = params.get("amount")
    try:
        amount_int = int(amount)
    except Exception:
        raise ValueError("invalid amount")

    expected = int(Decimal(str(order.total_due)).quantize(Decimal("0.01")) * 100)
    if amount_int != expected:
        raise ValueError(f"amount mismatch: {amount_int} != {expected}")
    return amount_int


@method_decorator(csrf_exempt, name="dispatch")
class PaymeWebhookView(View):
    """Minimal Payme JSON-RPC handler."""

    http_method_names = ["post", "options"]

    def post(self, request, *args, **kwargs):
        # center_id baked into URL (per-center endpoint) takes priority;
        # fall back to request.center set by SubdomainMiddleware so that
        # {subdomain}.multilang.uz/payme/webhook/ also resolves correctly.
        url_center_id = kwargs.get("center_id")
        if not url_center_id:
            req_center = getattr(request, "center", None)
            if req_center is not None:
                url_center_id = req_center.pk

        rpc_id = None
        try:
            payload = json.loads(request.body.decode() or "{}")
            rpc_id = payload.get("id")
            method = payload.get("method")
            params = payload.get("params", {})
        except Exception as exc:
            logger.error("Payme: invalid JSON: %s", exc)
            return JsonResponse(_rpc_error(-32602, "Invalid params", rpc_id), status=200)

        # Auth check: Payme sends "Authorization: Basic base64('Paycom:{SECRET_KEY}')"
        # Must run BEFORE any method logic — Payme tests auth with empty/bad accounts.
        provided_auth = request.headers.get("Authorization", "")
        expected_key = self._resolve_secret_key(params, url_center_id)
        if not expected_key:
            # No key configured at all — deny to prevent unauthenticated access
            return JsonResponse(_rpc_error(-32504, "Unauthorized", rpc_id), status=200)
        if not self._check_auth(provided_auth, expected_key):
            return JsonResponse(_rpc_error(-32504, "Unauthorized", rpc_id), status=200)

        try:
            if method == "CheckPerformTransaction":
                return JsonResponse(self._check_perform(params, rpc_id), status=200)
            if method == "CreateTransaction":
                return JsonResponse(self._create_transaction(params, rpc_id), status=200)
            if method == "PerformTransaction":
                return JsonResponse(self._perform_transaction(params, rpc_id), status=200)
            if method == "CancelTransaction":
                return JsonResponse(self._cancel_transaction(params, rpc_id), status=200)
            if method == "CheckTransaction":
                return JsonResponse(self._check_transaction(params, rpc_id), status=200)
            if method == "GetStatement":
                return JsonResponse(self._get_statement(params, rpc_id), status=200)
            if method == "ChangePassword":
                return JsonResponse(self._change_password(params, rpc_id, url_center_id), status=200)

            return JsonResponse(_rpc_error(-32601, "Method not found", rpc_id), status=200)
        except Exception as exc:
            logger.error("Payme: unhandled error: %s", exc, exc_info=True)
            return JsonResponse(_rpc_error(-32603, "Internal error", rpc_id), status=200)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _check_auth(provided_auth: str, expected_key: str) -> bool:
        """
        Validate Payme's Authorization header.
        Payme sends: Authorization: Basic base64("Paycom:{SECRET_KEY}")
        """
        import base64 as _b64
        try:
            scheme, _, encoded = provided_auth.partition(" ")
            if scheme.lower() != "basic" or not encoded:
                return False
            decoded = _b64.b64decode(encoded.strip()).decode("utf-8", errors="replace")
            # decoded should be "Paycom:{SECRET_KEY}"
            return decoded == f"Paycom:{expected_key}"
        except Exception:
            return False

    @staticmethod
    def _resolve_secret_key(params, url_center_id=None):
        """
        Return the Payme secret key for this request.

        Priority:
        1. Center ID baked into the webhook URL  → direct DB lookup, always works
           (even for GetStatement / ChangePassword / bad-auth tests with empty account)
        2. order_id in params.account            → look up order → center key
        3. Global PAYME_SECRET_KEY setting       → fallback
        """
        def _key_for_center(c):
            """Return the active key based on sandbox mode."""
            if c.payme_sandbox:
                return c.payme_secret_key or None
            return c.payme_secret_key_prod or c.payme_secret_key or None

        # 1. Per-center URL: always resolvable regardless of params content
        if url_center_id:
            try:
                from organizations.models import TranslationCenter
                center = TranslationCenter.objects.get(pk=url_center_id)
                key = _key_for_center(center)
                if key:
                    return key
            except Exception:
                pass

        # 2. Resolve from order in params (shared URL fallback)
        try:
            order_id = _validate_account(params)
            order = Order.objects.select_related("branch__center").get(pk=order_id)
            center = order.branch.center if (order.branch and order.branch.center) else None
            if center:
                key = _key_for_center(center)
                if key:
                    return key
        except Exception:
            pass

        # 3. Global fallback
        return settings.PAYME_SECRET_KEY or None

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------
    def _check_perform(self, params, rpc_id):
        try:
            order_id = _validate_account(params)
            order = Order.objects.get(pk=order_id)
        except Exception:
            return _rpc_error(PAYME_ERROR_INVALID_ACCOUNT, "Invalid account", rpc_id)

        try:
            _validate_amount(order, params)
        except Exception:
            return _rpc_error(PAYME_ERROR_INVALID_AMOUNT, "Invalid amount", rpc_id)

        return _rpc_result({"allow": True}, rpc_id)

    @transaction.atomic
    def _create_transaction(self, params, rpc_id):
        try:
            order_id = _validate_account(params)
            order = Order.objects.select_for_update().get(pk=order_id)
        except Exception:
            return _rpc_error(PAYME_ERROR_INVALID_ACCOUNT, "Invalid account", rpc_id)

        try:
            amount_tiyin = _validate_amount(order, params)
        except Exception:
            return _rpc_error(PAYME_ERROR_INVALID_AMOUNT, "Invalid amount", rpc_id)

        if order.is_fully_paid or order.status in ["payment_confirmed", "completed", "ready"]:
            return _rpc_error(PAYME_ERROR_CANNOT_PERFORM, "Operation cannot be performed", rpc_id)

        payme_id = params.get("id")
        if not payme_id:
            return _rpc_error(PAYME_ERROR_INVALID_ACCOUNT, "Missing transaction id", rpc_id)

        tx, created = PaymeTransaction.objects.select_for_update().get_or_create(
            payme_transaction_id=payme_id,
            defaults={
                "order": order,
                "amount_tiyin": amount_tiyin,
                "account": params.get("account") or {},
                "state": PaymeTransaction.STATE_CREATED,
                "create_time_ms": _now_ms(),
                "raw_request": params,
            },
        )

        if not created:
            # Validate same order/amount
            if tx.order_id != order.id or tx.amount_tiyin != amount_tiyin:
                return _rpc_error(PAYME_ERROR_CANNOT_PERFORM, "Operation cannot be performed", rpc_id)
        else:
            # Mark order as awaiting payment
            order.payment_type = "card"
            order.status = "payment_pending"
            order.is_active = True
            order.save(update_fields=["payment_type", "status", "is_active", "updated_at"])

        result = {
            "create_time": tx.create_time_ms,
            "transaction": tx.payme_transaction_id,
            "state": PaymeTransaction.STATE_CREATED,
        }
        return _rpc_result(result, rpc_id)

    @transaction.atomic
    def _perform_transaction(self, params, rpc_id):
        payme_id = params.get("id")
        if not payme_id:
            return _rpc_error(PAYME_ERROR_TRANSACTION_NOT_FOUND, "Transaction not found", rpc_id)

        try:
            tx = PaymeTransaction.objects.select_for_update().get(payme_transaction_id=payme_id)
            order = Order.objects.select_for_update().get(pk=tx.order_id)
        except PaymeTransaction.DoesNotExist:
            return _rpc_error(PAYME_ERROR_TRANSACTION_NOT_FOUND, "Transaction not found", rpc_id)
        except Order.DoesNotExist:
            return _rpc_error(PAYME_ERROR_INVALID_ACCOUNT, "Invalid account", rpc_id)

        if tx.state == PaymeTransaction.STATE_PERFORMED:
            return _rpc_result(
                {
                    "transaction": tx.payme_transaction_id,
                    "perform_time": tx.perform_time_ms,
                    "state": PaymeTransaction.STATE_PERFORMED,
                },
                rpc_id,
            )

        if order.status == "cancelled":
            return _rpc_error(PAYME_ERROR_CANNOT_PERFORM, "Operation cannot be performed", rpc_id)

        # Confirm payment
        now_ms = _now_ms()
        tx.state = PaymeTransaction.STATE_PERFORMED
        tx.perform_time_ms = now_ms
        tx.save(update_fields=["state", "perform_time_ms", "updated_at"])

        # Mark order paid
        order.payment_type = "card"
        order.payment_accepted_fully = True
        order.received = order.total_due
        order.status = "payment_confirmed"
        order.is_active = True
        order.save(update_fields=["payment_type", "payment_accepted_fully", "received", "status", "is_active", "updated_at"])

        # Notify about status change
        try:
            send_order_status_notification(order, order._old_status if hasattr(order, "_old_status") else "payment_pending", "payment_confirmed")
        except Exception as notify_exc:
            logger.warning("Payme notify failed: %s", notify_exc)

        result = {
            "transaction": tx.payme_transaction_id,
            "perform_time": now_ms,
            "state": PaymeTransaction.STATE_PERFORMED,
        }
        return _rpc_result(result, rpc_id)

    @transaction.atomic
    def _cancel_transaction(self, params, rpc_id):
        payme_id = params.get("id")
        if not payme_id:
            return _rpc_error(PAYME_ERROR_TRANSACTION_NOT_FOUND, "Transaction not found", rpc_id)

        try:
            tx = PaymeTransaction.objects.select_for_update().get(payme_transaction_id=payme_id)
            order = Order.objects.select_for_update().get(pk=tx.order_id)
        except PaymeTransaction.DoesNotExist:
            return _rpc_error(PAYME_ERROR_TRANSACTION_NOT_FOUND, "Transaction not found", rpc_id)
        except Order.DoesNotExist:
            return _rpc_error(PAYME_ERROR_INVALID_ACCOUNT, "Invalid account", rpc_id)

        now_ms = _now_ms()
        reason = params.get("reason")

        # If already cancelled, return current state
        if tx.state in (PaymeTransaction.STATE_CANCELLED, PaymeTransaction.STATE_CANCELLED_AFTER_PERFORM):
            return _rpc_result(
                {
                    "transaction": tx.payme_transaction_id,
                    "cancel_time": tx.cancel_time_ms,
                    "state": tx.state,
                },
                rpc_id,
            )

        if tx.state == PaymeTransaction.STATE_PERFORMED:
            tx.state = PaymeTransaction.STATE_CANCELLED_AFTER_PERFORM
        else:
            tx.state = PaymeTransaction.STATE_CANCELLED

        tx.cancel_time_ms = now_ms
        tx.cancel_reason = reason
        tx.save(update_fields=["state", "cancel_time_ms", "cancel_reason", "updated_at"])

        order.status = "cancelled"
        order.save(update_fields=["status", "updated_at"])

        try:
            send_order_status_notification(order, order._old_status if hasattr(order, "_old_status") else "payment_pending", "cancelled")
        except Exception as notify_exc:
            logger.warning("Payme cancel notify failed: %s", notify_exc)

        return _rpc_result(
            {
                "transaction": tx.payme_transaction_id,
                "cancel_time": now_ms,
                "state": tx.state,
            },
            rpc_id,
        )

    def _check_transaction(self, params, rpc_id):
        payme_id = params.get("id")
        if not payme_id:
            return _rpc_error(PAYME_ERROR_TRANSACTION_NOT_FOUND, "Transaction not found", rpc_id)

        try:
            tx = PaymeTransaction.objects.get(payme_transaction_id=payme_id)
        except PaymeTransaction.DoesNotExist:
            return _rpc_error(PAYME_ERROR_TRANSACTION_NOT_FOUND, "Transaction not found", rpc_id)

        result = {
            "create_time": tx.create_time_ms or 0,
            "perform_time": tx.perform_time_ms or 0,
            "cancel_time": tx.cancel_time_ms or 0,
            "transaction": tx.payme_transaction_id,
            "state": tx.state,
            "reason": tx.cancel_reason,
        }
        return _rpc_result(result, rpc_id)

    def _get_statement(self, params, rpc_id):
        from_ts = params.get("from")
        to_ts = params.get("to")
        try:
            from_ts = int(from_ts)
            to_ts = int(to_ts)
        except Exception:
            return _rpc_error(PAYME_ERROR_INVALID_ACCOUNT, "Invalid timeframe", rpc_id)

        txs = PaymeTransaction.objects.filter(create_time_ms__gte=from_ts, create_time_ms__lte=to_ts).order_by("create_time_ms")
        data = []
        for tx in txs:
            data.append(
                {
                    "id": tx.payme_transaction_id,
                    "time": tx.create_time_ms or 0,
                    "amount": tx.amount_tiyin,
                    "account": tx.account,
                    "create_time": tx.create_time_ms or 0,
                    "perform_time": tx.perform_time_ms or 0,
                    "cancel_time": tx.cancel_time_ms or 0,
                    "transaction": tx.payme_transaction_id,
                    "state": tx.state,
                    "reason": tx.cancel_reason,
                }
            )

        return _rpc_result({"transactions": data}, rpc_id)

    def _change_password(self, params, rpc_id, url_center_id=None):
        """
        Payme may rotate the secret key at any time by calling ChangePassword.
        Save the new password to the center's payme_secret_key so subsequent
        requests continue to authenticate correctly.
        """
        new_password = (params.get("password") or "").strip()
        if not new_password:
            return _rpc_error(-32602, "Invalid params", rpc_id)

        saved = False
        if url_center_id:
            try:
                from organizations.models import TranslationCenter
                center = TranslationCenter.objects.get(pk=url_center_id)
                # Save into the currently-active key field
                if center.payme_sandbox:
                    center.payme_secret_key = new_password
                    center.save(update_fields=["payme_secret_key", "updated_at"])
                else:
                    center.payme_secret_key_prod = new_password
                    center.save(update_fields=["payme_secret_key_prod", "updated_at"])
                saved = True
                logger.info(
                    "Payme: ChangePassword saved for center %s (sandbox=%s)",
                    url_center_id, center.payme_sandbox,
                )
            except Exception as exc:
                logger.error("Payme: ChangePassword DB update failed: %s", exc)

        if not saved:
            # Shared URL fallback: update global setting is not possible at runtime,
            # log the new key so an admin can update .env manually.
            logger.warning(
                "Payme: ChangePassword received but no center resolved — "
                "update PAYME_SECRET_KEY in .env manually. new_key_preview=%s...",
                new_password[:6],
            )

        return _rpc_result({}, rpc_id)


payme_webhook_view = PaymeWebhookView.as_view()
