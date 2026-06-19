from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_sale_revision = fields.Boolean(related='company_id.enable_sale_revision',readonly=False)

    revision_prefix = fields.Char(related='company_id.revision_prefix',readonly=False)

    revision_separator = fields.Char(related='company_id.revision_separator',readonly=False)
    @api.constrains('enable_sale_revision', 'revision_separator')
    def _check_revision_separator(self):
        for rec in self:
            if rec.enable_sale_revision and not rec.revision_separator:
                raise ValidationError(
                    _("Revision Separator is required when Sale Revision is enabled.")
                )