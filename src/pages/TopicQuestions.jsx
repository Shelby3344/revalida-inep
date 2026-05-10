import React, { useState, useMemo } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft, FileText, CheckCircle2, Search, ExternalLink, ChevronDown,
  HelpCircle, BookOpen, X, Filter, Layers,
} from 'lucide-react';
import { getTopicById, examsCovered } from '../data/topicsData';
// Importa o BANCO COMPLETO de questoes (com texto + opcoes) somente aqui.
// Como TopicQuestions e lazy-loaded, este import grande fica em um chunk separado
// e nao pesa no carregamento inicial do Dashboard.
import { generatedQuestions as fullQuestions } from '../data/generatedData';

// Normalizacao para casar nomes de subtopicos com/sem acento.
const normalizeStr = (s) => {
  if (!s) return '';
  return s.normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase();
};

const getQuestionsByTopicId = (topicId) =>
  fullQuestions.filter((q) => q.topicId === topicId);

const getQuestionsBySubtopic = (subtopicName) => {
  const key = normalizeStr(subtopicName);
  return fullQuestions.filter((q) => normalizeStr(q.subtopic) === key);
};

export default function TopicQuestions() {
  const { topicId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const topic = getTopicById(topicId);
  const subtopicFilter = searchParams.get('subtopic') || null;

  // Questões: filtradas por subtópico se houver param, senão todas do tema
  const baseQuestions = subtopicFilter
    ? getQuestionsBySubtopic(subtopicFilter)
    : getQuestionsByTopicId(topicId);

  const [revealedAnswers, setRevealedAnswers] = useState({});
  const [searchTerm, setSearchTerm] = useState('');

  const filteredQuestions = useMemo(() => {
    if (!searchTerm.trim()) return baseQuestions;
    const q = searchTerm.toLowerCase();
    return baseQuestions.filter((qn) =>
      qn.questionText.toLowerCase().includes(q) ||
      qn.options.some((o) => o.toLowerCase().includes(q)) ||
      qn.examRef.toLowerCase().includes(q) ||
      (qn.explanation && qn.explanation.toLowerCase().includes(q))
    );
  }, [baseQuestions, searchTerm]);

  // Evolução por edição — calculada a partir das questões filtradas (subtópico ou tema)
  const evolutionData = useMemo(() => {
    const last5 = examsCovered.slice(-5);
    const counts = {};
    baseQuestions.forEach((q) => { counts[q.examRef] = (counts[q.examRef] || 0) + 1; });
    return last5.map((e) => ({ label: e, count: counts[e] || 0 }));
  }, [baseQuestions]);

  const toggleAnswer = (id) => {
    setRevealedAnswers((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const clearSubtopicFilter = () => {
    setSearchParams({});
  };

  if (!topic) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-20 text-center">
        <HelpCircle size={48} className="mx-auto mb-4 text-gray-300" />
        <h2 className="text-xl font-bold mb-2">Tema não encontrado</h2>
        <button onClick={() => navigate('/')} className="text-[#0071e3] hover:underline text-sm font-medium">
          Voltar ao Dashboard
        </button>
      </div>
    );
  }

  return (
    <main className="max-w-5xl mx-auto px-4 md:px-6 py-8">
      {/* BACK BUTTON */}
      <button
        onClick={() => navigate('/')}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-6 transition-colors"
      >
        <ArrowLeft size={16} />
        Voltar ao Dashboard
      </button>

      {/* HEADER CARD */}
      <div className="card p-5 md:p-8 mb-8">
        <div className="flex items-start gap-4 flex-wrap">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="badge bg-blue-500 text-white">{topic.areaName}</span>
              {subtopicFilter && (
                <span className="badge bg-purple-50 dark:bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-500/20">
                  <Layers size={10} className="mr-1" />
                  Subtópico
                </span>
              )}
            </div>

            <h1 className="text-xl md:text-2xl font-bold tracking-tight mb-2">
              {subtopicFilter ? subtopicFilter : topic.title}
            </h1>

            {subtopicFilter ? (
              <div className="flex items-center gap-2 flex-wrap">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Questões classificadas dentro do tema <strong>{topic.title}</strong>
                </p>
                <button
                  onClick={clearSubtopicFilter}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-gray-100 dark:bg-[#2c2c2e] text-xs font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-[#3a3a3c] transition-colors"
                >
                  <X size={12} />
                  Mostrar todos os subtópicos
                </button>
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">{topic.details}</p>
            )}
          </div>

          <div className="flex gap-3 text-center">
            <div className="bg-gray-50 dark:bg-[#2c2c2e] rounded-2xl p-4 min-w-[80px]">
              <span className="block text-2xl font-bold tracking-tight">{baseQuestions.length}</span>
              <span className="text-[10px] text-gray-500 dark:text-gray-400 font-semibold uppercase">Questões</span>
            </div>
            <div className="bg-gray-50 dark:bg-[#2c2c2e] rounded-2xl p-4 min-w-[80px]">
              <span className="block text-2xl font-bold tracking-tight">{topic.percentage.toFixed(1)}%</span>
              <span className="text-[10px] text-gray-500 dark:text-gray-400 font-semibold uppercase">Incidência</span>
            </div>
          </div>
        </div>

        {/* Evolução nas últimas 5 edições */}
        <div className="mt-5 bg-gray-50 dark:bg-[#2c2c2e] rounded-2xl p-4">
          <span className="block text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
            Evolução nas Últimas 5 Edições
            {subtopicFilter && <span className="ml-1.5 font-normal normal-case text-gray-400">— {subtopicFilter}</span>}
          </span>
          <div className="flex items-end gap-2 h-16">
            {evolutionData.map(({ label, count }, k) => {
              const maxVal = Math.max(...evolutionData.map((d) => d.count), 1);
              const heightPct = maxVal > 0 ? (count / maxVal) * 100 : 0;
              const areaColor = topic?.areaColor || '#0071e3';
              return (
                <div key={k} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                  <span className="text-[11px] font-bold text-gray-600 dark:text-gray-300">{count || '—'}</span>
                  <div
                    className="w-full rounded-t-sm transition-all duration-500"
                    style={{
                      height: count > 0 ? `${heightPct}%` : '3px',
                      background: count > 0 ? areaColor : '#d1d5db',
                      opacity: count > 0 ? 0.4 + k * 0.15 : 0.3,
                      minHeight: '3px',
                    }}
                  />
                  <span className="text-[9px] text-gray-400 dark:text-gray-500 mt-0.5 text-center leading-tight">{label}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Search */}
        <div className="mt-4 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-gray-400" />
          <input
            type="text"
            placeholder="Filtrar questões por palavra-chave, exame ou conteúdo..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#1c1c1e] text-sm focus:outline-none focus:ring-2 focus:ring-[#0071e3]/20 focus:border-[#0071e3] transition"
          />
        </div>
      </div>

      {/* QUESTIONS LIST */}
      {filteredQuestions.length === 0 ? (
        <div className="card p-12 text-center">
          <FileText size={32} className="mx-auto mb-3 text-gray-300" />
          <p className="text-gray-500 font-medium">
            {baseQuestions.length === 0
              ? subtopicFilter
                ? 'Este subtópico ainda não possui questões classificadas.'
                : 'Nenhuma questão classificada para este tema ainda.'
              : 'Nenhuma questão corresponde ao filtro.'}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {baseQuestions.length === 0
              ? 'As questões estão sendo extraídas e classificadas das provas do INEP.'
              : 'Tente outro termo de busca.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-500 dark:text-gray-400 font-medium">
              Mostrando {filteredQuestions.length} de {baseQuestions.length} questões
              {subtopicFilter && (
                <span className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-50 dark:bg-purple-500/10 text-purple-600 dark:text-purple-400 text-[10px] font-semibold border border-purple-200 dark:border-purple-500/20">
                  <Filter size={10} />
                  Subtópico: {subtopicFilter.length > 50 ? subtopicFilter.substring(0, 50) + '...' : subtopicFilter}
                </span>
              )}
            </p>
          </div>

          {filteredQuestions.map((q, idx) => {
            const isRevealed = revealedAnswers[q.id];
            return (
              <div key={q.id} className="card overflow-hidden transition-all">
                <div className="p-4 md:p-6">
                  {/* Badges */}
                  <div className="flex items-center gap-2 mb-3 flex-wrap">
                    <span className="badge bg-gray-100 dark:bg-[#2c2c2e] text-gray-500 text-[10px]">#{idx + 1}</span>
                    <span className="badge bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/20 text-[10px]">
                      Revalida {q.examRef}
                    </span>
                    <span className="badge bg-gray-50 dark:bg-[#3a3a3c] text-gray-500 text-[10px]">Q{q.questionNumber}</span>
                    {topic && <span className="text-[10px] text-gray-500 dark:text-gray-400 font-medium">{topic.areaName}</span>}
                    {q.subtopic && (
                      <span className="text-[10px] text-purple-500 dark:text-purple-400 font-medium truncate max-w-[200px]">
                        {q.subtopic}
                      </span>
                    )}
                  </div>

                  {/* Question text */}
                  <p className="text-sm md:text-base font-medium leading-relaxed mb-4">{q.questionText}</p>

                  {/* Options */}
                  <div className="space-y-2">
                    {q.options.map((opt, oi) => {
                      const letter = opt.charAt(0);
                      const isCorrect = letter === q.correctAnswer;
                      return (
                        <div
                          key={oi}
                          className={`p-3 rounded-xl border text-sm transition-all ${
                            isRevealed && isCorrect
                              ? 'bg-green-50 dark:bg-green-500/10 border-green-300 dark:border-green-500/30 text-green-800 dark:text-green-300 font-semibold'
                              : isRevealed && !isCorrect
                                ? 'bg-gray-50 dark:bg-[#2c2c2e] border-gray-100 dark:border-gray-700/50 opacity-60'
                                : 'bg-gray-50 dark:bg-[#2c2c2e] border-gray-100 dark:border-gray-700/50 hover:border-gray-300 dark:hover:border-gray-600'
                          }`}
                        >
                          <span className="font-bold mr-2">{letter}</span>
                          {opt.substring(3)}
                          {isRevealed && isCorrect && <CheckCircle2 size={16} className="inline ml-2 text-green-600" />}
                        </div>
                      );
                    })}
                  </div>

                  {/* Reveal button */}
                  <button
                    onClick={() => toggleAnswer(q.id)}
                    className={`mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-semibold transition-all ${
                      isRevealed
                        ? 'bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-500/20'
                        : 'bg-gray-100 dark:bg-[#2c2c2e] text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-[#3a3a3c]'
                    }`}
                  >
                    <BookOpen size={14} />
                    {isRevealed ? 'Resposta Revelada' : 'Revelar Gabarito'}
                    <ChevronDown size={14} className={`transition-transform ${isRevealed ? 'rotate-180' : ''}`} />
                  </button>

                  {/* Explanation */}
                  {isRevealed && q.explanation && (
                    <div className="mt-4 p-4 rounded-2xl bg-blue-50/50 dark:bg-blue-500/5 border border-blue-100 dark:border-blue-500/10">
                      <div className="flex items-start gap-2">
                        <HelpCircle size={14} className="text-blue-500 mt-0.5 flex-shrink-0" />
                        <p className="text-xs md:text-sm text-blue-800 dark:text-blue-300 leading-relaxed">{q.explanation}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Reference link */}
      <div className="mt-8 text-center">
        <a
          href="https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/revalida/provas-e-gabaritos"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
        >
          <ExternalLink size={12} />
          Baixar provas e gabaritos originais no site do INEP
        </a>
      </div>
    </main>
  );
}
