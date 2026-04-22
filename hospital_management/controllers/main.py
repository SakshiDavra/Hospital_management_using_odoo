from odoo import http
from odoo.http import request

class HospitalController(http.Controller):

    @http.route('/specializations', type='http', auth='public', website=True)
    def all_specializations(self, **kwargs):
        specializations = request.env['hospital.specialization'].sudo().search([])

        return request.render('hospital_management.all_specializations_page', {
            'specializations': specializations
        })

     # BOTH: all + specialization
    @http.route(['/doctors', '/doctors/<string:spec_slug>'], type='http', auth='public', website=True)
    def doctors(self, spec_slug=None, **kwargs):

        domain = [
            ('role_ids.name', '=', 'Doctor')
        ]

        specialization = None
        from_page = kwargs.get('from')

        # If specialization URL hoy
        if spec_slug:
            spec_name = spec_slug.replace('-', ' ')
            specialization = request.env['hospital.specialization'].sudo().search([
                ('name', 'ilike', spec_name)
            ], limit=1)

            if specialization:
                domain.append(('specialization_id', '=', specialization.id))

        doctors = request.env['res.partner'].sudo().search(domain)

        return request.render('hospital_management.doctor_list_page', {
            'doctors': doctors,
            'specialization': specialization,
            'from_page': from_page
        })
        