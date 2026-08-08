"""
extractor.py
------------
Single entry point used by the Flask app. Looks at the uploaded
file's extension and routes it to the right extraction module.
"""

import os

from .pdf_extractor import extract_pdf
from .docx_extractor import extract_docx
from .image_extractor import extract_image

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}


def is_supported(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in SUPPORTED_EXTENSIONS


def extract_text(file_path: str) -> dict:
    """Dispatch to the correct extractor based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        result = extract_pdf(file_path)
    elif ext == ".docx":
        result = extract_docx(file_path)
    elif ext in {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}:
        result = extract_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    result["filename"] = os.path.basename(file_path)
    return result
