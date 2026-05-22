from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    location_id = fields.Many2one(
        'stock.location',
        string='CustomLocation',
        domain=[('usage', '=', 'internal')],
    )

