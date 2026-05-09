"""Download all Revalida INEP objective exam PDFs and answer keys."""
import os, urllib.request, time, sys

BASE = "https://download.inep.gov.br/revalida/provas_e_gabaritos"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs")
os.makedirs(OUT, exist_ok=True)

# Mapeamento de todas as edições conhecidas
EDITIONS = [
    # Anos iniciais (2011-2017) - formato pode variar
    ("2011", None),
    ("2012", None),
    ("2013", None),
    ("2014", None),
    ("2015", None),
    ("2016", None),
    ("2017", None),
    # A partir de 2020: semestral
    ("2020", "1"), ("2020", "2"),
    ("2021", "1"), ("2021", "2"),
    ("2022", "1"), ("2022", "2"),
    ("2023", "1"), ("2023", "2"),
    ("2024", "1"), ("2024", "2"),
    ("2025", "1"), ("2025", "2"),
]

def download(url, filename):
    path = os.path.join(OUT, filename)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        print(f"  [skip] {filename}")
        return True
    try:
        print(f"  [down] {filename} ...", end=" ")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        with open(path, "wb") as f:
            f.write(data)
        print(f"OK ({len(data)} bytes)")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        return False

def try_patterns(year, sem):
    """Try multiple filename patterns for older exams."""
    patterns = []
    suffix = f"_{sem}" if sem else ""

    # Padrão moderno: YEAR_SEM_PV_objetiva_regular.pdf
    if sem:
        patterns.append(f"{year}{suffix}_PV_objetiva_regular.pdf")
        patterns.append(f"{year}{suffix}_GB_objetiva.pdf")
        patterns.append(f"{year}{suffix}_GB_objetiva_definitivo.pdf")
    else:
        patterns.append(f"{year}_PV_objetiva_regular.pdf")
        patterns.append(f"{year}_GB_objetiva.pdf")
        # Padrão antigo alternativo
        patterns.append(f"revalida_{year}_objetiva.pdf")
        patterns.append(f"revalida_{year}_gabarito.pdf")
        patterns.append(f"{year}_prova_objetiva.pdf")
        patterns.append(f"{year}_gabarito_objetiva.pdf")

    for pattern in patterns:
        url = f"{BASE}/{pattern}"
        download(url, pattern)

def main():
    total = 0
    for year, sem in EDITIONS:
        print(f"\n[{year}{'_' + sem if sem else ''}]")
        try_patterns(year, sem)
        total += 1
        time.sleep(0.3)  # Respeitar o servidor

    # Listar o que foi baixado
    files = sorted(os.listdir(OUT))
    print(f"\n\nTotal de arquivos em {OUT}: {len(files)}")
    for f in files:
        size = os.path.getsize(os.path.join(OUT, f))
        print(f"  {f:50s} {size:>8d} bytes")

if __name__ == "__main__":
    main()
