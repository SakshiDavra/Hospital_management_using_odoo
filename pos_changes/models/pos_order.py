from odoo import models

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _generate_pos_order_invoice(self):
        invoice = super()._generate_pos_order_invoice()

        if invoice.state == 'posted':
            invoice.button_draft()

        return invoice