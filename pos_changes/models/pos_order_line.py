from odoo import models, fields, api

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    # આ ફિલ્ડ ડેટાબેઝમાં ડેટા સેવ કરશે
    custom_location_id = fields.Many2one('stock.location', string="Selected Location")

    # આ મેથડ POS ને જણાવશે કે આ ફિલ્ડ ફ્રન્ટએન્ડમાં વાપરવા માટે મોકલો
    @api.model
    def _load_pos_data_fields(self, config):
        params = super()._load_pos_data_fields(config)
        params.append('custom_location_id')
        return params