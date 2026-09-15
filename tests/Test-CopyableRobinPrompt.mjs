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
  // Removing only the added formatting section and clarification must recover all baseline text.
  const restored = (s.slice(0, start) + s.slice(stop)).replace(newPlacement, oldPlacement);
  assert.equal(restored, baseline, 'generation, safety and literal-preservation rules unchanged');
  const section = s.slice(start, stop);
  assert.deepEqual(s.split('\n').filter(line => /^\s*```/.test(line)), ['```text', '```']);
  assert.equal((section.match(/^```text\nWAIT 1\n```$/gm) || []).length, 1, 'one top-level fence example');
  for (const required of [
    'チャット本文にMarkdownのフェンス付きコードブロックを1つだけ',
    '箇条書き・表・引用の中へ入れません',
    'textは開始フェンスの言語指定であり、Robin本文ではありません',
    'コードブロック内には貼り付ける完全なRobinだけ',
    '画面幅に合わせた実際の改行を加えず',
    'コードを出さず理由を説明します',
    'プロンプトだけでは保証できません',
    'HTML/JavaScriptや偽のコピーボタンを生成せず',
    '直前のRobinの内容を変更せずフェンスだけを整えます',
    'この例を別ブロックで再掲したり、不要なWAITを追加したりしません'
  ]) assert.ok(section.includes(required), 'missing format rule: ' + required);
}

test('accepted instruction and manifest are still the frozen baseline', () => {
  assert.equal(sha(read('copilot/agent-instructions.txt')), baseHash);
  assert.equal(oldManifest.instruction_sha256, baseHash);
  assert.equal(oldManifest.bundle_sha256, bundleHash);
  assert.equal(oldManifest.source_files.length, 7);
});
test('copyable instruction is strict UTF-8 without BOM and below both length bounds', () => {
  const b = read('copilot/agent-instructions-copyable.txt');
  assert.notDeepEqual([...b.subarray(0, 3)], [239, 187, 191]);
  assert.equal(Buffer.from(candidate, 'utf8').compare(b), 0);
  assert.ok(candidate.length <= 7000);
  assert.ok(candidate.length <= 8000);
});
test('version metadata binds the new instruction without claiming live acceptance', () => {
  assert.equal(manifest.version, '20260915-copyable');
  assert.equal(manifest.instruction_path, 'copilot/agent-instructions-copyable.txt');
  assert.equal(sha(read(manifest.instruction_path)), manifest.instruction_sha256);
  assert.equal(candidate.length, manifest.instruction_utf16);
  assert.equal(read(manifest.instruction_path).length, manifest.instruction_utf8_bytes);
  assert.equal(manifest.base_instruction_path, 'copilot/agent-instructions.txt');
  assert.equal(manifest.base_instruction_sha256, baseHash);
  assert.equal(manifest.knowledge_manifest, 'copilot/knowledge-bundle-manifest-20260913e.json');
  assert.equal(manifest.bundle_path, oldManifest.bundle_path);
  assert.equal(manifest.bundle_sha256, bundleHash);
  assert.equal(manifest.status, 'STATIC_CHECKED_LIVE_UNVERIFIED');
  for (const k of ['knowledge_changed', 'inherits_live_acceptance', 'copy_button_guaranteed']) assert.equal(manifest[k], false);
  for (const k of ['copilot_live_test', 'pad_live_test']) assert.equal(manifest[k], 'NOT_RUN');
});
test('single text-fence contract preserves every unrelated instruction', () => checkContract(candidate));
test('README routes the quick start to the full new instruction, not both versions', () => {
  const r = text('README.md');
  assert.ok(r.includes('2. [`copilot/agent-instructions-copyable.txt`]'));
  assert.ok(r.includes('二重に貼らない'));
  assert.ok(r.includes('基準版のみ'));
  assert.ok(r.includes('実Copilot・PAD受入は未検証'));
  assert.ok(r.includes('(copilot/copyable-output.md)'));
});
test('usage guide distinguishes native copy from whole-answer copy and states the limit', () => {
  const g = text('copilot/copyable-output.md');
  for (const required of ['回答全体のコピーボタンとは区別', 'プロンプトだけでは保証できません',
    '原文を確認できない場合', '実行は未検証', '既存のWindows PowerShell全テストは今回再実行していません']) {
    assert.ok(g.includes(required), required);
  }
});
// These are synthetic mutations of the documented contract, not tests of model compliance.
const mutations = [
  ['unsupported language tag', s => s.replace('\n```text\n', '\n```robin\n')],
  ['indented fence', s => s.replace('\n```text\n', '\n    ```text\n')],
  ['quoted fence', s => s.replace('\n```text\n', '\n> ```text\n')],
  ['label inside code', s => s.replace('\nWAIT 1\n', '\nPlain Text\nWAIT 1\n')],
  ['missing closing fence', s => s.replace('\n```\n', '\n')],
  ['duplicate block', s => s.replace('\n```\n', '\n```\n\n```text\nWAIT 1\n```\n')],
  ['changed example instruction', s => s.replace('\nWAIT 1\n', '\nWAIT 500\n')],
  ['removed UI limitation', s => s.replace('プロンプトだけでは保証できません', '常にコピーできます')],
  ['unrelated generation change', s => s.replace('AppendNewLine: False', 'AppendNewLine: True')],
  ['removed safe refusal', s => s.replace('コードを出さず理由を説明します', '推測でコードを生成します')]
];
for (const [name, mutate] of mutations) test('rejects ' + name, () => assert.throws(() => checkContract(mutate(candidate))));
