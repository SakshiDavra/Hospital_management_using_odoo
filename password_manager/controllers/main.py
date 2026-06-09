from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError


class PasswordPortal(http.Controller):
    @http.route('/my/passwords', type='http', auth='user', website=True)
    def portal_my_passwords(self, **kw):

        if request.env.user._is_admin():
            passwords = request.env['password.manager'].sudo().search([('active', '=', True)])
        else:
            passwords = request.env['password.manager'].sudo().search([
                ('allowed_user_ids', 'in', request.env.user.id),('active', '=', True)])

        timeout = int(
            request.env['ir.config_parameter'].sudo().get_param('password_manager.password_view_timeout', 10))

        return request.render(
            'password_manager.portal_my_passwords',
            {'passwords': passwords,
             'timeout_seconds': timeout,
             'page_name': 'passwords',}
        )

    @http.route('/my/password/verify', type='json', auth='user', website=True)
    def verify_password(self, password_id, login_password):

        credential = request.env['password.manager'].sudo().browse(int(password_id))

        if not credential.exists():
            return {'success': False,'error': 'Credential not found.'}
        try:
            credential._check_password_access('read')
        except AccessError as error:
            return {
                'success': False,
                'error': str(error)
            }

        valid = any(login_password == category.category_password
            for category in credential.category_ids
        )

        if not valid:
            return {
                'success': False,
                'error': 'Invalid Category Password.'
            }
        credential.message_post(body='Password viewed from portal')
        timeout = int(request.env['ir.config_parameter'].sudo().get_param('password_manager.password_view_timeout', 10))

        return {'success': True,'password': credential._decrypt_password(),'timeout': timeout,}
    
    @http.route('/my/password/<int:password_id>',type='http',auth='user',website=True)
    def portal_password_form(self, password_id, **kw):

        password = request.env['password.manager'].sudo().browse(password_id)
        if not password.exists():
            return request.not_found()
        try:
            password._check_password_access('read')
        except AccessError:
            return request.redirect('/my/passwords')
        if request.env.user._is_admin():
            passwords = request.env['password.manager'].sudo().search([('active', '=', True)])

        else:
            passwords = request.env['password.manager'].sudo().search([
                ('allowed_user_ids', 'in', request.env.user.id),('active', '=', True)])
        password_ids = passwords.ids
        try:
            current_index = password_ids.index(password.id)
        except ValueError:
            current_index = 0
        prev_record = (passwords[current_index - 1]
            if current_index > 0
            else False
        )
        next_record = ( passwords[current_index + 1]
            if current_index < len(passwords) - 1
            else False
        )
        timeout = int( request.env['ir.config_parameter'].sudo().get_param('password_manager.password_view_timeout',10))
    
        return request.render('password_manager.portal_password_form',
            {
                'password': password,
                'timeout_seconds': timeout,
                'page_name': 'password',
                'page_view': 'password',

                # 'prev_record': prev_record,
                # 'next_record': next_record,

                # 'prev_record_href':
                #     '/my/password/%s' % prev_record.id
                #     if prev_record else False,

                # 'next_record_href':
                #     '/my/password/%s' % next_record.id
                #     if next_record else False,
            }
        )
    

    @http.route('/my/password/new',type='http',auth='user',website=True)
    def portal_new_password(self, **kw):

        credential_types = request.env['password.credential.type'].sudo().search([])

        categories = request.env['password.category'].sudo().search([])

        return request.render('password_manager.portal_create_password',
            {'credential_types': credential_types,
                'categories': categories,
                'page_name': 'password_create',}
        )

    @http.route('/my/password/create',type='http',auth='user',website=True,methods=['POST'],csrf=True)
    def portal_create_password(self, **post):
        credential_types = request.env['password.credential.type'].sudo().search([])
        categories = request.env['password.category'].sudo().search([])
        vals = {
            'name': post.get('name'),
            'credential_type_id': int(post.get('credential_type_id'))
                if post.get('credential_type_id') else False,
            'username': post.get('username'),
            'password_type': post.get('password_type', 'manual'),
            'url': post.get('url'),
            'notes': post.get('notes'),
            'expiry_date': post.get('expiry_date') or False,
            'rotation_days': int(post.get('rotation_days') or 0),
            'owner_id': request.env.user.id,
            'state': 'draft',
        }

        duplicate = request.env['password.manager'].sudo().search_count([
            ('name', '=', vals['name']),('username', '=', vals.get('username') or False),
            ('credential_type_id', '=', vals['credential_type_id']),('active', '=', True),])

        if duplicate:
            return request.render('password_manager.portal_create_password',
                {'credential_types': credential_types,
                    'categories': categories,
                    'error': 'Duplicate credential found.', }
            )

        category_ids = request.httprequest.form.getlist('category_ids')
        if category_ids:
            vals['category_ids'] = [(6, 0, [int(x) for x in category_ids])]
        password_value = post.get('password')
        if not password_value:
            password_value = request.env['password.manager'].sudo()._generate_password()
        vals['password'] = password_value

        password = request.env['password.manager' ].sudo().create(vals)

        return request.redirect( '/my/password/%s' % password.id)
    
    @http.route('/my/password/<int:password_id>/confirm',type='http',auth='user',website=True)
    def portal_confirm_password(self, password_id,**kw):

        password = request.env['password.manager'].sudo().browse(password_id)

        if password.owner_id != request.env.user:
            return request.redirect('/my/passwords')

        password.action_confirm()

        return request.redirect('/my/password/%s' % password.id)
    
    @http.route('/my/password/generate',type='json',auth='user', website=True)
    def portal_generate_password(self):
        return {'password': request.env[
                'password.manager'].sudo()._generate_password()}
    
    @http.route( '/my/password/<int:password_id>/edit_detail',type='http',auth='user',website=True)
    def portal_edit_detail(self,password_id,**kw):

        password = request.env['password.manager'].sudo().browse(password_id)

        if not password.exists():
            return request.not_found()

        if password.owner_id != request.env.user:
            return request.redirect('/my/passwords')

        credential_types = request.env['password.credential.type'].sudo().search([])

        categories = request.env['password.category'].sudo().search([])

        return request.render('password_manager.portal_create_password',
            {'password': password,
                'credential_types': credential_types,
                'categories': categories,
                'edit_mode': True,
                'page_name': 'password_edit',}
        )
    
    @http.route('/my/password/<int:password_id>/update_detail',type='http',auth='user',website=True,methods=['POST'],csrf=True)
    def portal_update_detail(self, password_id, **post):
        password = request.env['password.manager'].sudo().browse(password_id)
        if not password.exists():
            return request.not_found()

        if password.owner_id != request.env.user:
            return request.redirect('/my/passwords')
        vals = {
            'name': post.get('name'),
            'credential_type_id': int(post.get('credential_type_id'))
                if post.get('credential_type_id') else False,
            'username': post.get('username'),
            'url': post.get('url'),
            'notes': post.get('notes'),
            'expiry_date': post.get('expiry_date') or False,
            'rotation_days': int(post.get('rotation_days') or 0),
            'password_type': post.get('password_type', 'manual'),
        }

        category_ids = request.httprequest.form.getlist('category_ids')
        vals['category_ids'] = [(6, 0, [int(x) for x in category_ids])]
        password.write(vals)
        return request.redirect('/my/password/%s' % password.id)
    
    @http.route('/my/password/generate',type='json',auth='user')
    def portal_generate_password(self):

        return {'password':request.env['password.manager'].sudo()._generate_password()}
    
    @http.route('/my/password/update_password',type='json',auth='user',website=True)
    def portal_update_password(self,password_id,current_password,new_password):
        password = request.env['password.manager'].sudo().browse(int(password_id))
        if not password.exists():
            return {'success': False,'error': 'Password not found'}
        try:
            password._check_password_access('write')
        except AccessError as e:
            return {'success': False,'error': str(e)}
        real_password = password._decrypt_password()
        if current_password != real_password:
            return {'success': False,'error': 'Current password is incorrect'}
        password.write({'password': new_password,})
        return {'success': True}