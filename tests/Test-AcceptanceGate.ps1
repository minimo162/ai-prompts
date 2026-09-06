# Evaluator fixtures are fictitious and never serve as actual acceptance evidence.
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\tools\Test-AgentAcceptance.ps1') -Mode Library
$checks=0
function Check($Value,[string]$Name){if(-not $Value){throw ('FAIL: '+$Name)};$script:checks++}
$candidate=[pscustomobject]@{hashes=[pscustomobject]@{'App.ps1'=('a'*64);'index.html'=('b'*64);'業務エージェント.cmd'=('c'*64)}}
$catalog=Read-AgentJson (Join-Path $PSScriptRoot '..\docs\issues-8-14-acceptance.json');$ids=@($catalog.issues|ForEach-Object {$_.acceptance|ForEach-Object id})
function New-Record([string]$Kind){return [pscustomobject]@{schema_version=1;record_id=[guid]::NewGuid().ToString('N');kind=$Kind;status='PASS';candidate_hashes=$candidate.hashes;attachments_verified=$true;simulated=$false;requirements=$ids;cases=@();host_id=('1'*32);participant_id=('1'*32);corporate=$false;administrator=$false;metrics=[pscustomobject]@{}}}
$records=@()
foreach($kind in @('nonlive','native_pad','live_m365','documentation')){$records+=New-Record $kind}
$records[0].simulated=$true
$records[1].cases=@('native_save_failure','paste_delay','foreground_change','clipboard_preservation')
$records[2].cases=@('authentication_expiry','post_send_timeout','long_response','multiple_turns')
foreach($count in @(1,50,100)){$r=New-Record business_e2e;$r.metrics=[pscustomobject]@{input_count=$count;output_count=$count;duplicate_ids=0;input_preserved=$true;ui_operated=$true};$records+=$r}
$r=New-Record corporate_pc;$r.host_id='2'*32;$r.participant_id='2'*32;$r.corporate=$true;$records+=$r
foreach($index in 1..5){$r=New-Record usability;$r.participant_id=($index.ToString()*32);$r.metrics=[pscustomobject]@{first_use=$true;completed=$true;oral_intervention=$false};$records+=$r}
$r=New-Record quality;$r.metrics=[pscustomobject]@{human_reviewed_ground_truth=$true;clear_accuracy=0.95;review_recall=1.0};$records+=$r
$r=New-Record comparison;$r.metrics=[pscustomobject]@{same_quality_threshold=$true;same_50_rows=$true;human_time_reduction=0.35;direct_copilot_human_seconds=100;fixed_flow_human_seconds=80;agent_human_seconds=52};$records+=$r
$json=ConvertTo-Json -InputObject $records -Depth 20
function Copy-Records {return ,(ConvertFrom-Json $json)}
$pass=Test-AgentAcceptanceEvidence $candidate $records $ids
Check ($pass.status -ceq 'READY_FOR_REVIEW' -and -not $pass.release_approved -and $pass.coverage.Count -eq 51) 'Coherent synthetic evidence reaches review, never release approval'
$onlyMocks=@($records | Where-Object kind -CEQ 'nonlive');$result=Test-AgentAcceptanceEvidence $candidate $onlyMocks $ids
Check ($result.status -ceq 'NOT_READY' -and ($result.blockers -join ' ') -match 'corporate|participants') 'Mock PASS cannot imply live or other-PC acceptance'
$changed=[pscustomobject]@{hashes=[pscustomobject]@{'App.ps1'=('d'*64);'index.html'=('b'*64);'業務エージェント.cmd'=('c'*64)}}
$result=Test-AgentAcceptanceEvidence $changed $records $ids
Check ($result.status -ceq 'NOT_READY' -and $result.accepted_records -eq 0) 'App-only candidate change invalidates every previous record'
foreach($case in @('hash','attachment','simulated','string_false','quality','people','size','comparison','native_case','first_use','duplicate')){
 $test=Copy-Records
 switch($case){
 'hash' {$test[1].candidate_hashes.'index.html'='d'*64}
 'attachment' {$test[1].attachments_verified=$false}
 'simulated' {$test[1].simulated=$true}
 'string_false' {$test[1].simulated='false'}
 'quality' {($test|Where-Object kind -CEQ quality).metrics.clear_accuracy=0.89}
 'people' {$test=@($test|Where-Object {$_.kind -cne 'usability' -or $_.participant_id -cne ('5'*32)})}
 'size' {($test|Where-Object {$_.kind -ceq 'business_e2e' -and $_.metrics.input_count -eq 100}).metrics.output_count=99}
 'comparison' {($test|Where-Object kind -CEQ comparison).metrics.human_time_reduction=0.29}
 'native_case' {$test[1].cases=@('paste_delay')}
 'first_use' {($test|Where-Object kind -CEQ usability)[0].metrics.first_use=$false}
 'duplicate' {$test+=,$test[0]}
 }
 $result=Test-AgentAcceptanceEvidence $candidate $test $ids
 Check ($result.status -ceq 'NOT_READY') ('Reject deficient evidence: '+$case)
}
$result=Test-AgentAcceptanceEvidence $candidate @() $ids
Check ($result.coverage.Count -eq 51 -and @($result.coverage|Where-Object status -CEQ 'UNVERIFIED').Count -eq 51) 'Empty folder leaves all original requirements unverified'
Write-Output "PASS: $checks acceptance evaluator tests; synthetic records only, no release approval."
