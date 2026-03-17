from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.tools.misc import format_datetime


class HospitalPortal(CustomerPortal):

    @http.route([
        '/my/appointments',
        '/my/appointments/page/<int:page>'
    ], type='http', auth="user", website=True)
    def portal_my_appointments(self, page=1, **kw):

        user = request.env.user
        Appointment = request.env['hospital.appointment']

        # Domain
        if user.has_group('base.group_system'):
            domain = []
        elif user.has_group('hospital_management.group_hospital_doctor'):
            domain = [('doctor_id.user_id', '=', user.id)]
        else:
            domain = [('patient_id.user_id', '=', user.id)]

        total = Appointment.sudo().search_count(domain)

        pager = portal_pager(
            url="/my/appointments",
            total=total,
            page=page,
            step=10
        )

        appointments = Appointment.sudo().search(
            domain,
            limit=10,
            offset=pager['offset']
        )

        values = {
            'appointments': appointments,
            'pager': pager,
            'format_datetime': format_datetime,
            'page_name': 'appointments'
        }

        return request.render(
            'hospital_management.portal_my_appointments_page',
            values
        )