# Real PS5.1 AiCall child processes with isolated, pre-send failure fixtures.
# No PAD flow, Copilot tab, browser connection or provider response is simulated here.
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$processTestApp=$script:AgentAppPath;$processTestHash=Get-AgentHash $processTestApp
$processTestRoot=Join-Path ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\.work'))) ('aicall-process-'+[guid]::NewGuid().ToString('N'))
$processTestHome=Initialize-AgentHome (Join-Path $processTestRoot 'home')
$script:processChecks=0
function Check-Process($Condition,[string]$Name){if(-not $Condition){throw ('FAIL: '+$Name)};$script:processChecks++}
function Invoke-ChildAiCall([string]$Request,[string]$Result){
 $info=New-Object Diagnostics.ProcessStartInfo
 $info.FileName=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
 $info.Arguments='-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$processTestApp+'" -Mode AiCall -HomePath "'+$processTestHome+'" -RequestPath "'+$Request+'" -ResultPath "'+$Result+'"'
 $info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden
 $info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
 $info.EnvironmentVariables['PSModulePath']=Join-Path $PSHOME 'Modules'
 $child=[Diagnostics.Process]::Start($info)
 try {
  $stdout=$child.StandardOutput.ReadToEndAsync();$stderr=$child.StandardError.ReadToEndAsync()
  if(-not $child.WaitForExit(15000)){throw ('Child still running beyond test deadline; PID='+$child.Id)}
  $null=$stdout.GetAwaiter().GetResult();$null=$stderr.GetAwaiter().GetResult()
  return $child.ExitCode
 } finally {$child.Dispose()}
}
function New-ChildContext([string]$Case){
 $jobId=[guid]::NewGuid().ToString('N');$runId=[guid]::NewGuid().ToString('N');$callId=[guid]::NewGuid().ToString('N')
 $jobRoot=Get-AgentJobDirectory $processTestHome $jobId;$runRoot=Join-Path $jobRoot ('runs\'+$runId);$callRoot=Join-Path $runRoot ('calls\'+$callId)
 [IO.Directory]::CreateDirectory($callRoot)|Out-Null
 $inputPath=Join-Path $jobRoot 'input.txt'
 [IO.File]::WriteAllText($inputPath,$(if($Case -ceq 'empty-input'){''}else{'Synthetic fixture'}),$script:AgentEncoding)
 Write-AgentJson (Join-Path $jobRoot 'job.json') @{job_id=$jobId;status='running_pad';target=$inputPath}
 Write-AgentJson (Join-Path $jobRoot 'active-run.json') @{job_id=$jobId;run_id=$runId;status='pad_running';run_directory=$runRoot;app_path=$processTestApp}
 $requestPath=Join-Path $callRoot 'request.json';$resultPath=Join-Path $callRoot 'result.json'
 Write-AgentJson $requestPath @{job_id=$jobId;run_id=$runId;ai_call_id=$callId;operation='translate';input_path=$inputPath;output_format='text';labels=@();instructions='Synthetic fixture';timeout_seconds=5}
 if($Case -ceq 'cancelled'){[IO.File]::WriteAllText((Join-Path $jobRoot 'cancel'),'stop')}
 return @{job_id=$jobId;run_id=$runId;call_id=$callId;job_root=$jobRoot;call_root=$callRoot;request_path=$requestPath;result_path=$resultPath}
}
foreach($case in @('empty-input','cancelled')){
 $context=New-ChildContext $case
 Check-Process ((Invoke-ChildAiCall $context.request_path $context.result_path) -eq 1) ($case+' child returns failure exit code')
 $result=Read-AgentJson $context.result_path
 $expectedStatus=if($case -ceq 'cancelled'){'cancelled'}else{'failed'}
 $expectedError=if($case -ceq 'cancelled'){'cancelled'}else{'empty_result'}
 Check-Process ($result.status -ceq $expectedStatus -and $result.error_type -ceq $expectedError -and $result.output_count -eq 0 -and $result.result -ceq '') ($case+' typed failure survives real process boundary')
 Check-Process ($result.job_id -ceq $context.job_id -and $result.run_id -ceq $context.run_id -and $result.ai_call_id -ceq $context.call_id) ($case+' result IDs match the request')
 Check-Process (([IO.File]::ReadAllText((Join-Path $context.call_root 'status.txt'))) -ceq $expectedStatus -and -not (Test-Path (Join-Path $context.call_root 'result.txt'))) ($case+' no successful text companion')
 Check-Process (-not (Test-Path (Get-AgentCopilotAttemptPath $processTestHome $context.call_id)) -and -not (Test-Path (Join-Path $context.job_root 'copilot-target.json'))) ($case+' failed before browser target or send reservation')
 $beforeHash=Get-AgentHash $context.result_path;$beforeTime=(Get-Item $context.result_path).LastWriteTimeUtc.Ticks
 Check-Process ((Invoke-ChildAiCall $context.request_path $context.result_path) -eq 1 -and (Get-AgentHash $context.result_path) -ceq $beforeHash -and (Get-Item $context.result_path).LastWriteTimeUtc.Ticks -eq $beforeTime) ($case+' duplicate child cannot replace its immutable result')
}
$context=New-ChildContext 'wrong-app'
$active=Read-AgentJson (Join-Path $context.job_root 'active-run.json');$active.app_path=Join-Path $processTestRoot 'unrelated.ps1';Write-AgentJson (Join-Path $context.job_root 'active-run.json') $active
Check-Process ((Invoke-ChildAiCall $context.request_path $context.result_path) -eq 1 -and -not (Test-Path $context.result_path) -and -not (Test-Path (Join-Path $context.call_root 'call.claim'))) 'Unpinned child context fails before claim/result writes'
Check-Process ((Get-AgentHash $processTestApp) -ceq $processTestHash) 'Production App preserved'
Write-AgentJson (Join-Path $processTestRoot 'result.json') @{status='passed';checks=$script:processChecks;app_sha256=$processTestHash;real_child_processes=5;pad_calls=0;provider_calls=0;scope='pre-send failures; not empty provider response or in-flight cancellation'}
"PASS: $script:processChecks real AiCall child-process checks; pre-send failures only, no PAD/provider. Evidence: $processTestRoot"
