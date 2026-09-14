import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {compareT10,sha256} from '../tools/Compare-T10Bytes.mjs';
const root=new URL('../',import.meta.url);
const bytes=p=>readFile(new URL(p,root));
const json=async p=>JSON.parse((await bytes(p)).toString('utf8'));
const prior=await json('catalog/evidence/t10-strict-20260914x-audit.json');
const result=await json('catalog/evidence/t10-strict-20260914x-recapture-results.json');
assert.equal(result.scope_id,prior.id);
assert.deepEqual(result.actual.map(x=>x.id),['primary','independent']);
assert.deepEqual(result.browser_prerequisite,{requests:1,completed:1,status:'AVAILABLE',method:'cua.getState()',target_tabs_initially_open:false});
assert.equal(result.pad_runs+result.copilot_sends+result.clipboard_changes,0);
function validateRecord(a){
 assert.equal(a.requests,1);assert.equal(a.completed,1);assert.equal(a.remaining,0);
 assert.equal(a.strict,'NOT_PROVEN');assert.equal(a.comparison.status,'FAIL');
 assert.equal(a.comparison.authorized_contents,true);assert.equal(a.comparison.outside_bytes,false);
}
let checked=0;
for(const actual of result.actual){
 validateRecord(actual);
 const original=prior.actual.find(x=>x.id===actual.id);
 const req=await json(actual.request),capture=await json(actual.capture),saved=await bytes(actual.saved);
 assert.equal(req.scope_id,prior.id);assert.equal(req.original_budget,1);assert.equal(req.this_request,1);assert.equal(req.prior_requests,0);
 assert.equal(req.conversation,original.conversation);assert.equal(capture.url,req.conversation);assert.equal(capture.selector,req.selector);
 assert.equal(req.node_count_observed,1);assert.equal(req.version,'20260913e');
 assert.equal(req.request_sha256,original.request_sha256);assert.equal(sha256(await bytes(original.request)),req.request_sha256);
 assert.equal(req.source_sha256,original.contract.source_sha256);
 const utf16=Buffer.from(capture.utf16le_base64,'base64');
 assert.equal(sha256(utf16),capture.utf16le_sha256);assert.equal(utf16.length,capture.utf16_code_units*2);
 assert.ok(Buffer.from(utf16.toString('utf16le'),'utf8').equals(saved));
 assert.equal(sha256(saved),capture.utf8_sha256);assert.equal(saved.length,capture.utf8_bytes);
 assert.equal(sha256(await bytes(actual.capture)),actual.transport.tool_output_sha256);
 assert.equal(actual.saving.sha256,capture.utf8_sha256);assert.equal(actual.saving.utf16_source_sha256,capture.utf16le_sha256);
 assert.equal(actual.saving.saved_equal_encoded_capture,true);
 assert.deepEqual(compareT10(await bytes(original.contract.source_path),saved,original.contract),actual.comparison);
 assert.equal(saved.filter(b=>b===13).length,0);assert.equal(saved.filter(b=>b===10).length,16);assert.equal(saved.at(-1),10);
 let requestText=(await bytes(original.request)).toString('utf8');
 if(actual.id==='independent'){
  requestText=(await bytes('copilot/agent-instructions.txt')).toString('utf8')+'\r\n\r\n'+requestText;
  assert.equal(sha256(Buffer.from(requestText)),req.identity.sent_body_sha256);
 }
 // Display-only identity check, never used by the strict response comparator.
 assert.equal(sha256(Buffer.from(requestText.replaceAll('\r\n','\n').replaceAll('\n',' '))),req.identity.user_dom_utf8_sha256);
 checked++;
}
for(const field of ['requests','completed','remaining']){const bad=structuredClone(result.actual[0]);bad[field]++;assert.throws(()=>validateRecord(bad));}
const falsePass=structuredClone(result.actual[0]);falsePass.strict='PASS';assert.throws(()=>validateRecord(falsePass));
console.log(JSON.stringify({status:'PASS',live_capture_artifacts_checked:checked,negative_record_checks:4,browser_or_clipboard_calls:0,strict:'NOT_PROVEN_BOTH'}));
