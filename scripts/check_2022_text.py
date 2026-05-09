"""Dump the raw text of 2022 PDF (page 2) to a UTF-8 file so we can see whether the text
is genuinely garbled (CID without ToUnicode) or just a console-encoding artifact.
"""
from pathlib import Path
import fitz
import pdfplumber

PDF_DIR = Path(__file__).parent.parent / "data" / "pdfs"
OUT = Path(__file__).parent.parent / "data" / "_2022_dump.txt"


def main():
    pdf_path = PDF_DIR / "2022_PV_objetiva_1.pdf"
    out_lines: list[str] = []

    out_lines.append("=== fitz get_text('text') page 2 ===")
    doc = fitz.open(pdf_path)
    out_lines.append(doc[1].get_text("text"))
    doc.close()

    out_lines.append("\n=== pdfplumber extract_text() page 2 ===")
    with pdfplumber.open(pdf_path) as pdf:
        out_lines.append(pdf.pages[1].extract_text() or "<empty>")
        out_lines.append("\n=== chars sample page 2 ===")
        for c in pdf.pages[1].chars[:20]:
            out_lines.append(repr({"text": c["text"], "fontname": c.get("fontname", ""), "x0": c.get("x0")}))

    OUT.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
