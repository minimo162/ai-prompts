param([string]$AppSourcePath = '')
$ErrorActionPreference = 'Stop'
if (-not $AppSourcePath) { $AppSourcePath = Join-Path $PSScriptRoot '..\App.ps1' }
. ([IO.Path]::GetFullPath($AppSourcePath)) -Mode Library
$script:Checks=0; $script:Sent=@(); $script:ChildPrompts=@(); $script:ReviewPhase=$false
function Assert-Case($Condition,[string]$Name) { if (-not $Condition) { throw ('FAIL: '+$Name) }; $script:Checks++ }
function Assert-Rejected([scriptblock]$Action,[string]$Prefix) { $errorText=''; try { & $Action | Out-Null } catch { $errorText=$_.Exception.Message }; Assert-Case ($errorText -like ($Prefix+':*')) $errorText }
function Start-AgentProcess { param($AppPath,$HomePath,$Mode,$JobId,$ExecutionId); return Get-Process -Id $PID }
function Test-AgentWorkerAlive { param($Directory); return $false }
function Invoke-AgentCopilot {
    param($Prompt,$RequestId,$JobId,$Settings,$HomePath,$CancelPath,$TimeoutSeconds)
    Reserve-AgentCopilotAttempt $HomePath $RequestId
    if ($script:ReviewPhase) { $script:ChildPrompts += $Prompt }
    $payload=ConvertFrom-Json ($Prompt.Substring($Prompt.IndexOf("REQUEST_JSON:`n")+"REQUEST_JSON:`n".Length))
    if ((Get-AgentProperty $payload 'kind' '') -ceq 'csv_plan') {
        $state=if ($payload.observation.summary.processing_complete) {'DONE'} else {'ACT'}; $actions=@()
        if ($state -ceq 'ACT') { $actions=@(@{operation='read_rows';arguments=@{row_ids=@($payload.observation.pending_row_ids)}},@{operation='classify_rows';arguments=@{row_ids=@($payload.observation.pending_row_ids)}},@{operation='write_results';arguments=@{output_id=$payload.approved_output_id}},@{operation='verify_results';arguments=@{output_id=$payload.approved_output_id}}) }
        return ConvertTo-Json -Depth 20 -Compress @{schema_version=1;request_id=$RequestId;observation_id=$payload.observation.observation_id;state=$state;message='合成計画';actions=$actions}
    }
    $script:Sent+=@($payload.rows | ForEach-Object row_id)
    return ConvertTo-Json -Depth 20 -Compress @{schema_version=1;request_id=$RequestId;results=@($payload.rows | ForEach-Object { @{row_id=$_.row_id;category=$(if($script:ReviewPhase){'その他'}else{'支払'});reason=$(if($script:ReviewPhase){'追加指示を反映'}else{'PRIVATE_OTHER_ROW'});status=$(if(-not $script:ReviewPhase -and $_.text -like '曖昧*'){'needs_review'}else{'success'})} })}
}
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\csv-review-'+[guid]::NewGuid().ToString('N')))); $null=Initialize-AgentHome $root
$path=Join-Path $root 'input.csv'; [IO.File]::WriteAllText($path,"id,本文`r`n001,明確1`r`n002,曖昧2`r`n003,明確3`r`n004,曖昧4`r`n",$script:AgentEncoding)
$parent=New-AgentCsvJob $root @($path) id 本文 utf-8 @('支払','その他') '分類' ([guid]::NewGuid().ToString('N'))
$queued=Start-AgentCsvJob $root $parent.job_id $parent.plan.plan_id $parent.plan_hash
$parent=Invoke-AgentCsvRun $root $parent.job_id $queued.execution_id
Assert-Case ($parent.status -ceq 'done' -and $parent.summary.needs_review -eq 2) 'Parent completed with two review rows'
$parentPath=Join-Path (Get-AgentJobDirectory $root $parent.job_id) 'job.json'; $parentHash=Get-AgentHash $parentPath
$priorArtifacts=@($parent.artifacts | ForEach-Object {[pscustomobject]@{path=$_.path;hash=$_.sha256}})
$selected=@($parent.results | Where-Object status -CEQ 'needs_review')[0].row_id
$settled=@($parent.results | Where-Object status -CEQ 'success')[0].row_id
Assert-Rejected { New-AgentCsvReviewJob $root $parent.job_id @($settled) '追加確認' ([guid]::NewGuid().ToString('N')) } CSV_REVIEW_SCOPE
Assert-Rejected { New-AgentCsvReviewJob $root $parent.job_id @($selected,$selected) '追加確認' ([guid]::NewGuid().ToString('N')) } CSV_REVIEW_SCOPE
$key=[guid]::NewGuid().ToString('N'); $child=New-AgentCsvReviewJob $root $parent.job_id @($selected) '追加確認：その他として再検討' $key
Assert-Case ($child.status -ceq 'awaiting_approval' -and $child.plan.row_ids.Count -eq 1 -and $child.summary.total -eq 4 -and $child.summary.unprocessed -eq 1 -and $child.summary.needs_review -eq 1) 'Only selected review row resets, all other results retained'
Assert-Case ($script:Sent.Count -eq 4) 'Review preparation sends nothing'
Assert-Case ((New-AgentCsvReviewJob $root $parent.job_id @($selected) '追加確認：その他として再検討' $key).job_id -ceq $child.job_id) 'Review idempotency key returns same child'
Assert-Rejected { New-AgentCsvReviewJob $root $parent.job_id @($selected) 'changed' $key } REQUEST_KEY_REUSED
Assert-Case ((Get-AgentCsvView $root $child).previous_results[0].status -ceq 'needs_review') 'Previous result available for comparison'
$script:ReviewPhase=$true; $queued=Start-AgentCsvJob $root $child.job_id $child.plan.plan_id $child.plan_hash
$child=Invoke-AgentCsvRun $root $child.job_id $queued.execution_id
Assert-Case ($child.status -ceq 'done' -and $child.summary.success -eq 3 -and $child.summary.needs_review -eq 1) 'Selected review becomes success; unrelated review remains'
Assert-Case ($script:Sent.Count -eq 5 -and $script:Sent[-1] -ceq $selected) 'Only one additional semantic row sent'
Assert-Case (-not ($script:ChildPrompts -join '').Contains('PRIVATE_OTHER_ROW')) 'No unrelated prior business reasons in child planning or classification prompt'
foreach ($old in $parent.results) { if ($old.row_id -cne $selected) { $new=@($child.results | Where-Object row_id -CEQ $old.row_id)[0]; Assert-Case ((ConvertTo-Json $old -Compress) -ceq (ConvertTo-Json $new -Compress)) 'Unrelated result unchanged' } }
Assert-Case ((Get-AgentHash $parentPath) -ceq $parentHash) 'Parent job remains byte-identical'
foreach ($artifact in $priorArtifacts) { Assert-Case ((Get-AgentHash $artifact.path) -ceq $artifact.hash) 'Prior artifact remains byte-identical' }
$basePath=Join-Path (Get-AgentJobDirectory $root $child.job_id) 'csv-base-results.json'; [IO.File]::AppendAllText($basePath,' ')
Assert-Rejected { Get-AgentCsvReconciledResults $root $child (Read-AgentCsvJobManifest $root $child) } CSV_BASE_CHANGED
Write-Output "PASS: $script:Checks CSV review checks; live sends 0. Evidence: $root"
