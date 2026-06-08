from odoo import models, fields
from odoo.exceptions import AccessError
from odoo.exceptions import AccessDenied, AccessError

class PasswordVerifyWizard(models.TransientModel):
    _name = 'password.verify.wizard'
    _description = 'Password Verify Wizard'
    password_id = fields.Many2one('password.manager',required=True)
    login_password = fields.Char(string='Current Login Password',required=True)

    def action_verify(self):
        credential = {'login': self.env.user.login, 'password': self.login_password, 'type': 'password',}
        try:
            self.env.user._check_credentials(credential,{'interactive': True})

        except AccessDenied:
            raise AccessError('Invalid login password.')

        return self.password_id._show_password_wizard()