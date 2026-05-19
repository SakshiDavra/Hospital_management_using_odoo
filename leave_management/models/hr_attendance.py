from odoo import api, models, _
from markupsafe import Markup


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

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

            leave_type = leave.holiday_status_id if leave else self.env[
                'hr.leave.type'
            ].search([
                ('name', 'ilike', 'Comp'),
                ('requires_allocation', '=', 'yes'),
            ], limit=1)

            if not leave_type:
                continue

            holiday = self.env['resource.calendar.leaves'].search([
                ('calendar_id', '=', calendar.id),
                ('date_from', '<=', attendance.check_in),
                ('date_to', '>=', attendance.check_in),
            ], limit=1)

            is_weekend = str(today.weekday()) not in \
                calendar.attendance_ids.mapped('dayofweek')

            if not leave and not (holiday or is_weekend):
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
                            _('Comp Off added for working on Holiday / Weekend.')
                        }
                        <br/>
                        <b>{_('Date')}:</b> {today}
                        <br/>
                        <b>{_('Credited Days')}:</b> {leave_days}
                    </p>
                """)
            )

        return attendances