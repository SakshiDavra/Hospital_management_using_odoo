# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, _, Command

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    def action_upload_invoice(self, file_name=False, file_type=False, file_data=False, **kwargs):
        self.ensure_one()
        if not file_data:
            return False

        attachment = self.env["ir.attachment"].create({
            'name': file_name or 'Vendor_Invoice.pdf',
            'mimetype': file_type or 'application/pdf',
            'datas': file_data,
            'res_model': self._name,
            'res_id': self.id,
        })

        return self._process_uploaded_invoice(attachment)

    def _process_uploaded_invoice(self, attachment):
        from ..utils.ocr_engine import OCRProcessor
        
        ocr_processor = OCRProcessor(self.env)
        ocr_result = ocr_processor.parse_invoice(attachment)
        
        if not ocr_result or not ocr_result.get('lines'):
            _logger.warning("No line data found from PDF text processing.")
            return False

        invoice_vals = self._prepare_invoice()
        
        if ocr_result.get('invoice_date'):
            invoice_vals['invoice_date'] = ocr_result['invoice_date']
        if ocr_result.get('invoice_number'):
            invoice_vals['ref'] = ocr_result['invoice_number']

        invoice_line_commands = []
        for item in ocr_result['lines']:
            line_vals = self._prepare_ocr_invoice_line(item, pdf_tax_rate=18.0)
            if line_vals:
                invoice_line_commands.append(Command.create(line_vals))
                
        if not invoice_line_commands:
            return False

        invoice_vals['invoice_line_ids'] = invoice_line_commands

        vendor_bill = self.env['account.move'].create(invoice_vals)
        vendor_bill.write({'purchase_id': self.id})
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bill'),
            'res_model': 'account.move',
            'res_id': vendor_bill.id,
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'current',
        }

    def _prepare_ocr_invoice_line(self, item, pdf_tax_rate=18.0):
        self.ensure_one()
        product_name = item.get("name", "Default Product")
        
        product = self.env["product.product"].search([
            ("name", "=ilike", product_name)
        ], limit=1)
        
        if not product:
            product = self.env["product.product"].create({
                "name": product_name,
                "purchase_ok": True,
                "sale_ok": False,
                "type": "consu",
            })

        account = product.product_tmpl_id._get_product_accounts()['expense']
        if not account:
            account = self.env['account.account'].search([('account_type', '=', 'expense_direct')], limit=1)

        line_vals = {
            'product_id': product.id,
            'name': product_name,
            'quantity': float(item.get('qty', 1)),
            'price_unit': float(item.get('price', 0.0)),
            'product_uom_id': product.uom_id.id,
            'account_id': account.id if account else False,
            'tax_ids': [], 
        }
        
        matching_tax = self.env['account.tax'].search([
            ('amount', '=', pdf_tax_rate),
            ('type_tax_use', '=', 'purchase'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not matching_tax:
            _logger.info(f"Tax rate {pdf_tax_rate}% not found in Odoo. Creating new tax...")
            try:
                matching_tax = self.env['account.tax'].create({
                    'name': f'Purchase GST {int(pdf_tax_rate)}%',
                    'amount_type': 'percent',
                    'amount': pdf_tax_rate,
                    'type_tax_use': 'purchase',
                    'company_id': self.company_id.id,
                    'sequence': 10,
                })
            except Exception as e:
                _logger.error(f"Failed to create tax at runtime: {str(e)}")
        
        if matching_tax:
            line_vals['tax_ids'] = [Command.set(matching_tax.ids)]
        
        return line_vals