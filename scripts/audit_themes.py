"""For each catch-all area, count how many questions match BROAD clinical themes
(by keyword presence). This tells us which subtopic rules to add or expand.
"""
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

DATA = Path(__file__).parent.parent / "data" / "extracted_questions.json"


def n(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


# Themes we SUSPECT exist in catch-all but lack rules. Each theme: list of broad keywords.
THEMES = {
    "Niveis de Prevencao (geral)": ["nivel de prevencao", "leavell", "prevencao primordial",
                                     "prevencao primaria", "prevencao secundaria", "prevencao terciaria",
                                     "prevencao quaternaria", "previne quaternaria", "promocao da saude"],
    "Rastreamento Doencas Cronicas (HAS/DM/Dislipidemia)": ["rastreamento diabetes", "glicemia jejum",
                                                              "hemoglobina glicada", "dislipidemia",
                                                              "perfil lipidico", "rastreamento hipertensao",
                                                              "check-up", "rastreio cardiovascular"],
    "Atencao Primaria / ESF / UBS": ["unidade basica", "ubs", "saude da familia", "esf",
                                       "agente comunitario", "acolhimento", "matriciamento",
                                       "apoio matricial", "visita domiciliar", "atencao primaria",
                                       "territorio", "adscricao", "clinica ampliada"],
    "Bioetica / etica medica": ["confidencialidade", "sigilo medico", "etica medica", "bioetica",
                                  "autonomia", "beneficencia", "nao maleficencia", "termo de consentimento",
                                  "testemunha de jeova", "objecao consciencia", "principio etico"],
    "Glomerulopatias / Hematuria": ["urina escura", "cor de coca", "hematuria macroscopica",
                                     "edema palpebral", "edema de face", "glomerulonefrite",
                                     "sindrome nefrotica", "sindrome nefritica", "hipertensao em crianca",
                                     "proteinuria nefrotica"],
    "ITU / Pielonefrite (geral)": ["disuria", "polaciuria", "urgencia urinaria", "infeccao urinaria",
                                     "pielonefrite", "cistite", "urinocultura"],
    "Sepse / Choque Septico": ["criterios de sepse", "sepse grave", "choque septico", "qsofa",
                                "lactato elevado", "infeccao com hipotensao", "sirs",
                                "sepsis", "criterios de sirs"],
    "Diabetes Gestacional": ["diabetes gestacional", "dmg", "tolerancia oral glicose gestacao",
                              "tolerancia glicose 75g", "glicemia gestacional"],
    "Vacina na Gestante / Imunizacao Materna": ["vacina na gestante", "vacinacao na gestacao",
                                                  "tdpa", "dtpa", "influenza gestante",
                                                  "vacina hepatite gestante"],
    "Anamnese / Semiologia": ["historia clinica", "exame fisico", "anamnese", "semiologia"],
    "Doencas Exantematicas / Erupcoes": ["sarampo", "rubeola", "varicela", "catapora", "escarlatina",
                                          "exantema", "kawasaki", "doenca mao-pe-boca", "eritema infeccioso",
                                          "5a doenca"],
    "Otite / IVAS Pediatricas": ["otite media aguda", "otite", "secrecao nasal", "obstrucao nasal",
                                   "rinite", "sinusite", "amigdalite", "faringoamigdalite"],
    "Traumas / Acidentes em Crianca": ["queda do berco", "queda crianca", "queimadura crianca",
                                         "engasgo crianca", "acidente domestico crianca",
                                         "trauma cranio crianca", "intoxicacao crianca"],
    "Maus-tratos / Violencia / ECA": ["violencia", "abuso", "maus-tratos", "negligencia infantil",
                                       "estatuto crianca", "eca", "conselho tutelar",
                                       "violencia domestica", "agressao"],
    "Imunoprevenivel / Surto": ["surto", "epidemia", "transmissao respiratoria",
                                  "investigacao epidemiologica", "curva epidemica",
                                  "fonte de infeccao", "isolamento de contato"],
    "Adolescente / Saude do Jovem": ["adolescente", "menarca tardia", "puberdade", "tanner",
                                       "saude adolescente", "anticoncepcao adolescente"],
    "Anemia Pediatrica / Ferropriva": ["anemia ferropriva", "ferro elementar", "lactente palido",
                                         "alimentacao deficiente", "leite materno excl"],
    "Gestacao Alto Risco": ["alto risco gestacional", "gestacao de alto risco", "doenca cardiaca gestante",
                              "diabetes pre-gestacional", "lupus na gestacao"],
    "Crescimento / Ganho Ponderal": ["ganho ponderal", "perda peso", "deficit estatura",
                                       "baixa estatura", "magreza", "desnutricao infantil",
                                       "obesidade infantil", "imc crianca"],
    "Pneumonia Pediatrica": ["pneumonia em crianca", "pneumonia infantil", "tosse e febre crianca",
                               "consolidacao pulmonar crianca"],
    "Asma / Sibilancia Crianca": ["sibilo crianca", "sibilancia", "asma em crianca"],
    "Bem-Estar Fetal / Cardiotocografia": ["cardiotocograf", "movimentos fetais", "perfil biofisico fetal",
                                             "doppler fetal"],
    "Enxaqueca / Cefaleia": ["enxaqueca", "cefaleia tensional", "cefaleia primaria", "cefaleia em salvas"],
    "Câncer (mama, próstata, colorretal — não rastreio)": ["nodulo mama suspeito", "ca de mama",
                                                              "tumor renal", "cancer de prostata avancado",
                                                              "cancer de pulmao avancado", "neoplasia avancada"],
    "Doenca Inflamatoria Pelvica (DIP)": ["doenca inflamatoria pelvica", "dip", "salpingite",
                                            "abscesso tubario"],
    "Vulvovaginites (geral)": ["candidiase vaginal", "vaginose bacteriana", "tricomoniase",
                                 "corrimento amarelado", "corrimento branco grumoso"],
    "Aleitamento materno (manejo)": ["fissura mamilar", "ingurgitamento mamario", "mastite",
                                       "tecnica de pega", "ordenha"],
}


def main():
    questions = json.load(open(DATA, encoding="utf-8"))
    catch = [q for q in questions if "Outros Temas" in q["subtopic"]]

    by_area = defaultdict(list)
    for q in catch:
        by_area[q["area"]].append(q)

    for area, items in sorted(by_area.items()):
        print(f"\n{'=' * 70}")
        print(f"  {area}: {len(items)} catch-all (total in pool, may overlap themes below)")
        print(f"{'=' * 70}")

        theme_hits = []
        for theme, kws in THEMES.items():
            hits = [q for q in items if any(n(kw) in n(q["questionText"]) for kw in kws)]
            if hits:
                theme_hits.append((theme, len(hits), hits))

        for theme, count, _ in sorted(theme_hits, key=lambda x: -x[1])[:15]:
            print(f"  [{count:>3}] {theme}")


if __name__ == "__main__":
    main()
