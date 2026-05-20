from odoo import api, models, _
from markupsafe import Markup


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def _send_email(self, template_xmlid, email_to=None):
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        smtp_email = self.env['ir.mail_server'].sudo().search([], limit=1).smtp_user
        if template:
            for rec in self:
                template.send_mail(
                    rec.id,
                    force_send=True,
                    email_values={
                        'email_to': email_to or '',
                        'email_from': smtp_email,
                        'reply_to': smtp_email,
                    }
                )

    @api.model_create_multi
    def create(self, vals_list):

        attendances = super().create(vals_list)

        for attendance in attendances:
            employee = attendance.employee_id
            today = attendance.check_in.date()
            worked_hours = attendance.worked_hours
            calendar = (
                employee.resource_calendar_id
                or employee.company_id.resource_calendar_id
            )
            hours_per_day = calendar.hours_per_day or 8
            leave_days = (
                1.5 if worked_hours >= hours_per_day * 1.5 else
                1 if worked_hours >= hours_per_day else
                0.5 if worked_hours >= hours_per_day / 2 else 0
            )

            if not leave_days:
                continue

            leave = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('request_date_from', '<=', today),
                ('request_date_to', '>=', today),
            ], limit=1)

            leave_type = (
                leave.holiday_status_id
                if leave else
                self.env['hr.leave.type'].search([
                    ('name', 'ilike', 'Comp')
                ], limit=1)
            )

            if not leave_type:
                continue

            holiday = self.env['resource.calendar.leaves'].search([
                ('calendar_id', '=', calendar.id),
                ('date_from', '<=', attendance.check_in),
                ('date_to', '>=', attendance.check_in),
            ], limit=1)

            is_weekend = (
                str(today.weekday())
                not in calendar.attendance_ids.mapped('dayofweek')
            )
            if not leave and not holiday and not is_weekend:
                continue

            if not leave_type.requires_allocation:
                if employee.parent_id.work_email:

                    attendance.with_context(
                        leave_type_name=leave_type.name
                    )._send_email(
                        'leave_management.email_template_extra_hours_manager',
                        employee.parent_id.work_email
                    )

                if leave:
                    leave.message_post(
                        body=Markup(f"""
                            <p>
                                <b>{employee.name}</b>
                                worked during approved leave.
                                <br/>
                                <b>Leave Type:</b> {leave_type.name}<br/>
                                <b>Date:</b> {today}<br/>
                                <b>Worked Hours:</b> {round(worked_hours, 2)}<br/>
                                <b>Equivalent Days:</b> {leave_days}
                            </p>
                        """)
                    )
                continue

            name = (
                f'Attendance Adjustment - {today}'
                if leave else
                f'Comp Off - {today}'
            )
            exists = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', leave_type.id),
                ('name', '=', name),
            ], limit=1)

            if exists:
                continue

            allocation = self.env['hr.leave.allocation'].create({
                'name': name,
                'employee_id': employee.id,
                'holiday_status_id': leave_type.id,
                'allocation_type': 'regular',
                'number_of_days': leave_days,
            })

            allocation._action_validate()
            allocation.message_post(
                body=Markup(f"""
                    <p>
                        {
                            _('Leave credited because employee worked during approved leave.')
                            if leave else
                            _('Comp Off added for Holiday / Weekend work.')
                        }


                        
                        <br/><br/>

                        <b>Date:</b> {today}<br/>
                        <b>Credited Days:</b> {leave_days}
                    </p>
                """)
            )
        return attendances