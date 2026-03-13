from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    appointment_duration = fields.Integer(
        string="Appointment Duration",
        default=30
    )

    reminder_days = fields.Integer(
        string="Reminder Days",
        default=1
    )
    max_appointment_duration = fields.Integer(
        string="Max Appointment Duration (minutes)",
        default=90
    )

    