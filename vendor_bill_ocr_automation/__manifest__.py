{
    'name': 'Vendor Bill OCR Automation',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'OCR-based vendor invoice processing and automation',
    'author': 'Sakshi Davra',
    'license': 'LGPL-3',

    'depends': [
        'account',
        'purchase',
        'stock',
    ],

    'data': [
        'security/ir.model.access.csv',
        'wizard/purchase_qty_wizard_view.xml',
        'wizard/purchase_bill_validation_wizard.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        
    ],

    'assets': {
        'web.assets_backend': [
            'vendor_bill_ocr_automation/static/src/js/invoice_uploader.js',
            'vendor_bill_ocr_automation/static/src/xml/invoice_uploader.xml',
          ],
    },

    'installable': True,
    'application': False,
    'auto_install': False,
}