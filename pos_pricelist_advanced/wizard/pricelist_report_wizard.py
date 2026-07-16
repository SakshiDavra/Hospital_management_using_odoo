# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PricelistReportWizard(models.TransientModel):
    _name = "pos.pricelist.report.wizard"
    _description = "POS Pricelist Sales Report Wizard"

    pricelist_ids = fields.Many2many("product.pricelist",string="Pricelists",)
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    group_by = fields.Selection(
        [("none", "No Group"),("config", "POS Shop"),("session", "POS Session"),],
        string="Group By",default="none",)

    def _get_orders(self):
        domain = []
        if self.pricelist_ids:
            domain.append(("pricelist_id", "in", self.pricelist_ids.ids))
        if self.date_from:
            domain.append(("date_order", ">=", self.date_from))
        if self.date_to:
            domain.append(("date_order", "<=", self.date_to))
        orders = self.env["pos.order"].search(domain)
        return orders

    def action_print_report(self):
        orders = self._get_orders()
        data = {"wizard_id": self.id,"ids": orders.ids,"model": "pos.order",}

        return self.env.ref("pos_pricelist_advanced.action_pricelist_sales_report").report_action(orders,data=data)
