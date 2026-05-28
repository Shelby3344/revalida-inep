import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const pdf = require('pdf-parse');

const __dirname = path.resolve();
const proofsDir = path.join(__dirname, 'Provas do revalida PDF', 'revalida provas');

// Function to extract questions from raw text
function parseQuestionsFromText(text, year) {
    const questions = [];
    
    // A regex to find blocks that look like "QUESTÃO X"
    // We will split the text by "QUESTÃO "
    const blocks = text.split(/QUESTÃO\s+(\d+)/gi);
    
    // blocks[0] is everything before the first question
    for (let i = 1; i < blocks.length; i += 2) {
        const questionNumber = parseInt(blocks[i], 10);
        let rawContent = blocks[i+1];
        
        // Find alternatives A, B, C, D
        const altARegex = /\nA\s+/g;
        const altBRegex = /\nB\s+/g;
        const altCRegex = /\nC\s+/g;
        const altDRegex = /\nD\s+/g;
        
        const indexA = rawContent.search(altARegex);
        const indexB = rawContent.search(altBRegex);
        const indexC = rawContent.search(altCRegex);
        const indexD = rawContent.search(altDRegex);
        
        let statement = rawContent;
        let alternatives = { A: "", B: "", C: "", D: "" };
        
        if (indexA !== -1 && indexB !== -1 && indexC !== -1 && indexD !== -1) {
            statement = rawContent.substring(0, indexA).trim();
            alternatives.A = rawContent.substring(indexA + 3, indexB).trim();
            alternatives.B = rawContent.substring(indexB + 3, indexC).trim();
            alternatives.C = rawContent.substring(indexC + 3, indexD).trim();
            
            // D might go until the end or until some footer. For now we take it to the end.
            // We can clean it up later if there's trailing garbage
            alternatives.D = rawContent.substring(indexD + 3).trim();
        }
        
        questions.push({
            id: `revalida_${year}_q${questionNumber}`,
            year,
            number: questionNumber,
            statement,
            alternatives,
            images: [] // To be handled manually or by advanced parser if needed
        });
    }
    
    return questions;
}

async function extractExam(year, pdfPath, outputPath) {
    try {
        console.log(`Extracting ${pdfPath}...`);
        let dataBuffer = fs.readFileSync(pdfPath);
        
        const data = await pdf(dataBuffer);
        
        // data.text contains the raw text
        console.log(`Successfully read PDF with ${data.numpages} pages.`);
        
        const questions = parseQuestionsFromText(data.text, year);
        
        fs.writeFileSync(outputPath, JSON.stringify(questions, null, 2), 'utf-8');
        console.log(`Extracted ${questions.length} questions to ${outputPath}`);
    } catch (err) {
        console.error(`Error processing ${pdfPath}:`, err);
    }
}

async function main() {
    const targetPdf = path.join(proofsDir, '2024', 'Prova Objetiva 01', '2024_2_PV_objetiva_regular.pdf');
    const outDir = path.join(__dirname, 'data', 'exams');
    if (!fs.existsSync(outDir)) {
        fs.mkdirSync(outDir, { recursive: true });
    }
    
    const targetOut = path.join(outDir, '2024_obj_01.json');
    await extractExam('2024', targetPdf, targetOut);
}

main();
