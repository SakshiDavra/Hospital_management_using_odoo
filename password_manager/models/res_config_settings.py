from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    password_length = fields.Integer(
        string='Password Length',
        config_parameter='password_manager.password_length',
        default=16
    )

    require_uppercase = fields.Boolean(string='Require Uppercase',config_parameter='password_manager.require_uppercase')
    require_lowercase = fields.Boolean(string='Require Lowercase',config_parameter='password_manager.require_lowercase')
    require_numbers = fields.Boolean(string='Require Numbers',config_parameter='password_manager.require_numbers')
    require_special = fields.Boolean(string='Require Special Characters',config_parameter='password_manager.require_special')