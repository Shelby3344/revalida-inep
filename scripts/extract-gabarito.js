import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const pdf = require('pdf-parse');

const __dirname = path.resolve();
const proofsDir = path.join(__dirname, 'Provas do revalida PDF', 'revalida provas');

// Function to extract gabarito from raw text
function parseGabaritoFromText(text) {
    const gabarito = {};
    const lines = text.split('\n').map(l => l.trim()).filter(l => l.startsWith('Gabarito'));
    
    let allAnswers = '';
    for (const line of lines) {
        allAnswers += line.replace('Gabarito', '').trim();
    }
    
    for (let i = 0; i < allAnswers.length; i++) {
        gabarito[i + 1] = allAnswers[i] === '—' ? 'ANULADA' : allAnswers[i];
    }
    
    return gabarito;
}

async function extractGabarito(pdfPath, outputPath) {
    try {
        console.log(`Extracting Gabarito from ${pdfPath}...`);
        let dataBuffer = fs.readFileSync(pdfPath);
        
        const data = await pdf(dataBuffer);
        
        const gabarito = parseGabaritoFromText(data.text);
        
        fs.writeFileSync(outputPath, JSON.stringify(gabarito, null, 2), 'utf-8');
        console.log(`Extracted gabarito for ${Object.keys(gabarito).length} questions to ${outputPath}`);
    } catch (err) {
        console.error(`Error processing ${pdfPath}:`, err);
    }
}

async function main() {
    const targetPdf = path.join(proofsDir, '2024', 'Prova Objetiva 01', '2024_2_GB_objetiva.pdf');
    const outDir = path.join(__dirname, 'data', 'exams');
    if (!fs.existsSync(outDir)) {
        fs.mkdirSync(outDir, { recursive: true });
    }
    
    const targetOut = path.join(outDir, '2024_gabarito_01.json');
    await extractGabarito(targetPdf, targetOut);
}

main();
