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
        rpc_id = None
        try:
            payload = json.loads(request.body.decode() or "{}")
            rpc_id = payload.get("id")
            method = payload.get("method")
            params = payload.get("params", {})
        except Exception as exc:
            logger.error("Payme: invalid JSON: %s", exc)
            return JsonResponse(_rpc_error(-32602, "Invalid params", rpc_id), status=200)

        # Auth check: look up per-center secret key when possible, fall back to global
        provided_auth = request.headers.get("Authorization", "")
        expected = self._resolve_secret_key(params)
        if expected and expected not in provided_auth:
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

            return JsonResponse(_rpc_error(-32601, "Method not found", rpc_id), status=200)
        except Exception as exc:
            logger.error("Payme: unhandled error: %s", exc, exc_info=True)
            return JsonResponse(_rpc_error(-32603, "Internal error", rpc_id), status=200)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_secret_key(params):
        """
        Return the Payme secret key to validate the incoming request.

        Tries to look up the order in the params and return its center's
        per-center secret key.  Falls back to the global PAYME_SECRET_KEY
        if the center has no per-center key configured.
        """
        try:
            from organizations.models import TranslationCenter
            order_id = _validate_account(params)
            order = Order.objects.select_related("branch__center").get(pk=order_id)
            center = order.branch.center if (order.branch and order.branch.center) else None
            if center and center.payme_secret_key:
                return center.payme_secret_key
        except Exception:
            pass
        return settings.PAYME_SECRET_KEY

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


payme_webhook_view = PaymeWebhookView.as_view()
