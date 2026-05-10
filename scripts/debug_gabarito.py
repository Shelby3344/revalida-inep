"""Debug gabarito parsing for editions with 0 answers."""
import pdfplumber, re
from pathlib import Path

BASE     = Path(__file__).parent.parent
PDF_NEW  = BASE / "Provas do revalida PDF" / "revalida provas"
PDF_OLD  = BASE / "data" / "pdfs"

FAILING = [
    ("2011",   PDF_NEW / "2011/inep_gabarito_definitivo_revalida-2011.pdf"),
    ("2013",   PDF_NEW / "2013/caderno cinza/po_cinza_gabarito_definitivo_revalida_2013.pdf"),
    ("2020-1", PDF_NEW / "2020/Prova Objetiva 01/gabarito_caderno_1.pdf"),
    ("2023-1", PDF_NEW / "2023/Prova Objetiva 02/2023_1_GB_objetiva_definitivo.pdf"),
    ("2024-1", PDF_NEW / "2024/Prova Objetiva 02/2024_1_GB_objetiva.pdf"),
]

for label, path in FAILING:
    print(f"\n=== {label} ({path.name}) ===")
    if not path.exists():
        print("  FILE NOT FOUND:", path)
        continue
    with pdfplumber.open(path) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    # Show first 500 chars
    print("  First 500 chars:")
    print(repr(text[:500]))
    # Try regex
    m = re.findall(r'\b(\d{1,3})\s*[\.:\-]?\s*([A-E])\b', text)
    valid = [(int(n), a) for n, a in m if 1 <= int(n) <= 120]
    print(f"  Pattern matches (valid 1-120): {valid[:10]}")
    # Show lines with digits
    digit_lines = [l.strip() for l in text.splitlines() if re.search(r'\d', l)][:10]
    print("  Lines with digits (first 10):", digit_lines)
