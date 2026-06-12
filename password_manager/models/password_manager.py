from odoo import models, fields, api
from odoo.exceptions import AccessError, ValidationError, UserError
from dateutil.relativedelta import relativedelta
import secrets
import string
from cryptography.fernet import Fernet, InvalidToken
import logging

_logger = logging.getLogger(__name__)

class PasswordManager(models.Model):
    _name = 'password.manager'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Password Manager'
    _rec_name = 'name'
    name = fields.Char(required=True)
    credential_type_id = fields.Many2one('password.credential.type', string='Credential Type')
    category_ids = fields.Many2many('password.category', string='Categories', required=True)
    username = fields.Char()
    password_type = fields.Selection([('manual', 'Manual'),('generate', 'Generate'),
    ], string='Password Type', default='manual', required=True)
    password = fields.Text(string='Password', required=True)
    url = fields.Char()
    notes = fields.Text()
    owner_id = fields.Many2one('res.users', default=lambda self: self.env.user, required=True)
    access_ids = fields.One2many('password.access', 'password_id', string='Access Rights')
    state = fields.Selection([('draft', 'Draft'),('confirmed', 'Confirmed'),
        ('expired', 'Expired'),], string='Status', default='draft', tracking=True)
    expiry_date = fields.Date()
    active = fields.Boolean(default=True)
    rotation_days = fields.Integer(string='Rotation Days', default=0)
    rotation_date = fields.Date(string='Next Rotation Date')
    allowed_user_ids = fields.Many2many('res.users',compute='_compute_allowed_users',store=True)
    duplicate_count = fields.Integer(compute="_compute_duplicate_count",store=False,search="_search_duplicate_count")
    rotation_overdue = fields.Boolean(compute='_compute_rotation_overdue',store=True)

    @api.depends('rotation_date', 'state')
    def _compute_rotation_overdue(self):
        today = fields.Date.today()
        for rec in self:
            rec.rotation_overdue = (
                rec.state == 'confirmed'
                and rec.rotation_date
                and rec.rotation_date < today)
    def _search_duplicate_count(self, operator, value):
        if operator not in ('=', '!=', '>', '>=', '<', '<='):
            raise UserError("Unsupported operator for duplicate count search.")
        
        query = """
            SELECT name, username, credential_type_id
            FROM password_manager
            WHERE active = true
            GROUP BY name, username, credential_type_id
            HAVING COUNT(id) > 1
        """
        self.env.cr.execute(query)
        res = self.env.cr.dictfetchall()        
        domain = []
        for r in res:
            domain.append([('name', '=', r['name']),('username', '=', r['username']),
                ('credential_type_id', '=', r['credential_type_id'])])        
        if not domain:
            return [('id', '=', False)]            
        or_domain = ['|'] * (len(domain) - 1)
        for d in domain:
            or_domain.extend(d)            
        return or_domain

    @api.depends('name', 'username', 'credential_type_id', 'active')
    def _compute_duplicate_count(self):
        for rec in self:
            rec.duplicate_count = 0
        active_records = self.filtered(lambda r: r.active and r.name)
        if not active_records:
            return
        self.env.cr.execute("""SELECT name,username,credential_type_id,COUNT(*) as total
            FROM password_manager
            WHERE active = TRUE
            GROUP BY name,username,credential_type_id
            HAVING COUNT(*) > 1
        """)

        duplicate_map = {(row['name'],row['username'],row['credential_type_id']): row['total']
            for row in self.env.cr.dictfetchall()
        }
        for rec in active_records:
            key = (rec.name,rec.username,rec.credential_type_id.id)
            rec.duplicate_count = max(duplicate_map.get(key, 0) - 1,0)

    @api.depends('owner_id', 'access_ids.user_id', 'access_ids.group_id', 'access_ids.department_id', 'access_ids.active', 'access_ids.access_until')
    def _compute_allowed_users(self):
        for rec in self:
            users = rec.owner_id
            for access in rec.access_ids:
                if not access.active or (access.access_until and access.access_until <= fields.Datetime.now()):
                    continue
                if access.user_id:
                    users |= access.user_id
                if access.group_id:
                    users |= access.group_id.user_ids
                if access.department_id:
                    employees = self.env['hr.employee'].sudo().search([('department_id', '=', access.department_id.id)])
                    users |= employees.mapped('user_id')
            rec.allowed_user_ids = users

    def _get_cipher(self):
        key = self.env['ir.config_parameter'].sudo().get_param('password_manager.encryption_key')
        if not key:
            raise UserError('System Configuration Error: Encryption key missing. Please contact administrator.')
        return Fernet(key.encode())

    @api.model
    def cron_rotation_reminder(self):
        reminder_days = int(self.env['ir.config_parameter'].sudo().get_param('password_manager.rotation_reminder_days', 3))
        records = self.search([('state', '=', 'confirmed'), ('rotation_date', '!=', False)])
        for rec in records:
            remaining_days = (rec.rotation_date - fields.Date.today()).days
            if remaining_days == reminder_days:
                rec.message_post(body=f'Password rotation is due in {remaining_days} day(s). Please update the password.')                
                existing_activity = self.env['mail.activity'].search([
                    ('res_model', '=', 'password.manager'),('res_id', '=', rec.id),
                    ('user_id', '=', rec.owner_id.id),('summary', '=', 'Password Rotation Reminder'),], limit=1)
                if not existing_activity:
                    rec.activity_schedule('mail.mail_activity_data_todo',user_id=rec.owner_id.id,
                        summary='Password Rotation Reminder',note=f'Password "{rec.name}" needs rotation in {remaining_days} day(s).')
                    
    @api.model
    def cron_password_reminder(self):        
        reminder_days = int(self.env['ir.config_parameter'].sudo().get_param('password_manager.password_reminder_days', 5))
        records = self.search([('state', '=', 'confirmed'), ('expiry_date', '!=', False)])
        for rec in records:
            remaining_days = (rec.expiry_date - fields.Date.today()).days
            if remaining_days == reminder_days:
                rec.message_post(body=f'Password "{rec.name}" will expire in {remaining_days} day(s).')

    def _encrypt_password(self, password):
        if not password:
            return ''
        return self._get_cipher().encrypt(password.encode()).decode()

    def _decrypt_password(self):
        self.ensure_one()
        if not self.password:
            return ''
        try:
            return self._get_cipher().decrypt(self.password.encode()).decode()
        except InvalidToken:
            _logger.exception("Password decryption failed for credential ID %s",self.id)
            raise UserError("Unable to decrypt this password. Please contact your administrator.")

        except Exception:
            _logger.exception("Unexpected decryption error for credential ID %s",self.id)
            raise UserError("An unexpected error occurred while decrypting the password.")
    
    def _calculate_rotation_date(self, days):
        if days > 0:
            return fields.Date.today() + relativedelta(days=days)
        return False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('password_type') == 'generate' and not vals.get('password'):
                vals['password'] = self._generate_password()
            if vals.get('password'):
                vals['password'] = self._encrypt_password(vals['password'])
        records = super().create(vals_list)
        for rec in records:
            rec.message_post(body='Credential created')
        return records
    
    def action_generate_password_preview(self):
        return True

    def write(self, vals):
        _logger.warning("WRITE VALS = %s", vals)
        for rec in self:
            if set(vals.keys()) == {'state'}:
                continue
            rec._check_password_access('write')
            editable_fields = {'password'}
            changed_fields = set(vals.keys()) - editable_fields
            _logger.warning("STATE=%s CHANGED_FIELDS=%s VALS=%s",rec.state,changed_fields,vals)

            if changed_fields and rec.state != 'draft':
                raise AccessError('Credential can only be modified in Draft state.' )
        password_changed = 'password' in vals
        if password_changed and vals.get('password'):
            vals['password'] = self._encrypt_password(vals['password'])
        result = super().write(vals)
        if password_changed:
            for rec in self:
                rec.message_post(body='Password changed')
        return result
    
    def _get_employee_department_id(self, user):
        employee = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        return employee.department_id.id if employee else False

    def _get_access_lines(self, user):
        employee_department_id = self._get_employee_department_id(user)
        return self.access_ids.filtered(lambda x: 
            (x.user_id and x.user_id == user) or
            (x.group_id and x.group_id in user.group_ids) or 
            (x.department_id and employee_department_id and x.department_id.id == employee_department_id))
    
    def _has_permission(self, access_line, permission):
        permission_map = {'read': access_line.can_read,'write': access_line.can_write,'share': access_line.can_share,}
        return permission_map.get(permission, False)
            
    def _check_password_access(self, permission='read'):
        self.ensure_one()
        user = self.env.user
        if self.owner_id == user:
            return True
        if permission == 'read' and self.state == 'draft':
            raise AccessError('Credential is still in Draft state.')
        if self.state == 'expired':
            raise AccessError('Credential has expired.')
        access = self._get_access_lines(user)
        if not access:
            raise AccessError('You are not allowed to access this password.')
        for access_line in access:
            if not access_line.active:
                continue
            if access_line.access_until and access_line.access_until <= fields.Datetime.now():
                continue
            if self._has_permission(access_line, permission):
                return True
        raise AccessError('Permission denied.')
    
    def action_show_password(self):
        self.ensure_one()
        if (self.owner_id != self.env.user and self.expiry_date and self.expiry_date <= fields.Date.today()):
            raise AccessError('This credential has expired.')

        self._check_password_access('read')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Verify Password',
            'res_model': 'password.verify.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_password_id': self.id}
        }
    
    def _show_password_wizard(self):
        self.ensure_one()
        password = self._decrypt_password()

        self.message_post(body='Password viewed')
        timeout = int(self.env['ir.config_parameter'].sudo().get_param('password_manager.password_view_timeout', 10))
        
        wizard = self.env['password.view.wizard'].create({'password': password, 'timeout_seconds': timeout})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Password',
            'res_model': 'password.view.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'auto_close_timeout': timeout}
        }

    @api.model
    def cron_expire_passwords(self):
        records = self.search([('state', '=', 'confirmed'), ('expiry_date', '<', fields.Date.today())])
        records.write({'state': 'expired'})

    def _change_state(self, state, message):
        self.ensure_one()
        self._check_password_access('write')
        self.write({'state': state})
        self.message_post(body=message)
        
    def action_confirm(self):
        self.ensure_one()
        self._check_password_access('write')
        vals = {'state': 'confirmed','rotation_date': False,}
        if self.rotation_days > 0:
            vals['rotation_date'] = (fields.Date.today() + relativedelta(days=self.rotation_days))
        self.write(vals)
                    
    def action_set_draft(self):
        self._change_state('draft', 'Credential moved to draft')

    @api.constrains('expiry_date', 'rotation_date')
    def _check_rotation_date(self):
        for rec in self:
            if rec.expiry_date and rec.rotation_date and rec.rotation_date > rec.expiry_date:
                raise ValidationError('Rotation date cannot be greater than expiry date.')
            
    @api.constrains('expiry_date', 'rotation_days')
    def _check_rotation_days(self):
        for rec in self:
            if rec.expiry_date and rec.rotation_days:
                rotation_date = fields.Date.today() + relativedelta(days=rec.rotation_days)
                if rotation_date > rec.expiry_date:
                    raise ValidationError(
                        'Rotation date cannot be greater than expiry date.'
                    )
                
    @api.model
    def _generate_password(self):
        params = self.env['ir.config_parameter'].sudo()
        length = int(params.get_param('password_manager.password_length', 16))
        require_uppercase = (params.get_param('password_manager.require_uppercase', 'False') == 'True')
        require_lowercase = (params.get_param('password_manager.require_lowercase', 'False') == 'True')
        require_numbers = (params.get_param('password_manager.require_numbers', 'False') == 'True')
        require_special = (params.get_param('password_manager.require_special', 'False') == 'True')
        
        password_list = []
        all_chars = ''
        if require_uppercase:
            password_list.append(secrets.choice(string.ascii_uppercase))
            all_chars += string.ascii_uppercase
        if require_lowercase:
            password_list.append(secrets.choice(string.ascii_lowercase))
            all_chars += string.ascii_lowercase
        if require_numbers:
            password_list.append(secrets.choice(string.digits))
            all_chars += string.digits
        if require_special:
            password_list.append(secrets.choice('!@#$%^&*()'))
            all_chars += '!@#$%^&*()'

        if not all_chars:
            raise UserError('Configuration Error: Please enable at least one password policy.')

        if length < len(password_list):
            length = len(password_list)

        while len(password_list) < length:
            password_list.append(secrets.choice(all_chars))

        secrets.SystemRandom().shuffle(password_list)
        return ''.join(password_list)
    
    def action_generate_password(self):
        self.ensure_one()
        self._check_password_access('write')
        new_password = self._generate_password()
        self.write({
            'password': new_password,
        })
    
    def action_edit_password(self):
        self.ensure_one()
        self._check_password_access('write')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Password',
            'res_model': 'password.change.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_password_id': self.id}
        }
    
    def unlink(self):
        for rec in self:

            if rec.state != 'draft':
                raise UserError(
                    "You cannot delete a confirmed or expired credential. "
                    "You must first set it to Draft state."
                )
            rec._check_password_access('delete')

        return super().unlink()