from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalAppointment(CustomerPortal):

    @http.route(['/my/appointment/<int:appointment_id>'], type='http', auth="user", website=True)
    def portal_appointment_detail(self, appointment_id=None, **kw):

        appointment_obj = request.env['hospital.appointment']

        # 👇 All appointments for current user
        appointments = appointment_obj.sudo().search([])

        # 👇 Get ids list
        appointment_ids = appointments.ids

        # 👇 Current index
        try:
            index = appointment_ids.index(appointment_id)
        except ValueError:
            index = 0

        # 👇 Prev / Next IDs
        prev_id = appointment_ids[index - 1] if index > 0 else False
        next_id = appointment_ids[index + 1] if index < len(appointment_ids) - 1 else False

        appointment = appointment_obj.sudo().browse(appointment_id)

        values = {
            'appointment': appointment,
            'page_name': 'appointment',

            # ✅ Required for pager
            'prev_record': prev_id,
            'next_record': next_id,
            'page_view': 'appointment',
        }

        return request.render(
            "hospital_management.portal_appointment_page",
            values
        )