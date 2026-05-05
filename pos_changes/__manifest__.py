{
    'name': 'POS Change',
    'version': '1.0',
    'depends': ['point_of_sale','account'],
    'data': [
        'views/pos_config_view.xml',
        'reports/report.xml',
        'reports/pos_order_receipt.xml',
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
            'pos_changes/static/src/js/location_popup.js',
            'pos_changes/static/src/xml/location_popup.xml',

            # 'pos_changes/static/src/js/popup/custom_popup.js',
            # 'pos_changes/static/src/xml/popup/custom_popup.xml',
            'pos_changes/static/src/js/product_screen_override.js',
            # 'pos_changes/static/src/js/orderline_patch.js',
        ],

    },
    'author': 'Sakshi Davra',
    'license': 'LGPL-3',
}