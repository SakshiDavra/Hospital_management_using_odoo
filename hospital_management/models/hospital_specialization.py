from odoo import models, fields


class HospitalSpecialization(models.Model):
    _name = 'hospital.specialization'
    _description = 'Doctor Specialization'

    name = fields.Char(string="Specialization", required=True)
    description = fields.Text(string="Description")