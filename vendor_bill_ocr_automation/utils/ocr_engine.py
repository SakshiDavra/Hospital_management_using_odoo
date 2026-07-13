# -*- coding: utf-8 -*-
import logging
import re
from datetime import datetime
from difflib import SequenceMatcher

_logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = np = None

try:
    import fitz
except ImportError:
    fitz = None

RapidOCR = None
for pkg in ['rapidocr_onnxruntime', 'rapidocr', 'rapidocr_openvino', 'rapidocr_paddle']:
    try:
        RapidOCR = __import__(pkg, fromlist=['RapidOCR']).RapidOCR
        break
    except ImportError:
        continue


class ProductionOCRProcessor:
    HEADER_MAP = {
        "sr": ["#", "sr", "sr.", "sr no", "sr no.", "srno", "serial", "serial no", "s.no", "sl", "sl no"],
        "name": ["product", "item", "description", "particular", "particulars", "details", "service", "material", "article"],
        "hsn": ["hsn", "sac", "hsn/sac", "code", "item code"],
        "qty": ["qty", "quantity", "qnty", "ordered qty", "qtv", "oty", "nos", "pcs", "box", "kg", "ltr", "volume"],
        "unit": ["unit", "uom", "pcs", "pc", "nos", "box", "kg", "ltr"],
        "price": ["price", "rate", "unit price", "list price", "unit rate", "basic rate", "mrp", "cost", "unit cost"],
        "discount": ["disc", "discount", "less", "disc.", "discount%", "dis%"],
        "tax": ["tax", "gst", "igst", "cgst", "sgst", "vat", "tax %", "gst %", "tax rate"],
        "amount": ["amount", "value", "total", "net amount", "line amount", "taxable value", "gross", "line total", "final amount"]
    }

    FOOTER_KEYWORDS = ["total", "grand total", "round off", "sub total", "subtotal", "cgst", "sgst", "igst", "tax summary", "amount in words", "bank", "terms", "signature", "authorised", "untaxed", "tax amount", "balance", "payment", "remarks", "payable", "balance due"]

    def __init__(self, env=None):
        self.env = env
        self._rapid_engine = None

    def _get_ocr_engine(self):
        if self._rapid_engine or not RapidOCR:
            return self._rapid_engine
        try:
            self._rapid_engine = RapidOCR()
        except Exception:
            self._rapid_engine = None
        return self._rapid_engine

    def parse_invoice(self, attachment):
        if not attachment or not attachment.raw:
            return False
        name = (attachment.name or "").lower()
        mimetype = attachment.mimetype or ""
        if "pdf" in mimetype or name.endswith(".pdf"):
            return self._parse_pdf_engine(attachment.raw)
        elif name.endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
            return self._parse_image_engine(attachment.raw)
        return False

    def _parse_pdf_engine(self, pdf_bytes):
        if not fitz:
            return False
        result = {'invoice_number': False, 'invoice_date': False, 'lines': []}
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                full_text = "\n".join([page.get_text("text") for page in doc])
                if len(full_text.strip()) < 30:
                    return self._parse_scanned_pdf(pdf_bytes)
                all_pages_words = [page.get_text("words") for page in doc]

            result['invoice_number'] = self._extract_invoice_number(full_text)
            result['invoice_date'] = self._extract_invoice_date(full_text)
            invoice_tax = self._extract_invoice_tax(full_text)
            result['lines'] = self._extract_table_lines(all_pages_words)

            for line in result['lines']:
                if not line.get("tax"):
                    line["tax"] = invoice_tax
        except Exception:
            return False
        return result

    def _parse_scanned_pdf(self, pdf_bytes):
        images = self._pdf_to_images(pdf_bytes)
        if not images:
            return False
        all_pages_words = [self._ocr_image_words(img) for img in images]
        full_text = "\n".join(w[4] for page in all_pages_words for w in page)
        result = {
            "invoice_number": self._extract_invoice_number(full_text),
            "invoice_date": self._extract_invoice_date(full_text),
            "lines": self._extract_ocr_table_lines(all_pages_words)
        }
        tax = self._extract_invoice_tax(full_text)
        for line in result["lines"]:
            if not line.get("tax"):
                line["tax"] = tax
        return result

    def _parse_image_engine(self, image_bytes):
        if cv2 is None or np is None or not self._get_ocr_engine():
            return False
        image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            return False
        words = self._ocr_image_words(image)
        if not words:
            return False
        full_text = "\n".join(w[4] for w in words)
        result = {
            "invoice_number": self._extract_invoice_number(full_text),
            "invoice_date": self._extract_invoice_date(full_text),
            "lines": self._extract_ocr_table_lines([words])
        }
        tax = self._extract_invoice_tax(full_text)
        for line in result["lines"]:
            if not line.get("tax"):
                line["tax"] = tax
        return result

    def _extract_invoice_number(self, text):
        patterns = [
            r'(?:inv(?:oice)?|bill|tax\s+invoice|ref|doc(?:ument)?|voucher|cash\s+memo)\s*(?:no|num|number|#)?[:.\s\-#]+([A-Za-z0-9\-/\s]+)',
            r'\b\d{4}/\d{2}-\d{2}\b'
        ]
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                value = m.group(1).strip() if m.groups() else m.group(0).strip()
                if value.lower() not in ("invoice", "number", "no", "bill", "inv", ""):
                    return value
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
                    try:
                        return datetime.strptime(raw, fmt).strftime('%Y-%m-%d')
                    except ValueError:
                        continue
        return False

    def _group_words_by_lines(self, words):
        if not words:
            return []
        avg_height = sum(w[3] - w[1] for w in words) / len(words)
        y_buffer = max(avg_height * 0.8, 8)
        lines = {}
        for w in words:
            y_center = (w[1] + w[3]) / 2.0
            found = False
            for y in lines.keys():
                if abs(y_center - y) <= y_buffer:
                    lines[y].append(w)
                    found = True
                    break
            if not found:
                lines[y_center] = [w]
        return [sorted(line, key=lambda w: w[0]) for y, line in sorted(lines.items())]

    def _clean_number(self, val):
        try:
            text = re.sub(r"[$\|\]%]", "", str(val).strip())
            if re.match(r"^\d+,\d{2}$", text):
                text = text.replace(",", ".")
            elif re.match(r"^\d{1,3}(,\d{3})+(\.\d+)?$", text):
                text = text.replace(",", "")
            text = re.sub(r"[^0-9.\-]", "", text)
            return float(text) if text else 0.0
        except Exception:
            return 0.0

    def _extract_tax_value(self, text):
        if not text:
            return 0.0
        m = re.search(r'(\d+(?:\.\d+)?)\s*%', text) or re.search(r'(?:GST|CGST|SGST|IGST)\s*(\d+(?:\.\d+)?)', text, re.I)
        if m:
            return float(m.group(1))
        val = self._clean_number(text)
        return val if val <= 50 else 0.0

    def _extract_table_lines(self, all_pages_words):
        lines_data, table_started, col_mapping, pending_line = [], False, {}, None
        for words in all_pages_words:
            for line_words in self._group_words_by_lines(words):
                tokens = [w[4].strip() for w in line_words if w[4].strip()]
                combined = " ".join(tokens).lower()

                if table_started and any(k in combined for k in self.FOOTER_KEYWORDS):
                    table_started = False
                    break

                if not table_started:
                    if any(k in combined for k in self.HEADER_MAP['name']) and any(k in combined for k in self.HEADER_MAP['amount'] + self.HEADER_MAP['price']):
                        table_started = True
                        col_mapping = {key: [] for key in self.HEADER_MAP}
                        for w in line_words:
                            text = w[4].lower()
                            for k, syn in self.HEADER_MAP.items():
                                if any(s in text for s in syn):
                                    col_mapping[k].append((w[0], w[2]))
                        continue

                if table_started and len(tokens) >= 2:
                    row = {k: [] for k in col_mapping}
                    for w in line_words:
                        x = (w[0] + w[2]) / 2.0
                        for k, ranges in col_mapping.items():
                            if any(s - 10 <= x <= e + 10 for s, e in ranges):
                                row[k].append(w[4].strip())
                                break

                    p_name = " ".join(row['name'])
                    p_name = re.sub(r'^\s*\d+\s*[\.\-\)]*\s*', '', p_name).strip()
                    qty = self._clean_number("".join(row['qty']))
                    price = self._clean_number("".join(row['price']))
                    disc = self._clean_number("".join(row['discount']))
                    tax = self._extract_tax_value("".join(row['tax']))
                    amt = self._clean_number("".join(row['amount']))

                    if p_name and not (qty or price or amt):
                        if pending_line:
                            pending_line["name"] += " " + p_name
                        continue

                    if pending_line:
                        lines_data.append(pending_line)
                    if p_name:
                        if amt > 0 and qty == 0 and price == 0:
                            qty, price = 1, amt
                        elif qty > 0 and amt > 0 and price == 0:
                            price = amt / qty
                        pending_line = {"name": p_name, "qty": qty or 1, "price": price, "discount": disc, "tax": tax}

            if pending_line:
                lines_data.append(pending_line)
                pending_line = None
        return lines_data or self._generic_fallback(all_pages_words)

    def _extract_invoice_tax(self, text):
        text = text.upper()
        match = re.search(r'(?:GST|IGST)\s*(?:\(|@)?\s*(\d+(?:\.\d+)?)', text)
        if match:
            return float(match.group(1))
        cgst = re.search(r'CGST\s*(?:\(|@)?\s*(\d+(?:\.\d+)?)', text)
        sgst = re.search(r'SGST\s*(?:\(|@)?\s*(\d+(?:\.\d+)?)', text)
        return float(cgst.group(1)) + float(sgst.group(1)) if cgst and sgst else 0.0

    def _generic_fallback(self, all_pages):
        res = []
        for words in all_pages:
            for line in self._group_words_by_lines(words):
                tokens = [w[4].strip() for w in line if w[4].strip()]
                amt = self._clean_number(tokens[-1])
                if len(tokens) >= 2 and amt > 0 and not any(k in " ".join(tokens).lower() for k in self.FOOTER_KEYWORDS):
                    res.append({"name": " ".join(tokens[:-1]), "qty": 1.0, "price": amt})
        return res

    def _is_footer_line(self, lower: str) -> bool:
        return any(k in lower for k in self.FOOTER_KEYWORDS) if lower else False

    def _filter_invalid_lines(self, lines):
        valid = []
        for line in lines:
            name = (line.get("name") or "").strip()
            price = float(line.get("price") or 0.0)
            amount = float(line.get("amount") or 0.0)
            if price == 0.0 and amount == 0.0 and (len(name.split()) > 10 or len(name) < 3):
                continue
            valid.append(line)
        return valid

    def _extract_ocr_table_lines(self, all_pages_words):
        lines_data = []
        for words in all_pages_words:
            if not words:
                continue
            grouped = self._group_words_by_lines(words)
            if not grouped:
                continue

            header_idx, columns = None, None
            for i, line_words in enumerate(grouped):
                if line_words:
                    columns = self._detect_header_columns(line_words)
                    if columns:
                        header_idx = i
                        break

            if header_idx is None or not columns:
                continue

            footer_start = len(grouped)
            for j in range(header_idx + 1, len(grouped)):
                line_text = " ".join(w[4].strip() for w in grouped[j] if w[4].strip())
                if self._is_footer_line(line_text.lower()):
                    footer_start = j
                    break

            raw_rows = []
            for k in range(header_idx + 1, footer_start):
                parsed = self._assign_word_to_column(grouped[k], columns)
                if parsed is not None:
                    raw_rows.append(parsed)

            lines_data.extend(self._merge_multiline_rows(raw_rows))
        return self._filter_invalid_lines(lines_data)

    def _pdf_to_images(self, pdf_bytes):
        if not fitz:
            return []
        try:
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                images = []
                for page in doc:
                    pix = page.get_pixmap(dpi=300)
                    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR if pix.n == 4 else cv2.COLOR_RGB2BGR)
                    images.append(img)
                return images
        except Exception:
            return []

    def _ocr_image_words(self, image):
        if cv2 is None or np is None or not self._get_ocr_engine():
            return []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        ocr_input = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

        try:
            ocr_result, _ = self._rapid_engine(ocr_input)
        except Exception:
            ocr_result = None

        if not ocr_result:
            try:
                ocr_result, _ = self._rapid_engine(image)
            except Exception:
                return []

        words = []
        if ocr_result:
            for item in ocr_result:
                box, text = item[0], item[1]
                score = item[2] if len(item) > 2 else 1.0
                txt = (text or "").strip()
                if not txt or (float(score) * 100) < 15:
                    continue

                xs, ys = [p[0] for p in box], [p[1] for p in box]
                left, top, right, bottom = min(xs), min(ys), max(xs), max(ys)
                tokens = txt.split()

                if len(tokens) > 1:
                    total_chars = sum(len(t) for t in tokens) or 1
                    width, cursor = right - left, left
                    for tok in tokens:
                        tok_w = width * (len(tok) / total_chars)
                        words.append((int(cursor), int(top), int(cursor + tok_w), int(bottom), tok))
                        cursor += tok_w
                else:
                    words.append((int(left), int(top), int(right), int(bottom), txt))
        return words

    def _detect_header_columns(self, line_words):
        line_words.sort(key=lambda w: w[0])
        columns = {}
        for i in range(len(line_words)):
            word = line_words[i][4].lower()
            x = (line_words[i][0] + line_words[i][2]) / 2
            phrase = f"{word} {line_words[i+1][4].lower()}" if i+1 < len(line_words) else word
            for field, aliases in self.HEADER_MAP.items():
                if any(SequenceMatcher(None, word, a).ratio() > 0.75 or SequenceMatcher(None, phrase, a).ratio() > 0.75 for a in aliases):
                    columns[field] = (columns.get(field, x) + x) / 2
                    break
        if "price" not in columns or "amount" not in columns or len(columns) < 4:
            return None
        if "name" not in columns:
            columns["name"] = min(columns.values())
        return dict(sorted(columns.items(), key=lambda x: x[1]))

    def _assign_word_to_column(self, row_words, columns):
        col_x_coords = sorted(columns.values())
        dynamic_threshold = min([col_x_coords[i + 1] - col_x_coords[i] for i in range(len(col_x_coords) - 1)]) * 0.6 if len(col_x_coords) > 1 else 200
        row_data = {"name": [], "hsn": None, "qty": None, "unit": None, "price": None, "discount": None, "tax": None, "amount": None}

        for word in row_words:
            text = word[4].strip()
            x = (word[0] + word[2]) / 2
            col = self._nearest_column(x, columns)
            if col != "name" and abs(columns[col] - x) > dynamic_threshold:
                continue
            if col == "name":
                if not row_data["name"] and re.fullmatch(r"\d+", text):
                    continue
                row_data["name"].append(text)
            elif col in ("hsn", "unit"):
                row_data[col] = text
            elif col in ("qty", "price", "discount", "tax", "amount"):
                val = self._clean_number(text)
                row_data[col] = max(row_data[col], val) if row_data[col] is not None else val

        row_data["name"] = re.sub(r"^\d+\s*[\.\-\)]*\s*", "", " ".join(row_data["name"]).strip()).strip()
        if not row_data["name"] or self._is_footer_line(row_data["name"].lower()):
            return None

        qty, price, amount = row_data["qty"] or 1.0, row_data["price"] or 0.0, row_data["amount"] or 0.0
        if amount == 0 and price > 0:
            amount = round(price * qty, 2)
        elif price == 0 and amount > 0 and qty > 0:
            price = round(amount / qty, 2)

        return {
            "name": row_data["name"], "hsn": row_data["hsn"], "qty": round(qty, 2), "unit": row_data["unit"],
            "price": round(price, 2), "discount": row_data["discount"] or 0.0, "tax": row_data["tax"] or 0.0, "amount": round(amount, 2)
        }

    def _nearest_column(self, x, columns):
        cols = sorted(columns.items(), key=lambda c: c[1])
        for i, (field, cx) in enumerate(cols):
            if i == len(cols) - 1 or x < (cx + cols[i+1][1]) / 2:
                return field
        return cols[-1][0]

    def _merge_multiline_rows(self, rows):
        if not rows:
            return []
        merged, current = [], rows[0]
        for nxt in rows[1:]:
            is_prod = (nxt["qty"] not in (None, 0.0, 1.0)) or (nxt["price"] != 0.0) or (nxt["amount"] != 0.0)
            if nxt["name"] and len(nxt["name"].split()) <= 4 and not is_prod:
                current["name"] += " " + nxt["name"]
            else:
                merged.append(current)
                current = nxt
        merged.append(current)
        return merged