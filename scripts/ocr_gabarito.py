"""
Extrai gabaritos de PDFs escaneados via OCR (fitz + tesseract).
Gera/atualiza data/gabaritos_manuais.json com as respostas encontradas.

Uso:
  python scripts/ocr_gabarito.py
"""
import json, re, sys
from pathlib import Path

BASE     = Path(__file__).parent.parent
OUT_FILE = BASE / "data" / "gabaritos_manuais.json"

try:
    import fitz
except ImportError:
    raise SystemExit("pip install pymupdf")

try:
    import pytesseract
    from PIL import Image
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    OCR_OK = True
except Exception:
    OCR_OK = False
    print("[WARN] pytesseract/PIL não disponível — OCR desabilitado")

PDF_NEW = BASE / "Provas do revalida PDF" / "revalida provas"

# PDFs para processar via OCR
OCR_TARGETS = [
    ("2013", PDF_NEW / "2013/caderno cinza/po_cinza_gabarito_definitivo_revalida_2013.pdf"),
]

def ocr_page(page):
    mat = fitz.Matrix(3, 3)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples).convert("L")
    return pytesseract.image_to_string(img, lang="eng", config="--psm 6")

def parse_ocr_text(text):
    """Extract {question_number: answer} from raw OCR text."""
    answers = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Fix common OCR misreads
        line = re.sub(r'\bSL(\d)', r'5\1', line)   # SL1 -> 51
        line = re.sub(r'\b7O\b', '70', line)        # 7O -> 70
        line = re.sub(r'\b838\b', '88', line)       # 838 -> 88
        line = re.sub(r'\bBSE\b', '55E', line)      # BSE -> 55E
        line = re.sub(r'79\.C', '79C', line)        # 79.C -> 79C
        # Extract all (number, letter) pairs from the line
        for m in re.finditer(r'(\d{1,3})\s*([A-EX])\b', line):
            q, a = int(m.group(1)), m.group(2).upper()
            if 1 <= q <= 120:
                answers[q] = None if a == "X" else a
    return answers

def run():
    # Load existing file or start fresh
    if OUT_FILE.exists():
        with open(OUT_FILE, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    if not OCR_OK:
        print("[SKIP] OCR não disponível")
    else:
        for edition, pdf_path in OCR_TARGETS:
            if not pdf_path.exists():
                print(f"[SKIP] {edition}: arquivo não encontrado — {pdf_path}")
                continue

            print(f"[OCR] {edition}: {pdf_path.name} ...")
            doc = fitz.open(str(pdf_path))
            full_text = ""
            for page in doc:
                full_text += ocr_page(page) + "\n"
            doc.close()

            answers = parse_ocr_text(full_text)
            if answers:
                # Convert keys to strings for JSON
                data[edition] = {str(k): v for k, v in sorted(answers.items())}
                print(f"  -> {len(answers)} respostas extraídas")
            else:
                print(f"  -> 0 respostas (verifique o PDF)")

    # Ensure placeholders for editions without PDF gabarito
    for edition in ["2017", "2020-1", "2020-2"]:
        if edition not in data:
            data[edition] = {}
            print(f"[MANUAL] {edition}: placeholder criado (preencha manualmente)")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Salvo em {OUT_FILE}")
    print("     Preencha manualmente 2017, 2020-1, 2020-2 neste arquivo.")

if __name__ == "__main__":
    run()
