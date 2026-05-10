"""Check answer key coverage per edition."""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent

with open(BASE / "data/questoes_db.json", encoding="utf-8") as f:
    qs = json.load(f)

by_edition = {}
for q in qs:
    e = q["examRef"]
    if e not in by_edition:
        by_edition[e] = {"total": 0, "with_ans": 0}
    by_edition[e]["total"] += 1
    if q["correctAnswer"]:
        by_edition[e]["with_ans"] += 1

print("Edition    total  answers")
for e in sorted(by_edition):
    d = by_edition[e]
    pct = round(100 * d["with_ans"] / d["total"])
    print(f"  {e:<10s} {d['total']:3d}    {d['with_ans']:3d}  ({pct}%)")
