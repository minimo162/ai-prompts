// Real Edge/PS5/HTTP; seeded completed job and OfflineTest prohibit provider/PAD/app launch.
const fs=require('node:fs'),path=require('node:path'),a=require('node:assert/strict'),{spawn,spawnSync}=require('node:child_process'),{randomUUID}=require('node:crypto');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');const wait=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
const repo=path.resolve(__dirname,'..'),root=path.join(repo,'.work','general-artifact-ui-'+randomUUID().replaceAll('-','')),app=path.join(root,'app'),home=path.join(root,'home');fs.mkdirSync(app,{recursive:true});for(const n of ['App.ps1','index.html','業務エージェント.cmd'])fs.copyFileSync(path.join(repo,n),path.join(app,n));
const ps=path.join(process.env.SystemRoot,'System32/WindowsPowerShell/v1.0/powershell.exe'),env={...process.env,PSModulePath:path.join(path.dirname(ps),'Modules')},seed=path.join(root,'seed.ps1');
fs.writeFileSync(seed,`param($SeedApp,$SeedHome,$SeedOutput)
$ErrorActionPreference='Stop'
. $SeedApp -Mode Library -HomePath $SeedHome -OfflineTest
$null=Initialize-AgentHome $SeedHome
$id=[guid]::NewGuid().ToString('N');$dir=Get-AgentJobDirectory $SeedHome $id;$run=Join-Path $dir ('runs\\'+[guid]::NewGuid().ToString('N'));[void][IO.Directory]::CreateDirectory((Join-Path $run 'artifacts'))
$file=Join-Path $run 'artifacts\\ready.txt';[IO.File]::WriteAllText($file,'preview text')
$observed=Get-AgentObservedArtifacts ([pscustomobject]@{status='success';artifacts=@($file)}) $run
$job=[pscustomobject]@{job_id=$id;status='done';goal='fixture';target=$SeedHome;question='';final_answer='ready';error='';history=@();observed_artifacts=$observed;artifacts=@(Get-AgentArtifactView $observed)}
Save-AgentJob $dir $job;Write-AgentJson (Join-Path $SeedHome 'data\\latest.json') @{job_id=$id}
Write-AgentJson $SeedOutput @{job_id=$id;artifact_id=$job.artifacts[0].artifact_id;path=$file}
`);
const seeded=spawnSync(ps,['-NoProfile','-ExecutionPolicy','Bypass','-File',seed,'-SeedApp',path.join(app,'App.ps1'),'-SeedHome',home,'-SeedOutput',path.join(root,'seed.json')],{env,encoding:'utf8',windowsHide:true});a.equal(seeded.status,0,seeded.stderr);const fixture=JSON.parse(fs.readFileSync(path.join(root,'seed.json'),'utf8'));
const server=spawn(ps,['-NoProfile','-ExecutionPolicy','Bypass','-STA','-File',path.join(app,'App.ps1'),'-Mode','Serve','-HomePath',home,'-OfflineTest','-NoBrowser'],{env,windowsHide:true});let browser,runtime;let checks=0;
try{
for(let i=0;i<200;i++){try{runtime=JSON.parse(fs.readFileSync(path.join(home,'data/server.json'),'utf8'));break}catch{}await wait(100)}a(runtime?.offline_test);const base=`http://127.0.0.1:${runtime.port}`;
browser=await chromium.launch({channel:'msedge',headless:true});const page=await browser.newPage({viewport:{width:1280,height:960}});const requests=[];page.on('request',r=>{if(r.url().endsWith('/api/artifact/open'))requests.push(r.postDataJSON())});await page.goto(base+'/#token='+runtime.token);await page.getByText('アプリに接続済み',{exact:true}).waitFor();await page.locator('#artifacts button').waitFor();a.equal(await page.locator('#artifacts button').count(),1);checks++;
await page.locator('#artifacts button').click();await page.waitForFunction(()=>document.querySelector('#action-message').textContent.includes('ARTIFACT_OPEN_OFFLINE'));a.deepEqual(requests[0],{job_id:fixture.job_id,artifact_id:fixture.artifact_id});checks++;
await page.reload();await page.locator('#artifacts button').waitFor();await page.locator('#artifacts button').click();await page.waitForFunction(()=>document.querySelector('#action-message').textContent.includes('ARTIFACT_OPEN_OFFLINE'));a.deepEqual(requests[1],requests[0]);checks++;
fs.writeFileSync(fixture.path,'tampered');await page.locator('#artifacts button').click();await page.waitForFunction(()=>document.querySelector('#action-message').textContent.includes('ARTIFACT_CHANGED'));checks++;
await page.screenshot({path:path.join(root,'changed-refused.png'),fullPage:true});a(!fs.existsSync(path.join(home,'data/edge-profile')));checks++;
console.log('PASS: '+checks+' general artifact UI checks; no associated app/provider/PAD launched. Evidence: '+root);
}finally{if(browser)await browser.close();if(runtime)try{await fetch(`http://127.0.0.1:${runtime.port}/api/restart`,{method:'POST',headers:{'X-App-Token':runtime.token,'Content-Type':'application/json'},body:'{}'})}catch{}server.kill()}
})().catch(e=>{console.error(e);process.exitCode=1});
