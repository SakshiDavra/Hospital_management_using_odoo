from odoo import api, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    @api.onchange(
        'request_date_from_period',
        'request_date_to_period'
    )
    def _onchange_half_day_custom(self):

        self.request_unit_half = True
        self._compute_date_from_to()
        self._compute_duration()
