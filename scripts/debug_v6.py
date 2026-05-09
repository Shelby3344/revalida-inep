"""Debug: show full Q1 block for 2015 and 2021."""
import pdfplumber, unicodedata, re
from pathlib import Path

BASE = Path(__file__).parent.parent

def norm(s):
    if not s: return ''
    return unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode().lower()

for label, fpath in [
    ("2015", BASE/"Provas do revalida PDF/revalida provas/2015/caderno cinza/prova_objetiva_cinza.pdf"),
    ("2021", BASE/"Provas do revalida PDF/revalida provas/2021/Prova Objetiva 01/2021_PV_objetiva_1.pdf"),
]:
    print(f"\n{'='*60}\nPDF: {label}\n{'='*60}")
    pages_raw = []
    with pdfplumber.open(fpath) as pdf:
        for page in pdf.pages:
            w, h = page.width, page.height
            l = page.crop((0,0,w*0.5,h)).extract_text() or ''
            r = page.crop((w*0.5,0,w,h)).extract_text() or ''
            combined = l + '\n' + r if (l.strip() and r.strip()) else (page.extract_text() or '')
            pages_raw.append(combined)
    raw = '\n'.join(pages_raw)

    raw_markers = {}
    for m in re.finditer(r'QUEST[^\d\n]{0,10}(\d{1,3})\b', raw, re.IGNORECASE):
        q_num = int(m.group(1))
        if 1 <= q_num <= 120 and q_num not in raw_markers:
            raw_markers[q_num] = m.start()
    for m in re.finditer(r'\b(\d{1,3})\s+QUEST[^\s\d]{0,10}\b', raw, re.IGNORECASE):
        q_num = int(m.group(1))
        if 1 <= q_num <= 120 and q_num not in raw_markers:
            raw_markers[q_num] = m.start()

    pos_sorted = sorted((pos, q) for q, pos in raw_markers.items())
    pos1, q1 = pos_sorted[0]
    pos2 = pos_sorted[1][0] if len(pos_sorted) > 1 else pos1+2000
    blk = raw[pos1:pos2]
    lines = [l.strip() for l in blk.splitlines() if l.strip()]
    lines = [l for l in lines if not re.match(r'QUEST', l, re.I) and not re.match(r'^\d+\s+QUEST', l, re.I) and not re.match(r'^\d+\.\s+ITEM', l, re.I)]

    opt_re = re.compile(r'^([A-E])\s*[\)\. ](.*)$')
    print(f"Q{q1} — {len(lines)} lines total:")
    for i, l in enumerate(lines):
        m = opt_re.match(l)
        tag = f"[OPT {m.group(1)}]" if m else "[txt]"
        print(f"  {i:2d} {tag} {repr(l[:80])}")
