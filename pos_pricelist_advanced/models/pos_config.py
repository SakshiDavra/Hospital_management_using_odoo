from odoo import models
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"

    def get_new_pricelists(self, loaded_ids):
        self.ensure_one()

        pricelists = self.available_pricelist_ids.filtered(
            lambda p: p.id not in loaded_ids
        )
        return pricelists._load_pos_data_read(pricelists, self)