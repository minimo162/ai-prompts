// Explicit live test: real sealed App, real Copilot, synthetic CSV only, no PAD operations.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {spawn}=require('node:child_process');const {createHash}=require('node:crypto');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const wait=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const [contextPath,countArg,live,...options]=process.argv.slice(2);assert.equal(live,'--live');
 assert(options.every(v=>v==='--long-text'),'Unknown measurement option');
 const longText=options.includes('--long-text');
 const config=JSON.parse(fs.readFileSync(contextPath,'utf8'));assert.equal(config.synthetic_only,true);assert.equal(config.pad_required,false);
 const count=Number(countArg);assert([1,50,100].includes(count));
 const root=path.dirname(path.resolve(contextPath)),out=path.join(root,`run-${count}-${Date.now()}`);fs.mkdirSync(out);
 const input=path.join(out,'synthetic.csv');
 const topics=[['支払','請求書の振込予定日を確認したいです。'],['決算','月次決算の締め日と仕訳提出期限を確認したいです。'],['システム','経理システムにログインできないため調査をお願いします。'],['その他','会議室の予約方法を教えてください。']];
 const values=[];const expected=[];
 for(let i=1;i<=count;i++){const t=topics[(i-1)%4];const ambiguous=i%5===0;let body=ambiguous?'処理が進みません。何の手続かはまだ確認できていません。':t[1];if(longText)body+='\n'+('補足記録です。同じ状況の確認を待っています。\n'.repeat(80));values.push([String(i).padStart(5,'0'),body,`合成 ${i} "引用", 100%`]);expected.push({id:String(i).padStart(5,'0'),category:ambiguous?null:t[0],needs_review:ambiguous});}
 const quote=s=>'"'+s.replaceAll('"','""')+'"';
 fs.writeFileSync(input,'\uFEFF'+[['id','本文','任意列'],...values].map(r=>r.map(quote).join(',')).join('\r\n')+'\r\n');
 fs.writeFileSync(path.join(out,'expected-draft.json'),JSON.stringify({human_reviewed:false,author:'assistant draft',rows:expected},null,2));
 const sha=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');const inputHash=sha(input);
 assert.equal(sha(config.app),config.release.hashes['App.ps1']);
 const ps=path.join(process.env.SystemRoot,'System32','WindowsPowerShell','v1.0','powershell.exe');
 const server=spawn(ps,['-NoProfile','-ExecutionPolicy','Bypass','-STA','-File',config.app,'-Mode','Serve','-HomePath',config.home,'-NoBrowser'],{windowsHide:true,env:{...process.env,PSModulePath:path.join(path.dirname(ps),'Modules')}});
 let browser,runtime,page,job;let stderr='';server.stderr.on('data',c=>stderr+=c);
 const runtimePath=path.join(config.home,'data','server.json');const start=Date.now();
 const activeStatuses=['queued','planning','running_csv','waiting_user'];
 const record={kind:'live_business_measurement',input_count:count,input_variant:longText?'long_text':'short_text',input_bytes:fs.statSync(input).size,max_body_characters:Math.max(...values.map(r=>r[1].length)),started_utc:new Date().toISOString(),candidate_hashes:config.release.hashes,source_commit:config.source_commit || null,provider:'real M365 Copilot',pad_invocations:0,human_reviewed_ground_truth:false,status:'running'};
 try{
  const deadline=Date.now()+20000;while(Date.now()<deadline){if(fs.existsSync(runtimePath)){try{const value=JSON.parse(fs.readFileSync(runtimePath,'utf8'));if(value.pid===server.pid){runtime=value;break}}catch{}}await wait(100)}assert(runtime,stderr||'new server not ready');assert.notEqual(runtime.offline_test,true);
  const base=`http://127.0.0.1:${runtime.port}`,headers={'X-App-Token':runtime.token};const state=()=>fetch(base+'/api/state',{headers}).then(r=>r.json());
  browser=await chromium.launch({channel:'msedge',headless:false});page=await browser.newPage({viewport:{width:1280,height:960}});
  await page.goto(base+'/#token='+runtime.token);await page.getByText('アプリに接続済み',{exact:true}).waitFor();
  await page.locator('#csv-paths').fill(input);await page.locator('#csv-instructions').fill('支払・決算・システム・その他に分類してください。具体的な根拠がない、何の処理か不明な依頼は必ず要確認にし、推測を確定扱いにしないでください。理由を短く記してください。');
  await page.locator('#csv-prepare').click();await page.locator('#csv-approval').waitFor({state:'visible'});
  record.prepared_ms=Date.now()-start;await page.screenshot({path:path.join(out,'approval.png')});
  await page.locator('#csv-approve').click();record.approved_utc=new Date().toISOString();
  const limit=Date.now()+40*60*1000;let last='';
  while(Date.now()<limit){
   const current=await state();assert.equal(current.ok,true,JSON.stringify(current));job=current.job;
   if(job){const key=job.status+':'+JSON.stringify(job.summary);if(key!==last){last=key;console.log(new Date().toISOString(),job.status,JSON.stringify(job.summary));}
    if(['done','partial','blocked','failed','unknown','cancelled'].includes(job.status))break;
   }
   await wait(1000);
  }
  assert(job);record.job_id=job.job_id;record.status=job.status;record.summary=job.summary;record.error=job.error;record.elapsed_ms=Date.now()-start;record.input_preserved=sha(input)===inputHash;
  if(activeStatuses.includes(job.status)){record.observation_timed_out=true;process.exitCode=2;}
  else if(job.status!=='done'){process.exitCode=2;}
  await wait(1200);await page.screenshot({path:path.join(out,'result.png'),fullPage:true});
  record.artifacts=job.artifacts;
  console.log('RESULT',JSON.stringify({status:record.status,elapsed_ms:record.elapsed_ms,error:record.error,evidence:out}));
 }catch(error){record.status='test_error';record.error=error.message;process.exitCode=1;if(page){try{console.error(await page.locator('#action-message').innerText({timeout:2000}));await page.screenshot({path:path.join(out,'failure.png'),fullPage:true});}catch{}}console.error(error.message,stderr);}
 finally{
  record.finished_utc=new Date().toISOString();fs.writeFileSync(path.join(out,'measurement.json'),JSON.stringify(record,null,2));
  if(browser)await browser.close();
  // Unknown state after a harness error may still have an active worker. Leave it inspectable.
  const terminal=job&&['done','partial','blocked','failed','unknown','cancelled'].includes(job.status);
  if(runtime&&terminal){try{await fetch(`http://127.0.0.1:${runtime.port}/api/restart`,{method:'POST',headers:{'X-App-Token':runtime.token,'Content-Type':'application/json'},body:'{}'})}catch{}}
  // Never kill a still-active business worker or erase its claims from a measurement helper.
  if(terminal)server.kill();
  else {server.stdout.destroy();server.stderr.destroy();server.unref();}
 }
})().catch(error=>{console.error(error);process.exitCode=1});
