"""
Extract questions from Revalida INEP PDFs and classify by area + subtopic.
v5 — Column-order fix, OCR fallback, 15+ new classification rules, reduced unclassified gap.
"""
import pdfplumber, json, os, re, sys, unicodedata
from pathlib import Path

PDF_DIR = Path(__file__).parent.parent / "data" / "pdfs"
OUT_FILE = Path(__file__).parent.parent / "data" / "extracted_questions.json"

def normalize(text):
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    return nfkd.encode('ASCII', 'ignore').decode('ASCII').lower()

# ============================================================
# CLASSIFICATION RULES (v4 — expanded, de-biased)
# ============================================================
RULES = [
    # ==================== MEDICINA PREVENTIVA ====================
    {"area": "Med. Preventiva", "topicId": "prev-01",
     "subtopic": "Prevencao Quaternaria e Medicalizacao Excessiva",
     "kw": ["prevencao quaternaria", "prevencao quartenaria",
            "sobrediagnostico", "sobre-diagnostico", "sobretratamento", "sobre-tratamento",
            "medicalizacao", "disease mongering", "iatrogenia", "cuidado excessivo",
            "exame desnecessario", "exames desnecessarios", "tratamento desnecessario",
            "intervencao desnecessaria", "check-up completo", "check up completo",
            "exames de rotina sem", "solicitar diversos exames"]},

    {"area": "Med. Preventiva", "topicId": "prev-01",
     "subtopic": "Niveis de Prevencao (Primario, Secundario, Terciario, Quaternario)",
     "kw": ["nivel de prevencao", "niveis de prevencao", "prevencao primaria",
            "prevencao secundaria", "prevencao terciaria", "prevencao quaternaria",
            "leavell e clark", "leavell", "prevencao primordial",
            "promocao da saude", "promocao de saude",
            "protecao especifica", "diagnostico precoce",
            "limitacao do dano", "limitacao da incapacidade", "reabilitacao",
            "classificacao de leavell", "esquema de leavell",
            "modelo de leavell", "fases de leavell"]},

    {"area": "Med. Preventiva", "topicId": "prev-01",
     "subtopic": "Rastreamento de Cancer (Mama, Colo Uterino, Colorretal, Prostata)",
     "kw": ["mamografia", "rastreamento mamografico", "rastreamento de mama",
            "rastreamento do cancer de mama", "rastreamento de cancer de colo",
            "rastreamento do cancer colorretal", "rastreamento do cancer de prostata",
            "rastreamento de cancer", "screening cancer",
            "papanicola", "colpocitologia", "citologia oncotica", "preventivo ginecologico",
            "sangue oculto nas fezes", "psof", "psofi", "colonoscopia de rastreio",
            "colonoscopia para rastreamento", "psa", "toque retal", "antigeno prostatico",
            "screening de cancer", "diretrizes do inca", "inca", "diretriz do inca",
            "rastreamento populacional", "tomografia de baixa dose"]},

    {"area": "Med. Preventiva", "topicId": "prev-01",
     "subtopic": "Rastreamento de Doencas Cronicas (HAS, DM, Dislipidemia)",
     "kw": ["rastreamento de diabetes", "rastreamento de hipertensao",
            "rastreamento de dislipidemia", "rastreamento da has",
            "rastreamento da hipertensao", "rastreamento de dm",
            "glicemia de jejum", "glicemia em jejum", "hemoglobina glicada",
            "perfil lipidico", "ldl colesterol", "hdl colesterol",
            "colesterol total", "trigliceride", "rastreio de diabetes",
            "rastreio de hipertensao", "prevencao cardiovascular",
            "escore de risco cardiovascular", "framingham",
            "check-up", "check up", "rastreamento de doenca cronica",
            "imc 28", "sobrepeso assintomatico"]},

    {"area": "Med. Preventiva", "topicId": "prev-01",
     "subtopic": "Aconselhamento (Tabagismo, Alcool, TCC, Entrevista Motivacional)",
     "kw": ["cessacao tabagica", "cessacao do tabagismo", "tratamento do tabagismo",
            "tratamento do fumante", "abordagem do tabagismo", "abordagem do fumante",
            "nicotina", "reposicao de nicotina", "trn", "tnr",
            "bupropiona", "vareniclina", "adesivo de nicotina",
            "etilismo", "abuso de alcool", "abuso de drogas",
            "aconselhamento breve", "aconselhamento intensivo",
            "abordagem motivacional", "entrevista motivacional",
            "terapia cognitivo comportamental", "tcc",
            "audit-c", "audit c", "cage",
            "atividade fisica recomendada", "minutos de atividade",
            "150 minutos", "75 minutos vigorosa",
            "estagios de mudanca", "prochaska"]},

    # SUS - Leis (very specific keywords)
    {"area": "Med. Preventiva", "topicId": "prev-04",
     "subtopic": "Leis Organicas (8080/90 e 8142/90) e Decreto 7508/2011",
     "kw": ["lei 8.080", "lei 8080", "lei 8.142", "lei 8142", "decreto 7508",
            "lei organica", "campo de atuacao SUS", "competencia SUS",
            "NOB", "NOAS", "Norma Operacional", "diretrizes SUS"]},

    # SUS - Financiamento
    {"area": "Med. Preventiva", "topicId": "prev-04",
     "subtopic": "Financiamento (EC 95, Blocos, Previne Brasil) e Controle Social",
     "kw": ["financiamento SUS", "bloco financiamento", "Previne Brasil",
            "emenda constitucional 95", "fundo saude", "orcamento saude",
            "conferencia saude", "conselho de saude", "participacao social"]},

    # SUS - RAS / APS (NO "UBS" or "unidade basica" — they're just narrative setting)
    {"area": "Med. Preventiva", "topicId": "prev-04",
     "subtopic": "Redes de Atencao a Saude (RAS) e Regionalizacao",
     "kw": ["rede de atencao a saude", "rede de atencao", "regionalizacao",
            "hierarquizacao", "atencao primaria a saude",
            "ESF", "estrategia saude da familia",
            "NASF", "PNAB", "atributo APS",
            "territorializacao", "eSF", "equipe saude familia",
            "agente comunitario", "microarea", "area adstrita", "adscricao"]},

    # SUS - Principios
    {"area": "Med. Preventiva", "topicId": "prev-04",
     "subtopic": "Principios Doutrinarios (Universalidade, Equidade, Integralidade)",
     "kw": ["universalidade", "equidade", "integralidade",
            "sistema unico de saude", "direito a saude", "principio do SUS",
            "planejaSUS", "controle social"]},

    # APS / MCCP (specific tools and concepts)
    {"area": "Med. Preventiva", "topicId": "prev-03",
     "subtopic": "Atencao Primaria — MCCP, Genograma, Ecomapa, PTS, Matriciamento",
     "kw": ["mccp", "metodo clinico centrado",
            "genograma", "ecomapa", "ciclo de vida familiar",
            "abordagem familiar", "famililograma",
            "projeto terapeutico singular", "pts",
            "apoio matricial", "matriciamento",
            "clinica ampliada", "acolhimento com classificacao",
            "equipe multiprofissional", "atributos da aps",
            "atributo essencial", "atributo derivado",
            "porta de entrada do sistema", "longitudinalidade",
            "coordenacao do cuidado",
            "starfield", "mcwhinney"]},

    # Atencao Domiciliar / VD (separate — specific to home-based care)
    {"area": "Med. Preventiva", "topicId": "prev-03",
     "subtopic": "Atencao Domiciliar e Visita Domiciliar (VD, Cuidador, Idoso Acamado)",
     "kw": ["visita domiciliar", "atencao domiciliar",
            "paciente acamado", "idoso acamado",
            "cuidador domiciliar", "cuidados domiciliares",
            "internacao domiciliar", "melhor em casa",
            "atencao a saude no domicilio", "domicilio do paciente",
            "ficha de visita", "agente comunitario na visita"]},

    # Vigilancia
    {"area": "Med. Preventiva", "topicId": "prev-05",
     "subtopic": "Doencas de Notificacao Compulsoria (Imediata vs Semanal, SINAN)",
     "kw": ["notificacao compulsoria", "SINAN", "vigilancia epidemiologica",
            "doenca de notificacao", "agravo de notificacao",
            "notificacao imediata", "SIM", "SINASC", "notificar"]},

    {"area": "Med. Preventiva", "topicId": "prev-05",
     "subtopic": "Indicadores de Saude (Mortalidade, Morbidade, Swaroop-Uemura)",
     "kw": ["indicador saude", "coeficiente mortalidade", "taxa mortalidade", "morbidade",
            "Swaroop", "esperanca vida", "mortalidade infantil", "mortalidade materna",
            "razao mortalidade", "letalidade", "incidencia", "prevalencia",
            "sindemia", "transicao epidemiologica", "transicao demografica"]},

    {"area": "Med. Preventiva", "topicId": "prev-05",
     "subtopic": "Investigacao Epidemiologica de Surtos e Epidemias",
     "kw": ["surto", "epidemia", "pandemia", "investigacao epidemiologica",
            "curva epidemica", "vigilancia sanitaria", "barreira sanitaria",
            "controle de infeccao", "biosseguranca"]},

    # Epidemiologia
    {"area": "Med. Preventiva", "topicId": "prev-02",
     "subtopic": "Tipos de Estudos (Coorte, Caso-Controle, Transversal, Ensaio Clinico)",
     "kw": ["estudo coorte", "caso-controle", "estudo transversal", "ensaio clinico",
            "randomizado", "metanalise", "revisao sistematica", "delineamento estudo",
            "estudo ecologico", "estudo observacional", "estudo experimental",
            "follow-up", "seguimento", "longitudinal"]},

    {"area": "Med. Preventiva", "topicId": "prev-02",
     "subtopic": "Medidas de Associacao (RR, OR, RP, RAR, NNT)",
     "kw": ["risco relativo", "odds ratio", "razao prevalencia", "NNT", "NNH",
            "risco atribuivel", "intervalo confianca", "medida de associacao",
            "estatisticamente significante", "p valor", "IC 95",
            "razao de chance", "taxa de ataque"]},

    {"area": "Med. Preventiva", "topicId": "prev-02",
     "subtopic": "Sensibilidade, Especificidade, VPP, VPN, Curva ROC",
     "kw": ["sensibilidade", "especificidade", "valor preditivo", "VPP", "VPN",
            "curva ROC", "teste diagnostico", "acuracia", "razao verossimilhanca",
            "falso positivo", "falso negativo", "ponto de corte"]},

    # Saude do Trabalhador
    {"area": "Med. Preventiva", "topicId": "prev-06",
     "subtopic": "LER/DORT e Doencas Ocupacionais",
     "kw": ["LER", "DORT", "ocupacional", "trabalhador",
            "CAT", "nexo causal", "acidente trabalho", "NR-", "norma regulamentadora",
            "pneumoconiose", "PAIR", "silicose", "asbesto", "insalubridade",
            "periculosidade", "PCMSO", "PPRA", "saude do trabalhador"]},

    # ==================== GINECOLOGIA & OBSTETRICIA ====================
    {"area": "Ginecologia & Obstetricia", "topicId": "go-01",
     "subtopic": "Sifilis na Gestacao (VDRL, Teste Rapido, Penicilina Benzatina, Sifilis Congenita)",
     "kw": ["sifilis", "VDRL", "teste treponemico", "penicilina benzatina",
            "sifilis congenita", "cancro duro", "sifilis gestacao",
            "sifilis materna", "neurossifilis"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-01",
     "subtopic": "HIV/AIDS - Transmissao Vertical (AZT, Profilaxia, Parto, Aleitamento)",
     "kw": ["HIV", "AIDS", "transmissao vertical", "AZT", "antirretroviral", "TARV",
            "carga viral", "profilaxia HIV", "aleitamento HIV", "teste rapido HIV",
            "gestante HIV", "parto HIV"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-01",
     "subtopic": "Toxoplasmose Gestacional (IgG/IgM, Avidez, Espiramicina, Sulfadiazina)",
     "kw": ["toxoplasmose", "toxoplasma", "avidez IgG", "espiramicina",
            "sulfadiazina", "pirimetamina", "acido folinico"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-01",
     "subtopic": "Hepatites B e C na Gestacao (HBsAg, Imunoglobulina, Vacina)",
     "kw": ["hepatite B", "hepatite C", "HBsAg", "HBeAg", "imunoglobulina hepatite",
            "vacina hepatite", "transmissao vertical hepatite"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-01",
     "subtopic": "STORCH e Zika Virus na Gestacao",
     "kw": ["STORCH", "TORCH", "CMV", "citomegalovirus", "rubeola", "zika",
            "herpes gestacao", "varicela gestacao", "infeccao congenita", "microcefalia"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-02",
     "subtopic": "Rastreamento Cancer de Colo (Citopatologia, Periodicidade, Idade-alvo)",
     "kw": ["citopatologia", "colpocitologia", "preventivo ginecologico",
            "rastreamento colo", "screening cancer colo", "colposcopia",
            "HSIL", "LSIL", "ASC-US", "ASC-H", "AGC"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-02",
     "subtopic": "Vacina HPV (Quadrivalente, PNI, Indicacoes Ampliadas)",
     "kw": ["vacina HPV", "HPV quadrivalente", "imunizacao HPV",
            "papilomavirus humano", "vacinacao contra HPV"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-02",
     "subtopic": "NIC I/II/III - Manejo (Colposcopia, Biopsia, Conizacao, Histerectomia)",
     "kw": ["NIC I", "NIC II", "NIC III", "neoplasia intraepitelial cervical",
            "conizacao", "biopsia colo", "histerectomia", "CAF",
            "cirurgia de alta frequencia", "cone", "LEEP", "lesao intraepitelial"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-03",
     "subtopic": "Pre-eclampsia - Diagnostico, Classificacao, Criterios de Gravidade",
     "kw": ["pre-eclampsia", "pre eclampsia", "proteinuria", "doenca hipertensiva",
            "eclampsia", "convulsao gestante", "sulfato magnesio",
            "HELLP", "sindrome HELLP", "hipertensao arterial gestacao"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-04",
     "subtopic": "Mecanismo do Parto (Insinuacao, Descida, Rotacao, Desprendimento)",
     "kw": ["mecanismo parto", "insinuacao", "periodo parto", "partograma",
            "distocia", "trabalho parto", "inducao parto", "misoprostol",
            "ocitocina", "parto vaginal", "cesariana", "indicacao cesarea",
            "Robson", "parto normal", "parto humanizado"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-05",
     "subtopic": "Contraceptivos Orais Combinados e Progestagenos (Criterios OMS)",
     "kw": ["contracepcao", "contraceptivo", "anticoncepcional", "metodo contraceptivo",
            "DIU", "dispositivo intrauterino", "ligadura tubaria", "laqueadura",
            "vasectomia", "planejamento familiar", "implante contraceptivo",
            "injetavel contraceptivo", "pilula contraceptiva",
            "anticoncepcao emergencia", "categoria OMS"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-06",
     "subtopic": "Sangramento de 1a Metade (Abortamento, Gravidez Ectopica, Mola)",
     "kw": ["abortamento", "aborto", "gravidez ectopica", "mola hidatiforme",
            "sangramento primeiro trimestre", "ameaca aborto", "beta-hCG",
            "gestacao ectopica", "doenca trofoblastica"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-06",
     "subtopic": "Sangramento de 2a Metade (DPP, Placenta Previa, Rotura, Vasa Previa)",
     "kw": ["DPP", "placenta previa", "descolamento placenta", "rotura uterina",
            "vasa previa", "sangramento terceiro trimestre", "hemorragia gestacao",
            "acretismo", "placenta acreta"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-05",
     "subtopic": "Climaterio e Menopausa (Definicoes, Sintomas, Terapia Hormonal)",
     "kw": ["climaterio", "menopausa", "fogacho", "terapia hormonal",
            "THM", "sintomas vasomotores", "osteoporose pos-menopausa",
            "atrofia vaginal"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-05",
     "subtopic": "Sangramentos Uterinos Anormais (PALM-COEIN, Miomatose)",
     "kw": ["sangramento uterino anormal", "mioma", "miomatose", "PALM-COEIN",
            "polipo endometrial", "hiperplasia endometrial", "adenomiose",
            "endometrio"]},

    {"area": "Ginecologia & Obstetricia", "topicId": "go-05",
     "subtopic": "Endometriose e Dor Pelvica Cronica",
     "kw": ["endometriose", "dor pelvica", "dismenorreia", "infertilidade feminina",
            "ovario policistico", "SOP", "sindrome dos ovarios policisticos"]},

    # ==================== CIRURGIA GERAL (EXPANDED) ====================
    # Abdome Agudo
    {"area": "Cirurgia Geral", "topicId": "cir-01",
     "subtopic": "Abdome Agudo Inflamatorio (Apendicite, Colecistite, Pancreatite, Diverticulite)",
     "kw": ["apendicite", "Alvarado", "McBurney", "Blumberg",
            "abdome agudo inflamatorio", "pancreatite aguda", "diverticulite aguda",
            "Murphy", "fossa iliaca direita", "apendicectomia",
            "dor em fossa iliaca", "sinal de Blumberg", "sinal de Murphy",
            "descompressao dolorosa", "dor em hipocondrio direito",
            "colica biliar", "pancreatite", "amilase", "lipase",
            "Tokyo", "colecistolitiase", "abdome agudo"]},

    {"area": "Cirurgia Geral", "topicId": "cir-01",
     "subtopic": "Abdome Agudo Obstrutivo (Bridas, Volvo, Neoplasia, Hernia Encarcerada)",
     "kw": ["obstrucao intestinal", "abdome agudo obstrutivo", "brida",
            "volvo", "empilhamento moeda", "distensao abdominal",
            "parada eliminacao", "hernia encarcerada", "hernia estrangulada",
            "suboclusao intestinal", "aderencia", "laparotomia previa",
            "sem eliminar gases", "sem evacuar", "distensao",
            "hernia inguinal encarcerada"]},

    {"area": "Cirurgia Geral", "topicId": "cir-01",
     "subtopic": "Abdome Agudo Perfurativo (Ulcera Peptica, Diverticulo, Neoplasia)",
     "kw": ["abdome agudo perfurativo", "pneumoperitonio", "perfuracao intestinal",
            "ulcera perfurada", "peritonite", "sinal Jobert",
            "ar livre", "pneumoperitoneo", "ulcera gastrica",
            "ulcera duodenal", "perfuracao gastrica", "dor em barra"]},

    {"area": "Cirurgia Geral", "topicId": "cir-01",
     "subtopic": "Abdome Agudo Hemorragico e Isquemico/Vascular",
     "kw": ["abdome agudo hemorragico", "abdome agudo vascular",
            "isquemia mesenterica", "hemoperitonio",
            "rotura aneurisma", "aneurisma aorta",
            "aneurisma roto", "isquemia intestinal", "trombose mesenterica"]},

    # Trauma / ATLS
    {"area": "Cirurgia Geral", "topicId": "cir-02",
     "subtopic": "ATLS — Avaliacao Primaria e Secundaria (ABCDE) / Politrauma",
     "kw": ["ATLS", "ABCDE", "politraumatizado", "colar cervical", "prancha rigida",
            "cinematica trauma", "atendimento inicial trauma",
            "avaliacao primaria trauma", "avaliacao secundaria trauma",
            "trauma contuso", "trauma penetrante", "acidente automobilistico",
            "vitima de acidente", "colisao", "atropelamento",
            "capacete", "cinto seguranca", "extricacao",
            "hemorragia externa", "via aerea trauma", "escore Glasgow",
            "escala coma Glasgow", "pupila trauma", "choque hemorragico",
            "politrauma", "trauma cranioencefalico", "TCE",
            "trauma raquimedular", "TRM", "trauma de bacia"]},

    {"area": "Cirurgia Geral", "topicId": "cir-02",
     "subtopic": "Trauma Toracico (Pneumotorax Hipertensivo, Tamponamento, Drenagem)",
     "kw": ["pneumotorax", "hemotorax", "tamponamento cardiaco", "drenagem toracica",
            "dreno torax", "torax instavel", "contusao pulmonar", "trauma torax",
            "fratura costela", "enfisema subcutaneo", "dreno pleural",
            "selo agua", "toracotomia", "janela pericardica",
            "triade Beck", "turgência jugular", "abafamento bulhas",
            "desvio traqueia", "murmurio abolido", "timpanismo torax"]},

    {"area": "Cirurgia Geral", "topicId": "cir-02",
     "subtopic": "Trauma Abdominal (FAST, LPD, Laparotomia Exploradora)",
     "kw": ["FAST", "LPD", "lavado peritoneal", "ultrassom trauma",
            "liquido livre", "hemoperitonio", "ultrassonografia trauma",
            "laparotomia exploradora", "trauma abdominal",
            "trauma abdominal contuso", "trauma abdominal penetrante",
            "FAF", "ferimento arma fogo", "ferimento arma branca",
            "estocada", "facada", "baleado", "tiro"]},

    # Colecistite / Vias Biliares
    {"area": "Cirurgia Geral", "topicId": "cir-03",
     "subtopic": "Colecistite Aguda e Doencas das Vias Biliares (Tokyo, CPRE, Cirurgia)",
     "kw": ["colecistite", "litiase biliar", "calculo vesicula", "colecistectomia",
            "vesicula biliar", "colica biliar", "coledocolitiase", "colangite",
            "CPRE", "vias biliares", "ictericia obstrutiva", "coledoco",
            "sinal Murphy", "colecistectomia videolaparoscopica",
            "videolaparoscopica", "videolaparoscopia", "colangiopancreatografia"]},

    # Hemorragia Digestiva
    {"area": "Cirurgia Geral", "topicId": "cir-03",
     "subtopic": "Hemorragia Digestiva Alta e Baixa (Varizes, Ulcera, Diverticulo)",
     "kw": ["hemorragia digestiva", "hemorragia digestiva alta", "HDA",
            "hemorragia digestiva baixa", "hematemese", "melena",
            "enterorragia", "hematoquezia", "varizes esofagicas",
            "ligadura elastica", "escleroterapia",
            "octreotide", "terlipressina", "Blakemore", "Sengstaken"]},

    # Choque
    {"area": "Cirurgia Geral", "topicId": "cir-04",
     "subtopic": "Choque (Hipovolemico, Septico, Cardiogenico, Anafilatico)",
     "kw": ["choque hipovolemico", "choque septico", "choque cardiogenico",
            "choque anafilatico", "choque hemorragico", "choque",
            "hipoperfusao", "lactato elevado",
            "reposicao volemica", "cristaloide",
            "noradrenalina", "vasopressor", "droga vasoativa",
            "acesso venoso central", "PVC", "PAI",
            "hipotensao refrataria", "hipotensao persistente"]},

    # Queimaduras
    {"area": "Cirurgia Geral", "topicId": "cir-04",
     "subtopic": "Queimaduras (Classificacao, SCQ, Regra dos 9, Parkland, Tratamento)",
     "kw": ["queimadura", "SCQ", "regra dos 9", "Parkland",
            "superficie corporal queimada", "grau queimadura", "escarotomia",
            "hidratacao queimado", "Lund", "Browder",
            "queimado", "queimadura termica", "queimadura eletrica",
            "queimadura quimica", "inalacao fumaca", "carboxihemoglobina",
            "Ringer lactato", "grande queimado", "enxerto pele"]},

    # Hernias
    {"area": "Cirurgia Geral", "topicId": "cir-05",
     "subtopic": "Hernias da Parede Abdominal (Inguinal, Femoral, Umbilical, Incisional)",
     "kw": ["hernia inguinal", "hernia abdominal", "hernia femoral",
            "hernia umbilical", "hernioplastia", "hernia incisional",
            "tela cirurgica", "Lichtenstein", "Shouldice", "NYHUS",
            "anel inguinal", "regiao inguinal", "herniorrafia",
            "abaulamento", "manobra Valsalva",
            "redutivel", "encarcerada", "estrangulada",
            "hernia", "herniaria", "herniario"]},

    # Pre/Pos operatorio
    {"area": "Cirurgia Geral", "topicId": "cir-05",
     "subtopic": "Cuidados Pre e Pos-operatorios (Risco Cirurgico, Complicacoes, Feridas)",
     "kw": ["pre-operatorio", "pos-operatorio", "complicacao cirurgica",
            "infeccao sitio cirurgico", "profilaxia antibiotica cirurgia",
            "jejum pre-operatorio", "tromboprofilaxia",
            "avaliacao risco cirurgico", "ASA", "preparo colon",
            "dreno cirurgico", "deiscencia", "seroma", "hematoma",
            "infeccao ferida operatoria", "sutura", "fio sutura",
            "Mononylon", "categute", "Vicryl", "PDS", "Prolene"]},

    # Tumores Digestivos
    {"area": "Cirurgia Geral", "topicId": "cir-03",
     "subtopic": "Tumores do Aparelho Digestivo (Gastrico, Colorretal, Pancreas, Esofago)",
     "kw": ["cancer gastrico", "cancer colorretal", "cancer de pancreas",
            "cancer esofago", "tumor aparelho digestivo", "neoplasia colon",
            "adenocarcinoma gastrico", "CEA", "polipose", "Lynch", "FAP",
            "gastrectomia", "colectomia"]},

    # ==================== CLINICA MEDICA ====================
    {"area": "Clinica Medica", "topicId": "cli-01",
     "subtopic": "Tuberculose (Diagnostico — TRM-TB, ADA, Cultura; TTO — RIPE, ILTB)",
     "kw": ["tuberculose", "Mycobacterium tuberculosis", "bacilo alcool",
            "BAAR", "RIPE", "TRM-TB", "ILTB", "PPD", "cavitacao", "hemoptise",
            "rifampicina", "isoniazida", "pirazinamida", "etambutol", "meningite TB"]},

    {"area": "Clinica Medica", "topicId": "cli-01",
     "subtopic": "Hanseniase (Classificacao OMS e Madrid, PQT, Reacoes Hansenicas)",
     "kw": ["hanseniase", "lepra", "Mycobacterium leprae", "PQT", "dapsona",
            "rifampicina hanseniase", "reacao hansenica", "talidomida",
            "paucibacilar", "multibacilar", "Mitsuda", "lesao hipocromica"]},

    {"area": "Clinica Medica", "topicId": "cli-01",
     "subtopic": "Leptospirose (Sindrome de Weil, Penicilina G Cristalina)",
     "kw": ["leptospirose", "Leptospira", "sindrome Weil", "doenca rato",
            "ictericia febril", "hemorragia pulmonar leptospirose"]},

    {"area": "Clinica Medica", "topicId": "cli-01",
     "subtopic": "Meningites Bacterianas (Pneumococo, Meningococo, Haemophilus)",
     "kw": ["meningite", "meningococo", "pneumococo", "Haemophilus",
            "rigidez nuca", "liquor", "LCR", "ceftriaxona",
            "dexametasona meningite", "Kernig", "Brudzinski", "petequias",
            "Neisseria meningitidis", "Streptococcus pneumoniae"]},

    {"area": "Clinica Medica", "topicId": "cli-02",
     "subtopic": "Diabetes Mellitus — Diagnostico e Tratamento (Metformina, Insulina, GLP-1)",
     "kw": ["diabetes", "hiperglicemia", "glicemia", "metformina", "insulina",
            "GLP-1", "iSGLT2", "cetoacidose", "CAD", "EHH",
            "estado hiperglicemico", "hemoglobina glicada", "HbA1c",
            "pe diabetico", "retinopatia diabetica"]},

    {"area": "Clinica Medica", "topicId": "cli-02",
     "subtopic": "Doencas da Tireoide (Hipotireoidismo, Hipertireoidismo, Nodulos)",
     "kw": ["tireoide", "hipotireoidismo", "hipertireoidismo", "levotiroxina",
            "TSH", "T4 livre", "bocio", "nodulo tireoide", "doenca Graves",
            "Hashimoto", "tireoidite", "PTU", "metimazol", "propiltiouracil"]},

    {"area": "Clinica Medica", "topicId": "cli-02",
     "subtopic": "Doencas das Adrenais (Cushing, Addison, Feocromocitoma)",
     "kw": ["adrenal", "Cushing", "Addison", "feocromocitoma", "hipercortisolismo",
            "insuficiencia adrenal", "aldosterona", "cortisol"]},

    {"area": "Clinica Medica", "topicId": "cli-03",
     "subtopic": "Hipertensao Arterial Sistemica (Diagnostico, MAPA, MRPA, Tratamento)",
     "kw": ["hipertensao arterial", "HAS", "pressao arterial", "MAPA", "MRPA",
            "anti-hipertensivo", "IECA", "BRA", "bloqueador calcio", "diuretico",
            "hidroclorotiazida", "enalapril", "losartan", "anlodipino",
            "crise hipertensiva", "anti-hipertensiva"]},

    {"area": "Clinica Medica", "topicId": "cli-03",
     "subtopic": "Insuficiencia Cardiaca (Classificacao NYHA/ACC, IECA/BRA, Betabloqueador)",
     "kw": ["insuficiencia cardiaca", "ICC", "NYHA", "dispneia", "ortopneia",
            "turgência jugular", "estertores", "BNP", "fracao ejecao",
            "betabloqueador", "carvedilol", "digoxina", "espironolactona"]},

    {"area": "Clinica Medica", "topicId": "cli-03",
     "subtopic": "Sindromes Coronarianas Agudas (SCASST, IAMCSST, Antiagregacao)",
     "kw": ["infarto", "IAM", "angina", "SCA", "coronariana", "troponina",
            "eletrocardiograma", "supra ST", "AAS", "clopidogrel",
            "estreptoquinase", "angioplastia", "trombolitico",
            "dor precordial", "isquemia miocardio"]},

    {"area": "Clinica Medica", "topicId": "cli-03",
     "subtopic": "Arritmias (Fibrilacao Atrial — CHA2DS2-VASc, Anticoagulacao)",
     "kw": ["arritmia", "fibrilacao atrial", "anticoagulacao",
            "varfarina", "DOAC", "marca-passo", "bradicardia", "taquicardia",
            "flutter atrial", "sincope", "QT longo", "Torsades", "cardioversao"]},

    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Pneumonia Adquirida na Comunidade (CURB-65, PSI, Antibioticoterapia)",
     "kw": ["pneumonia", "PAC", "CURB-65", "consolidacao pulmonar",
            "taquipneia", "leucocitose", "infiltrado pulmonar",
            "derrame pleural", "toracocentese", "empiema", "broncopneumonia"]},

    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "DPOC (GOLD, Classificacao ABE, Tratamento Escalonado)",
     "kw": ["DPOC", "bronquite cronica", "enfisema", "GOLD", "VEF1",
            "espirometria", "oxigenoterapia", "inalatorio",
            "LAMA", "LABA", "corticoide inalado", "exacerbacao DPOC",
            "broncodilatador"]},

    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Asma (GINA — Degraus Terapeuticos)",
     "kw": ["asma", "sibilancia", "GINA", "crise asma", "corticoide inalatorio",
            "broncoespasmo", "formoterol", "salmeterol", "budesonida"]},

    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Tromboembolismo Pulmonar (Wells, Geneva, D-dimero, Angio-TC)",
     "kw": ["tromboembolismo", "TEP", "embolia pulmonar", "trombose venosa",
            "TVP", "D-dimero", "Wells", "Geneva", "heparina",
            "angio-TC", "cintilografia"]},

    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Injuria Renal Aguda (KDIGO, Classificacao, Etiologia)",
     "kw": ["injuria renal aguda", "IRA", "KDIGO", "creatinina",
            "dialise", "necrose tubular aguda", "rabdomiolise",
            "contraste nefropatia"]},

    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Disturbios do Sodio (Hiponatremia — SIADH, Hipernatremia)",
     "kw": ["hiponatremia", "hipernatremia", "SIADH", "sodio serico",
            "osmolaridade", "disturbio sodio", "soro hipertonico",
            "poliuria", "polidipsia"]},

    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Doenca Renal Cronica (Estadiamento TFG, Anemia, Disturbio Mineral-Osseo)",
     "kw": ["doenca renal cronica", "DRC", "TFG", "clearence", "eritropoetina",
            "hiperparatireoidismo renal", "hiperfosfatemia",
            "dialise peritoneal", "hemodialise"]},

    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Sindromes Febris (Dengue, Chikungunya, Zika, Malaria, Febre Amarela)",
     "kw": ["dengue", "chikungunya", "malaria", "febre amarela",
            "arbovirose", "febre hemorragica", "Aedes", "Plasmodium",
            "artralgia", "exantema febril", "prova laco"]},

    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Hepatopatias (Hepatites Virais, Cirrose, Hepatocarcinoma)",
     "kw": ["hepatite viral", "cirrose hepatica", "hepatocarcinoma", "CHC",
            "ascite", "varizes esofago", "encefalopatia hepatica",
            "MELD", "Child-Pugh", "transplante figado"]},

    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Antimicrobianos e Resistencia Bacteriana",
     "kw": ["antibiotico", "antimicrobiano", "resistencia bacteriana", "MRSA",
            "KPC", "CRE", "vancomicina", "meropenem", "cefalosporina"]},

    # ==================== PEDIATRIA ====================
    {"area": "Pediatria", "topicId": "ped-01",
     "subtopic": "Crescimento (Curvas OMS — Peso, Estatura, IMC, Perimetro Cefalico)",
     "kw": ["crescimento infantil", "estatura", "percentil", "escore Z",
            "baixa estatura", "desnutricao infantil", "obesidade infantil",
            "IMC infantil", "perimetro cefalico", "curva crescimento",
            "grafico OMS", "peso infantil", "estadiamento puberal"]},

    {"area": "Pediatria", "topicId": "ped-01",
     "subtopic": "Desenvolvimento Neuropsicomotor (Marcos — Denver II, Sinais de Alarme)",
     "kw": ["desenvolvimento neuropsicomotor", "DNPM", "Denver",
            "marco desenvolvimento", "atraso desenvolvimento",
            "autismo", "TEA", "puericultura", "consulta pediatrica rotina"]},

    {"area": "Pediatria", "topicId": "ped-01",
     "subtopic": "Alimentacao (Aleitamento Materno Exclusivo, Complementar, BLW)",
     "kw": ["aleitamento materno", "amamentacao", "formula infantil",
            "leite materno", "alimentacao complementar", "desmame",
            "BLW", "introducao alimentar", "suplementacao ferro",
            "suplementacao vitamina D", "formula lactea"]},

    {"area": "Pediatria", "topicId": "ped-01",
     "subtopic": "Triagens Neonatais (Pezinho, Orelhinha, Coracaozinho, Olhinho)",
     "kw": ["triagem neonatal", "teste pezinho", "teste orelhinha",
            "teste coracaozinho", "teste olhinho", "PKU",
            "fenilcetonuria", "hipotireoidismo congenito",
            "fibrose cistica", "anemia falciforme"]},

    {"area": "Pediatria", "topicId": "ped-02",
     "subtopic": "Bronquiolite Viral Aguda (VSR, Criterios de Internacao, O2, Palivizumabe)",
     "kw": ["bronquiolite", "VSR", "virus sincicial", "sibilancia lactente",
            "tiragem", "palivizumabe", "oxigenoterapia pediatrica",
            "desconforto respiratorio bebe"]},

    {"area": "Pediatria", "topicId": "ped-02",
     "subtopic": "Asma Pediatrica (GINA Pediatrico, Dispositivos Inalatorios)",
     "kw": ["asma infantil", "sibilancia crianca", "bombinha",
            "inalatorio pediatrico", "espacador", "crise asmatica crianca",
            "corticoide inalado pediatria"]},

    {"area": "Pediatria", "topicId": "ped-02",
     "subtopic": "Laringite/Crupe (Estridor, Dexametasona, Nebulizacao com Adrenalina)",
     "kw": ["laringite", "crupe", "estridor", "tosse metalica",
            "rouquidao crianca", "dexametasona oral",
            "nebulizacao adrenalina", "cornagem"]},

    {"area": "Pediatria", "topicId": "ped-03",
     "subtopic": "Reanimacao Neonatal (SBP — Passos Iniciais, VPP, Massagem, Drogas)",
     "kw": ["reanimacao neonatal", "sala parto", "ventilacao pressao positiva",
            "massagem cardiaca neonatal", "adrenalina neonatal",
            "apneia neonatal", "liquido amniotico meconial",
            "clampeamento cordao", "prematuridade"]},

    {"area": "Pediatria", "topicId": "ped-03",
     "subtopic": "Ictericia Neonatal (Zonas de Kramer, Fototerapia, Exsanguineotransfusao)",
     "kw": ["ictericia neonatal", "hiperbilirrubinemia", "Kramer", "fototerapia",
            "bilirrubina", "exsanguineotransfusao", "kernicterus",
            "incompatibilidade Rh", "incompatibilidade ABO", "deficiencia G6PD"]},

    {"area": "Pediatria", "topicId": "ped-03",
     "subtopic": "Infeccoes Congenitas (STORCH — Sifilis, Toxoplasmose, Rubeola, CMV, Herpes)",
     "kw": ["sifilis congenita", "toxoplasmose congenita",
            "rubeola congenita", "CMV congenito", "herpes neonatal",
            "infeccao congenita bebe", "triagem infecciosa gestante"]},

    {"area": "Pediatria", "topicId": "ped-04",
     "subtopic": "Calendario PNI (Crianca, Adolescente, Gestante, Idoso)",
     "kw": ["calendario vacinal", "PNI", "imunizacao", "vacinacao",
            "BCG", "pentavalente", "poliomielite", "VIP", "rotavirus",
            "pneumococica", "meningococica", "triplice viral",
            "hepatite B vacina", "DTP", "dTpa", "esquema vacinal", "dose reforco"]},

    {"area": "Pediatria", "topicId": "ped-04",
     "subtopic": "Contraindicacoes, Intervalos e Eventos Adversos Pos-Vacinacao",
     "kw": ["contraindicacao vacina", "evento adverso vacina",
            "anafilaxia vacina", "intervalo vacina",
            "imunossupressao vacina", "vacina vivo atenuado",
            "vacina inativada", "febre pos-vacinal", "convulsao vacina"]},

    {"area": "Pediatria", "topicId": "ped-05",
     "subtopic": "Diarreia Aguda — Etiologia, Planos A/B/C da OMS, Probioticos, Zinco",
     "kw": ["diarreia aguda", "desidratacao", "TRO", "soro reidratacao oral",
            "plano A", "plano B", "plano C", "reidratacao venosa",
            "probiotico", "zinco", "gastroenterite aguda",
            "Norwalk", "colera", "Shigella"]},

    {"area": "Pediatria", "topicId": "ped-05",
     "subtopic": "Alergia a Proteina do Leite de Vaca (APLV — IgE vs Nao-IgE Mediada)",
     "kw": ["APLV", "alergia leite vaca", "formula hidrolisada",
            "formula aminoacido", "soja", "colite alergica",
            "enterocolite", "proctocolite", "sangue fezes bebe",
            "colica bebe", "regurgitacao"]},

    {"area": "Pediatria", "topicId": "ped-02",
     "subtopic": "Doencas Exantematicas (Sarampo, Rubeola, Varicela, Escarlatina, Kawasaki)",
     "kw": ["exantema", "sarampo", "rubeola", "varicela", "catapora",
            "escarlatina", "exantema subito", "eritema infeccioso",
            "Kawasaki", "doenca mao-pe-boca", "coxsackie", "herpangina"]},

    # ==================== ADDITIONAL TOPICS (recover unclassified) ====================
    # Dermatologia basica
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Dermatologia Basica (Hanseniase, Lesoes Elementares, Cancer Pele)",
     "kw": ["dermatite", "eczema", "psoriase", "urticaria", "prurido",
            "cancer pele", "carcinoma basocelular", "carcinoma epidermoide",
            "melanoma", "lesao pele", "placa eritematosa", "macula",
            "papula", "nodulo", "ulcera pele", "ABCDE melanoma"]},

    # Reumatologia
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Reumatologia (Artrite Reumatoide, LES, Gota, Osteoartrite)",
     "kw": ["artrite reumatoide", "lupus", "LES", "gota", "osteoartrite",
            "artrite", "artralgia", "fator reumatoide", "FAN",
            "anti-DNA", "acido urico", "colagenose", "vasculite",
            "esclerodermia", "Sjogren", "espondilite", "sacroileite"]},

    # Neurologia
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Neurologia (AVC, Epilepsia, Cefaleia, Demencias, Parkinson)",
     "kw": ["AVC", "acidente vascular cerebral", "AVE", "epilepsia",
            "convulsao", "cefaleia", "enxaqueca", "migranea",
            "demencia", "Alzheimer", "Parkinson", "tremor",
            "doenca cerebrovascular", "hemorragia cerebral",
            "isquemia cerebral", "trombose cerebral", "ataxia"]},

    # Gastroenterologia
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Gastroenterologia (DRGE, Ulcera Peptica, Doenca Inflamatoria Intestinal)",
     "kw": ["DRGE", "doenca refluxo", "esofagite", "gastrite",
            "ulcera peptica", "dispepsia", "Helicobacter",
            "doenca inflamatoria intestinal", "Crohn", "retocolite",
            "constipacao", "sindrome intestino irritavel", "diarreia cronica",
            "esteatose hepatica", "doenca hepatica gordurosa"]},

    # Hematologia
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Hematologia (Anemias, Leucemias, Linfomas, Coagulopatias)",
     "kw": ["anemia", "anemia ferropriva", "anemia megaloblastica",
            "anemia hemolitica", "anemia falciforme", "talassemia",
            "leucemia", "linfoma", "Hodgkin", "coagulopatia",
            "hemofilia", "plaquetopenia", "trombocitopenia",
            "neutropenia", "pancitopenia", "hemograma",
            "ferritina", "ferro serico", "vitamina B12", "acido folico"]},

    # Psiquiatria
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Psiquiatria (Depressao, Ansiedade, TAB, Esquizofrenia, Suicidio)",
     "kw": ["depressao", "ansiedade", "transtorno ansiedade", "TAG",
            "transtorno bipolar", "TAB", "esquizofrenia", "psicose",
            "suicidio", "ideacao suicida", "transtorno panico",
            "TOC", "transtorno estresse", "TEPT", "sindrome panico",
            "antidepressivo", "ISRS", "fluoxetina", "sertralina",
            "ansiolitico", "benzodiazepinico", "antipsicotico"]},

    # === NEW RULES v5 — filling classification gaps ===

    # Oftalmologia
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Oftalmologia (Catarata, Glaucoma, Retinopatia, Estrabismo, Emergencias Oculares)",
     "kw": ["oftalmologia", "acuidade visual", "teste do olhinho", "reflexo vermelho",
            "catarata congenita", "estrabismo", "leucocoria", "retinoblastoma",
            "glaucoma", "retinopatia diabetica", "retinopatia hipertensiva",
            "descolamento retina", "blefarite", "conjuntivite", "uveite",
            "corpo estranho ocular", "trauma ocular", "queimadura ocular",
            "hordeolo", "calazio", "chalazion", "edema palpebral",
            "palpebra", "olho seco", "degeneracao macular", "DMRI"]},

    # Otorrinolaringologia (ENT)
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Otorrinolaringologia (Otite, Sinusite, Surdez, Vertigem, Corpo Estranho)",
     "kw": ["otorrinolaringologia", "acuidade auditiva", "hipoacusia", "surdez",
            "perda auditiva", "plenitude auditiva", "zumbido", "tinitus",
            "otite media", "otite externa", "sinusite", "rinossinusite",
            "rinite alergica", "epistaxe", "sangramento nasal",
            "corpo estranho nasal", "obstrucao nasal", "desvio septo",
            "vertigem", "labirintite", "doenca Meniere", "VPPB",
            "amigdalite", "faringite", "laringite", "disfonia", "rouquidao"]},

    # Ortopedia e Traumatologia
    {"area": "Cirurgia Geral", "topicId": "cir-02",
     "subtopic": "Ortopedia e Traumatologia (Fraturas, Luxacoes, Entorses, Lombalgia)",
     "kw": ["ortopedia", "fratura", "luxacao", "entorse", "lombalgia",
            "coluna vertebral", "escoliose", "hiperextensao punho",
            "fratura Colles", "fratura femur", "fratura tibia",
            "imobilizacao", "gesso", "tala", "tracao",
            "queda altura", "lesao ligamento", "lesao menisco",
            "sindrome tunel carpo", "bursite", "tendinite",
            "dor lombar", "ciatica", "hernia disco",
            "proteses articulares", "artroplastia", "consolidacao ossea"]},

    # Toxicologia / Intoxicações
    {"area": "Pediatria", "topicId": "ped-05",
     "subtopic": "Toxicologia Pediatrica (Intoxicacoes Exogenas, Drogas, Acidentes Domestivos)",
     "kw": ["toxicologia", "intoxicacao exogena", "ingeriu", "ingestao acidental",
            "desinfetante", "produto limpeza", "quimico", "toxina",
            "envenenamento", "overdose", "naloxona", "carvao ativado",
            "lavagem gastrica", "antidoto", "centro toxicologia",
            "drogas abuso", "alcool intoxicacao", "opioide",
            "inalacao fumaca", "monoxido carbono", "organofosforado",
            "inseticida", "raticida", "pilha", "bateria",
            "corpo estranho ingerido", "acidente domestico"]},

    # Violência / Abuso
    {"area": "Med. Preventiva", "topicId": "prev-03",
     "subtopic": "Violencia e Maus-tratos (Abuso Infantil, Violencia Domestica, Notificacao)",
     "kw": ["abuso sexual", "abusada sexualmente", "violencia domestica",
            "maus-tratos", "negligencia infantil", "conselho tutelar",
            "estatuto crianca", "ECA", "notificacao violencia",
            "ficha notificacao violencia", "lesao suspeita",
            "abusador", "pedofilia", "exploracao sexual",
            "violencia contra mulher", "Lei Maria Penha",
            "agressao fisica", "queimadura suspeita", "sindrome bebe sacudido"]},

    # Geriatria
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Geriatria (Demencia, Delirium, Fragilidade, Quedas, Iatrogenia em Idosos)",
     "kw": ["geriatria", "idoso fragil", "fragilidade idoso", "sarcopenia",
            "esquecimento", "comprometimento cognitivo", "demencia senil",
            "Alzheimer", "demencia vascular", "delirium", "confusao mental idoso",
            "queda idoso", "cuidador idoso", "sobrecarga cuidador",
            "polifarmacia idoso", "iatrogenia idoso", "avaliacao geriatrica",
            "escala Katz", "escala Lawton", "indice Barthel",
            "instituicao longa permanencia", "idoso institucionalizado"]},

    # Doenças Infecciosas e Parasitárias
    {"area": "Pediatria", "topicId": "ped-04",
     "subtopic": "Parasitoses Intestinais e Doenças Infecciosas Pediatricas",
     "kw": ["parasitose", "parasitose intestinal", "ascaridiase", "lombriga",
            "estrongiloidiase", "ancilostomiase", "teniase", "esquistossomose",
            "giardiase", "amebiase", "oxiuriase", "enterobius",
            "saneamento basico", "agua contaminada", "zona rural sem saneamento",
            "desnutricao proteica", "hipovitaminose", "diarreia cronica parasitaria",
            "albendazol", "mebendazol", "metronidazol", "praziquantel",
            "geohelmintiase", "helmintiase", "protozoario intestinal"]},

    # Alergia e Imunologia
    {"area": "Pediatria", "topicId": "ped-01",
     "subtopic": "Alergia Alimentar (APLV, Dermatite Atopica, Anafilaxia em Pediatria)",
     "kw": ["alergia alimentar", "proteina leite vaca", "APLV",
            "dermatite atopica", "anafilaxia", "reacao alergica",
            "hipersensibilidade alimentar", "formula hidrolisada",
            "formula aminoacidos", "dieta exclusao",
            "teste provocacao oral", "IgE especifica",
            "alergia ovo", "alergia soja", "alergia trigo",
            "urticaria", "angioedema", "adrenalina autoinjetavel"]},

    # PNPIC / Práticas Integrativas
    {"area": "Med. Preventiva", "topicId": "prev-01",
     "subtopic": "PNPIC e Praticas Integrativas no SUS",
     "kw": ["PNPIC", "praticas integrativas", "praticas complementares",
            "medicina tradicional chinesa", "acupuntura", "homeopatia",
            "fitoterapia", "auriculoterapia", "reiki",
            "biodanca", "musicoterapia", "arteterapia", "meditacao"]},

    # Oncologia Clínica
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Oncologia (Cancer de Esôfago, Estomago, Figado, Pancreas)",
     "kw": ["neoplasia esofagica", "cancer esofago", "cancer estomago",
            "carcinoma espinocelular", "adenocarcinoma esofago",
            "disfagia progressiva", "perda ponderal neoplasica",
            "cancer figado", "hepatocarcinoma", "cancer pancreas",
            "tabagista etilista cancer", "neoplasia sistema nervoso",
            "quimioterapia", "radioterapia", "cuidados paliativos oncologia",
            "marcador tumoral", "estadiamento oncologico", "TNM"]},

    # Emergências Pediátricas / PALS
    {"area": "Pediatria", "topicId": "ped-03",
     "subtopic": "Emergencias Pediatricas (PALS, PCR, Choque, Obstrucao Via Aerea)",
     "kw": ["suporte avancado pediatria", "PALS", "PCR pediatrica",
            "parada cardiorrespiratoria crianca", "RCP crianca",
            "colapso subito crianca", "cianose subita",
            "obstrucao via aerea corpo estranho", "engasgo",
            "manobra Heimlich", "desfibrilacao pediatrica",
            "arritmia pediatrica", "bradicardia pediatrica"]},

    # Obstetrícia — Complicações Agudas
    {"area": "Ginecologia & Obstetricia", "topicId": "go-05",
     "subtopic": "Emergencias Obstetricas (Hemorragia Pos-parto, DPP, Eclampsia, Rotura Uterina)",
     "kw": ["hemorragia pos-parto", "atonis uterina", "sangramento pos-cesarea",
            "descolamento prematuro placenta", "DPP", "placenta previa",
            "eclampsia", "pre-eclampsia grave", "sindrome HELLP",
            "rotura uterina", "inversao uterina", "embolia amniotica",
            "trabalho parto prematuro", "urgencia obstetrica"]},

    # Ginecologia — Patologia Cervical / Vulvovaginite
    {"area": "Ginecologia & Obstetricia", "topicId": "go-01",
     "subtopic": "Patologia do Trato Genital Inferior (Vulvovaginite, Citopatologico, Colposcopia)",
     "kw": ["vulvovaginite", "corrimento vaginal", "vaginose", "candidisse vaginal",
            "tricomoniase", "vaginose bacteriana", "Gardnerella",
            "exame citopatologico", "colpocitologia oncotica", "citologia oncotica",
            "ASC-US", "LSIL", "HSIL", "colposcopia", "lesao intraepitelial",
            "Papilomavirus", "rastreio cancer colo", "colposcopia anormal"]},

    # Ginecologia — Massas Anexiais / Cistos Ovarianos
    {"area": "Ginecologia & Obstetricia", "topicId": "go-01",
     "subtopic": "Tumores Ovarianos e Massas Anexiais (Cistos, Teratomas, CA-125)",
     "kw": ["cisto ovariano", "cisto anexial", "cisto anecoico",
            "imagem cistica", "projecao papilar", "massa anexial",
            "teratoma ovariano", "cistoadenoma", "cistoadenocarcinoma",
            "endometrioma", "CA-125", "marcador tumoral ovario",
            "torcao anexial", "torcao ovario", "dor pelvica cisto"]},

    # Procedimentos Ambulatoriais / Cirurgia Pediátrica
    {"area": "Cirurgia Geral", "topicId": "cir-03",
     "subtopic": "Cirurgia Pediatrica (Estenose Hipertrofica Piloro, Invaginacao, Apendicite)",
     "kw": ["estenose hipertrofica piloro", "vomitos nao biliosos",
            "vomitos biliosos", "oliva pilorica", "invaginacao intestinal",
            "intussuscepcao", "atresia esofagica", "enterocolite necrosante",
            "mal rotacao intestinal", "diverticulo Meckel", "megacolon congenito",
            "cirurgia pediatrica", "lactente vomito", "recem-nascido vomito"]},

    # ============================================================
    # NOVAS REGRAS (v6.1) — para reduzir o catch-all de ~32% para <15%
    # Cada regra usa MARCADORES CLINICOS especificos (nao buzzwords genericos)
    # ============================================================

    # ---------- MED. PREVENTIVA — adicionais ----------
    # Bioetica / Etica medica (testemunha de Jeova, sigilo, autonomia)
    {"area": "Med. Preventiva", "topicId": "prev-03",
     "subtopic": "Bioetica e Etica Medica (Sigilo, Autonomia, Confidencialidade, CFM)",
     "kw": ["sigilo medico", "sigilo profissional", "confidencialidade",
            "testemunha de jeova", "transfusao em testemunha",
            "objecao de consciencia", "objecao consciente",
            "autonomia do paciente", "principio da autonomia",
            "principio da beneficencia", "principio da nao maleficencia",
            "principio da justica", "termo de consentimento",
            "consentimento livre e esclarecido", "tcle",
            "codigo de etica medica", "cfm", "conselho regional de medicina",
            "crm", "comissao de etica", "diretiva antecipada",
            "morte encefalica", "doacao de orgaos",
            "denuncia de violencia", "comunicacao obrigatoria"]},

    # Saude do Adolescente
    {"area": "Med. Preventiva", "topicId": "prev-03",
     "subtopic": "Saude do Adolescente e do Jovem (PROSAD, Confidencialidade, Anticoncepcao)",
     "kw": ["adolescente que procura", "adolescente que comparece",
            "atendimento ao adolescente", "consulta com adolescente",
            "saude do adolescente", "prosad",
            "estagios de tanner", "tanner m", "tanner p",
            "menarca", "espermaca", "puberdade precoce", "puberdade tardia",
            "consulta sem acompanhamento", "consulta sem responsavel",
            "anticoncepcao para adolescente", "iniciacao sexual"]},

    # Maus-tratos / Violencia / ECA
    {"area": "Med. Preventiva", "topicId": "prev-05",
     "subtopic": "Violencia, Maus-tratos e ECA (Notificacao SINAN, Conselho Tutelar)",
     "kw": ["violencia domestica", "violencia contra a mulher",
            "violencia sexual", "abuso sexual", "estupro",
            "maus-tratos", "maus tratos infantis", "negligencia infantil",
            "ficha de notificacao de violencia", "notificacao de violencia",
            "conselho tutelar", "estatuto da crianca e do adolescente",
            "eca", "estatuto do idoso",
            "lei maria da penha", "medida protetiva",
            "agressao fisica suspeita", "lesao suspeita de violencia",
            "queimadura suspeita", "sindrome do bebe sacudido",
            "abandono de incapaz", "cativeiro", "exploracao sexual",
            "rede de protecao", "denuncia obrigatoria"]},

    # Diabetes Gestacional (preventiva tem foco em rastreio mas pertence a GO clinica)
    {"area": "Ginecologia & Obstetricia", "topicId": "go-01",
     "subtopic": "Diabetes Gestacional (DMG — TOTG 75g, Diagnostico, Tratamento)",
     "kw": ["diabetes gestacional", "diabete gestacional", "dmg",
            "tolerancia oral a glicose 75", "totg 75", "glicose 75g",
            "intolerancia gestacional a glicose", "glicemia de jejum gestacao",
            "glicemia capilar gestante", "insulina na gestacao",
            "rastreio dmg", "rastreamento de diabetes na gestacao"]},

    # Vacinacao na Gestante
    {"area": "Ginecologia & Obstetricia", "topicId": "go-01",
     "subtopic": "Vacinacao na Gestante (dT/dTpa, Influenza, Hep B, COVID)",
     "kw": ["vacina na gestante", "vacinacao na gestacao", "vacinacao da gestante",
            "dtpa", "tdap", "vacina dt", "vacina contra tetano gestante",
            "vacina influenza gestante", "vacina contra a influenza gestacao",
            "vacina hepatite b gestante", "esquema vacinal gestante",
            "calendario vacinal gestacao"]},

    # Bem-estar fetal / Cardiotocografia / Doppler
    {"area": "Ginecologia & Obstetricia", "topicId": "go-04",
     "subtopic": "Avaliacao de Bem-Estar Fetal (CTG, Perfil Biofisico, Doppler)",
     "kw": ["cardiotocografia", "cardiotocograf",
            "perfil biofisico fetal", "pbf",
            "doppler de arteria umbilical", "doppler fetal",
            "movimentos fetais", "ausencia de movimentos fetais",
            "bcf", "batimentos cardiofetais", "ausculta dos bcf",
            "indice de liquido amniotico", "ila",
            "oligodramnia", "polidramnia",
            "padrao ativo da cardiotocografia", "registro cardiotocografico",
            "categorias de cardiotocografia"]},

    # ITU / Pielonefrite (clinica geral)
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Infeccao do Trato Urinario (Cistite, Pielonefrite, ITU)",
     "kw": ["infeccao urinaria", "infeccao do trato urinario", "itu",
            "cistite aguda", "cistite nao complicada",
            "pielonefrite aguda", "pielonefrite",
            "urinocultura", "urocultura",
            "escherichia coli urinaria", "e. coli na urina",
            "100.000 ufc", "ufc/ml",
            "disuria e polaciuria", "urgencia urinaria"]},

    # ITU na gestante (separada porque a conduta muda)
    {"area": "Ginecologia & Obstetricia", "topicId": "go-01",
     "subtopic": "ITU e Bacteriuria Assintomatica na Gestacao",
     "kw": ["bacteriuria assintomatica", "bacteriuria na gestacao",
            "itu na gestante", "itu na gestacao", "pielonefrite na gestacao",
            "cistite na gestante"]},

    # Sepse / Choque Septico (cli geral)
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Sepse, Choque Septico e SIRS (qSOFA, Lactato, Antibioticoterapia)",
     "kw": ["sepse", "choque septico", "qsofa", "sofa score",
            "criterios de sirs", "sindrome da resposta inflamatoria",
            "lactato elevado", "lactato serico", "hipotensao com infeccao",
            "infeccao com hipotensao", "criterios de sepse",
            "campanha sobrevivendo a sepse", "ressuscitacao volemica na sepse",
            "antibiotico empirico em sepse"]},

    # Hepatites Virais (clinica)
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Hepatites Virais (A, B, C, D, E — Sorologia, HBsAg, Anti-HBc)",
     "kw": ["hepatite a", "hepatite b cronica", "hepatite c cronica",
            "hbsag", "anti-hbs", "anti-hbc", "anti hbe", "hbeag",
            "hcv", "hav", "hbv", "hdv",
            "transaminases elevadas", "tgo elevada", "tgp elevada",
            "ictericia colestatica", "hepatite aguda",
            "biopsia hepatica", "carga viral hepatite"]},

    # Glomerulopatias / Sindrome Nefrotica/Nefritica (Pediatria + Clinica)
    {"area": "Pediatria", "topicId": "ped-04",
     "subtopic": "Glomerulonefrite e Sindrome Nefritica/Nefrotica em Pediatria",
     "kw": ["glomerulonefrite", "gnda", "sindrome nefrotica",
            "sindrome nefritica", "urina cor de coca", "urina escura na crianca",
            "urina cor coca-cola", "edema palpebral", "edema de face",
            "proteinuria nefrotica", "proteinuria 24h",
            "estreptococo grupo a apos infeccao",
            "hematuria macroscopica em crianca", "iga nefropatia",
            "edema na crianca", "anasarca em crianca"]},

    # ITU pediatrica
    {"area": "Pediatria", "topicId": "ped-04",
     "subtopic": "Infeccao Urinaria em Pediatria (Lactente Febril, ITU em Crianca)",
     "kw": ["lactente febril sem foco", "febre sem foco em lactente",
            "infeccao urinaria em crianca", "itu em crianca", "itu na crianca",
            "pielonefrite em crianca", "pielonefrite na crianca",
            "cistite em crianca", "lactente com febre alta",
            "investigacao de itu em crianca", "uretrocistografia miccional",
            "refluxo vesicoureteral", "rvu"]},

    # IVAS / Otite / Faringoamigdalite Pediatrica
    {"area": "Pediatria", "topicId": "ped-02",
     "subtopic": "IVAS, Otite Media Aguda e Faringoamigdalite Pediatrica",
     "kw": ["otite media aguda", "otite media", "oma",
            "tympanocentese", "membrana timpanica abaulada",
            "faringoamigdalite", "amigdalite aguda",
            "estreptococo beta hemolitico", "centor",
            "rinossinusite aguda em crianca", "sinusite em crianca",
            "rinite alergica em crianca", "ivas em crianca",
            "obstrucao nasal e secrecao", "rinorreia",
            "secrecao nasal hialina"]},

    # Pneumonia em Pediatria
    {"area": "Pediatria", "topicId": "ped-02",
     "subtopic": "Pneumonia na Infancia (Etiologia por Faixa Etaria, Antibioticoterapia)",
     "kw": ["pneumonia em crianca", "pneumonia na infancia",
            "pneumonia adquirida na comunidade pediatrica",
            "pac pediatrica", "pneumonia bacteriana em crianca",
            "tosse com febre em crianca", "consolidacao pulmonar pediatrica",
            "amoxicilina pediatrica para pneumonia",
            "internacao por pneumonia em crianca"]},

    # Sibilancia / Asma em Crianca (dentro da area Pediatria, "asma" e seguro)
    {"area": "Pediatria", "topicId": "ped-02",
     "subtopic": "Sibilancia e Asma em Pediatria (GINA Pediatrico, Beta2-agonista, Corticoide)",
     "kw": ["asma bronquica", "asma desde os", "asma persistente",
            "lactente sibilante", "lactente sibilancia",
            "sibilancia recorrente", "sibilo expiratorio",
            "diagnostico de asma", "tratamento de asma",
            "asma na crianca", "asma pediatrica", "asma em crianca",
            "broncodilatador", "salbutamol", "fenoterol",
            "espacador com mascara", "corticoide inalatorio",
            "fluticasona", "budesonida", "beclometasona",
            "exacerbacao asmatica"]},

    # Anemia Pediatrica / Ferropriva
    {"area": "Pediatria", "topicId": "ped-05",
     "subtopic": "Anemia Ferropriva no Lactente e Pre-escolar",
     "kw": ["anemia ferropriva", "anemia carencial",
            "lactente palido", "palidez no lactente",
            "ferro elementar", "sulfato ferroso",
            "deficiencia de ferro", "introducao alimentar inadequada",
            "leite de vaca antes dos 12 meses", "ingesta de leite de vaca em excesso",
            "vcm baixo", "rdw alto", "ferritina baixa"]},

    # Acidentes / Traumas em Pediatria
    {"area": "Pediatria", "topicId": "ped-05",
     "subtopic": "Acidentes na Infancia (Quedas, Queimaduras, Engasgo, Intoxicacoes)",
     "kw": ["queda do berco", "queda da cama em crianca",
            "queimadura em crianca", "queimadura por liquido quente",
            "engasgo em crianca", "aspiracao de corpo estranho",
            "intoxicacao em crianca", "ingestao acidental",
            "acidente domestico em crianca", "trauma cranio em crianca",
            "tce em crianca",
            "envenenamento por inseticida em crianca",
            "manobra de heimlich em pediatria"]},

    # Dor toracica em Adulto / IAM
    {"area": "Clinica Medica", "topicId": "cli-03",
     "subtopic": "Dor Toracica e Sindrome Coronariana Aguda (IAM, AAS, Aspirina, Reperfusao)",
     "kw": ["dor toracica em aperto", "dor precordial",
            "dor toracica retroesternal", "supradesnivel de st",
            "supra de st", "infra de st", "infradesnivel de st",
            "iamcsst", "iamssst", "scasst", "scacssst",
            "infarto agudo do miocardio", "iam",
            "troponina elevada", "ck-mb",
            "angioplastia primaria", "trombolitico", "alteplase", "tenecteplase"]},

    # AVC
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "AVC (Isquemico e Hemorragico — NIHSS, Trombolise, Janela)",
     "kw": ["avc isquemico", "avc hemorragico", "acidente vascular cerebral",
            "deficit neurologico subito", "hemiparesia subita",
            "hemiplegia subita", "afasia subita", "paralisia facial central",
            "nihss", "janela terapeutica", "rtpa", "alteplase no avc",
            "trombolise quimica", "trombectomia mecanica",
            "tomografia de cranio sem contraste no avc",
            "fast", "afasia de broca", "afasia de wernicke"]},

    # Crise convulsiva / Epilepsia
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Crises Convulsivas, Estado de Mal Epileptico e Epilepsia",
     "kw": ["crise convulsiva generalizada", "crise tonico-clonica",
            "estado de mal epileptico", "estado epileptico",
            "diazepam intravenoso", "midazolam intramuscular",
            "fenitoina", "carbamazepina", "valproato",
            "epilepsia mioclonica", "epilepsia parcial",
            "convulsao febril", "convulsao febril simples", "convulsao febril complexa"]},

    # AVE / Cefaleia
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Cefaleia (Migranea, Tensional, Salvas, Sinais de Alarme)",
     "kw": ["cefaleia", "enxaqueca", "migranea",
            "cefaleia tensional", "cefaleia em salvas",
            "aura visual", "aura migranosa",
            "fonofobia", "fotofobia",
            "sinais de alarme em cefaleia",
            "cefaleia em trovao", "thunderclap"]},

    # DM Cetoacidose / Coma hiperosmolar
    {"area": "Clinica Medica", "topicId": "cli-02",
     "subtopic": "Cetoacidose Diabetica e Estado Hiperglicemico Hiperosmolar (CAD, EHH)",
     "kw": ["cetoacidose diabetica", "cad",
            "estado hiperglicemico hiperosmolar", "ehh",
            "respiracao de kussmaul", "halito cetonico",
            "glicemia maior que 250", "glicemia >250",
            "bicarbonato baixo", "anion gap elevado",
            "insulina regular endovenosa", "insulinoterapia em bomba"]},

    # Doenca Renal Cronica
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Doenca Renal Cronica (TFG, KDIGO, Anemia da DRC, DMO)",
     "kw": ["doenca renal cronica", "drc", "kdigo",
            "tfg estimada", "estagio g3", "estagio g4", "estagio g5",
            "creatinina elevada", "ureia elevada",
            "proteinuria persistente",
            "dialise", "hemodialise", "dialise peritoneal",
            "anemia da drc", "eritropoetina"]},

    # Tireoide (separada do cli-02 generico para ser mais especifica)
    # ja existe. Adicionando regra para tireoidectomia (cirurgia)
    {"area": "Cirurgia Geral", "topicId": "cir-03",
     "subtopic": "Cirurgia de Tireoide e Paratireoide (Nodulo, Tireoidectomia)",
     "kw": ["tireoidectomia", "tireoidectomia total", "lobectomia tireoidiana",
            "nodulo tireoidiano", "nodulo de tireoide suspeito",
            "bethesda", "puncao aspirativa por agulha fina", "paaf",
            "carcinoma papilifero", "carcinoma folicular tireoide",
            "cirurgia de paratireoide", "hiperparatireoidismo cirurgico"]},

    # Cirurgia: massa em mama / cancer
    {"area": "Cirurgia Geral", "topicId": "cir-03",
     "subtopic": "Cancer e Tumores de Mama (Diagnostico, BI-RADS, Cirurgia)",
     "kw": ["nodulo de mama palpavel", "nodulo mama suspeito",
            "tumor de mama", "carcinoma de mama",
            "bi-rads 4", "bi-rads 5", "bi-rads 3", "birads 4", "birads 5", "birads 3",
            "biopsia de mama", "core biopsy",
            "mastectomia", "quadrantectomia", "linfonodo sentinela mama",
            "carcinoma ductal", "carcinoma lobular"]},

    # Cirurgia: hemorroida / fissura / fistula
    {"area": "Cirurgia Geral", "topicId": "cir-05",
     "subtopic": "Doencas Anorretais (Hemorroida, Fissura Anal, Fistula, Abscesso)",
     "kw": ["hemorroida", "hemorroidas internas", "hemorroidas externas",
            "fissura anal", "fissura anal cronica",
            "fistula anal", "fistula perianal",
            "abscesso perianal", "abscesso anorretal",
            "doenca hemorroidaria"]},

    # Doencas Tropicais / Negligenciadas
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Doencas Tropicais Negligenciadas (Doenca de Chagas, Leishmaniose, Esquistossomose)",
     "kw": ["doenca de chagas", "trypanosoma cruzi",
            "leishmaniose tegumentar", "leishmaniose visceral",
            "calazar", "ulcera de leishmaniose",
            "esquistossomose mansoni", "schistosoma",
            "hepatoesplenomegalia em area endemica",
            "raiva humana", "mordedura por animal",
            "vacina antirabica", "soro antirabico",
            "acidente por animal peconhento", "soro antiofidico",
            "picada de cobra", "soro antiarachnidico"]},

    # ============================================================
    # NOVAS REGRAS (v6.2) — cobertura adicional de casos clinicos
    # ============================================================

    # Pre-natal / Acompanhamento de gestacao
    {"area": "Ginecologia & Obstetricia", "topicId": "go-01",
     "subtopic": "Pre-natal de Baixo Risco (Suplementacao, Exames, Consultas, Cartao)",
     "kw": ["pre-natal de baixo risco", "consulta de pre-natal",
            "primeira consulta de pre-natal", "rotina do pre-natal",
            "exames de pre-natal", "cartao da gestante",
            "suplementacao de acido folico", "suplementacao de ferro na gestacao",
            "ganho de peso na gestacao", "altura uterina",
            "datacao da gestacao", "ultrassonografia obstetrica",
            "ig duvidosa", "idade gestacional duvidosa",
            "amenorreia gestacional", "dum", "data da ultima menstruacao",
            "tipagem sanguinea gestacional", "coombs indireto"]},

    # Trabalho de Parto Prematuro / Pre-termo
    {"area": "Ginecologia & Obstetricia", "topicId": "go-04",
     "subtopic": "Trabalho de Parto Prematuro (Tocolise, Corticoide, Sulfato de Magnesio)",
     "kw": ["trabalho de parto prematuro", "trabalho de parto pre-termo",
            "tpp", "ameaca de parto prematuro",
            "tocolise", "tocolitico", "nifedipino na gestacao",
            "betametasona em gestante", "corticoide para maturacao pulmonar",
            "neuroprotecao com sulfato de magnesio",
            "incompetencia istmocervical", "circlagem",
            "dilatacao precoce do colo"]},

    # Hemorragia pos-parto / Atonia (separar da rotura uterina)
    {"area": "Ginecologia & Obstetricia", "topicId": "go-06",
     "subtopic": "Hemorragia Pos-parto (Atonia Uterina, Balao de Bakri, Misoprostol)",
     "kw": ["hemorragia pos-parto", "atonia uterina",
            "sangramento pos-parto", "sangramento pos-cesarea",
            "balao de bakri", "balao intrauterino",
            "manobra de hamilton", "ocitocina pos-parto",
            "misoprostol pos-parto", "ergometrina",
            "carbetocina", "tamponamento uterino"]},

    # Sangramento de 2a metade
    {"area": "Ginecologia & Obstetricia", "topicId": "go-06",
     "subtopic": "Sangramento de 2a Metade (DPP, Placenta Previa, Vasa Previa, Acretismo)",
     "kw": ["descolamento prematuro de placenta", "dpp",
            "placenta previa", "placenta de insercao baixa",
            "acretismo placentario", "placenta acreta", "placenta increta", "placenta percreta",
            "vasa previa", "rotura uterina",
            "hemorragia anteparto", "sangramento de segunda metade"]},

    # Fluxo Menstrual / SUA / Miomatose
    {"area": "Ginecologia & Obstetricia", "topicId": "go-05",
     "subtopic": "Sangramento Uterino Anormal (SUA, PALM-COEIN, Miomatose, Polipos)",
     "kw": ["sangramento uterino anormal", "sua", "palm-coein",
            "miomatose uterina", "mioma uterino", "leiomioma",
            "polipo endometrial", "hiperplasia endometrial",
            "menorragia", "metrorragia", "hipermenorreia",
            "endometrio espessado", "histeroscopia"]},

    # ITU adulta — alargar
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Doencas Diarreicas (Gastroenterite, Disenteria, DTA, Toxinfeccao Alimentar)",
     "kw": ["gastroenterite aguda", "diarreia aguda em adulto",
            "diarreia infecciosa", "intoxicacao alimentar",
            "doenca transmitida por alimento", "dta",
            "vibrio cholerae", "salmonella", "shigella", "rotavirus em adulto",
            "campylobacter", "clostridioides difficile", "c difficile",
            "diarreia do viajante",
            "fezes com sangue", "disenteria"]},

    # Asma adulto
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Asma do Adulto (GINA, Step Up/Down, Tratamento de Manutencao)",
     "kw": ["asma do adulto", "asma persistente",
            "controle da asma", "exacerbacao de asma",
            "salbutamol em adulto", "corticoide inalatorio em adulto",
            "formoterol", "salmeterol", "beclometasona",
            "vef1", "pico de fluxo expiratorio",
            "step up asma", "step down asma",
            "broncoespasmo agudo"]},

    # DPOC
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "DPOC (GOLD, Exacerbacao, Oxigenoterapia, Antibiotico)",
     "kw": ["doenca pulmonar obstrutiva cronica", "dpoc",
            "tabagista com dispneia", "dispneia progressiva em tabagista",
            "exacerbacao de dpoc", "exacerbacao infecciosa",
            "oxigenoterapia domiciliar", "oxigenio em dpoc",
            "tiotropio", "lama lala", "saba laba", "broncodilatador de longa duracao",
            "espirometria com indice de tiffeneau",
            "vef1/cvf"]},

    # Hipotireoidismo / Hipertireoidismo isolados
    {"area": "Clinica Medica", "topicId": "cli-02",
     "subtopic": "Hipotireoidismo e Hashimoto (TSH alto, Levotiroxina, Tireoidite)",
     "kw": ["hipotireoidismo", "hipotireoidismo subclinico",
            "tireoidite de hashimoto", "anti-tpo",
            "levotiroxina", "tsh elevado", "t4 livre baixo",
            "constipacao com bocio", "intolerancia ao frio com bocio"]},

    {"area": "Clinica Medica", "topicId": "cli-02",
     "subtopic": "Hipertireoidismo e Doenca de Graves (TSH baixo, Metimazol, I131)",
     "kw": ["hipertireoidismo", "doenca de graves",
            "tirotoxicose", "tempestade tireotoxica",
            "metimazol", "propiltiouracil", "iodo radioativo",
            "tsh suprimido", "trab", "anti receptor de tsh",
            "exoftalmia", "oftalmopatia de graves"]},

    # Cushing / Addison
    {"area": "Clinica Medica", "topicId": "cli-02",
     "subtopic": "Doencas das Adrenais (Cushing, Addison, Insuficiencia Adrenal)",
     "kw": ["sindrome de cushing", "doenca de cushing",
            "estrias violaceas", "fascies em lua cheia", "giba dorsal",
            "insuficiencia adrenal", "doenca de addison",
            "hiperpigmentacao cutanea com fadiga",
            "hidrocortisona em insuficiencia",
            "feocromocitoma", "metanefrinas",
            "hiperaldosteronismo primario", "conn", "aldosterona renina"]},

    # Reumatologia (LES, AR, gota)
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Lupus Eritematoso Sistemico (LES, Criterios SLICC/ACR, FAN)",
     "kw": ["lupus eritematoso sistemico", "les",
            "criterios slicc", "criterios eular acr",
            "fan reagente", "fan positivo", "anti-dna",
            "anti-sm", "anti-ssa", "anti-ssb",
            "rash malar", "lesao em borboleta",
            "nefrite lupica", "lupus discoide"]},

    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Artrite Reumatoide (AR, Fator Reumatoide, Anti-CCP, MTX)",
     "kw": ["artrite reumatoide", "fator reumatoide",
            "anti-ccp", "anti-peptideo citrulinado",
            "rigidez matinal prolongada", "rigidez articular matinal",
            "artrite simetrica de pequenas articulacoes",
            "metotrexato em ar", "leflunomida"]},

    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Gota e Hiperuricemia (Tofos, Acido Urico, Colchicina, Alopurinol)",
     "kw": ["gota", "hiperuricemia", "tofo gotoso",
            "podagra", "ataque de gota",
            "acido urico elevado", "uricemia",
            "colchicina", "alopurinol", "febuxostate"]},

    # Anemias do adulto (alargar cli-05 hematologia)
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Anemias do Adulto (Ferropriva, Megaloblastica, Anemia Cronica)",
     "kw": ["anemia ferropriva no adulto", "anemia por deficiencia de ferro",
            "anemia megaloblastica", "deficiencia de b12", "deficiencia de folato",
            "anemia perniciosa", "fator intrinseco",
            "anemia da doenca cronica", "anemia cronica",
            "anemia falciforme", "doenca falciforme",
            "crise vaso-oclusiva", "crise dolorosa falcemica",
            "hemoglobina baixa com vcm baixo",
            "hemoglobina baixa com vcm alto"]},

    # Psiquiatria
    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Depressao, Ansiedade e Transtorno do Humor (PHQ-9, ISRS, TAB)",
     "kw": ["transtorno depressivo", "depressao maior",
            "phq-9", "phq 9", "hamilton depressao",
            "isrs", "fluoxetina", "sertralina", "escitalopram",
            "transtorno de ansiedade generalizada", "tag",
            "panico", "transtorno do panico",
            "transtorno bipolar", "tab", "mania", "hipomania",
            "litio", "carbonato de litio",
            "tristeza por mais de duas semanas",
            "ideacao suicida", "tentativa de suicidio"]},

    {"area": "Clinica Medica", "topicId": "cli-05",
     "subtopic": "Sindromes Psicoticas (Esquizofrenia, Delirium, Antipsicoticos)",
     "kw": ["esquizofrenia",
            "alucinacoes auditivas", "delirio persecutorio",
            "antipsicotico", "haloperidol", "risperidona", "olanzapina",
            "delirium hiperativo", "delirium hipoativo",
            "confusao mental aguda em idoso",
            "transtorno por uso de substancia"]},

    # ETV / TVP / TEP
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Doenca Tromboembolica Venosa (TVP, TEP, Wells, D-dimero)",
     "kw": ["trombose venosa profunda", "tvp",
            "tromboembolismo pulmonar", "tep",
            "escore de wells", "d-dimero",
            "doppler venoso de mmii", "doppler de membros inferiores",
            "angio-tc de torax", "angiotomografia pulmonar",
            "anticoagulacao com heparina", "rivaroxabana",
            "edema unilateral de membro inferior", "empastamento de panturrilha"]},

    # Suicidio em adolescente / Pediatria psiquiatrica
    {"area": "Pediatria", "topicId": "ped-05",
     "subtopic": "Saude Mental na Infancia e Adolescencia (TDAH, TEA, Depressao Juvenil)",
     "kw": ["transtorno do espectro autista", "tea",
            "autismo infantil",
            "transtorno do deficit de atencao", "tdah",
            "comportamento impulsivo escolar", "indisciplina escolar",
            "metilfenidato", "ritalina",
            "depressao na adolescencia", "ideacao suicida em adolescente"]},

    # Pediatria — Hidratacao / TRO
    {"area": "Pediatria", "topicId": "ped-05",
     "subtopic": "Diarreia, TRO e Desidratacao Pediatrica (Plano A/B/C, Soro)",
     "kw": ["diarreia aguda em crianca",
            "diarreia em lactente", "diarreia liquida em crianca",
            "tro", "terapia de reidratacao oral",
            "soro caseiro", "sais de reidratacao oral",
            "plano a", "plano b", "plano c",
            "desidratacao leve em crianca", "desidratacao moderada em crianca",
            "desidratacao grave em crianca", "criterios de desidratacao",
            "criterios oms desidratacao",
            "zinco em diarreia",
            "fralda seca", "lagrimas ausentes em crianca"]},

    # Pediatria — Pubertal precoce/atrasada
    {"area": "Pediatria", "topicId": "ped-01",
     "subtopic": "Puberdade Precoce e Atrasada (Tanner, Hormonios, GnRH)",
     "kw": ["puberdade precoce", "telarca precoce", "pubarca precoce",
            "puberdade tardia", "atraso puberal",
            "estagio de tanner", "tanner mamario", "tanner pubiano",
            "lh elevado", "fsh elevado", "estradiol",
            "analogo de gnrh"]},

    # Cli-04 — DM2 medicamentos / Insulinoterapia
    {"area": "Clinica Medica", "topicId": "cli-02",
     "subtopic": "DM2 — Tratamento Farmacologico (Metformina, GLP-1, SGLT-2, Insulina)",
     "kw": ["metformina", "metformina basal",
            "glp-1", "agonista de glp", "liraglutide", "semaglutide",
            "sglt-2", "isglt2", "dapagliflozina", "empagliflozina",
            "insulina nph", "insulina regular", "insulina glargina",
            "insulina detemir", "insulina lispro",
            "esquema basal-bolus",
            "controle glicemico", "alvo de a1c", "meta de glicada"]},

    # Cli — IC com fracao reduzida
    {"area": "Clinica Medica", "topicId": "cli-03",
     "subtopic": "Insuficiencia Cardiaca Cronica (ICFEr, ICFEp, IECA, BB, Espironolactona)",
     "kw": ["insuficiencia cardiaca", "icfer", "icfep", "icfm",
            "fracao de ejecao reduzida", "fracao de ejecao preservada",
            "iniciar betabloqueador na ic", "espironolactona na ic",
            "sacubitril/valsartana", "entresto",
            "dapagliflozina na ic",
            "nyha ii", "nyha iii", "nyha iv",
            "ortopneia", "dispneia paroxistica noturna",
            "edema de mmii em ic"]},

    # Cli — FA
    {"area": "Clinica Medica", "topicId": "cli-03",
     "subtopic": "Fibrilacao Atrial (CHA2DS2-VASc, Anticoagulacao, Cardioversao)",
     "kw": ["fibrilacao atrial", "fa cronica",
            "cha2ds2-vasc", "chads2",
            "anticoagulacao oral", "varfarina",
            "rivaroxabana", "apixabana", "dabigatrana",
            "ablacao de fa", "cardioversao eletrica",
            "controle de frequencia cardiaca",
            "pulso irregularmente irregular"]},

    # Cir — Apendicite / Aporcelanada
    {"area": "Cirurgia Geral", "topicId": "cir-01",
     "subtopic": "Apendicite Aguda (Alvarado, McBurney, Apendicectomia, Plastrao)",
     "kw": ["apendicite aguda",
            "escore de alvarado",
            "ponto de mcburney", "sinal de blumberg",
            "apendicectomia", "apendice retrocecal",
            "plastrao apendicular", "apendice perfurado"]},

    # Cir — Diverticulite
    {"area": "Cirurgia Geral", "topicId": "cir-01",
     "subtopic": "Doenca Diverticular dos Colons (Diverticulite, Hinchey, Tratamento)",
     "kw": ["doenca diverticular dos colons",
            "diverticulite aguda", "diverticulite complicada",
            "classificacao de hinchey", "hinchey 1", "hinchey 2", "hinchey 3", "hinchey 4",
            "fistula colovesical",
            "abscesso pericolico"]},

    # Cir — Vias biliares / Coledocolitiase
    {"area": "Cirurgia Geral", "topicId": "cir-03",
     "subtopic": "Pancreatite Aguda (Atlanta, BISAP, Ranson, Necrosectomia)",
     "kw": ["pancreatite aguda",
            "criterios de atlanta", "bisap", "ranson",
            "amilase elevada", "lipase elevada",
            "tomografia de pancreas",
            "necrose pancreatica", "necrosectomia",
            "pancreatite biliar",
            "pseudo-cisto pancreatico"]},

    # Cir — Tumores aparelho digestivo
    {"area": "Cirurgia Geral", "topicId": "cir-03",
     "subtopic": "Cancer de Estomago, Esofago e Colorretal (Estadiamento, Cirurgia)",
     "kw": ["adenocarcinoma gastrico",
            "linfoma gastrico", "marginal de baixo grau",
            "carcinoma escamocelular de esofago",
            "adenocarcinoma de esofago",
            "esofagectomia", "gastrectomia subtotal", "gastrectomia total",
            "hemicolectomia direita", "hemicolectomia esquerda",
            "ressecao anterior baixa do reto",
            "ostomia definitiva",
            "carcinomatose peritoneal"]},

    # Cir — Aneurisma de Aorta / vascular
    {"area": "Cirurgia Geral", "topicId": "cir-02",
     "subtopic": "Cirurgia Vascular (AAA, Isquemia Mesenterica, Doenca Arterial Periferica)",
     "kw": ["aneurisma de aorta abdominal", "aaa",
            "isquemia mesenterica aguda",
            "doenca arterial periferica", "dap",
            "claudicacao intermitente",
            "tromboembolismo arterial", "embolia arterial aguda",
            "indice tornozelo-braco",
            "endarterectomia", "bypass aorto-femoral"]},

    # Cir — Trauma de cranio / TCE
    {"area": "Cirurgia Geral", "topicId": "cir-02",
     "subtopic": "TCE — Glasgow, TCE Leve/Moderado/Grave, Hematomas Intracranianos",
     "kw": ["traumatismo cranioencefalico", "tce leve", "tce moderado", "tce grave",
            "escala de coma de glasgow", "glasgow 15",
            "hematoma extradural", "hematoma epidural", "hematoma subdural",
            "hemorragia subaracnoidea traumatica",
            "lucidez e perda de consciencia"]},

    # Cir — Trauma raquimedular
    {"area": "Cirurgia Geral", "topicId": "cir-02",
     "subtopic": "Trauma Raquimedular (Imobilizacao, Choque Neurogenico, ASIA)",
     "kw": ["trauma raquimedular", "tatem",
            "lesao medular", "asia a", "asia b", "asia c",
            "choque neurogenico",
            "imobilizacao cervical",
            "colar cervical",
            "tetraplegia subita", "paraplegia traumatica"]},

    # Hipoglicemia
    {"area": "Clinica Medica", "topicId": "cli-02",
     "subtopic": "Hipoglicemia (Whipple, Glucagon, Glicose Hipertonica)",
     "kw": ["hipoglicemia",
            "triade de whipple",
            "glicose hipertonica endovenosa",
            "glucagon im", "glucose 50%"]},

    # Tabagismo / DPOC etiologia
    # (ja em prev-01 + cli-04)

    # Cuidados Paliativos
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Cuidados Paliativos e Comunicacao de Mas Noticias (SPIKES)",
     "kw": ["cuidados paliativos", "paliativismo",
            "controle de dor oncologica",
            "morfina via oral", "morfina sc", "morfina opiacea",
            "spikes", "comunicacao de mas noticias",
            "fim de vida", "ortotanasia",
            "cuidado de fim de vida", "diretiva antecipada de vontade"]},

    # ALERGIA / RINITE / DERMATITE
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Rinite Alergica e Dermatite Atopica em Adulto (Anti-histaminicos, Corticoide)",
     "kw": ["rinite alergica",
            "anti-histaminico oral", "loratadina", "desloratadina", "fexofenadina",
            "corticoide nasal", "budesonida nasal", "mometasona nasal",
            "dermatite atopica", "eczema atopico",
            "prurido cutaneo cronico"]},

    # GO — Obstetricia: pos-natal / aleitamento
    {"area": "Pediatria", "topicId": "ped-01",
     "subtopic": "Aleitamento Materno (Tecnica de Pega, Ordenha, Fissura, Mastite)",
     "kw": ["aleitamento materno exclusivo", "amamentacao exclusiva",
            "fissura mamilar", "ingurgitamento mamario", "mastite puerperal",
            "tecnica de pega", "pega adequada",
            "ordenha manual", "ordenha do leite",
            "banco de leite humano",
            "leite materno cru", "leite materno pasteurizado"]},

    # ============================================================
    # NOVAS REGRAS PEDIATRICAS (v6.3) — area-restricted broad keywords
    # Como a area ja foi detectada como Pediatria, podemos usar termos
    # gerais (tipo "anemia", "leucemia") sem confundir com adultos.
    # ============================================================

    # Neonatologia — distress respiratorio / ictericia / sepse / cardiopatia
    {"area": "Pediatria", "topicId": "ped-03",
     "subtopic": "Distress Respiratorio Neonatal (DMH, Surfactante, Taquipneia Transitoria)",
     "kw": ["doenca de membrana hialina", "dmh",
            "sindrome do desconforto respiratorio neonatal",
            "taquipneia transitoria do rn", "tttn",
            "sindrome de aspiracao meconial", "sam",
            "surfactante pulmonar", "cpap nasal no rn",
            "respiratorio do recem-nascido",
            "desconforto respiratorio neonatal",
            "cianose ao choro", "cianose central neonatal"]},

    {"area": "Pediatria", "topicId": "ped-03",
     "subtopic": "Sepse Neonatal (Precoce e Tardia, Antibiotico Empirico, Hemocultura)",
     "kw": ["sepse neonatal precoce", "sepse neonatal tardia",
            "sepse neonatal", "infeccao neonatal grave",
            "ampicilina e gentamicina no rn",
            "hemocultura no rn", "investigacao de sepse no rn",
            "fatores de risco para sepse neonatal",
            "rotura prematura de membranas com febre"]},

    # Cardiopatias congenitas
    {"area": "Pediatria", "topicId": "ped-03",
     "subtopic": "Cardiopatias Congenitas (Sopro, Cianose, Tetralogia de Fallot, CIV/CIA)",
     "kw": ["cardiopatia congenita", "sopro cardiaco em rn",
            "sopro sistolico em lactente", "sopro sistolico em rn",
            "tetralogia de fallot", "transposicao de grandes",
            "comunicacao interventricular", "civ",
            "comunicacao interatrial", "cia",
            "persistencia do canal arterial", "pca",
            "ducto arterioso patente",
            "teste do coracaozinho", "oximetria de pulso pre e pos ductal",
            "cianose neonatal central"]},

    # Doencas exantematicas / erupcoes (expandir a regra existente)
    {"area": "Pediatria", "topicId": "ped-02",
     "subtopic": "Doencas Exantematicas Pediatricas (Sarampo, Rubeola, Catapora, Eritema Infeccioso)",
     "kw": ["sarampo", "rubeola adquirida", "varicela", "catapora",
            "exantema", "rash cutaneo na crianca",
            "doenca mao-pe-boca", "mao pe boca",
            "eritema infeccioso", "5a doenca",
            "escarlatina", "doenca de kawasaki",
            "manchas de koplik", "sinal de filatov",
            "lingua em framboesa"]},

    # Convulsao febril
    {"area": "Pediatria", "topicId": "ped-05",
     "subtopic": "Convulsao Febril (Simples vs Complexa, Investigacao, Profilaxia)",
     "kw": ["convulsao febril",
            "crise convulsiva febril em crianca",
            "criterios para convulsao febril simples",
            "convulsao febril complexa",
            "criterios de convulsao febril",
            "diazepam retal pediatrico"]},

    # Hematologia pediatrica (anemia, leucemias, distúrbios)
    {"area": "Pediatria", "topicId": "ped-05",
     "subtopic": "Hematologia Pediatrica (Anemia Falciforme, Leucemia, PTI, Distúrbios)",
     "kw": ["anemia falciforme", "doenca falciforme em crianca",
            "crise vaso-oclusiva", "crise dolorosa falcemica",
            "sindrome torac falcemica", "sequestro esplenico",
            "leucemia linfoblastica aguda", "lla",
            "leucemia mieloide aguda em crianca",
            "purpura trombocitopenica imune", "pti",
            "purpura de henoch-schonlein", "phs",
            "hemofilia infantil",
            "petequias e equimoses",
            "pancitopenia em crianca",
            "anemia em crianca"]},

    # Cefaleia em crianca
    {"area": "Pediatria", "topicId": "ped-05",
     "subtopic": "Cefaleia em Pediatria (Migranea, Cefaleia Tensional, Sinais de Alarme)",
     "kw": ["cefaleia em crianca",
            "cefaleia recorrente em crianca",
            "enxaqueca pediatrica", "migranea infantil",
            "criterios diagnosticos de migranea pediatrica",
            "cefaleia com aura em adolescente"]},

    # Ortopedia pediatrica
    {"area": "Pediatria", "topicId": "ped-05",
     "subtopic": "Ortopedia Pediatrica (Sinovite Transitoria, Legg-Calve-Perthes, Artrite Septica)",
     "kw": ["sinovite transitoria do quadril",
            "legg-calve-perthes", "perthes",
            "epifisiolise femoral proximal", "efp",
            "claudicacao em crianca",
            "artrite septica em crianca",
            "displasia do desenvolvimento do quadril", "ddq",
            "manobra de ortolani", "manobra de barlow",
            "marcha em crianca pequena"]},

    # Doencas geneticas / sindromes
    {"area": "Pediatria", "topicId": "ped-05",
     "subtopic": "Sindromes Geneticas (Sind. Down, Turner, Klinefelter, Erros Inatos do Metabolismo)",
     "kw": ["sindrome de down", "trissomia do 21",
            "sindrome de turner", "sindrome de klinefelter",
            "fibrose cistica", "mucoviscidose",
            "fenilcetonuria", "pku",
            "hipotireoidismo congenito",
            "erros inatos do metabolismo",
            "teste do pezinho ampliado"]},

    # Criptorquidia / Hernia em crianca
    {"area": "Cirurgia Geral", "topicId": "cir-03",
     "subtopic": "Cirurgia Pediatrica Eletiva (Criptorquidia, Hernia Inguinal, Hidrocele)",
     "kw": ["testiculo nao descido", "testiculo ausente",
            "criptorquidia", "criptorquidismo",
            "orquipexia", "orquidopexia",
            "hernia inguinal em crianca", "hernia inguinal pediatrica",
            "hidrocele em crianca", "hidrocele comunicante",
            "fimose patologica", "postectomia",
            "torsao testicular"]},

    # Trauma em pediatria (queda, queimadura)
    # ja existe ped-05 "Acidentes na Infancia" — confirmar keywords cobrem queda

    # Saude mental em adolescente / Depressao juvenil
    # ja existe ped-05 "Saude Mental na Infancia"

    # GINECOLOGIA-OBSTETRICIA — Adicionais

    # Endometriose / dor pelvica
    {"area": "Ginecologia & Obstetricia", "topicId": "go-05",
     "subtopic": "Endometriose e Dor Pelvica Cronica (Dismenorreia, Adenomiose)",
     "kw": ["endometriose", "endometrioma",
            "dor pelvica cronica",
            "dismenorreia secundaria", "dismenorreia primaria",
            "adenomiose", "adenomioma",
            "dispareunia profunda",
            "implantes peritoneais"]},

    # Doenca Inflamatoria Pelvica (DIP)
    {"area": "Ginecologia & Obstetricia", "topicId": "go-01",
     "subtopic": "Doenca Inflamatoria Pelvica (DIP, Salpingite, Abscesso Tubario)",
     "kw": ["doenca inflamatoria pelvica", "dip",
            "salpingite", "anexite", "abscesso tubario",
            "criterios para dip",
            "tratamento ambulatorial de dip",
            "ceftriaxona doxiciclina metronidazol",
            "dor pelvica aguda em mulher"]},

    # Climaterio / TRH
    {"area": "Ginecologia & Obstetricia", "topicId": "go-05",
     "subtopic": "Climaterio, Menopausa e TRH (Sintomas, Indicacoes, Contraindicacoes)",
     "kw": ["climaterio", "menopausa",
            "fogachos", "ondas de calor", "sintomas vasomotores",
            "terapia de reposicao hormonal", "trh",
            "estrogeno isolado", "estrogeno combinado com progesterona",
            "contraindicacoes da trh",
            "atrofia urogenital", "secura vaginal"]},

    # CIRURGIA — Adicionais

    # Tumor de partes moles / lipoma / cisto sebaceo
    {"area": "Cirurgia Geral", "topicId": "cir-05",
     "subtopic": "Cirurgia Ambulatorial Menor (Lipoma, Cisto Sebaceo, Excisao, Sutura)",
     "kw": ["cisto sebaceo", "cisto epidermico",
            "lipoma subcutaneo",
            "lesao cutanea elevada",
            "excisao com ponto", "exerese de cisto",
            "drenagem de abscesso superficial",
            "sutura simples", "ponto separado", "ponto continuo"]},

    # Câncer de pulmão (clinica)
    {"area": "Clinica Medica", "topicId": "cli-04",
     "subtopic": "Cancer de Pulmao (Tabagismo, Tomografia, Diagnostico, Estadiamento)",
     "kw": ["cancer de pulmao",
            "neoplasia pulmonar",
            "carcinoma de pequenas celulas",
            "carcinoma nao pequenas celulas",
            "nodulo pulmonar suspeito",
            "tabagista com nodulo",
            "espicula pulmonar",
            "estadiamento do cancer de pulmao",
            "tnm pulmao"]},
]

# ============================================================
# COLUMN-AWARE PDF EXTRACTION
# ============================================================
def extract_text_by_column(pdf_path):
    """Extract text from 2-column INEP PDF with correct reading order.

    INEP layout: questions alternate between columns per page.
    Reading order: left-col-top-to-bottom, then right-col-top-to-bottom.
    This function preserves per-page sequencing so question markers appear in order.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page_texts = []
            for page in pdf.pages:
                words = page.extract_words(keep_blank_chars=True)
                if not words:
                    continue
                mid_x = page.width / 2
                left_words = [w for w in words if w["x0"] < mid_x]
                right_words = [w for w in words if w["x0"] >= mid_x]
                left_words.sort(key=lambda w: (round(w["top"], 1), w["x0"]))
                right_words.sort(key=lambda w: (round(w["top"], 1), w["x0"]))

                def words_to_text(word_list):
                    lines, cur_line, cur_top = [], [], None
                    for w in word_list:
                        if cur_top is None or abs(w["top"] - cur_top) < 3:
                            if cur_top is None: cur_top = w["top"]
                            cur_line.append(w["text"])
                        else:
                            lines.append(" ".join(cur_line))
                            cur_line, cur_top = [w["text"]], w["top"]
                    if cur_line: lines.append(" ".join(cur_line))
                    return "\n".join(lines)

                left_text = words_to_text(left_words)
                right_text = words_to_text(right_words)
                if "LEIA" in left_text and "ATEN" in left_text:
                    continue
                # Per-page interleave: left column first, then right (natural reading order)
                page_texts.append(left_text + "\n" + right_text)

            return "\n".join(page_texts)
    except Exception as e:
        print(f"  ERROR extracting {pdf_path}: {e}")
        return ""

# ============================================================
# GABARITO PARSING
# ============================================================
def parse_answer_key(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
    if not full_text:
        return {}

    answers = {}

    # Method 1: number-answer pair format (2021/2022 and older)
    # Lines like: "1  B          40  D   79  B" or "1 Anulada       36      C"
    for m in re.finditer(r'\b(\d{1,3})\s+([A-E]|X|Anulada)\b', full_text, re.IGNORECASE):
        qnum = int(m.group(1))
        ans = m.group(2).upper()
        if 1 <= qnum <= 100 and qnum not in answers:
            answers[qnum] = None if ans in ('X', 'ANULADA') else ans

    # Method 2: table format (2023+) — "Questão 1 2...20" / "Gabarito A B...C"
    if len(answers) < 10:
        lines = full_text.split("\n")
        q_lines, g_lines = [], []
        for i, line in enumerate(lines):
            if re.search(r'Quest[ãa]o\s+\d+', line, re.IGNORECASE):
                nums = [int(n) for n in re.findall(r'\b(\d{1,3})\b', line)]
                if nums: q_lines.append((i, nums))
            elif re.search(r'Gabarito\s+[A-E]', line, re.IGNORECASE):
                letters = re.findall(r'\b([A-E])\b', line)
                if letters: g_lines.append((i, letters))
        for (qi, qnums), (gi, glets) in zip(q_lines, g_lines):
            if abs(qi - gi) <= 2:
                for qnum, letter in zip(qnums, glets):
                    if 1 <= qnum <= 100 and qnum not in answers:
                        answers[qnum] = letter

    return answers

# ============================================================
# QUESTION EXTRACTION & CLASSIFICATION
# ============================================================
def extract_questions(text):
    """Detect question boundaries in three formats found across Revalida editions:

    Modern (2018+):  ``QUESTÃO 01``  / ``QUESTÃO 1``
    Legacy (2011-2017):  ``01 questão`` / ``1 questão`` (number BEFORE the word)
    Mixed (2020):  alternates BOTH formats inside a single PDF
    """
    modern = list(re.finditer(r'QUEST[ÃA]O\s+(\d{1,3})\b', text, re.IGNORECASE))
    legacy = list(re.finditer(r'\b(\d{1,3})\s+quest[ãa]o\b', text, re.IGNORECASE))

    # Merge both — but legacy can have false positives (e.g. "exame realizado em 12 questões"),
    # so guard the legacy hits: require either (a) the digit is at the start of a line and
    # followed by 'questão', or (b) modern format has < 5 hits (so PDF clearly uses legacy).
    use_both = len(modern) > 5 and len(legacy) > 5
    if use_both:
        # Mixed PDF (e.g. 2020): include legacy hits whose digit looks like a fresh marker
        # (preceded by a newline + nothing else interesting).
        merged = list(modern)
        for m in legacy:
            ctx = text[max(0, m.start() - 2):m.start()]
            if "\n" in ctx:
                merged.append(m)
        merged.sort(key=lambda m: m.start())
        matches = merged
    elif len(modern) >= len(legacy):
        matches = modern
    else:
        matches = legacy

    # De-duplicate by question number — keep the first occurrence in document order.
    seen = set()
    unique = []
    for m in matches:
        key = m.group(1)
        if key in seen:
            continue
        seen.add(key)
        unique.append(m)

    questions = []
    for i, m in enumerate(unique):
        qnum = int(m.group(1))
        start = m.start()
        end = unique[i + 1].start() if i + 1 < len(unique) else len(text)
        chunk = text[start:end].strip()
        if len(chunk) < 60:
            continue
        questions.append({"number": qnum, "text": chunk})
    return questions

# ============================================================
# AREA DETECTION (v6 — strong markers, age-aware, no leakage)
# Each Revalida exam has 100 questions covering 5 areas.
# Questions are interleaved (not blocked); each one carries its own
# clinical case markers. We anchor the AREA from those markers BEFORE
# choosing a subtopic.
# ============================================================
PED_MARKERS = [
    # Termos demograficos / etarios pediatricos
    r"\bcrianca\b", r"\blactente\b", r"\bescolar\b", r"\bpre-?escolar\b",
    r"\brecem-?nascido\b", r"\brn\s+a\s+termo\b", r"\bneonat[oa]\b",
    r"\bbebe\s+(de|com)\b",  # 'bebe de 2 meses', 'bebe com'
    # "menina/menino de/com X anos" para idades 0-17 (texto numerico ou por extenso)
    r"\b(uma\s+)?(menina|menino)\s+(de|com)\s+([0-9]|1[0-7])\s+anos\b",
    r"\b(uma\s+)?(menina|menino)\s+(de|com)\s+(um|dois|tres|quatro|cinco|seis|sete|oito|nove|dez|onze|doze|treze|quatorze|catorze|quinze|dezesseis|dezessete)\s+anos\b",
    # idades em meses/dias (so pediatricas)
    r"\bcom\s+\d+\s+(meses|dias)\s+de\s+(vida|idade)\b",
    r"\bidade\s+gestacional\s+ao\s+nascimento\b",
    # adolescente especificamente (com idade ou contexto)
    r"\badolescente\s+(de|com)\s+(1[0-9])\s+anos\b",
    # Conceitos / estruturas pediatricas
    r"\bpedi[aá]tric[oa]\b", r"\bpueric",
    r"\baleitamento\s+materno\b", r"\bcaderneta\s+da\s+crianca\b",
    r"\bcalendario\s+(nacional\s+)?de\s+vacinacao\s+da\s+crianca\b",
    r"\bbronquiolite\b", r"\bicter[ií]cia\s+neonat",
    r"\bapgar\b", r"\bcurva\s+de\s+crescimento\b",
    r"\btriagem\s+neonatal\b",
    r"\b(criancas|adolescentes)\s+(de|menores|com\s+idade)\b",
]

GO_MARKERS = [
    r"\bgestante\b", r"\bgravidez\b", r"\bgravida\b",
    r"\bidade\s+gestacional\b", r"\bsemanas?\s+de\s+gestacao\b",
    r"\bpre-?natal\b", r"\bpuerpera\b", r"\bpuerperio\b",
    r"\btrabalho\s+de\s+parto\b", r"\bpos-?parto\b",
    r"\bcesariana\b", r"\bcesarea\b",
    r"\bmamogram", r"\bcolo\s+ut", r"\bovari[oa]\b",
    r"\bcolpocitologia\b", r"\bpapanicola", r"\bmenarca\b", r"\bmenopausa\b",
    r"\bmultigesta\b", r"\bmultipara\b", r"\bnuligesta\b", r"\bnulipara\b",
    r"\bprimigesta\b", r"\bprimipara\b",
    r"\bpre-eclampsia\b", r"\beclampsia\b", r"\bplacenta\b",
    r"\bdescolamento\s+prematuro\b", r"\babortamento\b", r"\bgravidez\s+ectopica\b",
    r"\bcontraceptiv", r"\bplanejamento\s+familiar\b", r"\bdiu\s+de\s+cobre\b",
    r"\bnic\s+i\b", r"\bnic\s+ii\b", r"\bnic\s+iii\b",
    r"\bginecolog", r"\bobstetric", r"\bvulvovagin",
    r"\bcorrimento\s+vaginal\b", r"\bsangramento\s+uterino\b",
    r"\bsifilis\s+gestacion", r"\bsifilis\s+na\s+gestacao\b",
    r"\btoxoplasmose\s+gestacional\b",
    r"\bdoenca\s+inflamatoria\s+pelvica\b", r"\bdip\b",
    r"\bteratoma\s+ovariano\b", r"\bcisto\s+ovariano\b",
]

CIR_MARKERS = [
    # Pos / pre operatorio
    r"\bpos-?operat", r"\bpre-?operat", r"\bperi-?operat", r"\bdia\s+pos-operatorio\b",
    r"\bcirurgia\s+(geral|abdominal|de\s+urgencia|eletiva)\b", r"\bcirurgico\b",
    r"\bemergencia\s+cirurgica\b", r"\bavaliacao\s+cirurgica\b",
    # Abdome agudo
    r"\babdome\s+agudo\b",
    r"\bapendicite\b", r"\bcolecistite\b", r"\bpancreatite\s+aguda\b",
    r"\bdiverticulite\b", r"\bcolelitiase\b", r"\bcoledocolitiase\b",
    r"\bcolangite\b", r"\bcolangiopancreatografia\b", r"\bcpre\b",
    r"\bperitonite\b", r"\bdor\s+em\s+fossa\s+iliaca\s+direita\b",
    r"\balvarado\b", r"\bsinal\s+de\s+(murphy|blumberg|rovsing)\b",
    # Trauma
    r"\btrauma\b", r"\bpolitraumat", r"\batls\b", r"\bfratura\b",
    r"\bferimento\s+por", r"\bperfurac.{1,3}o\s+(intestin|por\s+arma|abdom)",
    r"\bferimento\s+(por\s+)?arma", r"\bacidente\s+(de\s+)?(transito|automobilistico)\b",
    r"\bvitima\s+de\s+(acidente|trauma|atropelamento)\b",
    r"\btce\s+(grave|moderado)\b", r"\btraumatismo\b",
    r"\bhematoma\s+(subdural|epidural)\b",
    # Queimaduras
    r"\bqueimadur", r"\bregra\s+dos?\s+9\b", r"\bparkland\b",
    # Hernias
    r"\bhernia\s+(inguinal|umbilical|femoral|incisional|hiatal)\b",
    r"\bhernia\s+encarcerada\b", r"\bhernia\s+estrangulada\b",
    # Obstrucao / vias biliares / GI
    r"\bobstrucao\s+intestinal\b", r"\bbridas\b", r"\bvolvo\b",
    r"\bsuboclusao\s+intestinal\b",
    r"\bvesicula\s+biliar\b", r"\bcoledoc",
    r"\bgastrectomia\b", r"\bcolectomia\b", r"\bgastroduodeno",
    r"\bcolostomia\b", r"\bileostomia\b",
    r"\bhemorragia\s+digestiv", r"\bhematemese\b", r"\bmelena\b", r"\benterorragia\b",
    r"\bulcera\s+(peptica|duodenal|gastrica)\b",
    # Toracica
    r"\bpneumotorax\b", r"\bhemotorax\b", r"\btamponamento\s+cardiac",
    r"\bdrenagem\s+toracica\b", r"\bdreno\s+de\s+torax\b",
    r"\btorax\s+instavel\b", r"\bcontusao\s+pulmonar\b",
    # Vascular
    r"\bisquemia\s+(mesenterica|aguda)\b", r"\baneurisma\s+de\s+aorta\b",
    r"\bvarizes\s+esofagianas\b",
    # Urologia cirurgica
    r"\bcalculo\s+(renal|ureteral|vesical)\b", r"\blitiase\s+(renal|urinaria)\b",
    r"\bnefrolitiase\b", r"\bureterolitiase\b", r"\bhematuria\b",
    r"\bretencao\s+urinaria\b", r"\bsondagem\s+vesical\b",
    r"\bcolica\s+(nefretica|renal)\b",
    r"\bdor\s+(em\s+)?(colica|tipo\s+colica)\s+(em\s+regiao\s+)?lombar\b",
    # Proctologia
    r"\bfissura\s+anal\b", r"\bfistula\s+(anal|perianal)\b",
    r"\bhemorroid", r"\bplastia\s+anal\b",
    # Mama / Tireoide cirurgicas
    r"\bnodulo\s+(de\s+)?mama\b", r"\bbi-rads\s+[345]\b", r"\bbirads\s+[345]\b",
    r"\bcancer\s+de\s+mama\b", r"\btireoidectomia\b",
    # Ferimentos / abscessos / curativos
    r"\babscess[oa]\s+(perianal|de\s+parede|cutaneo)\b",
    r"\bferida\s+operatoria\b", r"\bdeiscencia\s+de\s+ferida\b",
    r"\bsutura\b",
    # Choque / anestesia
    r"\bchoque\s+hipovolemic", r"\bchoque\s+hemorragic",
    r"\branticoagulacao\s+pos\b", r"\benoxaparina\s+pos\b",
    r"\bsindrome\s+compartimental\b",
    # Procedimentos
    r"\bcorpo\s+estranho\b", r"\baspirac.{1,3}o\s+de\s+corpo", r"\bingestao\s+de\s+corpo\s+estranho\b",
    r"\bcricotireoidostomia\b", r"\bintubacao\s+orotraqueal\b",
]

PREV_MARKERS = [
    # ===== Marcadores STRONG (especificos de tema preventivo) =====
    r"\bsus\b", r"\blei\s+8\.?080\b", r"\blei\s+8\.?142\b", r"\bdecreto\s+7\.?508\b",
    r"\bvigilancia\s+(epidemiologica|sanitaria|em\s+saude|nutricional|do\s+trabalhador)\b",
    r"\bnotificacao\s+compulsoria\b",
    r"\bnotificar\s+(o\s+caso|imediatamente|em\s+ate|essa\s+doenca)\b",
    r"\bsinan\b", r"\bsinasc\b",
    # Modelos / atributos APS
    r"\batributo\s+(essencial|derivado)\s+da\s+aps\b",
    r"\bmodelo\s+de\s+atencao\s+a\s+saude\b",
    r"\bprincipio\s+(do\s+sus|doutrinario)\b",
    # Epidemiologia
    r"\bcoeficiente\s+de\s+mortalidade\b", r"\btaxa\s+de\s+mortalidade\b",
    r"\bestudo\s+(de\s+coorte|transversal|ecologico|caso-controle|controlado)\b",
    r"\bensaio\s+clinico\s+randomizado\b",
    r"\bsensibilidade\s+(e|/)\s+especificidade\b", r"\bvalor\s+preditivo\b",
    r"\brisco\s+relativo\b", r"\bodds\s+ratio\b", r"\bnumero\s+necessario",
    r"\bcurva\s+roc\b", r"\bp\s+valor\b", r"\bintervalo\s+de\s+confianca\b",
    # Niveis de prevencao (conceito explicito)
    r"\bnivel\s+de\s+prevencao\b", r"\bniveis\s+de\s+prevencao\b",
    r"\bprevencao\s+(primaria|secundaria|terciaria|quaternaria|primordial)\b",
    r"\bleavell\s+(e|&)\s+clark\b", r"\bclassificacao\s+de\s+leavell\b",
    # Saude do trabalhador
    r"\bler\s*/\s*dort\b", r"\bnorma\s+regulamentadora\b", r"\bnr-?\d",
    r"\bocupacional\b", r"\bsaude\s+do\s+trabalhador\b",
    r"\bfinanciamento\s+do\s+sus\b",
    # Surtos
    r"\bsurto\s+(de|epidemico|alimentar)\b", r"\bepidemia\s+de\b",
    r"\binvestigacao\s+epidemiologica\b", r"\bcurva\s+epidemica\b",
    # Indicadores / Politicas
    r"\bdesigualdade\s+em\s+saude\b",
    r"\bindicador\s+de\s+saude\b", r"\btransicao\s+(epidemiologica|demografica)\b",
    r"\bdeterminante\s+social\s+da\s+saude\b",

    # ===== Marcadores MODERATE (acao preventiva sem ser clínico individual) =====
    # Sao avaliados DEPOIS dos markers de Pediatria/G&O/Cirurgia, entao só capturam
    # questões claramente preventivas (sem caso clinico de outra area).
    r"\brastreamento\s+(de|do|da|para|em|populacional)\b",
    r"\brastreio\s+(de|do|da|para)\b",
    r"\bscreening\s+(de|do|da|para|em)\b",
    r"\bpromocao\s+da\s+saude\b", r"\bprotecao\s+da\s+saude\b",
    r"\batencao\s+primaria\s+a?\s*saude\b",
    r"\bestrategia\s+saude\s+da\s+familia\b",
    r"\bagente\s+comunitario\s+de\s+saude\b",
    r"\bequipe\s+(da\s+)?saude\s+da\s+familia\b",
    r"\bprograma\s+saude\s+da\s+familia\b",
    r"\bnasf\b",
    r"\bcadastro\s+da\s+familia\b", r"\bterritorializacao\b",
    r"\bcalendario\s+nacional\s+de\s+vacinacao\b",
    r"\bpolitica\s+nacional\s+de\s+(saude|atencao)\b",
    r"\bplanejamento\s+em\s+saude\b",
    r"\bbioetica\b", r"\bcfm\b", r"\bcrm\b",
    r"\bmaus-tratos\b", r"\bviolencia\s+(domestica|sexual|contra\s+a\s+mulher|contra\s+a\s+crianca)\b",
    r"\bestatuto\s+da\s+crianca\s+e\s+do\s+adolescente\b",
    r"\bconselho\s+tutelar\b",
]


# Marcadores de TOPICO PREVENTIVO FORTES — sobrescrevem Clinica/Cirurgia.
# (Não sobrescrevem Pediatria ou G&O porque uma criança/gestante com câncer
#  ainda é Pediatria/G&O — a quest é sobre seu manejo, não rastreio populacional.)
PREV_TOPIC_OVERRIDE = [
    # Rastreamentos de cancer (population-level)
    r"\brastreamento\s+(de|do)\s+cancer\b",
    r"\bdiretrizes?\s+do\s+inca\b",
    r"\binca\s+(recomenda|preconiza)",
    r"\bmamografia\s+de\s+rastreamento\b",
    r"\bmamografia\s+(bianual|anual|de\s+rotina|preventiva|de\s+screening)\b",
    r"\bpapanicola", r"\bcolpocitologia\s+oncotica\b",
    r"\bpsof\b", r"\bsangue\s+oculto\s+nas\s+fezes\b",
    r"\bcolonoscopia\s+(de\s+)?(rastreio|rastreamento|para\s+rastreio)\b",
    r"\bpsa\s+(de\s+rastreamento|para\s+screening)\b",
    r"\btomografia\s+de\s+baixa\s+dose\b",
    r"\bdiretriz\s+de\s+rastreamento\b",
    # Rastreamentos de doencas cronicas (population-level — assintomaticos)
    r"\brastreamento\s+(de|do|da|para)\s+(diabetes|hipertensao|dislipidemia|has|dm|doenca\s+cronica)\b",
    r"\brastreio\s+(de|do|da)\s+(diabetes|hipertensao|dislipidemia|has|dm)\b",
    r"\bsobre\s+o\s+rastreamento\b",
    r"\brastrear\s+(diabetes|hipertensao)\b",
    r"\b(paciente|adulto)\s+assintomatic[oa].*(rastreamento|rastreio)\b",
    r"\bcheck-?up\s+(em|para)\s+adulto\b",
    # Niveis de prevencao explicito
    r"\bnivel(\s+de|is\s+de)\s+prevencao\b",
    r"\bprevencao\s+(primaria|secundaria|terciaria|quaternaria|primordial)\b",
    r"\bleavell\s+(e|&)\s+clark\b",
    r"\bsobrediagnostico\b", r"\bsobretratamento\b",
    r"\bdisease\s+mongering\b", r"\bmedicalizacao\s+excessiva\b",
    # SUS legislacao / vigilancia
    r"\blei\s+8\.?(080|142)\b", r"\bdecreto\s+7\.?508\b",
    r"\bnotificacao\s+compulsoria\b", r"\bsinan\b",
    # Epidemiologia
    r"\bestudo\s+(de\s+coorte|caso-controle|transversal|ecologico)\b",
    r"\bensaio\s+clinico\s+randomizado\b",
    r"\bcurva\s+roc\b", r"\bvalor\s+preditivo\b",
    # Aconselhamento populacional / Promocao da saude
    r"\bcessacao\s+(do\s+)?tabagismo\b",
    r"\babordagem\s+(do\s+)?fumante\b",
    r"\baconselhamento\s+(breve|para\s+cessacao)\b",
    r"\bentrevista\s+motivacional\b",
    # Saude do trabalhador
    r"\bler\s*/\s*dort\b", r"\bnorma\s+regulamentadora\b",
    r"\bcat\s*-\s*comunicacao\s+de\s+acidente\b",
]


def detect_area(qtext: str) -> str:
    """Return the strongest area for this question. Defaults to Clinica Medica.

    Hierarchy:
      1) PREV_TOPIC_OVERRIDE — population-level prevention/SUS/epidem topics → Preventiva
         (UNLESS the patient is a child or a gestante — then Pediatria/G&O wins because
          even prevention questions about kids/pregnant women belong to that area)
      2) Pediatria (children, no gestation context)
      3) G&O (gestation, gynecology)
      4) Cirurgia
      5) Med. Preventiva (other moderate markers)
      6) Clinica Medica (default)
    """
    n = normalize(qtext)
    has_gestational = any(
        re.search(g, n) for g in [r"\bgestante\b", r"\bgravida\b", r"\bidade\s+gestacional\b",
                                   r"\bpre-?natal\b", r"\bsemanas?\s+de\s+gestacao\b",
                                   r"\bprimigesta\b", r"\bmultigesta\b", r"\bnuligesta\b"]
    )
    has_ped = any(re.search(p, n) for p in PED_MARKERS)

    # Hard override: explicit population-level prevention topic
    if any(re.search(p, n) for p in PREV_TOPIC_OVERRIDE):
        if not has_ped and not has_gestational:
            return "Med. Preventiva"

    # Pediatria first (children) — but EXCLUDE if patient is gestante
    if has_ped and not has_gestational:
        return "Pediatria"
    # GO
    if any(re.search(p, n) for p in GO_MARKERS) or has_gestational:
        return "Ginecologia & Obstetricia"
    # Cirurgia
    if any(re.search(p, n) for p in CIR_MARKERS):
        return "Cirurgia Geral"
    # Preventiva (moderate markers)
    if any(re.search(p, n) for p in PREV_MARKERS):
        return "Med. Preventiva"
    return "Clinica Medica"


# Generic fallback subtopics when no rule matches inside the detected area
FALLBACK_SUBTOPICS = {
    "Pediatria": ("ped-99", "Pediatria — Outros Temas (Caso Clinico Pediatrico)"),
    "Ginecologia & Obstetricia": ("go-99", "G&O — Outros Temas (Caso Clinico Ginecologico/Obstetrico)"),
    "Cirurgia Geral": ("cir-99", "Cirurgia — Outros Temas (Caso Clinico Cirurgico)"),
    "Med. Preventiva": ("prev-99", "Saude Coletiva — Outros Temas (Politicas/SUS/Indicadores)"),
    "Clinica Medica": ("cli-99", "Clinica Medica — Outros Temas (Caso Clinico)"),
}


def classify_question(qtext):
    """Two-stage classifier:
    1) Detect AREA from strong markers (age/gestational/surgical/preventive).
    2) Choose the best matching subtopic RULE *within that area* by length-weighted score.
       Longer keywords carry more weight (more specific). Tie-breaker: longest keyword
       matched first wins. If no subtopic in the area matches, return the area's fallback.
    """
    ntext = normalize(qtext)
    area = detect_area(qtext)

    best_score, best_rule, best_max_kw_len = 0, None, 0
    for rule in RULES:
        if rule["area"] != area:
            continue
        score = 0
        max_kw_len_matched = 0
        for kw in rule["kw"]:
            nkw = normalize(kw)
            kw_len = len(nkw)
            matched = False
            if kw_len <= 4:
                if re.search(r'\b' + re.escape(nkw) + r'\b', ntext):
                    matched = True
            else:
                if nkw in ntext:
                    matched = True
            if matched:
                # Length-weighted: a 25-char keyword counts ~5× more than a 5-char one.
                # Cap at 40 to avoid one super-long keyword swamping multi-keyword matches.
                score += min(kw_len, 40)
                max_kw_len_matched = max(max_kw_len_matched, kw_len)

        # Higher score wins. Ties broken by the longest matched keyword (more specific).
        if score > best_score or (score == best_score and max_kw_len_matched > best_max_kw_len):
            best_score, best_rule, best_max_kw_len = score, rule, max_kw_len_matched

    # Require at least one keyword of length ≥ 5 to claim a specific subtopic.
    # Below that, keep the question in the area-level fallback.
    if best_rule and best_max_kw_len >= 5:
        return best_rule

    fb_id, fb_name = FALLBACK_SUBTOPICS[area]
    return {"area": area, "topicId": fb_id, "subtopic": fb_name, "kw": []}

def extract_options(qtext):
    letter_positions = list(re.finditer(r'\n([A-D])\s{2,}', qtext))
    if len(letter_positions) < 3:
        return []
    seen = set()
    opt_starts = []
    for m in reversed(letter_positions):
        letter = m.group(1)
        if letter not in seen:
            seen.add(letter)
            opt_starts.append(m)
    opt_starts.reverse()
    if len(opt_starts) < 3:
        return []
    options = []
    for i, m in enumerate(opt_starts):
        letter = m.group(1)
        content_start = m.start() + len(m.group(0))
        content_end = opt_starts[i + 1].start() if i + 1 < len(opt_starts) else len(qtext)
        content = qtext[content_start:content_end]
        clean = re.sub(r'\s+', ' ', content.strip())
        options.append(f"{letter}) {clean}")
    return options

def clean_question_text(qtext):
    text = re.sub(r'QUEST[ÃA]O\s+\d{1,3}\s*', '', qtext, flags=re.IGNORECASE)
    opt_markers = list(re.finditer(r'\nA\s{2,}', text))
    if opt_markers:
        opt_start = opt_markers[-1].start()
        if opt_start > 80:
            text = text[:opt_start]
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ============================================================
# OCR FALLBACK FOR CID-FONT PDFs (e.g. 2022)
# ============================================================
def ocr_pdf(pdf_path):
    """Attempt OCR on a PDF using Tesseract if available.
    Returns extracted text or empty string on failure.
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract

        # Try common Tesseract install paths on Windows
        for tess_path in [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\Felipe Erick\AppData\Local\Tesseract-OCR\tesseract.exe",
        ]:
            if Path(tess_path).exists():
                pytesseract.pytesseract.tesseract_cmd = tess_path
                break

        images = convert_from_path(pdf_path, dpi=250, first_page=1, last_page=4)
        # Only OCR first few pages to check readability
        texts = []
        for img in images:
            text = pytesseract.image_to_string(img, lang="por")
            texts.append(text)

        sample = "\n".join(texts)
        # Verify OCR worked (should have Portuguese words)
        if len(sample) > 500 and ("QUESTÃO" in sample or "questão" in sample):
            # If first pages OK, OCR the rest
            all_images = convert_from_path(pdf_path, dpi=250)
            full_text = "\n".join(
                pytesseract.image_to_string(img, lang="por")
                for img in all_images
            )
            return full_text
        return sample if len(sample) > 200 else ""
    except ImportError:
        return ""
    except Exception as e:
        print(f"  OCR attempt failed: {e}")
        return ""

# ============================================================
# MAIN PIPELINE
# ============================================================
def main():
    os.makedirs(str(PDF_DIR), exist_ok=True)

    # Find exam PDFs with both naming patterns
    exam_files = sorted(list(PDF_DIR.glob("*_PV_objetiva_*.pdf")))
    gabarito_files = sorted(list(PDF_DIR.glob("*_GB_objetiva*.pdf")))

    print(f"Found {len(exam_files)} exam PDFs and {len(gabarito_files)} answer key PDFs\n")

    all_questions = []
    qid = 1

    for exam_pdf in exam_files:
        fname = exam_pdf.name

        # Parse year and semester from filename
        # Pattern 1: 2023_1_PV_objetiva_regular.pdf → year=2023, sem=1
        # Pattern 2: 2022_PV_objetiva_1.pdf → year=2022, sem=1
        m = re.search(r'(\d{4})_(\d)_PV', fname)
        if not m:
            m = re.search(r'(\d{4})_PV_objetiva_(\d)', fname)
        if not m:
            print(f"  SKIP: cannot parse filename {fname}")
            continue

        year = m.group(1)
        sem = m.group(2)
        exam_ref = f"{year}/{sem}"

        print(f"\n{'='*60}")
        print(f"Processing: {fname} ({exam_ref})")
        print(f"{'='*60}")

        # Match gabarito by year AND semester
        gabarito = None
        for g in gabarito_files:
            if f"{year}_{sem}_" in g.name:
                gabarito = g
                break
            # Old pattern
            if f"{year}_GB_objetiva_{sem}" in g.name:
                gabarito = g
                break

        text = extract_text_by_column(str(exam_pdf))
        if not text:
            print(f"  SKIP: could not extract text")
            continue

        # Detect CID-encoded fonts (common in older INEP PDFs)
        cid_count = len(re.findall(r'\(cid:\d+\)', text, re.IGNORECASE))
        if cid_count > 500:
            print(f"  CID-encoded fonts detected ({cid_count} glyphs), attempting OCR...")
            ocr_text = ocr_pdf(str(exam_pdf))
            if ocr_text and len(ocr_text) > 1000:
                print(f"  OCR extracted {len(ocr_text)} chars, using OCR text")
                text = ocr_text
            else:
                print(f"  SKIP: OCR unavailable or failed, exam unreadable")
                continue

        answers = {}
        if gabarito:
            answers = parse_answer_key(str(gabarito))
            print(f"  Answer key: {len(answers)} answers parsed ({gabarito.name})")
        else:
            print(f"  WARNING: no gabarito found for {year}/{sem}")

        questions = extract_questions(text)
        print(f"  Questions detected: {len(questions)}")

        classified = 0
        for q in questions:
            qtext = q["text"]
            classification = classify_question(qtext)
            if not classification:
                continue

            answer = answers.get(q["number"], "?")
            options = extract_options(qtext)
            prompt = clean_question_text(qtext)

            if len(prompt) < 50:
                continue

            all_questions.append({
                "id": f"q-{qid:04d}",
                "topicId": classification["topicId"],
                "subtopic": classification["subtopic"],
                "examRef": exam_ref,
                "questionNumber": q["number"],
                "area": classification["area"],
                "questionText": prompt,
                "options": options if len(options) >= 3 else [
                    "A) Ver PDF original",
                    "B) Ver PDF original",
                    "C) Ver PDF original",
                    "D) Ver PDF original"
                ],
                "correctAnswer": answer,
                "explanation": "",
            })
            classified += 1
            qid += 1

        print(f"  Questions classified: {classified}")

    # Save
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"TOTAL classified questions: {len(all_questions)}")
    print(f"Output: {OUT_FILE}")

    by_subtopic = {}
    by_area = {}
    for q in all_questions:
        st, ar = q["subtopic"], q["area"]
        by_subtopic[st] = by_subtopic.get(st, 0) + 1
        by_area[ar] = by_area.get(ar, 0) + 1

    print("\n--- By Area ---")
    for k, v in sorted(by_area.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    print("\n--- Top 30 Subtopics ---")
    for k, v in sorted(by_subtopic.items(), key=lambda x: -x[1])[:30]:
        print(f"  [{v:3d}] {k}")

if __name__ == "__main__":
    main()
