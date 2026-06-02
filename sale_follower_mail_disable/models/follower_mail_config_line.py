from odoo import api, fields, models


class FollowerMailConfigLine(models.Model):
    _name = 'follower.mail.config.line'
    _description = 'Follower Mail Configuration Line'

    active = fields.Boolean(default=True, string='Disable Notification')

    config_id = fields.Many2one('follower.mail.config',string='Configuration',required=True,ondelete='cascade')

    model_name = fields.Char(related='config_id.model_id.model')

    subtype_id = fields.Many2one('mail.message.subtype',string='Subtype',required=True)

    allowed_partner_ids = fields.Many2many('res.partner',compute='_compute_allowed_partner_ids')

    partner_ids = fields.Many2many('res.partner',string='Followers')

    @api.depends('config_id.model_id')
    def _compute_allowed_partner_ids(self):
        for rec in self:
            rec.allowed_partner_ids = False

            if not rec.config_id.model_id:
                continue

            model_name = rec.config_id.model_id.model

            records = self.env[model_name].search([])

            rec.allowed_partner_ids = records.mapped(
                'message_partner_ids'
            )