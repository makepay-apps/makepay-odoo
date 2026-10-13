# Changelog

## 18.0.1.0.1 — 2026-10-13

- Fix unauthenticated payment-state changes through the browser return route. Return parameters no longer reconcile transactions; payment confirmation requires a signed webhook.
- Accept MakePay's plain JSON webhook deliveries and recognize completed payments.
- Reject malformed webhook payloads and match paid event names exactly.
- Add Odoo 18 HTTP regression tests for return forgery, webhook authentication, reconciliation, and checkout rendering.
- Clarify that this release supports Odoo 18. Odoo 19 requires different payment notification hooks.

Thanks to **kta1kri** for privately reporting the return-route vulnerability.
