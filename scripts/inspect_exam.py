"""Quick inspection: print the first marker of each area block in a PDF.

We extract text via the same column-aware reader and print:
- header lines that look like area boundaries (CLINICA, CIRURGIA, GO, PEDIATRIA, SAUDE COLETIVA / PREVENTIVA)
- the question number near each header
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_classify import extract_text_by_column

PDF_DIR = Path(__file__).parent.parent / "data" / "pdfs"

# Headers commonly found in Revalida exams
HEADER_PATTERNS = [
    r"\bCL[IÍ]NICA\s+M[ÉE]DICA\b",
    r"\bCIRURGIA\s+GERAL\b",
    r"\bGINECOLOGIA\s+E\s+OBSTETR[ÍI]CIA\b",
    r"\bPEDIATRIA\b",
    r"\bSA[ÚU]DE\s+COLETIVA\b",
    r"\bMEDICINA\s+PREVENTIVA\b",
    r"\bMEDICINA\s+DE\s+FAM[ÍI]LIA\b",
]

QUESTION_RE = re.compile(r"QUEST[ÃA]O\s+(\d{1,3})", re.IGNORECASE)


def inspect(pdf_path: Path):
    text = extract_text_by_column(str(pdf_path))
    if not text:
        print(f"  [skip] no text from {pdf_path.name}")
        return

    print(f"\n=== {pdf_path.name} ===")
    # Walk through text, print every header occurrence with the *previous* QUESTAO N (anchor)
    last_qnum = None
    for line in text.split("\n"):
        qm = QUESTION_RE.search(line)
        if qm:
            last_qnum = int(qm.group(1))
        for pat in HEADER_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                print(f"  [near Q{last_qnum}] {line.strip()[:120]}")
                break

    # Also report all unique question numbers (sanity check)
    qnums = sorted({int(m.group(1)) for m in QUESTION_RE.finditer(text)})
    print(f"  Question numbers: {len(qnums)} found, range {qnums[0] if qnums else '?'}–{qnums[-1] if qnums else '?'}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if target:
        inspect(PDF_DIR / target)
    else:
        for p in sorted(PDF_DIR.glob("*_PV_objetiva*.pdf")):
            inspect(p)
