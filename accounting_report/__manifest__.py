{
    'name': 'Accounting Report',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Custom Accounting Reports',
    'author': 'Sakshi Davra',
    'license': 'LGPL-3',
    'depends': [ 'base',
        'account',
        
        ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/partner_balance_report_views.xml',
    ],
    'installable': True,
    'application': True,
}