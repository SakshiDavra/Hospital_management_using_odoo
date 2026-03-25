from collections import OrderedDict
from odoo import http
from odoo import fields
from odoo.http import request
from datetime import datetime, timedelta
from odoo.fields import Datetime
from itertools import groupby as groupby_func
from odoo.exceptions import ValidationError
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import pytz



class PortalAppointment(CustomerPortal):

    # ================= SEARCHBAR =================

    def _get_searchbar_sortings(self):
        return {
            'date': {'label': 'Date', 'order': 'start_date desc'},
            'appointment': {'label': 'Appointment No', 'order': 'name'},
            'patient': {'label': 'Patient', 'order': 'patient_id'},
            'doctor': {'label': 'Doctor', 'order': 'doctor_id'},
            'specialization': {'label': 'Specialization', 'order': 'specialization_id'},

            'fees': {'label': 'Fees', 'order': 'fees desc'},
        }

    def _get_searchbar_filters(self):

        today = datetime.today()

        # Week calculations (Monday start)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        last_week_start = start_of_week - timedelta(days=7)
        last_week_end = start_of_week - timedelta(days=1)

        next_week_start = start_of_week + timedelta(days=7)
        next_week_end = next_week_start + timedelta(days=6)

        # Month calculations
        start_of_month = today.replace(day=1)

        if today.month == 12:
            next_month_start = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month_start = today.replace(month=today.month + 1, day=1)

        end_of_month = next_month_start - timedelta(days=1)

        last_month_end = start_of_month - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        if next_month_start.month == 12:
            next_month_end = next_month_start.replace(year=next_month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            next_month_end = next_month_start.replace(month=next_month_start.month + 1, day=1) - timedelta(days=1)

        # Year calculations
        start_of_year = today.replace(month=1, day=1)
        end_of_year = today.replace(month=12, day=31)

        return {
            'all': {'label': 'All', 'domain': []},

            'draft': {'label': 'Draft', 'domain': [('state', '=', 'draft')]},
            'confirmed': {'label': 'Confirmed', 'domain': [('state', '=', 'confirmed')]},
            'requested': {'label': 'Requested', 'domain': [('state', '=', 'requested')]},
            'done': {'label': 'Done', 'domain': [('state', '=', 'done')]},
            'cancel': {'label': 'Cancelled', 'domain': [('state', '=', 'cancel')]},

            # NEW DATE FILTERS

            'this_week': {
                'label': 'This Week',
                'domain': [('start_date', '>=', start_of_week),
                        ('start_date', '<=', end_of_week)]
            },

            'last_week': {
                'label': 'Last Week',
                'domain': [('start_date', '>=', last_week_start),
                        ('start_date', '<=', last_week_end)]
            },

            'next_week': {
                'label': 'Next Week',
                'domain': [('start_date', '>=', next_week_start),
                        ('start_date', '<=', next_week_end)]
            },

            'this_month': {
                'label': 'This Month',
                'domain': [('start_date', '>=', start_of_month),
                        ('start_date', '<=', end_of_month)]
            },

            'last_month': {
                'label': 'Last Month',
                'domain': [('start_date', '>=', last_month_start),
                        ('start_date', '<=', last_month_end)]
            },

            'next_month': {
                'label': 'Next Month',
                'domain': [('start_date', '>=', next_month_start),
                        ('start_date', '<=', next_month_end)]
            },

            'this_year': {
                'label': 'This Year',
                'domain': [('start_date', '>=', start_of_year),
                        ('start_date', '<=', end_of_year)]
            },
        }

    def _get_searchbar_groupby(self):
        user_partner = request.env.user.partner_id
        roles = user_partner.role_ids.mapped('name')

        groupby = {
            'none': {'label': 'None'},
            'doctor_id': {'label': 'Doctor'},
            'specialization_id': {'label': 'Specialization'},
            'patient_id': {'label': 'Patient'},
            'state': {'label': 'Status'},

            'date_year': {'label': 'Year'},
            'date_month': {'label': 'Month'},
            'date_week': {'label': 'Week'},
            'date_day': {'label': 'Day'},
        }

        #  ROLE BASED REMOVE
        if 'Doctor' in roles and 'Patient' not in roles:
            groupby.pop('doctor_id', None)

        if 'Patient' in roles and 'Doctor' not in roles:
            groupby.pop('patient_id', None)

        return groupby

    def _get_searchbar_inputs(self):
        return {
            'all': {'input': 'all', 'label': 'Search All'},
            'patient': {'input': 'patient', 'label': 'Patient'},
            'doctor': {'input': 'doctor', 'label': 'Doctor'},
            'appointment': {'input': 'appointment', 'label': 'Appointment No'},
            'specialization': {'input': 'specialization', 'label': 'Specialization'},
        }

    def _get_search_domain(self, search_in, search):

        if search_in == 'patient':
            return ['|',
                ('patient_id.name', 'ilike', search),
                ('patient_id.hospital_code', 'ilike', search)]

        elif search_in == 'doctor':
            return ['|',
                    ('doctor_id.name', 'ilike', search),
                    ('doctor_id.hospital_code', 'ilike', search)]

        elif search_in == 'appointment':
            return [('name', 'ilike', search)]

        elif search_in == 'specialization':
            return [('specialization_id.name', 'ilike', search)]

    
        else:
            # SEARCH ALL
            return ['|','|','|','|','|','|',
                ('name', 'ilike', search),

                ('patient_id.name', 'ilike', search),
                ('patient_id.hospital_code', 'ilike', search),

                ('doctor_id.name', 'ilike', search),
                ('doctor_id.hospital_code', 'ilike', search),

                ('specialization_id.name', 'ilike', search),
                ('start_date', 'ilike', search)]           

    # ================= ROUTE =================

    @http.route(['/my/appointments', '/my/appointments/page/<int:page>'],
        type='http', auth="user", website=True)
    def portal_my_appointments(self, page=1, sortby='date', filterby='all',
                            groupby='none', search=None, search_in='all', **kw):

        Appointment = request.env['hospital.appointment']

        searchbar_sortings = self._get_searchbar_sortings()
        searchbar_filters = self._get_searchbar_filters()
        searchbar_groupby = self._get_searchbar_groupby()
        searchbar_inputs = self._get_searchbar_inputs()

        user_partner = request.env.user.partner_id
        roles = user_partner.role_ids.mapped('name')

        domain = list(searchbar_filters.get(filterby, {}).get('domain', []))

        if 'Doctor' in roles and 'Patient' not in roles:
            domain += [('doctor_id', '=', user_partner.id)]
        elif 'Patient' in roles and 'Doctor' not in roles:
            domain += [('patient_id', '=', user_partner.id)]

        if search:
            domain += self._get_search_domain(search_in, search)

        order = searchbar_sortings.get(sortby, {}).get('order', 'start_date desc')

        #  STEP FETCH ALL DATA
        all_appointments = Appointment.search(domain, order=order)

        # GROUPING
        grouped_appointments = []

        def prepare_group(key, records):
            recs = list(records)

            group_field_map = {
                'doctor_id': 'doctor_id',
                'patient_id': 'patient_id',
                'specialization_id': 'specialization_id',
                'state': 'state',
            }

            # TOTAL COUNT FIX
            if groupby in group_field_map and key:
                field = group_field_map[groupby]

                if groupby == 'state':
                    total_count = request.env['hospital.appointment'].search_count(
                        domain + [(field, '=', key)]
                    )
                else:
                    total_count = request.env['hospital.appointment'].search_count(
                        domain + [(field, '=', key.id)]
                    )
            else:
                total_count = len(recs)

            return {
                'key': key,
                'records': recs,
                'total_fees': sum(r.fees for r in recs),
                'total_count': total_count
            }

        # ================= GROUP LOGIC =================

        if groupby == 'doctor_id':
            all_appointments = all_appointments.sorted(key=lambda x: x.doctor_id.id or 0)
            for key, group in groupby_func(all_appointments, key=lambda x: x.doctor_id):
                grouped_appointments.append(prepare_group(key, group))

        elif groupby == 'patient_id':
            all_appointments = all_appointments.sorted(key=lambda x: x.patient_id.id or 0)
            for key, group in groupby_func(all_appointments, key=lambda x: x.patient_id):
                grouped_appointments.append(prepare_group(key, group))

        elif groupby == 'specialization_id':
            all_appointments = all_appointments.sorted(key=lambda x: x.specialization_id.id or 0)
            for key, group in groupby_func(all_appointments, key=lambda x: x.specialization_id):
                grouped_appointments.append(prepare_group(key, group))

        elif groupby == 'state':
            all_appointments = all_appointments.sorted(key=lambda x: x.state or '')
            for key, group in groupby_func(all_appointments, key=lambda x: x.state):
                grouped_appointments.append(prepare_group(key, group))

        #  DATE GROUPING 
        elif groupby == 'date_year':
            all_appointments = all_appointments.sorted(key=lambda x: x.start_date or datetime.min)
            for key, group in groupby_func(all_appointments, key=lambda x: x.start_date.year if x.start_date else 0):
                grouped_appointments.append(prepare_group(key, group))

        elif groupby == 'date_month':
            all_appointments = all_appointments.sorted(key=lambda x: x.start_date or datetime.min)
            for key, group in groupby_func(
                all_appointments,
                key=lambda x: (x.start_date.year, x.start_date.month) if x.start_date else (0, 0)
            ):
                grouped_appointments.append(prepare_group(key, group))

        elif groupby == 'date_week':
            all_appointments = all_appointments.sorted(key=lambda x: x.start_date or datetime.min)
            for key, group in groupby_func(
                all_appointments,
                key=lambda x: x.start_date.isocalendar()[1] if x.start_date else 0
            ):
                grouped_appointments.append(prepare_group(key, group))

        elif groupby == 'date_day':
            all_appointments = all_appointments.sorted(key=lambda x: x.start_date or datetime.min)
            for key, group in groupby_func(
                all_appointments,
                key=lambda x: x.start_date.date() if x.start_date else ''
            ):
                grouped_appointments.append(prepare_group(key, group))

        # DEFAULT
        else:
            grouped_appointments = [{
                'key': False,
                'records': all_appointments,
                'total_fees': sum(r.fees for r in all_appointments),
                'total_count': len(all_appointments)
            }]

        # PAGINATION (RECORD LEVEL BUT GROUP SAFE)
        page_size = 10
        start = (page - 1) * page_size
        end = start + page_size

        final_groups = []
        count = 0

        for group in grouped_appointments:
            new_records = []

            for rec in group['records']:
                if count >= start and count < end:
                    new_records.append(rec)
                count += 1

            if new_records:
                final_groups.append({
                    'key': group['key'],
                    'records': new_records,
                    'total_fees': sum(r.fees for r in new_records),
                    'total_count': group.get('total_count')   
                })

        total = len(all_appointments)

        pager = portal_pager(
            url="/my/appointments",
            url_args={
                'sortby': sortby,
                'filterby': filterby,
                'groupby': groupby,
                'search': search,
                'search_in': search_in,
            },
            total=total,
            page=page,
            step=10
        )

        values = {
        'appointments': all_appointments,
        'grouped_appointments': final_groups,
        'pager': pager,
        'page_name': 'appointments',

        'default_url': '/my/appointments', 

        'searchbar_sortings': searchbar_sortings,
        'searchbar_filters': searchbar_filters,
        'searchbar_groupby': searchbar_groupby,
        'searchbar_inputs': searchbar_inputs,

        'sortby': sortby,
        'filterby': filterby,
        'groupby': groupby,
        'search': search,
        'search_in': search_in,

        'is_patient': 'Patient' in roles,
        'is_doctor': 'Doctor' in roles,
    }

        return request.render("hospital_management.portal_my_appointments", values)

    # ================= FORM PAGE =================
    @http.route(['/my/appointment/new'], type='http', auth="user", website=True)
    def portal_create_appointment_form(self, **kw):

        appointment_id = kw.get('appointment_id')
        appointment = False

        start_date_local = False
        end_date_local = False

        if appointment_id:
            appointment = request.env['hospital.appointment'].sudo().browse(int(appointment_id))

            # TIMEZONE CONVERSION (SAFE WAY)
            if appointment.start_date:
                start_local = Datetime.context_timestamp(request.env.user, appointment.start_date)
                start_date_local = start_local.strftime('%Y-%m-%dT%H:%M')

            if appointment.end_date:
                end_local = Datetime.context_timestamp(request.env.user, appointment.end_date)
                end_date_local = end_local.strftime('%Y-%m-%dT%H:%M')

        user_partner = request.env.user.partner_id
        roles = user_partner.role_ids.mapped('name')

        doctor_fees = 0
        if 'Doctor' in roles:
            doctor_fees = user_partner.consultation_fees

        values = {
            'appointment': appointment,
            'is_edit': bool(appointment),

            # IMPORTANT
            'start_date_local': start_date_local,
            'end_date_local': end_date_local,

            'patients': request.env['res.partner'].sudo().search([('role_ids.name', '=', 'Patient')]),
            'doctors': request.env['res.partner'].sudo().search([('role_ids.name', '=', 'Doctor')]),
            'specializations': request.env['hospital.specialization'].sudo().search([]),

            'is_patient': 'Patient' in roles,
            'is_doctor': 'Doctor' in roles,

            'user_specialization': user_partner.specialization_id,
            'doctor_fees': doctor_fees,

            'page_name': 'create_appointment'
        }

        return request.render("hospital_management.portal_create_appointment", values)


    # ================= CREATE / UPDATE =================
    @http.route(['/my/appointment/create'], type='http', auth="user", website=True, methods=['POST'])
    def portal_create_appointment(self, **post):

        Appointment = request.env['hospital.appointment'].sudo()
        user_partner = request.env.user.partner_id
        roles = user_partner.role_ids.mapped('name')

        try:
            user_tz = pytz.timezone(request.env.user.tz or 'UTC')

            # ================= START =================
            start = post.get('start_date')
            start = datetime.strptime(start, '%Y-%m-%dT%H:%M')
            start = user_tz.localize(start).astimezone(pytz.UTC)
            start = start.replace(tzinfo=None)

            # ================= END =================
            end = post.get('end_date')
            if end:
                end = datetime.strptime(end, '%Y-%m-%dT%H:%M')
                end = user_tz.localize(end).astimezone(pytz.UTC)
                end = end.replace(tzinfo=None)
            else:
                end = False

            # ================= PATIENT =================
            if 'Patient' in roles and 'Doctor' not in roles:
                patient_id = user_partner.id
            else:
                patient_id = int(post.get('patient_id'))

            # ================= DOCTOR =================
            if 'Doctor' in roles:
                doctor_id = user_partner.id
            else:
                doctor_id = int(post.get('doctor_id'))

            # ================= VALUES =================
            vals = {
                'patient_id': patient_id,
                'doctor_id': doctor_id,
                'fees': float(post.get('fees') or 0),
                'specialization_id': int(post.get('specialization_id')),
                'start_date': start,
                'end_date': end,
                'symptoms': post.get('symptoms'),
            }

            appointment_id = request.httprequest.args.get('appointment_id')

            if appointment_id:
                appointment = Appointment.browse(int(appointment_id))

                if appointment.state != 'draft':
                    return request.redirect('/my/appointment/%s' % appointment.id)

                appointment.write(vals)
            else:
                appointment = Appointment.create(vals)

            return request.redirect('/my/appointment/%s' % appointment.id)

        except ValidationError as e:

            appointment_id = request.httprequest.args.get('appointment_id')

            return request.render("hospital_management.portal_create_appointment", {
                'error': str(e),
                'old': post,
                'is_edit': bool(appointment_id),
                'appointment': Appointment.browse(int(appointment_id)) if appointment_id else False,

                'patients': request.env['res.partner'].sudo().search([('role_ids.name','=','Patient')]),
                'doctors': request.env['res.partner'].sudo().search([('role_ids.name','=','Doctor')]),
                'specializations': request.env['hospital.specialization'].sudo().search([]),

                'is_patient': 'Patient' in roles,
                'is_doctor': 'Doctor' in roles,
                'user_specialization': user_partner.specialization_id,
                'doctor_fees': user_partner.consultation_fees if 'Doctor' in roles else 0,
            })