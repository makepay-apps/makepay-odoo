# Changelog

## 1.1.0 — 2026-10-13

- Support Odoo 18 and 19 from the same addon and `main` branch.
- Use Odoo 19's transaction lookup and payment update pipeline while retaining Odoo 18's notification hooks.
- Reconcile signed lifecycle events by hosted link UID without comparing crypto settlement amounts to the order currency.
- Use a series-independent manifest version, normalized by Odoo to `18.0.1.1.0` or `19.0.1.1.0`.
- Fix checkout error translation when MakePay returns a link UID without a redirect URL.
- Run installation, checkout rendering, and webhook regression tests in both Odoo versions.

## 18.0.1.0.1 — 2026-10-13

- Fix unauthenticated payment-state changes through the browser return route. Return parameters no longer reconcile transactions; payment confirmation requires a signed webhook.
- Accept MakePay's plain JSON webhook deliveries and recognize completed payments.
- Reject malformed webhook payloads and match paid event names exactly.
- Add Odoo 18 HTTP regression tests for return forgery, webhook authentication, reconciliation, and checkout rendering.
- Clarify that this release supports Odoo 18. Odoo 19 requires different payment notification hooks.

Thanks to **kta1kri** for privately reporting the return-route vulnerability.
