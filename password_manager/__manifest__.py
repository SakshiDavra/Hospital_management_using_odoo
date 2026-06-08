{
    'name': 'Password Manager',
    'version': '19.0.1.0.0',
    'summary': 'Secure Password Management',
    'description': 'Password Manager Module',
    'author': 'Sakshi',
    'category': 'Tools',
    'license': 'LGPL-3',

    'depends': ['base','hr'],

    'data': [

        'data/cron.xml',
            
        'security/ir.model.access.csv',
        'security/password_manager_security.xml',

        'views/password_credential_type_views.xml',
        'views/password_category_views.xml',
        'views/password_manager_views.xml',
        'views/res_config_settings_views.xml',
        

        'wizard/password_change_wizard_views.xml',
        # 'wizard/password_view_wizard_views.xml',
        'wizard/password_verify_wizard_views.xml',
        'wizard/password_merge_wizard_views.xml',


        'views/menu_views.xml',

        
    ],

    'assets': {
        'web.assets_backend': [

            'password_manager/static/src/js/password_auto_close.js',
        ],
    },

    'installable': True,
    'application': True,
}