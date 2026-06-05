from odoo import models, fields


class PasswordVault(models.Model):
    _name = 'password.vault'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Password Vault'
    _rec_name = 'name'

    name = fields.Char(
        string='Vault Name',
        required=True,
        tracking=True
    )

    description = fields.Text(
        string='Description'
    )

    owner_id = fields.Many2one(
        'res.users',
        string='Owner',
        default=lambda self: self.env.user,
        required=True
    )

    password_ids = fields.One2many(
        'password.manager',
        'vault_id',
        string='Passwords'
    )

    active = fields.Boolean(
        default=True
    )