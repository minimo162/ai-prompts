# PS5 job/approval/recovery contracts; provider and worker launch replaced, no live services.
[CmdletBinding()]
param([string]$AppSourcePath = '')
$ErrorActionPreference = 'Stop'
if (-not $AppSourcePath) { $AppSourcePath = Join-Path $PSScriptRoot '..\App.ps1' }
. ([IO.Path]::GetFullPath($AppSourcePath)) -Mode Library
$script:Checks = 0; $script:Calls = 0; $script:StopAfter = 4; $script:SentIds = @(); $script:Launches = 0
function Assert-True($Condition, [string]$Name) { if (-not $Condition) { throw ('FAIL: ' + $Name) }; $script:Checks++ }
function Assert-Throws([scriptblock]$Action, [string]$Pattern, [string]$Name) {
    $message = ''; try { & $Action | Out-Null } catch { $message = $_.Exception.Message }
    Assert-True ($message -match $Pattern) ($Name + ' (' + $message + ')')
}
function Start-AgentProcess { param($AppPath,$HomePath,$Mode,$JobId,$ExecutionId); $script:Launches++; return Get-Process -Id $PID }
function Test-AgentWorkerAlive { param($Directory); return $false }
function Invoke-AgentCopilot {
    param($Prompt,$RequestId,$JobId,$Settings,$HomePath,$CancelPath,$TimeoutSeconds)
    $script:Calls++; Reserve-AgentCopilotAttempt $HomePath $RequestId
    $payload = ConvertFrom-Json ($Prompt.Substring($Prompt.IndexOf("REQUEST_JSON:`n") + "REQUEST_JSON:`n".Length))
    $script:SentIds += @($payload.rows | ForEach-Object row_id)
    if ($script:Calls -eq $script:StopAfter) { [IO.File]::WriteAllText($CancelPath, 'stop', $script:AgentEncoding) }
    return ConvertTo-Json -Depth 10 -Compress @{ schema_version = 1; request_id = $RequestId; results = @($payload.rows | ForEach-Object { @{ row_id = $_.row_id; category = '支払'; reason = '合成応答'; status = 'success' } }) }
}
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\csv-lifecycle-' + [guid]::NewGuid().ToString('N'))))
$null = Initialize-AgentHome $root
$path = Join-Path $root 'synthetic.csv'; $csv = "id,本文`r`n" + ((1..50 | ForEach-Object { "$_,支払依頼$_" }) -join "`r`n")
[IO.File]::WriteAllText($path, $csv, $script:AgentEncoding); $originalHash = Get-AgentHash $path
$key = [guid]::NewGuid().ToString('N'); $categories = @('支払','その他')
$job = New-AgentCsvJob $root @($path) id 本文 utf-8 $categories '分類してください。' $key
Assert-True ($job.status -ceq 'awaiting_approval' -and $script:Calls -eq 0 -and $script:Launches -eq 0) 'Preparation has no worker launch or provider calls'
$again = New-AgentCsvJob $root @($path) id 本文 utf-8 $categories '分類してください。' $key
Assert-True ($again.job_id -ceq $job.job_id -and $again.plan_hash -ceq $job.plan_hash) 'Repeated preparation key returns same frozen plan'
Assert-Throws { New-AgentCsvJob $root @($path) id 本文 utf-8 $categories '変更' $key } 'REQUEST_KEY_REUSED' 'Same key cannot change scope'
Assert-Throws { Start-AgentCsvJob $root $key $job.plan.plan_id ('0' * 64) } 'PLAN_CHANGED' 'Wrong plan hash rejects execution'
Assert-True ($script:Launches -eq 0) 'Invalid approval has zero launch side effects'
$queued = Start-AgentCsvJob $root $key $job.plan.plan_id $job.plan_hash
$repeat = Start-AgentCsvJob $root $key $job.plan.plan_id $job.plan_hash
Assert-True ($script:Launches -eq 1 -and $queued.execution_id -ceq $repeat.execution_id) 'Repeated approval queues one execution'
$partial = Invoke-AgentCsvRun $root $key $queued.execution_id
Assert-True ($partial.status -ceq 'cancelled' -and $partial.summary.success -eq 20 -and $partial.summary.unprocessed -eq 30 -and $partial.summary.total -eq 50) 'Stop after 20 verified rows preserves remaining 30'
$initialAttempts = @($partial.batch_ids | Select-Object -First 4 | ForEach-Object { $file = Join-Path $root ("data\jobs\$key\csv-attempts\$_\result.json"); [pscustomobject]@{ path = $file; hash = Get-AgentHash $file } })
$resume = Start-AgentCsvJob $root $key $partial.plan.plan_id $partial.plan_hash -Resume
$done = Invoke-AgentCsvRun $root $key $resume.execution_id
Assert-True ($done.status -ceq 'done' -and $done.summary.success -eq 50 -and $done.summary.processing_complete) 'Resume processes remaining rows'
Assert-True ($script:SentIds.Count -eq 50 -and @($script:SentIds | Select-Object -Unique).Count -eq 50 -and $script:Calls -eq 10) 'First 20 never resent; each row sent exactly once'
foreach ($attempt in $initialAttempts) { Assert-True ((Get-AgentHash $attempt.path) -ceq $attempt.hash) 'Previously committed attempt unchanged' }
Assert-True ((Get-AgentHash $path) -ceq $originalHash) 'Original bytes unchanged'
Assert-Throws { Invoke-AgentCsvRun $root $key $resume.execution_id } 'CSV_EXECUTION|exist|存在' 'Completed execution cannot reenter'
$manifest = Read-AgentCsvJobManifest $root $done
$directory = Get-AgentJobDirectory $root $key
$firstId = $done.batch_ids[0]; $recordPath = Join-Path $directory ("csv-attempts\$firstId\attempt.json")
$firstRecord = Read-AgentJson $recordPath; $firstRecord.phase = 'response_received'; $firstRecord.result_sha256 = ''; Write-AgentJson $recordPath $firstRecord
$recovered = Get-AgentCsvReconciledResults $root $done $manifest
Assert-True ((Get-AgentCsvSummary $manifest $recovered $categories).success -eq 50) 'Result committed before interrupted status write is recovered'
$resultPath = Join-Path $directory ("csv-attempts\$firstId\result.json")
$firstRecord.result_sha256 = '0' * 64; Write-AgentJson $recordPath $firstRecord
$recovered = Get-AgentCsvReconciledResults $root $done $manifest
Assert-True ((Get-AgentCsvSummary $manifest $recovered $categories).unknown -eq 5) 'Hash mismatch quarantines affected rows'
$done.status = 'partial'; Save-AgentJob $directory $done
Assert-Throws { Start-AgentCsvJob $root $key $done.plan.plan_id $done.plan_hash -Resume } 'CSV_UNKNOWN' 'Unknown send/result blocks resume'
Assert-Throws { New-AgentJob $root 'new task' $path } 'BUSY' 'Unknown previous job blocks new side effects'
Write-Output ("PASS: $script:Checks CSV lifecycle checks; live sends 0. Evidence: $root")
