{
    'name': 'POS Change',
    'version': '1.0',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_config_view.xml',
    ],
    'installable': True,

    'assets': {
        'point_of_sale._assets_pos': [
            'pos_changes/static/src/js/clear_button.js',
            'pos_changes/static/src/xml/clear_button.xml',
            'pos_changes/static/src/xml/pos_buttons.xml',

            # 'pos_changes/static/src/scss/pos_custom.scss',

            'pos_changes/static/src/js/pos_dynamic_style.js',

        ],

    },
    'author': 'Sakshi Davra',
    'license': 'LGPL-3',
}