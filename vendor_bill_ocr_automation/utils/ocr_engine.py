# -*- coding: utf-8 -*-
import logging
import re
from datetime import datetime

_logger = logging.getLogger(__name__)

try:
    import fitz
except ImportError:
    fitz = None

try:
    import cv2
    import numpy as np
    import pytesseract
except ImportError:
    cv2 = np = pytesseract = None


class OCRProcessor:
    def __init__(self, env=None):
        self.env = env

    def parse_invoice(self, attachment):
        if not attachment or not attachment.raw:
            return False

        file_bytes = attachment.raw
        mimetype = attachment.mimetype or ''
        filename = attachment.name or ''

        if 'pdf' in mimetype or filename.lower().endswith('.pdf'):
            if not fitz:
                _logger.error("PyMuPDF (fitz) is missing in production environment.")
                return False
            pdf_text = self._extract_text_with_fitz(file_bytes)
            return self._parse_pdf_text(pdf_text) if pdf_text.strip() else False

        elif mimetype.startswith("image/") or filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tif', '.tiff')):
            if not all([cv2, np, pytesseract]):
                _logger.error("OCR dependencies (cv2, numpy, pytesseract) are missing.")
                return False
            image_text = self._extract_text_with_tesseract(file_bytes)
            return self._parse_image_text(image_text) if image_text.strip() else False

        return False

    def _extract_text_with_fitz(self, pdf_bytes):
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                return "\n".join([page.get_text("text") for page in doc if page.get_text("text")])
        except Exception as e:
            _logger.error("PyMuPDF failed: %s", e)
            return ""

    def _extract_text_with_tesseract(self, image_bytes):
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return ""
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            return pytesseract.image_to_string(gray, lang="eng", config="--oem 3 --psm 6")
        except Exception as e:
            _logger.error("Tesseract failed: %s", e)
            return ""

    def _find_header_mapping(self, text):
        header_keywords = {
            "product": ["product", "item", "description", "particulars", "name"],
            "qty": ["qty", "quantity", "q'ty", "nos", "qty/unit"],
            "price": ["price", "unit price", "rate", "u.price", "cost"],
            "amount": ["amount", "total", "value", "net amt"]
        }
        lines = [l.strip().lower() for l in text.split('\n') if l.strip()]
        for line in lines:
            has_prod = any(k in line for k in header_keywords["product"])
            has_qty = any(k in line for k in header_keywords["qty"])
            has_price = any(k in line for k in header_keywords["price"])
            
            if has_prod and (has_qty or has_price):
                tokens = re.split(r'\s{2,}', line)
                if len(tokens) < 2:
                    tokens = line.split()
                    
                mapping = {}
                for idx, token in enumerate(tokens):
                    token = token.strip()
                    for key, keywords in header_keywords.items():
                        if any(k == token or k in token for k in keywords):
                            if key not in mapping:
                                mapping[key] = idx
                
                if "product" in mapping and ("qty" in mapping or "price" in mapping):
                    return mapping
        return None

    def _parse_table_with_mapping(self, text, mapping):
        lines = []
        raw_lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in raw_lines:
            if any(k in line.lower() for k in ['subtotal', 'total', 'gst', 'tax', 'payment', 'untaxed', 'invoice', 'date']):
                continue
                
            tokens = re.split(r'\s{2,}', line)
            if len(tokens) < 2:
                tokens = line.split()
                
            if len(tokens) < len(mapping):
                continue
                
            try:
                prod_name = tokens[mapping["product"]].strip('(:. ')
                if len(prod_name) < 2 or any(k == prod_name.lower() for k in ['product', 'qty', 'quantity', 'price', 'amount']):
                    continue
                
                raw_qty = re.sub(r'[^\d.]', '', tokens[mapping["qty"]]) if "qty" in mapping else "1"
                raw_price = re.sub(r'[^\d.]', '', tokens[mapping["price"]]) if "price" in mapping else "0"
                raw_amount = re.sub(r'[^\d.]', '', tokens[mapping["amount"]]) if "amount" in mapping else "0"
                
                qty_val = int(float(raw_qty)) if raw_qty else 1
                price_val = float(raw_price) if raw_price else 0.0
                amount_val = float(raw_amount) if raw_amount else 0.0
                
                if qty_val > 0 and price_val > 0:
                    lines.append({"name": prod_name, "qty": qty_val, "price": price_val})
            except (ValueError, IndexError):
                continue
        return lines

    def _parse_pdf_text(self, text):
        result = {'invoice_number': False, 'invoice_date': False, 'lines': []}
        inv_match = re.search(r'(?i)inv(?:oice)?\s*no(?:umber)?[:.\s\-]+([A-Z0-9\-–\/]+)', text)
        if inv_match:
            result['invoice_number'] = inv_match.group(1).strip()

        date_match = re.search(r'(?i)date[:.\s\-]+(\d{1,2}[-/\.\s][A-Za-z0-9]{3,9}[-/\.\s]\d{4}|\d{4}[-/\.\s]\d{1,2}[-/\.\s]\d{1,2})', text)
        if date_match:
            raw_date = date_match.group(1).strip()
            for fmt in ("%d-%b-%Y", "%d/%b/%Y", "%d %b %Y", "%d/%m/%Y", "%Y-%m-%d"):
                try:
                    result['invoice_date'] = datetime.strptime(raw_date, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue

        mapping = self._find_header_mapping(text)
        if mapping:
            result['lines'] = self._parse_table_with_mapping(text, mapping)

        if not result['lines']:
            raw_lines = [line.strip() for line in text.split('\n') if line.strip()]
            for idx, line in enumerate(raw_lines):
                if any(k in line.lower() for k in ['total', 'subtotal', 'gst']) or not re.match(r'^\d+$', line):
                    continue
                
                qty_val = int(line)
                if 0 < idx < len(raw_lines) - 1:
                    prod_name = raw_lines[idx - 1]
                    price_line = raw_lines[idx + 1]
                    if any(k == prod_name.lower() for k in ['product', 'qty', 'quantity', 'price', 'amount']) or len(prod_name) < 2:
                        continue
                    try:
                        price_unit = float(re.sub(r'[^\d.]', '', price_line))
                        if qty_val > 0 and price_unit > 0:
                            result['lines'].append({"name": prod_name, "qty": qty_val, "price": price_unit})
                    except ValueError:
                        pass
        return result

    def _parse_image_text(self, text):
        result = {'invoice_number': False, 'invoice_date': False, 'lines': []}
        inv_match = re.search(r'(?i)(?:invoice\s*no|inv\s*no|bill\s*no|invoice\s*#|woes\s*mo)[:.\s\-]+([A-Z0-9\-–\/]+)|\b(INV[-_]\d{4}[-_]\d+)\b', text)
        if inv_match:
            result['invoice_number'] = (inv_match.group(1) or inv_match.group(2)).strip()

        date_match = re.search(r'(?i)date[:.\s\-]+([\w\-. /]+)', text)
        if date_match:
            raw_date = re.sub(r'[^\w\-/]', '', date_match.group(1).strip().split('\n')[0])
            for fmt in ("%d-%b-%Y", "%d/%b/%Y", "%d%b%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y"):
                try:
                    result['invoice_date'] = datetime.strptime(raw_date, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue

        mapping = self._find_header_mapping(text)
        if mapping:
            result['lines'] = self._parse_table_with_mapping(text, mapping)

        if not result['lines']:
            for line in [l.strip() for l in text.split('\n') if l.strip()]:
                if any(k in line.lower() for k in ['subtotal', 'total', 'gst', 'tax', 'payment', 'untaxed']):
                    continue

                inline_match = re.search(r'^(.*?)\s+([\d.]+)\s+[\‘\']?([\d.]+)\s+\$?\s*([\d.,]+)$', line)
                if inline_match:
                    prod_name = inline_match.group(1).strip('(:. ')
                    raw_qty = float(inline_match.group(2))
                    raw_price = float(inline_match.group(3))
                    raw_total = float(inline_match.group(4).replace(',', ''))

                    qty_val = round(raw_total / raw_price) if abs((raw_qty * raw_price) - raw_total) > 1.0 else int(raw_qty)
                    if qty_val > 0 and raw_price > 0 and len(prod_name) > 2:
                        result['lines'].append({"name": prod_name, "qty": qty_val, "price": raw_price})

        return result