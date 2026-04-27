from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_card_resize = fields.Boolean(
        related="pos_config_id.enable_card_resize",
        readonly=False
    )

    product_card_width = fields.Integer(
        related="pos_config_id.product_card_width",
        readonly=False
    )

    product_card_height = fields.Integer(
        related="pos_config_id.product_card_height",
        readonly=False
    )

    product_font_size = fields.Integer(
        related="pos_config_id.product_font_size",
        readonly=False
    )