from odoo import models, fields, api
from cryptography.fernet import Fernet
from odoo.exceptions import AccessError
from odoo.fields import Datetime
from odoo.fields import Date
import random
import string


class PasswordManager(models.Model):
    _name = 'password.manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Password Manager'
    _rec_name = 'name'
    name = fields.Char(required=True)
    credential_type_id = fields.Many2one('password.credential.type', string='Credential Type')
    category_ids = fields.Many2many('password.category',string='Categories')
    username = fields.Char()
    password = fields.Text(string='Password')
    url = fields.Char()
    notes = fields.Text()
    owner_id = fields.Many2one('res.users',default=lambda self: self.env.user)
    access_ids = fields.One2many('password.access','password_id',string='Access Rights')
    state = fields.Selection(
        [('draft', 'Draft'),('confirmed', 'Confirmed'),('expired', 'Expired'),('archived', 'Archived'),],
        string='Status',default='draft')
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
                vals['password'] = self._encrypt_password(vals.get('password'))

        records = super().create(vals_list)
        for rec in records:
            rec.message_post(body='Credential created')

        return records

    def write(self, vals):
        if 'state' not in vals:
            for rec in self:
                rec._check_password_access('write')
        password_changed = 'password' in vals
        if password_changed:
            vals['password'] = self._encrypt_password(vals.get('password'))

        result = super().write(vals)
        for rec in self:
            if password_changed:
                rec.message_post(body='Password changed')
            else:
                rec.message_post(body='Credential updated')

        return result
        
    def _check_password_access(self, permission='read'):
        self.ensure_one()
        user = self.env.user

        if self.state == 'draft':
            if self.owner_id != user:
                raise AccessError('Credential is still in Draft state.')
            return True

        if self.state == 'archived':
            raise AccessError('Credential has been archived.')

        if self.state == 'expired':
            raise AccessError('Credential has expired.')

        if self.owner_id == user:
            return True

        employee = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)],limit=1)
        employee_department_id = (employee.department_id.id if employee else False)
        access = self.access_ids.filtered(
            lambda x:(x.user_id and x.user_id == user) or (x.group_id and x.group_id in user.group_ids)
                or( x.department_id and employee_department_id and x.department_id.id == employee_department_id))

        if not access:
            raise AccessError('You are not allowed to access this password.')

        for access_line in access:

            if not access_line.active:
                continue

            if (access_line.access_until and access_line.access_until <= Datetime.now()):
                continue

            if permission == 'read' and access_line.can_read:
                return True

            if permission == 'write' and access_line.can_write:
                return True

            if permission == 'delete' and access_line.can_delete:
                return True

            if permission == 'share' and access_line.can_share:
                return True

        raise AccessError('Permission denied.')
    
    def action_show_password(self):
        self.ensure_one()
        if (self.expiry_date and self.expiry_date <= Date.today()):
            self.write({'state': 'expired'})

            raise AccessError('This credential has expired.')

        self._check_password_access()
        self.message_post( body='Password viewed' )
        password = self._decrypt_password()

        return {'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': {'title': 'Password', 'message': password,}}
    
    # @api.onchange('expiry_date')
    # def _onchange_expiry_date(self):
    #     if (self.expiry_date and self.expiry_date < Date.today()):
    #         self.state = 'expired'

    @api.model
    def cron_expire_passwords(self):
        records = self.search([('state', '=', 'confirmed'),('expiry_date', '<', Date.today())])
        records.write({'state': 'expired' })

    def action_confirm(self):
        self.state = 'confirmed'
        self.message_post(body='Credential confirmed')

    def action_archive(self):        
        self.state = 'archived'
        self.message_post(body='Credential archived')

    def action_set_draft(self):
        self.state = 'draft'

    def _generate_password(self):

        params = self.env['ir.config_parameter'].sudo()
        length = int(params.get_param('password_manager.password_length',16))
        require_uppercase = (params.get_param('password_manager.require_uppercase','False') == 'True')
        require_lowercase = (params.get_param('password_manager.require_lowercase','False') == 'True')
        require_numbers = (params.get_param('password_manager.require_numbers','False') == 'True')
        require_special = (params.get_param('password_manager.require_special','False') == 'True')
        password_list = []
        all_chars = ''

        if require_uppercase:
            password_list.append(random.choice(string.ascii_uppercase))
            all_chars += string.ascii_uppercase

        if require_lowercase:
            password_list.append(random.choice(string.ascii_lowercase))
            all_chars += string.ascii_lowercase

        if require_numbers:
            password_list.append(random.choice(string.digits))
            all_chars += string.digits

        if require_special:
            password_list.append(random.choice('!@#$%^&*()'))
            all_chars += '!@#$%^&*()'

        if not all_chars:
            raise AccessError('Please enable at least one password policy.' )

        if length < len(password_list):
            length = len(password_list)

        while len(password_list) < length:
            password_list.append(random.choice(all_chars))

        random.shuffle(password_list)
        return ''.join(password_list)
    
    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        result['password'] = self._generate_password()
        return result
    
    def action_edit_password(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Password',
            'res_model': 'password.change.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_password_id': self.id,
            }
        }