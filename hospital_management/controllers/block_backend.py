# from odoo import http
# from odoo.addons.web.controllers.home import Home
# from odoo.http import request

# class BlockBackend(Home):

#     @http.route('/is_patient', type='jsonrpc', auth="user")
#     def is_patient(self):
#         return request.env.user.has_group('hospital_management.group_hospital_patient')
    
#     # /web
#     @http.route('/web', type='http', auth="user")
#     def web_client(self, s_action=None, **kw):

#         if request.env.user.has_group('hospital_management.group_hospital_patient'):
#             return request.redirect('/')

#         return super().web_client(s_action=s_action, **kw)

#     # /odoo 
#     @http.route('/odoo', type='http', auth="user")
#     def block_odoo_root(self, **kw):

#         if request.env.user.has_group('hospital_management.group_hospital_patient'):
#             return request.redirect('/')

#         return request.redirect('/web')


#     # /odoo/*
#     @http.route('/odoo/<path:path>', type='http', auth="user")
#     def block_odoo_paths(self, path=None, **kw):

#         if request.env.user.has_group('hospital_management.group_hospital_patient'):
#             return request.redirect('/')

#         return request.redirect('/web')

