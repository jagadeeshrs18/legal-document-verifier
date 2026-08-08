"""
image_extractor.py
-------------------
Extracts text from image files (photos/scans of documents) using
Tesseract OCR.
"""

import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from PIL import Image


def extract_image(image_path: str) -> dict:
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img).strip()

    return {
        "file_type": "image",
        "is_scanned": True,
        "full_text": text,
        "total_chars": len(text),
    }
