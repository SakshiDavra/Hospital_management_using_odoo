from odoo import models, fields

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    parent_line_id = fields.Many2one(
        'sale.order.line',
        string='Original Line',
        copy=False
    )