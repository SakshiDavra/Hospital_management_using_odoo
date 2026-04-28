from odoo import models

class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_config(self):
        res = super()._loader_params_pos_config()
  
        res['search_params']['fields'].extend([
            'enable_card_resize',
            'product_card_width',
            'product_card_height',
            'product_font_size'
        ])
        return res