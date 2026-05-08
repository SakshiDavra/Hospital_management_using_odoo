{
    'name': 'POS Change',
    'version': '1.0',
    'depends': ['point_of_sale','account','stock'],
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
            'pos_changes/static/src/js/product_stock_popup.js',
            'pos_changes/static/src/js/product_screen_patch.js',
            'pos_changes/static/src/xml/product_stock_popup.xml',
            'pos_changes/static/src/js/pos_store.js',
            'pos_changes/static/src/js/product_configurator_patch.js',
            # 'pos_changes/static/src/js/optional_product_popup.js',

        ],

    },
    'author': 'Sakshi Davra',
    'license': 'LGPL-3',
}