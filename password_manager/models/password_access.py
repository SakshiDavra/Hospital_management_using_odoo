from odoo import models, fields, api
from odoo.exceptions import AccessError

class PasswordAccess(models.Model):
    _name = 'password.access'
    _description = 'Password Access'
    access_until = fields.Datetime(string='Access Until')
    active = fields.Boolean(default=True)
    password_id = fields.Many2one('password.manager')
    user_id = fields.Many2one('res.users')
    group_id = fields.Many2one('res.groups')
    department_id = fields.Many2one('hr.department')
    can_read = fields.Boolean()
    can_write = fields.Boolean()
    can_delete = fields.Boolean()
    can_share = fields.Boolean()

    def _check_access_rights_permission(self, password):

        if password.state != 'draft':
            raise AccessError(
                'Access Rights can only be modified when credential is in Draft state.'
            )
        # Owner
        if password.owner_id == self.env.user:
            return True

        # User has write permission on this credential
        password._check_password_access('write')

        return True

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            password = self.env['password.manager'].browse(
                vals.get('password_id')
            )

            self._check_access_rights_permission(password)

        return super().create(vals_list)

    def write(self, vals):

        for rec in self:
            self._check_access_rights_permission(rec.password_id)

        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.password_id.owner_id != self.env.user:
                raise AccessError('Only credential owner can remove access rights.')
        return super().unlink()