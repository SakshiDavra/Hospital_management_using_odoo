from odoo import models, api

class StockLocation(models.Model):
    _inherit = 'stock.location'

    @api.model
    def _load_pos_data(self, data):
        return self.search_read(
            [('usage', '=', 'internal')],
            ['id', 'name', 'complete_name']
        )