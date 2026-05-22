from odoo import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('purchase_line_id'):
                purchase_line = self.env['purchase.order.line'].browse(vals['purchase_line_id'])
                if purchase_line.location_id:
                    vals['location_dest_id'] = purchase_line.location_id.id
        return super().create(vals_list)