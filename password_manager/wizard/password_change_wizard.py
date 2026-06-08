from odoo import models, fields
from odoo.exceptions import ValidationError


class PasswordChangeWizard(models.TransientModel):
    _name = 'password.change.wizard'
    _description = 'Password Change Wizard'

    password_id = fields.Many2one(
        'password.manager'
    )

    new_password = fields.Char(
        string='New Password',
    )
    def action_generate_password(self):

        self.new_password = self.env[
            'password.manager'
        ]._generate_password()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'password.change.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


    def action_update_password(self):
        self.password_id._check_password_access('write')
        self.password_id.write({'password': self.new_password})
