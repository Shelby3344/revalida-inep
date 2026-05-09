"""
Generate JS files with extracted questions and subtopic counts.

Outputs (split for faster initial bundle):
  - generatedMeta.js   — small, contains COUNTS only (loaded by Dashboard)
  - generatedData.js   — large, full question text + options (lazy-loaded by TopicQuestions)
"""
import json, re
from pathlib import Path
from collections import defaultdict

EXTRACTED = Path(__file__).parent.parent / "data" / "extracted_questions.json"
OUTPUT = Path(__file__).parent.parent / "src" / "data" / "generatedData.js"
META_OUTPUT = Path(__file__).parent.parent / "src" / "data" / "generatedMeta.js"

# Map extracted subtopic names to topicId by checking which topic IDs appear
# We'll use the RULES mapping from extract_classify.py
# For now, just group by subtopic and let the React app handle it

with open(EXTRACTED, "r", encoding="utf-8") as f:
    questions = json.load(f)

# Escape JS strings
def js_str(s):
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")

# Build questions array as JS
lines = ["// Auto-generated from extracted INEP questions", "// DO NOT EDIT MANUALLY", ""]
lines.append("export const generatedQuestions = [")

for q in questions:
    opts = "[" + ", ".join(f"'{js_str(o)}'" for o in q["options"]) + "]"
    lines.append("  {")
    lines.append(f"    id: '{q['id']}',")
    lines.append(f"    topicId: '{q['topicId']}',")
    lines.append(f"    subtopic: '{js_str(q['subtopic'])}',")
    lines.append(f"    examRef: '{q['examRef']}',")
    lines.append(f"    questionNumber: {q['questionNumber']},")
    lines.append(f"    area: '{q['area']}',")
    lines.append(f"    questionText: '{js_str(q['questionText'])}',")
    lines.append(f"    options: {opts},")
    lines.append(f"    correctAnswer: '{q['correctAnswer']}',")
    lines.append(f"    explanation: '{js_str(q.get('explanation', ''))}',")
    lines.append("  },")

lines.append("];")
lines.append("")

# Generate subtopic counts
subtopic_counts = defaultdict(int)
for q in questions:
    subtopic_counts[q["subtopic"]] += 1

lines.append("export const generatedSubtopicCounts = {")
for st, count in sorted(subtopic_counts.items(), key=lambda x: -x[1]):
    lines.append(f"  '{js_str(st)}': {count},")
lines.append("};")
lines.append("")

# Generate topic counts
topic_counts = defaultdict(int)
for q in questions:
    topic_counts[q["topicId"]] += 1

lines.append("export const generatedTopicCounts = {")
for tid, count in sorted(topic_counts.items()):
    lines.append(f"  '{tid}': {count},")
lines.append("};")
lines.append("")

# Generate area counts
area_counts = defaultdict(int)
for q in questions:
    area_counts[q["area"]] += 1

lines.append("export const generatedAreaCounts = {")
for area, count in sorted(area_counts.items()):
    lines.append(f"  '{area}': {count},")
lines.append("};")

# Export raw questions length
lines.append(f"export const generatedTotalQuestions = {len(questions)};")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

# ============================================================
# SLIM META FILE — para Dashboard (sem questionText/options)
# Reduz o bundle inicial em ~60%.
# ============================================================
meta_lines = [
    "// Auto-gerado: dados LEVES para o dashboard (sem texto das questoes).",
    "// O texto completo das questoes esta em generatedData.js (lazy).",
    "",
    "// Lista minima de questoes — apenas o que o dashboard precisa para",
    "// calcular subtopics/percentage/history/probability por topico.",
    "export const generatedQuestionsMeta = [",
]
for q in questions:
    meta_lines.append("  {")
    meta_lines.append(f"    id: '{q['id']}',")
    meta_lines.append(f"    topicId: '{q['topicId']}',")
    meta_lines.append(f"    subtopic: '{js_str(q['subtopic'])}',")
    meta_lines.append(f"    examRef: '{q['examRef']}',")
    meta_lines.append(f"    area: '{q['area']}',")
    meta_lines.append("  },")
meta_lines.append("];")
meta_lines.append("")
meta_lines.append("export const generatedSubtopicCounts = {")
for st, count in sorted(subtopic_counts.items(), key=lambda x: -x[1]):
    meta_lines.append(f"  '{js_str(st)}': {count},")
meta_lines.append("};")
meta_lines.append("")
meta_lines.append("export const generatedTopicCounts = {")
for tid, count in sorted(topic_counts.items()):
    meta_lines.append(f"  '{tid}': {count},")
meta_lines.append("};")
meta_lines.append("")
meta_lines.append("export const generatedAreaCounts = {")
for area, count in sorted(area_counts.items()):
    meta_lines.append(f"  '{area}': {count},")
meta_lines.append("};")
meta_lines.append("")
meta_lines.append(f"export const generatedTotalQuestions = {len(questions)};")

with open(META_OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(meta_lines))

print(f"Generated {OUTPUT} (full questions)")
print(f"Generated {META_OUTPUT} (slim metadata)")
print(f"Total questions: {len(questions)}")
print(f"Subtopics: {len(subtopic_counts)}")
