from odoo import models, fields

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    revision_base_price = fields.Float(
        string='Revision Base Price'
    )
    revision_base_qty = fields.Float(
        string="Revision Base Qty"
    )
    revision_sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Revision Sale Line'
    )