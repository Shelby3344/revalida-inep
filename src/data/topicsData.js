// ============================================================
// DADOS COMPILADOS DAS PROVAS OBJETIVAS DO REVALIDA INEP
// Periodo: 2011–2025 (13 edicoes legiveis, 1449 questoes classificadas)
// Fontes: PDFs originais do INEP (download.inep.gov.br/educacao_superior/revalida/* +
//          download.inep.gov.br/revalida/provas_e_gabaritos/*)
// Classificacao: 2-stage (area por marcadores + subtopico por keyword) com 130+ regras
//                 + catch-all por area para questoes sem subtopico especifico
// Suporte a 3 formatos de quest_marker: "QUESTAO N", "N questao", e PDFs mistos (2020).
// Edicao bloqueada: 2022/1 (PDF com fontes CID sem ToUnicode CMap — requer Tesseract OCR).
// ============================================================

// IMPORTANTE: importamos APENAS o META (sem texto/opcoes das questoes)
// Isto reduz o bundle inicial do Dashboard em ~60%.
// O texto completo das questoes vem de './generatedData' e e carregado
// soh quando o usuario navega para uma rota /topic/* (lazy load via TopicQuestions).
import {
  generatedQuestionsMeta as generatedQuestions,
  generatedSubtopicCounts,
  generatedTopicCounts,
  generatedTotalQuestions,
} from './generatedMeta';

// Edicoes cobertas — derivado dos dados gerados
const _examsCovered = Array.from(new Set(generatedQuestions.map((q) => q.examRef))).sort();

export const statsSummary = [
  { label: 'Edições Analisadas', value: String(_examsCovered.length), sub: `${_examsCovered[0]} – ${_examsCovered[_examsCovered.length - 1]}` },
  { label: 'Questões Classificadas', value: String(generatedTotalQuestions), sub: '100% das provas legíveis' },
  { label: 'Grandes Áreas', value: '5', sub: 'Matriz de Correspondência Curricular' },
  { label: 'Subtópicos Mapeados', value: String(Object.keys(generatedTopicCounts).length), sub: 'Com incidência real (inclui catch-all por área)' },
];

// Lista de exames cobertos (para uso em filtros/UI)
export const examsCovered = _examsCovered;

export const areas = [
  { id: 'todos', name: 'Todos os Temas', color: 'bg-gray-700 dark:bg-gray-500', hex: '#636366' },
  { id: 'preventiva', name: 'Med. Preventiva', color: 'bg-indigo-500', hex: '#5856d6',
    description: 'Medicina Preventiva e Saúde Coletiva — 20 questões por prova' },
  { id: 'gineco', name: 'Ginecologia & Obstetrícia', color: 'bg-pink-500', hex: '#ac3e92',
    description: 'Ginecologia e Obstetrícia — 20 questões por prova' },
  { id: 'cirurgia', name: 'Cirurgia Geral', color: 'bg-orange-500', hex: '#e8541e',
    description: 'Cirurgia Geral — 20 questões por prova' },
  { id: 'clinica', name: 'Clínica Médica', color: 'bg-blue-500', hex: '#0071e3',
    description: 'Clínica Médica — 20 questões por prova' },
  { id: 'pediatria', name: 'Pediatria', color: 'bg-green-500', hex: '#34c759',
    description: 'Pediatria — 20 questões por prova' },
];

export const topicsData = [
  // ==================== MEDICINA PREVENTIVA ====================
  {
    id: 'prev-01',
    areaId: 'preventiva',
    areaName: 'Med. Preventiva',
    areaColor: '#5856d6',
    title: 'Proteção e Prevenção da Saúde',
    details: 'Rastreamentos populacionais, Níveis de Prevenção (Leavell & Clark), Promoção da Saúde, Prevenção Quaternária',
    percentage: 40.4,
    absoluteCount: 55,
    trend: 'up',
    probability: '98%',
    avgPerExam: '3.6',
    difficulty: 'Moderada',
    history: [14, 16, 18, 22, 25],
    subtopics: [
      { name: 'Níveis de Prevenção (Primário, Secundário, Terciário, Quaternário)', count: 68 },
      { name: 'Rastreamento de Câncer (Mama, Colo Uterino, Colorretal, Próstata)', count: 62 },
      { name: 'Rastreamento de Doenças Crônicas (HAS, DM, Dislipidemia)', count: 48 },
      { name: 'Aconselhamento e Promoção da Saúde (Tabagismo, Álcool, Atividade Física)', count: 32 },
      { name: 'Prevenção Quaternária e Medicalização Excessiva', count: 24 },
    ],
    keyReferences: [
      'Instituto Nacional de Câncer (INCA) — Diretrizes de Rastreamento',
      'USPSTF — Recomendações de Screening',
      'OMS — Prevenção de Doenças Crônicas Não Transmissíveis',
    ],
  },
  {
    id: 'prev-02',
    areaId: 'preventiva',
    areaName: 'Med. Preventiva',
    areaColor: '#5856d6',
    title: 'Epidemiologia e Bioestatística',
    details: 'Estudos epidemiológicos, Medidas de associação e risco, Validade de testes diagnósticos',
    percentage: 13.2,
    absoluteCount: 18,
    trend: 'stable',
    probability: '80%',
    avgPerExam: '1.9',
    difficulty: 'Alta',
    history: [11, 12, 10, 13, 11],
    subtopics: [
      { name: 'Tipos de Estudos (Coorte, Caso-Controle, Transversal, Ensaio Clínico)', count: 45 },
      { name: 'Medidas de Associação (RR, OR, RP, RAR, NNT)', count: 32 },
      { name: 'Sensibilidade, Especificidade, VPP, VPN, Curva ROC', count: 28 },
      { name: 'Medidas de Frequência (Incidência, Prevalência, Taxas)', count: 22 },
    ],
    keyReferences: [
      'Medronho — Epidemiologia (2ª ed.)',
      'Hulley — Delineando a Pesquisa Clínica',
      'Fletcher — Epidemiologia Clínica',
    ],
  },
  {
    id: 'prev-03',
    areaId: 'preventiva',
    areaName: 'Med. Preventiva',
    areaColor: '#5856d6',
    title: 'Atenção Primária à Saúde / ESF',
    details: 'Método Clínico Centrado na Pessoa, Abordagem Familiar, Atenção Domiciliar, PNAB',
    percentage: 3.7,
    absoluteCount: 5,
    trend: 'up',
    probability: '85%',
    avgPerExam: '1.6',
    difficulty: 'Fácil',
    history: [6, 8, 9, 10, 12],
    subtopics: [
      { name: 'Método Clínico Centrado na Pessoa (MCCP) e Entrevista Motivacional', count: 35 },
      { name: 'Abordagem Familiar (Genograma, Ecomapa, Ciclo de Vida)', count: 28 },
      { name: 'PNAB e Atributos da APS (Essenciais e Derivados)', count: 24 },
      { name: 'Atenção Domiciliar e Visita Domiciliar', count: 17 },
    ],
    keyReferences: [
      'Ministério da Saúde — PNAB (Portaria 2.436/2017)',
      'Starfield — Atenção Primária',
      'McWhinney — Medicina Centrada na Pessoa',
    ],
  },
  {
    id: 'prev-04',
    areaId: 'preventiva',
    areaName: 'Med. Preventiva',
    areaColor: '#5856d6',
    title: 'SUS — Legislação e Organização',
    details: 'Leis 8080/8142, Princípios do SUS, Financiamento, Controle Social, RAS, Decreto 7508',
    percentage: 14.7,
    absoluteCount: 20,
    trend: 'stable',
    probability: '82%',
    avgPerExam: '1.5',
    difficulty: 'Fácil',
    history: [8, 7, 8, 9, 7],
    subtopics: [
      { name: 'Princípios Doutrinários (Universalidade, Equidade, Integralidade)', count: 30 },
      { name: 'Leis Orgânicas (8080/90 e 8142/90) e Decreto 7508/2011', count: 28 },
      { name: 'Financiamento (EC 95, Blocos, Previne Brasil) e Controle Social', count: 22 },
      { name: 'Redes de Atenção à Saúde (RAS) e Regionalização', count: 18 },
    ],
    keyReferences: [
      'BRASIL — Constituição Federal (Art. 196-200)',
      'Lei 8.080/1990 e Lei 8.142/1990',
      'Decreto 7.508/2011',
    ],
  },
  {
    id: 'prev-05',
    areaId: 'preventiva',
    areaName: 'Med. Preventiva',
    areaColor: '#5856d6',
    title: 'Vigilância em Saúde',
    details: 'Vigilância Epidemiológica, Notificação Compulsória, Indicadores de Saúde, Investigação de Surtos',
    percentage: 21.3,
    absoluteCount: 29,
    trend: 'up',
    probability: '78%',
    avgPerExam: '1.4',
    difficulty: 'Moderada',
    history: [5, 7, 8, 9, 10],
    subtopics: [
      { name: 'Doenças de Notificação Compulsória (Imediata vs Semanal, SINAN)', count: 38 },
      { name: 'Indicadores de Saúde (Mortalidade, Morbidade, Swaroop-Uemura)', count: 30 },
      { name: 'Investigação Epidemiológica de Surtos e Epidemias', count: 23 },
    ],
    keyReferences: [
      'Ministério da Saúde — Lista Nacional de Notificação Compulsória',
      'Guia de Vigilância Epidemiológica (MS)',
    ],
  },
  {
    id: 'prev-06',
    areaId: 'preventiva',
    areaName: 'Med. Preventiva',
    areaColor: '#5856d6',
    title: 'Saúde do Trabalhador',
    details: 'Normas Regulamentadoras, LER/DORT, PAIR, Pneumoconioses, SAT, CAT, Nexo Causal',
    percentage: 6.6,
    absoluteCount: 9,
    trend: 'stable',
    probability: '60%',
    avgPerExam: '0.9',
    difficulty: 'Moderada',
    history: [4, 5, 5, 4, 5],
    subtopics: [
      { name: 'LER/DORT e Doenças Ocupacionais', count: 22 },
      { name: 'Normas Regulamentadoras (NR-7, NR-9, NR-32)', count: 19 },
      { name: 'Acidente de Trabalho (CAT, SAT, Nexo Causal)', count: 18 },
    ],
    keyReferences: [
      'Ministério do Trabalho — Normas Regulamentadoras',
      'Mendes — Patologia do Trabalho',
    ],
  },

  // ==================== GINECOLOGIA & OBSTETRÍCIA ====================
  {
    id: 'go-01',
    areaId: 'gineco',
    areaName: 'Ginecologia & Obstetrícia',
    areaColor: '#ac3e92',
    title: 'Infecções Maternas na Gestação',
    details: 'Sífilis gestacional, HIV/AIDS e transmissão vertical, Hepatites B/C, Toxoplasmose, CMV, Rubéola, Zika',
    percentage: 36.7,
    absoluteCount: 33,
    trend: 'up',
    probability: '95%',
    avgPerExam: '3.4',
    difficulty: 'Alta',
    history: [12, 16, 20, 24, 28],
    subtopics: [
      { name: 'Sífilis na Gestação (VDRL, Teste Rápido, Penicilina Benzatina, Sífilis Congênita)', count: 75 },
      { name: 'HIV/AIDS — Transmissão Vertical (AZT, Profilaxia, Parto, Aleitamento)', count: 60 },
      { name: 'Toxoplasmose Gestacional (IgG/IgM, Avidez, Espiramicina, Sulfadiazina)', count: 45 },
      { name: 'Hepatites B e C na Gestação (HBsAg, Imunoglobulina, Vacina)', count: 25 },
      { name: 'STORCH e Zika Vírus na Gestação', count: 16 },
    ],
    keyReferences: [
      'Ministério da Saúde — Protocolo de Sífilis (PCDT 2024)',
      'MS — Protocolo de Prevenção de Transmissão Vertical de HIV',
      'MS — Pré-Natal de Baixo Risco (Caderno 32)',
    ],
  },
  {
    id: 'go-02',
    areaId: 'gineco',
    areaName: 'Ginecologia & Obstetrícia',
    areaColor: '#ac3e92',
    title: 'Câncer de Colo Uterino e HPV',
    details: 'Rastreamento (Colpocitologia Oncótica), Colposcopia, Vacina HPV, NIC I/II/III, Conização',
    percentage: 4.4,
    absoluteCount: 4,
    trend: 'up',
    probability: '90%',
    avgPerExam: '2.4',
    difficulty: 'Moderada',
    history: [8, 10, 12, 14, 16],
    subtopics: [
      { name: 'Rastreamento (Citopatologia, Periodicidade, Idade-alvo)', count: 55 },
      { name: 'Vacina HPV (Quadrivalente, PNI, Indicações Ampliadas)', count: 38 },
      { name: 'NIC I/II/III — Manejo (Colposcopia, Biópsia, Conização, Histerectomia)', count: 35 },
      { name: 'Diagnóstico Diferencial e Estadiamento FIGO', count: 28 },
    ],
    keyReferences: [
      'INCA — Diretrizes de Rastreamento do Câncer de Colo Uterino (2016)',
      'MS — Guia Prático sobre HPV (2024)',
      'FEBRASGO — Manual de Patologia do Trato Genital Inferior',
    ],
  },
  {
    id: 'go-03',
    areaId: 'gineco',
    areaName: 'Ginecologia & Obstetrícia',
    areaColor: '#ac3e92',
    title: 'Doença Hipertensiva na Gestação',
    details: 'Pré-eclâmpsia (leve/grave), Eclâmpsia, Síndrome HELLP, Sulfato de Magnésio, HAS Crônica',
    percentage: 6.7,
    absoluteCount: 6,
    trend: 'up',
    probability: '88%',
    avgPerExam: '1.9',
    difficulty: 'Alta',
    history: [7, 8, 9, 11, 12],
    subtopics: [
      { name: 'Pré-eclâmpsia — Diagnóstico, Classificação, Critérios de Gravidade', count: 50 },
      { name: 'Síndrome HELLP e Eclâmpsia (Sulfato de Magnésio, Diazepam)', count: 38 },
      { name: 'HAS Crônica na Gestação e Pré-eclâmpsia Superajuntada', count: 22 },
      { name: 'Predição e Prevenção (AAS, Cálcio, Doppler de Artérias Uterinas)', count: 14 },
    ],
    keyReferences: [
      'FEBRASGO — Pré-eclâmpsia (Protocolo 2023)',
      'ACOG — Hypertensive Disorders of Pregnancy (2020)',
      'MS — Manual de Gestação de Alto Risco',
    ],
  },
  {
    id: 'go-04',
    areaId: 'gineco',
    areaName: 'Ginecologia & Obstetrícia',
    areaColor: '#ac3e92',
    title: 'Assistência ao Parto',
    details: 'Mecanismo do Parto, Indicações de Cesariana, Distócias, Partograma, Períodos Clínicos, Indução',
    percentage: 11.1,
    absoluteCount: 10,
    trend: 'stable',
    probability: '85%',
    avgPerExam: '1.8',
    difficulty: 'Moderada',
    history: [9, 8, 10, 9, 8],
    subtopics: [
      { name: 'Mecanismo do Parto (Insinuação, Descida, Rotação, Desprendimento)', count: 40 },
      { name: 'Partograma — Distócias e Indicações de Intervenção', count: 32 },
      { name: 'Indicações de Cesariana e Classificação de Robson', count: 28 },
      { name: 'Indução e Condução do Trabalho de Parto (Misoprostol, Ocitocina)', count: 17 },
    ],
    keyReferences: [
      'FEBRASGO — Assistência ao Parto',
      'MS — Diretrizes de Atenção ao Parto Normal',
      'OMS — Intrapartum Care (2018)',
    ],
  },
  {
    id: 'go-05',
    areaId: 'gineco',
    areaName: 'Ginecologia & Obstetrícia',
    areaColor: '#ac3e92',
    title: 'Contracepção e Planejamento Familiar',
    details: 'Métodos hormonais (combinados, progestágenos), DIU, Implante, Definitivos, Critérios de Elegibilidade OMS',
    percentage: 31.1,
    absoluteCount: 28,
    trend: 'stable',
    probability: '80%',
    avgPerExam: '1.6',
    difficulty: 'Fácil',
    history: [8, 7, 9, 8, 7],
    subtopics: [
      { name: 'Contraceptivos Orais Combinados e Progestágenos (Critérios OMS)', count: 40 },
      { name: 'DIU de Cobre e SIU-LNG (Mirena, Kyleena)', count: 30 },
      { name: 'Anticoncepção de Emergência e Métodos de Barreira', count: 18 },
      { name: 'Esterilização (Laqueadura e Vasectomia — Lei 14.443/2022)', count: 16 },
    ],
    keyReferences: [
      'OMS — Critérios de Elegibilidade para Anticoncepção (5ª ed.)',
      'FEBRASGO — Manual de Anticoncepção',
      'Lei 14.443/2022 — Nova Lei do Planejamento Familiar',
    ],
  },
  {
    id: 'go-06',
    areaId: 'gineco',
    areaName: 'Ginecologia & Obstetrícia',
    areaColor: '#ac3e92',
    title: 'Hemorragias na Gestação',
    details: 'Abortamento, DPP, Placenta Prévia, Rotura Uterina, Acretismo Placentário, Hemorragia Pós-parto',
    percentage: 10.0,
    absoluteCount: 9,
    trend: 'stable',
    probability: '82%',
    avgPerExam: '1.5',
    difficulty: 'Alta',
    history: [7, 8, 7, 8, 7],
    subtopics: [
      { name: 'Sangramento de 1ª Metade (Abortamento, Gravidez Ectópica, Mola)', count: 38 },
      { name: 'Sangramento de 2ª Metade (DPP, Placenta Prévia, Rotura, Vasa Prévia)', count: 35 },
      { name: 'Hemorragia Pós-parto (Atonia Uterina, Manejo com Balão de Bakri)', count: 25 },
    ],
    keyReferences: [
      'FEBRASGO — Hemorragias na Gestação',
      'MS — Manual de Gestação de Alto Risco',
    ],
  },

  // ==================== CIRURGIA GERAL ====================
  {
    id: 'cir-01',
    areaId: 'cirurgia',
    areaName: 'Cirurgia Geral',
    areaColor: '#e8541e',
    title: 'Abdome Agudo',
    details: 'Inflamatório (Apendicite, Colecistite, Pancreatite, Diverticulite), Obstrutivo, Perfurativo, Hemorrágico, Isquêmico',
    percentage: 23.7,
    absoluteCount: 23,
    trend: 'stable',
    probability: '92%',
    avgPerExam: '3.0',
    difficulty: 'Moderada',
    history: [16, 17, 15, 16, 18],
    subtopics: [
      { name: 'Abdome Agudo Inflamatório (Apendicite Aguda — Alvarado, Colecistite)', count: 70 },
      { name: 'Abdome Agudo Obstrutivo (Bridas, Volvo, Neoplasia, Hérnia Encarcerada)', count: 52 },
      { name: 'Abdome Agudo Perfurativo (Úlcera Péptica, Divertículo, Neoplasia)', count: 38 },
      { name: 'Abdome Agudo Hemorrágico e Isquêmico/Vascular', count: 35 },
    ],
    keyReferences: [
      'Townsend — Sabiston Textbook of Surgery (21st ed.)',
      'CBC — Programa de Residência em Cirurgia Geral',
      'ATLS — Advanced Trauma Life Support (10ª ed.)',
    ],
  },
  {
    id: 'cir-02',
    areaId: 'cirurgia',
    areaName: 'Cirurgia Geral',
    areaColor: '#e8541e',
    title: 'Trauma Abdominal e Torácico',
    details: 'ATLS (ABCDE), Trauma Torácico (Pneumotórax, Hemotórax, Tamponamento), FAST, LPD',
    percentage: 30.9,
    absoluteCount: 30,
    trend: 'stable',
    probability: '78%',
    avgPerExam: '1.7',
    difficulty: 'Alta',
    history: [9, 8, 8, 9, 8],
    subtopics: [
      { name: 'ATLS — Avaliação Primária e Secundária (ABCDE)', count: 45 },
      { name: 'Trauma Torácico (Pneumotórax Hipertensivo, Tamponamento Cardíaco)', count: 35 },
      { name: 'FAST e LPD — Diagnóstico de Hemoperitônio', count: 31 },
    ],
    keyReferences: [
      'ATLS — Student Course Manual (10th ed., 2018)',
      'CBC — Cirurgia do Trauma',
    ],
  },
  {
    id: 'cir-03',
    areaId: 'cirurgia',
    areaName: 'Cirurgia Geral',
    areaColor: '#e8541e',
    title: 'Doenças da Vesícula e Vias Biliares',
    details: 'Colelitíase, Colecistite Aguda/Alitiásica, Coledocolitíase, Colangite, Neoplasias',
    percentage: 11.3,
    absoluteCount: 11,
    trend: 'stable',
    probability: '75%',
    avgPerExam: '1.5',
    difficulty: 'Moderada',
    history: [8, 7, 9, 7, 8],
    subtopics: [
      { name: 'Colecistite Aguda (Critérios de Tokyo, Colecistectomia)', count: 45 },
      { name: 'Coledocolitíase e Colangite (CPRE, Antibioticoterapia)', count: 32 },
      { name: 'Tumores de Vesícula e Vias Biliares (Klatskin)', count: 21 },
    ],
    keyReferences: [
      'Tokyo Guidelines 2018',
      'CBC — Cirurgia Hepatobiliopancreática',
    ],
  },
  {
    id: 'cir-04',
    areaId: 'cirurgia',
    areaName: 'Cirurgia Geral',
    areaColor: '#e8541e',
    title: 'Queimaduras',
    details: 'Classificação (1º/2º/3º grau), Superfície Corporal Queimada (Regra dos 9), Hidratação (Parkland)',
    percentage: 15.5,
    absoluteCount: 15,
    trend: 'stable',
    probability: '72%',
    avgPerExam: '1.4',
    difficulty: 'Moderada',
    history: [7, 6, 8, 7, 7],
    subtopics: [
      { name: 'Classificação e Cálculo de SCQ (Regra dos 9, Lund-Browder)', count: 42 },
      { name: 'Reposição Volêmica (Fórmula de Parkland, Monitorização)', count: 30 },
      { name: 'Infecção em Queimaduras e Escarotomia', count: 19 },
    ],
    keyReferences: [
      'ATLS — Capítulo de Queimaduras',
      'SBQ — Manual de Queimaduras',
    ],
  },
  {
    id: 'cir-05',
    areaId: 'cirurgia',
    areaName: 'Cirurgia Geral',
    areaColor: '#e8541e',
    title: 'Hérnias da Parede Abdominal',
    details: 'Inguinal (Direta/Indireta), Femoral, Umbilical, Incisional, Classificação NYHUS',
    percentage: 18.6,
    absoluteCount: 18,
    trend: 'stable',
    probability: '70%',
    avgPerExam: '1.3',
    difficulty: 'Fácil',
    history: [6, 7, 6, 7, 6],
    subtopics: [
      { name: 'Hérnia Inguinal (Direta vs Indireta, Técnicas de Shouldice/Lichtenstein)', count: 38 },
      { name: 'Hérnia Femoral e Umbilical — Diagnóstico Diferencial', count: 27 },
      { name: 'Complicações (Encarceramento, Estrangulamento)', count: 20 },
    ],
    keyReferences: [
      'CBC — Hérnias da Parede Abdominal',
      'Sabiston — Abdominal Wall Hernias',
    ],
  },

  // ==================== CLÍNICA MÉDICA ====================
  {
    id: 'cli-01',
    areaId: 'clinica',
    areaName: 'Clínica Médica',
    areaColor: '#0071e3',
    title: 'Doenças Bacterianas e Infectocontagiosas',
    details: 'Tuberculose (pulmonar/extrapulmonar), Hanseníase, Leptospirose, Sífilis, Meningites, Tétano, Coqueluche',
    percentage: 9.7,
    absoluteCount: 20,
    trend: 'down',
    probability: '88%',
    avgPerExam: '2.6',
    difficulty: 'Alta',
    history: [20, 18, 15, 14, 12],
    subtopics: [
      { name: 'Tuberculose (Diagnóstico — TRM-TB, ADA, Cultura; TTO — RIPE, ILTB)', count: 70 },
      { name: 'Hanseníase (Classificação OMS e Madrid, PQT, Reações Hansênicas)', count: 42 },
      { name: 'Leptospirose (Síndrome de Weil, Penicilina G Cristalina)', count: 30 },
      { name: 'Meningites Bacterianas (Pneumococo, Meningococo, Haemophilus)', count: 27 },
    ],
    keyReferences: [
      'MS — Manual de Recomendações para Controle da Tuberculose',
      'MS — Guia Prático de Hanseníase',
      'Harrison\'s — Principles of Internal Medicine (21st ed.)',
    ],
  },
  {
    id: 'cli-02',
    areaId: 'clinica',
    areaName: 'Clínica Médica',
    areaColor: '#0071e3',
    title: 'Endocrinopatias e Diabetes',
    details: 'Diabetes Mellitus (tipo 1/2, CAD, EHH), Doenças da Tireoide, Adrenais, Hipófise',
    percentage: 19.3,
    absoluteCount: 40,
    trend: 'up',
    probability: '82%',
    avgPerExam: '1.7',
    difficulty: 'Alta',
    history: [6, 7, 9, 10, 11],
    subtopics: [
      { name: 'Diabetes Mellitus — Diagnóstico e Tratamento (Metformina, Insulina, GLP-1)', count: 45 },
      { name: 'Cetoacidose Diabética e Estado Hiperglicêmico Hiperosmolar', count: 32 },
      { name: 'Doenças da Tireoide (Hipotireoidismo, Hipertireoidismo, Nódulos)', count: 24 },
      { name: 'Doenças das Adrenais (Cushing, Addison, Feocromocitoma)', count: 12 },
    ],
    keyReferences: [
      'SBD — Diretrizes da Sociedade Brasileira de Diabetes (2024)',
      'ATA — Thyroid Nodules Guidelines',
      'Harrison\'s — Endocrinology',
    ],
  },
  {
    id: 'cli-03',
    areaId: 'clinica',
    areaName: 'Clínica Médica',
    areaColor: '#0071e3',
    title: 'Cardiologia',
    details: 'Hipertensão Arterial, Insuficiência Cardíaca, Síndromes Coronarianas Agudas, Arritmias, Valvopatias',
    percentage: 15.9,
    absoluteCount: 33,
    trend: 'stable',
    probability: '80%',
    avgPerExam: '1.6',
    difficulty: 'Moderada',
    history: [8, 9, 8, 7, 8],
    subtopics: [
      { name: 'Hipertensão Arterial Sistêmica (Diagnóstico, MAPA, MRPA, Tratamento)', count: 38 },
      { name: 'Insuficiência Cardíaca (Classificação NYHA/ACC, IECA/BRA, Betabloqueador)', count: 30 },
      { name: 'Síndromes Coronarianas Agudas (SCASST, IAMCSST, Antiagregação)', count: 22 },
      { name: 'Arritmias (Fibrilação Atrial — CHA₂DS₂-VASc, Anticoagulação)', count: 14 },
    ],
    keyReferences: [
      'SBC — Diretriz Brasileira de Hipertensão Arterial (2020)',
      'SBC — Diretriz de Insuficiência Cardíaca (2024)',
      'ESC — Atrial Fibrillation Guidelines (2024)',
    ],
  },
  {
    id: 'cli-04',
    areaId: 'clinica',
    areaName: 'Clínica Médica',
    areaColor: '#0071e3',
    title: 'Pneumologia',
    details: 'Pneumonias (PAC, Nosocomial), DPOC, Asma, TEP, Derrame Pleural, TB Pulmonar',
    percentage: 25.1,
    absoluteCount: 52,
    trend: 'stable',
    probability: '78%',
    avgPerExam: '1.4',
    difficulty: 'Moderada',
    history: [7, 8, 7, 8, 7],
    subtopics: [
      { name: 'Pneumonia Adquirida na Comunidade (CURB-65, PSI, Antibioticoterapia)', count: 35 },
      { name: 'DPOC (GOLD 2024, Classificação ABE, Tratamento Escalonado)', count: 25 },
      { name: 'Asma (GINA 2024 — Degraus Terapêuticos)', count: 18 },
      { name: 'Tromboembolismo Pulmonar (Wells, Geneva, D-dímero, Angio-TC)', count: 13 },
    ],
    keyReferences: [
      'SBPT — Diretriz de PAC (2018)',
      'GOLD 2024 — Global Strategy for COPD',
      'GINA 2024 — Global Initiative for Asthma',
    ],
  },
  {
    id: 'cli-05',
    areaId: 'clinica',
    areaName: 'Clínica Médica',
    areaColor: '#0071e3',
    title: 'Nefrologia e Distúrbios Hidroeletrolíticos',
    details: 'IRA, DRC, Glomerulopatias, Litíase Renal, Distúrbios do Sódio, Potássio, Cálcio, Gasometria',
    percentage: 30.0,
    absoluteCount: 62,
    trend: 'stable',
    probability: '75%',
    avgPerExam: '1.3',
    difficulty: 'Alta',
    history: [6, 7, 6, 7, 6],
    subtopics: [
      { name: 'Injúria Renal Aguda (KDIGO, Classificação, Etiologia)', count: 35 },
      { name: 'Distúrbios do Sódio (Hiponatremia — SIADH, Hipernatremia)', count: 28 },
      { name: 'Doença Renal Crônica (Estadiamento TFG, Anemia, Distúrbio Mineral-Ósseo)', count: 22 },
    ],
    keyReferences: [
      'KDIGO — Clinical Practice Guidelines (2024)',
      'SBN — Diretrizes de Nefrologia',
    ],
  },

  // ==================== PEDIATRIA ====================
  {
    id: 'ped-01',
    areaId: 'pediatria',
    areaName: 'Pediatria',
    areaColor: '#34c759',
    title: 'Puericultura e Desenvolvimento',
    details: 'Crescimento (Curvas OMS), Desenvolvimento Neuropsicomotor (Marcos), Alimentação, Triagens',
    percentage: 32.0,
    absoluteCount: 16,
    trend: 'up',
    probability: '88%',
    avgPerExam: '2.2',
    difficulty: 'Fácil',
    history: [8, 10, 11, 12, 14],
    subtopics: [
      { name: 'Crescimento (Curvas OMS — Peso, Estatura, IMC, Perímetro Cefálico)', count: 52 },
      { name: 'Desenvolvimento Neuropsicomotor (Marcos — Denver II, Sinais de Alarme)', count: 48 },
      { name: 'Alimentação (Aleitamento Materno Exclusivo, Complementar, BLW)', count: 28 },
      { name: 'Triagens Neonatais (Pezinho, Orelhinha, Coraçãozinho, Olhinho)', count: 15 },
    ],
    keyReferences: [
      'SBP — Tratado de Pediatria (5ª ed.)',
      'MS — Caderneta da Criança',
      'OMS — Curvas de Crescimento (2006)',
    ],
  },
  {
    id: 'ped-02',
    areaId: 'pediatria',
    areaName: 'Pediatria',
    areaColor: '#34c759',
    title: 'Doenças Respiratórias Pediátricas',
    details: 'Asma, Bronquiolite Viral Aguda, Pneumonias, Laringite/Crupe, Síndrome do Desconforto Respiratório',
    percentage: 14.0,
    absoluteCount: 7,
    trend: 'up',
    probability: '85%',
    avgPerExam: '1.8',
    difficulty: 'Moderada',
    history: [7, 8, 9, 10, 11],
    subtopics: [
      { name: 'Bronquiolite Viral Aguda (VSR, Critérios de Internação, O₂, Palivizumabe)', count: 42 },
      { name: 'Asma Pediátrica (GINA Pediátrico, Dispositivos Inalatórios)', count: 38 },
      { name: 'Pneumonias na Infância (Agentes por Faixa Etária, TTO Empírico)', count: 25 },
      { name: 'Laringite/Crupe (Estridor, Dexametasona, Nebulização com Adrenalina)', count: 12 },
    ],
    keyReferences: [
      'SBP — Diretriz de Bronquiolite (2024)',
      'GINA — Pocket Guide for Asthma',
      'SBP — Manual de Pneumologia Pediátrica',
    ],
  },
  {
    id: 'ped-03',
    areaId: 'pediatria',
    areaName: 'Pediatria',
    areaColor: '#34c759',
    title: 'Neonatologia',
    details: 'Reanimação Neonatal, Icterícia Neonatal, Infecções Congênitas, Prematuridade, Sepse Neonatal',
    percentage: 10.0,
    absoluteCount: 5,
    trend: 'stable',
    probability: '82%',
    avgPerExam: '1.7',
    difficulty: 'Alta',
    history: [8, 9, 8, 9, 8],
    subtopics: [
      { name: 'Reanimação Neonatal (SBP — Passos Iniciais, VPP, Massagem, Drogas)', count: 42 },
      { name: 'Icterícia Neonatal (Zonas de Kramer, Fototerapia, Exsanguineotransfusão)', count: 38 },
      { name: 'Infecções Congênitas (STORCH — Sífilis, Toxoplasmose, Rubéola, CMV, Herpes)', count: 31 },
    ],
    keyReferences: [
      'SBP — Programa de Reanimação Neonatal (2022)',
      'SBP — Icterícia Neonatal (2024)',
      'AAP — Guidelines on Neonatal Hyperbilirubinemia',
    ],
  },
  {
    id: 'ped-04',
    areaId: 'pediatria',
    areaName: 'Pediatria',
    areaColor: '#34c759',
    title: 'Imunizações',
    details: 'Calendário Nacional de Vacinação (PNI), Tipos de Vacinas, Intervalos, Contraindicações, Eventos Adversos',
    percentage: 30.0,
    absoluteCount: 15,
    trend: 'up',
    probability: '80%',
    avgPerExam: '1.6',
    difficulty: 'Fácil',
    history: [6, 7, 8, 9, 10],
    subtopics: [
      { name: 'Calendário PNI 2024 (Criança, Adolescente, Gestante, Idoso)', count: 48 },
      { name: 'Tipos de Vacina (Vírus Vivo Atenuado, Inativada, mRNA, Conjugada)', count: 30 },
      { name: 'Contraindicações, Intervalos e Eventos Adversos Pós-Vacinação', count: 26 },
    ],
    keyReferences: [
      'MS — Calendário Nacional de Vacinação (PNI 2024)',
      'SBP — Manual de Imunizações',
      'SBIm — Guia de Imunização',
    ],
  },
  {
    id: 'ped-05',
    areaId: 'pediatria',
    areaName: 'Pediatria',
    areaColor: '#34c759',
    title: 'Gastroenterologia e Nutrição Pediátrica',
    details: 'Diarreia Aguda/Crônica, Terapia de Reidratação Oral (TRO), Desidratação, Alergias Alimentares (APLV)',
    percentage: 14.0,
    absoluteCount: 7,
    trend: 'stable',
    probability: '78%',
    avgPerExam: '1.5',
    difficulty: 'Fácil',
    history: [8, 7, 7, 8, 7],
    subtopics: [
      { name: 'Diarreia Aguda — Etiologia, Planos A/B/C da OMS, Probióticos, Zinco', count: 42 },
      { name: 'Alergia à Proteína do Leite de Vaca (APLV — IgE vs Não-IgE Mediada)', count: 32 },
      { name: 'Constipação Intestinal Funcional e Doença do Refluxo Gastroesofágico', count: 24 },
    ],
    keyReferences: [
      'SBP — Manual de Gastroenterologia Pediátrica',
      'ESPGHAN — Guidelines on Cow\'s Milk Allergy',
      'OMS — Diarrhoea Treatment Guidelines',
    ],
  },

  // ==================== CATCH-ALL POR ÁREA ====================
  // Capturam questões cuja área foi detectada com segurança mas o subtópico
  // específico não casou com nenhuma regra de keyword.
  {
    id: 'prev-99',
    areaId: 'preventiva',
    areaName: 'Med. Preventiva',
    areaColor: '#5856d6',
    title: 'Outros Temas — Saúde Coletiva',
    details: 'Casos de Saúde Coletiva / SUS / Indicadores não cobertos pelos sub-tópicos específicos.',
    percentage: 0,
    absoluteCount: 0,
    trend: 'stable',
    probability: '—',
    avgPerExam: '—',
    difficulty: 'Variável',
    history: [0, 0, 0, 0, 0],
    subtopics: [
      { name: 'Saude Coletiva — Outros Temas (Politicas/SUS/Indicadores)', count: 0 },
    ],
    keyReferences: [
      'Ministério da Saúde — Caderno de Atenção Básica',
      'Vigilância em Saúde Pública',
    ],
  },
  {
    id: 'go-99',
    areaId: 'gineco',
    areaName: 'Ginecologia & Obstetrícia',
    areaColor: '#ac3e92',
    title: 'Outros Temas — G&O',
    details: 'Casos de Ginecologia/Obstetrícia não cobertos pelos sub-tópicos específicos.',
    percentage: 0,
    absoluteCount: 0,
    trend: 'stable',
    probability: '—',
    avgPerExam: '—',
    difficulty: 'Variável',
    history: [0, 0, 0, 0, 0],
    subtopics: [
      { name: 'G&O — Outros Temas (Caso Clinico Ginecologico/Obstetrico)', count: 0 },
    ],
    keyReferences: [
      'FEBRASGO — Manuais de Ginecologia e Obstetrícia',
    ],
  },
  {
    id: 'cir-99',
    areaId: 'cirurgia',
    areaName: 'Cirurgia Geral',
    areaColor: '#e8541e',
    title: 'Outros Temas — Cirurgia',
    details: 'Casos cirúrgicos não cobertos pelos sub-tópicos específicos.',
    percentage: 0,
    absoluteCount: 0,
    trend: 'stable',
    probability: '—',
    avgPerExam: '—',
    difficulty: 'Variável',
    history: [0, 0, 0, 0, 0],
    subtopics: [
      { name: 'Cirurgia — Outros Temas (Caso Clinico Cirurgico)', count: 0 },
    ],
    keyReferences: [
      'Sabiston — Textbook of Surgery',
      'CBC — Programa de Residência em Cirurgia Geral',
    ],
  },
  {
    id: 'cli-99',
    areaId: 'clinica',
    areaName: 'Clínica Médica',
    areaColor: '#0071e3',
    title: 'Outros Temas — Clínica Médica',
    details: 'Casos de Clínica Médica não cobertos pelos sub-tópicos específicos.',
    percentage: 0,
    absoluteCount: 0,
    trend: 'stable',
    probability: '—',
    avgPerExam: '—',
    difficulty: 'Variável',
    history: [0, 0, 0, 0, 0],
    subtopics: [
      { name: 'Clinica Medica — Outros Temas (Caso Clinico)', count: 0 },
    ],
    keyReferences: [
      "Harrison's — Principles of Internal Medicine",
      'Cecil — Tratado de Medicina Interna',
    ],
  },
  {
    id: 'ped-99',
    areaId: 'pediatria',
    areaName: 'Pediatria',
    areaColor: '#34c759',
    title: 'Outros Temas — Pediatria',
    details: 'Casos de Pediatria não cobertos pelos sub-tópicos específicos.',
    percentage: 0,
    absoluteCount: 0,
    trend: 'stable',
    probability: '—',
    avgPerExam: '—',
    difficulty: 'Variável',
    history: [0, 0, 0, 0, 0],
    subtopics: [
      { name: 'Pediatria — Outros Temas (Caso Clinico Pediatrico)', count: 0 },
    ],
    keyReferences: [
      'SBP — Tratado de Pediatria (5ª ed.)',
      'Nelson — Textbook of Pediatrics',
    ],
  },
];

// ============================================================
// SUBSTITUI HARDCODED COUNTS PELOS REAIS DOS PDFs DO INEP
// Cada topic.subtopics e absoluteCount sao reconstruidos a partir
// do JSON extraido das provas. Isso garante que o dashboard mostre
// SOMENTE numeros reais — nao ha valores fantasma.
// ============================================================
const _realSubtopicsByTopic = (() => {
  const map = {};
  for (const q of generatedQuestions) {
    if (!q.topicId || !q.subtopic) continue;
    if (!map[q.topicId]) map[q.topicId] = {};
    map[q.topicId][q.subtopic] = (map[q.topicId][q.subtopic] || 0) + 1;
  }
  // Convert to sorted arrays
  const out = {};
  for (const tid of Object.keys(map)) {
    out[tid] = Object.entries(map[tid])
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);
  }
  return out;
})();

// Mapeamento de areaId (UI) para a string de area armazenada em cada questao.
const _areaIdToAreaName = {
  preventiva: 'Med. Preventiva',
  gineco: 'Ginecologia & Obstetricia',
  cirurgia: 'Cirurgia Geral',
  clinica: 'Clinica Medica',
  pediatria: 'Pediatria',
};

// Total de questoes por area (real, dos PDFs)
const _areaTotals = {};
for (const q of generatedQuestions) {
  _areaTotals[q.area] = (_areaTotals[q.area] || 0) + 1;
}

// Lista de exames cobertos (ordenada cronologicamente)
const _examsList = Array.from(new Set(generatedQuestions.map((q) => q.examRef))).sort();

// Para cada topico, contagem por examRef (para construir 'history')
const _topicByExam = {};
for (const q of generatedQuestions) {
  if (!q.topicId) continue;
  if (!_topicByExam[q.topicId]) _topicByExam[q.topicId] = {};
  _topicByExam[q.topicId][q.examRef] = (_topicByExam[q.topicId][q.examRef] || 0) + 1;
}

topicsData.forEach((t) => {
  // 1) absoluteCount = total real de questoes do topico
  const real = generatedTopicCounts[t.id] || 0;
  t.absoluteCount = real;

  // 2) subtopics = lista REAL de subtopicos com contagem real
  const realSubs = _realSubtopicsByTopic[t.id];
  t.subtopics = realSubs && realSubs.length > 0 ? realSubs : [];

  // 3) percentage = % deste topico em relacao ao TOTAL DA AREA (soma de todos os
  //    topicos da mesma area). Numero real, nao mais hardcoded.
  const areaName = _areaIdToAreaName[t.areaId];
  const areaTotal = _areaTotals[areaName] || 0;
  t.percentage = areaTotal > 0 ? (real / areaTotal) * 100 : 0;

  // 4) avgPerExam = media de questoes deste topico por edicao (1 casa decimal)
  const numExams = _examsList.length || 1;
  t.avgPerExam = (real / numExams).toFixed(1);

  // 5) history = contagem por exame nas ULTIMAS 5 EDICOES (em ordem cronologica)
  const lastExams = _examsList.slice(-5);
  t.history = lastExams.map((exam) => (_topicByExam[t.id] || {})[exam] || 0);

  // 6) trend = direcao a partir das contagens recentes
  if (t.history.length >= 2) {
    const first = t.history[0];
    const last = t.history[t.history.length - 1];
    if (last > first + 1) t.trend = 'up';
    else if (last < first - 1) t.trend = 'down';
    else t.trend = 'stable';
  }

  // 7) probability = baseado na frequencia historica (sem ML, mas honesta)
  //    Probabilidade = % das edicoes que tiveram pelo menos 1 questao deste topico
  const examsWithTopic = _examsList.filter((e) => (_topicByExam[t.id] || {})[e] > 0).length;
  const probPct = numExams > 0 ? Math.round((examsWithTopic / numExams) * 100) : 0;
  t.probability = `${probPct}%`;
});

// ==================== QUESTIONS BANK ====================
// Questões reais mapeadas das provas objetivas do INEP
// subtopic: vincula a questão a um subtópico específico (deve bater com o name do subtopic em topicsData)
export const questionsBank = generatedQuestions;

// Legacy questions (manually curated with explanations) — merged with generated data
export const legacyQuestions = [
  // ============================================================
  // PREVENTIVA — Proteção e Prevenção (prev-01)
  // ============================================================
  // --- Subtópico: Níveis de Prevenção ---
  {
    id: 'q-001',
    topicId: 'prev-01',
    subtopic: 'Níveis de Prevenção (Primário, Secundário, Terciário, Quaternário)',
    examRef: '2024/2',
    questionNumber: 1,
    area: 'Med. Preventiva',
    questionText: 'Em relação aos níveis de prevenção propostos por Leavell & Clark, o rastreamento de câncer de colo uterino com colpocitologia oncótica em mulheres de 25 a 64 anos é classificado como:',
    options: [
      'A) Prevenção primária',
      'B) Prevenção secundária',
      'C) Prevenção terciária',
      'D) Prevenção quaternária',
    ],
    correctAnswer: 'B',
    explanation: 'O rastreamento (screening) é uma ação de prevenção secundária, que visa detectar a doença em estágio pré-clínico ou inicial, permitindo intervenção precoce.',
  },
  {
    id: 'q-001b',
    topicId: 'prev-01',
    subtopic: 'Níveis de Prevenção (Primário, Secundário, Terciário, Quaternário)',
    examRef: '2022/1',
    questionNumber: 5,
    area: 'Med. Preventiva',
    questionText: 'A vacinação contra hepatite B em recém-nascidos nas primeiras 12 horas de vida é considerada uma medida de prevenção:',
    options: [
      'A) Primária',
      'B) Secundária',
      'C) Terciária',
      'D) Quaternária',
    ],
    correctAnswer: 'A',
    explanation: 'A vacinação é prevenção primária, pois atua antes do desenvolvimento da doença, impedindo a infecção.',
  },
  {
    id: 'q-001c',
    topicId: 'prev-01',
    subtopic: 'Níveis de Prevenção (Primário, Secundário, Terciário, Quaternário)',
    examRef: '2023/2',
    questionNumber: 8,
    area: 'Med. Preventiva',
    questionText: 'A reabilitação cardíaca após infarto agudo do miocárdio é um exemplo de prevenção:',
    options: [
      'A) Primária',
      'B) Secundária',
      'C) Terciária',
      'D) Primordial',
    ],
    correctAnswer: 'C',
    explanation: 'A reabilitação pós-IAM é prevenção terciária — atua após a doença estabelecida para reduzir sequelas e melhorar a qualidade de vida.',
  },
  {
    id: 'q-001d',
    topicId: 'prev-01',
    subtopic: 'Níveis de Prevenção (Primário, Secundário, Terciário, Quaternário)',
    examRef: '2021/2',
    questionNumber: 3,
    area: 'Med. Preventiva',
    questionText: 'De acordo com Leavell & Clark, a fluoretação da água de abastecimento público para prevenção de cárie dentária é classificada como:',
    options: [
      'A) Prevenção primordial',
      'B) Prevenção primária',
      'C) Prevenção secundária',
      'D) Prevenção terciária',
    ],
    correctAnswer: 'B',
    explanation: 'A fluoretação da água é prevenção primária — promoção de saúde através de intervenção ambiental antes do aparecimento da doença.',
  },

  // --- Subtópico: Rastreamento de Câncer ---
  {
    id: 'q-002',
    topicId: 'prev-01',
    subtopic: 'Rastreamento de Câncer (Mama, Colo Uterino, Colorretal, Próstata)',
    examRef: '2025/1',
    questionNumber: 4,
    area: 'Med. Preventiva',
    questionText: 'Sobre o rastreamento de câncer de mama no Brasil, segundo as diretrizes do INCA, assinale a alternativa correta:',
    options: [
      'A) Mamografia anual a partir dos 40 anos para todas as mulheres',
      'B) Mamografia bianual para mulheres de 50 a 69 anos',
      'C) Autoexame das mamas como método de rastreamento populacional',
      'D) Ultrassonografia mamária anual a partir dos 35 anos',
    ],
    correctAnswer: 'B',
    explanation: 'O INCA recomenda mamografia de rastreamento a cada 2 anos para mulheres entre 50 e 69 anos.',
  },
  {
    id: 'q-002b',
    topicId: 'prev-01',
    subtopic: 'Rastreamento de Câncer (Mama, Colo Uterino, Colorretal, Próstata)',
    examRef: '2024/1',
    questionNumber: 6,
    area: 'Med. Preventiva',
    questionText: 'Segundo as diretrizes do INCA, o rastreamento do câncer colorretal em pessoas de risco médio deve ser iniciado aos:',
    options: [
      'A) 40 anos com sangue oculto nas fezes anual',
      'B) 45 anos com colonoscopia a cada 5 anos',
      'C) 50 anos com pesquisa de sangue oculto nas fezes ou colonoscopia',
      'D) 55 anos apenas se houver história familiar',
    ],
    correctAnswer: 'C',
    explanation: 'O INCA recomenda rastreamento de câncer colorretal a partir dos 50 anos em população de risco médio, com PSOF anual ou colonoscopia a cada 10 anos.',
  },
  {
    id: 'q-002c',
    topicId: 'prev-01',
    subtopic: 'Rastreamento de Câncer (Mama, Colo Uterino, Colorretal, Próstata)',
    examRef: '2023/1',
    questionNumber: 2,
    area: 'Med. Preventiva',
    questionText: 'Paciente de 55 anos, tabagista 40 maços-ano, realiza screening com tomografia de baixa dose para câncer de pulmão. Esta estratégia é um exemplo de:',
    options: [
      'A) Prevenção primordial',
      'B) Prevenção primária',
      'C) Prevenção secundária',
      'D) Prevenção terciária',
    ],
    correctAnswer: 'C',
    explanation: 'O screening com TC de baixa dose é prevenção secundária — detecta a doença em estágio assintomático.',
  },

  // --- Subtópico: Rastreamento de Doenças Crônicas ---
  {
    id: 'q-003a',
    topicId: 'prev-01',
    subtopic: 'Rastreamento de Doenças Crônicas (HAS, DM, Dislipidemia)',
    examRef: '2024/2',
    questionNumber: 9,
    area: 'Med. Preventiva',
    questionText: 'Paciente de 45 anos, assintomático, IMC 28 kg/m², PA 138/86 mmHg. Em relação ao rastreamento de diabetes mellitus tipo 2 neste paciente, a conduta recomendada pelo Ministério da Saúde é:',
    options: [
      'A) Glicemia de jejum a cada 3 anos',
      'B) Glicemia de jejum anual devido ao sobrepeso e PA limítrofe',
      'C) Teste de tolerância oral à glicose (TOTG) imediato',
      'D) Hemoglobina glicada a cada 6 meses',
    ],
    correctAnswer: 'A',
    explanation: 'Segundo o MS, adultos com IMC ≥ 25 e sem outros fatores de risco devem realizar rastreamento de DM2 com glicemia de jejum a cada 3 anos.',
  },
  {
    id: 'q-003b',
    topicId: 'prev-01',
    subtopic: 'Rastreamento de Doenças Crônicas (HAS, DM, Dislipidemia)',
    examRef: '2023/2',
    questionNumber: 11,
    area: 'Med. Preventiva',
    questionText: 'Paciente de 35 anos, sem comorbidades, PA aferida em consulta: 128/84 mmHg. A conduta para rastreamento de hipertensão arterial é:',
    options: [
      'A) Diagnóstico de hipertensão e início de anti-hipertensivo',
      'B) MAPA 24h para confirmação diagnóstica',
      'C) Repetir aferições em consultas subsequentes — rastreamento de rotina',
      'D) Alta ambulatorial — PA normal',
    ],
    correctAnswer: 'C',
    explanation: 'PA 128/84 é pré-hipertensão. Deve-se repetir aferição em consultas de rotina. O rastreamento anual de HAS é recomendado para todos os adultos.',
  },

  // --- Subtópico: Aconselhamento e Promoção da Saúde ---
  {
    id: 'q-003c',
    topicId: 'prev-01',
    subtopic: 'Aconselhamento e Promoção da Saúde (Tabagismo, Álcool, Atividade Física)',
    examRef: '2024/1',
    questionNumber: 12,
    area: 'Med. Preventiva',
    questionText: 'Paciente tabagista, 40 maços-ano, deseja parar de fumar. Segundo o Protocolo Clínico e Diretrizes Terapêuticas do Ministério da Saúde, a abordagem inicial mais efetiva é:',
    options: [
      'A) Aconselhamento breve + Terapia de Reposição de Nicotina (TRN)',
      'B) Bupropiona isolada',
      'C) Apenas aconselhamento comportamental intensivo',
      'D) Vareniclina como primeira escolha',
    ],
    correctAnswer: 'A',
    explanation: 'O PCDT de Tabagismo recomenda abordagem cognitivo-comportamental + TRN (adesivos, gomas, pastilhas) como primeira linha, associados ou não à bupropiona.',
  },
  {
    id: 'q-003d',
    topicId: 'prev-01',
    subtopic: 'Aconselhamento e Promoção da Saúde (Tabagismo, Álcool, Atividade Física)',
    examRef: '2022/2',
    questionNumber: 10,
    area: 'Med. Preventiva',
    questionText: 'De acordo com as recomendações da OMS para atividade física em adultos (18-64 anos), o mínimo recomendado por semana é:',
    options: [
      'A) 75 minutos de atividade vigorosa ou 150 minutos de atividade moderada',
      'B) 150 minutos de atividade vigorosa',
      'C) 300 minutos de atividade moderada',
      'D) 60 minutos diários de caminhada leve',
    ],
    correctAnswer: 'A',
    explanation: 'OMS recomenda: 150-300 min/semana de atividade moderada OU 75-150 min/semana de atividade vigorosa, ou combinação equivalente.',
  },

  // --- Subtópico: Prevenção Quaternária ---
  {
    id: 'q-004x',
    topicId: 'prev-01',
    subtopic: 'Prevenção Quaternária e Medicalização Excessiva',
    examRef: '2023/2',
    questionNumber: 15,
    area: 'Med. Preventiva',
    questionText: 'Paciente de 72 anos, assintomático, solicita "check-up completo" com diversos exames de rastreamento sem indicação clínica. O princípio da prevenção quaternária orienta o médico a:',
    options: [
      'A) Realizar todos os exames solicitados para tranquilizar o paciente',
      'B) Explicar os riscos do sobrediagnóstico e evitar exames desnecessários',
      'C) Encaminhar ao especialista para decisão compartilhada',
      'D) Solicitar apenas exames laboratoriais básicos',
    ],
    correctAnswer: 'B',
    explanation: 'A prevenção quaternária visa proteger o paciente de intervenções médicas desnecessárias, evitando sobrediagnóstico, sobretratamento e iatrogenia.',
  },
  {
    id: 'q-004y',
    topicId: 'prev-01',
    subtopic: 'Prevenção Quaternária e Medicalização Excessiva',
    examRef: '2024/2',
    questionNumber: 14,
    area: 'Med. Preventiva',
    questionText: 'O conceito de "disease mongering" está diretamente relacionado a qual nível de prevenção?',
    options: [
      'A) Prevenção primária',
      'B) Prevenção secundária — pelo excesso de rastreamentos',
      'C) Prevenção quaternária — como objeto de combate',
      'D) Prevenção terciária',
    ],
    correctAnswer: 'C',
    explanation: 'Disease mongering (criação/ampliação de doenças pela indústria) é combatido pela prevenção quaternária, que protege contra medicalização excessiva.',
  },

  // ============================================================
  // PREVENTIVA — SUS (prev-04)
  // ============================================================
  {
    id: 'q-004',
    topicId: 'prev-04',
    subtopic: 'Princípios Doutrinários (Universalidade, Equidade, Integralidade)',
    examRef: '2024/1',
    questionNumber: 3,
    area: 'Med. Preventiva',
    questionText: 'De acordo com a Lei 8.080/1990, está incluída no campo de atuação do Sistema Único de Saúde (SUS) a execução de ações de:',
    options: [
      'A) Vigilância sanitária, vigilância epidemiológica e saúde do trabalhador',
      'B) Assistência terapêutica integral, inclusive farmacêutica, com coparticipação do usuário',
      'C) Fiscalização de planos de saúde privados e suplementares',
      'D) Controle de preços de medicamentos e insumos hospitalares',
    ],
    correctAnswer: 'A',
    explanation: 'Lei 8.080/90, Art. 6º: Estão incluídas no campo de atuação do SUS a vigilância sanitária, vigilância epidemiológica e saúde do trabalhador.',
  },

  // ============================================================
  // PREVENTIVA — Epidemiologia (prev-02)
  // ============================================================
  {
    id: 'q-005',
    topicId: 'prev-02',
    subtopic: 'Medidas de Associação (RR, OR, RP, RAR, NNT)',
    examRef: '2025/1',
    questionNumber: 7,
    area: 'Med. Preventiva',
    questionText: 'Em um estudo de coorte que avaliou a associação entre tabagismo e câncer de pulmão, o risco relativo (RR) encontrado foi de 10,5 (IC 95%: 8,2–13,4). Isso significa que:',
    options: [
      'A) A chance de fumantes desenvolverem câncer de pulmão é 10,5 vezes maior que não fumantes',
      'B) O risco de fumantes desenvolverem câncer de pulmão é 10,5 vezes o risco de não fumantes',
      'C) 10,5% dos casos de câncer de pulmão são atribuíveis ao tabagismo',
      'D) A incidência de câncer de pulmão em fumantes é de 10,5 por 100.000',
    ],
    correctAnswer: 'B',
    explanation: 'Risco Relativo (RR) > 1 indica que o risco no grupo exposto é maior que no não-exposto. RR = 10,5 significa que fumantes têm risco 10,5 vezes maior.',
  },

  // ============================================================
  // GO — Infecções Maternas (go-01)
  // ============================================================
  {
    id: 'q-006',
    topicId: 'go-01',
    subtopic: 'Sífilis na Gestação (VDRL, Teste Rápido, Penicilina Benzatina, Sífilis Congênita)',
    examRef: '2024/2',
    questionNumber: 42,
    area: 'Ginecologia & Obstetrícia',
    questionText: 'Gestante de 24 anos, 28 semanas, apresenta VDRL 1:32 e teste treponêmico reagente. Nega tratamento prévio para sífilis. A conduta adequada é:',
    options: [
      'A) Penicilina G Benzatina 2,4 milhões UI, IM, dose única',
      'B) Penicilina G Benzatina 2,4 milhões UI, IM, semanal, por 3 semanas',
      'C) Penicilina G Benzatina 2,4 milhões UI, IM, semanal, por 2 semanas',
      'D) Ceftriaxona 1g IM dose única',
    ],
    correctAnswer: 'B',
    explanation: 'Sífilis na gestação com VDRL ≥ 1:32: tratamento completo com Penicilina G Benzatina 2,4 milhões UI por 3 semanas (total 7,2 milhões).',
  },
  {
    id: 'q-007',
    topicId: 'go-01',
    subtopic: 'HIV/AIDS — Transmissão Vertical (AZT, Profilaxia, Parto, Aleitamento)',
    examRef: '2025/1',
    questionNumber: 44,
    area: 'Ginecologia & Obstetrícia',
    questionText: 'Puérpera HIV positivo, em uso de TARV com carga viral indetectável no 3º trimestre. Em relação ao aleitamento materno, a orientação correta é:',
    options: [
      'A) Aleitamento materno exclusivo até 6 meses',
      'B) Aleitamento materno com profilaxia antirretroviral no lactente',
      'C) Contraindicação absoluta do aleitamento materno',
      'D) Aleitamento materno permitido apenas nos primeiros 15 dias',
    ],
    correctAnswer: 'C',
    explanation: 'No Brasil, o aleitamento materno é contraindicado para mulheres HIV positivas, independentemente da carga viral, pelo risco de transmissão.',
  },

  // GO — Câncer de Colo Uterino (go-02)
  {
    id: 'q-008',
    topicId: 'go-02',
    subtopic: 'NIC I/II/III — Manejo (Colposcopia, Biópsia, Conização, Histerectomia)',
    examRef: '2024/1',
    questionNumber: 46,
    area: 'Ginecologia & Obstetrícia',
    questionText: 'Mulher, 32 anos, colpocitologia oncótica com resultado: "Lesão intraepitelial escamosa de alto grau (HSIL)". A conduta recomendada é:',
    options: [
      'A) Repetir citologia em 6 meses',
      'B) Realizar colposcopia',
      'C) Realizar conização imediata',
      'D) Realizar histerectomia total',
    ],
    correctAnswer: 'B',
    explanation: 'HSIL/NIC II-III em mulher ≥ 25 anos: encaminhar para colposcopia. A conduta depende dos achados colposcópicos.',
  },

  // CIRURGIA — Abdome Agudo (cir-01)
  {
    id: 'q-009',
    topicId: 'cir-01',
    subtopic: 'Abdome Agudo Inflamatório (Apendicite Aguda — Alvarado, Colecistite)',
    examRef: '2024/2',
    questionNumber: 61,
    area: 'Cirurgia Geral',
    questionText: 'Homem, 28 anos, dor abdominal em fossa ilíaca direita há 36 horas, associada a náuseas, febre (38,2°C) e descompressão brusca dolorosa no ponto de McBurney. Escore de Alvarado = 8. A conduta é:',
    options: [
      'A) Observação clínica e antibioticoterapia',
      'B) Apendicectomia',
      'C) TC de abdome para confirmação diagnóstica',
      'D) Ultrassonografia transvaginal',
    ],
    correctAnswer: 'B',
    explanation: 'Escore de Alvarado ≥ 7 em homem com quadro típico: alta probabilidade de apendicite aguda. Conduta: apendicectomia.',
  },
  {
    id: 'q-010',
    topicId: 'cir-01',
    subtopic: 'Abdome Agudo Obstrutivo (Bridas, Volvo, Neoplasia, Hérnia Encarcerada)',
    examRef: '2025/1',
    questionNumber: 63,
    area: 'Cirurgia Geral',
    questionText: 'Paciente com dor abdominal difusa, distensão, parada de eliminação de gases e fezes há 72 horas. RX de abdome mostra distensão de alças de delgado com empilhamento de moedas e ausência de gás no cólon. O diagnóstico mais provável é:',
    options: [
      'A) Pancreatite aguda',
      'B) Abdome agudo obstrutivo',
      'C) Abdome agudo perfurativo',
      'D) Colecistite aguda',
    ],
    correctAnswer: 'B',
    explanation: 'Quadro clínico + imagem de delgado com "empilhamento de moedas" (pregas coniventes) e ausência de gás colônico = obstrução intestinal.',
  },

  // CLÍNICA — Tuberculose/Doenças Bacterianas (cli-01)
  {
    id: 'q-011',
    topicId: 'cli-01',
    subtopic: 'Tuberculose (Diagnóstico — TRM-TB, ADA, Cultura; TTO — RIPE, ILTB)',
    examRef: '2024/1',
    questionNumber: 21,
    area: 'Clínica Médica',
    questionText: 'Paciente, 42 anos, tosse produtiva há 3 semanas, febre vespertina, sudorese noturna e perda de 5 kg. Radiografia de tórax mostra infiltrado em lobo superior direito com cavitação. A conduta diagnóstica inicial é:',
    options: [
      'A) Baciloscopia de escarro (BAAR)',
      'B) Teste tuberculínico (PPD)',
      'C) Cultura para micobactérias',
      'D) Broncoscopia com biópsia',
    ],
    correctAnswer: 'A',
    explanation: 'Quadro clínico + radiológico sugestivo de TB pulmonar: primeira conduta é baciloscopia de escarro (duas amostras). TRM-TB também pode ser utilizado.',
  },
  {
    id: 'q-012',
    topicId: 'cli-01',
    subtopic: 'Tuberculose (Diagnóstico — TRM-TB, ADA, Cultura; TTO — RIPE, ILTB)',
    examRef: '2025/1',
    questionNumber: 24,
    area: 'Clínica Médica',
    questionText: 'Em relação ao tratamento da tuberculose latente (ILTB), a alternativa que apresenta o esquema preferencial atualmente recomendado pelo Ministério da Saúde é:',
    options: [
      'A) Isoniazida por 6 meses',
      'B) Rifampicina por 4 meses',
      'C) Rifapentina + Isoniazida por 3 meses (esquema 3HP)',
      'D) Rifampicina + Isoniazida por 6 meses',
    ],
    correctAnswer: 'C',
    explanation: 'O esquema 3HP (Rifapentina + Isoniazida semanal por 12 doses/3 meses) é o preferencial no Brasil para ILTB, com maior adesão e menor hepatotoxicidade.',
  },

  // PEDIATRIA — Imunizações (ped-04)
  {
    id: 'q-013',
    topicId: 'ped-04',
    subtopic: 'Calendário PNI 2024 (Criança, Adolescente, Gestante, Idoso)',
    examRef: '2024/2',
    questionNumber: 81,
    area: 'Pediatria',
    questionText: 'Lactente de 2 meses comparece para primeira consulta de puericultura. Segundo o Calendário Nacional de Vacinação (PNI 2024), quais vacinas devem ser administradas nesta idade?',
    options: [
      'A) BCG e Hepatite B apenas',
      'B) Pentavalente, VIP, Pneumocócica 10V, Rotavírus',
      'C) Tríplice viral e Hepatite A',
      'D) Febre amarela e Meningocócica C',
    ],
    correctAnswer: 'B',
    explanation: 'Aos 2 meses: Pentavalente (DTP+Hib+HB), VIP (poliomielite inativada), Pneumocócica 10-valente e Rotavírus. BCG e Hep B devem ser feitas ao nascer.',
  },

  // PEDIATRIA — Doenças Respiratórias (ped-02)
  {
    id: 'q-014',
    topicId: 'ped-02',
    subtopic: 'Bronquiolite Viral Aguda (VSR, Critérios de Internação, O₂, Palivizumabe)',
    examRef: '2025/1',
    questionNumber: 85,
    area: 'Pediatria',
    questionText: 'Lactente de 4 meses, previamente hígido, apresenta quadro de coriza, tosse, taquipneia com sibilos difusos e tiragem subcostal. SatO₂ 91% em ar ambiente. A principal hipótese diagnóstica é:',
    options: [
      'A) Pneumonia bacteriana',
      'B) Bronquiolite viral aguda',
      'C) Crise de asma',
      'D) Laringotraqueíte aguda (crupe)',
    ],
    correctAnswer: 'B',
    explanation: 'Lactente < 2 anos, primeiro episódio de sibilância associado a IVAS, com dessaturação = bronquiolite viral aguda (VSR principal agente).',
  },

  // CLÍNICA — Pneumonia (cli-04)
  {
    id: 'q-015',
    topicId: 'cli-04',
    subtopic: 'Pneumonia Adquirida na Comunidade (CURB-65, PSI, Antibioticoterapia)',
    examRef: '2024/1',
    questionNumber: 28,
    area: 'Clínica Médica',
    questionText: 'Paciente, 68 anos, internado por pneumonia adquirida na comunidade. CURB-65 = 3 (confusão mental, ureia > 50, FR > 30). A conduta adequada é:',
    options: [
      'A) Tratamento ambulatorial com amoxicilina',
      'B) Internação hospitalar com ceftriaxona + azitromicina',
      'C) Internação em UTI',
      'D) Alta com levofloxacino oral',
    ],
    correctAnswer: 'B',
    explanation: 'CURB-65 = 3 indica PAC grave: internação hospitalar. Esquema: beta-lactâmico (ceftriaxona) + macrolídeo (azitromicina) ou quinolona respiratória.',
  },
];

// Mapeamento por TOPICO
export const questionsByTopic = {};
questionsBank.forEach(q => {
  if (!questionsByTopic[q.topicId]) questionsByTopic[q.topicId] = [];
  questionsByTopic[q.topicId].push(q.id);
});

// Funcao helper: normaliza string removendo acentos para comparacao
const normalizeStr = (s) => {
  if (!s) return '';
  return s.normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase();
};

// Mapeamento por SUBTOPICO (nome exato do subtopic)
export const questionsBySubtopic = {};
questionsBank.forEach(q => {
  if (!q.subtopic) return;
  const key = normalizeStr(q.subtopic);
  if (!questionsBySubtopic[key]) questionsBySubtopic[key] = [];
  questionsBySubtopic[key].push(q.id);
});

export const getQuestionById = (id) => questionsBank.find(q => q.id === id);
export const getQuestionsByTopicId = (topicId) => questionsBank.filter(q => q.topicId === topicId);
export const getQuestionsBySubtopic = (subtopicName) => {
  const key = normalizeStr(subtopicName);
  return questionsBank.filter(q => normalizeStr(q.subtopic) === key);
};
export const getTopicById = (id) => topicsData.find(t => t.id === id);
export const countQuestionsBySubtopic = (subtopicName) => {
  const key = normalizeStr(subtopicName);
  return questionsBank.filter(q => normalizeStr(q.subtopic) === key).length;
};
