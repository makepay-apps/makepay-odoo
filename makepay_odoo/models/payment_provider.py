from __future__ import annotations

import logging

import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("makepay", "MakePay")],
        ondelete={"makepay": "set default"},
    )
    makepay_key_id = fields.Char(string="MakePay Key ID", groups="base.group_system")
    makepay_key_secret = fields.Char(string="MakePay Key Secret", groups="base.group_system")
    makepay_webhook_secret = fields.Char(
        string="MakePay Webhook Secret",
        groups="base.group_system",
    )
    makepay_base_url = fields.Char(
        string="MakePay Partner API Base URL",
        default="https://www.makecrypto.io",
        required_if_provider="makepay",
    )
    makepay_send_payment_request_email = fields.Boolean(
        string="Send Payment Request Email",
        default=True,
    )

    def _get_supported_currencies(self):
        supported = super()._get_supported_currencies()
        if self.code != "makepay":
            return supported
        return supported.filtered(lambda currency: currency.name)

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code != "makepay":
            return default_codes
        return {"makepay"}

    def _get_redirect_form_view(self, is_validation=False):
        if self.code != "makepay":
            return super()._get_redirect_form_view(is_validation=is_validation)
        return self.env.ref("makepay_odoo.redirect_form")

    def _makepay_create_payment_link(self, payload):
        self.ensure_one()

        if not self.makepay_key_id or not self.makepay_key_secret:
            raise ValidationError(_("MakePay credentials are not configured."))

        url = f"{self.makepay_base_url.rstrip('/')}/api/partner/v1/makepay/payment-links"
        body = {
            "status": "active",
            "sendPaymentRequestEmail": bool(self.makepay_send_payment_request_email),
            "payload": payload,
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-MakeCrypto-Key-Id": self.makepay_key_id,
            "X-MakeCrypto-Key-Secret": self.makepay_key_secret,
        }

        try:
            response = requests.post(url, json=body, headers=headers, timeout=20)
            response.raise_for_status()
        except requests.RequestException as exc:
            _logger.exception("MakePay payment-link request failed.")
            raise ValidationError(_("MakePay payment-link request failed: %s") % exc) from exc

        data = response.json()
        return data.get("paymentLink") or data
