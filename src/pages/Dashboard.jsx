import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { TrendingUp, Minus, TrendingDown, ChevronDown, FileText, Target, BarChart2, ExternalLink, Info, Eye } from 'lucide-react';
import { topicsData, statsSummary, areas, questionsByTopic, countQuestionsBySubtopic, examsCovered } from '../data/topicsData';

const areaColors = {
  preventiva: { bg: 'bg-indigo-500', hex: '#5856d6', name: 'Medicina Preventiva e Saúde Coletiva' },
  gineco:     { bg: 'bg-pink-500',   hex: '#ac3e92', name: 'Ginecologia e Obstetrícia' },
  cirurgia:   { bg: 'bg-orange-500', hex: '#e8541e', name: 'Cirurgia Geral' },
  clinica:    { bg: 'bg-blue-500',   hex: '#0071e3', name: 'Clínica Médica' },
  pediatria:  { bg: 'bg-green-500',  hex: '#34c759', name: 'Pediatria' },
};


export default function Dashboard() {
  const [activeFilter, setActiveFilter] = useState('todos');
  const [expandedId, setExpandedId] = useState(null);
  const [animated, setAnimated] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 200);
    return () => clearTimeout(t);
  }, []);

  // Reset expanded when filter changes
  const handleFilterChange = (areaId) => {
    setActiveFilter(areaId);
    setExpandedId(null);
  };

  const filteredTopics = useMemo(() => {
    if (activeFilter === 'todos') return topicsData;
    return topicsData.filter((t) => t.areaId === activeFilter);
  }, [activeFilter]);

  const maxPct = useMemo(() => Math.max(...filteredTopics.map((t) => t.percentage), 1), [filteredTopics]);

  return (
    <main className="max-w-5xl mx-auto px-3 md:px-6 pb-20">
      {/* HERO */}
      <section className="pt-12 md:pt-20 pb-8 md:pb-12 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 rounded-full bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 text-xs font-semibold uppercase tracking-widest border border-blue-200 dark:border-blue-500/20">
          <BarChart2 size={14} />
          Análise das Provas Objetivas · INEP
        </div>
        <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-4" style={{ letterSpacing: '-0.02em' }}>
          O que mais cai no Revalida
        </h1>
        <p className="text-base md:text-lg text-gray-500 dark:text-gray-400 max-w-2xl mx-auto leading-relaxed">
          Mapeamento das provas teóricas (1ª fase) do INEP de{' '}
          <strong className="text-gray-900 dark:text-white">{examsCovered[0]} a {examsCovered[examsCovered.length - 1]}</strong>{' '}
          ({examsCovered.length} edições legíveis).
          <br />
          <span className="text-sm">
            Os percentuais abaixo mostram quanto cada tema representa dentro da sua área —{' '}
            calculado a partir das questões reais extraídas dos PDFs do INEP.
          </span>
        </p>
      </section>

      {/* STATS CARDS */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-10">
        {statsSummary.map((stat, i) => (
          <div key={i} className="card p-5 md:p-6 hover:shadow-[0_8px_30px_rgba(0,0,0,0.08)] dark:hover:shadow-[0_8px_30px_rgba(0,0,0,0.4)] transition-shadow">
            <h3 className="text-3xl md:text-4xl font-bold text-[#0071e3] tracking-tight mb-1">{stat.value}</h3>
            <p className="text-xs md:text-sm font-semibold mb-0.5">{stat.label}</p>
            <p className="text-[10px] md:text-xs text-gray-500 dark:text-gray-400">{stat.sub}</p>
          </div>
        ))}
      </section>

      {/* FILTERS */}
      <div className="mb-6 space-y-3">
        <div>
          <h2 className="text-xl md:text-2xl font-bold tracking-tight flex items-center gap-2">
            <Target size={20} className="text-[#0071e3]" />
            {filteredTopics.length} Temas Mapeados
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Clique na seta <ChevronDown size={12} className="inline" /> de cada tema para ver os detalhes e subtópicos
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {areas.map((area) => (
            <button
              key={area.id}
              onClick={() => handleFilterChange(area.id)}
              className={`whitespace-nowrap flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-semibold transition-all duration-200
                ${activeFilter === area.id
                  ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 shadow-md scale-105'
                  : 'bg-white dark:bg-[#1c1c1e] text-gray-700 dark:text-gray-400 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-[#2c2c2e]'
                }`}
            >
              <span className={`w-2 h-2 rounded-full ${area.color} ${activeFilter === area.id ? 'opacity-100' : 'opacity-60'}`} />
              {area.name}
            </button>
          ))}
        </div>
      </div>

      {/* UNIFIED TOPIC LIST — cada tema expande INLINE */}
      <div className="card overflow-hidden">
        <div className="divide-y divide-gray-200 dark:divide-white/10">
          {filteredTopics.map((topic, i) => {
            const isExpanded = expandedId === topic.id;
            const ac = areaColors[topic.areaId] || areaColors.clinica;
            const qCount = questionsByTopic[topic.id]?.length || 0;
            const trendIcon =
              topic.trend === 'up' ? <TrendingUp size={12} /> : topic.trend === 'down' ? <TrendingDown size={12} /> : <Minus size={12} />;
            const trendLabel = topic.trend === 'up' ? 'Tendência de alta' : topic.trend === 'down' ? 'Tendência de queda' : 'Estável';
            const trendStyle =
              topic.trend === 'up'
                ? 'text-green-600 bg-green-50 dark:bg-green-500/10 border-green-200 dark:border-green-500/20'
                : topic.trend === 'down'
                  ? 'text-red-600 bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/20'
                  : 'text-gray-500 bg-gray-50 dark:bg-gray-500/10 border-gray-200 dark:border-gray-500/20';

            return (
              <div key={topic.id} id={`topic-${topic.id}`} className="scroll-mt-20">
                {/* ---------- LINHA PRINCIPAL (sempre visível) ---------- */}
                <button
                  onClick={() => setExpandedId(isExpanded ? null : topic.id)}
                  className={`w-full flex items-center gap-3 md:gap-4 p-3 md:p-4 text-left transition-colors
                    ${isExpanded ? 'bg-blue-50/50 dark:bg-blue-500/5' : 'hover:bg-gray-50 dark:hover:bg-[#2c2c2e]/50'}`}
                >
                  {/* Ranking */}
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0 transition-colors
                      ${isExpanded ? 'bg-[#0071e3] text-white' : 'bg-gray-100 dark:bg-[#2c2c2e] text-gray-500 dark:text-gray-400'}`}
                  >
                    {i + 1}
                  </div>

                  {/* Nome do tema + badges */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider text-white ${ac.bg}`}>
                        {topic.areaName}
                      </span>
                      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-semibold border ${trendStyle}`}>
                        {trendIcon}
                        {trendLabel}
                      </span>
                      {qCount > 0 && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/20">
                          <FileText size={10} className="mr-1" />
                          {qCount} questões
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm md:text-base font-bold leading-snug">{topic.title}</h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{topic.details}</p>
                  </div>

                  {/* Barra + % */}
                  <div className="hidden sm:flex items-center gap-3 flex-shrink-0">
                    <div className="w-28 md:w-40 h-7 bg-gray-100 dark:bg-[#3a3a3c] rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-1000 ease-out"
                        style={{
                          width: animated ? `${(topic.percentage / maxPct) * 100}%` : '0%',
                          background: `linear-gradient(90deg, ${ac.hex}99, ${ac.hex})`,
                        }}
                      />
                    </div>
                    <span className="text-lg md:text-xl font-bold w-14 text-right" style={{ color: ac.hex }}>
                      {topic.percentage.toFixed(1)}%
                    </span>
                  </div>

                  {/* % mobile */}
                  <span className="sm:hidden text-base font-bold flex-shrink-0 w-10 text-right" style={{ color: ac.hex }}>
                    {topic.percentage.toFixed(0)}%
                  </span>

                  <ChevronDown
                    size={20}
                    className={`text-gray-400 flex-shrink-0 transition-transform duration-300 ${isExpanded ? 'rotate-180 text-[#0071e3]' : ''}`}
                  />
                </button>

                {/* ---------- CONTEÚDO EXPANDIDO (abre INLINE aqui mesmo) ---------- */}
                <div
                  className={`transition-all duration-400 ease-in-out overflow-hidden
                    ${isExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'}`}
                >
                  <div className="px-4 md:px-6 py-5 border-t border-black/5 dark:border-white/10 bg-gray-50/30 dark:bg-[#1c1c1e]/50">
                    {/* Badge info + explicação do percentual */}
                    <div className="flex items-start gap-2 mb-5 p-3 rounded-2xl bg-blue-50/70 dark:bg-blue-500/5 border border-blue-100 dark:border-blue-500/10">
                      <Info size={14} className="text-blue-500 flex-shrink-0 mt-0.5" />
                      <div className="text-xs text-blue-700 dark:text-blue-300 leading-relaxed">
                        <strong>{topic.percentage.toFixed(1)}% da área de {ac.name}</strong> — isso equivale a aproximadamente{' '}
                        <strong>{topic.avgPerExam} questões por prova</strong> (média histórica).{' '}
                        Probabilidade estimada de cair na próxima edição: <strong>{topic.probability}</strong>.
                        Total de <strong>{topic.absoluteCount} questões</strong> em {examsCovered.length} edições analisadas ({examsCovered[0]}–{examsCovered[examsCovered.length - 1]}).
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* COLUNA ESQUERDA: Subtópicos clicáveis */}
                      <div>
                        <h4 className="text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                          Desdobramento do Tema (Subtópicos)
                        </h4>
                        <p className="text-[10px] text-gray-500 dark:text-gray-400 mb-3">Clique em qualquer subtópico para ver as questões específicas</p>
                        <div className="space-y-2">
                          {topic.subtopics.map((sub, j) => {
                            const subQCount = countQuestionsBySubtopic(sub.name) || sub.count;
                            return (
                              <button
                                key={j}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigate(`/topic/${topic.id}?subtopic=${encodeURIComponent(sub.name)}`);
                                }}
                                className="w-full text-left p-3 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#1c1c1e] hover:border-blue-300 dark:hover:border-blue-500/40 hover:shadow-sm hover:bg-blue-50/30 dark:hover:bg-blue-500/5 transition-all group"
                              >
                                <div className="flex justify-between items-start text-xs mb-2">
                                  <span className="font-medium text-gray-800 dark:text-gray-200 leading-snug group-hover:text-[#0071e3] transition-colors">
                                    {sub.name}
                                  </span>
                                  <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
                                    {sub.probability != null && (
                                      <span className="inline-flex items-center font-bold px-2 py-0.5 rounded-full text-[10px]"
                                        style={{
                                          background: sub.probability >= 70 ? '#dcfce7' : sub.probability >= 40 ? '#fef9c3' : '#fee2e2',
                                          color:      sub.probability >= 70 ? '#15803d' : sub.probability >= 40 ? '#a16207' : '#b91c1c',
                                        }}>
                                        {sub.probability}%
                                      </span>
                                    )}
                                    <span className="inline-flex items-center gap-1 font-bold text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-[#2c2c2e] px-2 py-0.5 rounded-full text-[10px]">
                                      <Eye size={10} />
                                      {subQCount} <span className="font-normal text-gray-500 dark:text-gray-400">questões</span>
                                    </span>
                                  </div>
                                </div>
                                <div className="w-full h-2 bg-gray-200 dark:bg-[#3a3a3c] rounded-full overflow-hidden">
                                  <div
                                    className="h-full rounded-full transition-all duration-700 ease-out"
                                    style={{
                                      width: isExpanded ? `${(sub.count / topic.absoluteCount) * 100}%` : '0%',
                                      background: ac.hex,
                                      opacity: 0.7 + j * 0.08,
                                    }}
                                  />
                                </div>
                                <div className="flex justify-end mt-1.5">
                                  <span className="text-[10px] text-blue-500 font-medium opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                                    Ver questões <ExternalLink size={10} />
                                  </span>
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      {/* COLUNA DIREITA: Métricas + Ações */}
                      <div className="flex flex-col">
                        <h4 className="text-[11px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
                          Métricas e Evolução
                        </h4>

                        {/* Mini cards */}
                        <div className="mb-4">
                          <div className="bg-white dark:bg-[#1c1c1e] rounded-2xl p-3 border border-black/5 dark:border-white/10">
                            <span className="block text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase tracking-wider mb-1">Probabilidade</span>
                            <span className="text-xl font-bold tracking-tight">{topic.probability}</span>
                            <span className="block text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">de aparecer na prova</span>
                          </div>
                        </div>

                        {/* Histórico visual */}
                        <div className="bg-white dark:bg-[#1c1c1e] rounded-2xl p-4 border border-black/5 dark:border-white/10 mb-4">
                          <span className="block text-[10px] text-gray-500 dark:text-gray-400 font-bold uppercase tracking-wider mb-3">
                            Evolução nas Últimas 5 Edições
                          </span>
                          <div className="flex items-end gap-1.5 h-14">
                            {topic.history.map((val, k) => {
                              const maxH = Math.max(...topic.history, 1);
                              // Labels reais — ultimas 5 edicoes legiveis nos PDFs
                              const labels = examsCovered.slice(-5);
                              return (
                                <div key={k} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                                  <span className="text-[10px] font-bold text-gray-500">{val}</span>
                                  <div
                                    className="w-full rounded-t-sm transition-all duration-700 ease-out"
                                    style={{
                                      height: isExpanded ? `${(val / maxH) * 100}%` : '0%',
                                      background: ac.hex,
                                      opacity: 0.35 + k * 0.16,
                                    }}
                                  />
                                  <span className="text-[9px] text-gray-500 dark:text-gray-400 mt-1">{labels[k]}</span>
                                </div>
                              );
                            })}
                          </div>
                        </div>

                        {/* Botões de ação */}
                        <div className="flex gap-2 mt-auto">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/topic/${topic.id}`);
                            }}
                            className="flex-1 inline-flex items-center justify-center gap-1.5 px-4 py-2.5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-full text-xs font-semibold hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors"
                          >
                            <FileText size={14} />
                            Ver Todas as Questões ({qCount})
                          </button>
                          <a
                            href="https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/revalida/provas-e-gabaritos"
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 bg-gray-100 dark:bg-[#2c2c2e] rounded-full text-xs font-semibold hover:bg-gray-200 dark:hover:bg-[#3a3a3c] transition-colors"
                          >
                            <ExternalLink size={12} />
                            PDF Original no INEP
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
}
