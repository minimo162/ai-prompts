// Fixed synthetic fixture verification; never approves payments or proves PAD execution.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const expected = fs.readFileSync(path.join(root, 'catalog/fixtures/finance-expense-dummy/expected.csv'), 'utf8');
const lines = s => s.replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n');
const expectedLines = lines(expected);
const totalExpected = 43001;
const files = process.argv.slice(2);
assert.ok(files.length, 'Provide one or more copied CSV paths.');
const results = files.map(file => {
  const bytes = fs.readFileSync(file);
  const s = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes);
  assert.ok(!s.startsWith('\uFEFF'), 'BOM must be examined explicitly; fixed fixture has none.');
  assert.ok(!s.includes('```'), 'Markdown fence contamination');
  const actual = lines(s);
  assert.deepEqual(actual, expectedLines, 'Header, order, row count, IDs, amounts or reasons differ');
  const total = actual.slice(1).reduce((n, row) => n + Number(row.split(',')[2]), 0);
  assert.equal(total, totalExpected);
  return { file, status: 'PASS_FIXED_CSV_CONTENT', rows: actual.length - 1, total_jpy: total,
    sha256: crypto.createHash('sha256').update(bytes).digest('hex'),
    final_lf: s.endsWith('\n'), bytes: bytes.length };
});
console.log(JSON.stringify({ results, same_raw_bytes: new Set(results.map(r => r.sha256)).size === 1,
  native_pad: 'NOT_RUN', corporate_m365: 'NOT_RUN', connector_execution: 'NOT_RUN' }, null, 2));
