// Run a copy in a temporary directory with the bundled node_modules junction.
// Arguments: table-payload.json, repository/adjudication path, scratch preview path.
import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook } from '@oai/artifact-tool';

const [payloadPath, outputDir, previewPath] = process.argv.slice(2);
const tables = JSON.parse(await fs.readFile(payloadPath, 'utf8'));
const workbook = Workbook.create();
for (const [filename, matrix] of Object.entries(tables)) {
  const sheet = workbook.worksheets.add(filename.startsWith('human_') ? 'Human decisions' : 'Queue');
  const range = sheet.getRangeByIndexes(0, 0, matrix.length, matrix[0].length);
  range.values = matrix;
  const readback = range.values;
  if (JSON.stringify(readback) !== JSON.stringify(matrix)) throw new Error(`Cell round-trip mismatch: ${filename}`);
  const escape = value => /[\t\n\r"]/.test(value) ? `"${value.replaceAll('"', '""')}"` : value;
  const text = readback.map(row => row.map(escape).join('\t')).join('\n') + '\n';
  const destination = path.join(outputDir, filename);
  try {
    const old = await fs.readFile(destination, 'utf8');
    if (old !== text) throw new Error(`Refusing to overwrite differing artifact: ${filename}`);
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
    await fs.writeFile(destination, text, { encoding: 'utf8', flag: 'wx' });
  }
  sheet.freezePanes.freezeRows(1);
  range.format.font.size = 11;
  range.format.columnWidth = 24;
  range.format.rowHeight = 32;
  sheet.getRangeByIndexes(0, 0, 1, matrix[0].length).format.font.bold = true;
}
const check = await workbook.inspect({kind:'table', range:"'Queue'!A1:F6", include:'values,formulas', tableMaxRows:6, tableMaxCols:6});
console.log(check.ndjson);
const preview = await workbook.render({sheetName:'Queue', range:'A1:F6', scale:1, format:'png'});
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
console.log('TSV cell round-trip and export complete; decision cells blank.');
