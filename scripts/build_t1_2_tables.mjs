import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { Workbook } from '@oai/artifact-tool';

const [payloadPath, outputDir, previewDir] = process.argv.slice(2);
const tables = JSON.parse(await fs.readFile(payloadPath, 'utf8'));
const book = Workbook.create();
for (const [filename, matrix] of Object.entries(tables)) {
  const isHuman = filename === 'human_terminology_decisions.tsv';
  const sheet = book.worksheets.add(isHuman ? 'Recorded decisions' : 'Sami');
  const range = sheet.getRangeByIndexes(0, 0, matrix.length, matrix[0].length);
  range.values = matrix;
  if (JSON.stringify(range.values) !== JSON.stringify(matrix)) throw new Error('Cell round-trip failed');
  const quote = value => /[\t\r\n"]/.test(value) ? `"${value.replaceAll('"', '""')}"` : value;
  const text = range.values.map(row => row.map(quote).join('\t')).join('\n') + '\n';
  const target = path.join(outputDir, filename);
  if (isHuman) {
    const previous = await fs.readFile(target);
    const digest = crypto.createHash('sha256').update(previous).digest('hex');
    if (digest !== 'be3269d83f394a80889803aef6cbfeb198178cc02d781de630d11f0b02ffc97a' && previous.toString('utf8') !== text) {
      throw new Error('Unexpected existing human decisions; refusing overwrite');
    }
    await fs.writeFile(target, text, 'utf8');
  } else {
    await fs.writeFile(target, text, {encoding:'utf8', flag:'wx'});
  }
  range.format.font.size = 11;
  range.format.rowHeight = isHuman ? 26 : 135;
  range.format.columnWidth = 28;
  range.format.wrapText = true;
  sheet.getRange('A:A').format.columnWidth = 12;
  if (!isHuman) sheet.getRange('C:C').format.columnWidth = 75;
  else sheet.getRange('C:C').format.columnWidth = 50;
  sheet.getRange('A1:C1').format.font.bold = true;
  const preview = await book.render({sheetName:sheet.name, range:isHuman ? 'A1:C4' : 'A1:C4', scale:1, format:'png'});
  await fs.writeFile(path.join(previewDir, isHuman ? 'decisions.png' : 'sami.png'), new Uint8Array(await preview.arrayBuffer()));
}
console.log('Two TSVs exported with exact cell round-trip and protected human-file transition.');
