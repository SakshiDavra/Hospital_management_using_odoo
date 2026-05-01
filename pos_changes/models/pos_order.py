from odoo import models

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def action_print_receipt(self):
        return self.env.ref('pos_changes.action_pos_order_receipt_backend').report_action(self)

    def get_display_lines(self):
        self.ensure_one()  # IMPORTANT

        result = []
        for line in self.lines:
            if line.combo_line_ids:
                result.append(line)
                result.extend(line.combo_line_ids)
            elif not line.combo_parent_id:
                result.append(line)

        return result or []  # SAFE RETURN
    
    def get_hsn_summary(self):
        result = {}

        for line in self.lines:

            if line.combo_parent_id:
                continue

            #  REMOVE N/A
            hsn = line.product_id.l10n_in_hsn_code

            #  SKIP if empty
            if not hsn:
                continue

            taxes = line.tax_ids_after_fiscal_position

            gst_taxes = taxes.filtered(
                lambda t: hasattr(t, 'l10n_in_tax_type') and t.l10n_in_tax_type
            )

            rate = sum(t.amount for t in gst_taxes)

            if hsn not in result:
                result[hsn] = {
                    'rate': rate,
                    'amount': 0,
                    'base': 0,
                }

            result[hsn]['base'] += line.price_subtotal
            result[hsn]['amount'] += (line.price_subtotal_incl - line.price_subtotal)

        return result
    
    def get_tax_breakup(self):
        result = {}

        for line in self.lines:

            taxes = line.tax_ids_after_fiscal_position

            for tax in taxes:
                group = tax.tax_group_id

                # GROUP BY tax group (NOT rate)
                key = group.id

                if key not in result:
                    result[key] = {
                        'name': group.name,
                        'rate': tax.amount,   # display purpose
                        'base': 0,
                        'amount': 0,
                    }

                base = line.price_subtotal
                tax_amt = line.price_subtotal_incl - line.price_subtotal

                result[key]['base'] += base
                result[key]['amount'] += tax_amt

        return list(result.values())
    
    def get_pos_lines(self):
        result = []

        for line in self.lines:
            is_child = bool(line.combo_parent_id)

            result.append({
                'name': line.full_product_name,
                'qty': line.qty,
                'is_child': is_child,
                'unit_price': line.price_unit,
                'discount': line.discount,

                # KEY LOGIC
                'price': 0 if is_child else line.price_subtotal_incl,
            })

        return result
    
    def get_pos_ui_lines(self):
        result = []

        for line in self.lines:

            is_child = bool(line.combo_parent_id)

            qty = line.qty or 1
            unit_price = line.price_subtotal_incl / qty if qty else 0

            # ✅ COMBO TOTAL
            if line.combo_line_ids:
                combo_total = sum(l.price_subtotal_incl for l in line.combo_line_ids)
            else:
                combo_total = line.price_subtotal_incl

            result.append({
                'name': line.full_product_name,
                'qty': line.qty,
                'is_child': is_child,

                'unit_price': round(unit_price, 2),

                # ✅ FIXED PRICE
                'price': 0 if is_child else round(combo_total, 2),

                'discount': line.discount,

                # ✅ MAIN FIX HERE
                'no_discount_price': round(self.get_no_discount_price(line), 2),
            })

        return result
    
    def get_no_discount_price(self, line):

        #  COMBO CASE
        if line.combo_line_ids:
            total = 0
            for child in line.combo_line_ids:

                taxes = child.tax_ids_after_fiscal_position.compute_all(
                    child.price_unit,
                    quantity=child.qty,
                    currency=line.order_id.currency_id
                )

                total += taxes['total_included']

            return total

        #  NORMAL PRODUCT
        taxes = line.tax_ids_after_fiscal_position.compute_all(
            line.price_unit,
            quantity=line.qty,
            currency=line.order_id.currency_id
        )

        return taxes['total_included']
    def compute_pos_discount_total(self):
        self.ensure_one()

        currency = self.currency_id or self.company_id.currency_id
        total_discount = 0.0

        for line in self.lines:

            if line.combo_parent_id:
                continue

            price_unit = line.price_unit
            qty = line.qty
            discount = line.discount or 0.0

            # WITH discount
            discounted_unit = price_unit * (1 - discount / 100.0)

            taxes_with_discount = line.tax_ids_after_fiscal_position.compute_all(
                discounted_unit,
                quantity=qty,
                currency=currency
            )

            # WITHOUT discount
            taxes_without_discount = line.tax_ids_after_fiscal_position.compute_all(
                price_unit,
                quantity=qty,
                currency=currency
            )

            total_discount += (
                taxes_without_discount['total_included']
                - taxes_with_discount['total_included']
            )

        return currency.round(total_discount)