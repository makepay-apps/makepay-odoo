{
    "name": "MakePay Payment Provider",
    "version": "18.0.1.0.0",
    "category": "Accounting/Payment Providers",
    "summary": "Accept MakePay hosted payment links in Odoo.",
    "author": "MakePay",
    "website": "https://www.makecrypto.io",
    "license": "LGPL-3",
    "depends": ["payment"],
    "data": [
        "views/payment_provider_views.xml",
        "views/payment_redirect_templates.xml",
        "data/payment_provider_data.xml",
    ],
    "installable": True,
    "application": False,
}
