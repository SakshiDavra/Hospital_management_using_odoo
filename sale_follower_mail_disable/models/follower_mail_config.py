from odoo import fields, models


class FollowerMailConfig(models.Model):
    _name = 'follower.mail.config'
    _description = 'Follower Mail Configuration'
    _rec_name = 'model_id'

    active = fields.Boolean(default=True)

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade'
    )
    model_name = fields.Char(
        related='model_id.model',
        readonly=True
    )

    auto_follower = fields.Boolean(
        string='Auto Follower',
        default=True
    )

    notification_enabled = fields.Boolean(
        string='Enable Notification',
        default=True
    )

    filter_domain = fields.Text(
        string='Filter Domain'
    )

    line_ids = fields.One2many(
        'follower.mail.config.line',
        'config_id',
        string='Subtype Configuration'
    )