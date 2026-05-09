"""Show first 200 chars of each question's text + current classified area + a smarter
proposed area (from age/gestante/cirurgia markers).
"""
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_classify import extract_text_by_column, extract_questions, classify_question

PDF_DIR = Path(__file__).parent.parent / "data" / "pdfs"


def normalize(t):
    return unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()


PED_MARKERS = [
    r"\bcrianca\b", r"\bbebe\b", r"\blactente\b", r"\brecem-?nascido\b", r"\brn\b",
    r"\bneonat[oa]\b", r"\bescolar\b", r"\badolescente\b", r"\bpre-?escolar\b",
    r"\bpueric", r"\bcalendario(\s+nacional)?\s+de\s+vacinacao\b",
    r"\bmenina(\s+de)?\s+\d+\s+(anos?|meses?)\b",
    r"\bmenino(\s+de)?\s+\d+\s+(anos?|meses?)\b",
    r"\bcom\s+\d+\s+(meses|dias)\s+de\s+(vida|idade)\b",
    r"\bcom\s+([1-9]|1[0-7])\s+anos\b",
    r"\bde\s+([1-9]|1[0-7])\s+anos(\s+de\s+idade)?\b",
    r"\baleitamento\s+materno\b",
    r"\binfant[il]", r"\bpedi[aá]tric[oa]\b", r"\bmae(\s+leva|\s+traz)\b",
]

GO_MARKERS = [
    r"\bgestante\b", r"\bgravidez\b", r"\bgravida\b",
    r"\bidade\s+gestacional\b", r"\bsemanas?\s+de\s+gestacao\b",
    r"\bpre-?natal\b", r"\bpuerpera\b", r"\bpuerperio\b",
    r"\bparto\b", r"\bcesari?a\b", r"\bcesariana\b",
    r"\bmamogram", r"\butero\b", r"\bcolo\s+ut", r"\bovari[oa]\b",
    r"\bcolpocitologia\b", r"\bpapanicola", r"\bmenarca\b", r"\bmenopausa\b",
    r"\bmultigesta\b", r"\bmultipara\b", r"\bnuligesta\b", r"\bnulipara\b",
    r"\bpre-eclampsia\b", r"\beclampsia\b", r"\bplacenta\b",
    r"\bdpp\b", r"\babortamento\b", r"\bgravidez\s+ectopica\b",
    r"\bcontracept", r"\bplanejamento\s+familiar\b", r"\bdiu\b",
    r"\bnic\s+i\b", r"\bnic\s+ii\b", r"\bnic\s+iii\b", r"\bhpv\b",
    r"\bginecolog", r"\bobstetric",
]

CIR_MARKERS = [
    r"\bpos-?operat", r"\bpre-?operat", r"\bcirurgia\b", r"\bcirurgico\b",
    r"\bapendicite\b", r"\bcolecistite\b", r"\bpancreatite\b",
    r"\bdiverticulite\b", r"\babdome\s+agudo\b",
    r"\btrauma\b", r"\bpolitraumat", r"\batls\b", r"\bfratura\b",
    r"\bqueimadur", r"\bhernia\b",
    r"\bferimento\s+por", r"\bperfuracao\s+intestinal\b",
    r"\bobstrucao\s+intestinal\b", r"\bbridas\b",
    r"\bvesicula\s+biliar\b", r"\bcoledoc",
    r"\bgastrectomia\b", r"\bcolectomia\b", r"\bgastroduodeno",
    r"\bpneumotorax\b", r"\bhemotorax\b",
    r"\bcorpo\s+estranho\b", r"\boclusao\s+intestinal\b",
    r"\benoxaparina\s+pos\b", r"\b5o\s+dia\s+pos-operatorio\b",
]

PREV_MARKERS = [
    r"\bsus\b", r"\blei\s+8\.?080\b", r"\blei\s+8\.?142\b",
    r"\bvigilancia\b", r"\bnotificacao\s+compulsoria\b",
    r"\bsinan\b", r"\bsim\b", r"\bsinasc\b",
    r"\bestrategia\s+saude\s+da\s+familia\b", r"\besf\b",
    r"\bnasf\b", r"\batencao\s+primaria\b", r"\bunidade\s+basica\s+de\s+saude\b",
    r"\brastreamento\b", r"\brastreio\b", r"\bcoeficiente\s+de\s+mortalidade\b",
    r"\bestudo\s+de\s+coorte\b", r"\bensaio\s+clinico\b",
    r"\bsensibilidade\b", r"\bespecificidade\b", r"\bvalor\s+preditivo\b",
    r"\bnivel\s+de\s+prevencao\b", r"\bprevencao\s+primaria\b",
    r"\bprevencao\s+secundaria\b", r"\bprevencao\s+terciaria\b",
    r"\bprevencao\s+quaternaria\b", r"\bler\s*/\s*dort\b",
    r"\bnorma\s+regulamentadora\b", r"\bnr-?\d", r"\bocupacional\b",
    r"\bsaude\s+do\s+trabalhador\b", r"\bfinanciamento\s+do\s+sus\b",
    r"\btabagismo\b",
]


def detect_area_smart(qtext: str) -> str | None:
    n = normalize(qtext)
    # Pediatria first (children)
    for pat in PED_MARKERS:
        if re.search(pat, n):
            # but not if also has gestante (a child of a gestante is a pediatric outcome, but the
            # main subject in gestation is the mother → GO)
            if any(re.search(g, n) for g in [r"\bgestante\b", r"\bgravida\b", r"\bidade\s+gestacional\b", r"\bpre-?natal\b"]):
                continue
            return "Pediatria"
    # GO
    for pat in GO_MARKERS:
        if re.search(pat, n):
            return "Ginecologia & Obstetricia"
    # Cirurgia
    for pat in CIR_MARKERS:
        if re.search(pat, n):
            return "Cirurgia Geral"
    # Preventiva
    for pat in PREV_MARKERS:
        if re.search(pat, n):
            return "Med. Preventiva"
    return None


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "2024_2_PV_objetiva_regular.pdf"
    pdf = PDF_DIR / target
    text = extract_text_by_column(str(pdf))
    qs = extract_questions(text)
    print(f"=== {target}: {len(qs)} questions ===\n")

    counts = {"Pediatria": 0, "Ginecologia & Obstetricia": 0, "Cirurgia Geral": 0,
              "Med. Preventiva": 0, "Clinica Medica": 0, "Unclassified": 0}

    rows = []
    for q in qs:
        smart = detect_area_smart(q["text"])
        rule = classify_question(q["text"])
        old_area = rule["area"] if rule else None
        # If smart finds nothing, fallback to old (or Clinica)
        final = smart or old_area or "Clinica Medica"
        counts[final] += 1
        rows.append((q["number"], smart, old_area, final, q["text"][:120]))

    print("Q | smart | old | final")
    for r in rows[:30]:
        print(f"{r[0]:3d} | {str(r[1])[:18]:18s} | {str(r[2])[:18]:18s} | {r[3][:18]:18s} | {re.sub(chr(10),' ',r[4])[:80]}")
    print("\n--- Counts ---")
    for k, v in counts.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
