{
    'name': 'Sale Follower Mail Disable',
    'version': '19.0.1.0.0',
    'summary': 'Manage follower and subtype notifications',
    'description': """
        Control auto followers and subtype wise mail notification
    """,
    'author': 'Sakshi Davra',
    'website': '',
    'category': 'Sales',
    'license': 'LGPL-3',

    'depends': [
        'mail',
        'sale',
    ],

    'data': [
        'security/ir.model.access.csv',

        'views/follower_mail_config_views.xml',
    ],
    'installable': True,
    'application': False,
}