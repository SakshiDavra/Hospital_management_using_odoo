from odoo import models, api

class StockLocation(models.Model):
    _inherit = 'stock.location'

    @api.depends('complete_name', 'usage')
    def _compute_display_name(self):
        super()._compute_display_name()
        if not self.env.context.get('show_location_qty'):
            return
        product_id = self.env.context.get('product_id')
        for location in self:
            if location.usage == 'internal':
                domain = [
                    ('location_id', '=', location.id),
                    ('quantity', '>', 0),
                ]
                if product_id:
                    domain.append(('product_id', '=', product_id))
                quants = self.env['stock.quant'].search(domain)
                available_qty = sum(quants.mapped('available_quantity'))
                location.display_name = f"[{available_qty:.1f}] {location.display_name}"