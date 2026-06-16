# __manifest__.py database name :- sale_order_revision_v19

{
    'name': 'Sale Order Revision',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Manage revisions for confirmed sale orders',
    'author': 'Sakshi Davra',
    'license': 'LGPL-3',

    'depends': [
       'sale_management',
    ],

    'data': [
        'views/res_config_settings_views.xml',
        "views/sale_order_views.xml",

        'data/server_actions.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}