from odoo import models, fields


class PasswordCredentialType(models.Model):
    _name = 'password.credential.type'
    _description = 'Password Credential Type'
    _rec_name = 'name'

    name = fields.Char(
        string='Type Name',
        required=True
    )

    description = fields.Text(
        string='Description'
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )