from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

class PasswordPortal(CustomerPortal):


    def _get_timeout(self):
        """Helper to get password view timeout config parameter."""
        param_obj = request.env['ir.config_parameter'].sudo()
        return int(param_obj.get_param('password_manager.password_view_timeout', 10))

    def _get_password_record(self, password_id, access_type='read', return_json=False):
        """
        Helper to fetch password record and validate access.
        Returns (record, error_response) tuple.
        """
        password = request.env['password.manager'].browse(int(password_id))
        
        if not password.exists():
            if return_json:
                return False, {'success': False, 'error': 'Password not found.'}
            return False, request.not_found()

        try:
            password._check_password_access(access_type)
        except AccessError as error:
            if return_json:
                return False, {'success': False, 'error': str(error)}
            if access_type == 'write':
                # For write access failures in UI, often redirect back to list
                return False, request.redirect('/my/passwords')
            return False, request.redirect('/my/passwords')

        return password, False

    def _prepare_password_vals(self, post):
        """Helper to structure vals dictionary for create and write methods."""
        vals = {
            'name': post.get('name'),
            'credential_type_id': int(post.get('credential_type_id')) if post.get('credential_type_id') else False,
            'username': post.get('username'),
            'url': post.get('url'),
            'notes': post.get('notes'),
            'expiry_date': post.get('expiry_date') or False,
            'rotation_days': int(post.get('rotation_days') or 0),
            'password_type': post.get('password_type', 'manual'),
        }
        
        category_ids = request.httprequest.form.getlist('category_ids')

        vals['category_ids'] = [(6, 0, [int(x) for x in category_ids])]
            
        return vals

    def _get_searchbar_filters(self):
        return {
            'all': {'label': 'All', 'domain': []},
            'draft': {'label': 'Draft', 'domain': [('state', '=', 'draft')]},
            'confirmed': {'label': 'Confirmed', 'domain': [('state', '=', 'confirmed')]},
            'expired': {'label': 'Expired', 'domain': [('state', '=', 'expired')]},
        }

    def _get_searchbar_inputs(self):
        return {
            'all': {'input': 'all', 'label': 'Search All'},
            'name': {'input': 'name', 'label': 'Name'},
            'username': {'input': 'username', 'label': 'Username'},
            'credential_type': {'input': 'credential_type', 'label': 'Credential Type'},
            'category': {'input': 'category', 'label': 'Category'},
            'owner': {'input': 'owner', 'label': 'Owner'},
            'state': {'input': 'state', 'label': 'Status'},
        }

    def _get_search_domain(self, search_in, search):
        if search_in == 'name':
            return [('name', 'ilike', search)]
        elif search_in == 'username':
            return [('username', 'ilike', search)]
        elif search_in == 'credential_type':
            return [('credential_type_id.name', 'ilike', search)]
        elif search_in == 'category':
            return [('category_ids.name', 'ilike', search)]
        elif search_in == 'owner':
            return [('owner_id.name', 'ilike', search)]
        elif search_in == 'state':
            return [('state', 'ilike', search)]
        else:
            return [
                '|', '|', '|', '|', '|',
                ('name', 'ilike', search),
                ('username', 'ilike', search),
                ('credential_type_id.name', 'ilike', search),
                ('category_ids.name', 'ilike', search),
                ('owner_id.name', 'ilike', search),
                ('state', 'ilike', search),
            ]

    @http.route(['/my/passwords', '/my/passwords/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_passwords(self, page=1, filterby='all', search=None, search_in='all', **kw):
        Password = request.env['password.manager']
        searchbar_filters = self._get_searchbar_filters()
        searchbar_inputs = self._get_searchbar_inputs()
        
        domain = [('active', '=', True)]

        if not request.env.user._is_admin():
            domain += [
                '|',
                ('state', '!=', 'draft'),
                ('owner_id', '=', request.env.user.id),
            ]
            
        domain += searchbar_filters.get(filterby, searchbar_filters['all'])['domain']

        if search:
            domain += self._get_search_domain(search_in, search)
            
        total = Password.search_count(domain)
        pager = portal_pager(
            url="/my/passwords",
            url_args={'filterby': filterby, 'search': search, 'search_in': search_in},
            total=total, page=page, step=10
        )

        passwords = Password.search(domain, order='create_date desc', limit=10, offset=pager['offset'])
        timeout = self._get_timeout()

        values = {
            'passwords': passwords,
            'pager': pager,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'filterby': filterby,
            'search': search,
            'search_in': search_in,
            'default_url': '/my/passwords',
            'timeout_seconds': timeout,
            'page_name': 'passwords',
        }
        return request.render('password_manager.portal_my_passwords', values)

    @http.route('/my/password/verify', type='json', auth='user', website=True)
    def verify_password(self, password_id, login_password):
        credential, error_response = self._get_password_record(password_id, access_type='read', return_json=True)
        if error_response:
            return error_response

        valid = any(login_password == category.category_password for category in credential.category_ids)
        if not valid:
            return {'success': False, 'error': 'Invalid Category Password.'}

        credential.message_post(body='Password viewed from portal')
        return {
            'success': True,
            'password': credential._decrypt_password(),
            'timeout': self._get_timeout(),
        }

    @http.route('/my/password/<int:password_id>', type='http', auth='user', website=True)
    def portal_password_form(self, password_id, **kw):
        password, error_redirect = self._get_password_record(password_id, access_type='read')
        if error_redirect:
            return error_redirect

        try:
            password._check_password_access('write')
            can_write = True
        except AccessError:
            can_write = False

        return request.render('password_manager.portal_password_form', {
            'password': password,
            'timeout_seconds': self._get_timeout(),
            'page_name': 'password',
            'page_view': 'password',
            'can_write': can_write,
        })

    @http.route('/my/password/new', type='http', auth='user', website=True)
    def portal_new_password(self, **kw):
        return request.render('password_manager.portal_create_password', {
            'credential_types': request.env['password.credential.type'].sudo().search([]),
            'categories': request.env['password.category'].sudo().search([]),
            'page_name': 'password_create',
        })

    @http.route('/my/password/create', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_create_password(self, **post):
        vals = self._prepare_password_vals(post)
        vals.update({
            'owner_id': request.env.user.id,
            'state': 'draft',
        })

        if not post.get('password'):
            vals['password'] = request.env['password.manager']._generate_password()
        else:
            vals['password'] = post.get('password')

        password = request.env['password.manager'].create(vals)
        return request.redirect('/my/password/%s' % password.id)

    @http.route('/my/password/<int:password_id>/confirm', type='http', auth='user', website=True)
    def portal_confirm_password(self, password_id, **kw):
        password, error_redirect = self._get_password_record(password_id, access_type='write')
        if error_redirect:
            return error_redirect

        password.action_confirm()
        return request.redirect('/my/password/%s' % password.id)

    @http.route('/my/password/generate', type='json', auth='user', website=True)
    def portal_generate_password(self):
        return {'password':  request.env['password.manager']._generate_password()}

    @http.route('/my/password/<int:password_id>/edit_detail', type='http', auth='user', website=True)
    def portal_edit_detail(self, password_id, **kw):
        password, error_redirect = self._get_password_record(password_id, access_type='write')
        if error_redirect:
            return error_redirect

        return request.render('password_manager.portal_create_password', {
            'password': password,
            'credential_types': request.env['password.credential.type'].sudo().search([]),
            'categories': request.env['password.category'].sudo().search([]),
            'edit_mode': True,
            'page_name': 'password_edit',
        })

    @http.route('/my/password/<int:password_id>/update_detail', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_update_detail(self, password_id, **post):
        password, error_redirect = self._get_password_record(password_id, access_type='write')
        if error_redirect:
            return error_redirect

        vals = self._prepare_password_vals(post)
        password.write(vals)
        return request.redirect('/my/password/%s' % password.id)

    @http.route('/my/password/update_password', type='json', auth='user', website=True)
    def portal_update_password(self, password_id, current_password, new_password):
        password, error_response = self._get_password_record(password_id, access_type='write', return_json=True)
        if error_response:
            return error_response

        if current_password != password._decrypt_password():
            return {'success': False, 'error': 'Current password is incorrect'}

        password.write({'password': new_password})
        return {'success': True}