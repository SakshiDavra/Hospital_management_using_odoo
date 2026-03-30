from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
import logging
import base64

_logger = logging.getLogger(__name__)

class HospitalAppointment(models.Model):
    _name = "hospital.appointment"
    _description = "Hospital Appointment"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    # ================= BASIC FIELDS =================

    name = fields.Char(string="Appointment No", readonly=True, copy=False)

    patient_id = fields.Many2one(
    'res.partner',
    string="Patient",
    required=True,
    tracking=True
    )

    color = fields.Integer(string="Color")

    company_id = fields.Many2one(
    'res.company',
    string="Company",
    required=True,
    default=lambda self: self.env.company
    )

    specialization_id = fields.Many2one(
        'hospital.specialization',
        string="Specialization",
        required=True
    )

    doctor_id = fields.Many2one(
        'res.partner',
        string="Doctor",
        required=True,
        tracking=True
    )

    start_date = fields.Datetime(
        string="Appointment Date & Time",
        required=True,
        tracking=True
    )

    end_date = fields.Datetime(
        string="End Date & Time",
        store=True,
        tracking=True
    )

    symptoms = fields.Text(string="Symptoms")

    currency_id = fields.Many2one(
    'res.currency',
    string="Currency",
    related="company_id.currency_id",
    readonly=True
    )

    fees = fields.Monetary(
        string="Consultation Fees",
        currency_field="currency_id",
        compute="_compute_fees",
        store=True,
        tracking=True
    )

    notes = fields.Text(string="Doctor Notes")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string="Status", default='draft', tracking=True)

    available_days = fields.Char(
        string="Doctor Available On",
        compute="_compute_available_days"
    )
    cancel_reason = fields.Text(string="Cancel Reason")

    invoice_id = fields.Many2one('account.move', string="Invoice")

    is_paid = fields.Boolean(
        string="Is Paid",
        compute="_compute_payment_status",
        store=True
    )

    @api.depends('invoice_id.payment_state')
    def _compute_payment_status(self):
        for rec in self:
            rec.is_paid = rec.invoice_id.payment_state == 'paid'

    def _sync_specialization_with_doctor(self, doctor):
        return doctor.specialization_id if doctor else False


    def _is_doctor_valid_for_specialization(self, doctor, specialization):
        if doctor and specialization:
            return doctor.specialization_id == specialization
        return True

    @api.onchange('specialization_id')
    def _onchange_specialization(self):
        if not self._is_doctor_valid_for_specialization(self.doctor_id, self.specialization_id):
            self.doctor_id = False

    @api.onchange('doctor_id')
    def _onchange_doctor(self):
        self.specialization_id = self._sync_specialization_with_doctor(self.doctor_id)

    # ================= HELPER METHOD =================

    def _get_duration(self):
        return self.env.company.appointment_duration or 30

    # ================= COMPUTE METHODS =================

    @api.depends('doctor_id')
    def _compute_fees(self):
        for rec in self:
            rec.fees = rec.doctor_id.consultation_fees if rec.doctor_id else 0.0

    @api.depends('doctor_id')
    def _compute_available_days(self):
        day_map = {
            '0': 'Mon', '1': 'Tue', '2': 'Wed',
            '3': 'Thu', '4': 'Fri', '5': 'Sat', '6': 'Sun',
        }

        def float_to_time(float_time):
            if float_time is None:
                return ""
            float_time = float(float_time)
            hour = int(float_time)
            minute = int((float_time - hour) * 60)
            hour_12 = hour % 12 or 12
            am_pm = "AM" if hour < 12 else "PM"
            return f"{hour_12:02d}:{minute:02d} {am_pm}"

        for rec in self:
            if not rec.doctor_id:
                rec.available_days = ""
                continue

            day_slots = {}

            for sched in rec.doctor_id.slot_ids:
                day_name = day_map.get(sched.day)
                if not day_name:
                    continue

                if day_name not in day_slots:
                    day_slots[day_name] = []

                if not sched.start_time and not sched.end_time:
                    day_slots[day_name].append("Full Day")
                else:
                    start = float_to_time(sched.start_time)
                    end = float_to_time(sched.end_time)
                    day_slots[day_name].append(f"{start} - {end}")

            result = []
            for day, slots in day_slots.items():
                result.append(f"{day} ({', '.join(slots)})")

            rec.available_days = ", ".join(result)

    # ================= CREATE =================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            # Set company if not provided
            vals.setdefault('company_id', self.env.company.id)

            # Generate sequence
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hospital.appointment'
                ) or 'APT000'

            # Auto calculate end date
            if vals.get('start_date') and not vals.get('end_date'):
                duration = self._get_duration()
                start = fields.Datetime.from_string(vals['start_date'])
                vals['end_date'] = start + timedelta(minutes=duration)
                
        _logger.info("Appointment created: %s", vals_list)
        return super().create(vals_list)


    def write(self, vals):
        if 'state' in vals:
            for rec in self:
                old_state = rec.state
                new_state = vals.get('state')

                # DONE is fully locked
                if old_state == 'done' and new_state != 'done':
                    raise ValidationError("Done appointment cannot be modified!")

                # Allowed transitions
                allowed = {
                    'draft': ['requested'],
                    'requested': ['confirmed', 'cancel'],
                    'confirmed': ['done', 'cancel'],
                    'done': [],  # no movement
                    'cancel': ['draft'],  # optional
                }

                if new_state not in allowed.get(old_state, []):
                    raise ValidationError(
                        f"Invalid move: {old_state} → {new_state} not allowed!"
                    )

        return super().write(vals)
    # ================= VALIDATION =================

    @api.constrains('doctor_id', 'patient_id', 'start_date', 'end_date')
    def _check_doctor_schedule_rules(self):
        for rec in self:

            if not rec.doctor_id or not rec.patient_id or not rec.start_date or not rec.end_date:
                continue

            start = rec.start_date
            end = rec.end_date

            # End must be after start
            if end <= start:
                raise ValidationError(
                    "End time must be after Appointment time!"
                )

            # Start and End must be same day
            if start.date() != end.date():
                raise ValidationError(
                    "Appointment start and end date must be on the same day!"
                )

            # Duration validation
            duration = (end - start).total_seconds() / 60
            max_duration = rec.company_id.max_appointment_duration or 90

            if duration > max_duration:
                raise ValidationError(
                    f"Appointment duration cannot exceed {max_duration} minutes!"
                )

            # Past appointment check
            now = fields.Datetime.now()
            if start < now:
                raise ValidationError(
                    "You cannot create an appointment in the past!"
                )

            # Common overlap domain
            domain = [
                ('id', '!=', rec.id),
                ('state', '!=', 'cancel'),
                ('start_date', '<', end),
                ('end_date', '>', start),
            ]

            # Doctor overlap
            doctor_overlap = self.search(domain + [
                ('doctor_id', '=', rec.doctor_id.id)
            ], limit=1)

            if doctor_overlap:
                raise ValidationError(
                    "Doctor already has an appointment in this time slot!"
                )

            # Patient overlap
            patient_overlap = self.search(domain + [
                ('patient_id', '=', rec.patient_id.id)
            ], limit=1)

            if patient_overlap:
                raise ValidationError(
                    "Patient already has an appointment in this time slot!"
                )


    # ================= EMAIL HELPER =================

    def _send_email(self, template_xmlid, email_to=None):
        template = self.env.ref(template_xmlid, raise_if_not_found=False)

        if not template:
            return

        for rec in self:

            email_values = {}
            if email_to:
                email_values = {
                    'email_to': email_to,
                    'recipient_ids': [],
                }

            template.send_mail(rec.id, force_send=True, email_values=email_values)

    def action_request(self):

        if not (
            self.env.user.has_group('hospital_management.group_hospital_patient')
            or self.env.user.has_group('base.group_system')
        ):
            raise UserError("Only patient or admin can request appointment.")

        self.write({'state': 'requested'})
        
        for rec in self.filtered(lambda r: r.patient_id.email):
            rec._send_email(
                'hospital_management.email_template_appointment_requested',
                rec.doctor_id.email
            )

        return True

    def action_confirm(self):

        if not (
            self.env.user.has_group('hospital_management.group_hospital_doctor')
            or self.env.user.has_group('base.group_system')
        ):
            raise UserError("Only doctor or admin can confirm appointment.")

        for rec in self:

            # ================= STATE =================
            rec.write({'state': 'confirmed'})

            # ================= INVOICE CREATE =================
            if not rec.invoice_id:

                AccountMove = self.env['account.move'].sudo() 

                invoice = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': rec.patient_id.id,
                    'invoice_origin': rec.name,
                    'ref': rec.name,

                    'invoice_line_ids': [(0, 0, {
                        'name': f"Consultation - {rec.doctor_id.name}",
                        'quantity': 1,
                        'price_unit': rec.fees,
                    })],
                })

                invoice.action_post()
                invoice._portal_ensure_token()

                rec.invoice_id = invoice.id

            else:
                invoice = rec.invoice_id

            # ================= PDF GENERATE =================
            pdf, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'hospital_management.action_hospital_invoice_report',
                [invoice.id]
            )

            attachment = self.env['ir.attachment'].sudo().create({
                'name': f"Invoice_{invoice.name}.pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf), 
                'res_model': 'hospital.appointment',
                'res_id': rec.id,
                'mimetype': 'application/pdf',
            })

            # ================= SINGLE MAIL (CONFIRM + PDF) =================
            if rec.patient_id.email:

                template = self.env.ref('hospital_management.email_template_appointment_confirmed')

                # attach PDF
                template.attachment_ids = [(4, attachment.id)]

                template.send_mail(
                    rec.id,
                    force_send=True,
                    email_values={'email_to': rec.patient_id.email}
                )

                # ================= CHATTER =================
                body = template._render_field("body_html", rec.ids)[rec.id]

                rec.with_context(mail_notify_force_send=False).message_post(
                    body=body,
                    message_type='comment',
                    subtype_xmlid="mail.mt_comment"
                )

                # ❗ CLEANUP
                template.attachment_ids = [(5, 0, 0)]

        return True

    def action_cancel_with_mail(self):
        for rec in self:
            if rec.patient_id.email:
                rec._send_email(
                    'hospital_management.email_template_appointment_cancelled',
                    rec.patient_id.email
                )

            # CHATTER CONTENT
            template = self.env.ref('hospital_management.email_template_appointment_cancelled')

            body = template._render_field("body_html", rec.ids)[rec.id]

            rec.message_post(
                body=body,
                message_type='comment',
                subtype_xmlid="mail.mt_note"
            )

    def action_open_cancel_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Cancel Appointment',
            'res_model': 'appointment.cancel.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'hospital_management.view_cancel_wizard_form'
            ).id,
            'target': 'new',
            'context': {
                'default_appointment_id': self.id,
            }
        }

    def action_cancel_from_portal(self, reason=None):
        for rec in self:

            # reason set
            rec.cancel_reason = reason or "Cancelled from portal"

            # state change
            rec._set_state('cancel')

            # mail send (already existing method use)
            rec.action_cancel_with_mail()

    #state change helper
 
    def _set_state(self, state):
        self.write({'state': state})


    # ================= STATE ACTIONS =================

    def action_done(self):

        if not (
            self.env.user.has_group('hospital_management.group_hospital_doctor')
            or self.env.user.has_group('base.group_system')
        ):
            raise UserError("Only doctor or admin can mark appointment done.")

        for rec in self:
            if (
                rec.doctor_id.user_id != self.env.user
                and not self.env.user.has_group('base.group_system')
            ):
                raise UserError("You can update only your own appointments.")

        self._set_state('done')


    def action_cancel(self):

        if not (
            self.env.user.has_group('hospital_management.group_hospital_doctor')
            or self.env.user.has_group('base.group_system')
        ):
            raise UserError("Only doctor or admin can cancel appointment.")

        for rec in self:
            if (
                rec.doctor_id.user_id != self.env.user
                and not self.env.user.has_group('base.group_system')
            ):
                raise UserError("You can cancel only your own appointments.")

        self._set_state('cancel')

    def action_draft(self):

        if not self.env.user.has_group('base.group_system'):
            raise UserError("Only admin can reset appointment to draft.")

        self._set_state('draft')



    @api.model
    def send_appointment_reminders(self):

        reminder_days = self.env.company.reminder_days or 1

        today = fields.Date.context_today(self)
        target_date = today + timedelta(days=reminder_days)

        appointments = self.search([
            ('state', '=', 'confirmed')
        ])

        # Filter by date in user timezone
        appointments = appointments.filtered(
            lambda a: fields.Date.to_date(
                fields.Datetime.context_timestamp(self, a.start_date)
            ) == target_date
        )

        _logger.info("Appointments Found: %s", len(appointments))
        for appt in appointments:
            _logger.info("Processing Appointment: %s", appt.id)

            if appt.patient_id.email:
                appt._send_email(
                    'hospital_management.email_template_appointment_reminder',
                    appt.patient_id.email
                )


    @api.onchange('start_date')
    def _onchange_appointment_datetime(self):
        for rec in self:
            if rec.start_date:
                duration = rec._get_duration()
                rec.end_date = rec.start_date + timedelta(minutes=duration)


    def action_print_summary_report(self):

        appointments = self.search([])

        if not appointments:
            raise UserError("No Appointment Found!")

        return self.env.ref(
            "hospital_management.action_appointment_summary_report"
        ).report_action(appointments)

    def action_view_invoice(self):
        self.ensure_one()

        if not self.invoice_id:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.invoice_id.id,
            'target': 'current',
        }

    def action_preview_portal(self):
        self.ensure_one()

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        return {
            'type': 'ir.actions.act_url',
            'url': f"{base_url}/my/appointment/{self.id}?access_token={self._portal_ensure_token()}",
            'target': 'self',
        }