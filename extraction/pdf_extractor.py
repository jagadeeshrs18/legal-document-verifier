"""
pdf_extractor.py
----------------
Extracts text (and tables) from PDF files.

Two paths are handled:
1. Digital/text-based PDFs  -> fast extraction with PyMuPDF (fitz)
2. Scanned/image-only PDFs  -> render each page to an image and run
   Tesseract OCR on it (via pytesseract)

A PDF is auto-classified as "scanned" if PyMuPDF can't find a real
text layer on its pages.
"""

import pymupdf as fitz   # PyMuPDF (new import name)
import pdfplumber
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from PIL import Image
import io


def is_scanned_pdf(pdf_path: str, min_chars: int = 50) -> bool:
    """Return True if the PDF has no selectable text layer (i.e. it's
    a scan / photo of a document rather than a digitally created PDF)."""
    doc = fitz.open(pdf_path)
    has_text = False
    for page in doc:
        if len(page.get_text("text").strip()) > min_chars:
            has_text = True
            break
    doc.close()
    return not has_text


def extract_text_digital(pdf_path: str) -> list[dict]:
    """Extract text page-by-page from a digital (non-scanned) PDF."""
    doc = fitz.open(pdf_path)
    pages = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        pages.append({
            "page_number": page_num,
            "text": text,
            "char_count": len(text),
            "source": "digital",
        })
    doc.close()
    return pages


def extract_text_ocr(pdf_path: str, dpi: int = 300) -> list[dict]:
    """Extract text from a scanned PDF by rendering each page to an
    image and running Tesseract OCR on it."""
    doc = fitz.open(pdf_path)
    pages = []
    zoom = dpi / 72  # PDF default is 72 dpi
    matrix = fitz.Matrix(zoom, zoom)

    for page_num, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=matrix)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img).strip()
        pages.append({
            "page_number": page_num,
            "text": text,
            "char_count": len(text),
            "source": "ocr",
        })
    doc.close()
    return pages


def extract_tables(pdf_path: str) -> list[dict]:
    """Extract tables (schedules, penalty tables, payment terms, etc.)
    using pdfplumber. Only works on digital PDFs with a text layer."""
    tables = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                for idx, table in enumerate(page.extract_tables()):
                    if not table:
                        continue
                    rows = [" | ".join(cell or "" for cell in row) for row in table]
                    table_text = "\n".join(rows)
                    if table_text.strip():
                        tables.append({
                            "page_number": page_num,
                            "table_index": idx,
                            "text": table_text,
                        })
    except Exception:
        pass
    return tables


def extract_pdf(pdf_path: str) -> dict:
    """Main entry point: decides digital vs scanned and extracts
    accordingly. Returns a structured dict."""
    scanned = is_scanned_pdf(pdf_path)

    if scanned:
        pages = extract_text_ocr(pdf_path)
        tables = []  # OCR table extraction is out of scope for now
    else:
        pages = extract_text_digital(pdf_path)
        tables = extract_tables(pdf_path)

    full_text = "\n\n".join(p["text"] for p in pages if p["text"])

    return {
        "file_type": "pdf",
        "is_scanned": scanned,
        "total_pages": len(pages),
        "pages": pages,
        "tables": tables,
        "full_text": full_text,
        "total_chars": len(full_text),
    }
