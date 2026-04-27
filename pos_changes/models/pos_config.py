from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_card_resize = fields.Boolean(string="Enable Card Resize") 
    product_card_width = fields.Integer(default=150)
    product_card_height = fields.Integer(default=200)
    product_font_size = fields.Integer(default=14)

    def _loader_params_pos_config(self):
        result = super()._loader_params_pos_config()
        result['search_params']['fields'].extend([
            'enable_card_resize',
            'product_card_width',
            'product_card_height',
            'product_font_size',
        ])
        return result