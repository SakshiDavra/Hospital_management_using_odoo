from odoo import models, api

class StockQuant(models.Model):
    _inherit = ['stock.quant', 'pos.load.mixin']

    @api.model
    def _load_pos_data_domain(self, data, config):
        
        return [ ]

    @api.model
    def _load_pos_data_fields(self, config):
        return ['product_id', 'location_id', 'quantity', 'reserved_quantity']

    @api.model
    def _load_pos_data_read(self, records, config):
        return super()._load_pos_data_read(records, config)