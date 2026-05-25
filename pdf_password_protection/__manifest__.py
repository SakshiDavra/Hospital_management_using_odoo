{
    'name': 'PDF Password Protection',
    'version': '19.0.1.0.0',
    'summary': 'Protect PDF reports using password',
    'description': """
        PDF Password Protection
    """,

    'author': 'Sakshi Davra',
    'website': '',

    'license': 'LGPL-3',

    'depends': ['base'],

    'data': [
        'views/ir_actions_report_views.xml',
    ],

    'assets': {
        'web.assets_backend': [

        ],
    },

    'installable': True,
    'application': False,
}