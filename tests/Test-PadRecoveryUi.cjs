// Real PS5 HTTP + rendered Edge. Only the native Main restoration boundary is replaced.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawn,spawnSync}=require('node:child_process');const {randomUUID}=require('node:crypto');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const wait=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const repo=path.resolve(__dirname,'..'),root=path.join(repo,'.work','pad-recovery-ui-'+randomUUID().replaceAll('-',''));
 const app=path.join(root,'app'),home=path.join(root,'home');fs.mkdirSync(app,{recursive:true});
 const jobId=randomUUID().replaceAll('-',''),runId=randomUUID().replaceAll('-','');
 const jobDir=path.join(home,'data','jobs',jobId),runDir=path.join(jobDir,'runs',runId);fs.mkdirSync(runDir,{recursive:true});
 const stub=`
function Restore-AgentPadMain {
 param($HomePath,$JobId,$RunId,$ExpectedBackupHash)
 if(-not $script:AgentOfflineTest){throw 'TEST_OFFLINE_REQUIRED'}
 [IO.File]::AppendAllText((Join-Path $HomePath 'mock-restores.txt'),'one'+[Environment]::NewLine)
 return [pscustomobject]@{status='restored';run_id=$RunId;run_invocations=0;clipboard_status='restore_failed'}
}
`;
 const source=fs.readFileSync(path.join(repo,'App.ps1'),'utf8'),marker="if ($Mode -ne 'Library') {";
 assert.equal(source.split(marker).length,2);fs.writeFileSync(path.join(app,'App.ps1'),source.replace(marker,()=>stub+'\r\n'+marker));
 for(const name of ['index.html','業務エージェント.cmd'])fs.copyFileSync(path.join(repo,name),path.join(app,name));
 const ps=path.join(process.env.SystemRoot,'System32','WindowsPowerShell','v1.0','powershell.exe');
 const env={...process.env,PSModulePath:path.join(path.dirname(ps),'Modules')};
 const seal=spawnSync(ps,['-NoProfile','-ExecutionPolicy','Bypass','-File',path.join(repo,'tools','Seal-AgentRelease.ps1'),'-Directory',app,'-Channel','development'],{env,windowsHide:true});assert.equal(seal.status,0,seal.stderr.toString());
 fs.writeFileSync(path.join(runDir,'pad-backup.json'),JSON.stringify({job_id:jobId,run_id:runId}));
 fs.writeFileSync(path.join(runDir,'pad-recovery-state.json'),JSON.stringify({phase:'saving',execution_reserved:false,restored:false}));
 const job={job_id:jobId,status:'blocked',goal:'合成のPAD復旧検証',target:root,question:'',final_answer:'',error:'編集が中断しました。',artifacts:[],history:[],last_pad_run_id:runId,recovery_required:true,preservation:{main_status:'needs_recovery',clipboard_status:'restore_failed',warnings:['クリップボードを復元できませんでした。']},partial_artifacts:[{path:path.join(runDir,'artifacts','synthetic-long-file-name.txt'),reason:'内容・処理完了は未検証です。',state:'unverified'}]};
 fs.writeFileSync(path.join(jobDir,'job.json'),JSON.stringify(job));fs.writeFileSync(path.join(jobDir,'run.claim'),'preserve claim');fs.writeFileSync(path.join(home,'data','latest.json'),JSON.stringify({job_id:jobId}));
 const server=spawn(ps,['-NoProfile','-ExecutionPolicy','Bypass','-STA','-File',path.join(app,'App.ps1'),'-Mode','Serve','-HomePath',home,'-NoBrowser','-OfflineTest'],{env,windowsHide:true});
 let runtime,browser,page,checks=0,stderr='';server.stderr.on('data',c=>stderr+=c);
 async function until(fn,label){const end=Date.now()+20000;while(Date.now()<end){if(await fn())return;await wait(100)}throw new Error(label+' '+stderr)}
 try{
  const rp=path.join(home,'data','server.json');await until(()=>fs.existsSync(rp),'server');runtime=JSON.parse(fs.readFileSync(rp,'utf8'));assert.equal(runtime.pid,server.pid);checks++;
  const base=`http://127.0.0.1:${runtime.port}`,headers={'X-App-Token':runtime.token};
  browser=await chromium.launch({channel:'msedge',headless:true});page=await browser.newPage({viewport:{width:1280,height:900}});await page.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());
  await page.goto(base+'/#token='+runtime.token);await page.getByText('アプリに接続済み',{exact:true}).waitFor();
  assert.match(await page.locator('#preservation-warning').innerText(),/クリップボード/);assert.match(await page.locator('#partial-artifacts').innerText(),/未確認の途中ファイル/);checks+=2;
  const wrong=await fetch(base+'/api/pad/recover',{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({job_id:jobId,run_id:randomUUID().replaceAll('-',''),backup_sha256:'0'.repeat(64)})}).then(r=>r.json());assert.match(wrong.error,/PAD_RECOVERY_SCOPE/);assert(!fs.existsSync(path.join(home,'mock-restores.txt')));checks+=2;
  await page.locator('#pad-recover').click();await until(()=>JSON.parse(fs.readFileSync(path.join(jobDir,'job.json'),'utf8')).recovery_required===false,'recovery state');
  await page.locator('#pad-recover').waitFor({state:'hidden'});assert.match(await page.locator('#preservation-warning').innerText(),/Mainは復元しましたが/);checks++;
  assert.equal(fs.readFileSync(path.join(home,'mock-restores.txt'),'utf8').trim(),'one');assert.equal(fs.readFileSync(path.join(jobDir,'run.claim'),'utf8'),'preserve claim');checks+=2;
  await page.setViewportSize({width:390,height:844});await page.locator('#preservation-section').scrollIntoViewIfNeeded();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks++;
  await page.screenshot({path:path.join(root,'preservation-mobile.png')});
  console.log(`PASS: ${checks} PAD recovery rendered checks; native restoration replaced, native Run 0. Evidence: ${root}`);
 }finally{if(browser)await browser.close();if(runtime){try{await fetch(`http://127.0.0.1:${runtime.port}/api/restart`,{method:'POST',headers:{'X-App-Token':runtime.token,'Content-Type':'application/json'},body:'{}'})}catch{}}server.kill()}
})().catch(e=>{console.error(e);process.exitCode=1});
