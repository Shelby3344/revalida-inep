import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const pdf = require('pdf-parse');

const __dirname = path.resolve();
const proofsDir = path.join(__dirname, 'Provas do revalida PDF', 'revalida provas');
const outDir = path.join(__dirname, 'public', 'exams');

if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
}

// Reuse the parsing logic
function parseQuestionsFromText(text, year) {
    const questions = [];
    const blocks = text.split(/QUESTÃO\s+(\d+)/gi);
    
    for (let i = 1; i < blocks.length; i += 2) {
        const questionNumber = parseInt(blocks[i], 10);
        let rawContent = blocks[i+1];
        
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
            alternatives.A = rawContent.substring(indexA + 2, indexB).trim();
            alternatives.B = rawContent.substring(indexB + 2, indexC).trim();
            alternatives.C = rawContent.substring(indexC + 2, indexD).trim();
            alternatives.D = rawContent.substring(indexD + 2).trim();
        }
        
        questions.push({
            id: `revalida_${year}_q${questionNumber}`,
            year,
            number: questionNumber,
            statement,
            alternatives,
            images: []
        });
    }
    
    return questions;
}

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

async function processDirectory(dirPath, year) {
    const items = fs.readdirSync(dirPath);
    let objFile = null;
    let gbFile = null;

    for (const item of items) {
        const fullPath = path.join(dirPath, item);
        const stat = fs.statSync(fullPath);
        if (stat.isDirectory()) {
            await processDirectory(fullPath, year); // Recurse
        } else if (item.endsWith('.pdf')) {
            const lowerItem = item.toLowerCase();
            if (lowerItem.includes('gb') || lowerItem.includes('gabarito')) {
                gbFile = fullPath;
            } else if (lowerItem.includes('obj')) {
                objFile = fullPath;
            }
        }
    }

    if (objFile) {
        // Create an ID
        const dirName = path.basename(dirPath).replace(/[^a-zA-Z0-9]/g, '_');
        const baseId = `${year}_${dirName}`;
        
        try {
            console.log(`Processing Exam: ${objFile}`);
            const dataBuffer = fs.readFileSync(objFile);
            const data = await pdf(dataBuffer);
            const questions = parseQuestionsFromText(data.text, year);
            fs.writeFileSync(path.join(outDir, `${baseId}_obj.json`), JSON.stringify(questions, null, 2), 'utf-8');
            console.log(`Saved ${questions.length} questions for ${baseId}`);
        } catch (e) {
            console.error(`Failed ${objFile}:`, e.message);
        }

        if (gbFile) {
            try {
                console.log(`Processing Gabarito: ${gbFile}`);
                const gbBuffer = fs.readFileSync(gbFile);
                const gbData = await pdf(gbBuffer);
                const gabarito = parseGabaritoFromText(gbData.text);
                fs.writeFileSync(path.join(outDir, `${baseId}_gabarito.json`), JSON.stringify(gabarito, null, 2), 'utf-8');
                console.log(`Saved gabarito for ${baseId}`);
            } catch (e) {
                console.error(`Failed Gabarito ${gbFile}:`, e.message);
            }
        }
    }
}

async function main() {
    const years = fs.readdirSync(proofsDir);
    for (const year of years) {
        const yearPath = path.join(proofsDir, year);
        if (fs.statSync(yearPath).isDirectory()) {
            await processDirectory(yearPath, year);
        }
    }

    // Now generate a registry of all extracted exams
    const allFiles = fs.readdirSync(outDir);
    const objFiles = allFiles.filter(f => f.endsWith('_obj.json'));
    const registry = objFiles.map(f => {
        const id = f.replace('.json', '');
        return {
            id,
            title: `Revalida ${id.split('_')[0]} - ${id.replace(/_/g, ' ')}`.replace(' obj', ''),
            file: f
        };
    });
    
    // Save to an index file
    fs.writeFileSync(path.join(outDir, 'index.json'), JSON.stringify(registry, null, 2), 'utf-8');
    console.log("Done extracting all exams!");
}

main();
