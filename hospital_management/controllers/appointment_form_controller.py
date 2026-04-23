from odoo import http
from odoo.http import request


class WebsiteAppointmentController(http.Controller):

    # 🔹 specialization → doctor filter
    @http.route('/get_doctors_by_specialization', type='json', auth='public', website=True)
    def get_doctors(self, specialization_id=None):

        domain = [('role_ids.name', '=', 'Doctor')]

        #  only filter when specialization selected
        if specialization_id:
            domain.append(('specialization_id', '=', int(specialization_id)))

        doctors = request.env['res.partner'].sudo().search(domain)

        return [{
            'id': d.id,
            'name': d.name,
        } for d in doctors]


    # 🔹 doctor → specialization auto fill
    @http.route('/get_doctor_specialization', type='json', auth='public', website=True)
    def get_specialization(self, doctor_id):

        if not doctor_id:
            return {'specialization_id': False}

        doctor = request.env['res.partner'].sudo().browse(int(doctor_id))

        return {
            'specialization_id': doctor.specialization_id.id if doctor.specialization_id else False
        }