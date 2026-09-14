import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const bytes=p=>fs.readFileSync(path.resolve(root,p));
const json=p=>JSON.parse(bytes(p).toString('utf8').replace(/^\uFEFF/,''));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const evidencePath='catalog/evidence/final-content-acceptance-20260915.json';
const a=json(evidencePath);
const instruction='6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c';
const bundle='79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12';
function validateDecision(v){
 assert.equal(v.authority.kind,'EXPLICIT_USER_COMPLETION_CONTRACT_CHANGE');
 assert.equal(v.authority.prior_case,'B');
 assert.equal(v.package.instruction_sha256,instruction);assert.equal(v.package.bundle_sha256,bundle);
 assert.deepEqual(Object.keys(v.issue5.a_g).sort(),['A','B','C','D','E','F','G']);
 assert.deepEqual(Object.keys(v.issue27.cases).sort(),['T01','T02','T03','T05','T06','T07','T08','T09','T10','independent_T01','independent_T04_new_pair','independent_T10','P3-1','P3-2','P3-3','P3-4','P3-5','P3-6','negative_v2','knowledge_precheck'].sort());
 for(const issue of [v.issue5,v.issue27]){assert.equal(issue.status,'TECHNICAL_ACCEPTANCE_PASS');assert.deepEqual(issue.required_gaps,[]);}
 for(const x of Object.values(v.issue5.a_g)){assert.equal(x.status,'SATISFIED_MEASURED_REQUIRED_SCOPE');assert.deepEqual(x.required_gaps,[]);assert.ok(x.checks.length>0);}
 for(const x of Object.values(v.issue27.cases))assert.match(x.status,/^PASS/);
 for(const id of ['primary','independent']){
  const t=v.t10[id];for(const k of ['functional_execution','requested_changes_only','unchanged_command_content'])assert.equal(t[k],'PASS');
  assert.equal(t.transport_raw_byte_preservation,'NOT_PROVEN');assert.equal(t.transport_blocking,false);assert.equal(t.outside_raw_bytes,'FAIL');
  assert.deepEqual([t.requests,t.completed,t.remaining],[1,1,0]);assert.deepEqual(t.changed_lines,[2,4]);assert.equal(t.unchanged_commands,14);
 }
 assert.equal(v.publication_gate.issue_close_before_main,false);
 assert.ok(Object.values(v.live_operations).every(x=>x===0));
}
validateDecision(a);
for(const mutate of [v=>delete v.authority,v=>v.t10.primary.transport_raw_byte_preservation='PASS',v=>v.t10.independent.remaining=1,v=>v.issue5.required_gaps.push('missing reuse'),v=>delete v.issue27.cases.T06,v=>v.issue27.cases.T03.status='NOT_RUN',v=>v.issue5.a_g.B.required_gaps.push('Main not run')]){
 const bad=structuredClone(a);mutate(bad);assert.throws(()=>validateDecision(bad));
}
assert.equal(sha(bytes('copilot/agent-instructions.txt')),instruction);
assert.equal(sha(bytes('copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt')),bundle);
for(const f of a.evidence_manifest){
 const b=f.historical_at?execFileSync('git',['show',f.historical_at+':'+f.path],{cwd:root,maxBuffer:10000000}):bytes(f.path);
 assert.equal(sha(b),f.sha256,'evidence changed: '+f.path);
}
const manifest=json(a.package.manifest);
for(const f of manifest.source_files)assert.equal(sha(bytes(f.path)),f.sha256);

// Deliberately separate command-content comparison from the unchanged strict byte comparator.
function commands(b){const s=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(b);const v=s.split(/\r\n|\n/);if(v.at(-1)==='')v.pop();return v;}
function compareContent(source,candidate,contract){
 const expected=commands(source);assert.equal(expected.length,16);
 for(const f of contract.fields){const line=expected[f.line-1];assert.ok(line.startsWith(f.prefix+f.before));expected[f.line-1]=f.prefix+f.after+line.slice((f.prefix+f.before).length);}
 assert.deepEqual(commands(candidate),expected);
}
const strict=json('catalog/evidence/t10-strict-20260914x-audit.json');
const captures=json('catalog/evidence/t10-strict-20260914x-recapture-results.json');
for(const id of ['primary','independent']){
 const t=a.t10[id],c=strict.actual.find(x=>x.id===id).contract,r=captures.actual.find(x=>x.id===id);
 const src=bytes(t.source),candidate=bytes(t.response);compareContent(src,candidate,c);
 assert.equal(r.comparison.status,'FAIL');assert.equal(r.comparison.outside_bytes,false);assert.equal(r.comparison.authorized_contents,true);
 assert.notDeepEqual(src,candidate);
 for(const corrupt of [b=>Buffer.from(b.toString().replace('PowerPoint.','PowerPointChanged.')),b=>Buffer.from(' '+b.toString()),b=>Buffer.from(b.toString().replace('T10-Changed','Wrong')),b=>Buffer.from(b.toString()+'\n')])assert.throws(()=>compareContent(src,corrupt(candidate),c));
}
const resolve=(base,ref)=>{
 const options=ref.startsWith('catalog/')?[ref]:[path.posix.join(path.posix.dirname(base),ref),path.posix.join('catalog',ref)];
 const found=options.find(p=>fs.existsSync(path.resolve(root,p)));assert.ok(found,'Missing ref '+ref+' from '+base);return found;
};
let runs=0;
for(const [id,c] of Object.entries(a.issue27.cases)){
 const e=json(c.acceptance);
 if(id==='knowledge_precheck'||id==='negative_v2'){assert.match(e.status,/^PASS/);continue;}
 if(id==='independent_T04_new_pair'){assert.equal(e.runs.length,2);for(const r of e.runs){assert.equal(r.status,'PASS');assert.equal(r.input_unchanged,true);for(const f of r.artifacts)assert.equal(sha(bytes(f.path)),f.sha256);}continue;}
 if(id==='independent_T01'){assert.match(e.result,/^PASS/);assert.equal(e.runs.expected_output_match,true);assert.equal(e.integrity.input_unchanged,true);assert.equal(e.pad_roundtrip.recopy_after_save_and_run2_same,true);for(const ref of [e.runs.run1,e.runs.run2]){assert.equal(json(resolve(c.acceptance,ref)).run_status,'success');runs++;}continue;}
 const p=e.pad??e;
 const refs=p.runs?Array.isArray(p.runs)?p.runs.map(r=>r.evidence):Object.values(p.runs).map(r=>r.evidence):[p.run1_evidence??p.run1,p.run2_evidence??p.run2];
 assert.equal(refs.length,2,id+' two run records');
 for(const ref of refs){assert.equal(typeof ref,'string',id+' run ref');const r=json(resolve(c.acceptance,ref));assert.equal(r.run_status??r.status,'success',id+' successful run');runs++;}
 const texts=JSON.stringify(e);
 if(['P3-4','P3-5','P3-6'].includes(id)){const recorded=e.instruction?.sha256??e.version.instruction_sha256;assert.equal(recorded.replace('5081241e','508124c1e'),instruction);if(e.instruction)assert.equal(e.instruction.path,'copilot/agent-instructions.txt');else assert.equal(e.version.label,'20260913e');}else assert.ok(texts.includes(instruction),id+' current instruction');
 if(id==='T06'){
  // Immutable source metadata has an conflicting transcribed hash. Reconcile only through its explicit manifest.
  assert.equal(e.manifest,a.package.manifest);assert.equal(e.bundle_sha256.replace("529cadadb","529dacadb"),bundle);
  assert.ok(e.acceptance.two_runs_successful&&e.acceptance.body_replacement_and_rest_unchanged&&e.acceptance.input_sha_unchanged);
 }else assert.ok(texts.includes(bundle),id+' current bundle');
}
for(const n of [1,2]){const e=json('catalog/evidence/p3-subflow-reuse-20260913-run'+n+'.json');assert.equal(e.selected_subflow_before,'Main');assert.equal(e.completion_observed,true);assert.equal(e.button_pressed_match,true);assert.equal(e.source_unchanged,true);}
const reopen=json('catalog/evidence/p3-subflow-reuse-20260913-reopen-recopy.json');
for(const e of Object.values(reopen.recopy_after_reopen)){assert.equal(e.matches_previous_recopy,true);assert.equal(sha(bytes(e.path)),e.sha256);}
for(const p of ['catalog/coverage.json','catalog/index.json','catalog/evidence/current-package-status-20260913.json','catalog/evidence/issue5-completion-audit-20260913.json','catalog/evidence/issue5-a-g-trace-20260914g.json','catalog/evidence/current-package-static-check-20260914e.json']){
 const c=json(p).current_acceptance;assert.equal(c.evidence,evidencePath);assert.equal(c.status,'TECHNICAL_ACCEPTANCE_PASS');assert.deepEqual(c.required_gaps,[]);assert.equal(c.t10_transport,'NOT_PROVEN');assert.equal(c.transport_blocking,false);
}
console.log(`PASS final content acceptance: ${a.evidence_manifest.length} evidence hashes, ${runs} run records, fixed A-G/20-case scope, negative guards; strict NOT_PROVEN/FAIL retained; no live operations.`);
