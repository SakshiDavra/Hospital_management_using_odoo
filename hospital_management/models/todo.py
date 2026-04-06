from odoo import models, fields

class HospitalTodo(models.Model):
    _name = 'hospital.todo'
    _description = 'Hospital Todo'

    name = fields.Char(string="Task", required=True)
    is_done = fields.Boolean(string="Done")