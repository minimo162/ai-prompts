// Rendered Edge + real PS5 HTTP/child worker. Provider is replaced in an isolated copy.
// Both server and worker retain -OfflineTest; production Copilot HTTP/PAD boundaries refuse I/O.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const { randomUUID } = require('node:crypto');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
  const repo = path.resolve(__dirname, '..');
  const root = path.join(repo, '.work', `csv-ui-${randomUUID().replaceAll('-', '')}`);
  const app = path.join(root, 'app'); const home = path.join(root, 'home');
  assert(!fs.existsSync(root)); fs.mkdirSync(app, { recursive: true });
  const fixture = `
function Invoke-AgentCopilot {
  param($Prompt,$RequestId,$JobId,$Settings,$HomePath,$CancelPath,$TimeoutSeconds)
  if (-not $script:AgentOfflineTest) { throw 'TEST_REQUIRES_OFFLINE' }
  $payload = ConvertFrom-Json ($Prompt.Substring($Prompt.IndexOf("REQUEST_JSON:\n") + "REQUEST_JSON:\n".Length))
  if ($payload.rows[0].text -ceq '合成問い合わせ21') {
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    while (-not [IO.File]::Exists((Join-Path $HomePath 'resume-ready'))) {
      if (Test-AgentCancellation $CancelPath) { Start-Sleep -Milliseconds 500; throw 'CANCELLED: synthetic before send' }
      if ([DateTime]::UtcNow -gt $deadline) { throw 'TEST_TIMEOUT' }
      Start-Sleep -Milliseconds 100
    }
  }
  Reserve-AgentCopilotAttempt $HomePath $RequestId
  foreach ($row in $payload.rows) { [IO.File]::AppendAllText((Join-Path $HomePath 'mock-sends.txt'), $row.row_id + [Environment]::NewLine) }
  Start-Sleep -Milliseconds 150
  return ConvertTo-Json -Depth 10 -Compress @{schema_version=1;request_id=$RequestId;results=@($payload.rows | ForEach-Object {
    @{row_id=$_.row_id;category='支払';reason='合成応答 <script> を文字として表示';status=$(if ($_.text -match '問い合わせ2[123]$') {'needs_review'} else {'success'})}
  })}
}
`;
  const source = fs.readFileSync(path.join(repo, 'App.ps1'), 'utf8');
  const marker = "if ($Mode -ne 'Library') {";
  assert.equal(source.split(marker).length, 2);
  fs.writeFileSync(path.join(app, 'App.ps1'), source.replace(marker, () => fixture + '\r\n' + marker));
  fs.copyFileSync(path.join(repo, 'index.html'), path.join(app, 'index.html'));
  const ps = path.join(process.env.SystemRoot, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe');
  // Match the native CMD launcher, which isolates Windows PowerShell's module path.
  const child = spawn(ps, ['-NoProfile','-ExecutionPolicy','Bypass','-STA','-File',path.join(app,'App.ps1'),'-Mode','Serve','-HomePath',home,'-NoBrowser','-OfflineTest'], { windowsHide: true, env: { ...process.env, PSModulePath: path.join(path.dirname(ps), 'Modules') } });
  let stderr = ''; child.stderr.on('data', chunk => { stderr += chunk; });
  let browser; let runtime; let checks = 0; let page;
  const runtimePath = path.join(home, 'data', 'server.json');
  async function until(fn, label, timeout = 30000) {
    const end = Date.now() + timeout;
    while (Date.now() < end) { if (await fn()) return; await wait(150); }
    throw new Error(`Timeout: ${label}. ${stderr}`);
  }
  try {
    await until(() => fs.existsSync(runtimePath), 'server');
    runtime = JSON.parse(fs.readFileSync(runtimePath, 'utf8'));
    assert.equal(runtime.pid, child.pid); assert.equal(runtime.offline_test, true); checks += 2;
    assert(!fs.existsSync(path.join(home, 'data', 'edge-profile')));
    assert.equal(fs.readdirSync(path.join(home, 'data', 'jobs')).length, 0); checks += 2;
    const input = path.join(home, 'synthetic.csv');
    fs.writeFileSync(input, '\uFEFFid,本文,任意列\r\n' + Array.from({ length: 50 }, (_, i) => `"${String(i+1).padStart(5,'0')}","合成問い合わせ${i+1}","=1+1"`).join('\r\n'));
    const original = fs.readFileSync(input);
    const base = `http://127.0.0.1:${runtime.port}`; const headers = { 'X-App-Token': runtime.token };
    const state = async () => { const response = await fetch(`${base}/api/state`, { headers }); const value = await response.json(); assert.equal(value.ok, true, JSON.stringify(value)); return value; };
    browser = await chromium.launch({ channel: 'msedge', headless: true });
    const context = await browser.newContext({ viewport: { width: 1280, height: 960 } });
    await context.route('**/*', route => route.request().url().startsWith(base + '/') ? route.continue() : route.abort());
    page = await context.newPage(); const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(`${base}/#token=${runtime.token}`);
    await page.getByText('アプリに接続済み', { exact: true }).waitFor();
    await page.locator('#csv-paths').fill(input);
    await page.locator('#csv-prepare').click();
    await page.locator('#csv-approval').waitFor({ state: 'visible' });
    assert.equal((await state()).job.status, 'awaiting_approval'); checks++;
    assert(!fs.existsSync(path.join(home, 'mock-sends.txt'))); checks++;
    assert.match(await page.locator('#csv-plan').innerText(), /対象 50行/); checks++;
    // Editing invalidates the visible approval even across the next state poll.
    await page.locator('#csv-instructions').fill('支払とその他に分類。不明は要確認。');
    await wait(1300); assert(await page.locator('#csv-approval').isHidden()); checks++;
    await page.locator('#csv-prepare').click(); await page.locator('#csv-approval').waitFor({ state: 'visible' });
    await page.locator('#csv-approve').click();
    await until(async () => (await state()).job.summary.success === 20, '20 records');
    await page.locator('#csv-stop').click();
    await until(async () => (await state()).job.status === 'cancelled', 'UI cancellation');
    let current = await state();
    assert.equal(current.job.summary.success, 20); assert.equal(current.job.summary.unprocessed, 30); checks += 2;
    fs.writeFileSync(path.join(home, 'resume-ready'), 'continue');
    await page.locator('#csv-resume').waitFor({ state: 'visible' }); await page.locator('#csv-resume').click();
    await until(async () => (await state()).job.status === 'done', 'resume completion');
    await page.locator('#job-status').filter({ hasText: /^完了$/ }).waitFor();
    current = await state();
    assert.equal(current.job.summary.success, 47); assert.equal(current.job.summary.needs_review, 3); checks += 2;
    const sends = fs.readFileSync(path.join(home, 'mock-sends.txt'), 'utf8').trim().split(/\r?\n/);
    assert.equal(sends.length, 50); assert.equal(new Set(sends).size, 50); checks += 2;
    assert.deepEqual(fs.readFileSync(input), original); checks++;
    await page.locator('#csv-filter').selectOption('needs_review');
    await until(async () => (await page.locator('#csv-rows tr').count()) === 3, 'three review rows'); checks++;
    assert.equal(await page.locator('#csv-rows script').count(), 0); checks++;
    await page.locator('#csv-results').scrollIntoViewIfNeeded();
    await page.screenshot({ path: path.join(root, 'results-desktop.png') });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator('.csv-table-wrap').scrollIntoViewIfNeeded();
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)); checks++;
    await page.screenshot({ path: path.join(root, 'results-mobile.png') });
    await page.reload(); await page.getByText('アプリに接続済み', { exact: true }).waitFor();
    assert.equal((await state()).job.job_id, current.job.job_id); checks++;
    await page.getByText('問い合わせ用情報（本文なし）', { exact:true }).click();
    await page.locator('#support-preview').click(); await page.locator('#support-data').waitFor({ state:'visible' });
    const diagnostic = await page.locator('#support-data').innerText();
    assert(!diagnostic.includes('合成問い合わせ') && !diagnostic.includes(input) && !diagnostic.includes(runtime.token)); checks++;
    const downloadEvent = page.waitForEvent('download'); await page.locator('#support-save').click(); const download = await downloadEvent;
    await download.saveAs(path.join(root, 'diagnostic.json'));
    assert.equal(fs.readFileSync(path.join(root, 'diagnostic.json'), 'utf8'), diagnostic); checks++;
    assert.deepEqual(errors, []); checks++;
    fs.writeFileSync(path.join(root, 'verification.json'), JSON.stringify({ status:'PASS', checks, scope:'real PS5 HTTP and child worker; rendered Edge; mock provider', live_sends:0, rows:50, duplicate_sends:0, remaining:'real M365, native picker, other PCs and users' }, null, 2));
    console.log(`PASS: ${checks} rendered CSV checks. Evidence: ${root}`);
  } catch (error) {
    if (page) { console.error(await page.locator('body').innerText()); await page.screenshot({ path:path.join(root,'failure.png'), fullPage:true }); }
    throw error;
  } finally {
    if (browser) await browser.close();
    if (runtime) {
      try { await fetch(`http://127.0.0.1:${runtime.port}/api/restart`, { method:'POST', headers:{'X-App-Token':runtime.token,'Content-Type':'application/json'}, body:'{}' }); } catch {}
    }
    child.kill();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
