# Contributing

Thanks for helping improve the MakePay Odoo payment provider.

Run `python scripts/validate.py` before opening a pull request. Test checkout redirection, return handling, and webhook reconciliation in an Odoo development database before release.

Run the module's HTTP regression suite with:

```sh
odoo -d makepay_test -i makepay_odoo --test-enable --test-tags /makepay_odoo --stop-after-init --without-demo=all
```

Add this repository to Odoo's addons path and use a disposable development database. Run the suite in both Odoo 18 and Odoo 19; GitHub Actions tests both with PostgreSQL 16. Keep the manifest version independent of the Odoo series so the same addon installs in both versions.

Do not commit MakePay keys, Odoo database dumps, production transaction payloads, webhook signing secrets, or customer data.
