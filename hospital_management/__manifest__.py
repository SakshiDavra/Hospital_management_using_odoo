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
            'website_sale',
            'portal', 
            'account',
            'contacts',
            'mail',  
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
            'data/website_form_actions.xml',

            # Views
           
            'views/templates.xml',
            'views/doctor_list_template.xml',
            'views/hospital_role_views.xml',
            'views/hospital_partner_views.xml',
            'views/portal_appointments.xml',
            'views/hospital_appointment_views.xml',
            'views/hospital_settings_views.xml',
            'views/appointment_cancel_wizard_views.xml',
            # 'views/snippets/image_text_snippet.xml',
            # 'views/snippets/doctor_specialization.xml',
            'views/snippets/snippet_catalog.xml',
            'views/snippets/specialization_snippet.xml',
            'views/snippets/s_my_form.xml',
            'views/snippets/snippets.xml',
 
            'views/hospital_menus.xml',
        ],

        'assets': {
            'web.assets_backend': [
                'web/static/lib/Chart/Chart.js',

                # JS
                'hospital_management/static/src/js/calendar_reload.js',
                'hospital_management/static/src/js/dashboard.js',
                'hospital_management/static/src/js/live_timer.js',
                'hospital_management/static/src/js/form_view_patch.js',
        
                # COMPONENTS
                'hospital_management/static/src/js/components/counter_card.js',
                'hospital_management/static/src/js/components/pie_chart.js',  
                'hospital_management/static/src/js/components/bar_chart.js',
                'hospital_management/static/src/js/components/shape_canvas.js',
                'hospital_management/static/src/js/components/todo_list.js',
                'hospital_management/static/src/js/components/top_doctors.js',

                # CSS
                'hospital_management/static/src/css/kanban.css',

                # XML
                'hospital_management/static/src/xml/dashboard.xml',
                'hospital_management/static/src/xml/counter_card.xml',
                'hospital_management/static/src/xml/pie_chart.xml',
                'hospital_management/static/src/xml/bar_chart.xml',
                'hospital_management/static/src/xml/shape_canvas.xml',
                'hospital_management/static/src/xml/todo_list.xml',
                'hospital_management/static/src/xml/top_doctors.xml',
                'hospital_management/static/src/xml/processing_timer.xml',

            ],

            'web.assets_frontend': [
                'hospital_management/static/src/css/style.css',
                'hospital_management/static/src/js/specialization_snippet.js',
                'hospital_management/static/src/xml/specialization_template.xml', 
                'hospital_management/static/src/scss/specialization.scss',
                'hospital_management/static/src/scss/doctor_card.scss',
                'hospital_management/static/src/js/appointment_form.js',

            ],
            'website.assets_editor': [   
                'hospital_management/static/src/js/specialization_option.js',
                'hospital_management/static/src/js/specialization_plugin.js',
                'hospital_management/static/src/js/limit_action.js',
                'hospital_management/static/src/xml/specialization_option.xml',  
                'hospital_management/static/src/js/style_action.js',  
                'hospital_management/static/src/js/form_editor.js',     
            ]
        },

        'installable': True,
        'application': True,
        'auto_install': False,
}
