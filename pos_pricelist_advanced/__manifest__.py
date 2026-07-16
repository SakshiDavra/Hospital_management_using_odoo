{
    "name": "POS Pricelist Advanced",
    "version": "19.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Advanced POS Pricelist Management",
    "author" : "Sakshi Davra",
    "description": """Advanced POS Pricelist Management""",
    "depends": [
        "point_of_sale",
        "product",
        "pos_hr",
        "calendar",
    ],
    "data": [
        'security/ir.model.access.csv',
        'views/product_pricelist_views.xml',

        'wizard/pricelist_report_wizard_views.xml',
        'report/report.xml',
        'report/pricelist_sales_report.xml',
    ],
    "assets": {
        'point_of_sale._assets_pos': [
            'pos_pricelist_advanced/static/src/js/pricelist_utils.js',
            'pos_pricelist_advanced/static/src/js/pricelist_patch.js',
            'pos_pricelist_advanced/static/src/js/manager_pin_patch.js',
            'pos_pricelist_advanced/static/src/js/partner_pricelist_patch.js',
            'pos_pricelist_advanced/static/src/js/discount_patch.js',
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}