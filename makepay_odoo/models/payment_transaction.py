from __future__ import annotations

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from ..controllers.main import MakePayController


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    makepay_payment_link_uid = fields.Char(readonly=True)
    makepay_payment_url = fields.Char(readonly=True)

    def _get_specific_rendering_values(self, processing_values):
        rendering_values = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "makepay":
            return rendering_values

        base_url = self.provider_id.get_base_url()
        payload = {
            "title": _("Odoo transaction %s") % self.reference,
            "description": _("Payment for Odoo transaction %s") % self.reference,
            "amount": str(self.amount),
            "currency": self.currency_id.name,
            "orderId": self.reference,
            "customerEmail": self.partner_email,
            "returnUrl": f"{base_url}{MakePayController._return_url}?reference={self.reference}",
            "successUrl": f"{base_url}{MakePayController._return_url}",
            "failureUrl": f"{base_url}{MakePayController._return_url}",
            "metadata": {
                "platform": "odoo",
                "reference": self.reference,
                "transactionId": self.id,
            },
        }
        payment_link = self.provider_id._makepay_create_payment_link(payload)
        uid = payment_link.get("uid") or payment_link.get("id")
        redirect_url = payment_link.get("checkoutUrl") or payment_link.get("publicUrl")

        if not uid or not redirect_url:
            raise ValidationError(_("MakePay did not return a payment link URL."))

        self.write(
            {
                "makepay_payment_link_uid": uid,
                "makepay_payment_url": redirect_url,
                "provider_reference": uid,
            }
        )

        rendering_values.update(
            {
                "api_url": redirect_url,
                "makepay_payment_url": redirect_url,
            }
        )
        return rendering_values

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "makepay" or tx:
            return tx

        uid = self._makepay_payment_link_uid(notification_data)
        if not uid:
            raise ValidationError(_("MakePay notification did not include a payment link UID."))

        return self.search(
            [
                ("provider_code", "=", "makepay"),
                "|",
                ("makepay_payment_link_uid", "=", uid),
                ("provider_reference", "=", uid),
            ],
            limit=1,
        )

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != "makepay":
            return

        uid = self._makepay_payment_link_uid(notification_data)
        if uid and not self.makepay_payment_link_uid:
            self.makepay_payment_link_uid = uid
            self.provider_reference = uid

        if self._makepay_is_paid(notification_data):
            self._set_done()
        elif self._makepay_is_canceled(notification_data):
            self._set_canceled()
        elif self._makepay_is_failed(notification_data):
            self._set_error(_("MakePay reported a failed payment."))
        else:
            self._set_pending()

    @staticmethod
    def _makepay_payment_link_uid(notification_data):
        payment_link = notification_data.get("paymentLink") or {}
        data = notification_data.get("data") or {}
        return (
            payment_link.get("uid")
            or payment_link.get("id")
            or data.get("paymentLinkUid")
            or data.get("uid")
            or notification_data.get("reference")
        )

    @staticmethod
    def _makepay_is_paid(notification_data):
        values = PaymentTransaction._makepay_status_values(notification_data)
        return bool(values & {
            "paid", "complete", "payment.paid", "makepay.payment.paid",
            "payment.complete", "makepay.payment.complete",
        })

    @staticmethod
    def _makepay_is_failed(notification_data):
        values = PaymentTransaction._makepay_status_values(notification_data)
        return any(value in {"failed", "expired"} for value in values)

    @staticmethod
    def _makepay_is_canceled(notification_data):
        values = PaymentTransaction._makepay_status_values(notification_data)
        return any(value in {"canceled", "cancelled"} for value in values)

    @staticmethod
    def _makepay_status_values(notification_data):
        event = notification_data.get("event") or {}
        session = notification_data.get("session") or {}
        payment_link = notification_data.get("paymentLink") or {}
        return {
            str(value).lower()
            for value in [
                notification_data.get("type"),
                event.get("type"),
                session.get("status"),
                payment_link.get("status"),
                notification_data.get("status"),
            ]
            if value
        }
