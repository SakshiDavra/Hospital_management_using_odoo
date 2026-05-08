from odoo import models, api

class StockLocation(models.Model):
    _inherit = ['stock.location', 'pos.load.mixin']

    @api.model
    def _load_pos_data_fields(self, config):
        return ['name', 'complete_name', 'usage']