{
    'name': 'Leave Management',
    'version': '1.0',
    'author': 'Sakshi Davra',
    'license': 'LGPL-3',
    'depends': ['base', 'hr', 'hr_holidays','hr_attendance'],

    'data': [

        'data/mail_template.xml',

        
        'views/hr_leave_views.xml',
    ],

    'installable': True,
    'application': True,
}