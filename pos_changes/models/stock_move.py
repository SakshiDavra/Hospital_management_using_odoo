from odoo import models, fields


class StockMove(models.Model):
    _inherit = "stock.move"

    custom_location_id = fields.Many2one(
        "stock.location",
        string="Preferred Location"
    )

    def _action_assign(self):

        moves_with_custom = self.filtered(
            lambda m: m.custom_location_id
        )

        moves_without_custom = self - moves_with_custom

        # custom reservation
        for move in moves_with_custom:

            available_qty = self.env['stock.quant']._get_available_quantity(
                move.product_id,
                move.custom_location_id,
            )

            reserve_qty = min(
                available_qty,
                move.product_uom_qty
            )

            if reserve_qty > 0:

                move._update_reserved_quantity(
                    reserve_qty,
                    move.custom_location_id,
                    strict=False
                )

        # only normal moves use default logic
        return super(
            StockMove,
            moves_without_custom
        )._action_assign()