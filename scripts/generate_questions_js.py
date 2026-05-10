"""
Generate JS files from questoes_db.json (pipeline v6 — 3-level classification).

Outputs:
  - generatedData.js    — full questions (lazy-loaded by TopicQuestions)
  - generatedMeta.js    — slim metadata (loaded by Dashboard)
  - generatedTopics.js  — computed topicsData array (replaces hardcoded topicsData.js entries)
"""
import json, re, unicodedata
from pathlib import Path
from collections import defaultdict, Counter

BASE        = Path(__file__).parent.parent
QUESTOES_DB = BASE / "data" / "questoes_db.json"
ESTATISTICAS= BASE / "data" / "estatisticas_temas.json"
DATA_OUT    = BASE / "src" / "data" / "generatedData.js"
META_OUT    = BASE / "src" / "data" / "generatedMeta.js"
TOPICS_OUT  = BASE / "src" / "data" / "generatedTopics.js"

AREA_ID = {
    "Clínica Médica":            "clinica",
    "Cirurgia Geral":            "cirurgia",
    "Pediatria":                 "pediatria",
    "Ginecologia & Obstetrícia": "gineco",
    "Medicina Preventiva":       "preventiva",
}

AREA_META = {
    "clinica":    {"color": "bg-blue-500",   "hex": "#0071e3", "name": "Clínica Médica",             "desc": "Clínica Médica — 20 questões por prova"},
    "cirurgia":   {"color": "bg-orange-500", "hex": "#e8541e", "name": "Cirurgia Geral",             "desc": "Cirurgia Geral — 20 questões por prova"},
    "pediatria":  {"color": "bg-green-500",  "hex": "#34c759", "name": "Pediatria",                  "desc": "Pediatria — 20 questões por prova"},
    "gineco":     {"color": "bg-pink-500",   "hex": "#ac3e92", "name": "Ginecologia & Obstetrícia",  "desc": "Ginecologia e Obstetrícia — 20 questões por prova"},
    "preventiva": {"color": "bg-indigo-500", "hex": "#5856d6", "name": "Med. Preventiva",            "desc": "Medicina Preventiva e Saúde Coletiva — 20 questões por prova"},
}

def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower().strip()).strip('-')

def topic_id(grande_area, tema_principal):
    aid = AREA_ID.get(grande_area, "outros")
    return f"{aid}-{slug(tema_principal)}"

def js_str(s):
    if not s: return ''
    return str(s).replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ").replace("\r", "")

# ──────────────────────────────────────────────────────────────
# Load data
# ──────────────────────────────────────────────────────────────
with open(QUESTOES_DB, encoding="utf-8") as f:
    questions = json.load(f)

with open(ESTATISTICAS, encoding="utf-8") as f:
    stats = json.load(f)

meta = stats.get("_meta", {})
all_editions = sorted(meta.get("edicoes", {}).keys())
total = meta.get("total_questoes", len(questions))

# Enrich each question with derived JS fields
for q in questions:
    q["areaId"]  = AREA_ID.get(q["grande_area"], "outros")
    q["topicId"] = topic_id(q["grande_area"], q["tema_principal"])
    q["subtopic"] = q["subtopico"]

# ──────────────────────────────────────────────────────────────
# generatedData.js  (full questions — lazy loaded)
# ──────────────────────────────────────────────────────────────
lines = [
    "// Auto-generated from questoes_db.json — DO NOT EDIT MANUALLY",
    "// Full question bank (text + options) — lazy-loaded by TopicQuestions.",
    "",
    "export const generatedQuestions = [",
]
for q in questions:
    opts = "[" + ", ".join(f"'{js_str(o)}'" for o in q["options"]) + "]"
    lines += [
        "  {",
        f"    id: '{js_str(q['id'])}',",
        f"    topicId: '{js_str(q['topicId'])}',",
        f"    subtopic: '{js_str(q['subtopic'])}',",
        f"    areaId: '{js_str(q['areaId'])}',",
        f"    examRef: '{js_str(q['examRef'])}',",
        f"    year: {q['year']},",
        f"    questionNumber: {q['questionNumber']},",
        f"    questionText: '{js_str(q['questionText'])}',",
        f"    options: {opts},",
        f"    correctAnswer: '{js_str(q.get('correctAnswer', ''))}',",
        "  },",
    ]
lines += ["];", ""]
lines.append(f"export const generatedTotalQuestions = {total};")

with open(DATA_OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

# ──────────────────────────────────────────────────────────────
# generatedMeta.js  (slim — loaded by Dashboard)
# ──────────────────────────────────────────────────────────────
topic_counts   = Counter(q["topicId"]  for q in questions)
subtopic_counts= Counter(q["subtopic"] for q in questions)
area_counts    = Counter(q["areaId"]   for q in questions)

meta_lines = [
    "// Auto-generated — slim metadata for Dashboard (no questionText/options).",
    "// Full text is in generatedData.js (lazy-loaded).",
    "",
    "export const generatedQuestionsMeta = [",
]
for q in questions:
    meta_lines += [
        "  {",
        f"    id: '{js_str(q['id'])}',",
        f"    topicId: '{js_str(q['topicId'])}',",
        f"    subtopic: '{js_str(q['subtopic'])}',",
        f"    areaId: '{js_str(q['areaId'])}',",
        f"    examRef: '{js_str(q['examRef'])}',",
        "  },",
    ]
meta_lines += ["];", ""]

meta_lines += ["export const generatedTopicCounts = {"]
for tid, cnt in sorted(topic_counts.items()):
    meta_lines.append(f"  '{js_str(tid)}': {cnt},")
meta_lines += ["};", ""]

meta_lines += ["export const generatedSubtopicCounts = {"]
for st, cnt in sorted(subtopic_counts.items(), key=lambda x: -x[1]):
    meta_lines.append(f"  '{js_str(st)}': {cnt},")
meta_lines += ["};", ""]

meta_lines += ["export const generatedAreaCounts = {"]
for aid, cnt in sorted(area_counts.items()):
    meta_lines.append(f"  '{js_str(aid)}': {cnt},")
meta_lines += ["};", ""]

meta_lines.append(f"export const generatedTotalQuestions = {total};")

with open(META_OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(meta_lines))

# ──────────────────────────────────────────────────────────────
# generatedTopics.js  (computed topicsData array)
# ──────────────────────────────────────────────────────────────
def _trend(por_edicao, editions):
    counts = [por_edicao.get(e, 0) for e in editions]
    if len(counts) < 4:
        return "stable"
    mid = len(counts) // 2
    first_half = sum(counts[:mid]) or 1
    second_half = sum(counts[mid:]) or 0
    ratio = second_half / first_half
    if ratio > 1.25:
        return "up"
    if ratio < 0.75:
        return "down"
    return "stable"

# Build per-subtopic edition lookup: (grande_area, tema_principal, subtopico) -> set of examRef
sub_editions = defaultdict(set)
for q in questions:
    key = (q["grande_area"], q["tema_principal"], q["subtopico"])
    sub_editions[key].add(q["examRef"])

topic_entries = []
for area_name, area_cfg in stats.items():
    if area_name.startswith("_"):
        continue
    aid = AREA_ID.get(area_name, "outros")
    area_n = area_cfg["count"]
    ameta = AREA_META.get(aid, {})

    for tema_name, tema_cfg in area_cfg.get("temas", {}).items():
        tid = topic_id(area_name, tema_name)
        por_edicao = tema_cfg.get("por_edicao", {})
        editions_with_data = sorted(por_edicao.keys())

        trend = _trend(por_edicao, editions_with_data)

        editions_with_tema = sum(1 for e in all_editions if por_edicao.get(e, 0) > 0)
        probability = round(100 * editions_with_tema / max(len(all_editions), 1))

        avg_per_exam = round(tema_cfg["count"] / max(len(all_editions), 1), 1)

        # History: last 5 editions with data
        hist_editions = editions_with_data[-5:]
        history = [por_edicao.get(e, 0) for e in hist_editions]

        subtopics_list = []
        for s in tema_cfg.get("top_subtopicos", []):
            key = (area_name, tema_name, s["subtopico"])
            eds = sub_editions.get(key, set())
            sub_prob = round(100 * len(eds) / max(len(all_editions), 1))
            subtopics_list.append({
                "name": s["subtopico"],
                "count": s["count"],
                "probability": sub_prob,
            })
        details_str = ", ".join(s["name"] for s in subtopics_list[:3])

        topic_entries.append({
            "id": tid,
            "areaId": aid,
            "areaName": ameta.get("name", area_name),
            "areaColor": ameta.get("hex", "#888"),
            "title": tema_name,
            "details": details_str,
            "percentage": tema_cfg["pct_dentro_area"],
            "absoluteCount": tema_cfg["count"],
            "trend": trend,
            "probability": f"{probability}%",
            "avgPerExam": str(avg_per_exam),
            "history": history,
            "subtopics": subtopics_list,
        })

# Write generatedTopics.js
tlines = [
    "// Auto-generated computed topic metadata from estatisticas_temas.json.",
    "// Replaces the old hardcoded topicsData entries in topicsData.js.",
    "",
    "export const generatedTopicsData = [",
]
for t in topic_entries:
    subs_js = "[" + ", ".join(
        f"{{name: '{js_str(s['name'])}', count: {s['count']}, probability: {s['probability']}}}"
        for s in t["subtopics"]
    ) + "]"
    hist_js = "[" + ", ".join(str(h) for h in t["history"]) + "]"
    tlines += [
        "  {",
        f"    id: '{js_str(t['id'])}',",
        f"    areaId: '{js_str(t['areaId'])}',",
        f"    areaName: '{js_str(t['areaName'])}',",
        f"    areaColor: '{js_str(t['areaColor'])}',",
        f"    title: '{js_str(t['title'])}',",
        f"    details: '{js_str(t['details'])}',",
        f"    percentage: {t['percentage']},",
        f"    absoluteCount: {t['absoluteCount']},",
        f"    trend: '{t['trend']}',",
        f"    probability: '{js_str(t['probability'])}',",
        f"    avgPerExam: '{js_str(t['avgPerExam'])}',",
        f"    history: {hist_js},",
        f"    subtopics: {subs_js},",
        "  },",
    ]
tlines += ["];", ""]
tlines.append(f"export const generatedExamsCovered = {json.dumps(all_editions)};")

with open(TOPICS_OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(tlines))

print(f"[OK] generatedData.js    — {len(questions)} questões")
print(f"[OK] generatedMeta.js    — {len(questions)} slim entries, {len(topic_counts)} topics")
print(f"[OK] generatedTopics.js  — {len(topic_entries)} topic entries")
print(f"     Topics: {[t['id'] for t in topic_entries]}")
