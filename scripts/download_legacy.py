"""Download all legacy Revalida exams (2011-2020) using URL patterns confirmed via probing.
Saves with the *new* naming convention so extract_classify.py picks them up:
  {year}_PV_objetiva_1.pdf  /  {year}_GB_objetiva_1.pdf
"""
import os
import ssl
import urllib.request
from pathlib import Path

PDF_DIR = Path(__file__).parent.parent / "data" / "pdfs"
PDF_DIR.mkdir(parents=True, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


# (year, kind, source_url, dest_filename)
# URLs confirmed via doctormedmac archive + direct probing on download.inep.gov.br.
DOWNLOADS = [
    # 2011
    ("2011", "PV", "https://download.inep.gov.br/educacao_superior/revalida/provas/2011/prova_objetiva_cinza.pdf",
        "2011_PV_objetiva_1.pdf"),
    ("2011", "GB", "https://download.inep.gov.br/educacao_superior/revalida/gabaritos/2011/inep_gabarito_definitivo_revalida-2011.pdf",
        "2011_GB_objetiva_1.pdf"),
    # 2012
    ("2012", "PV", "https://download.inep.gov.br/educacao_superior/revalida/provas/2012/prova_objetiva_cinza_2012.pdf",
        "2012_PV_objetiva_1.pdf"),
    ("2012", "GB", "https://download.inep.gov.br/educacao_superior/revalida/gabaritos/2012/revalida_2012_gabaritoProvacinza.pdf",
        "2012_GB_objetiva_1.pdf"),
    # 2013
    ("2013", "PV", "https://download.inep.gov.br/educacao_superior/revalida/provas/2013/po_cinza_revalida_2013.pdf",
        "2013_PV_objetiva_1.pdf"),
    ("2013", "GB", "https://download.inep.gov.br/educacao_superior/revalida/gabaritos/2013/po_cinza_gabarito_definitivo_revalida_2013.pdf",
        "2013_GB_objetiva_1.pdf"),
    # 2014
    ("2014", "PV", "https://download.inep.gov.br/educacao_superior/revalida/provas/2014/po_cinza_revalida_objetiva_2014.pdf",
        "2014_PV_objetiva_1.pdf"),
    ("2014", "GB", "https://download.inep.gov.br/educacao_superior/revalida/gabaritos/2014/gabarito_preliminar_prova_cinza_objetiva_20072014.pdf",
        "2014_GB_objetiva_1.pdf"),
    # 2015
    ("2015", "PV", "https://download.inep.gov.br/educacao_superior/revalida/provas/2015/prova_objetiva_cinza.pdf",
        "2015_PV_objetiva_1.pdf"),
    ("2015", "GB", "https://download.inep.gov.br/educacao_superior/revalida/gabaritos/2015/gabarito_definitivo_prova_cinza.pdf",
        "2015_GB_objetiva_1.pdf"),
    # 2016 (gabarito not yet found — exam still useful even without it)
    ("2016", "PV", "https://download.inep.gov.br/educacao_superior/revalida/provas/2016/prova_objetiva_1.pdf",
        "2016_PV_objetiva_1.pdf"),
    # 2017 (gabarito not yet found)
    ("2017", "PV", "https://download.inep.gov.br/educacao_superior/revalida/provas/2017/prova_objetiva_1.pdf",
        "2017_PV_objetiva_1.pdf"),
    # 2020 (gabarito not yet found at probed URLs)
    ("2020", "PV", "https://download.inep.gov.br/educacao_superior/revalida/provas/2020/revalida_obj_001_1.pdf",
        "2020_PV_objetiva_1.pdf"),
]


def download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  [skip] {dest.name} (already exists)")
        return True
    try:
        print(f"  [GET ] {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
            data = r.read()
        dest.write_bytes(data)
        print(f"         -> {dest.name} ({len(data)} bytes)")
        return True
    except Exception as e:
        print(f"  [FAIL] {url} -> {e}")
        return False


def main():
    ok = 0
    for year, kind, url, dest_name in DOWNLOADS:
        if download(url, PDF_DIR / dest_name):
            ok += 1
    print(f"\n{ok}/{len(DOWNLOADS)} downloads succeeded")


if __name__ == "__main__":
    main()
