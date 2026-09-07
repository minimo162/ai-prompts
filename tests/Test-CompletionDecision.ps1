$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library -OfflineTest
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\completion-'+[guid]::NewGuid().ToString('N'))));[void][IO.Directory]::CreateDirectory($root)
$checks=0
function Check($value,$name){if(-not $value){throw ('FAIL: '+$name)};$script:checks++}
function Invoke-AgentCopilot {
 param($Prompt,$RequestId,$JobId,$ConversationId,$Settings,$HomePath,$CancelPath,$TimeoutSeconds,$Transport)
 if($Prompt.Contains('REVIEW_JSON:')){
  $script:reviews++;$context=$Prompt.Substring($Prompt.IndexOf("REVIEW_JSON:`n")+"REVIEW_JSON:`n".Length)|ConvertFrom-Json
  Check ($ConversationId -ceq $RequestId) 'Review uses a fresh scoped conversation'
  Check ($context.sources.Count -eq 1 -and $context.sources[0].content -ceq 'source' -and $context.sources[0].role -ceq 'input_not_output') 'Review receives separate original input evidence'
  Check ($Prompt.Contains('including all required text fences and markers')) 'Payload instruction preserves transport framing'
  Check ($context.artifacts[0].content -ceq $(if($script:completionCaseMode -eq 'truncated'){'x'*8192}else{'ready'})) 'Review receives actual observed content'
  $state=if($script:completionCaseMode -eq 'continue' -and $script:reviews -eq 1){'CONTINUE'}elseif($script:completionCaseMode -eq 'blocked'){'BLOCKED'}else{'DONE'}
  $reply=@{request_id=$RequestId;observation_id=$context.observation_id;state=$state;message='fixture decision';artifacts=@()}
  if($state -eq 'DONE'){$reply.artifacts=@($context.artifacts[-1].path)}
  if($script:completionCaseMode -eq 'unobserved'){$reply.artifacts=@($script:fixtureInput)}
  if($script:completionCaseMode -eq 'stale'){$reply.observation_id='stale'}
  if($script:completionCaseMode -eq 'extra'){$reply.robin='WAIT 0'}
  if($script:completionCaseMode -eq 'changed'){[IO.File]::AppendAllText($context.artifacts[-1].path,'changed')}
  if($script:completionCaseMode -eq 'input-changed'){[IO.File]::AppendAllText($context.sources[0].path,'changed')}
  return ($reply|ConvertTo-Json -Depth 8 -Compress)
 }
 $script:plans++
 $start=$Prompt.IndexOf("CONTEXT_JSON:`n")+"CONTEXT_JSON:`n".Length;$end=$Prompt.IndexOf("`nAn optional",$start);$context=$Prompt.Substring($start,$end-$start)|ConvertFrom-Json
 if($script:plans -gt 1){Check ($context.completion_reviews[0].state -ceq 'CONTINUE') 'Remaining-work assessment reaches the next generator'}
 return (@{request_id=$RequestId;state='ACT';message='fixture work';robin='WAIT 0';artifacts=@()}|ConvertTo-Json -Compress)
}
function Invoke-AgentPad {
 param($Robin,$RunDirectory,$RunId,$Job,$Settings,$CancelPath)
 $script:padRuns++;$path=Join-Path $RunDirectory 'artifacts\result.txt'
 [IO.File]::WriteAllText($path,$(if($script:completionCaseMode -eq 'truncated'){'x'*9000}else{'ready'}),(New-Object Text.UTF8Encoding($false)))
 return [pscustomobject]@{status='success';error='';artifacts=@($path)}
}
function Run-Case([string]$Mode,[int]$Rounds=1){
 $script:completionCaseMode=$Mode;$script:plans=0;$script:padRuns=0;$script:reviews=0
 $homePath=Initialize-AgentHome (Join-Path $root $Mode);$settings=Get-AgentSettings $homePath;$settings.max_rounds=$Rounds;Write-AgentJson (Join-Path $homePath 'data\settings.json') $settings
 $script:fixtureInput=Join-Path $homePath 'input.txt';[IO.File]::WriteAllText($script:fixtureInput,'source')
 $id=[guid]::NewGuid().ToString('N');$job=[pscustomobject]@{job_id=$id;status='queued';goal='Produce ready';target=$script:fixtureInput;question='';final_answer='';artifacts=@();history=@();error=''}
 Save-AgentJob (Get-AgentJobDirectory $homePath $id) $job
 return Invoke-AgentRun $homePath $id
}
$job=Run-Case done
Check ($job.status -ceq 'done' -and $script:plans -eq 1 -and $script:padRuns -eq 1 -and $script:reviews -eq 1) 'Completion ends the first round without another code generation, even at max_rounds=1'
Check (Test-AgentId $job.artifacts[0].artifact_id) 'Completion retains the observed artifact ID'
$job=Run-Case continue 2
Check ($job.status -ceq 'done' -and $script:plans -eq 2 -and $script:padRuns -eq 2) 'An unmet requirement permits another bounded step'
$job=Run-Case blocked
Check ($job.status -ceq 'blocked' -and $script:padRuns -eq 1) 'Blocked review cannot trigger another PAD run'
foreach($caseName in @('unobserved','stale','extra','changed','input-changed')){$job=Run-Case $caseName;Check ($job.status -ceq 'failed' -and $script:padRuns -eq 1) ('Invalid review cannot finish or reexecute: '+$caseName)}
$job=Run-Case truncated
Check ($job.status -ceq 'blocked' -and $script:padRuns -eq 1) 'A truncated artifact cannot become DONE'
$sourcePath=Join-Path $root 'source-evidence.txt';$sourceText="  100% C:\sample 'quote'`r`nnext  "
[IO.File]::WriteAllText($sourcePath,$sourceText,(New-Object Text.UTF8Encoding($true)))
$source=@(Get-AgentSourceEvidence ([pscustomobject]@{target=$sourcePath}))[0]
Check ($source.content -ceq $sourceText -and $source.text_status -ceq 'complete') 'Input observation excludes BOM but preserves all content'
[IO.File]::WriteAllText($sourcePath,('x'*8191)+[char]::ConvertFromUtf32(0x1f600)+'z',(New-Object Text.UTF8Encoding($false)))
$source=@(Get-AgentSourceEvidence ([pscustomobject]@{target=$sourcePath}))[0]
Check ($source.content.Length -eq 8191 -and $source.truncated) 'Input sample never ends with half a surrogate pair'
Check (@(Get-AgentSourceEvidence ([pscustomobject]@{target=$root})).Count -eq 0) 'Directory scope is not silently read recursively'
Write-Output "PASS: $checks completion decision checks; provider/PAD mocked. Evidence: $root"
