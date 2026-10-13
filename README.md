# MakePay Odoo Payment Provider

Odoo payment provider module for MakePay hosted payment links.

The module adds a MakePay provider, creates hosted payment links for Odoo transactions, redirects customers to MakePay checkout, and processes signed MakePay webhook notifications back into Odoo transaction states.

## Target Versions

- Odoo 18 payment provider API
- Odoo 19 is not supported by this release; its payment notification hooks differ.

## Configuration

After installing the module, configure the MakePay provider with:

- MakePay Key ID
- MakePay Key Secret
- MakePay Webhook Secret
- Partner API Base URL, normally `https://www.makecrypto.io`

Configure MakePay webhooks to send signed events to:

```text
https://your-odoo.example/payment/makepay/webhook
```

## Validation

```sh
python scripts/validate.py
```

The validator compiles Python files, checks XML data files, verifies required module metadata, and scans for forbidden identifiers and committed secrets.

## Production Notes

Upgrade installed modules to **18.0.1.0.1**. Browser return URLs only redirect to Odoo's payment status page; signed MakePay webhooks are required to confirm payments. Configure the webhook URL and secret on both sides before accepting payments. A customer may see a pending status until the webhook arrives.

Run this module in an Odoo development database before production use. The provider hooks follow Odoo 18's payment provider extension points.
