from odoo import http
from odoo.http import request, content_disposition
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalAppointment(CustomerPortal):

    @http.route(['/my/appointment/<int:appointment_id>'], type='http', auth="user", website=True)
    def portal_appointment_detail(self, appointment_id=None, **kw):

        appointment_obj = request.env['hospital.appointment']
        appointment = appointment_obj.sudo().browse(appointment_id)

        # 🔥 PDF condition (IMPORTANT FIX)
        if kw.get('report_type') == 'pdf':

            pdf, _ = request.env['ir.actions.report']._render_qweb_pdf(
                'hospital_management.report_hospital_appointment',
                [appointment.id]
            )

            filename = f"Appointment - {appointment.name}.pdf"

            # 🔥 DIFFERENCE HERE
            if kw.get('download'):
                disposition = content_disposition(filename)   # ✅ download
            else:
                disposition = f'inline; filename="{filename}"'  # ✅ preview

            return request.make_response(
                pdf,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Length', len(pdf)),
                    ('Content-Disposition', disposition)
                ]
            )

        # 👇 All appointments for current user
        user_partner = request.env.user.partner_id

        if request.env.user.has_group('base.group_system'):
            appointments = appointment_obj.sudo().search([])
        else:
            appointments = appointment_obj.sudo().search([
                '|',
                ('patient_id', '=', user_partner.id),
                ('doctor_id', '=', user_partner.id),
            ])
            
        appointment_ids = appointments.ids

        # 👇 Current index
        try:
            index = appointment_ids.index(appointment_id)
        except ValueError:
            index = 0

        # 👇 Prev / Next IDs
        prev_id = appointment_ids[index - 1] if index > 0 else False
        next_id = appointment_ids[index + 1] if index < len(appointment_ids) - 1 else False

        values = {
            'appointment': appointment,
            'page_name': 'appointment',

            # ✅ Pager
            'prev_record': prev_id,
            'next_record': next_id,
            'page_view': 'appointment',
        }

        return request.render(
            "hospital_management.portal_appointment_page",
            values
        )

    # ================= PORTAL ACTION BUTTONS =================

    # REQUEST (Patient)
    @http.route(['/appointment/request/<int:appointment_id>'], type='http', auth="user", website=True)
    def portal_request_appointment(self, appointment_id, **kw):
        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)
        appointment.action_request()
        return request.redirect('/my/appointment/%s' % appointment_id)


    # CONFIRM (Doctor)
    @http.route(['/appointment/confirm/<int:appointment_id>'], type='http', auth="user", website=True)
    def portal_confirm_appointment(self, appointment_id, **kw):
        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)
        appointment.action_confirm()
        return request.redirect('/my/appointment/%s' % appointment_id)


    # DONE (Doctor)
    @http.route(['/appointment/done/<int:appointment_id>'], type='http', auth="user", website=True)
    def portal_done_appointment(self, appointment_id, **kw):
        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)
        appointment.action_done()
        return request.redirect('/my/appointment/%s' % appointment_id)

    # CANCEL
    @http.route(
    ['/appointment/cancel/<int:appointment_id>'],
    type='http',
    auth="user",
    website=True,
    methods=['POST']   # 🔥 IMPORTANT
    )
    def portal_cancel_appointment(self, appointment_id, **kw):

        appointment = request.env['hospital.appointment'].sudo().browse(appointment_id)

        reason = kw.get('reason')

        appointment.action_cancel_from_portal(reason)

        return request.redirect('/my/appointment/%s' % appointment_id)