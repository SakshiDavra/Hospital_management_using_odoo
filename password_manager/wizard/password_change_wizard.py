from odoo import models, fields



class PasswordChangeWizard(models.TransientModel):
    _name = 'password.change.wizard'
    _description = 'Password Change Wizard'

    password_id = fields.Many2one('password.manager')
    new_password = fields.Char(string='New Password', required=True)

    def action_update_password(self):
        self.password_id.write({'password': self.new_password})

