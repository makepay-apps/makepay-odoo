import hmac
import json
import time
from hashlib import sha256
from unittest.mock import patch

from odoo import release
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.addons.payment.tests.http_common import PaymentHttpCommon

from ..controllers.main import MakePayController


@tagged("post_install", "-at_install")
class TestMakePayPayment(PaymentHttpCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls._prepare_provider("makepay", update_values={
            "makepay_key_id": "test-key-id",
            "makepay_key_secret": "test-key-secret",
            "makepay_webhook_secret": "test-webhook-secret",
        })
        cls.payment_method = cls.env.ref("makepay_odoo.payment_method_makepay")
        cls.payment_method_id = cls.payment_method.id

    def setUp(self):
        super().setUp()
        self.tx = self._create_transaction(
            "redirect", state="pending", makepay_payment_link_uid="test-link-uid",
            provider_reference="test-link-uid",
        )

    def _payload(self, status="complete"):
        return {
            "type": "makepay.payment.status_changed",
            "event": {"type": "status_changed"},
            "paymentLink": {"uid": "test-link-uid", "status": "active"},
            "session": {"status": status},
            "data": {},
        }

    def _post_webhook(self, payload, secret="test-webhook-secret", signature=None):
        body = json.dumps(payload).encode()
        if signature is None:
            timestamp = str(int(time.time()))
            digest = hmac.new(secret.encode(), timestamp.encode() + b"." + body, sha256).hexdigest()
            signature = f"t={timestamp},v1={digest}"
        return self.opener.post(
            self._build_url(MakePayController._webhook_url), data=body,
            headers={"Content-Type": "application/json", "X-MakePay-Signature": signature},
        )

    def test_browser_returns_cannot_change_payment_state(self):
        for parameters in (
            {"reference": "test-link-uid", "status": "paid"},
            {"reference": "test-link-uid", "status": "PAID"},
            {"reference": "test-link-uid", "type": "makepay.payment.paid"},
            {"reference": "test-link-uid", "status": "complete"},
            {"reference": "test-link-uid", "status": "failed"},
            {"reference": "test-link-uid", "status": "canceled"},
            {"reference": self.tx.reference, "status": "paid"},
            {},
        ):
            with self.subTest(parameters=parameters):
                response = self.opener.get(
                    self._build_url(MakePayController._return_url),
                    params=parameters, allow_redirects=False,
                )
                self.assertEqual(response.status_code, 303)
                self.assertEqual(response.headers["Location"], "/payment/status")
                self.tx.invalidate_recordset()
                self.assertEqual(self.tx.state, "pending")
                self.assertEqual(self.tx.provider_reference, "test-link-uid")

    def test_valid_plain_json_webhook_confirms_payment(self):
        response = self._post_webhook(self._payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "reconciled": True})
        self.tx.invalidate_recordset()
        self.assertEqual(self.tx.state, "done")
        # Retries and subsequent browser returns preserve a confirmed transaction.
        self.assertEqual(self._post_webhook(self._payload()).status_code, 200)
        self.opener.get(self._build_url(MakePayController._return_url), params={
            "reference": "test-link-uid", "status": "failed",
        }, allow_redirects=False)
        self.tx.invalidate_recordset()
        self.assertEqual(self.tx.state, "done")

    def test_unsigned_and_wrong_secret_webhooks_do_not_confirm_payment(self):
        for kwargs in ({"signature": ""}, {"secret": "wrong-secret"}):
            with self.subTest(kwargs=kwargs):
                response = self._post_webhook(self._payload(), **kwargs)
                self.assertEqual(response.status_code, 401)
                self.tx.invalidate_recordset()
                self.assertEqual(self.tx.state, "pending")

    def test_tampered_signed_body_does_not_confirm_payment(self):
        body = json.dumps(self._payload("pending")).encode()
        timestamp = str(int(time.time()))
        digest = hmac.new(b"test-webhook-secret", timestamp.encode() + b"." + body, sha256).hexdigest()
        response = self._post_webhook(self._payload(), signature=f"t={timestamp},v1={digest}")
        self.assertEqual(response.status_code, 401)
        self.tx.invalidate_recordset()
        self.assertEqual(self.tx.state, "pending")

    def test_missing_webhook_secret_fails_closed(self):
        self.provider.makepay_webhook_secret = False
        response = self._post_webhook(self._payload())
        self.assertEqual(response.status_code, 401)
        self.tx.invalidate_recordset()
        self.assertEqual(self.tx.state, "pending")

    def test_unknown_link_does_not_modify_existing_transaction(self):
        payload = self._payload()
        payload["paymentLink"]["uid"] = "unknown-link"
        response = self._post_webhook(payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "reconciled": False})
        self.tx.invalidate_recordset()
        self.assertEqual(self.tx.state, "pending")

    def test_malformed_webhooks_do_not_modify_transaction(self):
        for body in (b"{", b"\xff", b"[]", b'{"session":"complete"}', b"{}"):
            with self.subTest(body=body):
                response = self.opener.post(
                    self._build_url(MakePayController._webhook_url), data=body,
                    headers={"Content-Type": "application/json"},
                )
                self.assertEqual(response.status_code, 400)
                self.tx.invalidate_recordset()
                self.assertEqual(self.tx.state, "pending")

    def test_signed_failed_and_canceled_webhooks_reconcile(self):
        for status, state in (("failed", "error"), ("cancelled", "cancel"), ("paid", "done")):
            with self.subTest(status=status):
                self.tx.state = "pending"
                response = self._post_webhook(self._payload(status))
                self.assertEqual(response.status_code, 200)
                self.tx.invalidate_recordset()
                self.assertEqual(self.tx.state, state)

    def test_event_substrings_do_not_confirm_payment(self):
        payload = self._payload("pending")
        payload["type"] = "makepay.payment.paid.failed"
        response = self._post_webhook(payload)
        self.assertEqual(response.status_code, 200)
        self.tx.invalidate_recordset()
        self.assertEqual(self.tx.state, "pending")

    def test_checkout_creates_and_renders_hosted_link(self):
        response = {"uid": "checkout-link", "checkoutUrl": "https://www.makepay.io/payment/checkout-link"}
        with patch.object(type(self.provider), "_makepay_create_payment_link", return_value=response) as create_link:
            processing_values = self.tx._get_processing_values()
        payload = create_link.call_args.args[0]
        self.assertEqual(payload["orderId"], self.tx.reference)
        self.assertNotIn("status=", payload["successUrl"])
        self.assertNotIn("status=", payload["failureUrl"])
        self.assertIn(MakePayController._return_url, payload["returnUrl"])
        self.assertIn(response["checkoutUrl"], str(processing_values["redirect_form_html"]))
        self.assertEqual(self.tx.makepay_payment_link_uid, "checkout-link")
        self.assertEqual(self.tx.provider_reference, "checkout-link")
        self.assertEqual(self.tx.state, "pending")

    def test_manifest_version_matches_installed_odoo_series(self):
        module = self.env["ir.module.module"].search([("name", "=", "makepay_odoo")])
        self.assertEqual(module.latest_version, f"{release.major_version}.1.1.0")

    def test_signed_webhooks_match_supported_link_identifiers(self):
        for identity in (
            {"paymentLink": {"id": "test-link-uid"}},
            {"data": {"paymentLinkUid": "test-link-uid"}},
            {"data": {"uid": "test-link-uid"}},
            {"reference": "test-link-uid"},
        ):
            with self.subTest(identity=identity):
                self.tx.state = "pending"
                payload = {"session": {"status": "complete"}, **identity}
                response = self._post_webhook(payload)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"ok": True, "reconciled": True})
                self.tx.invalidate_recordset()
                self.assertEqual(self.tx.state, "done")

    def test_signed_webhook_matches_existing_provider_reference(self):
        self.tx.makepay_payment_link_uid = False
        response = self._post_webhook(self._payload())
        self.assertEqual(response.status_code, 200)
        self.tx.invalidate_recordset()
        self.assertEqual(self.tx.state, "done")
        self.assertEqual(self.tx.makepay_payment_link_uid, "test-link-uid")

    def test_native_payment_pipeline_reconciles_by_link_uid(self):
        transactions = self.env["payment.transaction"]
        payload = self._payload()
        if hasattr(transactions, "_process"):
            tx = transactions._process("makepay", payload)
        else:
            tx = transactions._handle_notification_data("makepay", payload)
        self.assertEqual(tx, self.tx)
        self.assertEqual(tx.state, "done")

    def test_other_provider_lookup_uses_native_behavior(self):
        transactions = self.env["payment.transaction"]
        payload = {"reference": self.tx.reference}
        if hasattr(transactions, "_process"):
            # The same reference with another provider must not match MakePay.
            self.assertFalse(transactions._search_by_reference("none", payload))
        else:
            self.assertFalse(transactions._get_tx_from_notification_data("none", payload))

    def test_crypto_settlement_amount_does_not_replace_order_amount(self):
        payload = self._payload()
        payload["paymentLink"].update({"amount": "0.0001", "currency": "BTC"})
        payload["session"].update({"invoiceAmount": "0.0001", "invoiceAsset": "BTC"})
        response = self._post_webhook(payload)
        self.assertEqual(response.status_code, 200)
        self.tx.invalidate_recordset()
        self.assertEqual(self.tx.state, "done")
        self.assertEqual(self.tx.amount, self.amount)
        self.assertEqual(self.tx.currency_id, self.currency)

    def test_checkout_rejects_incomplete_payment_link_response(self):
        for response in ({"uid": "checkout-link"}, {"checkoutUrl": "https://www.makepay.io"}):
            with self.subTest(response=response):
                with patch.object(type(self.provider), "_makepay_create_payment_link", return_value=response):
                    with self.assertRaises(ValidationError):
                        self.tx._get_processing_values()
                self.assertEqual(self.tx.makepay_payment_link_uid, "test-link-uid")
                self.assertEqual(self.tx.state, "pending")
