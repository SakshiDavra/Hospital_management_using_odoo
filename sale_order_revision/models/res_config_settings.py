from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_sale_revision = fields.Boolean(string='Enable Sale Revision',
        config_parameter='sale_order_revision.enable_sale_revision'
    )
    revision_prefix = fields.Char(
        string='Revision Prefix',
        config_parameter='sale_order_revision.revision_prefix',
        default='R'
    )