# Legal Document Verifier

College major project. Automated legal document analysis: OCR/text
extraction → clause segmentation → NLP-based clause/risk
classification → explainable risk report.

**Current milestone (this commit): document upload + text extraction.**

## Stack
- Backend: Python, Flask
- Text extraction: PyMuPDF, pdfplumber (digital PDFs), Tesseract OCR
  via pytesseract (scanned PDFs / images), python-docx (Word docs)

## Project structure
```
legal-document-verifier/
├── app.py                     # Flask app: routes, upload handling
├── extraction/
│   ├── extractor.py           # dispatches to the right extractor by file type
│   ├── pdf_extractor.py       # digital PDF + scanned PDF (OCR) extraction
│   ├── docx_extractor.py      # Word document extraction
│   └── image_extractor.py     # image OCR (png/jpg/scans)
├── templates/                 # HTML (upload form, results page)
├── static/style.css
├── uploads/                   # uploaded files land here (gitignored except sample)
├── data/
│   ├── extracted/             # extracted text saved as JSON per upload
│   └── reference/
│       └── legislation_and_templates/   # reference dataset, see below
└── requirements.txt
```

## Setup
```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Tesseract OCR must also be installed on the machine (it's a separate
binary, not just a pip package):
- Ubuntu/Debian: `sudo apt install tesseract-ocr`
- macOS: `brew install tesseract`
- Windows: install from https://github.com/UB-Mannheim/tesseract/wiki
  and add it to PATH (or set `pytesseract.pytesseract.tesseract_cmd`
  in `extraction/image_extractor.py` / `pdf_extractor.py` to the
  install path).

## Run
```bash
python app.py
```
Open http://127.0.0.1:5000, upload a PDF/DOCX/image, and it returns
the extracted text plus a saved JSON in `data/extracted/`.

A `/api/extract` JSON endpoint is also available for the frontend
(React or otherwise) to call directly.

## About the reference dataset (`data/reference/`)
This folder is a copy of the already-extracted, pre-processed text
(as JSON) from a teammate's related project (LexIQ — a RAG-based
legal assistant). It contains Indian legislation (Contract Act,
Companies Act, Labour laws, IP laws, GST/MSME compliance acts) and
standard contract templates (NDA, lease, employment, service
agreements, etc.), organized as:

```
data/reference/legislation_and_templates/
├── legislation/   (contract_law, business_law, labour_law, ip_law,
│                   dispute_resolution, property_law, consumer_law)
├── compliance/    (gst, msme)
└── templates/     (employment, confidentiality, business_formation,
                    services, ip, lease, reference)
```

This isn't needed for the text-extraction milestone itself — it's
here for the next stage, where the extracted clauses from an
uploaded contract get compared against this legal reference corpus
to flag risky/unfair terms. `uploads/sample_contract_for_testing.pdf`
is a sample contract (also from that repo) you can use to test the
extraction pipeline right away.

## Roadmap
1. ✅ Upload + text extraction (PDF/DOCX/scanned images)
2. Clause segmentation (split extracted text into individual clauses)
3. Clause classification (LegalBERT / spaCy / scikit-learn) using
   `data/reference/` as grounding
4. Risk scoring engine + explainable report (PDF/JSON) with
   highlighted clauses and recommendations
