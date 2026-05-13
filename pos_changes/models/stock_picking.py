from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _prepare_stock_move_vals(
        self,
        first_line,
        order_lines
    ):

        vals = super()._prepare_stock_move_vals(
            first_line,
            order_lines
        )

        # selected location
        if first_line.custom_location_id:

            vals['custom_location_id'] = (
                first_line.custom_location_id.id
            )

        return vals