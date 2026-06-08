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

    password_reminder_days = fields.Integer(
        string='Reminder Before Expiry (Days)',
        default=5,
        config_parameter='password_manager.password_reminder_days'
    )
    rotation_reminder_days = fields.Integer(
        string='Rotation Reminder Before (Days)',
        default=3,
        config_parameter='password_manager.rotation_reminder_days'
    )
    encryption_key = fields.Char(
        string='Encryption Key',
        config_parameter='password_manager.encryption_key'
    )
    password_view_timeout = fields.Integer(
        string="Password View Timeout (Seconds)",
        config_parameter='password_manager.password_view_timeout',
        default=10
    )