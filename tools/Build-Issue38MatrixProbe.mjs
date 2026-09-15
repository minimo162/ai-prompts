// Evaluator-assembled primitive probe, NEVER a Copilot-generated acceptance result.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const base=path.join(root,'catalog/acceptance/issue38');
const target=path.join(base,'probes/matrix-write');
const read=p=>fs.readFileSync(path.join(root,p),'utf8').trimEnd();
const literal=s=>"$'''"+s.replaceAll('\\','\\\\')+"'''";
const launch=read('catalog/actions/excel-launch/t04-open-readonly.robin');
const sheet=read('catalog/evidence/p3-excel-sheet-probe-20260910.robin').split(/\r?\n/)[1];
const range=read('catalog/actions/excel-read/t04-range-a1-c6.robin');
const close=read('catalog/actions/excel-close/t04-no-save.robin');
const write=read('catalog/acceptance/issue38/probes/matrix-write/captured-action.robin');
const save=read('catalog/flows/p3-saveas-collision/excel-saveas-source-20260912.robin').split(/\r?\n/)[2];
const spec=JSON.parse(fs.readFileSync(path.join(base,'spec.json'))).cases[0];
const work=path.join(base,'runs/probe-matrix-A/work.xlsx');
const output=path.join(base,'runs/probe-matrix-A/result.xlsx');
function open(file,instance,ro=true){return launch.replace(/Path: \$'''[^']*'''/,()=>`Path: ${literal(file)}`).replace('ReadOnly: True',`ReadOnly: ${ro?'True':'False'}`).replaceAll('ExcelInstance',instance);}
function select(name,instance){return sheet.replace("$'''Sheet1'''",()=>literal(name)).replaceAll('ExcelInstance',instance);}
function readRange(rect,instance,variable){const m=/^([A-Z]+)(\d+):([A-Z]+)(\d+)$/.exec(rect);return range.replace("StartColumn: $'''A'''",()=>`StartColumn: ${literal(m[1])}`).replace('StartRow: 1',`StartRow: ${m[2]}`).replace("EndColumn: $'''C'''",()=>`EndColumn: ${literal(m[3])}`).replace('EndRow: 6',`EndRow: ${m[4]}`).replaceAll('ExcelInstance',instance).replaceAll('ExcelData',variable);}
const lines=[];
for(let i=0;i<2;i++){
 const item=spec.inputs[i],ins=`Input${i+1}`,data=`Data${i+1}`;
 lines.push(open(path.join(base,item.file),ins),select(item.sheet,ins),readRange(item.range,ins,data),close.replaceAll('ExcelInstance',ins));
}
lines.push(open(work,'Work',false));
for(let i=0;i<2;i++){
 const item=spec.inputs[i],m=/^([A-Z]+)(\d+)$/.exec(item.target_start);
 lines.push(select(item.target_sheet,'Work'),write.replaceAll('ExcelInstance','Work').replaceAll('ExcelData',`Data${i+1}`).replace("Column: $'''C'''",()=>`Column: ${literal(m[1])}`).replace('Row: 4',`Row: ${m[2]}`));
}
lines.push(save.replaceAll('ExcelInstance','Work').replace(/DocumentPath: \$'''[^']*'''/,()=>`DocumentPath: ${literal(output)}`),close.replaceAll('ExcelInstance','Work'));
lines.push(open(output,'Reopened'));
for(let i=0;i<2;i++) lines.push(select(spec.inputs[i].target_sheet,'Reopened'),readRange(i===0?'C4:E5':'B3:C5','Reopened',`Readback${i+1}`));
lines.push(close.replaceAll('ExcelInstance','Reopened'));
const robin=lines.join('\r\n')+'\r\n';
fs.writeFileSync(path.join(target,'assembled-probe-rev2.robin'),robin,{flag:'wx'});
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
fs.writeFileSync(path.join(target,'plan-rev2.json'),JSON.stringify({kind:'EVALUATOR_PRIMITIVE_PROBE_NOT_COPILOT',supersedes:'plan.json; builder replacement-token defect caught before paste, zero runs',flow_name:'RobinIssue38MatrixRuntime20260915A',max_runs:2,timeout_seconds:120,source_sha256:hash(path.join(target,'assembled-probe-rev2.robin')),action_count:lines.length,freeze_sha256:hash(path.join(base,'freeze.json')),captured_write_sha256:hash(path.join(target,'captured-action.robin')),output,work,run2_gate:'Run1 snapshot plus logical comparison saved; move only owned result/work into Run1 evidence, prepare fresh work; no unresolved run or output collision'},null,2),{flag:'wx'});
console.log(`Prepared ${lines.length} action primitive probe. No Copilot or PAD execution.`);
