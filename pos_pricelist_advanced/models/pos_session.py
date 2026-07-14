from odoo import models

class PosSession(models.Model):
    _inherit = "pos.session"

    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)

        if self._name == "product.pricelist":
            fields += [
                "enable_schedule",
                "schedule_start_date",
                "schedule_end_date",
                "enable_time_slot",
                "time_slot_start",
                "time_slot_end",
                "state",
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
            ]
        return fields