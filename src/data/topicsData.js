// Auto-derived from pipeline v6 data (questoes_db.json + estatisticas_temas.json).
// Periodo: 2011–2025 — 1704 questões extraídas de 17 edições (2022-1 excluída por encoding CID).
// Classificação: 3 níveis — grande_area → tema_principal → subtopico (zero catch-all).

import {
  generatedQuestionsMeta as _meta,
  generatedTopicCounts,
  generatedTotalQuestions,
} from './generatedMeta';

import {
  generatedTopicsData,
  generatedExamsCovered,
} from './generatedTopics';

// ── Exported data ─────────────────────────────────────────────

export const topicsData = generatedTopicsData;

export const examsCovered = generatedExamsCovered;

export const areas = [
  { id: 'todos',     name: 'Todos os Temas',             color: 'bg-gray-700 dark:bg-gray-500', hex: '#636366' },
  { id: 'preventiva',name: 'Med. Preventiva',            color: 'bg-indigo-500', hex: '#5856d6',
    description: 'Medicina Preventiva e Saúde Coletiva — 20 questões por prova' },
  { id: 'gineco',    name: 'Ginecologia & Obstetrícia',  color: 'bg-pink-500',   hex: '#ac3e92',
    description: 'Ginecologia e Obstetrícia — 20 questões por prova' },
  { id: 'cirurgia',  name: 'Cirurgia Geral',             color: 'bg-orange-500', hex: '#e8541e',
    description: 'Cirurgia Geral — 20 questões por prova' },
  { id: 'clinica',   name: 'Clínica Médica',             color: 'bg-blue-500',   hex: '#0071e3',
    description: 'Clínica Médica — 20 questões por prova' },
  { id: 'pediatria', name: 'Pediatria',                  color: 'bg-green-500',  hex: '#34c759',
    description: 'Pediatria — 20 questões por prova' },
];

export const statsSummary = [
  {
    label: 'Edições Analisadas',
    value: String(examsCovered.length),
    sub: `${examsCovered[0]} – ${examsCovered[examsCovered.length - 1]}`,
  },
  {
    label: 'Questões Classificadas',
    value: String(generatedTotalQuestions),
    sub: '100% das provas legíveis',
  },
  {
    label: 'Grandes Áreas',
    value: '5',
    sub: 'Matriz de Correspondência Curricular',
  },
  {
    label: 'Especialidades Mapeadas',
    value: String(Object.keys(generatedTopicCounts).length),
    sub: 'Temas com incidência real nas provas',
  },
];

// ── Helper functions ──────────────────────────────────────────

const normalizeStr = (s) => {
  if (!s) return '';
  return s.normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase();
};

export const getTopicById = (id) => topicsData.find((t) => t.id === id);

// questionsByTopic: topicId → array of question IDs (from slim meta)
export const questionsByTopic = {};
_meta.forEach((q) => {
  if (!questionsByTopic[q.topicId]) questionsByTopic[q.topicId] = [];
  questionsByTopic[q.topicId].push(q.id);
});

// countQuestionsBySubtopic: used by Dashboard subtopic drill-down
export const countQuestionsBySubtopic = (subtopicName) => {
  const key = normalizeStr(subtopicName);
  return _meta.filter((q) => normalizeStr(q.subtopic) === key).length;
};
