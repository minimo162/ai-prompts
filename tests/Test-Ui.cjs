// Development-only rendered browser check against an actual App.ps1 localhost server.
// npm playwright is a test dependency, never an application/distribution requirement.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const home = path.resolve(process.argv[2] || '.work/ui-home');
  const runtime = JSON.parse(fs.readFileSync(path.join(home, 'data', 'server.json'), 'utf8'));
  const base = `http://127.0.0.1:${runtime.port}`;
  assert.equal(runtime.offline_test, true, 'Server must be launched with -OfflineTest');
  assert(!fs.existsSync(path.join(home, 'data', 'edge-profile')), 'Reject any existing browser profile');
  const jobs = path.join(home, 'data', 'jobs');
  assert(fs.readdirSync(jobs).length === 0, 'Reject existing jobs, including per-job Copilot connections');
  const target = path.join(home, 'synthetic-input.txt');
  fs.writeFileSync(target, '検証用の合成文章です。実サービスへ送信しません。\n', 'utf8');
  const headers = { 'X-App-Token': runtime.token };
  // This test requires a fresh, unsigned-in application home; it must not send to Copilot.
  assert(!fs.existsSync(path.join(home, 'data', 'copilot-target.json')), 'Use an isolated test home without a Copilot target');
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  let checks = 0;
  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`${base}/#token=${runtime.token}`);
    await page.getByText('アプリに接続済み', { exact: true }).waitFor(); checks++;
    assert(!page.url().includes('token=')); checks++;
    await page.locator('#goal').fill('このテキストを英訳してください（接続失敗経路の検証）');
    await page.locator('#target').fill(target);
    const previous = await fetch(`${base}/api/state`, { headers }).then(r => r.json());
    await page.locator('#start').click();
    let state;
    const deadline = Date.now() + 20000;
    do {
      state = await fetch(`${base}/api/state`, { headers }).then(r => r.json());
      if (state.job?.job_id !== previous.job?.job_id && state.job?.status === 'failed') break;
      await new Promise(resolve => setTimeout(resolve, 200));
    } while (Date.now() < deadline);
    await page.getByText('エラーで終了', { exact: true }).waitFor({ timeout: 20000 }); checks++;
    assert.notEqual(state.job.job_id, previous.job?.job_id);
    assert.equal(state.job.status, 'failed'); checks++;
    assert.match(state.job.error, /CDP_UNAVAILABLE/); checks++;
    assert.equal(state.job.artifacts.length, 0); checks++;
    assert.equal(state.job.final_answer, ''); checks++;
    assert(await page.locator('#start').isEnabled()); checks++;
    assert(await page.locator('#stop').isDisabled()); checks++;
    await page.reload();
    await page.getByText('アプリに接続済み', { exact: true }).waitFor(); checks++;
    assert.equal(await page.locator('#goal').inputValue(), state.job.goal); checks++;
    await page.screenshot({ path: path.join(home, 'ui-desktop.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(home, 'ui-mobile.png'), fullPage: true });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)); checks++;
    await page.close();
    const reopened = await context.newPage();
    await reopened.goto(`${base}/#token=${runtime.token}`);
    await reopened.getByText('エラーで終了', { exact: true }).waitFor(); checks++;
    const after = await fetch(`${base}/api/state`, { headers }).then(r => r.json());
    assert.equal(after.job.job_id, state.job.job_id); checks++;
    assert.equal(errors.length, 0, errors.join('\n')); checks++;
    console.log(`PASS: ${checks} rendered Edge / real localhost checks (start -> missing Copilot failure, reload, reopen, responsive). No live AI/PAD run.`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
