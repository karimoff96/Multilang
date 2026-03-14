"""
Critical tests for Payme webhook idempotency.

Covers:
- Authentication enforcement (bad/missing credentials rejected)
- CreateTransaction is idempotent for the same payme_id
- Duplicate CreateTransaction with a conflicting payme_id is rejected
- PerformTransaction is idempotent (re-call after success returns same result)
- CancelTransaction on a created (unpaid) transaction
- PerformTransaction on a cancelled order is rejected

Run with:
    python manage.py test orders.tests_payme_idempotency
"""

import base64
import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.urls import reverse

from orders.models import Order, PaymeTransaction
from orders.payme_webhook import PaymeWebhookView
from organizations.models import TranslationCenter, Branch
from services.models import Category, Product


SECRET_KEY = "test-payme-secret-key-abc"


def _auth_header(key=SECRET_KEY):
    """Build a valid Payme Basic-auth header for the given key."""
    token = base64.b64encode(f"Paycom:{key}".encode()).decode()
    return f"Basic {token}"


def _post(client, url, method, params, center_id=None, key=SECRET_KEY):
    """POST a Payme JSON-RPC request and return the parsed JSON response."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    path = url if center_id is None else f"/payme/webhook/{center_id}/"
    response = client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=_auth_header(key),
    )
    return response.json()


class PaymeTestBase(TestCase):
    """Shared fixtures for all Payme webhook tests."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser(
            username="payme_owner",
            password="secret123",
        )
        # Create center with sandbox key
        cls.center = TranslationCenter.objects.create(
            name="Payme Test Center",
            owner=cls.owner,
            payme_secret_key=SECRET_KEY,
            payme_sandbox=True,
        )
        # Branch is auto-created via TranslationCenter.save() signal if present;
        # grab it or create it if the signal doesn't run in test context.
        cls.branch = (
            cls.center.branches.first()
            or Branch.objects.create(name="Main", center=cls.center)
        )
        # Minimal Category + Product required by the Order FK
        cls.category = Category.objects.create(
            branch=cls.branch,
            name="Translation",
            charging="static",
        )
        cls.product = Product.objects.create(
            name="Standard Doc",
            category=cls.category,
            ordinary_first_page_price=Decimal("50000.00"),
            ordinary_other_page_price=Decimal("25000.00"),
            agency_first_page_price=Decimal("40000.00"),
            agency_other_page_price=Decimal("20000.00"),
        )

    def _make_order(self, total_price="50000.00", status="new"):
        """Create and return a payable test order.

        total_pages=0 prevents Order.save() from triggering the auto-price
        calculation path (which walks the product price matrix) — we supply
        the price directly via total_price.
        """
        order = Order.objects.create(
            branch=self.branch,
            product=self.product,
            manual_phone="998901234567",
            total_price=Decimal(total_price),
            total_pages=0,
            status=status,
        )
        return order


class PaymeAuthTests(PaymeTestBase):
    """Authorization header is enforced before any business logic."""

    def test_missing_auth_returns_error(self):
        order = self._make_order()
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "CheckPerformTransaction",
            "params": {
                "account": {"order_id": order.pk},
                "amount": int(order.total_due * 100),
            },
        }
        resp = self.client.post(
            f"/payme/webhook/{self.center.pk}/",
            data=json.dumps(payload),
            content_type="application/json",
            # No Authorization header
        )
        data = resp.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -32504)

    def test_wrong_key_returns_error(self):
        order = self._make_order()
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "CheckPerformTransaction",
            "params": {
                "account": {"order_id": order.pk},
                "amount": int(order.total_due * 100),
            },
        }
        wrong_token = base64.b64encode(b"Paycom:wrong-key").decode()
        resp = self.client.post(
            f"/payme/webhook/{self.center.pk}/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Basic {wrong_token}",
        )
        data = resp.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -32504)

    def test_correct_key_allows_through(self):
        order = self._make_order()
        params = {
            "account": {"order_id": order.pk},
            "amount": int(order.total_due * 100),
        }
        data = _post(self.client, None, "CheckPerformTransaction", params, center_id=self.center.pk)
        self.assertIn("result", data)
        self.assertTrue(data["result"]["allow"])


class PaymeCreateTransactionIdempotencyTests(PaymeTestBase):
    """CreateTransaction must be idempotent for the same payme_id."""

    def _create_params(self, order, payme_id):
        return {
            "id": payme_id,
            "time": 1700000000000,
            "amount": int(order.total_due * 100),
            "account": {"order_id": order.pk},
        }

    def test_first_create_succeeds(self):
        order = self._make_order()
        params = self._create_params(order, "txn-001")
        data = _post(self.client, None, "CreateTransaction", params, center_id=self.center.pk)
        self.assertIn("result", data, data)
        self.assertEqual(data["result"]["state"], PaymeTransaction.STATE_CREATED)
        self.assertTrue(PaymeTransaction.objects.filter(payme_transaction_id="txn-001").exists())

    def test_second_create_with_same_id_is_idempotent(self):
        order = self._make_order()
        params = self._create_params(order, "txn-002")
        # First call
        data1 = _post(self.client, None, "CreateTransaction", params, center_id=self.center.pk)
        self.assertIn("result", data1, data1)
        create_time_first = data1["result"]["create_time"]

        # Second call with identical parameters — must succeed and return the same create_time
        data2 = _post(self.client, None, "CreateTransaction", params, center_id=self.center.pk)
        self.assertIn("result", data2, data2)
        self.assertEqual(data2["result"]["create_time"], create_time_first)
        self.assertEqual(data2["result"]["transaction"], "txn-002")

        # Only one DB record should exist
        self.assertEqual(
            PaymeTransaction.objects.filter(payme_transaction_id="txn-002").count(), 1
        )

    def test_conflicting_payme_id_rejected(self):
        """Order already has a pending tx with id A — requesting id B must fail."""
        order = self._make_order()
        # Create first transaction
        data1 = _post(
            self.client, None, "CreateTransaction",
            self._create_params(order, "txn-003"),
            center_id=self.center.pk,
        )
        self.assertIn("result", data1, data1)

        # Request a different payme_id for the same order → conflict → -31050
        data2 = _post(
            self.client, None, "CreateTransaction",
            self._create_params(order, "txn-004-conflict"),
            center_id=self.center.pk,
        )
        self.assertIn("error", data2, data2)
        self.assertEqual(data2["error"]["code"], -31050)


class PaymePerformTransactionTests(PaymeTestBase):
    """PerformTransaction lifecycle and idempotency."""

    def _setup_created_tx(self, payme_id="txn-perform-001"):
        order = self._make_order()
        params = {
            "id": payme_id,
            "time": 1700000000000,
            "amount": int(order.total_due * 100),
            "account": {"order_id": order.pk},
        }
        _post(self.client, None, "CreateTransaction", params, center_id=self.center.pk)
        return order, payme_id

    def test_perform_succeeds(self):
        order, payme_id = self._setup_created_tx("txn-perf-010")
        data = _post(
            self.client, None, "PerformTransaction",
            {"id": payme_id},
            center_id=self.center.pk,
        )
        self.assertIn("result", data, data)
        self.assertEqual(data["result"]["state"], PaymeTransaction.STATE_PERFORMED)
        tx = PaymeTransaction.objects.get(payme_transaction_id=payme_id)
        self.assertEqual(tx.state, PaymeTransaction.STATE_PERFORMED)

    def test_perform_is_idempotent(self):
        """Calling PerformTransaction twice must return the same perform_time."""
        order, payme_id = self._setup_created_tx("txn-perf-011")
        data1 = _post(
            self.client, None, "PerformTransaction",
            {"id": payme_id},
            center_id=self.center.pk,
        )
        perform_time = data1["result"]["perform_time"]

        data2 = _post(
            self.client, None, "PerformTransaction",
            {"id": payme_id},
            center_id=self.center.pk,
        )
        self.assertIn("result", data2, data2)
        self.assertEqual(data2["result"]["perform_time"], perform_time)
        self.assertEqual(data2["result"]["state"], PaymeTransaction.STATE_PERFORMED)

    def test_perform_on_nonexistent_tx_returns_error(self):
        data = _post(
            self.client, None, "PerformTransaction",
            {"id": "txn-does-not-exist"},
            center_id=self.center.pk,
        )
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -31003)

    def test_perform_on_cancelled_order_returns_error(self):
        order, payme_id = self._setup_created_tx("txn-perf-012")
        # Manually cancel the order
        Order.objects.filter(pk=order.pk).update(status="cancelled")
        data = _post(
            self.client, None, "PerformTransaction",
            {"id": payme_id},
            center_id=self.center.pk,
        )
        self.assertIn("error", data, data)
        self.assertEqual(data["error"]["code"], -31008)


class PaymeCancelTransactionTests(PaymeTestBase):
    """CancelTransaction coverage."""

    def test_cancel_created_transaction(self):
        order = self._make_order()
        payme_id = "txn-cancel-001"
        create_params = {
            "id": payme_id,
            "time": 1700000000000,
            "amount": int(order.total_due * 100),
            "account": {"order_id": order.pk},
        }
        _post(self.client, None, "CreateTransaction", create_params, center_id=self.center.pk)

        data = _post(
            self.client, None, "CancelTransaction",
            {"id": payme_id, "reason": 1},
            center_id=self.center.pk,
        )
        self.assertIn("result", data, data)
        self.assertEqual(data["result"]["state"], PaymeTransaction.STATE_CANCELLED)
        tx = PaymeTransaction.objects.get(payme_transaction_id=payme_id)
        self.assertEqual(tx.state, PaymeTransaction.STATE_CANCELLED)

    def test_cancel_nonexistent_transaction_returns_error(self):
        data = _post(
            self.client, None, "CancelTransaction",
            {"id": "txn-missing", "reason": 1},
            center_id=self.center.pk,
        )
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -31003)
