// Fixed six-row synthetic CSV evidence only; no PAD, clipboard or payment calls.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const files = process.argv.slice(2);
assert.equal(files.length, 2, 'Provide the two original PAD output CSV files.');
const fixture = fs.readFileSync(path.join(root, 'catalog/fixtures/finance-expense-dummy/input.csv'));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
// BOM/newline handling is only for the logical comparison. Original bytes remain untouched.
const lines = b => new TextDecoder('utf-8', { fatal: true }).decode(b)
  .replace(/\r\n/g, '\n').replace(/\n$/, '').split('\n');
const expected = lines(fixture);
assert.equal(expected.length, 7, 'Fixed fixture must contain header plus six rows.');
const outputs = files.map(file => fs.readFileSync(file));
const results = outputs.map((bytes, i) => {
  const actual = lines(bytes);
  assert.deepEqual(actual, expected, 'All header, row, field, ID and amount values must match the fixed input.');
  const rows = actual.slice(1).map(s => s.split(','));
  assert.ok(rows.every(r => r.length === 4), 'Fixed fixture has exactly four fields per row.');
  assert.deepEqual(rows.map(r => r[0]), ['R01', 'R02', 'R03', 'R04', 'R05', 'R06']);
  assert.equal(rows.reduce((n, r) => n + Number(r[2]), 0), 43001);
  return { file: files[i], status: 'PASS_FIXED_PAD_CSV_CONTENT', rows: 6, columns: 4,
    total_jpy_checked_externally: 43001, bytes: bytes.length, sha256: sha(bytes),
    utf8_bom: bytes.subarray(0, 3).equals(Buffer.from([0xef, 0xbb, 0xbf])),
    final_lf: bytes.at(-1) === 10 };
});
assert.deepEqual(outputs[0], outputs[1], 'Run1 and Run2 must also match as original bytes.');
console.log(JSON.stringify({ status: 'PASS', results, same_raw_bytes: true,
  verification_kind: 'Offline fixed fixture comparison; live PAD status comes from observations.json' }, null, 2));
