param([string]$AppSourcePath='')
$ErrorActionPreference='Stop'
if(-not $AppSourcePath){$AppSourcePath=Join-Path $PSScriptRoot '..\App.ps1'}
. ([IO.Path]::GetFullPath($AppSourcePath)) -Mode Library
$script:sends=0;$script:checks=0;$script:lateRows=@()
function Check($Value,$Name){if(-not $Value){throw ('FAIL: '+$Name)};$script:checks++}
function Start-AgentProcess {param($AppPath,$HomePath,$Mode,$JobId,$ExecutionId);return Get-Process -Id $PID}
function Test-AgentWorkerAlive {param($Directory);return $false}
function Invoke-AgentCopilot {
 param($Prompt,$RequestId,$JobId,$Settings,$HomePath,$CancelPath,$TimeoutSeconds)
 $script:sends++;Reserve-AgentCopilotAttempt $HomePath $RequestId
 $payload=ConvertFrom-Json ($Prompt.Substring($Prompt.IndexOf("REQUEST_JSON:`n")+"REQUEST_JSON:`n".Length))
 if((Get-AgentProperty $payload 'kind' '') -ceq 'csv_plan'){
  $ids=@($payload.observation.pending_row_ids|Select-Object -First 2)
  return ConvertTo-Json -Depth 20 -Compress @{schema_version=1;request_id=$RequestId;observation_id=$payload.observation.observation_id;state='ACT';message='first two rows';actions=@(@{operation='read_rows';arguments=@{row_ids=$ids}},@{operation='classify_rows';arguments=@{row_ids=$ids}},@{operation='write_results';arguments=@{output_id=$payload.approved_output_id}},@{operation='verify_results';arguments=@{output_id=$payload.approved_output_id}})}
 }
 $script:lateRows=$payload.rows;throw 'RESPONSE_TIMEOUT: synthetic received-late response'
}
function Read-AgentCopilotCompletedResponse($HomePath,$JobId,$RequestId){return ConvertTo-Json -Depth 10 -Compress @{schema_version=1;request_id=$RequestId;results=@($script:lateRows|ForEach-Object {@{row_id=$_.row_id;category='支払';reason='合成の既存回答';status='success'}})}}
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\late-response-'+[guid]::NewGuid().ToString('N'))));$null=Initialize-AgentHome $root
$inputPath=Join-Path $root 'input.csv';[IO.File]::WriteAllText($inputPath,"id,本文`r`n1,支払1`r`n2,支払2`r`n3,支払3`r`n4,支払4`r`n5,支払5",$script:AgentEncoding)
$job=New-AgentCsvJob $root @($inputPath) id 本文 utf-8 @('支払','その他') '分類' ([guid]::NewGuid().ToString('N'))
$queued=Start-AgentCsvJob $root $job.job_id $job.plan.plan_id $job.plan_hash;$job=Invoke-AgentCsvRun $root $job.job_id $queued.execution_id
Check ($job.status -ceq 'unknown' -and $job.summary.unknown -eq 2 -and $job.summary.unprocessed -eq 3) 'Post-send timeout keeps unknown rows'
$calls=$script:sends;$oldArtifacts=@($job.artifacts)
$resolved=Resolve-AgentCsvLateResponses $root $job.job_id
Check ($resolved.status -ceq 'partial' -and $resolved.summary.success -eq 2 -and $resolved.summary.unknown -eq 0 -and $script:sends -eq $calls) 'Existing late response reconciles without a send'
foreach($artifact in $oldArtifacts){Check ((Get-AgentHash $artifact.path) -ceq $artifact.sha256) 'Historical partial output remains unchanged'}
$parentHash=Get-AgentHash (Join-Path (Get-AgentJobDirectory $root $job.job_id) 'job.json')
$key=[guid]::NewGuid().ToString('N');$child=New-AgentCsvContinuationJob $root $job.job_id $key
Check ($child.status -ceq 'awaiting_approval' -and $child.summary.success -eq 2 -and $child.summary.unprocessed -eq 3 -and $child.plan.row_ids.Count -eq 3) 'New-version continuation carries verified results and only pending rows'
Check ($script:sends -eq $calls -and (Get-AgentHash (Join-Path (Get-AgentJobDirectory $root $job.job_id) 'job.json')) -ceq $parentHash) 'Continuation preparation neither sends nor mutates its parent'
Check ((New-AgentCsvContinuationJob $root $job.job_id $key).job_id -ceq $child.job_id) 'Continuation key is idempotent'
Write-Output "PASS: $script:checks late-response/continuation checks; mocked provider, sends unchanged during recovery. Evidence: $root"
