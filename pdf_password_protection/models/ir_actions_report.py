import io
from pypdf import PdfReader, PdfWriter
from odoo import models, fields

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    enable_pdf_password = fields.Boolean(string='Enable PDF Password')
    password_type = fields.Selection([('static', 'Static'), ('dynamic', 'Dynamic')], string='Password Type')
    static_password = fields.Char(string='Static Password')
    dynamic_field_id = fields.Many2one(
        'ir.model.fields', 
        string='Dynamic Password Field',
        domain="[('model', '=', model), ('ttype', 'in', ['char', 'integer', 'float', 'date','many2one'])]"
    )

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        pdf_content, content_type = super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
        report = self._get_report(report_ref)

        if not report.enable_pdf_password:
            return pdf_content, content_type

        password = False
        if report.password_type == 'static':
            password = report.static_password
        elif report.password_type == 'dynamic' and res_ids and report.dynamic_field_id:
            record = self.env[report.model].browse(res_ids[0])
            value = record[report.dynamic_field_id.name]
            password = str(value.display_name if report.dynamic_field_id.ttype == 'many2one' else value) if value else False

        if not password:
            return pdf_content, content_type

        writer = PdfWriter()
        writer.append(io.BytesIO(pdf_content))  
        writer.encrypt(password)

        output_stream = io.BytesIO()
        writer.write(output_stream)
        return output_stream.getvalue(), content_type