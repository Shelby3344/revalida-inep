"""Print the FULL text of unclassified questions across exams.
Helps decide whether the area is genuinely missing or just under-keyworded.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_classify import (
    extract_text_by_column,
    extract_questions,
    classify_question,
)

PDF_DIR = Path(__file__).parent.parent / "data" / "pdfs"


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "2024_2_PV_objetiva_regular.pdf"
    pdf = PDF_DIR / target
    text = extract_text_by_column(str(pdf))
    qs = extract_questions(text)
    print(f"=== {target}: {len(qs)} questions ===\n")

    classified = {}
    unclassified = []
    for q in qs:
        rule = classify_question(q["text"])
        if rule:
            classified[q["number"]] = rule["area"]
        else:
            unclassified.append(q)

    print(f"Classified: {len(classified)}, Unclassified: {len(unclassified)}\n")

    # Print first 200 chars of each unclassified question
    for q in unclassified:
        clean = re.sub(r"\s+", " ", q["text"]).strip()
        print(f"--- Q{q['number']:>3} ---")
        print(clean[:280])
        print()


if __name__ == "__main__":
    main()
