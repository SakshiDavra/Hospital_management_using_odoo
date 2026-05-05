from odoo import api, models
import math

class PosReceiptReport(models.AbstractModel):
    _name = 'report.pos_changes.pos_order_receipt_backend'

    def _get_line_count(self, text, max_chars=30):
        if not text:
            return 1
        return max(1, math.ceil(len(text) / max_chars))

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['pos.order'].browse(docids)

        #  FIX 1: remove default big height
        max_total_height = 0

        for order in docs:
            height = 0

            height += 50

            if order.partner_id:
                name_lines = self._get_line_count(order.partner_id.name, 30)

                addr = " ".join(filter(None, [
                    order.partner_id.street,
                    order.partner_id.street2,
                    order.partner_id.city,
                    order.partner_id.zip,
                ]))
                addr_lines = self._get_line_count(addr, 35)

                height += (name_lines * 5) + (addr_lines * 5)

                if order.partner_id.phone:
                    height += 5

            # ===============================
            # PRODUCTS (FINAL FIX)  
            # ===============================
            lines = order.get_pos_ui_lines()

            for line in lines:
                is_child = line.get('is_child')

                # base line
                height += 6.4
                # product name
                name_lines = self._get_line_count(line.get('name'), 28)
                height += (name_lines - 1) * 7

                # unit price only for parent (POS style)
                if not is_child:
                    height += 3

                # discount only parent
                if line.get('discount') and not is_child:
                    height += 3.2


            # -------- TOTAL --------
            height += 20

            taxes = order.get_tax_breakup()
            for tax in taxes:
                text = f"Tax {tax['rate']}% on {tax['base']}"
                lines_count = self._get_line_count(text, 30)
                height += lines_count * 6

            # -------- PAYMENTS --------
            height += len(order.payment_ids) * 6

            # -------- DISCOUNT TOTAL --------
            if any(l.discount for l in order.lines if not l.combo_parent_id):
                height += 10

            # -------- QR --------
            height += 45

            # -------- HSN --------
            hsn_codes = set(filter(None, order.lines.mapped('product_id.l10n_in_hsn_code')))
            if hsn_codes:
                height += 8
                height += len(hsn_codes) * 6.5

            # -------- FOOTER --------
            height += 15

            max_total_height = max(max_total_height, height)

        paper_format = self.env.ref('pos_changes.paperformat_pos_receipt')

        # round height properly
        paper_format.sudo().write({
            'page_height': math.ceil(max_total_height)
        })

        return {
            'doc_ids': docids,
            'doc_model': 'pos.order',
            'docs': docs,
        }