from odoo import models, fields, api

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    custom_location_id = fields.Many2one('stock.location', string="Selected Location")

    @api.model
    def _load_pos_data_fields(self, config):
        params = super()._load_pos_data_fields(config)
        params.append('custom_location_id')
        return params
    
    @api.model
    def _order_line_fields(self, line, session_id=None):
        fields = super()._order_line_fields(line, session_id)
        if line[2].get('custom_location_id'):
            fields[2]['custom_location_id'] = line[2].get('custom_location_id')
        return fields
    