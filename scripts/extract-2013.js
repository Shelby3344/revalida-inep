import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const pdf = require('pdf-parse');

const __dirname = path.resolve();
const outDir = path.join(__dirname, 'public', 'exams');
const provasDir = path.join(__dirname, 'Provas do revalida PDF', 'revalida provas', '2013');

// 2013 uses QUESTÃO X pattern same as other years, but alternatives are A) B) C) D) E)
// (5 alternativas — anos antigos tinham E)
function parseQuestionsFromText(text, caderno) {
    const questions = [];
    const blocks = text.split(/QUEST[ÃA]O\s+(\d+)/gi);

    for (let i = 1; i < blocks.length; i += 2) {
        const num = parseInt(blocks[i], 10);
        const raw = blocks[i + 1] || '';

        // Find A) B) C) D) E) markers
        const idxA = raw.search(/\nA\)/);
        const idxB = raw.search(/\nB\)/);
        const idxC = raw.search(/\nC\)/);
        const idxD = raw.search(/\nD\)/);
        const idxE = raw.search(/\nE\)/);

        let statement = raw.trim();
        const alternatives = { A: '', B: '', C: '', D: '', E: '' };

        if (idxA !== -1 && idxB !== -1 && idxC !== -1 && idxD !== -1 && idxE !== -1) {
            statement = raw.substring(0, idxA).trim();
            alternatives.A = raw.substring(idxA + 3, idxB).trim();
            alternatives.B = raw.substring(idxB + 3, idxC).trim();
            alternatives.C = raw.substring(idxC + 3, idxD).trim();
            alternatives.D = raw.substring(idxD + 3, idxE).trim();
            alternatives.E = raw.substring(idxE + 3).trim();
        } else if (idxA !== -1 && idxB !== -1 && idxC !== -1 && idxD !== -1) {
            // Fallback: 4 alternativas
            statement = raw.substring(0, idxA).trim();
            alternatives.A = raw.substring(idxA + 3, idxB).trim();
            alternatives.B = raw.substring(idxB + 3, idxC).trim();
            alternatives.C = raw.substring(idxC + 3, idxD).trim();
            alternatives.D = raw.substring(idxD + 3).trim();
            delete alternatives.E;
        }

        questions.push({
            id: `revalida_2013_${caderno}_q${num}`,
            year: '2013',
            number: num,
            statement,
            alternatives,
            images: [],
        });
    }
    return questions;
}

function parseGabaritoFromText(text) {
    const gabarito = {};
    // Tenta padrão "Gabarito ABCDE..."
    const gabLines = text.split('\n').map(l => l.trim()).filter(l => /^Gabarito/i.test(l));
    if (gabLines.length > 0) {
        let allAnswers = gabLines.map(l => l.replace(/^Gabarito/i, '').trim()).join('');
        for (let i = 0; i < allAnswers.length; i++) {
            gabarito[i + 1] = allAnswers[i] === '—' ? 'ANULADA' : allAnswers[i];
        }
        return gabarito;
    }
    // Fallback: procura linhas "N letra" ou "N. letra"
    const lines = text.split('\n').map(l => l.trim());
    for (const line of lines) {
        const m = line.match(/^(\d+)[.)]\s*([A-Ea-e])\b/);
        if (m) gabarito[parseInt(m[1])] = m[2].toUpperCase();
    }
    return gabarito;
}

async function extractCaderno(pdfPath, gabPdfPath, caderno, fileId) {
    console.log(`\n=== ${caderno.toUpperCase()} ===`);

    // Extrai questões
    const buf = fs.readFileSync(pdfPath);
    const data = await pdf(buf);
    console.log(`PDF lido: ${data.numpages} páginas`);

    const questions = parseQuestionsFromText(data.text, caderno);
    const objPath = path.join(outDir, `${fileId}_obj.json`);
    fs.writeFileSync(objPath, JSON.stringify(questions, null, 2), 'utf-8');
    console.log(`✅ ${questions.length} questões → ${fileId}_obj.json`);

    // Extrai gabarito
    const gabBuf = fs.readFileSync(gabPdfPath);
    const gabData = await pdf(gabBuf);
    const gabarito = parseGabaritoFromText(gabData.text);
    const gabPath = path.join(outDir, `${fileId}_gabarito.json`);
    fs.writeFileSync(gabPath, JSON.stringify(gabarito, null, 2), 'utf-8');
    const gabCount = Object.keys(gabarito).length;
    console.log(`✅ ${gabCount} respostas no gabarito → ${fileId}_gabarito.json`);

    // Dump do texto bruto para debug se algo sair errado
    if (questions.length < 100) {
        fs.writeFileSync(path.join(__dirname, 'data', `_2013_${caderno}_dump.txt`), data.text, 'utf-8');
        console.log(`⚠️  Apenas ${questions.length} questões extraídas. Dump salvo para inspeção.`);
    }
    if (gabCount < 100) {
        fs.writeFileSync(path.join(__dirname, 'data', `_2013_${caderno}_gab_dump.txt`), gabData.text, 'utf-8');
        console.log(`⚠️  Apenas ${gabCount} gabaritos extraídos. Dump salvo para inspeção.`);
    }

    return { questions: questions.length, gabarito: gabCount };
}

function updateIndex(cinzaCount, vermelhoCount) {
    const indexPath = path.join(outDir, 'index.json');
    const index = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));

    const alreadyHas = (id) => index.some(e => e.id === id);

    if (!alreadyHas('2013_caderno_cinza_obj')) {
        index.push({
            id: '2013_caderno_cinza_obj',
            title: 'Revalida 2013 - 2013 caderno cinza',
            file: '2013_caderno_cinza_obj.json',
        });
    }
    if (!alreadyHas('2013_caderno_vermelho_obj')) {
        index.push({
            id: '2013_caderno_vermelho_obj',
            title: 'Revalida 2013 - 2013 caderno vermelho',
            file: '2013_caderno_vermelho_obj.json',
        });
    }

    fs.writeFileSync(indexPath, JSON.stringify(index, null, 2), 'utf-8');
    console.log(`\n✅ index.json atualizado com caderno cinza (${cinzaCount}q) e vermelho (${vermelhoCount}q)`);
}

async function main() {
    const cinzaDir = path.join(provasDir, 'caderno cinza');
    const vermelhoDir = path.join(provasDir, 'caderno vermelho');

    const cinza = await extractCaderno(
        path.join(cinzaDir, 'po_cinza_revalida_2013.pdf'),
        path.join(cinzaDir, 'po_cinza_gabarito_definitivo_revalida_2013.pdf'),
        'cinza',
        '2013_caderno_cinza'
    );

    const vermelho = await extractCaderno(
        path.join(vermelhoDir, 'po_vermelha_revalida_2013.pdf'),
        path.join(vermelhoDir, 'po_vermelha_gabarito_definitivo_revalida_2013.pdf'),
        'vermelho',
        '2013_caderno_vermelho'
    );

    updateIndex(cinza.questions, vermelho.questions);
}

main().catch(console.error);
