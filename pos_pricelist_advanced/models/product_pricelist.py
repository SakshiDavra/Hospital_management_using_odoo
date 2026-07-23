# -*- coding: utf-8 -*-

import logging
from collections import defaultdict
from datetime import datetime, time

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.calendar.models.calendar_recurrence import (
    RRULE_TYPE_SELECTION, END_TYPE_SELECTION, MONTH_BY_SELECTION,
    WEEKDAY_SELECTION, BYDAY_SELECTION,
)

_logger = logging.getLogger(__name__)

RRULE_TYPE_SELECTION_UI = [
    ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'),
    ('yearly', 'Yearly'), ('custom', 'Custom'),
]

RECURRENT_FIELDS = [
    'rrule_type', 'interval', 'count', 'end_type', 'until', 'event_tz',
    'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
    'month_by', 'day', 'weekday', 'byday',
]

WEEKDAYS = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')
RECURRENCE_TRIGGER_FIELDS = set(RECURRENT_FIELDS) | {'recurrency', 'rrule_type_ui'}


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    recurrence_id = fields.Many2one("calendar.recurrence", ondelete="set null")
    recurrency = fields.Boolean()
    rrule = fields.Char(related="recurrence_id.rrule", readonly=True, store=True)
    rrule_type_ui = fields.Selection(RRULE_TYPE_SELECTION_UI, default="weekly")
    rrule_type = fields.Selection(RRULE_TYPE_SELECTION, default="weekly")
    interval = fields.Integer(default=1)
    end_type = fields.Selection(END_TYPE_SELECTION, default="forever")
    count = fields.Integer(default=1)
    until = fields.Date()
    event_tz = fields.Selection( _tz_get, string="Timezone", default=lambda self: self.env.context.get("tz") or self.env.user.tz,)
    mon = fields.Boolean()
    tue = fields.Boolean()
    wed = fields.Boolean()
    thu = fields.Boolean()
    fri = fields.Boolean()
    sat = fields.Boolean()
    sun = fields.Boolean()

    month_by = fields.Selection(MONTH_BY_SELECTION, default="date")
    day = fields.Integer(default=1)
    weekday = fields.Selection(WEEKDAY_SELECTION)
    byday = fields.Selection(BYDAY_SELECTION)

    enable_schedule = fields.Boolean()
    schedule_start_date = fields.Date()
    schedule_end_date = fields.Date()

    enable_time_slot = fields.Boolean()
    time_slot_start = fields.Float()
    time_slot_end = fields.Float()

    state = fields.Selection([
        ("draft", "Draft"), ("confirm", "Waiting Approval"),
        ("approved", "Approved"), ("cancelled", "Cancelled"),
    ], default="draft", tracking=True)

    maximum_discount = fields.Float()
    manager_pin_required = fields.Boolean()
    is_available = fields.Boolean(compute="_compute_is_available", store=False)

    def _is_yearly_occurrence(self, today):
        start_date = self.schedule_start_date
        rule = self.recurrence_id._get_rrule(dtstart=datetime.combine(start_date, time.min))
        window = self.schedule_end_date - self.schedule_start_date

        last_occurrence = None
        for occ in rule:
            occ_date = occ.date()
            if occ_date > today:
                break
            last_occurrence = occ_date

        if not last_occurrence:
            return False
        return last_occurrence <= today <= last_occurrence + window

    def is_pricelist_available_today(self):
        self.ensure_one()
        today = fields.Date.context_today(self)

        if self.rrule_type != 'yearly' and self.enable_schedule:
            if self.schedule_start_date and today < self.schedule_start_date:
                return False
            if self.schedule_end_date and today > self.schedule_end_date:
                return False

        if not self.recurrency:
            return True
        if not self.recurrence_id:
            return False

        start_date = self.schedule_start_date if (self.enable_schedule and self.schedule_start_date) else today
        try:
            if self.rrule_type == 'yearly' and self.enable_schedule and self.schedule_start_date and self.schedule_end_date:
                return self._is_yearly_occurrence(today)
            rule = self.recurrence_id._get_rrule(dtstart=datetime.combine(start_date, time.min))
            return bool(rule.between(datetime.combine(today, time.min), datetime.combine(today, time.max), inc=True))
        except (ValueError, TypeError):
            _logger.exception("Recurrence evaluation failed for pricelist %s", self.id)
            return False

    @api.depends('recurrency', 'recurrence_id', 'recurrence_id.rrule', 'enable_schedule',
                 'schedule_start_date', 'schedule_end_date', 'rrule_type', 'month_by',
                 'day', 'weekday', 'byday')
    def _compute_is_available(self):
        for r in self:
            r.is_available = r.is_pricelist_available_today()

    @api.onchange('recurrence_id')
    def _onchange_recurrence_id(self):
        if self.recurrence_id:
            for f in RECURRENT_FIELDS:
                self[f] = self.recurrence_id[f]
            self.rrule_type_ui = 'custom' if self.recurrence_id.interval != 1 else self.recurrence_id.rrule_type

    def _apply_recurrence_values(self, values):
        self.ensure_one()
        if not self.recurrency:
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
            self.recurrence_id = self.env["calendar.recurrence"].create(values)

    def _unlink_recurrence_if_orphan(self):
        self.ensure_one()
        recurrence = self.recurrence_id
        if not recurrence:
            return
        other_users = self.search_count([
            ("recurrence_id", "=", recurrence.id),
            ("id", "!=", self.id),
        ])
        self.recurrence_id = False
        if not other_users:
            recurrence.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        recurrence_data = []
        for vals in vals_list:
            rv = {f: vals.get(f) for f in RECURRENT_FIELDS if f in vals}
            if vals.get('rrule_type_ui') and vals.get('rrule_type_ui') != 'custom':
                rv['rrule_type'] = vals['rrule_type_ui']
            recurrence_data.append(rv)

        records = super().create(vals_list)
        for record, vals, rv in zip(records, vals_list, recurrence_data):
            if vals.get("recurrency") and rv:
                record._apply_recurrence_values(rv)
        return records

    def write(self, vals):
        if 'rrule_type_ui' in vals and vals['rrule_type_ui'] != 'custom':
            vals['rrule_type'] = vals['rrule_type_ui']

        recurrence_touched = bool(RECURRENCE_TRIGGER_FIELDS & vals.keys())
        res = super().write(vals)

        if recurrence_touched:
            for record in self:
                if record.recurrency:
                    record._apply_recurrence_values({f: record[f] for f in RECURRENT_FIELDS})
                elif record.recurrence_id:
                    record._unlink_recurrence_if_orphan()
        return res

    def _reset_fields(self, field_names):
        for r in self:
            for fname in field_names:
                r[fname] = False

    @api.onchange("rrule_type_ui")
    def _onchange_rrule_type_ui(self):
        for r in self:
            if not r.rrule_type_ui or r.rrule_type_ui == "custom":
                continue
            r.rrule_type = r.rrule_type_ui
            r.interval = 1
            if r.rrule_type == "weekly":
                wd = fields.Date.context_today(r).weekday()
                for i, day in enumerate(WEEKDAYS):
                    r[day] = (wd == i)
            elif r.rrule_type in ("monthly", "yearly"):
                r.month_by = r.month_by or "date"
                if r.rrule_type == "monthly" and r.month_by == "date" and (not r.day or r.day == 1):
                    r.day = fields.Date.context_today(r).day

    @api.onchange("rrule_type")
    def _onchange_rrule_type(self):
        for r in self:
            if r.rrule_type not in ("monthly", "yearly"):
                r.month_by = "date"
                r.day = 1
                r.byday = False
                r.weekday = False

    @api.onchange("end_type")
    def _onchange_end_type(self):
        for r in self:
            if r.end_type == "count":
                r.count = r.count or 1
                r.until = False
            elif r.end_type == "end_date":
                r.count = 0
                r.until = r.until or fields.Date.context_today(r)
            elif r.end_type == "forever":
                r.count = 0
                r.until = False

    @api.onchange("recurrency")
    def _onchange_recurrency(self):
        for r in self:
            if r.recurrency:
                r.month_by = r.month_by or "date"

    @api.onchange("enable_schedule")
    def _onchange_enable_schedule(self):
        for r in self:
            if not r.enable_schedule:
                r._reset_fields(["schedule_start_date", "schedule_end_date"])

    @api.onchange("enable_time_slot")
    def _onchange_enable_time_slot(self):
        for r in self:
            if not r.enable_time_slot:
                r._reset_fields(["time_slot_start", "time_slot_end"])

    @api.constrains("enable_schedule", "schedule_start_date", "schedule_end_date")
    def _check_schedule_dates(self):
        for r in self:
            if r.enable_schedule and (not r.schedule_start_date or not r.schedule_end_date):
                raise ValidationError(_("Please set both Schedule Start Date and Schedule End Date."))
            if r.enable_schedule and r.schedule_start_date and r.schedule_end_date and r.schedule_start_date > r.schedule_end_date:
                raise ValidationError(_("Schedule Start Date must be before End Date."))

    @api.constrains("enable_time_slot", "time_slot_start", "time_slot_end")
    def _check_time_slot(self):
        for r in self:
            if not r.enable_time_slot:
                continue
            if r.time_slot_start is False or r.time_slot_end is False:
                raise ValidationError(_("Please set both Start Time and End Time."))
            if r.time_slot_start == r.time_slot_end:
                raise ValidationError(_("Start Time and End Time cannot be the same."))

    @api.constrains("maximum_discount")
    def _check_maximum_discount(self):
        for r in self:
            if r.maximum_discount and not (1 <= r.maximum_discount <= 100):
                raise ValidationError(_("Maximum Discount must be between 1 and 100."))

    @api.constrains(
        "name", "enable_schedule", "schedule_start_date", "schedule_end_date",
        "enable_time_slot", "time_slot_start", "time_slot_end", "recurrency", "rrule_type",
        "mon", "tue", "wed", "thu", "fri", "sat", "sun", "month_by", "day", "weekday", "byday",
    )
    def _check_pricelist_conflict(self):
        candidates = self.filtered(lambda r: r.enable_schedule and r.enable_time_slot and r.schedule_start_date and r.schedule_end_date)
        if not candidates:
            return
        for record in candidates:
            others = self.search([
                ("id", "!=", record.id),("name", "=", record.name),("enable_schedule", "=", True),("enable_time_slot", "=", True),
                ("schedule_start_date", "<=", record.schedule_end_date), ("schedule_end_date", ">=", record.schedule_start_date),
                ("time_slot_start", "<", record.time_slot_end),("time_slot_end", ">", record.time_slot_start),
            ])
            for other in others:
                if record._conflicts_with(other):
                    raise ValidationError( _("A duplicate pricelist schedule already exists for '%s'.")% other.display_name)

    def _conflicts_with(self, other):
        self.ensure_one()

        same = (self.recurrency == other.recurrency and self.rrule_type == other.rrule_type)
        if self.recurrency and other.recurrency:
            if self.rrule_type == "weekly":
                same = same and all(self[d] == other[d] for d in WEEKDAYS)
            elif self.rrule_type in ("monthly", "yearly"):
                same = (same and self.month_by == other.month_by and self.day == other.day
                    and self.weekday == other.weekday and self.byday == other.byday)
        return same

    def _check_manager_rights(self):
        if not self.env.user.has_group('point_of_sale.group_pos_manager'):
            raise UserError(_("Only a POS Manager can perform this action."))

    def action_confirm(self):
        self.write({"state": "confirm"})

    def action_approve(self):
        self._check_manager_rights()
        self.write({"state": "approved"})

    def action_cancel(self):
        self._check_manager_rights()
        self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        self._check_manager_rights()
        self.write({"state": "draft"})

    @api.model
    def _load_pos_data_fields(self, config):
        return super()._load_pos_data_fields(config) + [
            "enable_schedule", "schedule_start_date", "schedule_end_date",
            "enable_time_slot", "time_slot_start", "time_slot_end",
            "state", "maximum_discount", "recurrency", "manager_pin_required",
            "is_available", "rrule", "until", "end_type", "recurrence_id",
            "rrule_type",
        ]