# -*- coding: utf-8 -*-
import re
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    import pytesseract
except ImportError:
    cv2 = None
    np = None
    pytesseract = None

try:
    import fitz
except ImportError:
    fitz = None

class ProductionOCRProcessor:
    def __init__(self, env=None):
        self.env = env
        self.INV_PATTERNS = [
            r'(?:inv(?:oice)?|bill|tax\s+invoice|ref|doc(?:ument)?|voucher|cash\s+memo)\s*(?:no|num|number|#)?[:.\s\-#]+([A-Za-z0-9\-/\s]+)',
            r'\b\d{4}/\d{2}-\d{2}\b',
        ]
        self.HEADER_SYNONYMS = {
            'name': ['description', 'particulars', 'item', 'product', 'details', 'service'],
            'hsn': ['hsn', 'sac', 'hsn/sac', 'code'],
            'qty': ['qty', 'quantity', 'qtv', 'oty', 'qiy', 'nos', 'pcs', 'box', 'kg', 'ltr', 'volume'],
            'price': ['rate', 'price', 'unit price', 'list price', 'cost'],
            'tax': ['tax', 'gst', 'cgst', 'sgst', 'igst', 'vat', '%', 'tax %', 'gst %', 'tax rate'],
            'discount': ['disc', 'disc.', 'discount', 'discount%', 'discount %', 'dis%', 'less'],
            'amount': ['amount', 'value', 'net amount', 'total', 'final amount', 'taxable value']
        }
        self.FOOTER_KEYWORDS = ['total', 'subtotal', 'sub total', 'balances', 'grand total', 'amount in words', 'payable', 'balance due', 'round off']

    def parse_invoice(self, attachment):
        if not attachment or not attachment.raw:
            return False

        name = (attachment.name or "").lower()

        if "pdf" in (attachment.mimetype or "") or name.endswith(".pdf"):
            return self._parse_pdf_engine(attachment.raw)

        elif name.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
            return self._parse_image_engine(attachment.raw)

        return False

    def _parse_pdf_engine(self, pdf_bytes):
        result = {'invoice_number': False, 'invoice_date': False, 'lines': []}
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            full_text = "\n".join([page.get_text("text") for page in doc])
            if len(full_text.strip()) < 30:
                doc.close()
                return self._parse_scanned_pdf(pdf_bytes)
            all_pages_words = [page.get_text("words") for page in doc]

            result['invoice_number'] = self._extract_invoice_number(full_text)
            result['invoice_date'] = self._extract_invoice_date(full_text)
            invoice_tax = self._extract_invoice_tax(full_text)
            result['lines'] = self._extract_table_lines(all_pages_words)

            for line in result['lines']:
                if not line.get("tax"):
                    line["tax"] = invoice_tax
            doc.close()
        except Exception:
            return False
        return result

    def _extract_invoice_number(self, text):

        patterns = [
            r'Invoice\s*(?:No|Number)?\s*[:\-]?\s*([A-Z0-9\/\-]+)',
            r'Bill\s*(?:No|Number)?\s*[:\-]?\s*([A-Z0-9\/\-]+)',
            r'Inv(?:oice)?\s*#?\s*([A-Z0-9\/\-]+)',
        ]

        for p in patterns:
            m = re.search(p, text, re.I)
            if m:
                return m.group(1)

        return False

    def _extract_invoice_date(self, text):
        date_patterns = [
            (r'\b\d{1,2}[-/\.\s][A-Za-z]{3,9}[-/\.\s]\d{2,4}\b', ["%d-%b-%y", "%d-%b-%Y", "%d/%b/%Y", "%d %b %Y", "%d %B %Y"]),
            (r'\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}\b', ["%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y", "%Y-%m-%d", "%d.%m.%Y"]),
            (r'\b[A-Za-z]{3,9}\s+\d{1,2}\s*,\s*\d{4}\b', ["%B %d %Y", "%b %d %Y"]),
            (r'\b\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}\b', ["%Y-%m-%d", "%Y/%m/%d"])
        ]
        text = re.sub(r'\s+', ' ', text)
        for pattern, formats in date_patterns:
            for match in re.findall(pattern, text, re.IGNORECASE):
                raw = match.replace(',', '').replace('.', '-').replace('/', '-').strip()
                for fmt in formats:
                    try: return datetime.strptime(raw, fmt).strftime('%Y-%m-%d')
                    except ValueError: continue
        return False

    def _group_words_by_lines(self, words):
        if not words: return []
        avg_height = sum(w[3] - w[1] for w in words) / len(words)
        y_buffer = max(avg_height * 0.8, 8)
        lines = {}
        for w in words:
            y_center = (w[1] + w[3]) / 2.0
            found = False
            for y in lines.keys():
                if abs(y_center - y) <= y_buffer:
                    lines[y].append(w); found = True; break
            if not found: lines[y_center] = [w]
        
        return [sorted(line, key=lambda w: w[0]) for y, line in sorted(lines.items())]

    def _clean_number(self, val):
        try:
            text = str(val).strip()

            text = text.replace("$", "")
            text = text.replace("%", "")
            text = text.replace("]", "")
            text = text.replace("|", "")

            # OCR decimal comma (3,00 -> 3.00)
            if re.match(r"^\d+,\d{2}$", text):
                text = text.replace(",", ".")

            # Thousand separator (6,030.00)
            elif re.match(r"^\d{1,3}(,\d{3})+(\.\d+)?$", text):
                text = text.replace(",", "")

            # Remove remaining junk
            text = re.sub(r"[^0-9.\-]", "", text)

            return float(text) if text else 0.0

        except Exception:
            return 0.0
    
    def _extract_tax_value(self, text):
        if not text: return 0.0
        m = re.search(r'(\d+(?:\.\d+)?)\s*%', text) or re.search(r'(?:GST|CGST|SGST|IGST)\s*(\d+(?:\.\d+)?)', text, re.I)
        if m: return float(m.group(1))
        val = self._clean_number(text)
        return val if val <= 50 else 0.0

    def _extract_table_lines(self, all_pages_words):
        lines_data, table_started, col_mapping, pending_line = [], False, {}, None
        for words in all_pages_words:
            for line_words in self._group_words_by_lines(words):
                tokens = [w[4].strip() for w in line_words if w[4].strip()]
                combined = " ".join(tokens).lower()
                
                if table_started and any(k in combined for k in self.FOOTER_KEYWORDS):
                    table_started = False; break
                
                if not table_started:
                    if any(k in combined for k in self.HEADER_SYNONYMS['name']) and \
                       any(k in combined for k in self.HEADER_SYNONYMS['amount'] + self.HEADER_SYNONYMS['price']):
                        table_started = True
                        col_mapping = {key: [] for key in self.HEADER_SYNONYMS}
                        for w in line_words:
                            text = w[4].lower()
                            for k, syn in self.HEADER_SYNONYMS.items():
                                if any(s in text for s in syn): col_mapping[k].append((w[0], w[2]))
                        continue
                
                if table_started and len(tokens) >= 2:
                    row = {k: [] for k in col_mapping}
                    for w in line_words:
                        x = (w[0] + w[2]) / 2.0
                        for k, ranges in col_mapping.items():
                            if any(s - 20 <= x <= e + 20 for s, e in ranges):
                                row[k].append(w[4].strip()); break
                    
                    p_name = " ".join(row['name'])
                    qty = self._clean_number("".join(row['qty']))
                    price = self._clean_number("".join(row['price']))
                    disc = self._clean_number("".join(row['discount']))
                    tax = self._extract_tax_value("".join(row['tax']))
                    amt = self._clean_number("".join(row['amount']))

                    if p_name and not (qty or price or amt):
                        if pending_line: pending_line["name"] += " " + p_name
                        continue
                    
                    if pending_line: lines_data.append(pending_line); pending_line = None
                    if p_name:
                        if amt > 0 and qty == 0 and price == 0: qty, price = 1, amt
                        elif qty > 0 and amt > 0 and price == 0: price = amt / qty
                        pending_line = {"name": p_name, "qty": qty or 1, "price": price, "discount": disc, "tax": tax}
            
            if pending_line: lines_data.append(pending_line); pending_line = None
        return lines_data or self._generic_fallback(all_pages_words)

    def _extract_invoice_tax(self, text):
        text = text.upper()

        # GST (18%), GST 18%, GST@18, IGST (18%)
        match = re.search(
            r'(?:GST|IGST)\s*(?:\(|@)?\s*(\d+(?:\.\d+)?)',
            text
        )
        if match:
            return float(match.group(1))

        cgst = re.search(
            r'CGST\s*(?:\(|@)?\s*(\d+(?:\.\d+)?)',
            text
        )

        sgst = re.search(
            r'SGST\s*(?:\(|@)?\s*(\d+(?:\.\d+)?)',
            text
        )

        if cgst and sgst:
            return float(cgst.group(1)) + float(sgst.group(1))

        return 0.0

    def _generic_fallback(self, all_pages):
        res = []
        for words in all_pages:
            for line in self._group_words_by_lines(words):
                tokens = [w[4].strip() for w in line if w[4].strip()]
                amt = self._clean_number(tokens[-1])
                if len(tokens) >= 2 and amt > 0 and not any(k in " ".join(tokens).lower() for k in self.FOOTER_KEYWORDS):
                    res.append({"name": " ".join(tokens[:-1]), "qty": 1.0, "price": amt})
        return res
    

    #==========================================================img==================================================================
    

    def _parse_scanned_pdf(self, pdf_bytes):
        images = self._pdf_to_images(pdf_bytes)
        if not images: return False
        
        all_pages_words = [self._ocr_image_words(img) for img in images]
        full_text = "\n".join(w[4] for page in all_pages_words for w in page)
        
        result = {
            "invoice_number": self._extract_invoice_number(full_text),
            "invoice_date": self._extract_invoice_date(full_text),
            "lines": self._extract_ocr_table_lines(all_pages_words)
        }
        
        tax = self._extract_invoice_tax(full_text)
        for line in result["lines"]:
            if not line.get("tax"): line["tax"] = tax
        return result

    def _pdf_to_images(self, pdf_bytes):
        if not all([fitz, np, cv2]): return []
        images = []
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if pix.n in [3, 4]: img = cv2.cvtColor(img, cv2.COLOR_BGR2BGR if pix.n == 3 else cv2.COLOR_RGBA2BGR)
                images.append(img)
            doc.close()
        except: return []
        return images

    def _ocr_image_words(self, image):
        if image is None or not pytesseract: return []
        gray = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        thresh = cv2.adaptiveThreshold(cv2.GaussianBlur(gray, (3,3), 0), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
        data = pytesseract.image_to_data(thresh, lang="eng", config="--oem 3 --psm 6", output_type=pytesseract.Output.DICT)
        
        words = []
        for i in range(len(data["text"])):
            txt = data["text"][i].strip()
            if txt and float(data["conf"][i]) >= 35:
                words.append((data["left"][i], data["top"][i], data["left"][i]+data["width"][i], data["top"][i]+data["height"][i], txt))
        return words

    def _parse_image_engine(self, image_bytes):
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if image is None: return False
        words = self._ocr_image_words(image)
        if not words: return False
        
        full_text = "\n".join(w[4] for w in words)
        tax = self._extract_invoice_tax(full_text)
        result = {"invoice_number": self._extract_invoice_number(full_text), "invoice_date": self._extract_invoice_date(full_text), "lines": self._extract_ocr_table_lines([words])}
        for line in result["lines"]:
            if not line.get("tax"): line["tax"] = tax
        return result

    def _extract_ocr_table_lines(self, all_pages_words):
        lines_data = []
        for words in all_pages_words:
            grouped = self._group_words_by_lines(words)
            qty_x = price_x = amount_x = None
            table_started = False
            
            for line_words in grouped:
                line_text = " ".join([w[4].strip() for w in line_words if w[4].strip()])
                lower = line_text.lower()
                
                if not table_started:
                    if any(k in lower for k in ("product", "item")) and any(k in lower for k in ("qty", "quantity", "unit")):
                        table_started = True
                        for w in line_words:
                            txt, x = w[4].lower(), (w[0] + w[2]) / 2
                            if txt in ("qty", "cty", "oty", "quantity"): qty_x = x
                            elif "price" in txt: price_x = x
                            elif "amount" in txt: amount_x = x
                    continue
                
                if any(k in lower for k in self.FOOTER_KEYWORDS + ["gst", "cgst", "sgst", "igst"]): break
                
                product, qty_v, price_v, amt_v = [], [], [], []
                for w in line_words:
                    val, x = self._clean_number(w[4].strip()), (w[0] + w[2]) / 2
                    if qty_x and x < qty_x - 20: product.append(w[4].strip())
                    elif qty_x and price_x and qty_x-20 <= x < price_x-20 and val > 0: qty_v.append(val)
                    elif price_x and amount_x and price_x-20 <= x < amount_x-20 and val > 0: price_v.append(val)
                    elif amount_x and x >= amount_x - 20 and val > 0: amt_v.append(val)
                
                qty = max(qty_v) if qty_v else 1.0
                price = max(price_v) if price_v else 0.0
                amount = max(amt_v) if amt_v else 0.0
                
                if qty == 1 and len(price_v) >= 2: price, amount = min(price_v), max(price_v); qty = round(amount/price, 2)
                elif qty == 1 and price > 0 and amount > 0: qty = round(amount/price, 2)
                if amount > 0 and qty > 0 and abs(round(amount/qty, 2) - price) > 1: price = round(amount/qty, 2)
                
                if product:
                    lines_data.append({"name": " ".join(product), "qty": round(qty, 2), "price": round(price, 2), "discount": 0.0, "tax": 0.0})
        return lines_data