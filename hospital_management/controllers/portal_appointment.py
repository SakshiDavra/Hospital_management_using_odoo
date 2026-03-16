from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.tools.misc import format_datetime


class HospitalPortal(CustomerPortal):

    @http.route(['/my/appointments'], type='http', auth="user", website=True)
    def portal_my_appointments(self, **kw):

        user = request.env.user

        # Admin → show all
        if user.has_group('base.group_system'):
            appointments = request.env['hospital.appointment'].sudo().search([])

        # Doctor → show doctor's appointments
        elif user.has_group('hospital_management.group_hospital_doctor'):
            appointments = request.env['hospital.appointment'].sudo().search([
                ('doctor_id.user_id', '=', user.id)
            ])

        # Patient → show patient's appointments
        else:
            appointments = request.env['hospital.appointment'].sudo().search([
                ('patient_id.user_id', '=', user.id)
            ])

        values = {
            'appointments': appointments,
            'format_datetime': format_datetime,
            'page_name': 'my_appointments'
        }

        return request.render(
            'hospital_management.portal_my_appointments_page',
            values
        )