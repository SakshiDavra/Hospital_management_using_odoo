from odoo import http
from odoo.http import request

class HospitalSnippet(http.Controller):

    @http.route('/hospital/specializations_html', type='json', auth='public', website=True)
    def get_specializations_html(self):

        specs = request.env['hospital.specialization'].sudo().search([])

        html = request.env['ir.ui.view']._render_template(
            'hospital_management.specialization_card_template',
            {'specializations': specs}
        )

        return {'html': html}