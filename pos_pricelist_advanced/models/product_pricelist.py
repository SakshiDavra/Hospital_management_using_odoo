# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.calendar.models.calendar_recurrence import (
    RRULE_TYPE_SELECTION,
    END_TYPE_SELECTION,
    MONTH_BY_SELECTION,
    WEEKDAY_SELECTION,
    BYDAY_SELECTION,
)
from datetime import datetime, time, timedelta
import pytz
import logging
_logger = logging.getLogger(__name__)

RRULE_TYPE_SELECTION_UI = [
    ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'),
    ('yearly', 'Yearly'), ('custom', 'Custom'),
]

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    recurrence_id = fields.Many2one("calendar.recurrence", string="Recurrence Template", ondelete="set null")
    recurrency = fields.Boolean(string="Is Recurrent")
    rrule = fields.Char(related="recurrence_id.rrule", readonly=True, store=True)
    
    rrule_type_ui = fields.Selection(RRULE_TYPE_SELECTION_UI, string="Recurrence Type UI", default="weekly")
    
    rrule_type = fields.Selection(RRULE_TYPE_SELECTION, string="Recurrence Freq", default="weekly")
    interval = fields.Integer(string="Repeat Every", default=1)
    end_type = fields.Selection(END_TYPE_SELECTION, string="Recurrence Termination", default="forever")
    count = fields.Integer(string="Number of Repetitions", default=1)
    until = fields.Date(string="Repeat Until")
    event_tz = fields.Selection(_tz_get, string="Timezone", default=lambda self: self.env.context.get("tz") or self.env.user.tz)
    
    mon = fields.Boolean(string="Mon")
    tue = fields.Boolean(string="Tue")
    wed = fields.Boolean(string="Wed")
    thu = fields.Boolean(string="Thu")
    fri = fields.Boolean(string="Fri")
    sat = fields.Boolean(string="Sat")
    sun = fields.Boolean(string="Sun")
    
    month_by = fields.Selection(MONTH_BY_SELECTION, string="Option", default="date")
    day = fields.Integer(string="Date of month", default=1)
    weekday = fields.Selection(WEEKDAY_SELECTION, string="Day of week")
    byday = fields.Selection(BYDAY_SELECTION, string="Day")
    enable_schedule = fields.Boolean(string="Enable Schedule")
    schedule_start_date = fields.Date(string="Start Date")
    schedule_end_date = fields.Date(string="End Date")

    enable_time_slot = fields.Boolean(string="Enable Time Slot")
    time_slot_start = fields.Float(string="Start Time")
    time_slot_end = fields.Float(string="End Time")

    state = fields.Selection([
        ("draft", "Draft"),
        ("confirm", "Waiting Approval"),
        ("approved", "Approved"),
        ("cancelled", "Cancelled"),
    ], default="draft", tracking=True)

    maximum_discount = fields.Float(string="Maximum Discount")
    manager_pin_required = fields.Boolean(string="Manager PIN Required")
    is_available = fields.Boolean(string="Is Available Today", compute="_compute_is_available", store=False)

    def is_pricelist_available_today(self):
        self.ensure_one()
        if not self.recurrency:
            return True
        if not self.recurrence_id:
            return False

        try:
            today_date = fields.Date.context_today(self)
            start_of_today = datetime.combine(today_date, time.min)
            end_of_today = datetime.combine(today_date, time.max)
            if self.rrule_type == 'monthly':
                base_start_date = self.schedule_start_date if (self.enable_schedule and self.schedule_start_date) else today_date
                dtstart = datetime.combine(base_start_date, time.min)
                rule = self.recurrence_id._get_rrule(dtstart=dtstart)
                if self.month_by == 'date':
                    if today_date.day != self.day:
                        return False
                elif self.month_by == 'day':
                    today_occurrence = list(rule.between(start_of_today, end_of_today, inc=True))
                    if not today_occurrence:
                        return False
                if self.enable_schedule and self.schedule_start_date and self.schedule_end_date:
                    return self.schedule_start_date <= today_date <= self.schedule_end_date
                return True
            elif self.rrule_type == 'yearly' and self.enable_schedule and self.schedule_start_date and self.schedule_end_date:
                base_start_date = self.schedule_start_date
                dtstart = datetime.combine(base_start_date, time.min)
                
                rule = self.recurrence_id._get_rrule(dtstart=dtstart)
                
                start_search = datetime.combine(base_start_date, time.min)
                end_search = datetime.combine(today_date, time.max)
                occurrences = list(rule.between(start_search, end_search, inc=True))                
                if not occurrences:
                    return False
                last_occurrence = occurrences[-1].date()
                duration = self.schedule_end_date - self.schedule_start_date                
                window_start = last_occurrence
                window_end = last_occurrence + duration
                return window_start <= today_date <= window_end

            else:
                base_start_date = self.schedule_start_date if (self.enable_schedule and self.schedule_start_date) else today_date
                dtstart = datetime.combine(base_start_date, time.min)
                
                rule = self.recurrence_id._get_rrule(dtstart=dtstart)
                occurrences = list(rule.between(start_of_today, end_of_today, inc=True))
                return bool(occurrences)
            
        except Exception:
            _logger.exception("RECURRENCE ERROR")
            return False

    @api.depends('recurrency', 'recurrence_id', 'recurrence_id.rrule', 'enable_schedule', 'schedule_start_date', 'schedule_end_date', 'rrule_type', 'month_by', 'day', 'weekday', 'byday')
    def _compute_is_available(self):
        for rec in self:
            rec.is_available = rec.is_pricelist_available_today()

    @api.model
    def _get_recurrent_fields(self):
        return [
            'rrule_type', 'interval', 'count', 'end_type', 'until', 'event_tz', 
            'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 
            'month_by', 'day', 'weekday', 'byday'
        ]

    def _get_recurrence_params(self):
        self.ensure_one()
        return {field: self[field] for field in self._get_recurrent_fields()}

    @api.onchange('recurrence_id')
    def _onchange_recurrence_id(self):
        if self.recurrence_id:
            recurrence_fields = self._get_recurrent_fields()
            for field in recurrence_fields:
                self[field] = self.recurrence_id[field]
            self.rrule_type_ui = 'custom' if self.recurrence_id.interval != 1 else self.recurrence_id.rrule_type

    def _apply_recurrence_values(self, values):
        self.ensure_one()
        if not self.recurrency:
            if self.recurrence_id:
                self.recurrence_id.unlink()
                self.recurrence_id = False
            return

        values.setdefault("interval", 1)
        values.setdefault("rrule_type", "weekly")
        values.setdefault("month_by", "date")
        
        if values.get("end_type") == "count":
            values.setdefault("count", 1)
        if values.get("end_type") == "end_date" and not values.get("until"):
            values["until"] = fields.Date.context_today(self)

        if self.recurrence_id:
            self.recurrence_id.write(values)
        else:
            recurrence = self.env["calendar.recurrence"].create(values)
            self.recurrence_id = recurrence

    @api.model_create_multi
    def create(self, vals_list):
        recurrence_fields = self._get_recurrent_fields()
        recurrence_data = []
        
        for vals in vals_list:
            recurrence_values = {field: vals.get(field) for field in recurrence_fields if field in vals}
            if vals.get('rrule_type_ui') and vals.get('rrule_type_ui') != 'custom':
                recurrence_values['rrule_type'] = vals['rrule_type_ui']
            recurrence_data.append(recurrence_values)

        records = super().create(vals_list)

        for record, vals, recurrence_values in zip(records, vals_list, recurrence_data):
            if vals.get("recurrency") and recurrence_values:
                record._apply_recurrence_values(recurrence_values)
        return records

    def write(self, vals):
        recurrence_fields = self._get_recurrent_fields()
        if 'rrule_type_ui' in vals and vals['rrule_type_ui'] != 'custom':
            vals['rrule_type'] = vals['rrule_type_ui']
            
        recurrence_values = {field: vals.get(field) for field in recurrence_fields if field in vals}
        res = super().write(vals)

        for record in self:
            if record.recurrency:
                if recurrence_values or 'recurrency' in vals or 'rrule_type_ui' in vals:
                    base_data = record._get_recurrence_params()
                    record._apply_recurrence_values(base_data)
            elif record.recurrence_id:
                record.recurrence_id.unlink()
                record.recurrence_id = False
        return res

    @api.onchange("rrule_type_ui")
    def _onchange_rrule_type_ui(self):
        for rec in self:
            if not rec.rrule_type_ui or rec.rrule_type_ui == "custom":
                continue
            rec.rrule_type = rec.rrule_type_ui
            rec.interval = 1
            if rec.rrule_type == "weekly":
                today = fields.Date.context_today(rec).weekday()
                rec.mon = today == 0
                rec.tue = today == 1
                rec.wed = today == 2
                rec.thu = today == 3
                rec.fri = today == 4
                rec.sat = today == 5
                rec.sun = today == 6
            elif rec.rrule_type == "monthly":
                if not rec.month_by:
                    rec.month_by = "date"
                if rec.month_by == "date" and (not rec.day or rec.day == 1):
                    rec.day = fields.Date.context_today(rec).day
            elif rec.rrule_type == "yearly":
                if not rec.month_by:
                    rec.month_by = "date"

    @api.onchange("rrule_type")
    def _onchange_rrule_type(self):
        for rec in self:
            if rec.rrule_type not in ("monthly", "yearly"):
                rec.month_by = "date"
                rec.day = 1
                rec.byday = False
                rec.weekday = False

    @api.onchange("end_type")
    def _onchange_end_type(self):
        for rec in self:
            if rec.end_type == "count":
                if not rec.count or rec.count == 0:
                    rec.count = 1
                rec.until = False
            elif rec.end_type == "end_date":
                rec.count = 0
                if not rec.until:
                    rec.until = fields.Date.today()
            elif rec.end_type == "forever":
                rec.count = 0
                rec.until = False

    @api.onchange("recurrency")
    def _onchange_recurrency(self):
        for rec in self:
            if rec.recurrency:
                if not rec.month_by:
                    rec.month_by = "date"
                continue
            rec.rrule_type_ui = "weekly"
            rec.rrule_type = "weekly"
            rec.interval = 1
            rec.count = 1
            rec.until = False
            rec.mon = rec.tue = rec.wed = rec.thu = rec.fri = rec.sat = rec.sun = False
            rec.month_by = "date"
            rec.day = 1
            rec.weekday = rec.byday = False

    @api.onchange("enable_schedule")
    def _onchange_enable_schedule(self):
        for rec in self:
            if not rec.enable_schedule:
                rec.schedule_start_date = False
                rec.schedule_end_date = False

    @api.constrains("enable_schedule", "schedule_start_date", "schedule_end_date")
    def _check_schedule_dates(self):
        for rec in self:
            if rec.enable_schedule and (not rec.schedule_start_date or not rec.schedule_end_date):
                raise ValidationError(_("Please set both Start Date and End Date."))
                
    @api.onchange("enable_time_slot")
    def _onchange_enable_time_slot(self):
        for rec in self:
            if not rec.enable_time_slot:
                rec.time_slot_start = False
                rec.time_slot_end = False

    @api.constrains("enable_time_slot", "time_slot_start", "time_slot_end")
    def _check_time_slot(self):
        for rec in self:
            if rec.enable_time_slot and (rec.time_slot_start is False or rec.time_slot_end is False):
                raise ValidationError(_("Please set both Start Time and End Time."))
            if rec.enable_time_slot and rec.time_slot_start >= rec.time_slot_end:
                raise ValidationError(_("Start Time must be less than End Time."))
    
    def action_confirm(self): self.write({"state": "confirm"})
    def action_approve(self): self.write({"state": "approved"})
    def action_cancel(self): self.write({"state": "cancelled"})
    def action_reset_to_draft(self): self.write({"state": "draft"})

    @api.constrains(
        "name", "enable_schedule", "schedule_start_date", "schedule_end_date",
        "enable_time_slot", "time_slot_start", "time_slot_end", "recurrency", "rrule_type",
        "mon", "tue", "wed", "thu", "fri", "sat", "sun", "month_by", "day", "weekday", "byday",
    )
    def _check_pricelist_conflict(self):
        for rec in self:
            if not (rec.enable_schedule and rec.enable_time_slot and rec.schedule_start_date and rec.schedule_end_date):
                continue

            pricelists = self.search([
                ("id", "!=", rec.id), ("name", "=", rec.name),
                ("enable_schedule", "=", True), ("enable_time_slot", "=", True),
            ])

            for other in pricelists:
                if not (other.schedule_start_date and other.schedule_end_date):
                    continue

                date_overlap = rec.schedule_start_date <= other.schedule_end_date and rec.schedule_end_date >= other.schedule_start_date
                time_overlap = rec.time_slot_start < other.time_slot_end and rec.time_slot_end > other.time_slot_start
                same_recurrence = rec.recurrency == other.recurrency and rec.rrule_type == other.rrule_type

                if rec.recurrency and other.recurrency:
                    if rec.rrule_type == "weekly":
                        same_recurrence = (
                            same_recurrence and rec.mon == other.mon and rec.tue == other.tue 
                            and rec.wed == other.wed and rec.thu == other.thu and rec.fri == other.fri 
                            and rec.sat == other.sat and rec.sun == other.sun
                        )
                    elif rec.rrule_type in ("monthly", "yearly"):
                        same_recurrence = (
                            same_recurrence and rec.month_by == other.month_by and rec.day == other.day 
                            and rec.weekday == other.weekday and rec.byday == other.byday
                        )

                if date_overlap and time_overlap and same_recurrence:
                    raise ValidationError(_("A duplicate pricelist schedule already exists for '%s'.") % other.display_name)
                
    @api.constrains("maximum_discount")
    def _check_maximum_discount(self):
        for rec in self:
            if rec.maximum_discount and not (1 <= rec.maximum_discount <= 100):
                raise ValidationError(_("Maximum Discount must be between 1 and 100."))

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)
        fields += [
            "enable_schedule", "schedule_start_date", "schedule_end_date",
            "enable_time_slot", "time_slot_start", "time_slot_end", "state",
            "maximum_discount", "recurrency", "manager_pin_required", 
            "is_available","rrule","until","end_type","recurrence_id","rrule_type"
        ]
        return fields