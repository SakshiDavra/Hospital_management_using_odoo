from odoo import api, models, _
from odoo.exceptions import ValidationError


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    def _validate_total_discount(self):
        for item in self:
            pricelist = item.pricelist_id
            if not pricelist or not pricelist.maximum_discount:
                continue

            total = sum(line.percent_price
                for line in pricelist.item_ids
                if line.compute_price == "percentage"
            )

            if total > pricelist.maximum_discount:
                raise ValidationError(_("Total discount cannot exceed %.2f%%.") % pricelist.maximum_discount)

    @api.onchange("percent_price", "compute_price")
    def _onchange_total_discount_limit(self):
        self._validate_total_discount()

    @api.constrains("percent_price", "compute_price", "pricelist_id")
    def _check_total_discount_limit(self):
        self._validate_total_discount()
        