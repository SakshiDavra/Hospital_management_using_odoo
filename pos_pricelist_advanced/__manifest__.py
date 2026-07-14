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
        'views/product_pricelist_views.xml',
    ],
    "assets": {
        'web.assets_backend': [
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}