# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PurchaseBillValidationWizard(models.TransientModel):
    _name = "purchase.bill.validation.wizard"
    _description = "Purchase Bill Validation Wizard"
    purchase_id = fields.Many2one("purchase.order",string="Purchase Order",required=True,readonly=True,)
    line_ids = fields.One2many("purchase.bill.validation.wizard.line","wizard_id",string="Mismatch Lines",)

    def action_confirm(self):
        self.ensure_one()
        validation = self.purchase_id._check_bill_validation(self.purchase_id.ocr_json)
        if validation:
            return validation
        return self.purchase_id._create_vendor_bill_from_saved_ocr()
    def action_cancel(self):
        return {"type": "ir.actions.act_window_close"}


class PurchaseBillValidationWizardLine(models.TransientModel):
    _name = "purchase.bill.validation.wizard.line"
    _description = "Purchase Bill Validation Wizard Line"

    wizard_id = fields.Many2one("purchase.bill.validation.wizard",required=True,ondelete="cascade",)
    po_line_id = fields.Many2one("purchase.order.line",string="PO Line",readonly=True,)
    product_id = fields.Many2one("product.product",string="Product",readonly=True,)
    invoice_name = fields.Char(string="Invoice Product",readonly=True,)
    is_new_product = fields.Boolean(string="New Product",compute="_compute_is_new_product",)

    @api.depends("po_line_id")
    def _compute_is_new_product(self):
        for line in self:
            line.is_new_product = not bool(line.po_line_id)

    display_name = fields.Char(string="Product",compute="_compute_display_name",)
    po_qty = fields.Float(string="PO Qty",readonly=True,)
    receipt_qty = fields.Float(string="Received Qty",readonly=True,)
    invoice_qty = fields.Float(string="Invoice Qty",readonly=True,)

    @api.depends("product_id", "po_line_id", "invoice_name")
    def _compute_display_name(self):
        for line in self:
            line.display_name = (
                line.product_id.display_name
                or line.po_line_id.product_id.display_name
                or line.invoice_name
                or ""
            )