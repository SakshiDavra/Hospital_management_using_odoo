# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_upload_invoice(self, file_name=False, file_type=False, file_data=False, **kwargs):
        self.ensure_one()
        po = self.move_ids.purchase_line_id.order_id[:1]
        if not po:
            raise UserError("Purchase Order not found for this receipt.")
        
        return po.action_upload_invoice(
            file_name=file_name,
            file_type=file_type,
            file_data=file_data,
            from_model="stock.picking",
            picking_id=self.id
        )