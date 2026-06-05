from odoo import models, fields


class PasswordViewWizard(models.TransientModel):
    _name = 'password.view.wizard'
    _description = 'Password View Wizard'

    password = fields.Char(
        string='Password',
        readonly=True
    )