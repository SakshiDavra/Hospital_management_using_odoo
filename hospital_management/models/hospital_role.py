from odoo import models, fields

class HospitalRole(models.Model):
    _name = "hospital.role"
    _description = "Hospital Role"
    
    name = fields.Char(string="Role Name", required=True)