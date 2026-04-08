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
        'website',
        'portal', 
        'account',
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
        'reports/invoice_report.xml',

        # Data
        'data/hospital_role_data.xml',
        'data/hospital_sequence.xml',
        'data/appointment_status_data.xml', 
        'data/hospital_appointment_sequence.xml',
        'data/mail_template_data.xml',
        'data/hospital_cron.xml',

        # Views
        'views/templates.xml',
        'views/hospital_role_views.xml',
        'views/hospital_partner_views.xml',
        'views/portal_appointments.xml',
        'views/hospital_appointment_views.xml',
        'views/hospital_settings_views.xml',
        'views/appointment_cancel_wizard_views.xml',
        
        
        'views/hospital_menus.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'web/static/lib/Chart/Chart.js',
            'hospital_management/static/src/js/calendar_reload.js',
            'hospital_management/static/src/css/kanban.css',
            'hospital_management/static/src/js/dashboard.js',
            'hospital_management/static/src/js/components/counter_card.js',
            'hospital_management/static/src/js/components/pie_chart.js',
            'hospital_management/static/src/xml/dashboard.xml',
            'hospital_management/static/src/xml/counter_card.xml',
            'hospital_management/static/src/js/components/pie_chart.js',
            'hospital_management/static/src/xml/pie_chart.xml',
            'hospital_management/static/src/js/components/bar_chart.js',
            'hospital_management/static/src/xml/bar_chart.xml',
            'hospital_management/static/src/js/components/shape_canvas.js',
            'hospital_management/static/src/xml/shape_canvas.xml',

        ],

        'web.assets_frontend': [
            'hospital_management/static/src/css/style.css',

        ],
    },


    'installable': True,
    'application': True,
    'auto_install': False,
}