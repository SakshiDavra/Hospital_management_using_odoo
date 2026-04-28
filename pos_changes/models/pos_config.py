from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_card_resize = fields.Boolean(string="Enable Card Resize", default=False)
    product_card_width = fields.Integer(default=150)
    product_card_height = fields.Integer(default=170)
    product_font_size = fields.Integer(default=14)
