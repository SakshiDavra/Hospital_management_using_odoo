# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class PurchaseBillValidationWizard(models.TransientModel):
    _name = "purchase.bill.validation.wizard"
    _description = "Purchase Bill Validation Wizard"

    purchase_id = fields.Many2one("purchase.order", string="Purchase Order", required=True, readonly=True)
    line_ids = fields.One2many("purchase.bill.validation.wizard.line", "wizard_id", string="Mismatch Lines")

    def action_apply_and_create_bill(self):
        self.ensure_one()

        unmatched = self.line_ids.filtered(lambda l: not l.po_line_id)
        if unmatched:
            raise UserError(_(
                "These invoice products are not on the Purchase Order at all: %s.\n"
                "Please add them to the Purchase Order (or correct the invoice) "
                "before creating the Vendor Bill - a quantity fix alone can't "
                "resolve a missing product."
            ) % ", ".join(unmatched.mapped("invoice_name")))

        for line in self.line_ids:
            po_line = line.po_line_id

            if line.new_po_qty < 0 or line.new_receipt_qty < 0:
                raise UserError(_("Quantities cannot be negative."))

            if line.new_po_qty and float_compare(
                line.new_po_qty, po_line.product_qty, precision_rounding=po_line.product_uom_id.rounding
            ) != 0:
                po_line.product_qty = line.new_po_qty

            if line.new_receipt_qty:
                move = line._get_done_move()
                if move and float_compare(
                    line.new_receipt_qty, move.quantity, precision_rounding=move.product_uom.rounding
                ) != 0:
                    move.quantity = line.new_receipt_qty

        validation = self.purchase_id._check_bill_validation(self.purchase_id.ocr_json)
        if validation:
            return validation

        return self.purchase_id._create_vendor_bill_from_saved_ocr()

    def action_cancel(self):
        return {"type": "ir.actions.act_window_close"}


class PurchaseBillValidationWizardLine(models.TransientModel):
    _name = "purchase.bill.validation.wizard.line"
    _description = "Purchase Bill Validation Wizard Line"

    wizard_id = fields.Many2one("purchase.bill.validation.wizard", required=True, ondelete="cascade")
    po_line_id = fields.Many2one("purchase.order.line", string="PO Line", readonly=True)
    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    invoice_name = fields.Char(string="Invoice Product", readonly=True)
    is_new_product = fields.Boolean(string="New Product", compute="_compute_is_new_product")

    @api.depends("po_line_id")
    def _compute_is_new_product(self):
        for line in self:
            line.is_new_product = not bool(line.po_line_id)

    display_name = fields.Char(string="Product", compute="_compute_display_name")
    po_qty = fields.Float(string="PO Qty", readonly=True)
    receipt_qty = fields.Float(string="Received Qty", readonly=True)
    invoice_qty = fields.Float(string="Invoice Qty", readonly=True)
    new_po_qty = fields.Float(string="New PO Qty")
    new_receipt_qty = fields.Float(string="New Receipt Qty")

    @api.depends("product_id", "po_line_id", "invoice_name")
    def _compute_display_name(self):
        for line in self:
            line.display_name = (line.product_id.display_name or line.po_line_id.product_id.display_name or line.invoice_name or "")

    def _get_done_move(self):
        self.ensure_one()
        if not self.po_line_id:
            return self.env["stock.move"]
        return self.wizard_id.purchase_id.picking_ids.filtered(
            lambda p: p.picking_type_id.code == "incoming" and p.state == "done").move_ids.filtered(lambda m: m.purchase_line_id == self.po_line_id)[:1]