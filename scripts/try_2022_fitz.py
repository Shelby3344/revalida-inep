"""Try to read 2022 PDF via PyMuPDF (fitz) — sometimes handles CID fonts that pdfplumber can't.
If fitz fails too, try fitz.get_text('rawdict') and image-extraction approaches.
"""
import sys
from pathlib import Path

import fitz  # PyMuPDF

PDF_DIR = Path(__file__).parent.parent / "data" / "pdfs"


def main():
    pdf_path = PDF_DIR / "2022_PV_objetiva_1.pdf"
    if not pdf_path.exists():
        print(f"Missing {pdf_path}")
        return

    doc = fitz.open(pdf_path)
    print(f"Pages: {doc.page_count}")
    for i, page in enumerate(doc):
        if i >= 3:
            break
        # Try multiple text extraction modes
        for mode in ("text", "blocks", "words"):
            try:
                txt = page.get_text(mode)
                snippet = (str(txt)[:300] if txt else "<empty>").replace("\n", " | ")
                print(f"  Page {i+1} [{mode}]: {snippet}")
            except Exception as e:
                print(f"  Page {i+1} [{mode}] ERROR: {e}")

        # Show font info
        fonts = page.get_fonts(full=True)
        print(f"  Page {i+1} fonts ({len(fonts)}):")
        for f in fonts[:5]:
            print(f"    {f}")

    doc.close()


if __name__ == "__main__":
    main()
