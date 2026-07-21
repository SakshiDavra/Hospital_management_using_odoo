# -*- coding: utf-8 -*-

from odoo import fields, models


class PricelistReportWizard(models.TransientModel):
    _name = "pos.pricelist.report.wizard"
    _description = "POS Pricelist Sales Report Wizard"

    pricelist_ids = fields.Many2many("product.pricelist",string="Pricelists",)
    config_id = fields.Many2one("pos.config", string="POS Shop",)
    session_id = fields.Many2one("pos.session",string="POS Session",)
    cashier_id = fields.Many2one("hr.employee",string="Cashier",)
    date_from = fields.Date(string="Date From",)
    date_to = fields.Date(string="Date To",)
    group_by = fields.Selection(
        [
            ("none", "No Group"),
            ("config", "POS Shop"),
            ("session", "POS Session"),
            ("cashier", "Cashier"),
        ],
        string="Group By",
        default="none",
    )

    def _get_orders(self):
        domain = []
        if self.pricelist_ids:
            domain.append(("pricelist_id", "in", self.pricelist_ids.ids))
        if self.config_id:
            domain.append(("config_id", "=", self.config_id.id))
        if self.session_id:
            domain.append(("session_id", "=", self.session_id.id))
        if self.cashier_id:
            domain.append(("employee_id", "=", self.cashier_id.id))
        if self.date_from:
            domain.append(("date_order", ">=", self.date_from))
        if self.date_to:
            domain.append(("date_order", "<=", self.date_to))
        return self.env["pos.order"].search(domain)

    def action_print_report(self):
        orders = self._get_orders()
        data = {
            "wizard_id": self.id,
            "ids": orders.ids,
            "model": "pos.order",
            "group_by": self.group_by,
            "config_id": self.config_id.id if self.config_id else False,
            "session_id": self.session_id.id if self.session_id else False,
            "cashier_id": self.cashier_id.id if self.cashier_id else False,
        }

        return self.env.ref(
            "pos_pricelist_advanced.action_pricelist_sales_report"
        ).report_action(
            orders,
            data=data,
        )