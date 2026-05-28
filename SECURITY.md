# Security Policy

## Reporting

Report security issues to info@makepay.io.

## Credentials

- Store MakePay keys only on the Odoo payment provider record.
- Never expose MakePay partner keys to browser JavaScript.
- Verify MakePay webhook signatures before changing transaction states.
- Rotate MakePay keys if Odoo configuration or backups are exposed.
