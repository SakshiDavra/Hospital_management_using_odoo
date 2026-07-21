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
            'pos_pricelist_advanced/static/src/pricelist_utils.js',
            'pos_pricelist_advanced/static/src/app/components/order_tabs.js',
            'pos_pricelist_advanced/static/src/app/services/pos_store.js',
            "pos_pricelist_advanced/static/src/app/screens/product_screen/control_buttons/control_buttons.js",
            "pos_pricelist_advanced/static/src/app/models/pos_order.js",

        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}