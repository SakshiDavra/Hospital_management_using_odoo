from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_upload_invoice(self, attachment_ids):

        print("Attachment IDS :", attachment_ids)

        return False