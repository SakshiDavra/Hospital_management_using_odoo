from odoo import api, models

class PosReceiptReport(models.AbstractModel):
    _name = 'report.pos_changes.pos_order_receipt_backend'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['pos.order'].browse(docids)

        max_total_height = 120

        for order in docs:
            height = 0

            # -------- FIXED --------
            height += 45 # header

            # -------- CUSTOMER --------
            if order.partner_id:
                height += 18

            # -------- PRODUCTS --------
            for line in order.lines:
                height += 11.5

                if line.discount:
                    height += 7

                if line.full_product_name and '\n' in line.full_product_name:
                    height += 10

            # -------- TOTAL --------
            height += 12

            if order.amount_tax:
                height += 6

            # -------- PAYMENTS --------
            height += len(order.payment_ids) * 6

            # -------- DISCOUNT TOTAL --------
            if any(l.discount for l in order.lines):
                height += 12.5

            # -------- QR --------
            height += 45

            # -------- HSN --------
            hsn_codes = set(order.lines.mapped('product_id.l10n_in_hsn_code'))
            if hsn_codes:
                height += 11.5
                height += len(hsn_codes) * 7.2

            # -------- FOOTER --------
            height += 16

            max_total_height = max(max_total_height, height)

        paper_format = self.env.ref('pos_changes.paperformat_pos_receipt')
        paper_format.sudo().write({'page_height': max_total_height})

        return {
            'doc_ids': docids,
            'doc_model': 'pos.order',
            'docs': docs,
        }