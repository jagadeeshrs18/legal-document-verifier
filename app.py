"""
Legal Document Verifier - Flask app
Milestone: document upload + text extraction (PDF / DOCX / scanned images).

Run:
    pip install -r requirements.txt
    python app.py
Then open http://127.0.0.1:5000
"""

import os
import json
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from extraction.extractor import extract_text, is_supported
from segmentation.clause_segmenter import segment_clauses

try:
    from retrieval.clause_retriever import ClauseRetriever
    _retriever = ClauseRetriever()
    RETRIEVAL_ENABLED = True
except Exception as e:
    print(f"[warning] Clause-to-law retrieval disabled: {e}")
    print("          (Run vectorization/embed_dataset.py first to enable it.)")
    _retriever = None
    RETRIEVAL_ENABLED = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
EXTRACTED_FOLDER = os.path.join(BASE_DIR, "data", "extracted")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)

MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-this"  # replace before deployment
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "document" not in request.files:
        flash("No file part in the request.")
        return redirect(url_for("index"))

    file = request.files["document"]

    if file.filename == "":
        flash("No file selected.")
        return redirect(url_for("index"))

    if not is_supported(file.filename):
        flash("Unsupported file type. Upload a PDF, DOCX, or image (png/jpg).")
        return redirect(url_for("index"))

    # Save the upload with a unique name so parallel users don't collide
    unique_id = uuid.uuid4().hex[:8]
    safe_name = f"{unique_id}_{file.filename}"
    saved_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
    file.save(saved_path)

    # Run text extraction
    try:
        result = extract_text(saved_path)
    except Exception as e:
        flash(f"Extraction failed: {e}")
        return redirect(url_for("index"))

    # Split the extracted text into individual clauses
    result["clauses"] = segment_clauses(result.get("full_text", ""))
    result["total_clauses"] = len(result["clauses"])

    # For each clause, find the most relevant matching Indian law /
    # template provisions from the vectorized reference dataset
    if RETRIEVAL_ENABLED:
        result["clauses"] = _retriever.attach_matches(result["clauses"])
    result["retrieval_enabled"] = RETRIEVAL_ENABLED

    # Persist the extracted + segmented result as JSON (useful for the
    # next pipeline stage: NLP clause classification / risk scoring)
    json_name = f"{unique_id}.json"
    with open(os.path.join(EXTRACTED_FOLDER, json_name), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return render_template("result.html", result=result, json_name=json_name)


@app.route("/api/extract", methods=["POST"])
def api_extract():
    """JSON API version, useful once the React/other frontend is wired up."""
    if "document" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["document"]
    if file.filename == "" or not is_supported(file.filename):
        return jsonify({"error": "Unsupported or missing file"}), 400

    unique_id = uuid.uuid4().hex[:8]
    saved_path = os.path.join(app.config["UPLOAD_FOLDER"], f"{unique_id}_{file.filename}")
    file.save(saved_path)

    try:
        result = extract_text(saved_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
