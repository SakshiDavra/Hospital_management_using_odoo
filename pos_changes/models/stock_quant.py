from odoo import models, api

class StockQuant(models.Model):
    _inherit = ['stock.quant', 'pos.load.mixin']

    @api.model
    def _load_pos_data_domain(self, data, config):
        return [('quantity', '>', 0)]

    @api.model
    def _load_pos_data_fields(self, config):
        return ['product_id', 'location_id', 'quantity']