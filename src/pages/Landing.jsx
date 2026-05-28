import React from 'react';
import { ArrowRight, BookOpen, Clock, Calendar } from 'lucide-react';

export default function Landing({ onEnter }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 text-center select-none">

      {/* Badge */}
      <div className="mb-8 inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#008080]/30 bg-[#008080]/5 text-[#008080] text-xs font-semibold tracking-wide uppercase">
        <span className="w-1.5 h-1.5 rounded-full bg-[#008080] animate-pulse" />
        Provas Oficiais INEP
      </div>

      {/* Heading */}
      <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-5 leading-[1.05]">
        Simulados<br />
        <span
          className="text-transparent"
          style={{ backgroundImage: 'linear-gradient(180deg,#008080 0%,#004d4d 100%)', WebkitBackgroundClip: 'text', backgroundClip: 'text' }}
        >
          Revalida INEP
        </span>
      </h1>

      {/* Subtitle */}
      <p className="text-gray-500 dark:text-gray-400 max-w-sm text-lg mb-10 leading-relaxed">
        Resolva as provas objetivas na íntegra, com interface de prova real e gabarito oficial.
      </p>

      {/* Stats */}
      <div className="flex items-center gap-6 mb-12 flex-wrap justify-center">
        {[
          { icon: BookOpen, label: '22 cadernos', sub: '2011 – 2025' },
          { icon: Calendar, label: '14 edições', sub: 'anos letivos' },
          { icon: Clock,     label: '2.106 questões', sub: '100% oficiais' },
        ].map(({ icon: Icon, label, sub }) => (
          <div key={label} className="flex flex-col items-center gap-1">
            <div className="w-10 h-10 rounded-xl bg-gray-100 dark:bg-[#1c1c1e] flex items-center justify-center text-[#008080]">
              <Icon size={18} />
            </div>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">{label}</span>
            <span className="text-xs text-gray-400">{sub}</span>
          </div>
        ))}
      </div>

      {/* CTA */}
      <button
        onClick={onEnter}
        className="group flex items-center gap-2.5 bg-[#008080] hover:bg-[#006b6b] text-white font-semibold px-9 py-4 rounded-full transition-all duration-200 text-base shadow-lg shadow-[#008080]/20 hover:shadow-[#008080]/40 hover:scale-105 active:scale-95"
      >
        Acessar Material
        <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform duration-200" />
      </button>

      {/* Sources note */}
      <p className="mt-16 text-[11px] text-gray-400 dark:text-gray-600 max-w-xs">
        Fontes: INEP · Estratégia MED · Medway · Medcel · Recurso Oficial
      </p>
    </div>
  );
}
