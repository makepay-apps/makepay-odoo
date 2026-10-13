# MakePay Odoo Payment Provider

Odoo payment provider module for MakePay hosted payment links.

The module adds a MakePay provider, creates hosted payment links for Odoo transactions, redirects customers to MakePay checkout, and processes signed MakePay webhook notifications back into Odoo transaction states.

## Target Versions

- Odoo 18 and Odoo 19, using the same addon and `main` branch.
- Version `1.1.0` uses Odoo's version normalization: `18.0.1.1.0` on Odoo 18 and `19.0.1.1.0` on Odoo 19. No manifest edits or separate version branches are needed.

Install on Odoo.sh or a self-hosted Odoo instance that allows custom addons. Add this repository to the addons path, update the Apps list, and install **MakePay Payment Provider**.

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

The validator checks Python syntax and XML data files and scans for forbidden identifiers and committed secrets. GitHub Actions also installs the addon and runs its checkout and HTTP webhook regression suite against both Odoo 18 and 19 with PostgreSQL 16.

## Production Notes

Upgrade installed modules to **1.1.0** (shown as **18.0.1.1.0** or **19.0.1.1.0** by Odoo). Existing Odoo 18 installations can upgrade the addon in place. Moving an entire Odoo database from 18 to 19 still requires the usual Odoo database migration.

Browser return URLs only redirect to Odoo's payment status page; signed MakePay webhooks are required to confirm payments. Configure the webhook URL and secret on both sides before accepting payments. A customer may see a pending status until the webhook arrives.

The addon uses Odoo 18's notification hooks or Odoo 19's payment processing hooks automatically. MakePay lifecycle events can contain crypto settlement amounts rather than the original order currency, so Odoo 19's generic amount comparison is skipped for MakePay. Reconciliation uses the signed payment status and the hosted link UID stored when the transaction's payment link was created.
