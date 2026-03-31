from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HospitalDoctorSchedule(models.Model):
    _name = 'hospital.doctor.schedule'
        # Reverse relation: Doctors using this slot
    doctor_ids = fields.Many2many(
        'res.partner',
        'doctor_slot_rel',   # SAME relation table name
        'slot_id',           # this model column
        'doctor_id',         # res.partner column
        string="Assigned Doctors"
    )
    _description = 'Doctor Weekly Time Slot'
    _rec_name = 'display_name'

    # ================= TIME SLOT GENERATOR =================
    def _get_time_slots(self):
        slots = []
        for hour in range(0, 24):
            for minute in (0, 30):

                float_val = hour + minute / 60.0

                hour_12 = hour % 12 or 12
                am_pm = "AM" if hour < 12 else "PM"

                label = f"{hour_12:02d}:{minute:02d} {am_pm}"
                slots.append((float_val, label))

        return slots

    # ================= FIELDS =================
    

    day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string="Available Day", required=True)

    start_time = fields.Selection(
        selection=_get_time_slots,
        string="Start Time",
        required=True
    )

    end_time = fields.Selection(
        selection=_get_time_slots,
        string="End Time",
        required=True
    )

    display_name = fields.Char(
        compute="_compute_display_name",
        store=True
    )

    @api.depends('day', 'start_time', 'end_time')
    def _compute_display_name(self):
        day_map = {
            '0': 'Mon', '1': 'Tue', '2': 'Wed',
            '3': 'Thu', '4': 'Fri', '5': 'Sat', '6': 'Sun'
        }

        for rec in self:
            day = day_map.get(rec.day, '')
            rec.display_name = f"{day} {rec.start_time} - {rec.end_time}"

    
    @api.constrains('start_time', 'end_time')
    def _check_time_valid(self):
        for rec in self:
            if float(rec.start_time) >= float(rec.end_time):
                raise ValidationError("End Time must be greater than Start Time.")

    @api.constrains('day', 'start_time', 'end_time')
    def _check_unique_slot(self):
        for rec in self:
            existing = self.search([
                ('id', '!=', rec.id),
                ('day', '=', rec.day),
                ('start_time', '=', rec.start_time),
                ('end_time', '=', rec.end_time),
            ], limit=1)

            if existing:
                raise ValidationError(
                    "This time slot already exists!"
                )