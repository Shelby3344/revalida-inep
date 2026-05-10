"""Audit subtopic distribution and default fallback usage."""
import json
from collections import Counter
from pathlib import Path

BASE = Path(__file__).parent.parent

with open(BASE / "data/questoes_db.json", encoding="utf-8") as f:
    qs = json.load(f)

with open(BASE / "data/estatisticas_temas.json", encoding="utf-8") as f:
    stats = json.load(f)

total = len(qs)

print("=" * 70)
print(f"AUDITORIA DE SUBTÓPICOS — {total} questões")
print("=" * 70)

# Per area/tema breakdown
for area_name, area_cfg in stats.items():
    if area_name.startswith("_"):
        continue
    area_qs = [q for q in qs if q["grande_area"] == area_name]
    print(f"\n{'='*70}")
    print(f"  {area_name.upper()}  ({len(area_qs)} questões)")
    print(f"{'='*70}")

    for tema_name, tema_cfg in area_cfg.get("temas", {}).items():
        tema_qs = [q for q in area_qs if q["tema_principal"] == tema_name]
        if not tema_qs:
            continue

        sub_counter = Counter(q["subtopico"] for q in tema_qs)
        print(f"\n  [{tema_name}]  {len(tema_qs)} questões")

        for sub, cnt in sub_counter.most_common():
            pct = round(100 * cnt / len(tema_qs))
            bar = "#" * (cnt // 2)
            print(f"    {sub:<50s} {cnt:3d}  ({pct:2d}%)  {bar}")

print("\n" + "=" * 70)
print("RESUMO — subtópicos com menos de 3 questões (possível ruído)")
print("=" * 70)
sub_all = Counter(q["subtopico"] for q in qs)
small = [(s, c) for s, c in sub_all.items() if c < 3]
small.sort(key=lambda x: x[1])
for s, c in small:
    area_tema = next((f"{q['grande_area']} / {q['tema_principal']}" for q in qs if q["subtopico"] == s), "?")
    print(f"  {c}x  [{area_tema}]  {s}")

print(f"\nTotal subtópicos únicos: {len(sub_all)}")
print(f"Subtópicos com < 3 questões: {len(small)}")
