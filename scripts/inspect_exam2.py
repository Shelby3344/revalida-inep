"""Print the first 60 chars of the *first 3 questions* per exam to identify area order.
Also print the cover page text (first page).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_classify import extract_text_by_column

import pdfplumber

PDF_DIR = Path(__file__).parent.parent / "data" / "pdfs"

QUESTION_RE = re.compile(r"QUEST[ÃA]O\s+(\d{1,3})", re.IGNORECASE)


def inspect(pdf_path: Path):
    print(f"\n=== {pdf_path.name} ===")
    # First page text
    with pdfplumber.open(pdf_path) as pdf:
        if pdf.pages:
            first = pdf.pages[0].extract_text() or ""
            print("--- First page ---")
            print(first[:600])
            print("--- /First page ---")

    text = extract_text_by_column(str(pdf_path))
    if not text:
        return

    # For each question number 1-100, grab first 80 chars of its text after "QUESTAO N"
    matches = list(QUESTION_RE.finditer(text))
    for i, m in enumerate(matches):
        qnum = int(m.group(1))
        if qnum in (1, 2, 21, 22, 41, 42, 61, 62, 81, 82, 100):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            chunk = text[start:end].strip()
            chunk = re.sub(r"\s+", " ", chunk)
            print(f"  Q{qnum:>3}: {chunk[:140]}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect(PDF_DIR / sys.argv[1])
    else:
        for p in sorted(PDF_DIR.glob("*_PV_objetiva*.pdf")):
            inspect(p)
