[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$PlanPath,
    [Parameter(Mandatory=$true)][ValidateSet(1,2)][int]$RunNumber,
    [int]$TimeoutSeconds=90
)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$dir=Split-Path -Parent ([IO.Path]::GetFullPath($PlanPath))
$plan=Get-Content -LiteralPath $PlanPath -Raw -Encoding UTF8 | ConvertFrom-Json
$request=Join-Path $dir ('run'+$RunNumber+'-request.json')
$result=Join-Path $dir ('run'+$RunNumber+'-observation.json')
if($plan.max_run_starts -ne 2 -or (Test-Path -LiteralPath $request) -or (Test-Path -LiteralPath $result)){throw 'PAD_PAIR: invalid limit or already requested; do not repeat Run'}
if($RunNumber -eq 1 -and (Test-Path (Join-Path $dir 'run2-request.json'))){throw 'PAD_PAIR: pair already advanced'}
if($RunNumber -eq 2){
    $gate=Get-Content -LiteralPath (Join-Path $dir 'run1/values.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if($gate.status -cne 'PASS' -or $gate.verification_id -cne $plan.verification_id -or $gate.run_number -ne 1){throw 'PAD_PAIR: Run1 artifact/value gate required'}
    foreach($file in $gate.artifacts){
        if((Get-FileHash -LiteralPath (Join-Path $root $file.path)).Hash.ToLowerInvariant() -cne $file.sha256){throw 'PAD_PAIR: Run1 snapshot changed'}
    }
    if(@($gate.artifacts).Count -ne @($plan.outputs).Count){throw 'PAD_PAIR: missing Run1 artifact'}
}
foreach($name in $plan.outputs){if(Test-Path -LiteralPath (Join-Path $root $name)){throw 'PAD_PAIR: output must be absent before this Run'}}
if((Get-FileHash -LiteralPath (Join-Path $root $plan.input)).Hash.ToLowerInvariant() -cne $plan.input_sha256){throw 'PAD_PAIR: input changed'}
if((Get-FileHash -LiteralPath (Join-Path $root $plan.source)).Hash.ToLowerInvariant() -cne $plan.source_sha256){throw 'PAD_PAIR: source changed'}
. (Join-Path $root 'App.ps1') -Mode Library
Initialize-AgentPadTypes
function Target {
    $p=Get-Process -Id $plan.pid
    if($p.ProcessName -cne 'PAD.Designer' -or $p.SessionId -ne $plan.session_id -or $p.MainWindowHandle.ToInt64() -ne $plan.hwnd -or $p.MainWindowHandle -eq 0){throw 'PAD_PAIR: owner/HWND/session mismatch'}
    $w=[Windows.Automation.AutomationElement]::FromHandle($p.MainWindowHandle)
    if($w.Current.ProcessId -ne $plan.pid -or $w.Current.Name -cne ('Power Automate | '+$plan.flow_name)){throw 'PAD_PAIR: target flow mismatch'}
    return $w
}
$w=Target
$before=Get-AgentPadSnapshot -Window $w -AllowErrors
if(-not $before.ready -or $before.running -or -not $before.errors_known -or $before.errors -ne 0){throw 'PAD_PAIR: target is not stopped and error-free'}
$rec=[ordered]@{verification_id=$plan.verification_id;run_number=$RunNumber;pid=$plan.pid;hwnd=$plan.hwnd;session_id=$plan.session_id;flow_name=$plan.flow_name;requested_at=[DateTime]::UtcNow.ToString('o');plan_sha256=(Get-FileHash $PlanPath).Hash.ToLowerInvariant();source_sha256=$plan.source_sha256;input_sha256=$plan.input_sha256;outputs_absent=$true;before=@{ready=$before.ready;running=$before.running;errors=$before.errors;errors_known=$before.errors_known};request_count=1}
$bytes=[Text.Encoding]::UTF8.GetBytes(($rec|ConvertTo-Json -Depth 5))
$stream=[IO.File]::Open($request,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
# The durable marker consumes this Run even if Invoke or observation throws.
$samples=New-Object Collections.Generic.List[object]
$seenRunning=$false;$completed=$false;$invokeError=$null
try{
    $w=Target
    Invoke-AgentPadControl $before.start
}catch{$invokeError=$_.Exception.Message}
$deadline=[DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
do{
    Start-Sleep -Milliseconds 250
    try{
        $w=Target
        $s=Get-AgentPadSnapshot -Window $w -AllowErrors
        if($s.running){$seenRunning=$true}
        $samples.Add(@{at=[DateTime]::UtcNow.ToString('o');status=$s.status;running=$s.running;ready=$s.ready;errors=$s.errors;errors_known=$s.errors_known})
        $completed=($seenRunning -and $s.ready -and -not $s.running -and $s.errors_known -and $s.errors -eq 0)
        if($s.errors_known -and $s.errors -gt 0 -and -not $s.running){break}
    }catch{$samples.Add(@{at=[DateTime]::UtcNow.ToString('o');observer_error=$_.Exception.Message})}
}while(-not $completed -and [DateTime]::UtcNow -lt $deadline)
$record=[ordered]@{verification_id=$plan.verification_id;run_number=$RunNumber;execution_requested=$true;additional_run_requested=$false;invoke_error=$invokeError;running_observed=$seenRunning;completion_observed=$completed;status=$(if($completed){'STOPPED_ERROR_FREE_REQUIRES_ARTIFACT_GATE'}else{'OBSERVATION_OR_EXECUTION_INCOMPLETE_NO_REPEAT'});samples=$samples.ToArray()}
[IO.File]::WriteAllText($result,($record|ConvertTo-Json -Depth 8),(New-Object Text.UTF8Encoding($false)))
$record|ConvertTo-Json -Depth 8
if(-not $completed){throw 'PAD_PAIR: follow same Run read-only; do not repeat'}
