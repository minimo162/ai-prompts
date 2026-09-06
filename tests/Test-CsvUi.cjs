// Rendered Edge + real PS5 HTTP/child worker. Provider is replaced in an isolated copy.
// Both server and worker retain -OfflineTest; production Copilot HTTP/PAD boundaries refuse I/O.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { spawn, spawnSync } = require('node:child_process');
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
  if ((Get-AgentProperty $payload 'kind' '') -ceq 'csv_plan') {
    Reserve-AgentCopilotAttempt $HomePath $RequestId
    $askedMarker = Join-Path $HomePath 'fixture-asked'
    if (-not [IO.File]::Exists($askedMarker)) {
      [IO.File]::WriteAllText($askedMarker,'asked')
      return ConvertTo-Json -Depth 20 -Compress @{schema_version=1;request_id=$RequestId;observation_id=$payload.observation.observation_id;state='ASK_USER';message='分類候補を確認しました。今回の分類条件を回答してください。';actions=@()}
    }
    $actions = @(); $state = if ($payload.observation.summary.processing_complete) {'DONE'} else {'ACT'}
    if ($state -ceq 'ACT') { $actions = @(@{operation='read_rows';arguments=@{row_ids=@($payload.observation.pending_row_ids)}},@{operation='classify_rows';arguments=@{row_ids=@($payload.observation.pending_row_ids)}},@{operation='write_results';arguments=@{output_id=$payload.approved_output_id}},@{operation='verify_results';arguments=@{output_id=$payload.approved_output_id}}) }
    return ConvertTo-Json -Depth 20 -Compress @{schema_version=1;request_id=$RequestId;observation_id=$payload.observation.observation_id;state=$state;message='合成の型付き計画';actions=$actions}
  }
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
  $reviewPass = $payload.instructions.Contains('追加指示')
  return ConvertTo-Json -Depth 10 -Compress @{schema_version=1;request_id=$RequestId;results=@($payload.rows | ForEach-Object {
    @{row_id=$_.row_id;category=$(if($reviewPass){'その他'}else{'支払'});reason='合成応答 <script> を文字として表示';status=$(if (-not $reviewPass -and $_.text -match '問い合わせ2[123]$') {'needs_review'} else {'success'})}
  })}
}
`;
  const source = fs.readFileSync(path.join(repo, 'App.ps1'), 'utf8');
  const marker = "if ($Mode -ne 'Library') {";
  assert.equal(source.split(marker).length, 2);
  fs.writeFileSync(path.join(app, 'App.ps1'), source.replace(marker, () => fixture + '\r\n' + marker));
  fs.copyFileSync(path.join(repo, 'index.html'), path.join(app, 'index.html'));
  fs.copyFileSync(path.join(repo, '業務エージェント.cmd'), path.join(app, '業務エージェント.cmd'));
  const ps = path.join(process.env.SystemRoot, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe');
  const fixtureRecord = path.join(root,'fixture-release.json');
  const sealed = spawnSync(ps, ['-NoProfile','-ExecutionPolicy','Bypass','-File',path.join(repo,'tools','Seal-AgentRelease.ps1'),'-Directory',app,'-Channel','development','-RecordPath',fixtureRecord], {windowsHide:true,env:{...process.env,PSModulePath:path.join(path.dirname(ps),'Modules')}});
  assert.equal(sealed.status,0,sealed.stderr.toString());
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
    await page.locator('#question-section').waitFor({state:'visible'});
    assert(!fs.existsSync(path.join(home,'mock-sends.txt'))); checks++;
    await page.locator('#answer').fill('表示した分類候補の範囲で進めてください。');
    await page.locator('#send-answer').click();
    await until(async () => (await state()).job.summary.success === 20, '20 records');
    if(process.env.CSV_TEST_FORCE_KILL === '1') {
      const running=await state(),workerPath=path.join(home,'data','jobs',running.job.job_id,'worker.json');
      const killScript=path.join(root,'stop-owned-worker.ps1');
      fs.writeFileSync(killScript,"param($RecordPath,$ExpectedApp); $ErrorActionPreference='Stop'; $w=Get-Content -LiteralPath $RecordPath -Raw -Encoding UTF8 | ConvertFrom-Json; if($w.app_path -cne $ExpectedApp){throw 'WRONG_APP'}; $p=Get-Process -Id $w.pid; if($p.StartTime.ToUniversalTime().ToString('o') -cne $w.started){throw 'STALE_WORKER'}; $p.Kill(); if(-not $p.WaitForExit(5000)){throw 'WORKER_NOT_STOPPED'}");
      const killed=spawnSync(ps,['-NoProfile','-ExecutionPolicy','Bypass','-File',killScript,'-RecordPath',workerPath,'-ExpectedApp',path.join(app,'App.ps1')],{windowsHide:true});
      assert.equal(killed.status,0,killed.stderr.toString());checks++;
      await until(async()=>(await state()).job.status === 'partial','worker-exit reconciliation');
    } else {
      await page.locator('#csv-stop').click();
      await until(async () => (await state()).job.status === 'cancelled', 'UI cancellation');
    }
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
    assert.equal(current.job.clarifications.length,1); checks++;
    assert.deepEqual(fs.readFileSync(input), original); checks++;
    const postArtifact = async artifactId => fetch(`${base}/api/csv/artifact/open`, {method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({job_id:current.job.job_id,artifact_id:artifactId})}).then(r=>r.json());
    assert.match((await postArtifact(randomUUID().replaceAll('-',''))).error,/ARTIFACT_SCOPE/); checks++;
    const artifact = current.job.artifacts.find(a=>a.name==='classified.csv'); const artifactBytes=fs.readFileSync(artifact.path);
    assert.match((await postArtifact(artifact.artifact_id)).error,/ARTIFACT_OPEN_OFFLINE/); checks++;
    fs.appendFileSync(artifact.path,'modified');
    try { assert.match((await postArtifact(artifact.artifact_id)).error,/ARTIFACT_CHANGED/); checks++; } finally { fs.writeFileSync(artifact.path,artifactBytes); }
    const displaced=artifact.path+'.test-held'; fs.renameSync(artifact.path,displaced);
    try { assert.equal((await postArtifact(artifact.artifact_id)).ok,false); checks++; } finally { fs.renameSync(displaced,artifact.path); }
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
    const parentId = current.job.job_id;
    const parentJobPath = path.join(home,'data','jobs',parentId,'job.json'); const parentBytes = fs.readFileSync(parentJobPath);
    await page.getByRole('checkbox', { name:'00021を再検討する', exact:true }).check();
    await page.locator('#csv-review-instructions').fill('その他として再検討してください。');
    await page.locator('#csv-review').click(); await page.locator('#csv-approval').waitFor({ state:'visible' });
    assert.match(await page.locator('#csv-plan').innerText(), /送信対象 1行/); checks++;
    assert.equal(fs.readFileSync(path.join(home,'mock-sends.txt'),'utf8').trim().split(/\r?\n/).length,50); checks++;
    await page.locator('#csv-approve').click();
    await until(async () => { const s = await state(); return s.job.job_id !== parentId && s.job.status === 'done'; }, 'selected review');
    await page.locator('#job-status').filter({ hasText:/^完了$/ }).waitFor();
    const reviewed = await state();
    assert.equal(reviewed.job.summary.success,48); assert.equal(reviewed.job.summary.needs_review,2); checks += 2;
    const afterSends = fs.readFileSync(path.join(home,'mock-sends.txt'),'utf8').trim().split(/\r?\n/);
    const selectedId = current.csv.rows.find(row => row.original_id === '00021').row_id;
    assert.equal(afterSends.length,51); assert.equal(afterSends[50],selectedId); checks += 2;
    assert.deepEqual(fs.readFileSync(parentJobPath),parentBytes); checks++;
    await page.locator('#csv-filter').selectOption('all');
    assert.match(await page.locator('#csv-rows').innerText(), /前回: 支払\s*今回: その他/); checks++;
    await page.locator('#job-history').selectOption(parentId);
    await until(async () => (await page.locator('#csv-summary').innerText()).includes('成功 47'), 'parent history');
    assert.equal((await state()).job.job_id, reviewed.job.job_id); checks++;
    const historyResponse = await fetch(`${base}/api/state?job_id=${parentId}`, {headers}).then(r=>r.json());
    assert.equal(historyResponse.job.job_id,parentId); assert.equal(historyResponse.active_job.job_id,reviewed.job.job_id); checks += 2;
    assert.equal(historyResponse.job.artifacts[0].artifact_id,current.job.artifacts[0].artifact_id); checks++;
    await page.locator('#job-history').selectOption('');
    await until(async () => (await page.locator('#csv-summary').innerText()).includes('成功 48'), 'current history'); checks++;
    await page.getByText('問い合わせ用情報（本文なし）', { exact:true }).click();
    await page.locator('#support-preview').click(); await page.locator('#support-data').waitFor({ state:'visible' });
    const diagnostic = await page.locator('#support-data').innerText();
    assert(!diagnostic.includes('合成問い合わせ') && !diagnostic.includes(input) && !diagnostic.includes(runtime.token)); checks++;
    const downloadEvent = page.waitForEvent('download'); await page.locator('#support-save').click(); const download = await downloadEvent;
    await download.saveAs(path.join(root, 'diagnostic.json'));
    assert.equal(fs.readFileSync(path.join(root, 'diagnostic.json'), 'utf8'), diagnostic); checks++;
    // Exercise real release selection in a private cache after all business workers have ended.
    const releaseB = JSON.parse(fs.readFileSync(fixtureRecord,'utf8')).release;
    const prior = path.join(root,'previous'); fs.mkdirSync(prior);
    for (const name of ['App.ps1','index.html','業務エージェント.cmd']) fs.copyFileSync(path.join(app,name),path.join(prior,name));
    fs.appendFileSync(path.join(prior,'App.ps1'),'\r\n# Synthetic previous candidate\r\n');
    const priorRecord=path.join(root,'previous-release.json');
    const resealed=spawnSync(ps,['-NoProfile','-ExecutionPolicy','Bypass','-File',path.join(repo,'tools','Seal-AgentRelease.ps1'),'-Directory',prior,'-Channel','development','-RecordPath',priorRecord],{windowsHide:true,env:{...process.env,PSModulePath:path.join(path.dirname(ps),'Modules')}});
    assert.equal(resealed.status,0,resealed.stderr.toString());
    const releaseA=JSON.parse(fs.readFileSync(priorRecord,'utf8')).release;
    for(const [directory,release] of [[app,releaseB],[prior,releaseA]]) {
      const cache=path.join(home,'app',release.release);fs.mkdirSync(cache,{recursive:true});
      for(const name of ['App.ps1','index.html','業務エージェント.cmd']) fs.copyFileSync(path.join(directory,name),path.join(cache,name));
    }
    const pointerPath=path.join(home,'app','current.json');fs.writeFileSync(pointerPath,JSON.stringify({version:releaseB.version,release:releaseB.release,app_sha256:releaseB.hashes['App.ps1']}));
    await page.getByText('配布版・旧版への復帰',{exact:true}).click();
    await page.locator('#release-list').click();await page.locator('#rollback-panel').waitFor({state:'visible'});
    await page.locator('#rollback-target').selectOption(releaseA.release);await page.locator('#rollback-select').click();
    assert.match(await page.locator('#rollback-confirm-text').innerText(),new RegExp(releaseA.release_id)); checks++;
    await page.locator('#rollback-confirm').click();
    await until(()=>JSON.parse(fs.readFileSync(pointerPath,'utf8')).rollback_hold === true,'rollback pin');
    assert.equal(JSON.parse(fs.readFileSync(pointerPath,'utf8')).release,releaseA.release); checks++;
    await page.locator('#csv-paths').fill(input);
    await page.locator('#csv-prepare').click();await until(async()=>/RESTART_REQUIRED/.test(await page.locator('#action-message').innerText()),'new work requires selected runtime'); checks++;
    assert.deepEqual(fs.readFileSync(input),original);assert.deepEqual(fs.readFileSync(parentJobPath),parentBytes);checks+=2;
    await page.locator('#release-list').click();await page.locator('#rollback-unpin').waitFor({state:'visible'});await page.locator('#rollback-unpin').click();
    await until(()=>JSON.parse(fs.readFileSync(pointerPath,'utf8')).rollback_hold === false,'explicit unpin'); checks++;
    await page.locator('#storage-show').click();await until(async()=>/空き容量: \d+ MiB/.test(await page.locator('#storage-info').innerText()),'storage policy and measured capacity');checks++;
    assert.deepEqual(errors, []); checks++;
    fs.writeFileSync(path.join(root, 'verification.json'), JSON.stringify({ status:'PASS', checks, scope:'real PS5 HTTP and child worker; rendered Edge; mock provider', interruption:process.env.CSV_TEST_FORCE_KILL==='1'?'owned_worker_kill':'ui_stop', live_sends:0, rows:50, duplicate_sends:0, explicitly_reprocessed_review_rows:1, remaining:'real M365, native picker, other PCs and users' }, null, 2));
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
