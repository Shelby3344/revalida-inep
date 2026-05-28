import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, XCircle } from 'lucide-react';

export default function ExamViewer() {
  const { examId } = useParams();
  const navigate = useNavigate();
  
  const [questions, setQuestions] = useState([]);
  const [gabarito, setGabarito] = useState({});
  const [loading, setLoading] = useState(true);
  
  const [answers, setAnswers] = useState({});
  const [showResults, setShowResults] = useState(false);

  // Derivar o ano pelo ID
  const yearMatch = examId ? examId.match(/^(\d{4})/) : null;
  const examYear = yearMatch ? yearMatch[1] : 'INEP';

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const qRes = await fetch(`/exams/${examId}.json`);
        const qData = await qRes.json();
        
        const gRes = await fetch(`/exams/${examId.replace('_obj_', '_gabarito_')}.json`);
        let gData = {};
        if (gRes.ok) {
            gData = await gRes.json();
        }

        setQuestions(qData);
        setGabarito(gData);
      } catch (err) {
        console.error("Failed to load exam data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [examId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#0071e3]"></div>
      </div>
    );
  }

  if (!questions || questions.length === 0) {
    return (
      <div className="text-center py-20 text-gray-500">
        Prova não encontrada ou ocorreu um erro no carregamento.
      </div>
    );
  }

  const handleAnswer = (qNumber, altLetter) => {
    if (showResults) return; 
    setAnswers(prev => ({
      ...prev,
      [qNumber]: altLetter
    }));
  };

  const handleFinish = () => {
    if (window.confirm('Deseja realmente finalizar a prova e ver o resultado?')) {
      setShowResults(true);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const isCorrect = (qNumber, selected) => {
    return gabarito[qNumber] === selected;
  };

  const getAlternativeStyle = (qNumber, letter) => {
    const selected = answers[qNumber];
    const correctAns = gabarito[qNumber];
    const isThisSelected = selected === letter;
    
    let base = "flex gap-2 text-justify-custom cursor-pointer p-1.5 rounded transition-colors ";
    
    if (!showResults) {
      if (isThisSelected) {
        return base + "bg-blue-100 dark:bg-blue-900/30 text-blue-900 dark:text-blue-100";
      }
      return base + "hover:bg-gray-100 dark:hover:bg-gray-800";
    } else {
      const isThisCorrect = correctAns === letter;
      if (isThisCorrect) {
        return base + "bg-green-100 dark:bg-green-900/40 text-green-900 dark:text-green-100 font-medium";
      }
      if (isThisSelected && !isThisCorrect) {
        return base + "bg-red-100 dark:bg-red-900/40 text-red-900 dark:text-red-100 line-through";
      }
      return base + "opacity-50";
    }
  };

  return (
    <div className="bg-[#e5e5e5] dark:bg-[#1a1a1a] min-h-screen py-8">
      
      {/* Floating Header */}
      <div className="max-w-[210mm] mx-auto mb-6 flex items-center justify-between px-4">
        <button onClick={() => navigate('/exams')} className="text-gray-600 dark:text-gray-300 hover:text-black dark:hover:text-white flex items-center gap-2 bg-white/50 dark:bg-black/50 backdrop-blur px-3 py-1.5 rounded-full shadow-sm">
          <ArrowLeft size={16} /> Voltar
        </button>
        
        {!showResults ? (
          <button onClick={handleFinish} className="bg-[#0071e3] text-white px-5 py-2 rounded-full font-bold shadow hover:bg-blue-600 transition-colors">
            Finalizar Simulado
          </button>
        ) : (
          <div className="bg-white dark:bg-[#1c1c1e] text-black dark:text-white px-4 py-2 rounded-full font-bold shadow-sm flex items-center gap-2">
            Resultado: {Object.keys(answers).filter(k => isCorrect(k, answers[k])).length} / {questions.length}
          </div>
        )}
      </div>

      {/* Papel A4 */}
      <div className="a4-page text-[13.5px] leading-snug">
        
        {/* Cabeçalho */}
        <header className="text-center mb-8">
            <h1 className="text-4xl tracking-tighter" style={{ fontFamily: "'Arial', sans-serif" }}>
                <span className="font-bold">Revalida</span><span className="text-gray-400 font-light"> {examYear}</span>
            </h1>
        </header>

        {/* Colunas */}
        <div className="exam-columns">
          {questions.map((q) => {
            const qNumStr = String(q.number).padStart(2, '0');
            return (
              <div key={q.id} className="exam-question-block">
                
                {/* Banner */}
                <div className="question-banner">
                    <span className="font-bold text-sm tracking-widest mr-2">QUESTÃO</span> 
                    <svg width="10" height="10" viewBox="0 0 10 10" className="fill-current text-white/50 mr-2"><polygon points="0,10 10,0 10,10"/></svg>
                    <span className="font-bold text-sm tracking-widest">{qNumStr}</span>
                </div>

                {/* Enunciado */}
                <div className="mb-4 text-justify-custom" style={{ textIndent: '1rem' }}>
                  {q.statement.replace(/\n/g, ' ')}
                </div>

                {/* Alternativas */}
                <div className="flex flex-col gap-1">
                  {Object.entries(q.alternatives).map(([letter, text]) => {
                    if (!text) return null;
                    return (
                      <div 
                        key={letter} 
                        className={getAlternativeStyle(q.number, letter)}
                        onClick={() => handleAnswer(q.number, letter)}
                      >
                        <span className="font-bold">({letter})</span>
                        <span>{text.replace(/\n/g, ' ')}</span>
                      </div>
                    );
                  })}
                </div>

                {/* Explicação / Alerta de Erro no modo Review */}
                {showResults && (
                  <div className="mt-3 text-xs">
                    {answers[q.number] === gabarito[q.number] ? (
                      <span className="flex items-center gap-1 text-green-600 font-bold"><CheckCircle size={14} /> Resposta Correta</span>
                    ) : (
                      <span className="flex items-center gap-1 text-red-600 font-bold"><XCircle size={14} /> Você errou (Gabarito: {gabarito[q.number] || 'Anulada'})</span>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
}
