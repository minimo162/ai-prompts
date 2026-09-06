# Child-process provider-boundary fault injection. This does not operate PAD or M365.
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$testApp=$script:AgentAppPath;$testAppHash=Get-AgentHash $testApp
$testRoot=Join-Path ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\.work'))) ('aicall-provider-fault-'+[guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($testRoot)|Out-Null
$testHome=Initialize-AgentHome (Join-Path $testRoot 'home')
$fixtureApp=Join-Path $testRoot 'FixtureApp.ps1'
$source=[IO.File]::ReadAllText($testApp,[Text.Encoding]::UTF8)
$tokens=$null;$errors=$null;$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'SOURCE_PARSE'}
$provider=@($ast.FindAll({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Invoke-AgentCopilot'},$true))
if($provider.Count -ne 1){throw 'UNIQUE_PROVIDER_BOUNDARY_REQUIRED'}
$stub=@'
function Invoke-AgentCopilot {
 param($Prompt,$RequestId,$JobId,$Settings,$HomePath,$CancelPath,$TimeoutSeconds,$Transport)
 $offset=$Prompt.IndexOf("REQUEST_JSON:`n",[StringComparison]::Ordinal)
 if($offset -lt 0){throw 'FIXTURE_REQUEST_MISSING'}
 $payload=ConvertFrom-Json $Prompt.Substring($offset+"REQUEST_JSON:`n".Length)
 $case=[string]$payload.instructions
 if($case -cnotin @('fixture:refusal','fixture:empty','fixture:timeout','fixture:cancelled')){throw 'FIXTURE_CASE_REJECTED'}
 $callRoot=Join-Path (Get-AgentJobDirectory $HomePath $JobId) ('runs\'+$payload.run_id+'\calls\'+$RequestId)
 $hit=Join-Path $callRoot 'provider-boundary-hit.json'
 $stream=[IO.File]::Open($hit,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 try{$bytes=$script:AgentEncoding.GetBytes((ConvertTo-Json @{pid=$PID;case=$case;app_path=$script:AgentAppPath;request_id=$RequestId} -Compress));$stream.Write($bytes,0,$bytes.Length)}finally{$stream.Dispose()}
 if($case -ceq 'fixture:timeout'){throw 'RESPONSE_TIMEOUT: injected provider deadline'}
 if($case -ceq 'fixture:cancelled'){[IO.File]::WriteAllText($CancelPath,'cancel at provider return')}
 $response=[ordered]@{request_id=$RequestId;job_id=$JobId;run_id=$payload.run_id;ai_call_id=$RequestId;status='success';result='Synthetic result';error_type='';input_count=1;output_count=1}
 if($case -ceq 'fixture:refusal'){$response.status='failed';$response.result='';$response.error_type='refusal';$response.output_count=0}
 if($case -ceq 'fixture:empty'){$response.result=''}
 return ConvertTo-Json $response -Compress
}
'@
$start=$provider[0].Extent.StartOffset;$end=$provider[0].Extent.EndOffset
$fixture=$source.Substring(0,$start)+$stub+$source.Substring($end)
$newAst=[Management.Automation.Language.Parser]::ParseInput($fixture,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'FIXTURE_PARSE'}
$newProvider=@($newAst.FindAll({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Invoke-AgentCopilot'},$true))[0]
$restored=$fixture.Substring(0,$newProvider.Extent.StartOffset)+$provider[0].Extent.Text+$fixture.Substring($newProvider.Extent.EndOffset)
if(-not [string]::Equals($restored,$source,[StringComparison]::Ordinal)){throw 'ONLY_PROVIDER_BOUNDARY_MAY_DIFFER'}
[IO.File]::WriteAllText($fixtureApp,$fixture,(New-Object Text.UTF8Encoding($true)))
$rows=@();$checks=0
function Assert-Fault($Condition,[string]$Name){if(-not $Condition){throw ('FAIL: '+$Name)};$script:checks++}
foreach($case in @('refusal','empty','timeout','cancelled')){
 $jobId=[guid]::NewGuid().ToString('N');$runId=[guid]::NewGuid().ToString('N');$callId=[guid]::NewGuid().ToString('N')
 $jobRoot=Get-AgentJobDirectory $testHome $jobId;$runRoot=Join-Path $jobRoot ('runs\'+$runId);$callRoot=Join-Path $runRoot ('calls\'+$callId)
 [IO.Directory]::CreateDirectory($callRoot)|Out-Null
 $inputPath=Join-Path $jobRoot 'input.txt';[IO.File]::WriteAllText($inputPath,'Synthetic fixture input',$script:AgentEncoding)
 Write-AgentJson (Join-Path $jobRoot 'job.json') @{job_id=$jobId;status='running_pad';target=$inputPath}
 Write-AgentJson (Join-Path $jobRoot 'active-run.json') @{job_id=$jobId;run_id=$runId;status='pad_running';run_directory=$runRoot;app_path=$fixtureApp}
 $request=Join-Path $callRoot 'request.json';$resultPath=Join-Path $callRoot 'result.json'
 Write-AgentJson $request @{job_id=$jobId;run_id=$runId;ai_call_id=$callId;operation='translate';input_path=$inputPath;output_format='text';labels=@();instructions=('fixture:'+$case);timeout_seconds=5}
 $info=New-Object Diagnostics.ProcessStartInfo
 $info.FileName=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
 $info.Arguments='-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "'+$fixtureApp+'" -Mode AiCall -HomePath "'+$testHome+'" -RequestPath "'+$request+'" -ResultPath "'+$resultPath+'"'
 $info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
 $info.EnvironmentVariables['PSModulePath']=Join-Path $PSHOME 'Modules'
 $child=[Diagnostics.Process]::Start($info)
 try{$stdout=$child.StandardOutput.ReadToEndAsync();$stderr=$child.StandardError.ReadToEndAsync();if(-not $child.WaitForExit(15000)){throw ('CHILD_STILL_RUNNING: '+$child.Id)};$null=$stdout.GetAwaiter().GetResult();$null=$stderr.GetAwaiter().GetResult();$childId=$child.Id;$exitCode=$child.ExitCode}finally{$child.Dispose()}
 $hit=Read-AgentJson (Join-Path $callRoot 'provider-boundary-hit.json');$result=Read-AgentJson $resultPath
 $expectedStatus=if($case -ceq 'cancelled'){'cancelled'}else{'failed'};$expectedError=if($case -ceq 'empty'){'empty_result'}else{$case}
 Assert-Fault ($hit.pid -eq $childId -and $hit.pid -ne $PID -and $hit.app_path -ceq $fixtureApp -and $hit.request_id -ceq $callId) ($case+' injected in the actual child, not the parent')
 Assert-Fault ($exitCode -eq 1 -and $result.status -ceq $expectedStatus -and $result.error_type -ceq $expectedError) ($case+' typed failure and exit code')
 Assert-Fault ($result.job_id -ceq $jobId -and $result.run_id -ceq $runId -and $result.ai_call_id -ceq $callId -and $result.input_count -eq 1 -and $result.output_count -eq 0 -and $result.result -ceq '') ($case+' result correspondence and empty failure output')
 Assert-Fault (-not (Test-Path (Join-Path $callRoot 'result.txt')) -and [IO.File]::ReadAllText((Join-Path $callRoot 'status.txt')) -ceq $expectedStatus) ($case+' cannot masquerade as successful text')
 Assert-Fault (-not (Test-Path (Join-Path $jobRoot 'copilot-target.json')) -and -not (Test-Path (Get-AgentCopilotAttemptPath $testHome $callId))) ($case+' no real browser or send reservation')
 $rows+=@{case=$case;child_pid=$childId;status=$result.status;error_type=$result.error_type;result_sha256=Get-AgentHash $resultPath}
}
Assert-Fault ((Get-AgentHash $testApp) -ceq $testAppHash) 'Production source unchanged'
Write-AgentJson (Join-Path $testRoot 'validation.json') @{status='passed';checks=$checks;cases=$rows;source_sha256=$testAppHash;fixture_sha256=Get-AgentHash $fixtureApp;only_provider_function_replaced=$true;pad_calls=0;real_provider_calls=0;scope='child receiver fault injection; not live M365 refusal or real PAD flow'}
"PASS: $checks child provider-failure checks. Only the provider function was replaced; no live M365/PAD. Evidence: $testRoot"
