"""
clause_segmenter.py
--------------------
Splits extracted contract text into individual clauses.

This is a rule-based segmenter (no ML training data needed) that
recognizes common legal-drafting patterns:
  - "ARTICLE I", "Section 2", "Clause 5"
  - Numbered clauses: "1.", "2.1", "3.2.1"
  - Lettered/roman sub-clauses: "(a)", "(i)"

If no such markers are found (e.g. a plain-prose document), it falls
back to splitting on blank-line-separated paragraphs, so it never
returns a single giant blob.
"""

import re

# Each pattern matches a line that *starts* a new clause.
_CLAUSE_START_PATTERNS = [
    r'ARTICLE\s+[IVXLCDM\d]+',
    r'SECTION\s+\d+(\.\d+)*',
    r'CLAUSE\s+\d+(\.\d+)*',
    r'\d+(\.\d+)*\.\s+\S',        # "1. " / "2.1 " / "3.2.1 " followed by text
    r'\(?[a-zA-Z]\)\s+\S',        # "(a) " / "a) "
    r'\(?[ivxlcdm]{1,6}\)\s+\S',  # "(i) " / "(iv) "
]

_COMBINED = re.compile(
    '|'.join(f'(?:{p})' for p in _CLAUSE_START_PATTERNS),
    re.IGNORECASE,
)

_LEADING_NUMBER = re.compile(r'^\s*(\(?[\w]+\)?(?:\.\d+)*\.?)\s')


def _looks_like_clause_start(line: str) -> bool:
    return bool(_COMBINED.match(line.strip()))


def segment_clauses(text: str) -> list[dict]:
    """Split `text` into a list of clause dicts:
    {clause_id, clause_number, text, char_count}"""

    lines = [l for l in text.split("\n")]
    clauses = []
    current_lines: list[str] = []
    current_number = None

    def flush():
        nonlocal current_lines, current_number
        joined = "\n".join(current_lines).strip()
        if joined:
            clauses.append({
                "clause_id": len(clauses) + 1,
                "clause_number": current_number,
                "text": joined,
                "char_count": len(joined),
            })
        current_lines = []
        current_number = None

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue

        if _looks_like_clause_start(stripped) and current_lines:
            flush()

        if _looks_like_clause_start(stripped):
            m = _LEADING_NUMBER.match(stripped)
            current_number = m.group(1) if m else None

        current_lines.append(stripped)

    flush()

    # Fallback: no clause markers detected at all -> split by paragraph
    if len(clauses) <= 1:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            clauses = [
                {
                    "clause_id": i + 1,
                    "clause_number": None,
                    "text": p,
                    "char_count": len(p),
                }
                for i, p in enumerate(paragraphs)
            ]

    return clauses
