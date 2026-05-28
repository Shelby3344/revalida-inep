import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function parseExamInfo(id) {
  const year = id.substring(0, 4);
  const yr2 = year.slice(2);

  let cadernoNum = '01';
  if (/Objetiva_02|Prova_02|caderno_vermelho/.test(id)) cadernoNum = '02';
  else if (/Objetiva_03|_03_/.test(id)) cadernoNum = '03';

  let edition = '';
  if (year === '2022') {
    edition = /___2_obj|2022___2/.test(id) ? '/2' : '/1';
  }

  const monthMap = {
    '2011': 'Dez | 11', '2012': 'Dez | 12', '2013': 'Dez | 13',
    '2014': 'Out | 14', '2015': 'Out | 15', '2016': 'Nov | 16',
    '2017': 'Nov | 17', '2018': 'Out | 18', '2019': 'Out | 19',
    '2020': 'Nov | 20', '2021': 'Nov | 21', '2022': 'Out | 22',
    '2023': 'Out | 23', '2024': 'Out | 24', '2025': 'Out | 25',
  };

  let variant = 'Prova Objetiva';
  let cardClass = '';
  if (id.includes('caderno_cinza')) { variant = 'Caderno Cinza'; cardClass = 'exam-cover-card--cinza'; }
  else if (id.includes('caderno_vermelho')) { variant = 'Caderno Vermelho'; cardClass = 'exam-cover-card--vermelho'; }

  return { year, cadernoNum, edition, variant, cardClass, monthLabel: monthMap[year] || `Out | ${yr2}` };
}

export default function ExamList() {
  const navigate = useNavigate();
  const [exams, setExams] = useState([]);

  useEffect(() => {
    fetch('/exams/index.json')
      .then(res => res.json())
      .then(data => {
        const enriched = data.map(exam => ({
          ...exam,
          questions: exam.id.includes('2016') ? 55
            : (exam.id.includes('2017') ? 58
            : (exam.id.includes('2011') || exam.id.includes('2012') || exam.id.includes('2013') || exam.id.includes('2014') || exam.id.includes('2015') ? 110
            : 100)),
          timeLimit: '5h',
          status: 'available',
        })).sort((a, b) => b.id.localeCompare(a.id));
        setExams(enriched);
      });
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 md:px-6 py-12">
      <div className="mb-10">
        <h1 className="text-3xl font-bold mb-2">Simulados Revalida</h1>
        <p className="text-gray-500 dark:text-gray-400 mb-4">
          Resolva as provas oficiais objetivas do INEP na íntegra, com interface de prova real.
        </p>
        {exams.length > 0 && (
          <div className="flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-900 dark:text-white">{exams.length}</span>
              <span className="text-gray-500 dark:text-gray-400">cadernos disponíveis</span>
            </div>
            <div className="w-px h-4 bg-gray-300 dark:bg-gray-700" />
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-900 dark:text-white">
                {exams.reduce((acc, e) => acc + e.questions, 0).toLocaleString('pt-BR')}
              </span>
              <span className="text-gray-500 dark:text-gray-400">questões no total</span>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {exams.map(exam => {
          const info = parseExamInfo(exam.id);
          return (
            <div
              key={exam.id}
              onClick={() => navigate(`/exam/${exam.id}`)}
              className={`exam-cover-card${info.cardClass ? ` ${info.cardClass}` : ''}`}
            >
              <div className="exam-cover-reveal">INICIAR</div>

              <div className="exam-cover-main">
                {/* Caderno header */}
                <div className="border-2 border-gray-300 flex items-stretch mb-4">
                  <div className="bg-gray-800 text-white px-3 py-2 text-center font-bold flex flex-col justify-center min-w-[72px]">
                    <span className="block text-[8px] uppercase tracking-widest opacity-80">Caderno</span>
                    <span className="block text-[1.6rem] font-black leading-none my-0.5">{info.cadernoNum}</span>
                    <span className="block text-[8px] opacity-70">{info.monthLabel}</span>
                  </div>
                  <div className="flex-grow px-4 py-3 flex items-center">
                    <h2 className="text-lg font-light text-gray-900 tracking-tighter leading-tight">
                      Revalida<span className="font-bold text-gray-400 ml-1">{info.year}{info.edition}</span>
                    </h2>
                  </div>
                </div>

                {/* Instructions */}
                <div className="flex-grow">
                  <h3 className="font-bold text-center text-[9px] uppercase tracking-wider mb-3 text-gray-800">
                    Leia com atenção as instruções abaixo
                  </h3>
                  <ol className="list-decimal list-inside space-y-1.5 text-[10px] leading-snug text-gray-700">
                    <li>Verifique se você recebeu o <b>CARTÃO-RESPOSTA</b>.</li>
                    <li>Este caderno contém <b>{exam.questions} questões</b> de múltipla escolha.</li>
                    <li>Verifique se o seu nome está correto no <b>CARTÃO-RESPOSTA</b>.</li>
                    <li>Respostas com <b>caneta esferográfica de tinta preta</b>.</li>
                    <li>A prova terá duração de <b>5 (cinco) horas</b>.</li>
                    <li>Não realize qualquer consulta durante a prova.</li>
                    <li>Permanência mínima de <b>2 (duas) horas</b> na sala.</li>
                    <li>Entregue o <b>CARTÃO-RESPOSTA</b> ao Chefe de Sala.</li>
                  </ol>
                </div>

                <div className="mt-4 border-t border-gray-200 pt-2" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
