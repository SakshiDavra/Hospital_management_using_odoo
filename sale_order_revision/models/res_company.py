from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_sale_revision = fields.Boolean(string='Enable Sale Revision')
    revision_prefix = fields.Char(string='Revision Prefix')
    revision_separator = fields.Char(string='Revision Separator',default='/')