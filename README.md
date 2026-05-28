# MakePay Odoo Payment Provider

Odoo payment provider module for MakePay hosted payment links.

The module adds a MakePay provider, creates hosted payment links for Odoo transactions, redirects customers to MakePay checkout, and processes signed MakePay webhook notifications back into Odoo transaction states.

## Target Versions

- Odoo 18 and 19 payment provider APIs
- Odoo 17 may work with minor view or method adjustments

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

Run this module in an Odoo development database before production use. The provider hooks follow Odoo's standard payment provider extension points, but each Odoo major version can make small view or provider-field changes.
