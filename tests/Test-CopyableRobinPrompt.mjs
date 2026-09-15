// Static prompt/package regression only. No Copilot, browser, clipboard or PAD calls.
// Run from any directory: node tests/Test-CopyableRobinPrompt.mjs
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = p => fs.readFileSync(path.join(root, p));
const text = p => new TextDecoder('utf-8', { fatal: true }).decode(read(p));
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const baseHash = '6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c';
const bundleHash = '79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12';
const candidateHash = '66402a04a175b831d4ac16ae2514519205ccc844adf90be67bc33d020969614f';
const baseline = text('copilot/agent-instructions.txt');
const candidate = text('copilot/agent-instructions-copyable.txt');
const manifest = JSON.parse(text('copilot/copyable-output-20260915.json'));
const oldManifest = JSON.parse(text('copilot/knowledge-bundle-manifest-20260913e.json'));
const begin = '【コピー用コードブロック・必須】\n';
const end = '通常チャットで貼り付け用Robinを出す場合は、';
const oldPlacement = '対象サブフローと置換範囲を明記します。';
const newPlacement = '対象サブフローと置換範囲はブロックの外に明記します。';

function checkContract(s) {
  assert.equal(s.split(begin).length, 2, 'one new format section');
  const start = s.indexOf(begin), stop = s.indexOf(end, start);
  assert.ok(stop > start, 'the existing output contract remains');
  const restored = (s.slice(0, start) + s.slice(stop)).replace(newPlacement, oldPlacement);
  assert.equal(restored, baseline, 'generation, safety and literal-preservation rules unchanged');
  const section = s.slice(start, stop);
  assert.equal(section.includes('```'), false, 'prompt must not contain a literal fenced example');
  for (const required of [
    'Markdownのコードブロックを1つだけ使い、言語指定は `text`',
    'バッククォート3個の並びを本文として絶対に出力しません',
    '先頭行と最終の非空行はどちらも実際のPAD命令',
    '行番号付きでバッククォート3個が見える状態は失敗',
    'コードブロックを作り直します',
    'それでもRobinだけのコピー内容にできない場合は、コードを出さず',
    '画面幅に合わせた実際の改行を加えず',
    'プロンプトだけでは保証できません',
    'HTML/JavaScriptや偽のコピーボタンを生成せず',
    '直前のRobin本文を変更せず'
  ]) assert.ok(section.includes(required), 'missing format rule: ' + required);
}

function checkCopiedPayload(payload) {
  assert.equal(payload.includes('```'), false, 'Markdown fence leaked into copied payload');
  const lines = payload.split(/\r?\n/);
  const nonEmpty = lines.filter(x => x.length > 0);
  assert.ok(nonEmpty.length > 0, 'payload has a PAD instruction');
  for (const line of [nonEmpty[0], nonEmpty.at(-1)]) {
    assert.doesNotMatch(line, /^\s*(text|Plain Text|JSON)\s*$/i);
    assert.doesNotMatch(line, /^\s*#+\s/);
  }
}

test('accepted instruction and manifest are still the frozen baseline', () => {
  assert.equal(sha(read('copilot/agent-instructions.txt')), baseHash);
  assert.equal(oldManifest.instruction_sha256, baseHash);
  assert.equal(oldManifest.bundle_sha256, bundleHash);
  assert.equal(oldManifest.source_files.length, 7);
});
test('copyable r2 instruction is strict UTF-8 without BOM and below both length bounds', () => {
  const b = read('copilot/agent-instructions-copyable.txt');
  assert.notDeepEqual([...b.subarray(0, 3)], [239, 187, 191]);
  assert.equal(Buffer.from(candidate, 'utf8').compare(b), 0);
  assert.equal(sha(b), candidateHash);
  assert.ok(candidate.length <= 7000);
  assert.ok(candidate.length <= 8000);
});
test('version metadata binds r2 and records the observed r1 live failure', () => {
  assert.equal(manifest.version, '20260915-copyable-r2');
  assert.equal(manifest.instruction_path, 'copilot/agent-instructions-copyable.txt');
  assert.equal(sha(read(manifest.instruction_path)), manifest.instruction_sha256);
  assert.equal(candidate.length, manifest.instruction_utf16);
  assert.equal(read(manifest.instruction_path).length, manifest.instruction_utf8_bytes);
  assert.equal(manifest.base_instruction_path, 'copilot/agent-instructions.txt');
  assert.equal(manifest.base_instruction_sha256, baseHash);
  assert.equal(manifest.knowledge_manifest, 'copilot/knowledge-bundle-manifest-20260913e.json');
  assert.equal(manifest.bundle_path, oldManifest.bundle_path);
  assert.equal(manifest.bundle_sha256, bundleHash);
  assert.equal(manifest.status, 'STATIC_CHECKED_AFTER_LIVE_FENCE_LEAK_RETEST_REQUIRED');
  assert.equal(manifest.knowledge_changed, false);
  assert.equal(manifest.inherits_live_acceptance, false);
  assert.equal(manifest.copy_button_guaranteed, false);
  assert.equal(manifest.r1_live_observation.copy_button_displayed, true);
  assert.equal(manifest.r1_live_observation.closing_fence_visible_inside_code_block, true);
  assert.equal(manifest.r1_live_observation.copied_payload_valid_for_pad, false);
  assert.equal(manifest.r1_live_observation.pad_result, 'ERROR_DUE_TO_TRAILING_MARKDOWN_FENCE');
  assert.equal(manifest.copilot_live_retest, 'NOT_RUN_AFTER_R2');
  assert.equal(manifest.pad_live_retest, 'NOT_RUN_AFTER_R2');
});
test('r2 copy contract preserves every unrelated accepted instruction', () => checkContract(candidate));
test('safe copied payload accepts Robin without Markdown fence content', () => {
  checkCopiedPayload("Pdf.MergeFiles PDFFiles: ['C:\\\\a.pdf', 'C:\\\\b.pdf'] MergedPDFPath: $'''C:\\\\out.pdf''' IfFileExists: Pdf.IfFileExists.DoNotModifyFiles PasswordDelimiter: $''',''' MergedPDF=> MergedPDF");
});
test('copied payload rejects the exact trailing fence failure observed live', () => {
  assert.throws(() => checkCopiedPayload('Pdf.MergeFiles ...\n```'));
});
test('usage guide records r1 failure and r2 retest boundary', () => {
  const g = text('copilot/copyable-output.md');
  for (const required of [
    '`20260915-copyable-r2`',
    '閉じフェンスがコピー対象へ混入',
    'PADへ貼り付けるとエラー',
    'バッククォート3個の並びを入れない',
    '最終の非空行もPAD命令',
    'r2の実Copilotでの再生成',
    'まだ再試験前'
  ]) assert.ok(g.includes(required), required);
});
// Synthetic mutations of the documented contract, not tests of model compliance.
const mutations = [
  ['literal fence example reintroduced', s => s.replace('Markdownのコードブロックを1つだけ使い', '```text\nWAIT 1\n```\nMarkdownのコードブロックを1つだけ使い')],
  ['payload fence prohibition removed', s => s.replace('バッククォート3個の並びを本文として絶対に出力しません', 'バッククォートを本文へ出しても構いません')],
  ['last-line guard removed', s => s.replace('先頭行と最終の非空行はどちらも実際のPAD命令', '先頭行だけ実際のPAD命令')],
  ['visible numbered fence accepted', s => s.replace('行番号付きでバッククォート3個が見える状態は失敗', '行番号付きフェンスは許容')],
  ['removed UI limitation', s => s.replace('プロンプトだけでは保証できません', '常にコピーできます')],
  ['unrelated generation change', s => s.replace('AppendNewLine: False', 'AppendNewLine: True')],
  ['removed safe refusal', s => s.replace('それでもRobinだけのコピー内容にできない場合は、コードを出さず', 'それでも推測してコードを出し')]
];
for (const [name, mutate] of mutations) test('rejects ' + name, () => assert.throws(() => checkContract(mutate(candidate))));
