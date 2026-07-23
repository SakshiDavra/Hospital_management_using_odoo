from odoo import models


class PosConfig(models.Model):
    _inherit = "pos.config"

    def get_new_pricelists(self, loaded_ids):
        self.ensure_one()
        pricelists = self.available_pricelist_ids.filtered(lambda p: p.id not in loaded_ids)
        items = self.env["product.pricelist.item"].search([
            ("pricelist_id", "in", pricelists.ids),*self.env["product.pricelist.item"]._check_company_domain(self.company_id),])
        return {
            "pricelists": pricelists._load_pos_data_read(pricelists, self),
            "items": items.read(items._load_pos_data_fields(self),load=False,),
        }
    