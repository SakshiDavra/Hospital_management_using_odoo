from odoo import models, fields
from odoo.exceptions import ValidationError

class PasswordVerifyWizard(models.TransientModel):
    _name = 'password.verify.wizard'

    password_id = fields.Many2one(
        'password.manager',
        required=True
    )

    login_password = fields.Char(
        string='Category Password',
        required=True
    )

    def action_verify(self):
        self.ensure_one()

        credential = self.password_id

        valid = False

        for category in credential.category_ids:
            if self.login_password == category.category_password:
                valid = True
                break

        if not valid:
            raise ValidationError(
                "Invalid Category Password."
            )

        return credential._show_password_wizard()