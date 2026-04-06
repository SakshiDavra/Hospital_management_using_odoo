from odoo import http
from odoo.http import request
from datetime import datetime, timedelta


class HospitalDashboard(http.Controller):

    @http.route('/hospital/dashboard/data', type='json', auth='user')
    def dashboard_data(self, filter='week'):

        today = datetime.today().date()
        next_week = today + timedelta(days=7)
        last_week = today - timedelta(days=7)

        # STATE DATA (PieChart)
        state_data = request.env['hospital.appointment'].read_group(
            [],
            ['state'],
            ['state']
        )

        #  COMMON DATASETS
        states = ['draft', 'requested', 'confirmed', 'done', 'cancel']
        datasets = {state: [] for state in states}
        labels = []

        # ================= TOP 5 DOCTORS =================

        top_doctors = request.env['hospital.appointment'].read_group(
            domain=[('state', 'in', ['confirmed', 'done'])],
            fields=['doctor_id'],
            groupby=['doctor_id'],
            limit=5,
            orderby='doctor_id_count desc'
        )

        top_doctor_data = []
        for rec in top_doctors:
            top_doctor_data.append({
                'doctor': rec['doctor_id'][1] if rec['doctor_id'] else 'Unknown',
                'count': rec['doctor_id_count']
            })
        # =========================
        # WEEK (DAY-WISE)
        # =========================
        if filter == 'week':

            start_of_week = today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)

            for i in range(7):
                day = start_of_week + timedelta(days=i)
                next_day = day + timedelta(days=1)

                labels.append(day.strftime('%a'))

                for state in states:
                    count = request.env['hospital.appointment'].search_count([
                        ('state', '=', state),
                        ('start_date', '>=', datetime.combine(day, datetime.min.time())),
                        ('start_date', '<', datetime.combine(next_day, datetime.min.time())),
                    ])
                    datasets[state].append(count)

        # =========================
        #  MONTH (WEEK-WISE)
        # =========================
        elif filter == 'month':

            start_of_month = today.replace(day=1)

            labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5']

            for i in range(5):
                start = start_of_month + timedelta(days=i * 7)
                end = start + timedelta(days=7)

                for state in states:
                    count = request.env['hospital.appointment'].search_count([
                        ('state', '=', state),
                        ('start_date', '>=', start),
                        ('start_date', '<', end),
                    ])
                    datasets[state].append(count)

        # =========================
        #  YEAR (MONTH-WISE)
        # =========================
        elif filter == 'year':

            labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

            for month in range(1, 13):

                start = datetime(today.year, month, 1)

                if month == 12:
                    end = datetime(today.year + 1, 1, 1)
                else:
                    end = datetime(today.year, month + 1, 1)

                for state in states:
                    count = request.env['hospital.appointment'].search_count([
                        ('state', '=', state),
                        ('start_date', '>=', start),
                        ('start_date', '<', end),
                    ])
                    datasets[state].append(count)

        # FINAL CHART
        chart = {
            'labels': labels,
            'datasets': datasets
        }

        todos = request.env['hospital.todo'].search([], order="id desc", limit=5)

        todo_data = []
        for t in todos:
            todo_data.append({
                'id': t.id,
                'name': t.name,
                'is_done': t.is_done
            })

        # FINAL RESPONSE
        return {
            'patients': request.env['res.partner'].search_count([
                ('role_ids.name', '=', 'Patient')
            ]),

            'doctors': request.env['res.partner'].search_count([
                ('role_ids.name', '=', 'Doctor')
            ]),

            'appointments': request.env['hospital.appointment'].search_count([]),

            #  TODAY
            'today_appointments': request.env['hospital.appointment'].search_count([
                ('start_date', '>=', datetime.combine(today, datetime.min.time())),
                ('start_date', '<=', datetime.combine(today, datetime.max.time())),
            ]),

            # WEEK
            'week_appointments': request.env['hospital.appointment'].search_count([
                ('start_date', '>=', datetime.combine(today, datetime.min.time())),
                ('start_date', '<=', datetime.combine(next_week, datetime.max.time())),
            ]),

            #  PAST WEEK
            'past_week': request.env['hospital.appointment'].search_count([
                ('start_date', '>=', datetime.combine(last_week, datetime.min.time())),
                ('start_date', '<=', datetime.combine(today, datetime.max.time())),
            ]),

            'state_data': state_data,

            # IMPORTANT CHANGE
            'chart': chart,
            'top_doctors': top_doctor_data,
            'todos': todo_data,
        }


    @http.route('/hospital/todo/create', type='json', auth='user')
    def create_todo(self, name):

        todo = request.env['hospital.todo'].create({
            'name': name
        })

        return {
            'id': todo.id,
            'name': todo.name,
            'is_done': todo.is_done
        }

    @http.route('/hospital/todo/toggle', type='json', auth='user')
    def toggle_todo(self, id):

        todo = request.env['hospital.todo'].browse(id)

        todo.write({
            'is_done': not todo.is_done
        })

        return {'success': True}

    @http.route('/hospital/todo/delete', type='json', auth='user')
    def delete_todo(self, id):

        request.env['hospital.todo'].browse(id).unlink()

        return {'success': True}