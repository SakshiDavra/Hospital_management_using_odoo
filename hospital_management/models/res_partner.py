from odoo import models, fields, api
from odoo.fields import Domain
from odoo.models import Constraint
import secrets
from odoo.exceptions import ValidationError, UserError

class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "mail.thread", "mail.activity.mixin"]
    
    # ================= ROLES =================
    role_ids = fields.Many2many(
        'hospital.role',
        string="Hospital Roles",
        tracking=True
    )

    user_id = fields.Many2one(
        'res.users',
        string="User",
        readonly=True
    )
    # ================= COMMON HOSPITAL CODE =================
    hospital_code = fields.Char(
        string="Code",
        readonly=True,
        copy=False,
        tracking=True
    )

    # ================= DOCTOR FIELDS =================
    specialization_id = fields.Many2one(
        'hospital.specialization',
        string="Specialization",
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )
    consultation_fees = fields.Monetary(
            string="Consultation Fees",
            currency_field="currency_id",
            tracking=True
        )

    slot_ids = fields.Many2many(
        'hospital.doctor.schedule',
        'doctor_slot_rel',
        'doctor_id',
        'slot_id',
        string="Available Slots"

    )

    # ================= PATIENT FIELDS =================
    age = fields.Integer(string="Age" , tracking=True)

    blood_group = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'),
        ('o+', 'O+'), ('o-', 'O-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'),
    ], string="Blood Group" , tracking=True)

    # ================= UNIQUE CONSTRAINT =================
    @api.constrains('hospital_code')
    def _check_unique_code(self):
        for rec in self:
            if rec.hospital_code:
                existing = self.search([
                    ('hospital_code', '=', rec.hospital_code),
                    ('id', '!=', rec.id)
                ])
                if existing:
                    raise ValidationError("Hospital code must be unique!")

    # ================= APPOINTMENT COUNTS =================
    appointment_count = fields.Integer(
        string="Doctor Appointments",
        compute="_compute_appointment_count"
    )

    patient_appointment_count = fields.Integer(
        string="Patient Appointments",
        compute="_compute_patient_appointment_count"
    )

    # ================= NAME DISPLAY =================
    def name_get(self):
        result = []
        for rec in self:

            name = rec.name or ""

            # Doctor hoy to code + specialization show
            if 'Doctor' in rec.role_ids.mapped('name'):
                code = rec.hospital_code or ''
                spec = rec.specialization_id.name if rec.specialization_id else ''

                if spec:
                    name = f"[{code}] {rec.name} ({spec})"
                else:
                    name = f"[{code}] {rec.name}"

            # Patient hoy to code + name
            elif 'Patient' in rec.role_ids.mapped('name'):
                code = rec.hospital_code or ''
                name = f"[{code}] {rec.name}"

            result.append((rec.id, name))

        return result

    @api.model_create_multi
    def create(self, vals_list):

        doctor_role = self.env.ref('hospital_management.role_doctor')
        patient_role = self.env.ref('hospital_management.role_patient')

        doctor_group = self.env.ref('hospital_management.group_hospital_doctor')
        patient_group = self.env.ref('hospital_management.group_hospital_patient')

        # ---------- SEQUENCE ----------
        for vals in vals_list:
            role_ids = []
            for command in vals.get('role_ids', []):
                if command[0] == 6:
                    role_ids.extend(command[2])
                elif command[0] == 4:
                    role_ids.append(command[1])

            if doctor_role.id in role_ids:
                vals['hospital_code'] = self.env['ir.sequence'].next_by_code('hospital.doctor')
            elif patient_role.id in role_ids:
                vals['hospital_code'] = self.env['ir.sequence'].next_by_code('hospital.patient')

        # ---------- CREATE PARTNER ----------
        records = super().create(vals_list)

        # ---------- USER + GROUP ----------
        for rec in records:

            if doctor_role not in rec.role_ids and patient_role not in rec.role_ids:
                continue

            if not rec.email:
                raise UserError("Email required to create user.")

            # check existing user
            user = self.env['res.users'].sudo().search([
                ('login', '=', rec.email)
            ], limit=1)

            # create if not exist
            if not user:
                user = self.env['res.users'].sudo().create({
                    'name': rec.name,
                    'login': rec.email,
                    'partner_id': rec.id,
                    'email': rec.email,
                    'password': secrets.token_urlsafe(8),
                })
                user.action_reset_password()

            # link user
            rec.user_id = user.id

            # assign groups
            if doctor_role in rec.role_ids and doctor_group.id not in user.group_ids.ids:
                user.write({'group_ids': [(4, doctor_group.id)]})

            if patient_role in rec.role_ids and patient_group.id not in user.group_ids.ids:
                user.write({'group_ids': [(4, patient_group.id)]})

        return records
            
    # ================= NAME SEARCH =================
    def name_search(self, name='', args=None, operator='ilike', limit=100):

        args = args or []
        context = self.env.context

        if context.get('from_appointment_doctor'):

            doctor_role = self.env.ref('hospital_management.role_doctor').id

            domain = [('role_ids', 'in', [doctor_role])]

            specialization_id = context.get('filter_specialization_id')
            if specialization_id:
                domain.append(('specialization_id', '=', specialization_id))

            args = Domain.AND([args, domain])

        return super().name_search(name, args, operator, limit)

    # ================= DOCTOR APPOINTMENT COUNT =================
    def _compute_appointment_count(self):
        for rec in self:
            rec.appointment_count = self.env['hospital.appointment'].search_count([
                ('doctor_id', '=', rec.id)
            ])

    def action_view_appointments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form',
            'domain': [('doctor_id', '=', self.id)],
            'context': {'default_doctor_id': self.id},
        }

    # ================= PATIENT APPOINTMENT COUNT =================
    def _compute_patient_appointment_count(self):
        for rec in self:
            rec.patient_appointment_count = self.env['hospital.appointment'].search_count([
                ('patient_id', '=', rec.id)
            ])

    def action_view_patient_appointments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appointments',
            'res_model': 'hospital.appointment',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],
            'context': {'default_patient_id': self.id},
        }

    # ================= WRITE =================
    def write(self, vals):
        res = super().write(vals)

        if 'consultation_fees' in vals:
            self.message_post(
                body="Consultation fees updated."
            )

        return res