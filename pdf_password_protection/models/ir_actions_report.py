import io
import base64
import math
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import getAscent, getDescent
from odoo import models, fields, _
from odoo.exceptions import UserError


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'
    
    enable_pdf_password = fields.Boolean(string='Enable PDF Password')
    password_type = fields.Selection([
        ('static', 'Static'),
        ('dynamic', 'Dynamic')
    ], string='Password Type', default='static')

    static_password = fields.Char(string='Static Password')
    dynamic_field_path = fields.Char(string='Dynamic Password Field')
    enable_watermark = fields.Boolean(string='Enable Watermark')
    watermark_type = fields.Selection([('text', 'Text'), ('image', 'Image')], string='Watermark Type')
    font_name = fields.Selection([
        ('Helvetica', 'Helvetica'),
        ('Times-Roman', 'Times'),
        ('Courier', 'Courier')
    ], default='Helvetica')
    
    watermark_size = fields.Selection([
        ('xs', 'Extra Small'),
        ('sm', 'Small'),
        ('md', 'Medium'),
        ('lg', 'Large'),
        ('xl', 'Extra Large'),
    ], string='Font Size', default='md')

    font_color = fields.Char(string='Font Color', default='#808080')
    watermark_layout = fields.Selection([('horizontal', 'Horizontal'), ('diagonal', 'Diagonal')], default='diagonal')
    watermark_text = fields.Char(string='Watermark Text')
    watermark_opacity = fields.Selection([
        ('0.1', '0.1'), ('0.3', '0.3'), ('0.5', '0.5'),
        ('0.7', '0.7'), ('0.9', '0.9'), ('1.0', '1.0'),
    ], string='Opacity', default='0.3')
    
    vertical_position = fields.Selection([('top', 'Top'), ('middle', 'Middle'), ('bottom', 'Bottom')], default='middle')
    horizontal_position = fields.Selection([('left', 'Left'), ('center', 'Center'), ('right', 'Right')], default='center')
    watermark_image = fields.Binary(string='Watermark Image')
    image_scale = fields.Integer(string='Image Scale (%)', default=100)
    
    def _get_dynamic_font_size(self, page_width, page_height):
        size_ratio = {'xs': 0.04, 'sm': 0.06, 'md': 0.08, 'lg': 0.10, 'xl': 0.12}
        ratio = size_ratio.get(self.watermark_size, 0.08)
        base_size = (page_width + page_height) / 2
        return base_size * ratio
    
    def _setup_font(self, pdf_canvas, page_width, page_height):
        font_name = self.font_name or 'Helvetica'
        font_size = self._get_dynamic_font_size(page_width, page_height)
        try:
            pdf_canvas.setFont(font_name, font_size)
        except Exception:
            font_name = 'Helvetica'
            pdf_canvas.setFont(font_name, font_size)
        return font_name, font_size
    
    def _get_watermark_position(self, page_width, page_height, watermark_width, watermark_height):
        PADDING_RATIO = 0.05
        padding_x = page_width * PADDING_RATIO
        padding_y = page_height * PADDING_RATIO

        # Horizontal position
        if self.horizontal_position == 'left':
            x = (padding_x + watermark_width / 2)
        elif self.horizontal_position == 'right':
            x = (page_width - padding_x - watermark_width / 2)
        else:
            x = page_width / 2

        # Vertical position
        if self.vertical_position == 'top':
            y = (page_height - padding_y - watermark_height / 2)
        elif self.vertical_position == 'bottom':
            y = (padding_y + watermark_height / 2)
        else:
            y = page_height / 2

        return x, y 
        
    def _create_canvas(self, page_width, page_height):
        buffer = io.BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=(page_width, page_height))
        return buffer, pdf_canvas

    def _apply_opacity(self, pdf_canvas):
        try:
            opacity = float(self.watermark_opacity or 0.3)
            pdf_canvas.setFillAlpha(opacity)
        except (AttributeError, ValueError):
            pass

    def _get_font_color(self):
        try:
            color = (self.font_color or '#808080').lstrip('#')
            # Handle short hex like FFF
            if len(color) == 3:
                color = ''.join([c*2 for c in color])
            if len(color) != 6:
                raise ValueError
            
            r = int(color[0:2], 16) / 255
            g = int(color[2:4], 16) / 255
            b = int(color[4:6], 16) / 255
            return r, g, b
        except (ValueError, TypeError):
            return 0.5, 0.5, 0.5

    def _finalize_pdf(self, pdf_canvas, buffer):
        pdf_canvas.showPage()
        pdf_canvas.save()
        buffer.seek(0)
        return PdfReader(buffer)
    
    def _generate_image_watermark(self, page_width, page_height):
        if not self.watermark_image:
            return None
        buffer, pdf_canvas = self._create_canvas(page_width, page_height)
        self._apply_opacity(pdf_canvas)
        
        image = ImageReader(io.BytesIO(base64.b64decode(self.watermark_image)))
        original_width, original_height = image.getSize()

        scale = max(self.image_scale, 1) / 100
        width = original_width * scale
        height = original_height * scale

        x, y = self._get_watermark_position(page_width, page_height, width, height)
        pdf_canvas.drawImage(image, x - width / 2, y - height / 2, width=width, height=height, mask='auto')
        return self._finalize_pdf(pdf_canvas, buffer)

    def _get_text_dimensions(self, text, font_name, font_size, layout, pdf_canvas):
        text_width = pdf_canvas.stringWidth(text, font_name, font_size)
        text_height = font_size

        if layout == 'diagonal':
            angle = math.radians(45)
            watermark_width = (abs(text_width * math.cos(angle)) + abs(text_height * math.sin(angle)))
            watermark_height = (abs(text_width * math.sin(angle)) + abs(text_height * math.cos(angle)))
        else:
            watermark_width = text_width
            watermark_height = text_height

        return text_width, watermark_width, watermark_height
    
    def _draw_diagonal_text(self, pdf_canvas, x, y, text, text_width, font_name, font_size):
        pdf_canvas.translate(x, y)
        pdf_canvas.rotate(45)

        ascent = (getAscent(font_name) * font_size / 1000)
        descent = (getDescent(font_name) * font_size / 1000)

        visual_center_adjustment = 0.7
        text_offset = ((ascent - descent) / 2) * visual_center_adjustment
        pdf_canvas.drawString(-(text_width / 2), -text_offset, text)

    def _generate_text_watermark(self, page_width, page_height):
        if not self.watermark_text:
            return None
        buffer, pdf_canvas = self._create_canvas(page_width, page_height)

        self._apply_opacity(pdf_canvas)
        font_name, font_size = self._setup_font(pdf_canvas, page_width, page_height)

        layout = self.watermark_layout
        text = self.watermark_text or ''

        r, g, b = self._get_font_color()
        pdf_canvas.setFillColorRGB(r, g, b)

        text_width, watermark_width, watermark_height = self._get_text_dimensions(
            text, font_name, font_size, layout, pdf_canvas
        )
        x, y = self._get_watermark_position(page_width, page_height, watermark_width, watermark_height)

        pdf_canvas.saveState()
        if layout == 'diagonal':
            self._draw_diagonal_text(pdf_canvas, x, y, text, text_width, font_name, font_size)
        else:
            pdf_canvas.drawCentredString(x, y, text)

        return self._finalize_pdf(pdf_canvas, buffer)

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        pdf_content, content_type = super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
        report = self._get_report(report_ref)

        if not report.enable_watermark and not report.enable_pdf_password:
            return pdf_content, content_type

        reader = PdfReader(io.BytesIO(pdf_content))
        writer = PdfWriter()

        watermark_pdf = None
        if report.enable_watermark and reader.pages:
            first_page = reader.pages[0]
            page_width = float(first_page.mediabox.width)
            page_height = float(first_page.mediabox.height)
            
            if report.watermark_type == 'image':
                watermark_pdf = report._generate_image_watermark(page_width, page_height)
            elif report.watermark_type == 'text':
                watermark_pdf = report._generate_text_watermark(page_width, page_height)

        for page in reader.pages:
            if watermark_pdf and watermark_pdf.pages:
                page.merge_page(watermark_pdf.pages[0])
            writer.add_page(page)

        if report.enable_pdf_password:
            password = False
            if report.password_type == 'static':
                password = report.static_password
            elif report.password_type == 'dynamic' and report.dynamic_field_path and res_ids:

                try:
                    record = self.env[report.model].browse(res_ids[0])
                    value = record.mapped(report.dynamic_field_path)
                    if value:
                        value = value[0]
                        password = value.display_name if hasattr(value, 'display_name') else str(value)
                except Exception:
                    password = False

            if password:
                writer.encrypt(str(password))

        stream = io.BytesIO()
        writer.write(stream)
        return stream.getvalue(), content_type