import React, { useState, useEffect, lazy, Suspense } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Sun, Moon, Activity } from 'lucide-react';
import Dashboard from './pages/Dashboard';
// TopicQuestions e a tela mais pesada (mostra todas as questoes de um topico).
// Carrega so quando o usuario navega para /topic/* — economiza ~500KB no bundle inicial.
const TopicQuestions = lazy(() => import('./pages/TopicQuestions'));

const PageFallback = () => (
  <div className="max-w-5xl mx-auto px-3 md:px-6 py-20 text-center text-gray-400">
    Carregando...
  </div>
);

export default function App() {
  // Inicializa o estado a partir do que ja foi aplicado pelo script anti-flash
  // do index.html. Mesma logica de prioridade aqui para garantir que o estado
  // bate com o que ja esta no DOM (evita desync se o anti-flash falhou).
  const [dark, setDark] = useState(() => {
    if (typeof document === 'undefined') return true;
    try {
      const saved = localStorage.getItem('revalida-theme');
      if (saved === 'light') return false;
      if (saved === 'dark') return true;
      if (window.matchMedia) {
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
      }
    } catch { /* ignore */ }
    return document.documentElement.classList.contains('dark');
  });

  useEffect(() => {
    // Sincroniza classe DOM e suprime transitions durante a troca para evitar lag.
    const root = document.documentElement;
    root.classList.add('theme-switching');
    if (dark) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    try { localStorage.setItem('revalida-theme', dark ? 'dark' : 'light'); } catch { /* ignore */ }
    // Re-habilita transitions apos 1 frame (16ms). Garante que a mudanca de
    // bg/cor seja INSTANTANEA, sem 200+ elementos animando ao mesmo tempo.
    const id = window.requestAnimationFrame(() => {
      root.classList.remove('theme-switching');
    });
    return () => window.cancelAnimationFrame(id);
  }, [dark]);

  const navigate = useNavigate();
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <div className="min-h-screen bg-[#f5f5f7] dark:bg-black text-gray-900 dark:text-[#f5f5f7] font-sans">
      {/* HEADER */}
      <header className="sticky top-0 z-50 glass border-b border-black/5 dark:border-white/10">
        <div className="max-w-7xl mx-auto px-4 md:px-6 h-16 flex items-center justify-between">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 font-bold text-lg tracking-tight hover:opacity-80 transition-opacity"
          >
            <span className="w-8 h-8 rounded-lg bg-[#0071e3] flex items-center justify-center text-white text-sm font-extrabold">R</span>
            <span className="hidden sm:inline">Revalida<span className="text-[#0071e3]">INEP</span></span>
          </button>

          <div className="flex items-center gap-3">
            {!isHome && (
              <button
                onClick={() => navigate('/')}
                className="text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                ← Dashboard
              </button>
            )}
            <button
              onClick={() => setDark(!dark)}
              className="w-9 h-9 rounded-full flex items-center justify-center bg-gray-100 dark:bg-[#2c2c2e] hover:bg-gray-200 dark:hover:bg-[#3a3a3c] transition-colors"
              aria-label="Alternar tema"
            >
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
          </div>
        </div>
      </header>

      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/topic/:topicId" element={<TopicQuestions />} />
        </Routes>
      </Suspense>

      {/* FOOTER */}
      <footer className="border-t border-black/5 dark:border-white/10 py-8 mt-20">
        <div className="max-w-7xl mx-auto px-6 text-center text-xs text-gray-400 dark:text-gray-600 space-y-1">
          <p>Dados compilados das provas objetivas do Revalida INEP · 2011–2025</p>
          <p className="flex items-center justify-center gap-1">
            <Activity size={12} />
            Fontes: INEP, Estratégia MED, Medway, Medcel, Recurso Oficial, Portal Afya
          </p>
          <p>
            <a href="https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/revalida/provas-e-gabaritos"
               target="_blank" rel="noopener noreferrer"
               className="text-[#0071e3] hover:underline">
              gov.br/inep/revalida
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
