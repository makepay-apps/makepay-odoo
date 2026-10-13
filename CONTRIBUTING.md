# Contributing

Thanks for helping improve the MakePay Odoo payment provider.

Run `python scripts/validate.py` before opening a pull request. Test checkout redirection, return handling, and webhook reconciliation in an Odoo development database before release.

Run the module's HTTP regression suite with:

```sh
odoo -d makepay_test -i makepay_odoo --test-enable --test-tags /makepay_odoo --stop-after-init --without-demo=all
```

Add this repository to Odoo's addons path and use a disposable development database. GitHub Actions runs this suite in Odoo 18 with PostgreSQL 16.

Do not commit MakePay keys, Odoo database dumps, production transaction payloads, webhook signing secrets, or customer data.
