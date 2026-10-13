from __future__ import annotations

import hmac
import json
import logging
from hashlib import sha256

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class MakePayController(http.Controller):
    _return_url = "/payment/makepay/return"
    _webhook_url = "/payment/makepay/webhook"

    @http.route(_return_url, type="http", auth="public", methods=["GET"], csrf=False, save_session=False)
    def makepay_return(self, **data):
        # Browser return parameters are untrusted. Only signed webhooks reconcile payments.
        return request.redirect("/payment/status")

    @http.route(_webhook_url, type="http", auth="public", methods=["POST"], csrf=False, save_session=False)
    def makepay_webhook(self, **kwargs):
        raw_body = request.httprequest.get_data()
        signature = request.httprequest.headers.get("X-MakePay-Signature")
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return request.make_json_response({"error": "invalid payload"}, status=400)

        if not isinstance(payload, dict) or any(
            key in payload and not isinstance(payload[key], dict)
            for key in ("paymentLink", "data", "event", "session")
        ):
            return request.make_json_response({"error": "invalid payload"}, status=400)

        try:
            tx_sudo = request.env["payment.transaction"].sudo()._get_tx_from_notification_data(
                "makepay", payload,
            )
        except ValidationError:
            return request.make_json_response({"error": "missing payment link UID"}, status=400)

        if not tx_sudo:
            _logger.info("MakePay webhook ignored because no matching transaction was found.")
            return request.make_json_response({"ok": True, "reconciled": False})

        provider = tx_sudo.provider_id
        if not self._verify_signature(raw_body, signature, provider.makepay_webhook_secret):
            _logger.warning("MakePay webhook rejected because signature verification failed.")
            return request.make_json_response({"error": "invalid signature"}, status=401)

        tx_sudo._process_notification_data(payload)
        return request.make_json_response({"ok": True, "reconciled": True})

    @staticmethod
    def _verify_signature(raw_body: bytes, signature_header: str | None, secret: str | None) -> bool:
        if not signature_header or not secret:
            return False

        parts = {}
        for chunk in signature_header.split(","):
            key, _, value = chunk.strip().partition("=")
            parts[key] = value

        timestamp = parts.get("t")
        signature = parts.get("v1")
        if not timestamp or not signature:
            return False

        signed_payload = timestamp.encode("utf-8") + b"." + raw_body
        expected = hmac.new(secret.encode("utf-8"), signed_payload, sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
