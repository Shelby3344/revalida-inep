"""
Revalida INEP — Pipeline v6
Arquitetura: grande_area → tema_principal → subtopico
Regra: ZERO catch-all. Toda questão recebe especialidade médica real.
Saídas: data/questoes_db.json  +  data/estatisticas_temas.json
"""
import json, re, unicodedata
from pathlib import Path
from collections import defaultdict, Counter
try:
    import pdfplumber
except ImportError:
    raise SystemExit("pip install pdfplumber")

BASE     = Path(__file__).parent.parent
PDF_NEW  = BASE / "Provas do revalida PDF" / "revalida provas"
PDF_OLD  = BASE / "data" / "pdfs"
OUT_DB   = BASE / "data" / "questoes_db.json"
OUT_STAT = BASE / "data" / "estatisticas_temas.json"
GAB_MAN  = BASE / "data" / "gabaritos_manuais.json"

# Load manual/OCR gabaritos override
_manual_gabaritos = {}
if GAB_MAN.exists():
    with open(GAB_MAN, encoding="utf-8") as _f:
        _raw = json.load(_f)
    for _ed, _ans in _raw.items():
        _manual_gabaritos[_ed] = {int(k): v for k, v in _ans.items() if v}
    print(f"[GAB_MAN] Carregado: {list(_manual_gabaritos.keys())}")

# ─────────────────────────────────────────────────────────────
# EXAM REGISTRY
# ─────────────────────────────────────────────────────────────
def _e(year, edition, prova_rel, gabarito_rel=None, old=False):
    base = PDF_OLD if old else PDF_NEW
    return {
        "year": year, "edition": edition,
        "prova":    (base / prova_rel)    if prova_rel    else None,
        "gabarito": (base / gabarito_rel) if gabarito_rel else None,
    }

EXAMS = [
    _e(2011,"2011","2011/prova_objetiva_cinza.pdf","2011/inep_gabarito_definitivo_revalida-2011.pdf"),
    _e(2012,"2012","2012/prova_objetiva_cinza_2012.pdf","2012/revalida_2012_gabaritoProvacinza.pdf"),
    _e(2013,"2013","2013/caderno cinza/po_cinza_revalida_2013.pdf","2013/caderno cinza/po_cinza_gabarito_definitivo_revalida_2013.pdf"),
    _e(2014,"2014","2014/caderno cinza/po_cinza_revalida_objetiva_2014.pdf","2014/caderno cinza/gabarito_preliminar_prova_cinza_objetiva_20072014.pdf"),
    _e(2015,"2015","2015/caderno cinza/prova_objetiva_cinza.pdf","2015/caderno cinza/gabarito_definitivo_prova_cinza.pdf"),
    _e(2016,"2016-1","2016/Prova objetiva 01/prova_objetiva_1.pdf","2016/Prova objetiva 01/gabarito_definitivo_prova_objetiva_v1.pdf"),
    _e(2016,"2016-2","2016/Prova Objetiva 02/prova_objetiva_2.pdf","2016/Prova Objetiva 02/gabarito_definitivo_prova_objetiva_v2.pdf"),
    _e(2017,"2017","2017_PV_objetiva_1.pdf", None, old=True),
    _e(2020,"2020-1","2020/Prova Objetiva 01/revalida_obj_001_1.pdf","2020/Prova Objetiva 01/gabarito_caderno_1.pdf"),
    _e(2020,"2020-2","2020/Prova Objetiva 02/revalida_obj_001_2.pdf","2020/Prova Objetiva 02/gabarito_caderno_2.pdf"),
    _e(2021,"2021","2021/Prova Objetiva 01/2021_PV_objetiva_1.pdf","2021/Prova Objetiva 01/2021_GB_objetiva_1.pdf"),
    _e(2022,"2022-1","2022/Prova Objetiva 03 - 2022-1/2022_PV_objetiva_1.pdf","2022/Prova Objetiva 03 - 2022-1/2022_GB_objetiva_1.pdf"),
    _e(2022,"2022-2","2022/Prova Objetiva 01-2022 - 2/2022-2_PV_objetiva.pdf","2022/Prova Objetiva 01-2022 - 2/2022-2_GB_objetiva.pdf"),
    _e(2023,"2023-1","2023/Prova Objetiva 02/2023_1_PV_objetiva_regular.pdf","2023/Prova Objetiva 02/2023_1_GB_objetiva_definitivo.pdf"),
    _e(2023,"2023-2","2023/Prova Objetiva 01/2023_2_PV_objetiva_regular.pdf","2023/Prova Objetiva 01/2023_2_GB_objetiva.pdf"),
    _e(2024,"2024-1","2024/Prova Objetiva 02/2024_1_PV_objetiva_regular.pdf","2024/Prova Objetiva 02/2024_1_GB_objetiva.pdf"),
    _e(2024,"2024-2","2024/Prova Objetiva 01/2024_2_PV_objetiva_regular.pdf","2024/Prova Objetiva 01/2024_2_GB_objetiva.pdf"),
    _e(2025,"2025-1","2025/Prova Objetiva 01/2025_1_PV_objetiva_regular.pdf","2025/Prova Objetiva 01/2025_1_GB_objetiva_definitivo.pdf"),
]

# ─────────────────────────────────────────────────────────────
# NORMALIZATION
# ─────────────────────────────────────────────────────────────
def norm(s):
    if not s: return ""
    return unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower()

# ─────────────────────────────────────────────────────────────
# CLASSIFICATION RULES  (grande_area → tema_principal → subtopico)
# default_tema  : used when no tema keyword scores > 0
# default_sub   : used when no subtopic keyword scores > 0
# ─────────────────────────────────────────────────────────────
C = {

# ══════════════════════════════════════════════════════════════
"Clínica Médica": {
  "area_kw": [
    "clinica medica","clinico geral","internacao clinica","enfermaria clinica",
    "medicina interna","paciente adulto internado","seguimento ambulatorial",
  ],
  "default_tema": "Cardiologia",
  "temas": {

    "Cardiologia": {
      "kw": [
        "infarto","iam","sca","angina","coronari","stent","cateterismo","angioplastia",
        "ecg","eletrocardiograma","insuficiencia cardiaca","icc","ic sistolica","ic diastolica",
        "fibrilacao atrial","flutter atrial","taquicardia ventricular","fibrilacao ventricular",
        "arritmia","mark passo","marcapasso","cardioversao","desfibrilacao",
        "valvulopatia","estenose aortica","insuficiencia mitral","insuficiencia aortica",
        "estenose mitral","prolapso mitral","endocardite","pericardite","miocardite",
        "miocardiopatia","cardiomiopatia","cardiomegalia","bloc atriov","bloc ramo",
        "hipertensao arterial","has ","crise hipertensiva","emergencia hipertensiva",
        "urgencia hipertensiva","pressao arterial","amlodipina","enalapril","losartana",
        "captopril","verapamil","amiodarona","digoxina","betabloqueador",
        "febre reumatica","cardite","sopro cardiaco","b3 ","b4 ","tep cardiaco",
        "tamponamento cardiaco","dissecao aorta","aneurisma aorta abdomi",
        "sindrome coronariana","troponina","ck-mb","bnp","nt-probnp",
      ],
      "default_sub": "Diagnóstico e Conduta Cardiológica",
      "subtopicos": {
        "IAM e Síndromes Coronarianas Agudas": [
          "infarto agudo","infarto do miocardio","iam","sca","angina instavel",
          "dor toracica aguda","dor precordial","dor opressiva","dor retroesternal",
          "sindrome coronariana aguda","sindrome coronariana",
          "troponina","ck-mb","supradesnivelamento","infradesnivelamento",
          "supra de st","infra de st","onda q patologica","supra st","infra st",
          "stent","angioplastia","trombolitico","alteplase","estreptoquinase",
          "coronarografia","revascularizacao miocardica","cirurgia de ponte",
          "trombolise","angiografia coronaria","cateterismo cardiaco",
        ],
        "Insuficiência Cardíaca": [
          "insuficiencia cardiaca","icc","ic sistolica","ic diastolica",
          "feve reduzida","feve preservada","fracao ejecao","classe nyha",
          "edema agudo pulmao","edema pulmonar agudo","descompensacao cardiaca",
          "bnp","nt-probnp","furosemida","espironolactona","sacubitril",
          "cardiomegalia","congestao pulmonar","orthopneia","dispneia paroxistica",
          "turgencia jugular","hepatomegalia congestiva","b3 cardiaco",
        ],
        "Arritmias e Distúrbios de Condução": [
          "fibrilacao atrial","flutter atrial","taquicardia supraventricular","tsv",
          "taquicardia ventricular","fibrilacao ventricular","bradiarrit",
          "bloc atrioventricular","bloc ramo","sinusal","marcapasso",
          "cardioversao","desfibrilador","ablacao","amiodarona","adenosina",
          "palpitacao cardiaca","sincope cardiaca","presincope cardiaca",
          "extrassistole","wolff-parkinson-white","wpw","qt longo","qt prolongado",
          "bradicardia sinusal","taquicardia sinusal patologica",
        ],
        "Hipertensão Arterial Sistêmica": [
          "hipertensao arterial sistemica","crise hipertensiva",
          "emergencia hipertensiva","urgencia hipertensiva",
          "hipertensao resistente","hipertensao estagio","has estagio",
          "alvo pressorio","meta pressao arterial","controle pressao arterial",
          "monitoracao ambulatorial pressao","mapa has","mrpa",
          "lesao de orgao alvo has","retinopatia hipertensiva",
          "hipertrofia ventricular esquerda","nefropatia hipertensiva",
        ],
        "Valvulopatias e Endocardite": [
          "valvulopatia","estenose aortica","insuficiencia mitral","estenose mitral",
          "insuficiencia aortica","prolapso mitral","endocardite","duke",
          "vegetacao","sopro card","febre reumatica","cardite reumatica",
        ],
      },
    },

    "Infectologia": {
      "kw": [
        "hiv","aids","tuberculose","tbc","bacilo koch","baar","isoniazida","rifampicina",
        "malaria","plasmodium","cloroquina","dengue","zika","chikungunya","arbovirus",
        "leishmaniose","calazar","doenca de chagas","tripanossoma","leptospirose",
        "meningite bacteriana","encefalite","meningococo","pneumococo meningite",
        "hansenase","lepra","paucibacilar","multibacilar","dapsona","rifamp hansen",
        "toxoplasmose adulto","pneumocistose","pcp","criptococose","histoplasmose",
        "antirretroviral","tarv","inibidor protease","inibidor integ",
        "sifilis adulto","treponema","sifilis primaria","sifilis secundaria",
        "sifilis terciaria","penicilina benzatina sifilis",
        "hepatite a aguda","hepatite b aguda","hepatite c","sorol infec",
        "bacteremia","fungemia","sepse","choque septico","qsofa","sofa sepse",
        "antibiotico","beta-lactamico","cefalosporina","quinolona",
        "meropenem","vancomicina","oxacilina","infectologia",
        "osteomielite","artrite septica adulto",
        "influenza","covid","sars","pneumonia viral",
      ],
      "default_sub": "Infecção Bacteriana e Antibioticoterapia",
      "subtopicos": {
        "HIV/AIDS e Doenças Oportunistas": [
          "hiv","aids","cd4","carga viral","antirretroviral","tarv",
          "pneumocistose","pcp","toxoplasmose cerebral","criptococose",
          "tuberculose hiv","mycobacterium hiv","kaposi","linfoma aids",
          "profilaxia hiv","prep","pep","transmissao sexual hiv",
        ],
        "Tuberculose": [
          "tuberculose","tbc","mycobacterium tuberculosis","baar","baciloscopia",
          "cultura de escarro","rifampicina","isoniazida","pirazinamida","etambutol",
          "esquema rhze","teste tuberculinico","ppd","igra","tuberculose latente",
          "tuberculose miliar","tuberculos pulmonar","tuberculose extrapulmonar",
        ],
        "Dengue, Zika e Arboviroses": [
          "dengue","zika","chikungunya","arbovirus","aedes aegypti",
          "dengue grave","dengue com sinais de alarme","choque dengue",
          "trombocitopenia dengue","ns1","sorologia dengue",
        ],
        "Sepse e Infecções Graves": [
          "sepse","choque septico","qsofa","sofa score","bacteremia","fungemia",
          "foco infeccioso","antibioticoterapia empirica","hemocult",
          "lactat","disfuncao organica","terapia intensiva infec",
          "neutropenia febril","febre em imunossuprimido",
        ],
        "Doenças Tropicais e Parasitoses": [
          "malaria","plasmodium","cloroquina","artesunato","leishmaniose",
          "calazar","doenca de chagas","tripanossoma","leptospirose",
          "hansenase","lepra","dapsona","esquistossomose","filariose",
        ],
        "Hepatites Virais": [
          "hepatite a","hepatite b","hepatite c","hbsag","anti-hbs","anti-hbc",
          "anti-hcv","carga viral hepatite","soroconversao hep",
          "hepatite b cronica","tenofovir hepatite","interferon",
          "hepatite fulminante","hepatite viral aguda",
        ],
        "Meningite e Encefalite": [
          "meningite","encefalite","meningococo","pneumococo meningite",
          "haemophilus","dexametasona meningite","punca lombar","lcr",
          "ceftriaxona meningite","quimioprofilaxia meningite",
          "meningite tuberculosa","herpes encefalite","aciclovir encefalite",
        ],
        "Infecção Bacteriana e Antibioticoterapia": [
          "antibiotico","beta-lactamico","cefalosporina","aminoglicosideo",
          "quinolona","macrolideo","meropenem","vancomicina","linezolida",
          "osteomielite","artrite septica","celulite infecciosa",
          "erisipela","fasciite necrotizante","abscesso",
        ],
      },
    },

    "Gastroenterologia": {
      "kw": [
        "doenca de crohn","colite ulcerativa","dii","retocolite ulcerativa",
        "ulcera peptica","gastrite","helicobacter pylori","dispepsia",
        "sindrome do intestino irritavel","sii","constipacao cronica",
        "diarreia cronica adulto","doenca diverticular","isquemia mesenterica",
        "esofago de barrett","esofagite","refluxo gastroesofagico","drge","gerd",
        "acalasia","disfagia","pancreatite cronica","colonoscopia",
        "endoscopia digestiva","eda","cancer gastrico","adenocarcinoma gastrico",
        "cancer colorretal","polipose","hemorragia digestiva alta","hda",
        "hemorragia digestiva baixa","hdb","sangramento gastrointe",
        "gastroenterologia","h. pylori","h.pylori",
      ],
      "default_sub": "Diagnóstico e Tratamento Gastroenterológico",
      "subtopicos": {
        "Doença Inflamatória Intestinal (Crohn / RCU)": [
          "doenca de crohn","colite ulcerativa","retocolite ulcerativa","dii",
          "mesalazina","azatioprina","infliximabe","biologico intestinal",
          "colonoscopia crohn","estenose intestinal crohn",
          "fistula de crohn","abscesso crohn","megacolon toxico",
        ],
        "Úlcera Péptica e DRGE": [
          "ulcera peptica","ulcera gastrica","ulcera duodenal","gastrite",
          "helicobacter pylori","h. pylori","omeprazol","pantoprazol","ibb",
          "erradicacao hp","refluxo gastroesofagico","drge","esofagite",
          "esofago de barrett","acalasia","disfagia",
        ],
        "Hemorragia Digestiva": [
          "hemorragia digestiva alta","hemorragia digestiva baixa","hemorragia digestiva",
          "hda","hdb","melena","hematoquecia","hematemese","sangramento digestivo",
          "sangramento gastrointestinal","hemorragia gastrointestinal",
          "varizes esofagicas sangrantes","ligadura elastica","band liga",
          "ulcera sangrante","endoscopia terapeutica","escleroterapia",
          "angiodisplasia sangramento","diverticulo sangramento","sangramento retal",
        ],
        "Pancreatite e Doenças Pancreáticas": [
          "pancreatite aguda","pancreatite cronica","pancreatite",
          "lipase elevada","amilase elevada","lipase pancreatica","amilase serica",
          "balthazar","ranson","necrose pancreatica","pseudocisto pancreatico",
          "pancreatite por colelitiase","pancreatite alcoolica",
          "epigastralgia irradiando","dor epigastrica irradiando dorso",
          "cancer de pancreas","ca pancreas","insuficiencia pancreatica","esteatorreia",
        ],
        "Câncer Gastrointestinal": [
          "cancer gastrico","adenocarcinoma gastrico","cancer colorretal",
          "carcinoma colorretal","polipose adenomatosa","lynch",
          "rastreamento colonoscopia","cirurgia cancer gastrico","gastrectomia oncologica",
        ],
      },
    },

    "Hepatologia": {
      "kw": [
        "cirrose","cirrose hepatica","hepatite cronica","hepatite b cronica",
        "hepatite c cronica","carcinoma hepatocelular","chc","hepatocarcinoma",
        "hipertensao portal","varizes esofagicas","sangramento varicoso",
        "ascite","paracentese","peritonite bacteriana espontanea","pbe",
        "encefalopatia hepatica","lactulose","rifaximina",
        "insuficiencia hepatica","child-pugh","meld","transplante hepatico",
        "sindrome hepatorrenal","sindrome hepatopulmonar",
        "esteatohepatite","nash","nafld","esteatose hepatica",
        "hepatite alcoolica","hepatite autoimune","colangite biliar primaria",
        "colangite esclerosante","fibrose hepatica",
        "esplenomegalia","trombose veia porta",
      ],
      "default_sub": "Cirrose e Hipertensão Portal",
      "subtopicos": {
        "Cirrose e Hipertensão Portal": [
          "cirrose","hipertensao portal","varizes esofagicas","esplenomegalia",
          "child-pugh","meld","cirrose descompensada","cirrose compensada",
          "trombose veia porta","hiperesplenismo",
        ],
        "Ascite e Peritonite Bacteriana Espontânea": [
          "ascite","paracentese","peritonite bacteriana espontanea","pbe",
          "proteina ascite","gradiente albumina","restricao sodio",
          "diuretico ascite","terlipressina","tips",
        ],
        "Encefalopatia Hepática e Insuficiência Hepática": [
          "encefalopatia hepatica","lactulose","rifaximina","asterixe",
          "insuficiencia hepatica aguda","fulminante hepatico",
          "transplante de figado","ictericia hepatica",
        ],
        "Carcinoma Hepatocelular e Rastreamento": [
          "carcinoma hepatocelular","chc","hepatocarcinoma","afp",
          "ultrassom semestral","ablacao hepatica","embolizacao",
          "sorafenibe","transplante oncologico hepatico",
        ],
        "Hepatite Crônica e Esteatohepatite": [
          "hepatite b cronica","hepatite c cronica","tenofovir","sofosbuvir",
          "daclatasvir","tratamento hepatite c","tratamento hepatite b",
          "esteatohepatite","nash","nafld","esteatose hepatica",
          "hepatite alcoolica","hepatite autoimune",
        ],
      },
    },

    "Endocrinologia": {
      "kw": [
        "diabetes tipo 1","diabetes tipo 2","dm1","dm2","dm ","diabetes mellitus",
        "cetoacidose diabetica","cad","estado hiperosmolar","insulina",
        "glicemia","hemoglobina glicada","hba1c","a1c",
        "hipoglicemia","metformina","sulfonilureia","glibenclamida","glipizida",
        "inibidor sglt2","empagliflozina","dapagliflozina","glp1","liraglutida",
        "hipotireoidismo","hipertireoidismo","bócio","tireoidite hashimoto",
        "tireoidite de quervain","tireotoxicose","tempestade tireoidiana",
        "nodulo tireoide","cancer de tireoide","tireoidectomia",
        "tsh","t3","t4","levotiroxina","propiltiouracila","metimazol",
        "sindrome de cushing","hipercortisolismo","cortisol",
        "insuficiencia adrenal","addison","crise adrenal",
        "feocromocitoma","hiperaldosteronismo","conn",
        "hiperparatireoidismo","hipocalcemia","hipercalcemia",
        "osteoporose","densitometria","bifosfonato","denosumabe",
        "dislipidemia","colesterol","triglicerides","estatina",
        "sindrome metabolica","obesidade morbida","cirurgia bariatrica",
        "acromegalia","prolactinoma","hipopituitarismo",
      ],
      "default_sub": "Diabetes Mellitus e Controle Glicêmico",
      "subtopicos": {
        "Diabetes Mellitus e Controle Glicêmico": [
          "diabetes tipo 2","dm2","diabetes tipo 1","dm1","diabetes mellitus",
          "hemoglobina glicada","hba1c","glicemia em jejum","glicemia pos-prandial",
          "insulina","metformina","sulfonilureia","inibidor sglt2","glp1",
          "metas glicemicas","complicacao diabetica","pe diabetico",
          "retinopatia diabetica","nefropatia diabetica","neuropatia diabetica",
        ],
        "Emergências Metabólicas (CAD e EHH)": [
          "cetoacidose diabetica","cad","estado hiperosmolar","ehh",
          "hipoglicemia grave","insulina regular cad","bicarbonato cad",
          "reposicao eletrolitos cad",
        ],
        "Hipotireoidismo e Hipertireoidismo": [
          "hipotireoidismo","levotiroxina","tsh elevado","t4 livre baixo",
          "hipertireoidismo","tireotoxicose","propiltiouracila","metimazol",
          "tempestade tireoidiana","bócio","tireoidite hashimoto",
          "doenca de graves","oftalmopatia graves","nodulo tireoide",
          "cancer de tireoide","tireoidectomia",
        ],
        "Insuficiência Adrenal e Síndrome de Cushing": [
          "insuficiencia adrenal","doenca de addison","crise adrenal",
          "cortisol","acth","hidrocortisona","fludrocortisona",
          "sindrome de cushing","hipercortisolismo","supressao dexametasona",
          "feocromocitoma","hiperaldosteronismo","sindrome de conn",
        ],
        "Osteoporose e Distúrbios do Cálcio": [
          "osteoporose","densitometria ossea","fratura osteoporotica",
          "bifosfonato","alendronato","denosumabe","ranelato de estroncio",
          "hiperparatireoidismo","hipercalcemia","hipocalcemia","vitamina d",
        ],
        "Dislipidemia e Obesidade": [
          "dislipidemia","colesterol total","ldl","hdl","triglicerides",
          "estatina","ezetimiba","fibratos","sindrome metabolica",
          "obesidade morbida","cirurgia bariatrica","imc",
        ],
      },
    },

    "Nefrologia": {
      "kw": [
        "insuficiencia renal aguda","ira","lesao renal aguda","lra","aki",
        "insuficiencia renal cronica","irc","drc","ckd","taxa de filtrac glomerular",
        "tfg","creatinina elevada","ureia elevada","hiperazotemia",
        "hemodialise","dialise peritoneal","transplante renal",
        "sindrome nefrotica","sindrome nefritica","glomerulonefrite",
        "proteinuria","hematuria","cilindros urinarios",
        "hiperkalemia","hipercalemia","hiponatremia","hipernatremia",
        "hipocalemia","hipokalemia","disturbio acido-base","acidose metabolica",
        "alcalose metabolica","acidose respiratoria","alcalose respiratoria",
        "itu alta","pielonefrite","litiase renal","calculo renal",
        "nefropatia diabetica","nefropatia hipertensiva",
        "rim poliquistico","poliquistose renal",
      ],
      "default_sub": "Insuficiência Renal e Distúrbios Hidroeletrolíticos",
      "subtopicos": {
        "Lesão Renal Aguda (LRA)": [
          "lesao renal aguda","lra","insuficiencia renal aguda","ira",
          "necrose tubular aguda","nta","prerenal","intrinseca renal",
          "posrenal","creatinina aguda","oliguria","anuria",
          "nefrotoxicidade","contraste iodado renal",
        ],
        "Doença Renal Crônica (DRC) e Diálise": [
          "doenca renal cronica","drc","irc","tfg","filtrado glomerular",
          "estadio ckd","hemodialise","dialise peritoneal","transplante renal",
          "fistula arteriov renal","cateter dialitico",
          "anemia da drc","eritropoetina","quelante fosforo",
        ],
        "Síndromes Glomerulares": [
          "sindrome nefrotica","sindrome nefritica","glomerulonefrite",
          "proteinuria nefrotica","hipoalbuminemia renal","edema nefrotico",
          "hematuria glomerular","iga nefropatia","lupus nefrite",
          "gnda","gnrp","membranosa","focal segmentar",
        ],
        "Distúrbios Hidroeletrolíticos e Ácido-Base": [
          "hiperkalemia","hipercalemia","hiponatremia","hipernatremia",
          "hipocalemia","hipokalemia","hipermagnesemia",
          "acidose metabolica","alcalose metabolica",
          "acidose respiratoria","alcalose respiratoria",
          "disturbio misto","compensacao respiratoria","gap anion",
        ],
        "ITU e Litíase Renal": [
          "infeccao urinaria","itu","pielonefrite","cistite",
          "uretrite bacteriana","nitrituria","leucocituria",
          "calculo renal","litiase","nefrolitiase","urolitiase",
          "colica renal","litotripsia","nefrolitotomia",
        ],
      },
    },

    "Neurologia": {
      "kw": [
        "avc","acidente vascular cerebral","avc isquemico","avc hemorragico",
        "stroke","trombose cerebral","embolia cerebral","tia",
        "trombolise","alteplase avc","trombectomia",
        "parkinson","doenca de parkinson","levodopa","dopaminergico",
        "alzheimer","demencia","ccm","dct","meem","demencia vascular",
        "epilepsia","crise epileptica","convulsao","status epileptico",
        "anticonvulsivante","fenitoina","carbamazepina","valproato","levetiracetam",
        "cefaleia","enxaqueca","cefaleia tensional","cluster","trigeminea",
        "sumatriptano","triptano","profilaxia enxaqueca",
        "meningite adulto","encefalite adulto","herpes cerebral",
        "guillain-barre","polineuropatia","neuropatia periferica",
        "miastenia gravis","anticorpo anti-acr","piridostigmina",
        "esclerose multipla","interferon neurologico","natalizumabe",
        "hematoma subdural","hematoma epidural","hemorragia subaracnoide",
        "hsas","aneurisma cerebral","acidente vascular encefal",
        "hipertensao intracraniana","edema cerebral",
      ],
      "default_sub": "AVC e Doenças Cerebrovasculares",
      "subtopicos": {
        "AVC e Doenças Cerebrovasculares": [
          "avc","acidente vascular cerebral","stroke","avc isquemico",
          "avc hemorragico","tia","trombolise","alteplase","trombectomia",
          "nihss","escore alberta","tc cerebro","rm cerebro avc",
          "hemorragia subaracnoide","hsas","aneurisma cerebral",
          "anticoagulacao avc","antiagregacao",
        ],
        "Epilepsia e Crises Convulsivas": [
          "epilepsia","crise epileptica","convulsao","status epileptico",
          "anticonvulsivante","fenitoina","carbamazepina","valproato",
          "levetiracetam","lamotrigina","crise febril","eletroencefalograma","eeg",
        ],
        "Cefaleia e Dor Neuropática": [
          "cefaleia","enxaqueca","migrânea","cefaleia tensional","cluster",
          "cefaleia trigeminoautonômica","sumatriptano","triptano",
          "profilaxia enxaqueca","topiramate neurologico","amitriptilina neuro",
        ],
        "Doenças Neurodegenerativas": [
          "parkinson","levodopa","dopaminergico","alzheimer",
          "demencia","meem","mini-mental","ccm","dct","atrofia multissist",
          "esclerose lateral amiotrofica","ela","huntington",
        ],
        "Doenças Desmielinizantes e Neuromusculares": [
          "esclerose multipla","interferon neurologico","natalizumabe",
          "guillain-barre","imunoglobulina neurologica","plasmaferese neuro",
          "miastenia gravis","anticolinesterasico","piridostigmina",
          "polineuropatia","neuropatia periferica","emg","velocidade conducao",
        ],
      },
    },

    "Pneumologia": {
      "kw": [
        "dpoc","doenca pulmonar obstrutiva","enfisema pulmonar","bronquite cronica",
        "asma bronquica adulto","crise asmatica","beta2 agonista adulto",
        "embolia pulmonar","tep","tromboembolismo pulmonar","dvt","tvp",
        "pneumonia adquirida comunidade","pac","pneumonia hospitalar","pavm",
        "pneumonia atipica","legionella","mycoplasma pneumoniae",
        "derrame pleural","pleurite","toracocentese","drenagem pleural",
        "sdra","lesao pulmonar aguda","ards","ventilacao mecanica",
        "insuficiencia respiratoria aguda","oxigenoterapia",
        "cancer de pulmao","carcinoma pulmonar","adenocarcinoma pulmon",
        "sarcoidose","fibrose pulmonar","doenca intersticial","bronquiectasia",
        "pneumotorax espontaneo","espirometria","vef1","cvf",
        "sono obstrutivo","apneia do sono","cpap","bipap",
      ],
      "default_sub": "DPOC e Asma no Adulto",
      "subtopicos": {
        "DPOC e Asma no Adulto": [
          "dpoc","doenca pulmonar obstrutiva","enfisema","bronquite cronica",
          "gold dpoc","exacerbacao dpoc","broncodilatador","anticoli longa",
          "tiotropio","formoterol","salmeterol","corticoide inalado",
          "asma bronquica adulto","crise asmatica","step asma","gina asma",
        ],
        "Embolia Pulmonar e TVP": [
          "embolia pulmonar","tep","tromboembolismo","tvp",
          "anticoagulacao tep","heparina nfrac","heparina baixo peso",
          "rivaroxabana","apixabana","warfarina","score wells","score geneva",
          "angiotc torax","cintilografia",
        ],
        "Pneumonia e Infecção Respiratória": [
          "pneumonia adquirida comunidade","pac","pneumonia hospitalar",
          "pneumonia atipica","legionella","mycoplasma","chlamydia resp",
          "amoxicilina pneumonia","azitromicina pneumonia","score curb-65",
          "psi pneumonia","antibiotico pneumonia","radiografia torax infiltrado",
        ],
        "Insuficiência Respiratória e UTI": [
          "sdra","ards","lesao pulmonar aguda","insuficiencia respiratoria aguda",
          "ventilacao mecanica","vt protetor","prone position","paralise neuromusc",
          "oxigenoterapia","mascara reservatorio","cateter nasal",
          "desmame ventilatório","extubacao",
        ],
        "Doenças Pleurais e Intersticiais": [
          "derrame pleural","pleurite","toracocentese","drenagem pleural",
          "empiema","quilotorax","fibrose pulmonar","doenca intersticial",
          "sarcoidose","bronquiectasia","pneumotorax espontaneo",
          "hemotorax nao traumatico",
        ],
      },
    },

    "Hematologia": {
      "kw": [
        "anemia","anemia ferropriva","anemia megaloblastica","vit b12","folato",
        "anemia hemolitica","coombs","esferocitose","hemoglobinuria",
        "anemia falciforme","drepanocitose","hbs","crises vasoclusivas",
        "talassemia","betathalassemia","alfa talassemia",
        "leucemia","lma","llc","lmc","linfoma hodgkin","linfoma nao hodgkin",
        "mieloma multiplo","cadeia leve","bence jones",
        "plaquetopenia","trombocitopenia","pti","ptr","sus hematol","cid",
        "hemofilia","fviii","fix","doenca de von willebrand",
        "anticoagulante","warfarina","heparina","rivaroxabana",
        "transfusao sanguinea","hemocomponentes","concentrado hemacias",
        "plaquetas transfusao","pfc","crioprecipitado",
        "neutropenia","neutropenia febril","g-csf","filgrastim",
      ],
      "default_sub": "Anemias e Hemoglobinopatias",
      "subtopicos": {
        "Anemias e Hemoglobinopatias": [
          "anemia ferropriva","ferro","ferritina","saturaçao transferrina",
          "anemia megaloblastica","vit b12","folato","anemia hemolitica",
          "anemia falciforme","drepanocitose","talassemia","crise falciforme",
          "coombs direto","esferocitose","hemoglobinuria nocturna",
        ],
        "Leucemias e Linfomas": [
          "leucemia","lma","lmc","llc","lla","linfoma hodgkin","linfoma nao hodgkin",
          "linfoma de burkitt","mieloma multiplo","bence jones",
          "quimioterapia hematol","transplante medula ossea","tmoch",
          "neutropenia febril","g-csf",
        ],
        "Coagulopatias e Trombose": [
          "hemofilia","fator viii","fator ix","von willebrand","cid",
          "trombocitopenia","pti","ptr","purpura trombocitopenica",
          "anticoagulante","warfarina","heparina","inr","tp","ttpa",
          "trombose venosa","trombofilia","anticardiolipina","lupus anticoagulante",
        ],
        "Transfusão e Hemocomponentes": [
          "transfusao","hemocomponentes","concentrado hemacias","plaquetas transfus",
          "plasma fresco congelado","pfc","crioprecipitado",
          "reacao transfusional","indicacao transfusao","hemoterapia",
        ],
      },
    },

    "Reumatologia": {
      "kw": [
        "lupus","les","lúpus eritematoso","critérios slicc","anticorpo anti-dna",
        "artrite reumatoide","ar ","fator reumatoide","anti-ccp","sinovite",
        "espondiloartrite","espondilite anquilosante","coluna bamboo",
        "artrite psoriasica","artrite reativa","sindrome de reiter",
        "gota","acido urico","hiperuricemia","artrite gotosa","tofos",
        "fibromialgia","pontos dolorosos","polimialgia reumatica",
        "sjogren","olho seco","esclerodermia","fenomeno de raynaud",
        "polimiosite","dermatomiosite","miosite","cpk miosite",
        "vasculite","anca","poliangiite","granulomatose wegener","churg-strauss",
        "artralgia","sinovite","efusao articular","artrocentese",
        "metotrexato","hidroxicloroquina","leflunomida","anti-tnf",
        "dmard","prednisona reumatol","colchicina",
      ],
      "default_sub": "Artrite Reumatoide e Artropatias",
      "subtopicos": {
        "Lúpus Eritematoso Sistêmico": [
          "lupus","les","lúpus eritematoso sistemico","critérios slicc","acr les",
          "anticorpo anti-dna","anti-smith","anti-ro","anti-la",
          "nefrite lupica","serosite lupica","trombocitopenia lupica",
          "hidroxicloroquina","azatioprina les","ciclofosfamida les",
        ],
        "Artrite Reumatoide e Espondiloartrites": [
          "artrite reumatoide","ar ","fator reumatoide","anti-ccp","sinovite",
          "erosao articular","metotrexato","leflunomida","anti-tnf",
          "espondiloartrite","espondilite anquilosante","hla-b27",
          "artrite psoriasica","artrite reativa",
        ],
        "Gota e Artropatias por Microcristais": [
          "gota","acido urico","hiperuricemia","artrite gotosa","tofos",
          "colchicina","alopurinol","febuxostato","articulacao tofacea",
          "pseudogota","condrocalcinose","pirofosfato de calcio",
        ],
        "Vasculites e Miopatias Inflamatórias": [
          "vasculite","anca","granulomatose com poliangiite","wegener",
          "churg-strauss","poliarterite nodosa","vasculite de grandes vasos",
          "arterite de takayasu","arterite de celulas gigantes",
          "polimiosite","dermatomiosite","cpk","ald miosite","anti-jo1",
          "fibromialgia","polimialgia reumatica",
        ],
      },
    },

    "Psiquiatria": {
      "kw": [
        "depressao","transtorno depressivo maior","tdm","episodio depressivo",
        "antidepressivo","isrs","sertralina","fluoxetina","escitalopram",
        "transtorno bipolar","mania","hipomania","litio","valproato psiq","quetiapina",
        "esquizofrenia","psicose","alucinacao","delírio","antipsicótico",
        "haloperidol","risperidona","olanzapina","clozapina","aripiprazol",
        "transtorno de ansiedade","tag","pânico","fobia social","agorafobia",
        "transtorno obsessivo","toc","ptsd","estresse pos traumatico",
        "dependencia quimica","alcoolismo","tabagismo clinico","vareniclina",
        "benzodiazepinico","diazepam","clonazepam","alprazolam",
        "suicidio","ideacao suicida","risco suicida","tentativa suicidio",
        "tdah","transtorno deficit atencao","methylfenidato","atomoxetina",
        "transtorno somatoforme","hipocondria","conversao somatica",
        "avaliacao psiquiatrica","dsm","cid psiq",
      ],
      "default_sub": "Depressão e Transtornos do Humor",
      "subtopicos": {
        "Depressão e Transtornos do Humor": [
          "depressao","transtorno depressivo","episodio depressivo",
          "antidepressivo","isrs","sertralina","fluoxetina","escitalopram",
          "venlafaxina","duloxetina","mirtazapina","imao",
          "transtorno bipolar","mania","hipomania","litio","valproato bipolar",
          "ciclotimia","humor deprimido","anedonia",
        ],
        "Esquizofrenia e Transtornos Psicóticos": [
          "esquizofrenia","psicose","alucinacao auditiva","delírio persecutorio",
          "sintomas positivos","sintomas negativos","antipsicótico tipico",
          "antipsicótico atipico","haloperidol","risperidona","olanzapina",
          "clozapina","aripiprazol","depot","decanoato haloperidol",
        ],
        "Transtornos de Ansiedade e TOC": [
          "transtorno de ansiedade generalizada","tag","pânico",
          "fobia social","agorafobia","toc","transtorno obsessivo",
          "ptsd","estresse agudo","benzodiazepinico",
          "isrs ansiedade","tcc ansiedade","exposicao resposta",
        ],
        "Dependência Química e Álcool": [
          "dependencia de alcool","alcoolismo","sindrome de abstinencia",
          "delirium tremens","tiamina wernicke","disulfiram","naltrexona",
          "dependencia quimica","crack","cocaina","opiaceo","metadona",
          "abuso de substancia","cessacao do tabagismo psiq",
        ],
        "Suicídio e Urgências Psiquiátricas": [
          "suicidio","ideacao suicida","tentativa suicidio","risco suicida",
          "internacao involuntaria","contenção quimica","contenção fisica",
          "agitacao psicomotora","delirium",
        ],
      },
    },

    "Dermatologia": {
      "kw": [
        "melanoma","carcinoma basocelular","cbc","carcinoma espinocelular","cec",
        "dermatite","eczema","dermatite seborreica","dermatite atopica",
        "psoriase","placa eritematosa","psoríase","metrotexato dermat",
        "urticaria","angioedema","reacao alergica cutanea",
        "acne","rosacea","dermatose",
        "escabiose","sarna","pediculose","piolho",
        "tinea","dermato fito","onicomicose","candida cutanea",
        "herpes zoster","zona","varicela cutanea","aciclovir dermat",
        "ulcera de pressao","lesao por pressao","escaras",
        "ulcera venosa","ulcera arterial","pe diabetico",
        "alopecia","queda de cabelo","vitiligo","melasma",
        "condiloma","hpv cutaneo","verrugas","molluscum",
        "lesao cutanea","nevo melanocitico","lesao pigmentada",
      ],
      "default_sub": "Dermatoses Inflamatórias e Infecciosas",
      "subtopicos": {
        "Neoplasias Cutâneas": [
          "melanoma","carcinoma basocelular","cbc","carcinoma espinocelular","cec",
          "biopsia cutanea","abcd melanoma","espessura de breslow",
          "ceratose actinica","queratose","nevo melanocitico","exerese cutanea",
        ],
        "Dermatoses Inflamatórias e Infecciosas": [
          "dermatite","eczema","psoriase","urticaria","angioedema",
          "acne","rosacea","escabiose","tinea","dermatofitose",
          "herpes zoster","zona","varicela cutanea","impetigo","erisipela derm",
          "celulite dermato","fasciite cutanea",
        ],
        "Úlceras e Lesões Crônicas": [
          "ulcera de pressao","lesao por pressao","escaras","estadiamento up",
          "ulcera venosa","ulcera arterial","pe diabetico",
          "curativo","desbridamento","ostomia cuidado",
        ],
      },
    },

  }, # end temas Clínica Médica
}, # end Clínica Médica

# ══════════════════════════════════════════════════════════════
"Cirurgia Geral": {
  "area_kw": [
    "cirurgia","pre-operatorio","pos-operatorio","intraoperatorio",
    "abordagem cirurgica","indicacao cirurgica","laparotomia","laparoscopia",
    "anestesia","sala de operacao","bloco cirurgico",
  ],
  "default_tema": "Cirurgia do Aparelho Digestivo",
  "temas": {

    "Trauma": {
      "kw": [
        "trauma","atls","politrauma","avaliacao primaria","avaliacao secundaria",
        "abcde trauma","glasgow","gcs","pupilas trauma",
        "trauma toracico","pneumotorax hipertensivo","hemotorax","tamponamento cardiac",
        "trauma abdominal","lavado peritoneal","fast","eco fast",
        "trauma cranioencefal","tce","hematoma epidural","hematoma subdural",
        "hematoma extradural","hematoma intracerebral traumatico",
        "trauma raquimedular","fratura coluna","lesao medular",
        "trauma pelvico","fratura pelve","fratura acetabulo",
        "fratura femur proximal","fratura pertrocanteriana",
        "hemorragia classe i","hemorragia classe ii","hemorragia classe iii",
        "choque hipovolemico trauma","reposicao volemia",
        "queimadura","queimaduras","scq","regra dos 9","parkland",
        "intoxicacao exogena","intoxicacao aguda","envenenamento",
      ],
      "default_sub": "Trauma e ATLS — Avaliação Inicial",
      "subtopicos": {
        "Trauma e ATLS — Avaliação Inicial": [
          "atls","avaliacao primaria","abcde","politrauma","glasgow","gcs",
          "via aerea trauma","intubacao sequencia rapida","pneumotorax tension",
          "tamponamento cardiaco trauma","hemorragia classe","reposicao trauma",
          "fast","lavado peritoneal diagnostico",
        ],
        "Trauma Cranioencefálico": [
          "tce","trauma cranioencefal","hematoma epidural","hematoma subdural",
          "lucid interval","lesao axonal difusa","contusao cerebral",
          "hipertensao intracraniana tce","manitol","hiperventilacao tce",
          "glasgow escore","monitorar pic",
        ],
        "Trauma Torácico": [
          "trauma toracico","pneumotorax hipertensivo","hemotorax","hemopneumotorax",
          "fratura de costela","torax instavel","pneumotorax aberto",
          "ruptura aorta traumatica","contusao miocardica","tamponamento pericardico",
          "drenagem toracica","drenagem pleural trauma",
        ],
        "Queimaduras": [
          "queimadura","queimaduras","scq","superficie corporal queimada",
          "regra dos 9","formula de parkland","fluido ressuscitacao queimado",
          "queimadura 1 grau","queimadura 2 grau","queimadura 3 grau",
          "inalacao fumaca","escarotomia","enxerto queimado",
        ],
        "Trauma Abdominal e Pélvico": [
          "trauma abdominal","fast abdominal","lesao hepatica grau","lesao esplenica",
          "trauma baço","trauma figado","lesao intestinal","trauma renal",
          "fratura pelve","fratura acetabulo","hemorragia pelvica",
          "laparotomia exploradora trauma","cirurgia de controle de dano",
        ],
      },
    },

    "Cirurgia do Aparelho Digestivo": {
      "kw": [
        "abdome agudo","apendicite","colecistite aguda","pancreatite aguda cirurgia",
        "peritonite","abscesso intra-abdominal",
        "hemorragia digestiva cirurgica","varizes cirugia","laqueadura varizes",
        "obstrucao intestinal","bridas","aderencias","ileu","volvo","invaginacao adulto",
        "hernia inguinal","hernia femoral","hernia umbilical","hernia incisional",
        "hernia encarcerada","hernia estrangulada","herniorrafia",
        "colecistectomia","colangiopancreatografia","cpre","coledocolitiase",
        "cancer gastrico cirurgia","gastrectomia","esofagectomia",
        "cancer colorretal cirurgia","colectomia","ressecao anterior","amputacao abd perineal",
        "colostomia","ileostomia","hartmann","stomia",
        "fistula anal","hemorroida cirurgica","fissura anal cirurgica","proctologia",
        "doenca diverticular complicada","diverticulite aguda","diverticulite",
        "isquemia mesenterica cirurgica","infarto mesenterico",
        "cirurgia bariatrica","bypass gastrico","sleeve gastrectomia",
        "esofago acalasia cirugia","fundoplicatura",
      ],
      "default_sub": "Abdome Agudo e Emergências Abdominais",
      "subtopicos": {
        "Abdome Agudo e Emergências Abdominais": [
          "abdome agudo inflamatorio","apendicite aguda","colecistite aguda",
          "peritonite","abscesso intra-abdominal","pancreatite aguda cirurgica",
          "diverticulite aguda","perfuracao visceral","ulcera perfurada",
          "sinal de blumberg","defesa muscular","guarda abd",
        ],
        "Abdome Agudo Obstrutivo": [
          "obstrucao intestinal","bridas","aderencias pos operatorias",
          "ileu obstructivo","volvo","hernia encarcerada","hernia estrangulada",
          "cancer obstrutivo","intussuscep adulto","nivel hidroaereo",
        ],
        "Vias Biliares e Pâncreas": [
          "colecistectomia","colelitíase","colangite","coledocolitiase",
          "cpre","colangiopancreatografia","tokyo guidelines","colangite aguda",
          "pancreatite aguda cirurgica","necrose pancreatica","abscesso pancreatico",
          "drenagem cirurgica pancreas","pseudocisto cirurgico",
        ],
        "Cirurgia Oncológica Digestiva": [
          "cancer gastrico cirurgia","gastrectomia","adenocarcinoma gastrico cirg",
          "cancer colorretal cirurgia","colectomia","ressecao anterior baixa",
          "amputacao abdominoperineal","cirurgia de figado metastase",
          "hepatectomia","esplenectomia oncologica",
        ],
        "Hérnias e Parede Abdominal": [
          "hernia inguinal","hernia femoral","hernia umbilical","hernia incisional",
          "hernia de spiegel","hernia hiatal","herniorrafia","hernioplastia",
          "protese cirurgia hernia","tela","plug hernia",
        ],
        "Proctologia e Cólon": [
          "hemorroida","fissura anal","fistula anoretal","abscesso anal",
          "prolapso retal","doenca de crohn cirurgica","retocolite cirugia",
          "colostomia","ileostomia","hartmann","reversal ostomia",
          "cancer de reto","cirurgia de reto","excisao total mesorreto",
        ],
      },
    },

    "Cirurgia Pediátrica": {
      "kw": [
        "estenose hipertrofica do piloro","estenose pilorica","piloro",
        "atresia esofagica","fistula traqueoesofagica","imperforação anal",
        "atresia intestinal","ma rotacao intestinal","rotacao intestinal",
        "onfalocele","gastrosquise","defeito parede abdominal neonato",
        "hernia diafragmatica congenita","hdc","sinal de desconforto respiratorio neonatal cirg",
        "apendicite na crianca","apendicite pediatrica",
        "invaginacao intestinal","intussuscepção","enema opaco invaginacao",
        "doenca de hirschsprung","megacolo congenito","agangliose",
        "criptorquidia","testiculo nao descido","orquidopexia",
        "hipospadias","espadias","fimose","postite",
        "cirurgia pediatrica","cirurgia da crianca","neonatal cirurgico",
        "refluxo vesicoureteral crianca","hidronefrose neonatal",
        "quisto ovariano neonatal","cistoide","tumor de wilms","nefroblastoma",
        "neuroblastoma","hepatoblastoma","rabdomiossarcoma pediatrico",
      ],
      "default_sub": "Anomalias Congênitas e Urgências Pediátricas",
      "subtopicos": {
        "Estenose Pilórica e Patologias Neonatais": [
          "estenose pilorica","hipertrofia piloro","piloromiotomia","sinal oliveta",
          "atresia esofagica","fistula traqueoesofagica","atresia intestinal",
          "obstrucao intestinal neonatal","onfalocele","gastrosquise",
          "ma rotacao","volvo neonatal","enterocolite necros cirg",
        ],
        "Anomalias Congênitas e Urgências Pediátricas": [
          "hernia diafragmatica congenita","hdc","atresia esofagica",
          "imperforacao anal","hirschsprung","megacolo congenito","agangliose",
          "apendicite na crianca","invaginacao intestinal","intussuscepção",
          "obstrucao intestinal crianca","laparotomia pediatrica",
        ],
        "Urologia Pediátrica": [
          "criptorquidia","testiculo nao descido","orquidopexia",
          "hipospadia","espadias","fimose","prepucio","postite",
          "refluxo vesicoureteral","hidronefrose neonatal","hidroureteronefrose",
          "uropatia obstrutiva","cistouretrograma","uretra posterior",
        ],
        "Oncologia Pediátrica": [
          "tumor de wilms","nefroblastoma","neuroblastoma","hepatoblastoma",
          "rabdomiossarcoma","meduloblastoma","astrocitoma pediatrico",
          "linfoma pediatrico cirg","tumor abdominal crianca",
        ],
      },
    },

    "Cirurgia Vascular": {
      "kw": [
        "aneurisma de aorta abdominal","aaa","aneurisma aorta toracica",
        "dissecao aortica","dissecao de aorta","stanford","debakey",
        "doenca arterial obstrutiva periferica","daop","isquemia de membro",
        "claudicacao intermitente","gangrana","amputacao membro",
        "embolectomia","trombectomia arterial","by-pass femoro",
        "by-pass aortofemoral","by-pass femoro-popliteo",
        "varizes dos membros inferiores","insuficiencia venosa cronica",
        "trombose venosa profunda","tvp","sindrome pos-trombotica",
        "tromboembolismo venoso","tev","filtro veia cava",
        "fistula arteriovenosa","fav renal","acesso vascular",
        "sindrome compartimental","fasciotomia",
        "isquemia mesenterico vascular","oclusao arteria mesenterica",
        "estenose arteria carotida","endarterectomia carotida",
        "acidente vascular cerebral cirg","stent carotida",
        "aneurisma cerebral cirurgico",
      ],
      "default_sub": "Doença Arterial e Aneurismas",
      "subtopicos": {
        "Doença Arterial e Aneurismas": [
          "aneurisma de aorta","aaa","aneurisma aorta toracica",
          "dissecao aortica","stanford","doenca arterial obstrutiva",
          "daop","isquemia membro inferior","claudicacao","gangrana",
          "amputacao vascular","by-pass","endovascular","stent arterial",
        ],
        "Doenças Venosas e Trombose": [
          "trombose venosa profunda","tvp","varizes","insuficiencia venosa cronica",
          "sindrome pos-trombotica","tev","filtro veia cava",
          "safenectomia","escleroterapia varizes","flebite",
        ],
      },
    },

    "Ortopedia": {
      "kw": [
        "fratura","luxacao","entorse","contusao ossea",
        "osteossintese","fixacao interna","fixacao externa","placa parafuso",
        "artroscopia","artroplastia","protese quadril","protese joelho",
        "coluna vertebral","hernia de disco","protrusao discal","estenose canal espinhal",
        "escoliose","cifose","lordose patologica",
        "osteomielite ortopedica","artrite septica ortopedica",
        "fratura de femur","fratura pertrocanteriana","fratura colo femur",
        "fratura de umero","fratura de radio","fratura de escapula",
        "fratura de tornozelo","fratura bimaleolar","fratura de calcaneo",
        "rotura de tendao","tendinite","ligamento cruzado","lcm","lcl",
        "lesao de menisco","condropatia patelar",
        "amputacao ortopedica","membro fantasma",
        "ortopedia","traumatologia","lombalgia","lombociatalgia",
        "compressao radicular","deficit neurologico por coluna",
      ],
      "default_sub": "Fraturas e Luxações",
      "subtopicos": {
        "Fraturas e Luxações": [
          "fratura","luxacao","osteossintese","reducao ortopedica",
          "fratura de femur","fratura colo femur","fratura pertrocant",
          "fratura de radio","fratura de umero","fratura tornozelo",
          "fratura de coluna","fratura exposta","fratura patologica",
          "luxacao de quadril","luxacao de ombro",
        ],
        "Coluna e Neuropatias Compressivas": [
          "hernia de disco","protrusao discal","estenose canal espinhal",
          "compressao radicular","lombociatalgia","lombalgia cronica",
          "escoliose","cifose","espondilolistese","mielopatia cervical",
        ],
        "Articulações e Lesões Ligamentares": [
          "artroscopia","ligamento cruzado anterior","lca","ligamento cruzado posterior",
          "lesao de menisco","condropatia","tendinite","rotura tendinosa",
          "artroplastia","protese de joelho","protese de quadril",
          "entorse tornozelo","lesao sindesmose",
        ],
      },
    },

    "Otorrinolaringologia": {
      "kw": [
        "otite media aguda","otite media","otite cronica","oma","miringite",
        "sinusite","rinossinusite","sinusite cronica","polipo nasal",
        "rinite","rinorreia","obstrucao nasal",
        "amigdalite","tonsilite","amigdalectomia","adenoidectomia",
        "epistaxe","sangramento nasal","cauterizacao nasal",
        "corpo estranho naso","corpo estranho ouvido",
        "surdez","hipoacusia","perda auditiva","audiometria",
        "laringite","laringotraqueiobronquite","crupe","epiglotite",
        "apneia obstrutiva sono","cpap sono","ronco",
        "otorrinolaringologia","otoesclerose","colesteatoma",
        "vertigo","labirintite","vertigem posicional",
      ],
      "default_sub": "Otite, Sinusite e Infecções ORL",
      "subtopicos": {
        "Otite, Sinusite e Infecções ORL": [
          "otite media aguda","oma","otite cronica","sinusite","rinossinusite",
          "amigdalite","tonsilite","faringite","laringite","epiglotite",
          "antibioticoterapia orl","amoxicilina orl",
        ],
        "Epistaxe, Hipoacusia e Outras": [
          "epistaxe","surdez","hipoacusia","perda auditiva","audiometria",
          "labirintite","vertigem posicional","otoesclerose","colesteatoma",
          "corpo estranho orl","apneia do sono",
        ],
      },
    },

    "Oftalmologia": {
      "kw": [
        "glaucoma","pressao intraocular","pio","campo visual","trabeculoplastia",
        "catarata","opacificacao cristalino","facoemulsificacao",
        "retinopatia diabetica","fotocoagulacao retiniana",
        "retinopatia hipertensiva","degeneracao macular","dml",
        "descolamento de retina","buraco macular",
        "uveite","irite","iridociclite",
        "ceratite","conjuntivite","traqueoma","clamydia ocular",
        "estrabismo","amaurose","cegueira",
        "glaucoma de angulo fechado","glaucoma congenito",
        "tumor ocular","melanoma de coroide","retinoblastoma",
        "neurite optica","papiledema","fundo de olho",
        "oftalmologia","acuidade visual","ocular",
      ],
      "default_sub": "Glaucoma, Catarata e Retinopatias",
      "subtopicos": {
        "Glaucoma, Catarata e Retinopatias": [
          "glaucoma","pressao intraocular","campo visual","catarata","facoemulsificacao",
          "retinopatia diabetica","fotocoagulacao","retinopatia hipertensiva",
          "degeneracao macular","descolamento de retina","uveite",
        ],
      },
    },

  }, # end temas Cirurgia Geral
}, # end Cirurgia Geral

# ══════════════════════════════════════════════════════════════
"Pediatria": {
  "area_kw": [
    "crianca","pediatria","pediatrico","infantil","recem-nascido","lactente",
    "pre-escolar","escolar","adolescente","neonato","rn ","rnpig","rnpt",
    "crescimento infantil","desenvolvimento infantil","imunizacao infantil",
  ],
  "default_tema": "Puericultura",
  "temas": {

    "Puericultura": {
      "kw": [
        "aleitamento materno","amamentacao","leite materno","pega correta",
        "aleitamento exclusivo","leite artificial","formula infantil","blw",
        "introducao alimentar","alimentacao complementar",
        "crescimento","curva de crescimento","peso para idade","estatura para idade",
        "imc infantil","oms curva","percentil crescimento",
        "desenvolvimento neuropsicomotor","dnpm","marcos do desenvolvimento",
        "denver ii","bayley","reflexo de moro","reflexo de succa",
        "acompanhamento pediatrico","puericultura","consulta pediatrica",
        "teste do pezinho","triagem neonatal metabolica","pku",
        "hipotireoidismo congenito triagem","triagem genetica",
        "calendario nacional imunizacao","pni","vacina bcg","vacina hepatite b",
        "vacina pentavalente","vacina vip","vacina vorh","vacina pneumococica",
        "vacina meningococica","vacina triplice viral","vacina varicela",
        "vacina hpv","vacina influenza crianca","esquema vacinal",
        "violencia infantil","maus-tratos crianca","eca","conselho tutelar",
        "bullying","negligencia","abuso sexual","notificacao maus tratos",
      ],
      "default_sub": "Crescimento, Desenvolvimento e Puericultura",
      "subtopicos": {
        "Crescimento, Desenvolvimento e Puericultura": [
          "crescimento infantil","curva de crescimento","percentil","zscore",
          "desenvolvimento neuropsicomotor","dnpm","marcos motores","linguagem infantil",
          "denver ii","acompanhamento pediatrico","consulta preventiva",
        ],
        "Aleitamento Materno e Alimentação Infantil": [
          "aleitamento materno","amamentacao","leite materno","pega correta",
          "fissura mamilar","mastite lactacao","ordenhamento","banco de leite",
          "aleitamento exclusivo","formula infantil","blw","alimentacao complementar",
          "introducao alimentar","desmame","alergia proteina leite vaca","aplv",
        ],
        "Imunização e Calendário Vacinal": [
          "calendario nacional imunizacao","pni","vacina bcg","vacina hepatite b",
          "vacina pentavalente","vacina vip","vacina vorh","vacina pneumococica",
          "vacina meningococica","triplice viral","mmr","varicela",
          "hpv infantil","influenza crianca","esquema vacinal","contraindicacao vacinal",
          "evento adverso vacina","anafilaxia vacinal",
        ],
        "Violência Infantil e ECA": [
          "maus-tratos crianca","violencia infantil","eca","conselho tutelar",
          "abuso sexual infantil","negligencia","sindrome do bebe sacudido",
          "notificacao maus tratos","sinan violencia","lesao sem explicacao",
        ],
      },
    },

    "Neonatologia": {
      "kw": [
        "recem-nascido","neonato","rn ","rnpt","rnpig","prematuro","prematuridade",
        "apgar","escore apgar","reanimacao neonatal","sala de parto",
        "ictericia neonatal","hiperbilirrubinemia","bilirrubina indireta",
        "zonas de kramer","fototerapia","exsanguineotransfusao",
        "sepse neonatal","infeccao neonatal","hemocultura neonatal",
        "meningite neonatal","ampicilina gentamicina neonatal",
        "membrana hialina","sindrome angustia respiratoria neonatal","sar",
        "surfactante","cpap neonatal","ven neonatal",
        "disturbio respiratorio neonatal","transicao respiratoria",
        "enterocolite necrosante","ecn","nec",
        "infeccao congenita","torch","toxoplasmose congenita","sifilis congenita",
        "cmv congenito","herpes neonatal","rubeola congenita","zika congenita",
        "triagens neonatais","coracaozinho","orelhinha","olhinho","linguinha",
        "hipoglicemia neonatal","hipocalcemia neonatal",
        "doenca hemorragica rn","vitamina k rn","sangramento neonatal",
        "cariotipos","malformacao congenita","cromossomico",
        "pequeno para idade gestacional","pig","grande para ig","gig",
        "asfixia perinatal","hipoxia perinatal","encefalopatia hipoxica isquemica","ehi",
      ],
      "default_sub": "Reanimação Neonatal e Adaptação Pós-Natal",
      "subtopicos": {
        "Reanimação Neonatal e Adaptação Pós-Natal": [
          "reanimacao neonatal","sala de parto","apgar","vt reanimacao",
          "mascara e balao rn","intubacao neonatal","adrenalina rn",
          "depressao neonatal","asfixia perinatal","encefalopatia hipoxica isquemica","ehi",
          "hipotermia terapeutica","hipoxia neonatal",
        ],
        "Icterícia Neonatal": [
          "ictericia neonatal","hiperbilirrubinemia","bilirrubina indireta",
          "bilirrubina total rn","zonas de kramer","fototerapia",
          "exsanguineotransfusao","kernicterus","incompatibilidade abo",
          "incompatibilidade rh","doenca hemolitica rn",
        ],
        "Sepse Neonatal e Infecções Congênitas": [
          "sepse neonatal","infeccao neonatal","hemocultura neonatal",
          "antibiotico rn","ampicilina gentamicina","ceftriaxona neonatal",
          "infeccao congenita","torch","toxoplasmose congenita","sifilis congenita",
          "cmv congenito","herpes neonatal","rubeola congenita","zika congenita",
          "meningite neonatal",
        ],
        "Síndrome do Desconforto Respiratório Neonatal": [
          "membrana hialina","sar","sindrome angustia respiratoria neonatal",
          "surfactante exogeno","cpap neonatal","taquipneia transitoria rn",
          "aspiracao meconio","pneumotorax neonatal","ven neonatal",
          "displasia broncopulmonar","dbp","prematuridade respiratoria",
        ],
        "Prematuridade e Cuidados Intensivos Neonatais": [
          "prematuridade","prematuro","rnpt","muito baixo peso","extremo baixo peso",
          "utip neonatal","utin","enterocolite necrosante","ecn","nec",
          "hemorragia peri-intraventricular","hpiv","retinopatia prematuridade",
          "apneia prematuridade","anemia prematuridade",
        ],
      },
    },

    "Pneumologia Pediátrica": {
      "kw": [
        "asma pediatrica","asma na crianca","crise asmatica infantil",
        "broncoespasmo","sibilancia","wheeze","wheezing","lactente sibilante",
        "bronquiolite","vsr","virus sincicial respiratorio","bre","bd",
        "pneumonia bacteriana crianca","pneumonia viral crianca","pneu crianca",
        "broncopneumonia","antibiotico pneumonia infantil","radiografia pneu crianca",
        "laringite aguda","laringotraqueobronquite","crupe","estridor inspiratorio",
        "epiglotite","difteria","coqueluche","bordetella",
        "influenza pediatrica","oseltamivir pediatrico",
        "tuberculose na crianca","contato tb crianca","prophylaxis tb infantil",
        "fibrosa cistica","mucoviscidose",
        "displasia broncopulmonar crianca","dbp",
        "disturbio respiratorio infant","taquipneia","batimento asa nariz",
      ],
      "default_sub": "Pneumonia Pediátrica e Infecções Respiratórias",
      "subtopicos": {
        "Asma e Sibilância Pediátrica": [
          "asma pediatrica","asma na crianca","crise asmatica infantil",
          "crise de asma","exacerbacao asma","asma grave","asma moderada",
          "corticoide inalado crianca","beta2 agonista crianca","salbutamol crianca",
          "step asma pediatrica","gina pediatrico","espirometria crianca",
          "asma persistente","asma intermitente","profilaxia asma",
          "sibilancia recorrente","sibilancia cronica","sibilancia na crianca",
          "sibilancia maior 2 anos","broncoespasmo crianca","broncodilatador crianca",
          "salbutamol","broncoespasmo","hiperreatividade bronquica","atopia",
          "sibilancia","crise de sibilancia",
        ],
        "Bronquiolite Viral Aguda": [
          "bronquiolite","bronquiolite aguda","bronquiolite viral",
          "vsr","virus sincicial respiratorio",
          "lactente sibilante","primeiro episodio sibilancia",
          "sibilancia lactente","< 2 anos sibilancia","crianca menor 2 anos sibilante",
          "bronquiolite tratamento","suporte bronquiolite",
        ],
        "Pneumonia Pediátrica e Infecções Respiratórias": [
          "pneumonia bacteriana crianca","pneumonia viral crianca",
          "broncopneumonia","pneumonia crianca","pneumonia infantil",
          "antibiotico pneumonia infantil","amoxicilina pneumonia crianca",
          "radiografia torax crianca","derrame pleural crianca",
          "streptococcus pneumoniae crianca","pneumonia atipica crianca",
          "influenza pediatrica","coqueluche","bordetella pertussis",
          "pneumonia lobar crianca","consolidacao pulmonar crianca",
        ],
        "Laringite, Crupe e Epiglotite": [
          "laringite aguda","laringotraqueobronquite","crupe","estridor inspiratorio",
          "epiglotite","difteria","dexametasona crupe","epinefrina racemia",
        ],
      },
    },

    "Gastrologia Pediátrica": {
      "kw": [
        "diarreia aguda crianca","desidratacao infantil","plano a","plano b","plano c",
        "soro de reidratacao oral","sro","resol","oms hidratacao","zinc diarreia",
        "refluxo gastroesofagico infantil","rge lactente","vomito lactente",
        "doenca do refluxo gastroesofagico crianca","drge pediatrica",
        "constipacao crianca","constipacao cronica crianca","enurese nao regressiva",
        "dor abdominal cronica crianca","dor abdominal recorrente",
        "intolerancia lactose crianca","alergia proteina leite vaca","aplv",
        "doenca celiaca","enteropatia gluten",
        "hepatite a crianca","hepatite b crianca","hepatite virose infantil",
        "parasitose intestinal crianca","giardia","ascariase","oxiuriase","ancilostomose",
        "obstrucao intestinal crianca","invaginacao intestinal pediatrica",
        "diarreia cronica crianca","sindrome malabsorcao",
        "desnutricao infantil","marasmo","kwashiorkor",
        "intoxicacao alimentar crianca","gastroenterite viral",
      ],
      "default_sub": "Diarreia Aguda e Desidratação",
      "subtopicos": {
        "Diarreia Aguda e Desidratação": [
          "diarreia aguda crianca","desidratacao infantil","plano a","plano b","plano c",
          "soro de reidratacao oral","sro","resol","oms hidratacao",
          "zinc diarreia","probiotico diarreia","gastroenterite viral crianca",
        ],
        "Refluxo e Doenças do Esôfago Pediátrico": [
          "refluxo gastroesofagico infantil","rge lactente","vomito lactente",
          "drge pediatrica","pirose infantil","ph-metria pediatrica",
          "farmacoterapia rge pediatrico","cisaprida",
        ],
        "Parasitoses e Doenças Infecciosas Digestivas": [
          "parasitose intestinal crianca","giardia","ascariase","ancilostomose",
          "oxiuriase","enterobius","strongiloides infantil","ameba crianca",
          "hepatite a crianca","febr e ictericia crianca",
        ],
        "Doenças Crônicas Digestivas Pediátricas": [
          "doenca celiaca","enteropatia gluten","anticorpo antitransglutaminase",
          "alergia proteina leite vaca","aplv","formula extensamente hidrolisada",
          "intolerancia lactose","constipacao cronica crianca","laxativo pediatrico",
          "doenca inflamatoria intestinal crianca","crohn pediatrico",
        ],
      },
    },

    "Reumatologia Pediátrica": {
      "kw": [
        "artrite idiopatica juvenil","aij","artrite juvenil","oligoarticular",
        "poliarticular","sistemica aij","still da crianca",
        "febre reumatica","criterios de jones","cardite reumatica","corea de sydenham",
        "profilaxia febre reumatica","penicilina profilaxia reumatica",
        "lupus pediatrico","les crianca","nefrite lupica crianca",
        "purpura de henoch-schonlein","phs","nefrite phs","artralgia phs",
        "kawasaki","doenca de kawasaki","febre 5 dias","conjuntivite kawasaki",
        "imunoglobulina kawasaki","criterios kawasaki",
        "dermatomiosite juvenil","polimiosite crianca",
        "poliarterite nodosa infantil","vasculite leucocitoclastica",
        "sindrome de sjogren juvenil",
        "reumatologia pediatrica","artralgia crianca","artrite crianca",
      ],
      "default_sub": "Artrite Idiopática Juvenil e Reumatologia Pediátrica",
      "subtopicos": {
        "Artrite Idiopática Juvenil e Reumatologia Pediátrica": [
          "artrite idiopatica juvenil","aij","artrite juvenil","oligoarticular",
          "poliarticular","aij sistemica","still","ana aij","fator reum crianca",
          "metotrexato aij","biologico aij",
        ],
        "Febre Reumática": [
          "febre reumatica","criterios de jones","cardite reumatica","corea de sydenham",
          "valvulopatia reumatica","insuficiencia mitral reumatica",
          "profilaxia febre reumatica","penicilina benzatina reumatica",
          "streptococcus grupo a","faringite estreptococica",
        ],
        "Vasculites Pediátricas e Kawasaki": [
          "kawasaki","doenca de kawasaki","febre 5 dias","conjuntivite bulbar",
          "imunoglobulina ev kawasaki","aneurisma coronaria kawasaki",
          "purpura de henoch-schonlein","phs","arterite","vasculite pediatrica",
          "purpura cutanea palpavel crianca",
        ],
      },
    },

  }, # end temas Pediatria
}, # end Pediatria

# ══════════════════════════════════════════════════════════════
"Ginecologia & Obstetrícia": {
  "area_kw": [
    "gestacao","gravidez","gestante","obstetrica","obstetricia","parto","puerperio",
    "ginecologia","mulher","uterina","ovario","vagina","mama ginecol",
    "pre-natal","prenatal","menstruacao","ciclo menstrual",
  ],
  "default_tema": "Obstetrícia",
  "temas": {

    "Obstetrícia": {
      "kw": [
        "gestacao","gravidez","gestante","obstetrica","obstetricia",
        "semana de gestacao","ig ","idade gestacional",
        "pre-natal","prenatal","consulta pre-natal","sorologias gestacao",
        "trabalho de parto","partograma","fase ativa","periodo expulsivo",
        "cesariana","cesarea","indicacao cesarea","parto normal","parto vaginal",
        "episiotomia","forcipe","vacuo","forceps","distócia",
        "apresentacao fetal","podalica","transversa fetal",
        "pe-eclamsia","pre-eclampsia","eclampsia","hellp","dheg",
        "hipertensao gestacional","hipertensao na gravidez",
        "diabetes gestacional","dmg","tolerancia glucose gestacao",
        "hyperemese gravidica","nausea gestacao","vomito gestacao",
        "placenta previa","dppni","descolamento prematuro","rotura uterina",
        "amniorrexe prematura","rpmo","rpmpt","trabalho parto prematuro","tpp",
        "cerclagem","progesterona tocolise",
        "hemorragia pos-parto","hpp","atonia uterina","misoprostol parto",
        "gravidez ectopica","ectopica","salpinge","tubaria",
        "abortamento","aborto","mola hidatiforme","neoplasia trofoblastica",
        "ultrassonografia obstetrica","morfologica","doppler obstetrico",
        "ciur","restricao crescimento intra-uterino","pequenoig","oligoidramnio","polidramnio",
        "medicina fetal","amniocentese","cordocentese","biopsia vilo","genetica prenatal",
        "streptococcus agalactiae","estreptococo grupo b","profilaxia gbs",
        "puerpério","pos-parto","involucao uterina","loquios",
        "depressao pos-parto","psicose puerperal","mastite puerperal",
        "trombose puerperal","febre puerperal","sepse obstétrica",
        "sifilis gestacao","hiv gestacao","toxoplasmose gestacional","rubeola gestacao",
      ],
      "default_sub": "Intercorrências da Gestação",
      "subtopicos": {
        "Pré-Natal e Rotina Obstétrica": [
          "pre-natal","prenatal","consulta pre-natal","sorologias gestacao",
          "hb gestante","acido folico","sulfato ferroso gestacao",
          "ultrassonografia obstetrica","morfologica 1 tri","morfologica 2 tri",
          "doppler obstetrico","streptococcus grupo b","profilaxia gbs",
          "vacina gestante","hepatite b gestante",
        ],
        "Intercorrências da Gestação": [
          "pre-eclampsia","pe-eclamsia","eclampsia","hellp","dheg","sulfato magnesio",
          "hipertensao gestacional","diabetes gestacional","dmg","ttgo gestacao",
          "hiperêmese gravidica","vomito incoercivel gestacao",
          "placenta previa","dppni","descolamento prematuro placenta",
          "amniorrexe prematura","rpmo","trabalho parto prematuro","tocolise",
          "ciur","oligoidramnio","polidramnio","morte fetal",
          "sifilis gestacao","hiv gestacao","toxoplasmose gestacional",
          "gravidez ectopica","abortamento","mola hidatiforme",
        ],
        "Assistência ao Parto": [
          "trabalho de parto","partograma","fase ativa","periodo expulsivo",
          "parto normal","parto vaginal","cesariana","indicacao cesarea",
          "episiotomia","forcipe","forceps","vacuo","distócia",
          "apresentacao fetal","parto podalico","bispo","indução parto",
          "ocitocina parto","misoprostol parto","cardiotocografia","ctg",
        ],
        "Medicina Fetal e Diagnóstico Pré-Natal": [
          "medicina fetal","amniocentese","cordocentese","biopsia vilo corial",
          "genetica prenatal","trissomia 21","sindrome de down fetal",
          "translucencia nucal","doppler arteria uterina","arteria cerebral media",
          "maturidade pulmonar fetal","teste de estimulacao vibro",
          "perfil biofisico fetal",
        ],
        "Puerpério e Hemorragia Pós-Parto": [
          "puerperio","pos-parto","involucao uterina","loquios","amamentacao pos-parto",
          "hemorragia pos-parto","hpp","atonia uterina","laceracao perineal",
          "trauma obstetrico","retencao placenta","curetagem puerperal",
          "depressao pos-parto","psicose puerperal","mastite puerperal",
          "trombose puerperal","sepse obstetrica","febre puerperal",
          "sangramento apos parto","hemorragia apos parto","complicacao pos-parto",
          "endometrite pos-parto","subinvolucao uterina","hemorragia puerperal",
          "sangramento puerperal","curetagem apos parto","revisao cavidade uterina",
          "puerperal imediato","puerperal tardio","misoprostol hemorragia",
          "ocitocina hemorragia","uterotônico","uterotonicos","ergometrina",
        ],
      },
    },

    "Ginecologia": {
      "kw": [
        "ginecologia","ginecologica","ginecologico",
        "cancer de colo","ccu","ccol","citologia cervical","papanicolaou",
        "colposcopia","leep","conizacao","nic","lesao intraepitelial","hpv ginecol",
        "cancer de endometrio","cancer de ovario","ca ovario","mioma",
        "cancer de mama ginecol","mamografia ginecol","rastreamento mama",
        "corrimento vaginal","vaginose bacteriana","candida vaginal","tricomonas",
        "dst","ist","vulvovaginite","doenca inflamatoria pelvica","dip",
        "salpingite","endometrite","parametrite","piosalpinge",
        "sindrome ovarios policisticos","sop","ovario poliquistico",
        "amenorreia","menorragia","metrorragia","polimenorreia","oligomenorreia",
        "menopausa","climatério","fogachos","terapia hormonal",
        "anticoncepção","anticoncepcional","pilula","aco","diu","implante hormonal",
        "metodo contraceptivo","contracepcao de emergencia","levonorgestrel",
        "infertilidade feminina","estimulacao ovariana","fiv",
        "endometriose","adenomiose","mioma uterino","cisto ovariano",
        "mastologia","fibroadenoma","papiloma intraductal",
        "dismenorreia","tensao pre-menstrual","tpm",
      ],
      "default_sub": "Ginecologia Preventiva e Oncológica",
      "subtopicos": {
        "Ginecologia Preventiva e Oncológica": [
          "cancer de colo","ccu","citologia cervical","papanicolaou","colposcopia",
          "leep","conizacao","nic","lesao intraepitelial","hpv ginecol",
          "cancer de endometrio","cancer de ovario","ca ovario",
          "estadiamento figo","cirurgia oncologica ginecol",
          "cancer de mama tratamento","quimioterapia ginecologica",
        ],
        "Infecções Genitais e DIP": [
          "corrimento vaginal","vaginose bacteriana","candida vaginal","tricomonas",
          "vulvovaginite","dst","ist","herpes genital","hpv condiloma",
          "doenca inflamatoria pelvica","dip","salpingite","endometrite",
          "parametrite","piosalpinge","criterios dip","ceftriaxona dip",
        ],
        "Ginecologia Endócrina e Contracepção": [
          "sindrome ovarios policisticos","sop","amenorreia","ciclo menstrual",
          "menorragia","metrorragia","oligomenorreia","dismenorreia",
          "menopausa","climatério","terapia hormonal menopausa",
          "anticoncepção","anticoncepcional","pilula","aco","diu",
          "contracepcao emergencia","levonorgestrel","implante hormonal",
          "infertilidade","estimulacao ovariana",
        ],
        "Mastologia": [
          "mama","fibroadenoma","cisto de mama","descarga papilar","papiloma intraductal",
          "microcalcificacao mama","birads","biopsia de mama","cancer de mama",
          "mastectomia","carcinoma ductal in situ","carcinoma lobular",
        ],
        "Endometriose e Patologias Uterinas": [
          "endometriose","adenomiose","focos endometriosicos","endometrioma",
          "mioma uterino","leiomioma","miomectomia","embolizacao mioma",
          "histerectomia","cisto ovariano","cirurgia laparoscopica ginecol",
        ],
      },
    },

  }, # end temas G&O
}, # end G&O

# ══════════════════════════════════════════════════════════════
"Medicina Preventiva": {
  "area_kw": [
    "saude publica","saude coletiva","medicina preventiva","epidemiologia",
    "sus","sistema unico saude","atencao primaria","aps","esf",
    "saude do trabalhador","vigilancia epidemiologica","bioestatistica",
    "indicadores de saude","politica de saude","medicina de familia",
    "processo saude doenca",
  ],
  "default_tema": "Epidemiologia",
  "temas": {

    "Epidemiologia": {
      "kw": [
        "estudo epidemiologico","coorte","caso-controle","transversal","ecologico",
        "ensaio clinico","randomizado","rct","metanalise","revisao sistematica",
        "incidencia","prevalencia","taxa de ataque","periodo de incubacao",
        "coeficiente de mortalidade","mortalidade infantil","mortalidade materna",
        "razao mortalidade","swaroop","esperanca de vida","transicao epidemiologica",
        "transicao demografica","indicadores saude","morbidade",
        "odds ratio","risco relativo","razao prevalencia","risco atribuivel",
        "nnt","nnh","reducao risco absoluto","rra","reducao risco relativo",
        "intervalo de confianca","ic 95","valor p","teste hipotese",
        "sensibilidade","especificidade","valor preditivo positivo","vpp",
        "valor preditivo negativo","vpn","curva roc","acuracia",
        "rastreamento populacional","screening","validade","confiabilidade",
        "viés","confundimento","causalidade","criterios de hill",
        "surto","epidemia","pandemia","curva epidemica",
        "investigacao epidemiologica","hipotese epidemiologica",
        "vigilancia epidemiologica","sinan","notificacao compulsoria",
        "bioestatistica","distribuicao normal","media","mediana","desvio padrao",
        "qui-quadrado","qui quadrado","teste t","mann-whitney","kappa",
        "processo saude doenca","historia natural doenca","iceberg epidemiol",
      ],
      "default_sub": "Epidemiologia e Bioestatística",
      "subtopicos": {
        "Tipos de Estudos e Delineamentos": [
          "estudo coorte","caso-controle","estudo transversal","ecologico",
          "ensaio clinico randomizado","rct","metanalise","revisao sistematica",
          "nivel de evidencia","ebc","delineamento estudo","estudo observacional",
        ],
        "Medidas de Associação e Bioestatística": [
          "odds ratio","risco relativo","razao prevalencia","nnt","risco atribuivel",
          "intervalo de confianca","ic 95","valor p","teste hipotese",
          "qui-quadrado","teste t","mann-whitney","kappa","poder estatistico",
          "bioestatistica","media","mediana","desvio padrao",
        ],
        "Epidemiologia e Bioestatística": [
          "sensibilidade","especificidade","vpp","vpn","curva roc",
          "rastreamento populacional","screening","prevalencia","incidencia",
          "processo saude doenca","historia natural doenca","indicadores saude",
          "coeficiente mortalidade","mortalidade infantil","mortalidade materna",
          "swaroop","transicao epidemiologica",
        ],
        "Vigilância e Investigação Epidemiológica": [
          "vigilancia epidemiologica","notificacao compulsoria","sinan","sinasc","sim",
          "surto","epidemia","pandemia","investigacao epidemiologica",
          "curva epidemica","cadeia de transmissao","medidas controle surto",
        ],
      },
    },

    "Saúde do Trabalhador": {
      "kw": [
        "saude do trabalhador","doenca ocupacional","acidente de trabalho",
        "cat","comunicacao acidente trabalho","nexo causal","nexo tecnico",
        "ler","dort","lesao esforco repetitivo","disturbio osteomusc",
        "pair","perda auditiva induzida por ruido","ruido ocupacional",
        "pneumoconiose","silicose","asbestose","bissinose","beriliose",
        "insalubridade","periculosidade","adicional","nr ","norma regulamentadora",
        "pcmso","ppra","ppgrss","sesmt","cipa","sipat",
        "estresse ocupacional","burnout","sindrome esgotamento",
        "dermatose ocupacional","cancer ocupacional",
        "equipamento protecao individual","epi","epc",
        "reintegraçao trabalho","reducao danos ocupacional",
      ],
      "default_sub": "LER/DORT e Doenças Ocupacionais",
      "subtopicos": {
        "LER/DORT e Doenças Ocupacionais": [
          "ler","dort","lesao esforco repetitivo","disturbio osteomusc",
          "pair","silicose","asbestose","pneumoconiose","bissinose",
          "doenca ocupacional","nexo causal","cat","acidente trabalho",
        ],
        "Legislação e Saúde Ocupacional": [
          "insalubridade","periculosidade","nr ","norma regulamentadora",
          "pcmso","ppra","sesmt","cipa","sipat","epi",
          "readaptacao profissional","aposentadoria especial","previdencia social",
        ],
      },
    },

    "Atenção Primária": {
      "kw": [
        "atencao primaria","aps","esf","estrategia saude familia","nasf","pnab",
        "unidade basica saude","ubs legislacao","equipe saude familia",
        "agente comunitario","territorio","adscrição","microarea",
        "atributo aps","longitudinalidade","porta de entrada","coordenacao cuidado",
        "integralidade aps","vínculo","responsabilizacao",
        "sus","sistema unico saude","principios sus","universalidade","equidade",
        "lei 8080","lei 8142","decreto 7508","nob","noas","norma operacional",
        "financiamento sus","bloco financiamento","previne brasil",
        "conferencia saude","conselho saude","participacao social","controle social",
        "rede atencao saude","ras","regionalizacao","hierarquizacao","sus referencia",
        "politica nacional","programa nacional saude","politica publica saude",
        "rastreamento cancer","screening cancer aps","mamografia sus",
        "niveis de prevencao","leavell clark","prevencao primaria","prevencao secundaria",
        "prevencao terciaria","prevencao quaternaria",
        "violencia domestica notificacao","notificacao compulsoria aps",
        "visita domiciliar","atencao domiciliar",
      ],
      "default_sub": "Organização da APS, ESF e SUS",
      "subtopicos": {
        "Organização da APS, ESF e SUS": [
          "atencao primaria","aps","esf","estrategia saude familia","nasf",
          "equipe saude familia","agente comunitario","territorio",
          "atributo aps","longitudinalidade","porta de entrada",
          "rede atencao saude","ras","regionalizacao","hierarquizacao",
          "visita domiciliar","atencao domiciliar",
          "lei 8080","lei 8142","decreto 7508","nob","noas","norma operacional",
          "universalidade","equidade","integralidade sus","principios sus",
          "sistema unico saude","financiamento sus","bloco financiamento",
          "previne brasil","controle social","conselho saude","conferencia saude",
          "sus ","sus.","universal","equitativo",
        ],
        "Rastreamento e Níveis de Prevenção": [
          "rastreamento cancer","mamografia sus","papanicolaou sus","colonoscopia sus",
          "rastreamento mamario","rastreamento cervical","rastreamento colorretal",
          "niveis de prevencao","leavell clark","prevencao primaria","prevencao secundaria",
          "prevencao terciaria","prevencao quaternaria","promocao saude",
          "sobrediagnostico","medicalizacao","rastreamento populacional",
          "teste de rastreamento","sensibilidade especificidade rastreamento",
        ],
        "Violência e Notificação Compulsória na APS": [
          "violencia domestica","violencia contra mulher","notificacao compulsoria aps",
          "sinan aps","maus-tratos notificacao","violencia sexual notificacao",
          "notificacao de doenca","doenca de notificacao","agravo notificavel",
        ],
      },
    },

    "Medicina de Família": {
      "kw": [
        "medico de familia","medicina de familia","medicina de familia e comunidade",
        "mccp","metodo clinico centrado","abordagem centrada pessoa",
        "genograma","ecomapa","familiograma","ciclo vida familiar",
        "dinamica familiar","disfuncao familiar","crise familiar",
        "abordagem familiar","visita domiciliar familiar",
        "projeto terapeutico singular","pts","plano terapeutico",
        "apoio matricial","matriciamento","clinica ampliada",
        "multiprofissional","interprofissional","colaboracao interdisciplinar",
        "acolhimento","acolhimento com classificacao risco",
        "consulta compartilhada","interconsulta","referencia contrarreferencia",
        "etapy de prochaska","motivacional","aconselhamento breve",
        "ética médica","cfm","codigo de etica medica","sigilo medico",
        "consentimento informado","autonomia","beneficência","nao maleficencia",
        "justia bioética","bioetica","principios bioética",
        "starfield","mcwhinney","wonca",
        "saude mental na aps","transtorno mental comum","apoio psicossocial",
        "caps","raps","rede atencao psicossocial",
      ],
      "default_sub": "Medicina de Família e MCCP",
      "subtopicos": {
        "Medicina de Família e MCCP": [
          "medico de familia","mccp","metodo clinico centrado","abordagem centrada",
          "genograma","ecomapa","ciclo vida familiar","abordagem familiar",
          "projeto terapeutico singular","pts","apoio matricial","matriciamento",
          "starfield","mcwhinney","wonca","consulta compartilhada",
        ],
        "Ética Médica e Bioética": [
          "etica medica","cfm","codigo de etica medica","sigilo medico",
          "consentimento informado","autonomia","beneficencia","nao maleficencia",
          "justica bioetica","bioetica","principios bioética","erro medico",
          "ma pratica","responsabilidade medica","relacao medico-paciente",
        ],
        "Saúde Mental na APS e RAPS": [
          "saude mental na aps","transtorno mental comum","apoio psicossocial",
          "caps","raps","rede atencao psicossocial","desinstitucional",
          "reforma psiquiatrica","leito saude mental","crise mental aps",
          "interconsulta psiquiatrica","apoio matricial saude mental",
        ],
      },
    },

    "Sistemas de Informação": {
      "kw": [
        "sinan","sim","sinasc","sisprenatal","sia","sih","datasus",
        "e-sus","rnds","cnes","prontuario eletronico",
        "sistema informacao saude","tecnologia informacao saude",
        "registro de obito","declaracao nascido vivo","dnv",
        "dn","declaracao obito","do ","causa basica morte",
        "cid-10","classificacao internacional doencas",
        "dados epidemiologicos","banco de dados saude",
        "vigilancia sanitaria","anvisa","visa","rdc",
        "farmacovigilancia","tecnovigilancia","hemovigilancia",
        "notificacao adverso","evento adverso medicamento",
      ],
      "default_sub": "Sistemas de Informação em Saúde",
      "subtopicos": {
        "Sistemas de Informação em Saúde": [
          "sinan","sim","sinasc","sisprenatal","sia","sih","datasus",
          "e-sus","rnds","cnes","prontuario eletronico",
          "registro de obito","declaracao nascido vivo","cid-10",
          "causa basica morte","notificacao compulsoria sistema",
        ],
        "Vigilância Sanitária e Farmacovigilância": [
          "vigilancia sanitaria","anvisa","visa","rdc",
          "farmacovigilancia","tecnovigilancia","hemovigilancia",
          "notificacao adverso","evento adverso medicamento",
          "fiscalizacao sanitaria","inspecao sanitaria",
        ],
      },
    },

  }, # end temas Preventiva
}, # end Medicina Preventiva

} # end CLASSIFICATION dict C

# ─────────────────────────────────────────────────────────────
# SCORING ENGINE
# ─────────────────────────────────────────────────────────────
def _score(text_norm, kw_list):
    return sum(len(k) for k in kw_list if k in text_norm)

def classify(question_text, options):
    t = norm(question_text + " " + " ".join(options))

    # Step 1: grande_area
    area_scores = {a: _score(t, cfg["area_kw"]) for a, cfg in C.items()}
    # Also score all tema keywords per area to break ties
    for area, cfg in C.items():
        for tema_cfg in cfg["temas"].values():
            area_scores[area] += _score(t, tema_cfg["kw"]) * 0.3  # partial weight
    grande_area = max(area_scores, key=area_scores.get)
    if area_scores[grande_area] == 0:
        grande_area = "Clínica Médica"  # absolute fallback

    # Step 2: tema_principal
    temas = C[grande_area]["temas"]
    tema_scores = {tema: _score(t, cfg["kw"]) for tema, cfg in temas.items()}
    best_tema_score = max(tema_scores.values())
    if best_tema_score == 0:
        tema_principal = C[grande_area]["default_tema"]
    else:
        tema_principal = max(tema_scores, key=tema_scores.get)

    # Step 3: subtopico
    tema_cfg = temas[tema_principal]
    sub_scores = {sub: _score(t, kws) for sub, kws in tema_cfg["subtopicos"].items()}
    best_sub_score = max(sub_scores.values()) if sub_scores else 0
    if best_sub_score == 0:
        subtopico = tema_cfg["default_sub"]
    else:
        subtopico = max(sub_scores, key=sub_scores.get)

    return grande_area, tema_principal, subtopico

# ─────────────────────────────────────────────────────────────
# GABARITO PARSER
# ─────────────────────────────────────────────────────────────
def parse_gabarito(path):
    """Return dict {question_number: answer_letter}.
    Handles three formats:
      1. Row-table: 'Questão 1 2 3 ...' / 'Gabarito A B C ...'  (2011+, most editions)
      2. Pair:      '1. A' / '1: A' / '1 A'                     (older single-column)
      3. PDF table: pdfplumber table cells N → A
    """
    if not path or not path.exists():
        return {}
    answers = {}
    try:
        with pdfplumber.open(path) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)

        # Format 1: row table (most common from 2011 onwards)
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if re.match(r'Questão\s+\d', line, re.IGNORECASE):
                nums = [int(n) for n in re.findall(r'\d+', line) if 1 <= int(n) <= 120]
                # Next non-empty line should be the Gabarito row
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and re.match(r'Gabarito\s+', lines[j], re.IGNORECASE):
                    letters = re.findall(r'[A-E]', lines[j])
                    for idx, n in enumerate(nums):
                        if idx < len(letters):
                            answers[n] = letters[idx]

        # Format 2: individual "N. A" pairs (older single-column gabaritos)
        if not answers:
            for m in re.finditer(r'\b(\d{1,3})\s*[\.:\-]?\s*([A-E])\b', text):
                n = int(m.group(1))
                if 1 <= n <= 120:
                    answers[n] = m.group(2)

        # Format 3: pdfplumber table extraction
        if not answers:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    for table in (page.extract_tables() or []):
                        for row in table:
                            if not row: continue
                            for k, cell in enumerate(row):
                                if cell and re.match(r'^\d{1,3}$', str(cell).strip()):
                                    n = int(cell.strip())
                                    if 1 <= n <= 120 and k + 1 < len(row):
                                        nxt = str(row[k + 1] or "").strip()
                                        if re.match(r'^[A-E]$', nxt):
                                            answers[n] = nxt
    except Exception as e:
        print(f"  [GABARITO ERR] {path.name}: {e}")
    return answers

# ─────────────────────────────────────────────────────────────
# QUESTION EXTRACTOR
# ─────────────────────────────────────────────────────────────
def _extract_text_columns(path):
    """Extract text from PDF handling 2-column layout. Returns (raw_text, norm_text)."""
    pages_raw = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            w, h = page.width, page.height
            left  = page.crop((0, 0, w * 0.5, h)).extract_text() or ""
            right = page.crop((w * 0.5, 0, w, h)).extract_text() or ""
            if left.strip() and right.strip():
                pages_raw.append(left + "\n" + right)
            else:
                pages_raw.append(page.extract_text() or "")
    raw = "\n".join(pages_raw)
    return raw, norm(raw)


_FULL_OPT = re.compile(r'^\(?([A-E])[)\.\s](.+)$')    # "A) text", "(A) text", "A text"
_SOLO_OPT = re.compile(r'^([A-E])\s*$')               # single letter "A" alone
_HDR_LINE  = re.compile(r'^(REVALIDA|EXAME NACIONAL|Prova (Cinza|Vermelha)|[0-9]{4}$)', re.I)


def _find_options(lines_raw):
    """
    Find A-E options in multiple formats:
      - "A) text"  / "A text"  (standard)
      - "A"  followed by text on the next line(s)   (2015 style)
      - Multiline option where text wraps to next line(s) (2021 style)
    Returns (text_lines, option_list) where options are "X) normalized_text".
    """
    # Collect candidate option header positions
    # Each entry: (line_index, letter, inline_text_or_empty)
    headers = []
    for i, line in enumerate(lines_raw):
        m = _FULL_OPT.match(line)
        if m:
            headers.append((i, m.group(1), m.group(2).strip()))
            continue
        m = _SOLO_OPT.match(line)
        if m:
            headers.append((i, m.group(1), ""))

    # Need at least A and one other letter
    letters_found = {lt for _, lt, _ in headers}
    if len(letters_found) < 2:
        return lines_raw, []

    # Find the earliest 'A' header
    a_headers = [(i, lt, tx) for i, lt, tx in headers if lt == 'A']
    if not a_headers:
        return lines_raw, []

    opt_start = a_headers[0][0]
    text_lines = lines_raw[:opt_start]

    # Build options: for each header, gather its continuation until next header
    relevant = sorted([(i, lt, tx) for i, lt, tx in headers if i >= opt_start],
                      key=lambda x: x[0])

    options = []
    for j, (i, letter, inline) in enumerate(relevant):
        next_i = relevant[j + 1][0] if j + 1 < len(relevant) else len(lines_raw)
        parts = [inline] if inline else []
        for k in range(i + 1, next_i):
            l = lines_raw[k]
            if _HDR_LINE.match(l):
                break
            if _FULL_OPT.match(l) or _SOLO_OPT.match(l):
                break
            parts.append(l)
        content = norm(" ".join(p for p in parts if p)).strip()
        if content:
            options.append(f"{letter}) {content}")

    # Require at least 3 valid options with content
    if len(options) < 3:
        return lines_raw, []

    return text_lines, options


def extract_questions(exam):
    """Extract list of question dicts from prova PDF."""
    path = exam["prova"]
    if not path or not path.exists():
        print(f"  [SKIP] {exam['edition']} -- prova nao encontrada: {path}")
        return []

    print(f"  [READ] {exam['edition']} -- {path.name}")
    try:
        raw_text, n_text = _extract_text_columns(path)
    except Exception as e:
        print(f"  [ERR] {path.name}: {e}")
        return []

    # Find question block start positions using normalized text (handles encoding issues)
    positions = []
    for m in re.finditer(r'questao\s+(\d{1,3})\b', n_text):
        q_num = int(m.group(1))
        if 1 <= q_num <= 120:
            positions.append((m.start(), q_num))
    for m in re.finditer(r'\b(\d{1,3})\s+questao\b', n_text):
        q_num = int(m.group(1))
        existing_positions = {p for p, _ in positions}
        if 1 <= q_num <= 120 and m.start() not in existing_positions:
            positions.append((m.start(), q_num))

    if not positions:
        print(f"  [WARN] Sem marcadores questao -- fallback numerico")
        for m in re.finditer(r'(?m)^\s*(\d{1,3})\s*$', n_text):
            q_num = int(m.group(1))
            if 1 <= q_num <= 120:
                positions.append((m.start(), q_num))

    if not positions:
        print(f"  [FAIL] Sem questoes em {path.name}")
        return []

    positions.sort()

    # Build same positions in raw_text by finding raw markers
    # We map norm_pos -> raw_pos using a ratio approximation, then search nearby
    raw_len = len(raw_text)
    norm_len = len(n_text) if n_text else 1

    raw_positions = []
    # Search raw text for question markers using permissive regex
    raw_markers = {}
    for m in re.finditer(r'QUEST[^\d\n]{0,10}(\d{1,3})\b', raw_text, re.IGNORECASE):
        q_num = int(m.group(1))
        if 1 <= q_num <= 120 and q_num not in raw_markers:
            raw_markers[q_num] = m.start()
    for m in re.finditer(r'\b(\d{1,3})\s+QUEST[^\s\d]{0,10}\b', raw_text, re.IGNORECASE):
        q_num = int(m.group(1))
        if 1 <= q_num <= 120 and q_num not in raw_markers:
            raw_markers[q_num] = m.start()

    if raw_markers:
        # Use raw positions if available
        raw_positions = sorted((pos, q_num) for q_num, pos in raw_markers.items())
    else:
        # Fallback: use norm positions mapped to raw by ratio
        ratio = raw_len / norm_len if norm_len else 1.0
        raw_positions = [(int(p * ratio), q) for p, q in positions]

    # Slice raw_text into question blocks and extract
    questions = []
    for i, (pos, q_num) in enumerate(raw_positions):
        end = raw_positions[i + 1][0] if i + 1 < len(raw_positions) else raw_len
        blk = raw_text[pos:end]

        lines_raw = [l.strip() for l in blk.splitlines() if l.strip()]
        # Drop question header lines
        lines_raw = [l for l in lines_raw
                     if not re.match(r'QUEST', l, re.I)
                     and not re.match(r'^\d+\s+QUEST', l, re.I)
                     and not re.match(r'^\d+\.\s+ITEM', l, re.I)]

        text_lines_raw, options = _find_options(lines_raw)

        # Normalize text for storage (remove accents for consistency with old data)
        q_text = norm(" ".join(text_lines_raw)).strip()
        # Normalize option content too
        options = [f"{o[0]}) {norm(o[3:])}" for o in options if len(o) > 3]

        if len(q_text) < 20 or len(options) < 2:
            continue

        questions.append({
            "q_num":        q_num,
            "questionText": q_text,
            "options":      options,
        })

    return questions

# ─────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("REVALIDA INEP — PIPELINE v6  (3 Níveis, Sem Catch-All)")
    print("=" * 65)

    all_questions = []
    edition_counts = {}
    revisao_manual = []

    for exam in EXAMS:
        edition = exam["edition"]
        year    = exam["year"]

        # Check if PDF exists
        if not exam["prova"] or not exam["prova"].exists():
            print(f"\n[SKIP] {edition} — arquivo não encontrado")
            revisao_manual.append({"edition": edition, "motivo": "PDF não encontrado"})
            continue

        print(f"\n[EXAM] {edition}")
        gabarito = parse_gabarito(exam["gabarito"])
        # Merge with manual/OCR overrides (fills gaps or replaces if PDF gave 0)
        if edition in _manual_gabaritos:
            manual = _manual_gabaritos[edition]
            if not gabarito:
                gabarito = manual
                print(f"  [GAB_MAN] Usando gabarito manual ({len(gabarito)} respostas)")
            else:
                before = len(gabarito)
                for q, a in manual.items():
                    if q not in gabarito:
                        gabarito[q] = a
                print(f"  [GAB_MAN] +{len(gabarito)-before} respostas do gabarito manual")
        print(f"  [GAB]  {len(gabarito)} respostas carregadas")

        raw = extract_questions(exam)
        print(f"  [EXT]  {len(raw)} questões extraídas")

        if len(raw) < 10:
            revisao_manual.append({"edition": edition, "motivo": f"Apenas {len(raw)} questões extraídas"})

        count = 0
        for q in raw:
            q_num = q["q_num"]
            correct = gabarito.get(q_num, "")

            grande_area, tema_principal, subtopico = classify(
                q["questionText"], q["options"]
            )

            qid = f"{edition}-q{q_num:03d}"
            all_questions.append({
                "id":            qid,
                "examRef":       edition,
                "year":          year,
                "questionNumber": q_num,
                "grande_area":   grande_area,
                "tema_principal": tema_principal,
                "subtopico":     subtopico,
                "questionText":  q["questionText"],
                "options":       q["options"],
                "correctAnswer": correct,
                "revisao_manual": not bool(correct),
            })
            count += 1

        edition_counts[edition] = count
        print(f"  [OK]   {count} questões classificadas")

    # ── Write questoes_db.json ──
    with open(OUT_DB, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
    print(f"\n[OUT] {OUT_DB.name}  ({len(all_questions)} questões)")

    # ── Generate estatisticas_temas.json ──
    stats = {}
    total = len(all_questions)

    for area in C.keys():
        area_qs = [q for q in all_questions if q["grande_area"] == area]
        area_n  = len(area_qs)
        area_pct = round(100 * area_n / total, 2) if total else 0

        temas_stat = {}
        for tema in C[area]["temas"].keys():
            tema_qs = [q for q in area_qs if q["tema_principal"] == tema]
            tema_n  = len(tema_qs)
            if not tema_n: continue

            sub_counts = Counter(q["subtopico"] for q in tema_qs)
            top_subs = [
                {"subtopico": s, "count": c, "pct_dentro_tema": round(100*c/tema_n,1)}
                for s, c in sub_counts.most_common(10)
            ]
            by_edition = Counter(q["examRef"] for q in tema_qs)

            temas_stat[tema] = {
                "count": tema_n,
                "pct_dentro_area": round(100 * tema_n / area_n, 2) if area_n else 0,
                "pct_total": round(100 * tema_n / total, 2) if total else 0,
                "top_subtopicos": top_subs,
                "por_edicao": dict(sorted(by_edition.items())),
            }

        stats[area] = {
            "count": area_n,
            "pct_total": area_pct,
            "temas": temas_stat,
        }

    stats["_meta"] = {
        "total_questoes": total,
        "edicoes": edition_counts,
        "revisao_manual": revisao_manual,
    }

    with open(OUT_STAT, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"[OUT] {OUT_STAT.name}")

    # ── Summary ──
    print(f"\n{'='*65}")
    print("DISTRIBUIÇÃO FINAL")
    print(f"{'='*65}")
    for area, s in stats.items():
        if area.startswith("_"): continue
        print(f"  {area:<30} {s['count']:>4} q  ({s['pct_total']:.1f}%)")
        for tema, ts in s["temas"].items():
            print(f"    +- {tema:<28} {ts['count']:>3} q  ({ts['pct_dentro_area']:.1f}% area)")
    print(f"\n  TOTAL: {total} questões")
    if revisao_manual:
        print(f"\n[REVISAO MANUAL] {len(revisao_manual)} itens:")
        for r in revisao_manual:
            print(f"  - {r['edition']}: {r['motivo']}")
    print("\n[DONE] Pipeline v6 concluído.")

if __name__ == "__main__":
    main()
