# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PurchaseQtyWizard(models.TransientModel):
    _name = 'purchase.qty.wizard'
    _description = 'Purchase Quantity Mismatch Confirmation Wizard'
    purchase_id = fields.Many2one('purchase.order',string="Purchase Order",readonly=True,)
    picking_id = fields.Many2one('stock.picking',string="Receipt",readonly=True,)
    is_receipt = fields.Boolean(string="From Receipt",readonly=True,)
    line_ids = fields.One2many('purchase.qty.wizard.line','wizard_id',string="Invoice Changes",)

    def action_confirm_update(self):
        self.ensure_one()

        if self.is_receipt:
            for line in self.line_ids:
                if not line.po_line_id:
                    continue
                move = self.picking_id.move_ids.filtered(lambda m: m.purchase_line_id == line.po_line_id)[:1]
                if move:
                    move.quantity = line.invoice_qty
        else:
            for line in self.line_ids:
                if line.is_new_product:
                    self.purchase_id._create_po_line_from_invoice({
                        "name": line.invoice_name,
                        "qty": line.invoice_qty,
                        "price": line.price_unit,
                        "discount": line.discount,
                        "tax": line.tax_rate,
                    })
                    continue
                if line.po_line_id:
                    line.po_line_id.write({
                        "product_qty": line.invoice_qty,
                    })
        return {"type": "ir.actions.client","tag": "reload",}


class PurchaseQtyWizardLine(models.TransientModel):
    _name = 'purchase.qty.wizard.line'
    _description = 'Purchase Quantity Mismatch Line'

    wizard_id = fields.Many2one('purchase.qty.wizard',string="Wizard",ondelete="cascade",)
    po_line_id = fields.Many2one('purchase.order.line',string="PO Line",readonly=True,)
    product_id = fields.Many2one('product.product',string="Existing Product",readonly=True,)
    invoice_name = fields.Char(string="Invoice Product",readonly=True,)
    display_name = fields.Char(string="Product",compute="_compute_display_name",)

    @api.depends("product_id", "invoice_name")
    def _compute_display_name(self):
        for line in self:
            line.display_name = (line.product_id.display_name if line.product_id else line.invoice_name)

    is_new_product = fields.Boolean(string="New Product",readonly=True,)
    action_name = fields.Char(string="Action",compute="_compute_action_name",)

    @api.depends("is_new_product")
    def _compute_action_name(self):
        for line in self:
            line.action_name = ("Add New Product" if line.is_new_product else "Update Quantity")
    po_qty = fields.Float(string="Current Qty", readonly=True,)
    invoice_qty = fields.Float(string="Invoice Qty",readonly=True,)
    price_unit = fields.Float(string="Price",readonly=True,)
    discount = fields.Float(string="Discount",readonly=True,)
    tax_rate = fields.Float(string="Tax %",readonly=True,)