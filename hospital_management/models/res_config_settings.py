from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    appointment_duration = fields.Integer(
        related="company_id.appointment_duration",
        readonly=False
    )

    reminder_days = fields.Integer(
        related="company_id.reminder_days",
        readonly=False
    )
    max_appointment_duration = fields.Integer(
        related="company_id.max_appointment_duration",
        readonly=False
    )