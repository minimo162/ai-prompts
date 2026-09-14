import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, rmdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { compareT10, sha256 } from '../tools/Compare-T10Bytes.mjs';
import { saveCapture } from '../tools/Save-T10Capture.mjs';

const old = "FIRST\r\nExcel.WriteToExcel.WriteCell Value: $'''old''' Tail: 1\r\nTHIRD\r\nExcel.SaveExcel.SaveAs DocumentPath: $'''short''' Tail: 2\r\nLAST";
// Fixed positive, independently written, not assembled by the comparator.
const positive = "FIRST\r\nExcel.WriteToExcel.WriteCell Value: $'''new-long''' Tail: 1\r\nTHIRD\r\nExcel.SaveExcel.SaveAs DocumentPath: $'''x''' Tail: 2\r\nLAST";
const fields = [
  { line: 2, prefix: "Excel.WriteToExcel.WriteCell Value: $'''", before: 'old', after: 'new-long' },
  { line: 4, prefix: "Excel.SaveExcel.SaveAs DocumentPath: $'''", before: 'short', after: 'x' }
];
const cases = [
  ['positive', old, positive, true],
  ['outside-one-byte', old, positive.replace('THIRD', 'ThIRD'), false],
  ['CRLF-to-LF', old, positive.replaceAll('\r\n', '\n'), false],
  ['EOF-added', old, positive + '\r\n', false],
  ['EOF-deleted', old + '\r\n', positive, false],
  ['BOM-added', old, '\uFEFF' + positive, false],
  ['BOM-deleted', '\uFEFF' + old, positive, false],
  ['line-missing', old, positive.replace('THIRD\r\n', ''), false],
  ['line-extra', old, positive + '\r\nEXTRA', false],
  ['wrong-value', old, positive.replace('new-long', 'wrong'), false],
  ['allowed-line-suffix', old, positive.replace('Tail: 1', 'Tail: 9'), false],
  ['allowed-line-prefix', old, positive.replace('WriteCell', 'WriteCells'), false],
  ['unchanged-values', old, old, false],
  ['positive-with-BOM-and-EOF', '\uFEFF' + old + '\r\n', '\uFEFF' + positive + '\r\n', true]
];
const results = [];
for (const [id, s, c, pass] of cases) {
  const result = compareT10(Buffer.from(s), Buffer.from(c), { source_sha256: sha256(Buffer.from(s)), fields });
  assert.equal(result.status === 'PASS', pass, id);
  if (id === 'positive') assert.deepEqual(result.gaps.map(g => g.shift), [0, 5, 1]);
  results.push({ id, expected: pass ? 'PASS' : 'FAIL', result });
}
assert.throws(() => compareT10(Buffer.from(old), Buffer.from(positive), { source_sha256: '0'.repeat(64), fields }), /SOURCE_HASH_MISMATCH/);
const temp = await mkdtemp(join(tmpdir(), 't10-save-'));
try {
  const text = '\uFEFFA\r\nB\n\u03a9\ud83d\ude00';
  const capture = { utf16le_base64: Buffer.from(text, 'utf16le').toString('base64'), utf16_code_units: text.length, utf8_sha256: sha256(Buffer.from(text)) };
  const target = join(temp, 'capture.txt');
  const saved = await saveCapture(capture, target);
  assert.ok((await readFile(target)).equals(Buffer.from(text)));
  assert.equal(saved.code_points, [...text].length);
  await assert.rejects(() => saveCapture(capture, target), /EEXIST/);
  await assert.rejects(() => saveCapture({ ...capture, utf8_sha256: '0'.repeat(64) }, join(temp, 'bad.txt')), /MISMATCH/);
} finally { await rm(join(temp, 'capture.txt'), { force: true }); await rmdir(temp); }
const root = new URL('../', import.meta.url);
const audit = JSON.parse(await readFile(new URL('catalog/evidence/t10-strict-20260914x-audit.json', root), 'utf8'));
assert.equal(audit.actual.length, 2);
let evidenceChecks = 0;
for (const actual of audit.actual) {
  const src = await readFile(new URL(actual.contract.source_path, root));
  assert.equal(sha256(await readFile(new URL(actual.request, root))), actual.request_sha256);
  for (const saved of actual.saved_evidence_comparisons) {
    const { path, ...expected } = saved;
    assert.deepEqual(compareT10(src, await readFile(new URL(path, root)), actual.contract), expected);
    assert.equal(saved.status, 'FAIL');
    assert.equal(saved.authorized_contents, true);
    assert.equal(saved.outside_bytes, false);
    evidenceChecks++;
  }
  assert.equal(actual.strict, 'NOT_PROVEN');
  assert.equal(actual.live_recapture.count, 0);
}
const plan = JSON.parse(await readFile(new URL(audit.plan, root), 'utf8'));
const control = await readFile(new URL(audit.local_control.output.path, root));
assert.equal(sha256(control), audit.local_control.output.sha256);
assert.ok(control.equals(Buffer.concat([Buffer.from(plan.control.input_utf8_hex, 'hex'), Buffer.from([10])])));
assert.ok((await readFile(new URL(audit.local_control.fixed_output.path, root))).equals(Buffer.from(plan.control.input_utf8_hex, 'hex')));
assert.equal(audit.counts.pad_runs + audit.counts.copilot_sends + audit.counts.clipboard_mutations, 0);
console.log(JSON.stringify({ status: 'PASS', kind: 'NON_LIVE_SYNTHETIC_ONLY', comparator_cases: results.length, source_hash_rejection: true, saver_checks: 4, saved_evidence_checks: evidenceChecks, results }, null, 2));
