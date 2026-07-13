# -*- coding: utf-8 -*-
import re
from difflib import SequenceMatcher
from odoo import models, fields, _, Command
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
from ..utils.ocr_engine import ProductionOCRProcessor

_LEADING_ROW_NUMBER_RE = re.compile(r'^\s*\d+\s*[\.\-\)]*\s*')

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    ocr_json = fields.Json(string="OCR Data", copy=False)
    over_receipt_json = fields.Json(string="Over Receipt Data", copy=False)

    @staticmethod
    def _clean_ocr_name(name):
        text = re.sub(r"\s+", " ", (name or "").replace("\n", " ").strip())
        return _LEADING_ROW_NUMBER_RE.sub("", text).strip()

    def _get_or_create_tax(self, rate):
        if not rate:
            return False
        domain = [("amount", "=", rate), ("type_tax_use", "=", "purchase"), ("company_id", "=", self.company_id.id)]
        tax = self.env["account.tax"].search(domain, limit=1)
        if not tax:
            try:
                tax = self.env["account.tax"].create({
                    "name": f"Purchase GST {rate:g}%", "amount_type": "percent",
                    "amount": rate, "type_tax_use": "purchase", "company_id": self.company_id.id, "sequence": 10
                })
            except Exception:
                return False
        return tax

    def action_upload_invoice(self, file_name=False, file_type=False, file_data=False, from_model="purchase.order", picking_id=False, **kwargs):
        self.ensure_one()
        if not file_data:
            return False

        attachment = self.env["ir.attachment"].create({
            'name': file_name or 'Vendor_Invoice.pdf', 'mimetype': file_type or 'application/pdf',
            'datas': file_data, 'res_model': self._name, 'res_id': self.id,
        })

        ocr_result = self._process_uploaded_invoice_base(attachment)
        incoming_pickings = self.picking_ids.filtered(lambda p: p.picking_type_id.code == 'incoming' and p.state != 'cancel')

        if self.state in ('purchase', 'done') and incoming_pickings and all(p.state == 'done' for p in incoming_pickings):
            return self._create_vendor_bill_after_receipt(ocr_result)

        if from_model == "purchase.order":
            return self._sync_draft_po_from_invoice(ocr_result) if self.state in ("draft", "sent") else self._update_po_qty_from_invoice(ocr_result)

        if from_model == "stock.picking" and picking_id:
            picking = self.env['stock.picking'].browse(picking_id)
            if picking.state not in ('done', 'cancel'):
                return self._update_receipt_qty_from_invoice(ocr_result, picking)
        return True

    def _create_vendor_bill_after_receipt(self, ocr_result):
        self.ensure_one()
        if not ocr_result or not ocr_result.get("lines"):
            raise UserError(_("OCR data or invoice lines not found."))
        validation = self._check_bill_validation(ocr_result)
        return validation if validation else self._create_vendor_bill_from_saved_ocr()

    def _sync_draft_po_from_invoice(self, ocr_result):
        self.ensure_one()
        if not self.order_line:
            for item in ocr_result.get("lines", []):
                self._create_po_line_from_invoice(item)
            return self._send_notification(_("Success"), _("Purchase Order created successfully from Invoice."))

        used_po_lines, mismatched_lines = set(), []

        for item in ocr_result.get("lines", []):
            invoice_qty = float(item.get("qty") or 0.0)
            if invoice_qty <= 0:
                continue

            best_line = self._find_best_po_line(item.get("name"), used_po_lines)
            if best_line:
                used_po_lines.add(best_line.id)
                if float_compare(best_line.product_qty, invoice_qty, precision_rounding=best_line.product_uom_id.rounding) != 0:
                    mismatched_lines.append(Command.create({
                        "po_line_id": best_line.id, "product_id": best_line.product_id.id, "po_qty": best_line.product_qty,
                        "invoice_qty": invoice_qty, "price_unit": float(item.get("price") or best_line.price_unit),
                        "discount": float(item.get("discount") or 0.0), "tax_rate": float(item.get("tax") or 0.0), "is_new_product": False,
                    }))
                else:
                    vals = {"price_unit": float(item.get("price") or best_line.price_unit), "discount": float(item.get("discount") or 0.0)}
                    tax = self._get_or_create_tax(float(item.get("tax") or 0.0))
                    vals["tax_ids"] = [Command.set(tax.ids)] if tax else [Command.clear()]
                    best_line.write(vals)
            else:
                mismatched_lines.append(Command.create({
                    "invoice_name": item.get("name"), "invoice_qty": invoice_qty, "price_unit": float(item.get("price") or 0.0),
                    "discount": float(item.get("discount") or 0.0), "tax_rate": float(item.get("tax") or 0.0), "is_new_product": True,
                }))

        if mismatched_lines:
            wizard = self.env["purchase.qty.wizard"].create({"purchase_id": self.id, "line_ids": mismatched_lines})
            return {
                "type": "ir.actions.act_window", "name": _("Quantity Mismatch Confirmation"),
                "res_model": "purchase.qty.wizard", "res_id": wizard.id, "view_mode": "form",
                "views": [(self.env.ref("vendor_bill_ocr_automation.view_purchase_qty_wizard_form").id, "form")], "target": "new",
            }
        return self._send_notification(_("Success"), _("Purchase Order updated successfully from Invoice."))

    def _find_best_po_line(self, invoice_name, used_po_lines):
        best_score, best_line = 0.0, False
        clean_invoice_name = self._clean_ocr_name(invoice_name).lower()

        for po_line in self.order_line:
            if po_line.id in used_po_lines:
                continue
            po_product_name = self._clean_ocr_name(po_line.product_id.display_name).lower()
            if clean_invoice_name == po_product_name:
                return po_line
            score = SequenceMatcher(None, clean_invoice_name, po_product_name).ratio()
            if score > best_score:
                best_score, best_line = score, po_line

        return best_line if best_score >= 0.95 else False

    def _check_bill_validation(self, ocr_result):
        self.ensure_one()
        used_po_lines, mismatch_lines = set(), []
        done_incoming_moves = self.picking_ids.filtered(lambda p: p.picking_type_id.code == "incoming" and p.state == "done").move_ids

        for item in ocr_result.get("lines", []):
            invoice_qty = float(item.get("qty") or 0.0)
            po_line = self._find_best_po_line(item.get("name"), used_po_lines)

            if not po_line:
                mismatch_lines.append(Command.create({
                    "product_id": False, "invoice_name": item.get("name"), "po_qty": 0.0, "receipt_qty": 0.0, "invoice_qty": invoice_qty,
                }))
                continue

            used_po_lines.add(po_line.id)
            receipt_qty = sum(done_incoming_moves.filtered(lambda m: m.purchase_line_id == po_line).mapped("quantity"))
            po_qty = po_line.product_qty

            po_mismatch = float_compare(po_qty, invoice_qty, precision_rounding=po_line.product_uom_id.rounding) != 0
            receipt_mismatch = float_compare(receipt_qty, invoice_qty, precision_rounding=po_line.product_uom_id.rounding) != 0

            if po_mismatch or receipt_mismatch:
                mismatch_lines.append(Command.create({
                    "po_line_id": po_line.id, "product_id": po_line.product_id.id, "po_qty": po_qty, "receipt_qty": receipt_qty, "invoice_qty": invoice_qty,
                    "new_po_qty": invoice_qty if po_mismatch else po_qty, "new_receipt_qty": invoice_qty if receipt_mismatch else receipt_qty,
                }))

        if not mismatch_lines:
            return False

        wizard = self.env["purchase.bill.validation.wizard"].create({"purchase_id": self.id, "line_ids": mismatch_lines})
        return {
            "type": "ir.actions.act_window", "name": _("Vendor Bill Validation"), "res_model": "purchase.bill.validation.wizard", "res_id": wizard.id,
            "view_mode": "form", "views": [(self.env.ref("vendor_bill_ocr_automation.view_purchase_bill_validation_wizard_form").id, "form")], "target": "new",
        }

    def _create_po_line_from_invoice(self, item):
        self.ensure_one()
        ocr_product_name = item.get("name") or "Default Product"
        product = self.env["product.product"].search([("name", "=ilike", ocr_product_name)], limit=1)
        if not product:
            product = self.env["product.template"].create({
                "name": ocr_product_name, "purchase_ok": True, "sale_ok": False, "type": "consu",
            }).product_variant_id

        tax = self._get_or_create_tax(float(item.get("tax") or 0.0))
        self.env["purchase.order.line"].create({
            "order_id": self.id, "product_id": product.id, "product_qty": float(item.get("qty") or 1.0),
            "price_unit": float(item.get("price") or 0.0), "discount": float(item.get("discount") or 0.0),
            "date_planned": fields.Datetime.now(), "product_uom_id": product.uom_id.id, "tax_ids": [Command.set(tax.ids)] if tax else [],
        })

    def _process_uploaded_invoice_base(self, attachment):
        self.ensure_one()
        ocr_result = ProductionOCRProcessor().parse_invoice(attachment)
        if not ocr_result or not ocr_result.get("lines"):
            raise UserError(_("Unable to read invoice or no products found."))

        for line in ocr_result.get("lines", []):
            line["name"] = self._clean_ocr_name(line.get("name"))

        self.write({"ocr_json": ocr_result, "over_receipt_json": []})
        return ocr_result

    def _update_po_qty_from_invoice(self, ocr_result):
        self.ensure_one()
        used_po_lines, mismatched_lines = set(), []

        for item in ocr_result.get("lines", []):
            invoice_qty = float(item.get("qty") or 0.0)
            if invoice_qty <= 0:
                continue

            best_line = self._find_best_po_line(item.get("name"), used_po_lines)
            if not best_line:
                mismatched_lines.append(Command.create({
                    "invoice_name": item.get("name"), "invoice_qty": invoice_qty, "price_unit": float(item.get("price") or 0.0),
                    "discount": float(item.get("discount") or 0.0), "tax_rate": float(item.get("tax") or 0.0), "is_new_product": True,
                }))
                continue

            used_po_lines.add(best_line.id)
            if float_compare(best_line.product_qty, invoice_qty, precision_rounding=best_line.product_uom_id.rounding) != 0:
                mismatched_lines.append(Command.create({
                    "po_line_id": best_line.id, "product_id": best_line.product_id.id, "po_qty": best_line.product_qty, "invoice_qty": invoice_qty,
                }))
            else:
                best_line.write({"product_qty": invoice_qty, "price_unit": float(item.get("price") or best_line.price_unit), "discount": float(item.get("discount") or 0.0)})

        if mismatched_lines:
            wizard = self.env["purchase.qty.wizard"].create({"purchase_id": self.id, "line_ids": mismatched_lines})
            return {
                "type": "ir.actions.act_window", "name": _("Quantity Mismatch Confirmation"), "res_model": "purchase.qty.wizard", "res_id": wizard.id,
                "view_mode": "form", "views": [(self.env.ref("vendor_bill_ocr_automation.view_purchase_qty_wizard_form").id, "form")], "target": "new",
            }
        return self._send_notification(_("Success"), _("Purchase Order updated successfully from Invoice."))

    def _update_receipt_qty_from_invoice(self, ocr_result, picking):
        self.ensure_one()
        if picking.state in ("confirmed", "waiting"):
            picking.action_assign()
        used_po_lines, mismatched_lines = set(), []

        for item in ocr_result.get("lines", []):
            invoice_qty = float(item.get("qty") or 0.0)
            if invoice_qty <= 0:
                continue
            best_line = self._find_best_po_line(item.get("name"), used_po_lines)
            if not best_line:
                mismatched_lines.append(Command.create({
                    "invoice_name": item.get("name"), "invoice_qty": invoice_qty, "price_unit": float(item.get("price") or 0.0),
                    "discount": float(item.get("discount") or 0.0), "tax_rate": float(item.get("tax") or 0.0), "is_new_product": True,
                }))
                continue
            used_po_lines.add(best_line.id)
            move = picking.move_ids.filtered(lambda m: m.purchase_line_id == best_line)[:1]
            if not move:
                continue
            if float_compare(move.quantity, invoice_qty, precision_rounding=move.product_uom.rounding) != 0:
                mismatched_lines.append(Command.create({
                    "po_line_id": best_line.id, "product_id": best_line.product_id.id, "po_qty": move.quantity, "invoice_qty": invoice_qty,
                }))
            else:
                move.write({"quantity": invoice_qty})

        if mismatched_lines:
            wizard = self.env["purchase.qty.wizard"].create({"purchase_id": self.id, "picking_id": picking.id, "is_receipt": True, "line_ids": mismatched_lines})
            return {
                "type": "ir.actions.act_window", "name": _("Quantity Mismatch Confirmation"), "res_model": "purchase.qty.wizard", "res_id": wizard.id,
                "view_mode": "form", "views": [(self.env.ref("vendor_bill_ocr_automation.view_purchase_qty_wizard_form").id, "form")], "target": "new",
                "context": {"default_picking_id": picking.id, "from_receipt": True},
            }
        return self._send_notification(_("Receipt Updated"), _("Incoming Receipt quantities updated successfully from Invoice."))

    def _create_vendor_bill_from_saved_ocr(self):
        self.ensure_one()
        if self.env["account.move"].search([("move_type", "=", "in_invoice"), ("partner_id", "=", self.partner_id.id), ("invoice_origin", "=", self.name), ("state", "!=", "cancel")], limit=1):
            raise UserError(_("Vendor Bill already exists for this Purchase Order."))

        ocr_result = self.ocr_json
        if not ocr_result or not ocr_result.get("lines"):
            raise UserError(_("OCR data or invoice lines not found."))

        invoice_vals = self._prepare_invoice()
        if ocr_result.get("invoice_date"): invoice_vals["invoice_date"] = ocr_result["invoice_date"]
        if ocr_result.get("invoice_number"): invoice_vals["ref"] = ocr_result["invoice_number"]

        invoice_line_commands = []
        used_po_lines = set()

        for item in ocr_result.get("lines", []):
            line_vals = self._prepare_ocr_invoice_line(item, used_po_lines, pdf_tax_rate=float(item.get("tax") or 0.0))
            if line_vals:
                invoice_line_commands.append(Command.create(line_vals))

        if not invoice_line_commands:
            raise UserError(_("No invoice lines found."))

        invoice_vals["invoice_line_ids"] = invoice_line_commands
        vendor_bill = self.env["account.move"].create(invoice_vals)
        vendor_bill.purchase_id = self.id

        lines_dict = {item.get("name"): float(item.get("price") or 0.0) for item in ocr_result.get("lines", [])}
        for line in vendor_bill.invoice_line_ids:
            if lines_dict.get(line.name) == 0.0:
                line.price_unit = 0.0

        return {"type": "ir.actions.act_window", "res_model": "account.move", "res_id": vendor_bill.id, "view_mode": "form", "views": [(False, "form")], "target": "current"}

    def _validate_invoice_against_po(self, ocr_result):
        matched, unmatched, used_po_lines = 0, [], set()
        for item in ocr_result.get("lines", []):
            best_line = self._find_best_po_line(item.get("name"), used_po_lines)
            if best_line:
                matched += 1
                used_po_lines.add(best_line.id)
            else:
                unmatched.append({"invoice_product": item.get("name")})
        total = len(ocr_result.get("lines", []))
        return {"matched": matched, "unmatched": unmatched, "percentage": (matched / total) * 100 if total else 0}

    def _prepare_ocr_invoice_line(self, item, used_po_lines, pdf_tax_rate=0.0):
        self.ensure_one()
        raw_product_name = item.get("name") or "Default Product"
        qty, price, discount = float(item.get("qty", 1.0)), float(item.get("price", 0.0)), float(item.get("discount") or 0.0)

        if match := re.search(r'\(\s*(\d+)\s*(?:pieces|pcs|pices|nos)?\s*x\s*[\$\s]*([\d\.]+)\s*\)', raw_product_name, re.IGNORECASE):
            bracket_string, val_qty, val_price = match.group(0), float(match.group(1)), float(match.group(2))
            if qty == 1.0 and price > 0 and abs((val_qty * val_price) - price) < 1:
                qty, price = val_qty, val_price
            product_name = raw_product_name.replace(bracket_string, "").strip() or f"Laundry Service {bracket_string}"
        else:
            product_name = raw_product_name

        product_name = product_name or "Laundry Service"
        po_line = self._find_best_po_line(product_name, used_po_lines)

        if po_line:
            used_po_lines.add(po_line.id)
            line_vals = po_line._prepare_account_move_line()
            line_vals.update({"quantity": qty, "price_unit": price, "discount": discount})
        else:
            product = self.env["product.product"].search([("name", "=ilike", product_name)], limit=1) or self.env["product.product"].create({"name": product_name, "purchase_ok": True, "sale_ok": False, "type": "consu"})
            account = product.product_tmpl_id._get_product_accounts()['expense'] or self.env["account.account"].search([("account_type", "=", "expense_direct")], limit=1)
            line_vals = {"product_id": product.id, "name": product_name, "quantity": qty, "price_unit": price, "discount": discount, "product_uom_id": product.uom_id.id, "account_id": account.id or False, "tax_ids": []}

        tax = self._get_or_create_tax(pdf_tax_rate)
        if tax:
            line_vals["tax_ids"] = [Command.set(tax.ids)]
        elif not po_line:
            line_vals["tax_ids"] = [Command.clear()]

        return line_vals

    def _send_notification(self, title, message, notif_type="success", sticky=False):
        return {"type": "ir.actions.client", "tag": "display_notification", "params": {"title": title, "message": message, "type": notif_type, "sticky": sticky}}