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

RRULE_TYPE_SELECTION_UI = [('daily', 'Daily'),('weekly', 'Weekly'),('monthly', 'Monthly'),
    ('yearly', 'Yearly'),('custom', 'Custom'),]

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    recurrence_id = fields.Many2one("calendar.recurrence")
    recurrency = fields.Boolean()
    rrule = fields.Char(related="recurrence_id.rrule", readonly=True, store=True,)
    rrule_type_ui = fields.Selection(RRULE_TYPE_SELECTION_UI,compute="_compute_rrule_type_ui",readonly=False,)
    rrule_type = fields.Selection(RRULE_TYPE_SELECTION,compute="_compute_recurrence",readonly=False,)
    interval = fields.Integer(compute="_compute_recurrence",readonly=False,)
    end_type = fields.Selection(END_TYPE_SELECTION,compute="_compute_recurrence",readonly=False,)
    count = fields.Integer(compute="_compute_recurrence",readonly=False,)
    until = fields.Date(compute="_compute_recurrence",readonly=False,)
    event_tz = fields.Selection( _tz_get,default=lambda self: self.env.context.get("tz") or self.env.user.tz,compute="_compute_recurrence", readonly=False,)
    mon = fields.Boolean(compute="_compute_recurrence", readonly=False)
    tue = fields.Boolean(compute="_compute_recurrence", readonly=False)
    wed = fields.Boolean(compute="_compute_recurrence", readonly=False)
    thu = fields.Boolean(compute="_compute_recurrence", readonly=False)
    fri = fields.Boolean(compute="_compute_recurrence", readonly=False)
    sat = fields.Boolean(compute="_compute_recurrence", readonly=False)
    sun = fields.Boolean(compute="_compute_recurrence", readonly=False)
    month_by = fields.Selection(MONTH_BY_SELECTION,compute="_compute_recurrence",readonly=False,)
    day = fields.Integer(compute="_compute_recurrence",readonly=False,)
    weekday = fields.Selection(WEEKDAY_SELECTION,compute="_compute_recurrence",readonly=False,)
    byday = fields.Selection(BYDAY_SELECTION,compute="_compute_recurrence",readonly=False,)

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

    maximum_discount = fields.Float(string="Maximum Discount",)

    @api.model
    def _get_recurrent_fields(self):
        return ['rrule_type','interval','count','end_type','until','event_tz','mon',
            'tue','wed','thu','fri','sat','sun','month_by','day','weekday','byday',]

    def _get_recurrence_params(self):
        self.ensure_one()
        return {
            'rrule_type': self.rrule_type,
            'interval': self.interval,
            'count': self.count,
            'end_type': self.end_type,
            'until': self.until,
            'event_tz': self.event_tz,
            'mon': self.mon,
            'tue': self.tue,
            'wed': self.wed,
            'thu': self.thu,
            'fri': self.fri,
            'sat': self.sat,
            'sun': self.sun,
            'month_by': self.month_by,
            'day': self.day,
            'weekday': self.weekday,
            'byday': self.byday,
        }

    @api.depends('recurrence_id', 'recurrency')
    def _compute_rrule_type_ui(self):
        defaults = self.env["calendar.recurrence"].default_get(["interval", "rrule_type"])
        for rec in self:
            if rec.recurrency:
                if rec.recurrence_id:
                    rec.rrule_type_ui = ('custom' if rec.recurrence_id.interval != 1 else rec.recurrence_id.rrule_type)
                else:
                    rec.rrule_type_ui = defaults["rrule_type"]
            else:
                rec.rrule_type_ui = False

    @api.depends('recurrence_id','recurrency','rrule_type_ui',)
    def _compute_recurrence(self):
        recurrence_fields = self._get_recurrent_fields()
        false_values = {
            field: False 
            for field in recurrence_fields
        }
        defaults = self.env['calendar.recurrence'].default_get(recurrence_fields)
        default_rrule_values = self.env['calendar.recurrence'].default_get(recurrence_fields)
        for rec in self:
            if rec.recurrency:
                current_rrule = (rec.rrule_type if rec.rrule_type_ui == "custom" else rec.rrule_type_ui)
                rec.update(defaults)
                values = rec._get_recurrence_params()
                rrule_values = {}

                if rec.recurrence_id:
                    rrule_values = {field: rec.recurrence_id[field]
                        for field in recurrence_fields if rec.recurrence_id[field]}

                if not rrule_values:
                    rrule_values = default_rrule_values

                rrule_values["rrule_type"] = (current_rrule or rrule_values.get("rrule_type") or defaults["rrule_type"])

                rec.update({ **false_values,**defaults, **values, **rrule_values,})
            else:
                rec.update(false_values)

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
            recurrence_values = {
                field: vals.pop(field)
                for field in recurrence_fields
                if field in vals
            }
            recurrence_data.append(recurrence_values)

        records = super().create(vals_list)

        for record, vals, recurrence_values in zip(records, vals_list, recurrence_data):
            if vals.get("recurrency"):
                record._apply_recurrence_values(recurrence_values)

        return records

    def write(self, vals):
        recurrence_fields = self._get_recurrent_fields()

        recurrence_values = {field: vals.pop(field)
            for field in recurrence_fields
            if field in vals
        }
        res = super().write(vals)
        for record in self:
            if record.recurrency:
                record._apply_recurrence_values(recurrence_values)
            elif record.recurrence_id:
                record.recurrence_id.unlink()
                record.recurrence_id = False
        return res

    @api.onchange("rrule_type_ui")
    def _onchange_rrule_type_ui(self):
        for rec in self:
            if not rec.rrule_type_ui:
                continue
            if rec.rrule_type_ui == "custom":
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
                rec.month_by = "date"
                rec.day = fields.Date.context_today(rec).day
            elif rec.rrule_type == "yearly":
                rec.month_by = "date"

    @api.onchange("rrule_type")
    def _onchange_rrule_type(self):
        for rec in self:
            if rec.rrule_type != "monthly":
                rec.month_by = "date"
                rec.day = 1
                rec.byday = False
                rec.weekday = False

    @api.onchange("end_type")
    def _onchange_end_type(self):
        for rec in self:
            if rec.end_type == "count":
                if not rec.count:
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
                continue
            rec.rrule_type_ui = False
            rec.rrule_type = False
            rec.interval = 1
            rec.count = 1
            rec.until = False
            rec.mon = False
            rec.tue = False
            rec.wed = False
            rec.thu = False
            rec.fri = False
            rec.sat = False
            rec.sun = False
            rec.month_by = "date"
            rec.day = 1
            rec.weekday = False
            rec.byday = False

    @api.onchange("enable_schedule")
    def _onchange_enable_schedule(self):
        for rec in self:
            if not rec.enable_schedule:
                rec.schedule_start_date = False
                rec.schedule_end_date = False

    @api.constrains("schedule_start_date", "schedule_end_date")
    def _check_schedule_dates(self):
        for rec in self:
            if (rec.enable_schedule and rec.schedule_start_date and rec.schedule_end_date and rec.schedule_start_date > rec.schedule_end_date):
                raise ValidationError(_("Start Date cannot be greater than End Date."))
            
    def is_schedule_active(self):
        self.ensure_one()
        if not self.enable_schedule:
            return True
        today = fields.Date.context_today(self)
        if self.schedule_start_date and today < self.schedule_start_date:
            return False
        if self.schedule_end_date and today > self.schedule_end_date:
            return False
        return True
    
    @api.onchange("enable_time_slot")
    def _onchange_enable_time_slot(self):
        for rec in self:
            if not rec.enable_time_slot:
                rec.time_slot_start = False
                rec.time_slot_end = False

    @api.constrains("time_slot_start", "time_slot_end")
    def _check_time_slot(self):
        for rec in self:
            if (rec.enable_time_slot and rec.time_slot_start and rec.time_slot_end and rec.time_slot_start >= rec.time_slot_end):
                raise ValidationError(_("Start Time must be less than End Time."))
            
    def is_time_slot_active(self):
        self.ensure_one()
        if not self.enable_time_slot:
            return True
        now = fields.Datetime.context_timestamp(self,fields.Datetime.now())
        current_time = now.hour + (now.minute / 60.0)
        return (self.time_slot_start <= current_time <= self.time_slot_end)
    
    def action_confirm(self):
        self.write({"state": "confirm"})

    def action_approve(self):
        self.write({"state": "approved"})

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        self.write({"state": "draft"})

    @api.constrains("enable_schedule","schedule_start_date","schedule_end_date","enable_time_slot","time_slot_start","time_slot_end",)
    def _check_pricelist_conflict(self):
        for rec in self:
            if not (rec.enable_schedule and rec.enable_time_slot and rec.schedule_start_date and rec.schedule_end_date):
                continue
            pricelists = self.search([("id", "!=", rec.id),("enable_schedule", "=", True),("enable_time_slot", "=", True),])
            for other in pricelists:
                if not (other.schedule_start_date and other.schedule_end_date):
                    continue
                date_overlap = (rec.schedule_start_date <= other.schedule_end_date and rec.schedule_end_date >= other.schedule_start_date)
                time_overlap = (rec.time_slot_start < other.time_slot_end and rec.time_slot_end > other.time_slot_start)
                if date_overlap and time_overlap:
                    raise ValidationError(
                        _(
                            "This schedule conflicts with pricelist '%s'. "
                            "Please choose another date or time slot."
                        ) % other.display_name
                    )
                
    @api.constrains("maximum_discount")
    def _check_maximum_discount(self):
        for rec in self:
            if rec.maximum_discount and not (1 <= rec.maximum_discount <= 100):
                raise ValidationError(_("Maximum Discount must be between 1 and 100."))
            

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)
        fields += [
            "enable_schedule",
            "schedule_start_date",
            "schedule_end_date",
            "enable_time_slot",
            "time_slot_start",
            "time_slot_end",
            "state",
            "maximum_discount",
            "recurrency",
            "rrule_type",
            "interval",
            "mon",
            "tue",
            "wed",
            "thu",
            "fri",
            "sat",
            "sun",
            "month_by",
            "day",
            "weekday",
            "byday",
        ]
        return fields