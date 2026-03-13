from odoo import models, fields


class AppointmentStatus(models.Model):
    _name = "hospital.appointment.status"
    _description = "Appointment Status"

    name = fields.Char(string="Status", required=True)
    code = fields.Char(string="Code", required=True)