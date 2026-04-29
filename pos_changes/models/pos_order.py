from odoo import models

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def action_print_receipt(self):
        return self.env.ref('pos_changes.action_pos_order_receipt_backend').report_action(self)