from odoo import models, fields


class PasswordAccess(models.Model):
    _name = 'password.access'

    password_id = fields.Many2one(
        'password.manager'
    )

    user_id = fields.Many2one(
        'res.users'
    )

    group_id = fields.Many2one(
        'res.groups'
    )

    department_id = fields.Many2one(
        'hr.department'
    )

    can_read = fields.Boolean()
    can_write = fields.Boolean()
    can_delete = fields.Boolean()
    can_share = fields.Boolean()