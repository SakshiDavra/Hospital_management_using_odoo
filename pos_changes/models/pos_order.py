from odoo import models, api
import logging

_logger = logging.getLogger(__name__) 

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

            hsn = line.product_id.l10n_in_hsn_code

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
        currency = self.currency_id or self.company_id.currency_id

        for line in self.lines:
            taxes = line.tax_ids_after_fiscal_position

            for tax in taxes:
                group = tax.tax_group_id
                key = group.id

                if key not in result:
                    result[key] = {
                        'id': group.id,
                        'name': group.name,
                        'rate': tax.amount,
                        'base': 0,
                        'amount': 0,
                    }

                # NO ROUND HERE
                result[key]['base'] += line.price_subtotal
                result[key]['amount'] += (
                    line.price_subtotal_incl - line.price_subtotal
                )

        # ROUND ONLY AT END
        for val in result.values():
            val['base'] = currency.round(val['base'])
            val['amount'] = currency.round(val['amount'])

        return sorted(result.values(), key=lambda x: x['id'])
    
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
            unit_price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

            #  COMBO TOTAL
            if line.combo_line_ids:
                combo_total = sum(l.price_subtotal_incl for l in line.combo_line_ids)
            else:
                combo_total = line.price_subtotal_incl

            result.append({
                'name': line.full_product_name,
                'qty': line.qty,
                'is_child': is_child,

                'unit_price': round(unit_price, 2),

                # FIXED PRICE
                'price': 0 if is_child else round(combo_total, 2),

                'discount': line.discount,

                # MAIN FIX HERE
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
        ignored_product_ids = self._get_ignored_product_ids_total_discount() if hasattr(self, '_get_ignored_product_ids_total_discount') else []
        
        total_discount = 0.0
        currency = self.currency_id

        discount_policy = 'with_discount'
        if self.config_id:
            discount_policy = getattr(self.config_id, 'discount_policy', 'with_discount')

        for line in self.lines:
            if line.product_id.id in ignored_product_ids:
                continue

            is_without_discount = (discount_policy == 'without_discount')

            original_unit_price = line.product_id.lst_price if (is_without_discount and line.discount == 0) else line.price_unit

            orig_taxes = line.tax_ids_after_fiscal_position.compute_all(
                original_unit_price, 
                currency, 
                line.qty, 
                product=line.product_id, 
                partner=self.partner_id
            )

            discounted_unit_price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            current_taxes = line.tax_ids_after_fiscal_position.compute_all(
                discounted_unit_price, 
                currency, 
                line.qty, 
                product=line.product_id, 
                partner=self.partner_id
            )

            discount_on_this_line = orig_taxes['total_included'] - current_taxes['total_included']
            
            if discount_on_this_line > 0:
                total_discount += discount_on_this_line

        return currency.round(total_discount)
    
    def _prepare_stock_move_vals(
        self,
        picking,
        order_line,
        picking_type,
        vals
    ):
        res = super()._prepare_stock_move_vals(
            picking,
            order_line,
            picking_type,
            vals
        )

        if order_line.custom_location_id:
            res['custom_location_id'] = order_line.custom_location_id.id

        return res

    # def _create_picking(self):
    #     res = super()._create_picking()

    #     for order in self:
    #         for picking in order.picking_ids:
    #             for move in picking.move_ids:

    #                 line = order.lines.filtered(
    #                     lambda l: l.product_id == move.product_id
    #                 )[:1]

    #                 if line and line.custom_location_id:

    #                     # MOVE LOCATION
    #                     move.location_id = line.custom_location_id.id

    #                     # MOVE LINE LOCATION
    #                     move.move_line_ids.write({
    #                         'location_id': line.custom_location_id.id
    #                     })

    #     return res