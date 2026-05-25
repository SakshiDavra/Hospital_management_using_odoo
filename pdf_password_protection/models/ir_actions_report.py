import io
import base64
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from odoo import models, fields


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'
   
    enable_pdf_password = fields.Boolean(string='Enable PDF Password')

    password_type = fields.Selection(
        [
            ('static', 'Static'),
            ('dynamic', 'Dynamic')
        ],
        string='Password Type'
    )

    static_password = fields.Char(string='Static Password')

    dynamic_field_path = fields.Char(string='Dynamic Password Field')

    # WATERMARK
    enable_watermark = fields.Boolean(string='Enable Watermark')

    watermark_type = fields.Selection([('text', 'Text'),('image', 'Image')],string='Watermark Type')

    font_name = fields.Selection([('Helvetica', 'Helvetica'),('Times-Roman', 'Times'),('Courier', 'Courier')], 
        default='Helvetica'
    )

    font_size = fields.Integer(default=60)

    font_color = fields.Char(default='#808080')

    watermark_layout = fields.Selection([('horizontal', 'Horizontal'),('diagonal', 'Diagonal')],default='diagonal')

    watermark_text = fields.Char(string='Watermark Text')

    watermark_opacity = fields.Float(string='Opacity', default=0.3)

    vertical_position = fields.Selection([('top', 'Top'),('middle', 'Middle'),('bottom', 'Bottom')],default='middle')
    
    horizontal_position = fields.Selection([('left', 'Left'),('center', 'Center'),('right', 'Right')],default='center')

    watermark_image = fields.Binary(string='Watermark Image')

    image_scale = fields.Integer(string='Image Scale (%)', default=100)
    
    def _get_watermark_position(self, page_width, page_height, report, image_width, image_height):
        padding_x = page_width * 0.05
        padding_y = page_height * 0.05

        # center
        x = page_width / 2
        y = page_height / 2

        # vertical
        if report.vertical_position == 'top':
            y = page_height - (image_height / 2 + padding_y)

        elif report.vertical_position == 'bottom':
            y = (image_height / 2 + padding_y)

        # horizontal
        if report.horizontal_position == 'left':
            x = (image_width / 2 + padding_x)

        elif report.horizontal_position == 'right':
            x = page_width - (image_width / 2 + padding_x)

        return x, y
        

    def _generate_image_watermark(self, report, page_width, page_height):
        buffer = io.BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        opacity = (report.watermark_opacity or 0.3)
        if opacity > 1:
            opacity /= 100

        opacity = max(0.0, min(opacity, 1.0))
        try:
            pdf_canvas.setFillAlpha(opacity)
        except Exception:
            pass

        image = ImageReader(io.BytesIO(base64.b64decode( report.watermark_image)))
        # original image size
        original_width, original_height = (image.getSize())
        # scale
        scale = (report.image_scale / 100)
        width = (original_width * scale)
        height = (original_height * scale )
        # position
        x, y = (self._get_watermark_position(
                page_width,
                page_height,
                report,
                width,
                height ))

        pdf_canvas.drawImage(
            image,
            x - width / 2,
            y - height / 2,
            width=width,
            height=height,
            mask='auto' )
        pdf_canvas.showPage()
        pdf_canvas.save()
        buffer.seek(0)
        return PdfReader(buffer)

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        pdf_content, content_type = (super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data))
        report = self._get_report(report_ref)

        # WATERMARK
        if (report.enable_watermark and report.watermark_image):
            reader = PdfReader(io.BytesIO(pdf_content))
            # actual page size
            first_page = reader.pages[0]
            page_width = float(first_page.mediabox.width)
            page_height = float(first_page.mediabox.height)
            watermark_pdf = (self._generate_image_watermark(report, page_width,  page_height))
            writer = PdfWriter()
            for page in reader.pages:
                page.merge_page(watermark_pdf.pages[0])
                writer.add_page(page)

            stream = io.BytesIO()
            writer.write(stream)
            pdf_content = stream.getvalue()

        # PASSWORD
        password = False
        if report.enable_pdf_password:
            if report.password_type == 'static':
                password = (report.static_password)
            elif (report.password_type == 'dynamic' and report.dynamic_field_path and res_ids):
                record = self.env[report.model].browse(res_ids[0])
                value = record.mapped(report.dynamic_field_path)
                if value:
                    value = value[0]
                    password = (value.display_name if hasattr(value,'display_name') else str(value))

        if password:
            writer = PdfWriter()
            writer.append(io.BytesIO(pdf_content))
            writer.encrypt(str(password))
            stream = io.BytesIO()
            writer.write(stream)
            pdf_content = stream.getvalue()

        return pdf_content, content_type