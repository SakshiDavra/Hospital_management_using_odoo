from collections import defaultdict

from odoo import api, models


class PricelistSalesReport(models.AbstractModel):
    _name = "report.pos_pricelist_advanced.pricelist_sales_report"
    _description = "POS Pricelist Sales Report"
    @api.model
    def _get_report_values(self, docids, data=None):

        if data and data.get("ids"):
            orders = self.env["pos.order"].browse(data["ids"])
        else:
            orders = self.env["pos.order"].browse(docids)

        wizard = False
        if data and data.get("wizard_id"):
            wizard = self.env["pos.pricelist.report.wizard"].browse(data["wizard_id"])
        group_by = wizard.group_by if wizard else "none"
        total_sales = 0
        total_qty = 0
        flat_data = []
        grouped_data = defaultdict(list)
        for order in orders:
            total_sales += order.amount_total
            if group_by == "session":
                group_name = order.session_id.name or "No Session"
            elif group_by == "config":
                group_name = order.config_id.name or "No Shop"
            else:
                group_name = False
            for line in order.lines:
                total_qty += line.qty
                line_vals = {
                    "order": order.name,
                    "date": order.date_order,
                    "customer": order.partner_id.name or "",
                    "pricelist": order.pricelist_id.name or "",
                    "product": line.product_id.display_name,
                    "qty": line.qty,
                    "price": line.price_unit,
                    "discount": line.discount,
                    "subtotal": line.price_subtotal_incl,
                }
                if group_by in ("session", "config"):
                    grouped_data[group_name].append(line_vals)
                else:
                    flat_data.append(line_vals)
        return {
            "doc_ids": orders.ids,
            "doc_model": "pos.order",
            "docs": orders,
            "wizard": wizard,
            "group_by": group_by,
            "flat_data": flat_data,
            "grouped_data": dict(grouped_data),
            "total_orders": len(orders),
            "total_qty": total_qty,
            "total_sales": total_sales,
        }