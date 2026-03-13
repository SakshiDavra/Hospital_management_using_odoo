{
    'name': 'Hospital Management',
    'version': '1.0.0',
    'license': 'LGPL-3',
    'summary': 'Hospital Management System',
    'description': """
        Hospital Management Module
        - Manage Doctors
        - Manage Patients
        - Role-based structure using res.partner
    """,
    'author': 'Sakshi Davra',
    'category': 'Healthcare',
    'depends': [
        'base',
        'contacts',
        'mail',   # ADD THIS
    ],
    'data': [
        # Security
        'security/hospital_groups.xml',
        'security/ir.model.access.csv',
        'security/hospital_rules.xml',

        'wizard/appointment_report_wizard_view.xml',

        
        'reports/report_hospital_appointment.xml',
        'reports/appointment_summary_report.xml',
        'reports/appointment_summary_template.xml',

        # Data
        'data/hospital_role_data.xml',
        'data/hospital_sequence.xml',
        'data/appointment_status_data.xml', 
        'data/hospital_appointment_sequence.xml',
        'data/mail_template_data.xml',
        'data/hospital_cron.xml',

        # Views
        'views/hospital_role_views.xml',
        'views/hospital_partner_views.xml',

        'views/hospital_appointment_views.xml',
        'views/hospital_settings_views.xml',
        'views/appointment_cancel_wizard_views.xml',


        'views/hospital_menus.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'hospital_management/static/src/js/calendar_reload.js',
            'hospital_management/static/src/css/kanban.css'
        ],
    },


    'installable': True,
    'application': True,
    'auto_install': False,
}