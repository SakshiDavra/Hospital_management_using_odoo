from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalAppointment(CustomerPortal):

    @http.route(['/my/appointment/<int:appointment_id>'], type='http', auth="user", website=True)
    def portal_appointment_detail(self, appointment_id=None, **kw):

        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)

        values = {
            'appointment': appointment
        }

        return request.render(
            "hospital_management.portal_appointment_page",
            values
        )