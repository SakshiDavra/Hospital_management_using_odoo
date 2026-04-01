from odoo import http
from odoo.http import request
from datetime import datetime, timedelta

class HospitalDashboard(http.Controller):

    @http.route('/hospital/dashboard/data', type='json', auth='user')
    def dashboard_data(self):

        today = datetime.today().date()
        next_week = today + timedelta(days=7)
        last_week = today - timedelta(days=7)

        return {
            'patients': request.env['res.partner'].search_count([
                ('role_ids.name','=','Patient')
            ]),

            'doctors': request.env['res.partner'].search_count([
                ('role_ids.name','=','Doctor')
            ]),

            'appointments': request.env['hospital.appointment'].search_count([]),

            # ✅ TODAY (FIXED)
            'today_appointments': request.env['hospital.appointment'].search_count([
                ('start_date', '>=', datetime.combine(today, datetime.min.time())),
                ('start_date', '<=', datetime.combine(today, datetime.max.time())),
            ]),

            # ✅ WEEK (FIXED)
            'week_appointments': request.env['hospital.appointment'].search_count([
                ('start_date', '>=', datetime.combine(today, datetime.min.time())),
                ('start_date', '<=', datetime.combine(next_week, datetime.max.time())),
            ]),
            'past_week': request.env['hospital.appointment'].search_count([
                ('start_date', '>=', datetime.combine(last_week, datetime.min.time())),
                ('start_date', '<=', datetime.combine(today, datetime.max.time())),
            ]),
        }