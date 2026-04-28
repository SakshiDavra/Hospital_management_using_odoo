{
    'name': 'POS Change',
    'version': '1.0',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        
    ],
    'installable': True,

    'assets': {
        'point_of_sale._assets_pos': [
            'pos_changes/static/src/js/clear_button.js',
            'pos_changes/static/src/xml/clear_button.xml',
            'pos_changes/static/src/xml/pos_buttons.xml',
            'pos_changes/static/src/xml/product_card.xml',
            'pos_changes/static/src/xml/product_screen.xml',


        ],

    },
    'author': 'Sakshi Davra',
    'license': 'LGPL-3',
}