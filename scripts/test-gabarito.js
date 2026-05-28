import fs from 'fs';
import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const pdf = require('pdf-parse');

async function main() {
    let dataBuffer = fs.readFileSync('Provas do revalida PDF/revalida provas/2024/Prova Objetiva 01/2024_2_GB_objetiva.pdf');
    const data = await pdf(dataBuffer);
    console.log(data.text.substring(0, 1000));
}

main();
