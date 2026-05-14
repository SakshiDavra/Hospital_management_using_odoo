from odoo import models, fields
from odoo.tools.float_utils import float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    custom_location_id = fields.Many2one(
        "stock.location",
        string="Preferred Location"
    )

    def _action_assign(self):

        moves_with_custom = self.filtered(
            lambda m:
                m.custom_location_id
                and m.state in ['confirmed', 'waiting', 'partially_available']
        )

        normal_moves = self - moves_with_custom

        # NORMAL ODOO FLOW
        result = super(
            StockMove,
            normal_moves
        )._action_assign()

        for move in moves_with_custom:

            needed_qty = move.product_uom_qty

            # already reserved qty
            reserved_qty = sum(
                move.move_line_ids.mapped('quantity')
            )

            remaining_qty = needed_qty - reserved_qty

            if float_is_zero(
                remaining_qty,
                precision_rounding=move.product_uom.rounding
            ):
                continue

            # AVAILABLE IN PREFERRED LOCATION
            available_qty = self.env[
                'stock.quant'
            ]._get_available_quantity(
                move.product_id,
                move.custom_location_id,
                strict=True
            )

            reserve_qty = min(
                remaining_qty,
                available_qty
            )

            # STEP 1:
            # reserve from preferred location first
            if reserve_qty > 0:

                self.env[
                    'stock.quant'
                ]._update_reserved_quantity(
                    move.product_id,
                    move.custom_location_id,
                    reserve_qty,
                    lot_id=False,
                    package_id=False,
                    owner_id=False,
                    strict=True
                )

                self.env['stock.move.line'].create({
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'location_id': move.custom_location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'quantity': reserve_qty,
                    'picking_id': move.picking_id.id,
                })

            # STEP 2:
            # let Odoo reserve remaining qty
            super(StockMove, move.with_context(skip_custom_reservation=True))._action_assign()

        return result