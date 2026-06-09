from odoo import models, fields


class PasswordCategory(models.Model):
    _name = 'password.category'
    _description = 'Password Category'
    _rec_name = 'name'
    name = fields.Char(string='Category Name',required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    category_password = fields.Char(
        string="Category Password",
        required=True
    )