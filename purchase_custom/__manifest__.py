{
    'name': 'Purchase Order Customization',
    'version': '1.0',
    'author': 'Sakshi Davra',
    'license': 'LGPL-3',
    'depends': ['base','purchase', 'stock'],

    'data': [
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': True,
}