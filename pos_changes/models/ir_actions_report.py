# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        if report_ref == 'pos_changes.action_pos_order_receipt_backend' and res_ids:
            orders = self.env['pos.order'].browse(res_ids)
            
            # --- Dynamic Height Calculation ---
            # Base height 140mm (Header, QR, Footer) + 15mm per line
            base_height = 140 
            per_line_height = 15
            
            max_lines = 0
            for order in orders:
                if len(order.lines) > max_lines:
                    max_lines = len(order.lines)
            
            calculated_height = base_height + (max_lines * per_line_height)
            
            # Paper format ni height database ma update karo
            paper_format = self.env.ref('pos_changes.paperformat_pos_receipt', raise_if_not_found=False)
            if paper_format:
                paper_format.sudo().write({'page_height': calculated_height})

        return super(IrActionsReport, self)._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

    def _get_wkhtmltopdf_options(self, report_ref, res_ids=None, data=None):
        options = super(IrActionsReport, self)._get_wkhtmltopdf_options(report_ref, res_ids=res_ids, data=data)
        if report_ref == 'pos_changes.action_pos_order_receipt_backend':
            # Aa parameters split rokse
            options.append('--disable-smart-shrinking')
            options.append('--min-font-size')
            options.append('12')
        return options