const {spawnSync}=require('node:child_process');
const path=require('node:path');
const result=spawnSync(process.execPath,[path.join(__dirname,'Test-CsvUi.cjs')],{env:{...process.env,CSV_TEST_FORCE_KILL:'1'},stdio:'inherit',windowsHide:true});
if(result.error)throw result.error;
process.exitCode=result.status===null?1:result.status;
