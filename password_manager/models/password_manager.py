from odoo import models, fields, api
from cryptography.fernet import Fernet
from odoo.exceptions import AccessError


class PasswordManager(models.Model):
    _name = 'password.manager'
    _description = 'Password Manager'
    _rec_name = 'name'

    name = fields.Char(required=True)
    credential_type_id = fields.Many2one('password.credential.type', string='Credential Type')
    category_ids = fields.Many2many('password.category',string='Categories')
    username = fields.Char()
    password = fields.Text(string='Encrypted Password')
    url = fields.Char()
    notes = fields.Text()
    owner_id = fields.Many2one('res.users',default=lambda self: self.env.user)
    access_ids = fields.One2many(
        'password.access',
        'password_id',
        string='Access Rights'
    )
    expiry_date = fields.Date()
    active = fields.Boolean(default=True)

    def _encrypt_password(self, password):

        key = b'7d6N5sX3vJ1mK2rL8pQ9wT4yU0aBzCDeFgHiJkLmNo0='
        cipher = Fernet(key)

        return cipher.encrypt(password.encode()).decode()

    def _decrypt_password(self):

        key = b'7d6N5sX3vJ1mK2rL8pQ9wT4yU0aBzCDeFgHiJkLmNo0='
        cipher = Fernet(key)

        if self.password:
            return cipher.decrypt(self.password.encode()).decode()

        return ''

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('password'):
                vals['password'] = (self._encrypt_password(vals.get('password'))
                )
        return super().create(vals_list)

    def write(self, vals):
        for rec in self:
            rec._check_password_access('write')
        if vals.get('password'):
            vals['password'] = (
                self._encrypt_password(
                    vals.get('password')
                )
            )
        return super().write(vals)
    
    def _check_password_access(self, permission='read'):

        self.ensure_one()

        user = self.env.user

        if self.owner_id == user:
            return True

        employee = self.env['hr.employee'].search([('user_id', '=', user.id)],limit=1 )

        access = self.access_ids.filtered(
            lambda x:(x.user_id and x.user_id == user) or (x.group_id and x.group_id in user.groups_id) or
                (x.department_id and employee and x.department_id == employee.department_id)
        )

        if not access:
            raise AccessError('You are not allowed to access this password.')

        for access_line in access:
            if permission == 'read' and access_line.can_read:
                return True

            if permission == 'write' and access_line.can_write:
                return True

            if permission == 'delete' and access_line.can_delete:
                return True

            if permission == 'share' and access_line.can_share:
                return True

        raise AccessError(
            'Permission denied.'
        )

    def action_show_password(self):

        self.ensure_one()

        self._check_password_access()

        password = self._decrypt_password()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Password',
                'message': password,
            }
        }