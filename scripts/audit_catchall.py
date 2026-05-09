"""Audit: list every question that ended up in the area-level catch-all.
For each area, dump the first 200 chars of each catch-all question + frequency
of common keywords, so we can spot missing classification rules.
"""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "extracted_questions.json"


def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def main():
    questions = json.load(open(DATA, encoding="utf-8"))
    catch = [q for q in questions if "Outros Temas" in q["subtopic"]]
    print(f"Total catch-all questions: {len(catch)} / {len(questions)} ({100*len(catch)/len(questions):.1f}%)\n")

    # Group by area
    by_area = {}
    for q in catch:
        by_area.setdefault(q["area"], []).append(q)

    for area, items in sorted(by_area.items()):
        print(f"\n{'=' * 70}")
        print(f"  {area}: {len(items)} catch-all questions")
        print(f"{'=' * 70}")

        # Frequency of medically meaningful tokens (length 4-25, skip stopwords)
        STOP = {
            "uma", "ano", "anos", "com", "que", "para", "por", "dos", "das", "como",
            "mais", "este", "esse", "essa", "ela", "ele", "ela", "eles", "elas",
            "seu", "sua", "seus", "suas", "esta", "essa", "isso", "qual", "deve",
            "fazer", "feito", "feita", "presenta", "apresenta", "esse", "deste",
            "deste", "tambem", "tambem", "tem", "ter", "foi", "ser", "esta",
            "sao", "ate", "the", "and", "of", "in", "to", "que", "antes", "apos",
            "pelo", "pela", "pelos", "pelas", "para", "sem", "sobre", "no", "na",
            "nas", "nos", "lhe", "lhes", "ja", "qual", "porque", "mais", "menos",
            "muito", "pouco", "pacientes", "paciente", "consulta", "atendido",
            "atendida", "trazido", "trazida", "queixando", "relata", "relatando",
            "informa", "informou", "apresentou", "apresentando", "diagnostico",
            "diagnosticada", "diagnosticado", "alternativas", "abaixo", "todas",
            "alternativa", "afirmativa", "correta", "incorreta", "exceto",
            "considerando", "contexto", "situacao", "caso", "atendimento", "deve",
            "devera", "ainda", "mesmo", "mesma", "novo", "nova", "novos", "novas",
            "outro", "outra", "outros", "outras", "primeiro", "primeira",
            "segundo", "segunda", "terceiro", "terceira", "anterior", "atual",
            "presente", "ausente", "presencas", "diferente", "diferentes",
            "sintomas", "sintoma", "exame", "exames",
        }

        ctr: Counter = Counter()
        for q in items:
            for tok in re.findall(r"[a-zA-ZçÇãõáéíóúâêôÁÉÍÓÚÃÕÇ]{4,25}", q["questionText"]):
                t = norm(tok)
                if 4 <= len(t) <= 22 and t not in STOP:
                    ctr[t] += 1

        print("Top 25 tokens in catch-all:")
        for tok, n in ctr.most_common(25):
            print(f"  {n:>4d}  {tok}")
        print()

        # Show first 5 question samples
        print(f"First 8 samples:")
        for q in items[:8]:
            qtxt = re.sub(r"\s+", " ", q["questionText"])[:240]
            print(f"  [{q['examRef']} Q{q['questionNumber']:>3}] {qtxt}")
            print()


if __name__ == "__main__":
    main()
