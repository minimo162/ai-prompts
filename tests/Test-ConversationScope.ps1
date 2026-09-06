$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$checks=0
function Check($Value,$Name){if(-not $Value){throw ('FAIL: '+$Name)};$script:checks++}
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\conversation-scope-'+[guid]::NewGuid().ToString('N'))));$null=Initialize-AgentHome $root
$jobId=[guid]::NewGuid().ToString('N');$first=[guid]::NewGuid().ToString('N');$second=[guid]::NewGuid().ToString('N')
$settings=Get-AgentSettings $root;$a=Get-AgentCopilotConfig $root $settings $jobId $first;$b=Get-AgentCopilotConfig $root $settings $jobId $second;$plan=Get-AgentCopilotConfig $root $settings $jobId
Check ($a.Profile -ceq $b.Profile -and $a.Profile -ceq $plan.Profile) 'Dedicated application profile remains the same'
Check ($a.TargetPath -cne $b.TargetPath -and $a.TargetPath -cne $plan.TargetPath) 'Batch and planner target records are separate'
$script:pages=@();$script:newTargets=0
function Assert-AgentCopilotOwnership($Config){}
function Invoke-AgentCopilotHttp($Config,$Path,$Method='GET'){
 if($Path -ceq '/json/list'){return $script:pages}
 if($Method -ceq 'PUT'){$script:newTargets++;$target=[pscustomobject]@{id=('fixture-'+$script:newTargets);type='page';url=$Config.Url;webSocketDebuggerUrl=('ws://127.0.0.1:'+$Config.Port+'/devtools/page/fixture-'+$script:newTargets)};$script:pages+=,$target;return $target}
 throw 'Unexpected mock request'
}
$ta=Get-AgentCopilotTarget $a -Create;$tb=Get-AgentCopilotTarget $b -Create;$tp=Get-AgentCopilotTarget $plan -Create
Check ($ta.id -cne $tb.id -and $tb.id -cne $tp.id -and $script:newTargets -eq 3) 'Distinct owned tabs for two batches and the planner'
$ra=Read-AgentJson $a.TargetPath;$rb=Read-AgentJson $b.TargetPath
Check ((Test-AgentCopilotTargetRecord $a $ra) -and -not(Test-AgentCopilotTargetRecord $b $ra) -and -not(Test-AgentCopilotTargetRecord $plan $ra)) 'Conversation ownership cannot be borrowed across scopes'
Set-AgentCopilotJobSendStarted $a $ta
Check (-not (Get-AgentCopilotTarget $a).agent_first_job_send -and (Get-AgentCopilotTarget $b).agent_first_job_send) 'Sending one batch does not weaken the other baseline'
$script:pages=@($script:pages|Where-Object id -CNE $ta.id);$message='';try{Get-AgentCopilotTarget $a -Create|Out-Null}catch{$message=$_.Exception.Message}
Check ($message -like 'CDP_UNAVAILABLE:*' -and $script:newTargets -eq 3) 'Lost conversation is not replaced or replayed'
$message='';try{Get-AgentCopilotConfig $root $settings '' $first|Out-Null}catch{$message=$_.Exception.Message};Check ($message -like 'RESPONSE_INVALID:*') 'Conversation must belong to a job'
Write-Output "PASS: $checks conversation scope checks; no browser or provider contacted. Evidence: $root"
