from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_revision_adjustment = fields.Boolean(
        string='Revision Adjustment',
        default=False,
        copy=False,
    )