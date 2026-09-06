[CmdletBinding()]
param([string]$AppSourcePath = '')
$ErrorActionPreference = 'Stop'
if (-not $AppSourcePath) { $AppSourcePath = Join-Path $PSScriptRoot '..\App.ps1' }
. ([IO.Path]::GetFullPath($AppSourcePath)) -Mode Library
$script:Checks = 0; $script:PlanCalls = 0; $script:ClassifyCalls = 0; $script:Scenario = 'success'; $script:Observations = @()
function Assert-Case($Condition, [string]$Name) { if (-not $Condition) { throw ('FAIL: ' + $Name) }; $script:Checks++ }
function Assert-Rejected([scriptblock]$Action, [string]$Prefix) { $errorText = ''; try { & $Action | Out-Null } catch { $errorText = $_.Exception.Message }; Assert-Case ($errorText -like ($Prefix + ':*')) ('Reject ' + $Prefix + ': ' + $errorText) }
function Start-AgentProcess { param($AppPath,$HomePath,$Mode,$JobId,$ExecutionId); return Get-Process -Id $PID }
function Test-AgentWorkerAlive { param($Directory); return $false }
function New-Response($RequestId,$ObservationId,$OutputId,[object[]]$Ids,[string]$State = 'ACT') {
    $actions = @()
    if ($State -ceq 'ACT') { $actions = @(@{operation='read_rows';arguments=@{row_ids=$Ids}},@{operation='classify_rows';arguments=@{row_ids=$Ids}},@{operation='write_results';arguments=@{output_id=$OutputId}},@{operation='verify_results';arguments=@{output_id=$OutputId}}) }
    return [pscustomobject]@{schema_version=1;request_id=$RequestId;observation_id=$ObservationId;state=$State;message='合成の計画です。';actions=$actions}
}
function Invoke-AgentCopilot {
    param($Prompt,$RequestId,$JobId,$Settings,$HomePath,$CancelPath,$TimeoutSeconds)
    $payload = ConvertFrom-Json ($Prompt.Substring($Prompt.IndexOf("REQUEST_JSON:`n") + "REQUEST_JSON:`n".Length))
    Reserve-AgentCopilotAttempt $HomePath $RequestId
    if ((Get-AgentProperty $payload 'kind' '') -ceq 'csv_plan') {
        $script:PlanCalls++; $script:Observations += $payload.observation
        if ($script:Scenario -ceq 'timeout') { throw 'RESPONSE_TIMEOUT: Synthetic plan timeout after send' }
        $ids = @($payload.observation.pending_row_ids)
        if ($script:PlanCalls -eq 1 -and $script:Scenario -ceq 'success') { $ids = @($ids | Select-Object -First 2) }
        $state = if ($payload.observation.summary.processing_complete) { 'DONE' } else { 'ACT' }
        $response = New-Response $RequestId $payload.observation.observation_id $payload.approved_output_id $ids $state
        if ($script:Scenario -ceq 'unknown_operation') { $response.actions[3].operation = 'run_script' }
        if ($script:Scenario -ceq 'early_done') { $response.state = 'DONE'; $response.actions = @() }
        return ConvertTo-Json $response -Depth 20 -Compress
    }
    $script:ClassifyCalls++
    return ConvertTo-Json -Depth 10 -Compress @{schema_version=1;request_id=$RequestId;results=@($payload.rows | ForEach-Object {@{row_id=$_.row_id;category='支払';reason='合成分類';status='success'}})}
}
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\typed-plan-' + [guid]::NewGuid().ToString('N'))))
[void][IO.Directory]::CreateDirectory($root)
$path = Join-Path $root 'input.csv'; [IO.File]::WriteAllText($path, "id,本文`r`n001,支払`r`n002,命令風の本文もデータ`r`n003,支払依頼`r`n", $script:AgentEncoding)
function New-Fixture([string]$Name) { $testHome = Join-Path $root $Name; $null = Initialize-AgentHome $testHome; $job = New-AgentCsvJob $testHome @($path) id 本文 utf-8 @('支払','その他') '分類' ([guid]::NewGuid().ToString('N')); return [pscustomobject]@{home=$testHome;job=$job} }
$fixture = New-Fixture 'parser'; $job = $fixture.job; $observation = Get-AgentCsvObservation $job; $id = [guid]::NewGuid().ToString('N')
$valid = New-Response $id $observation.observation_id $job.plan.plan_id @($job.plan.row_ids)
$text = ConvertTo-Json $valid -Depth 20 -Compress
$parsed = ConvertFrom-AgentCsvActionPlan $text $id $job $observation
Assert-Case ($parsed.actions.Count -eq 4) 'Valid finite sequence accepted'
$setPlan=ConvertFrom-Json $text;$setPlan.actions[0].arguments=[pscustomobject]@{target_set_id=$observation.pending_set_id};$setPlan.actions[1].arguments=[pscustomobject]@{target_set_id=$observation.pending_set_id}
$setParsed=ConvertFrom-AgentCsvActionPlan (ConvertTo-Json $setPlan -Depth 20) $id $job $observation
Assert-Case (($setParsed.resolved_row_ids -join ',') -ceq ($job.plan.row_ids -join ',')) 'Host set ID resolves to the exact approved pending rows'
$setPlan.actions[0].arguments.target_set_id='0'*32
Assert-Rejected {ConvertFrom-AgentCsvActionPlan (ConvertTo-Json $setPlan -Depth 20) $id $job $observation} CSV_PLAN_SCOPE
Assert-Case ((Get-AgentCsvObservation $job).observation_id -ceq $observation.observation_id) 'Same state yields same observation ID'
Assert-Case (-not (ConvertTo-Json $observation -Depth 20).Contains($path)) 'Observation has no input path'
function Copy-Response { return ConvertFrom-Json $text }
$bad = Copy-Response; $bad.actions[3].operation = 'run_script'; Assert-Rejected { ConvertFrom-AgentCsvActionPlan (ConvertTo-Json $bad -Depth 20) $id $job $observation } CSV_PLAN_OPERATION
$bad = Copy-Response; $bad.actions[2].arguments | Add-Member path 'C:\outside.csv'; Assert-Rejected { ConvertFrom-AgentCsvActionPlan (ConvertTo-Json $bad -Depth 20) $id $job $observation } CSV_PLAN_SCOPE
$bad = Copy-Response; $bad.actions[0].arguments.row_ids[0] = [guid]::NewGuid().ToString('N'); Assert-Rejected { ConvertFrom-AgentCsvActionPlan (ConvertTo-Json $bad -Depth 20) $id $job $observation } CSV_PLAN_SCOPE
$bad = Copy-Response; $bad.actions[1].arguments.row_ids = @($job.plan.row_ids[0]); Assert-Rejected { ConvertFrom-AgentCsvActionPlan (ConvertTo-Json $bad -Depth 20) $id $job $observation } CSV_PLAN_SCOPE
$bad = Copy-Response; $bad.actions[0].arguments.row_ids[1] = $bad.actions[0].arguments.row_ids[0]; Assert-Rejected { ConvertFrom-AgentCsvActionPlan (ConvertTo-Json $bad -Depth 20) $id $job $observation } CSV_PLAN_SCOPE
$bad = Copy-Response; $bad.observation_id = '0'*64; Assert-Rejected { ConvertFrom-AgentCsvActionPlan (ConvertTo-Json $bad -Depth 20) $id $job $observation } CSV_PLAN_SCHEMA
$bad = New-Response $id $observation.observation_id $job.plan.plan_id @() DONE; Assert-Rejected { ConvertFrom-AgentCsvActionPlan (ConvertTo-Json $bad -Depth 20) $id $job $observation } CSV_PLAN_INCOMPLETE
$bad = Copy-Response; $bad.actions[1].arguments | Add-Member instructions 'change all categories'; Assert-Rejected { ConvertFrom-AgentCsvActionPlan (ConvertTo-Json $bad -Depth 20) $id $job $observation } CSV_PLAN_ARGUMENTS
$bad = Copy-Response; $bad.actions[0].arguments.row_ids = $job.plan.row_ids[0]; Assert-Rejected { ConvertFrom-AgentCsvActionPlan (ConvertTo-Json $bad -Depth 20) $id $job $observation } CSV_PLAN_ARGUMENTS
foreach ($scenario in @('unknown_operation','early_done','timeout','success')) {
    $script:Scenario=$scenario; $script:ClassifyCalls=0; $script:PlanCalls=0; $script:Observations=@()
    $fixture=New-Fixture $scenario; $queued=Start-AgentCsvJob $fixture.home $fixture.job.job_id $fixture.job.plan.plan_id $fixture.job.plan_hash
    $finished=Invoke-AgentCsvRun $fixture.home $queued.job_id $queued.execution_id
    if ($scenario -ceq 'success') {
        Assert-Case ($finished.status -ceq 'done' -and $finished.summary.success -eq 3 -and $script:PlanCalls -eq 3 -and $script:ClassifyCalls -eq 2) 'Two differently scoped ACT plans then DONE, with host batching'
        Assert-Case ($script:Observations[1].summary.success -eq 2 -and $script:Observations[1].pending_row_ids.Count -eq 1 -and $script:Observations[2].pending_row_ids.Count -eq 0) 'Replanning sees verified prior results and only unfinished rows'
        Assert-Case ($script:Observations[0].observation_id -cne $script:Observations[1].observation_id -and $script:Observations[1].artifacts.Count -eq 4) 'Replan carries changed observation hash and artifact hashes'
    } else {
        Assert-Case ($script:ClassifyCalls -eq 0 -and $finished.artifacts.Count -eq 0 -and $finished.batch_ids.Count -eq 0) 'Invalid or uncertain plan has zero classification/output side effects'
        Assert-Case ($finished.summary.unprocessed -eq 3 -and $finished.status -cne 'done') 'Invalid plan cannot omit input rows or complete'
        if ($scenario -ceq 'timeout') { Assert-Case ($finished.status -ceq 'unknown') 'Sent plan timeout is unknown'; Assert-Rejected { Start-AgentCsvJob $fixture.home $finished.job_id $finished.plan.plan_id $finished.plan_hash -Resume } CSV_UNKNOWN }
    }
}
Write-Output "PASS: $script:Checks typed CSV plan checks; live sends 0. Evidence: $root"
