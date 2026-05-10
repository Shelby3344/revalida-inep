"""Quick sanity check on questoes_db.json quality."""
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).parent.parent

with open(BASE / "data/questoes_db.json", encoding="utf-8") as f:
    qs = json.load(f)

total = len(qs)
with_answer = sum(1 for q in qs if q["correctAnswer"])
editions = sorted(set(q["examRef"] for q in qs))
areas = Counter(q["grande_area"] for q in qs)
temas = Counter(q["tema_principal"] for q in qs)

print(f"Total: {total} questions")
print(f"With correctAnswer: {with_answer} ({round(100*with_answer/total)}%)")
print(f"Editions ({len(editions)}): {editions}")
print(f"\nAreas:")
for a, c in areas.most_common():
    print(f"  {a}: {c}")
print(f"\nTop 10 temas:")
for t, c in temas.most_common(10):
    print(f"  {t}: {c}")

no_opts = [q for q in qs if len(q["options"]) < 4]
print(f"\nQuestions with <4 options: {len(no_opts)}")
for q in no_opts[:5]:
    print(f"  {q['id']}: {len(q['options'])} opts — {q['options'][:2]}")

# Check text quality
short_text = [q for q in qs if len(q["questionText"]) < 30]
print(f"\nQuestions with text <30 chars: {len(short_text)}")
for q in short_text[:3]:
    print(f"  {q['id']}: '{q['questionText']}'")
