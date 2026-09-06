param([string]$AppSourcePath='')
$ErrorActionPreference='Stop'
if(-not $AppSourcePath){$AppSourcePath=Join-Path $PSScriptRoot '..\App.ps1'}
. ([IO.Path]::GetFullPath($AppSourcePath)) -Mode Library
$script:checks=0
function Check($Value,[string]$Name){if(-not $Value){throw ('FAIL: '+$Name)};$script:checks++}
function Reject([scriptblock]$Action,[string]$Prefix){$message='';try{& $Action|Out-Null}catch{$message=$_.Exception.Message};Check ($message -like ($Prefix+':*')) $message}
$actualPolicy=(Get-Command Get-AgentEdgePolicyEntries).ScriptBlock
$before=ConvertTo-Json -InputObject (& $actualPolicy) -Compress
$script:entries=@()
function Get-AgentEdgePolicyEntries{return ,$script:entries}
foreach($value in @($null,1)){$script:entries=@([pscustomobject]@{scope='fixture';readable=$true;value=$value});Assert-AgentEdgePolicy;Check $true 'Unconfigured/enabled policy accepted'}
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\connection-'+[guid]::NewGuid().ToString('N'))))
$script:entries=@([pscustomobject]@{scope='HKLM';readable=$true;value=1},[pscustomobject]@{scope='HKCU';readable=$true;value=0})
Reject {Invoke-AgentCopilot -HomePath $root -JobId ('a'*32) -RequestId ('b'*32) -Prompt 'synthetic'} POLICY_BLOCKED
Reject {Open-AgentCopilot $root $null} POLICY_BLOCKED
Check (-not [IO.Directory]::Exists($root)) 'Policy denial creates no profile, telemetry or attempt'
$script:entries=@([pscustomobject]@{scope='fixture';readable=$false;value=$null});Reject {Assert-AgentEdgePolicy} POLICY_UNAVAILABLE
$script:entries=@([pscustomobject]@{scope='fixture';readable=$true;value='0'});Reject {Assert-AgentEdgePolicy} POLICY_UNAVAILABLE
$script:entries=@([pscustomobject]@{scope='fixture';readable=$true;value=1})
$trace=New-AgentConnectionTrace $root ('b'*32) ('a'*32) JsonPartsV1
Check ($trace.phase -ceq 'preparing' -and -not $trace.send_reserved) 'Preparation is not sending'
$trace.send_reserved=$true;Set-AgentConnectionTrace $root $trace send_reserved 10
$trace.click_acknowledged=$true;Set-AgentConnectionTrace $root $trace click_acknowledged 20
$trace.response_complete=$true;Set-AgentConnectionTrace $root $trace response_complete 50
$path=(Get-AgentCopilotAttemptPath $root ('b'*32))+'.json';$record=Read-AgentJson $path
Check ($record.events.Count -eq 4 -and $record.elapsed_ms -eq 50 -and $record.response_complete) 'Versioned event history retains distinct reservation/ack/completion'
Check ($null -eq $record.PSObject.Properties['prompt'] -and $null -eq $record.PSObject.Properties['response']) 'Trace contains no business text'
$hash=Get-AgentHash $path
try{New-AgentConnectionTrace $root ('b'*32) ('a'*32) JsonPartsV1|Out-Null}catch{}
Check ((Get-AgentHash $path) -ceq $hash) 'Request trace cannot be overwritten by a new attempt'
Check ((Get-AgentConnectionErrorType 'AUTH_REQUIRED: secret') -ceq 'authentication' -and (Get-AgentConnectionErrorType 'RESPONSE_TIMEOUT: secret') -ceq 'timeout') 'Errors reduced to fixed categories'
Check ($before -ceq (ConvertTo-Json -InputObject (& $actualPolicy) -Compress)) 'Actual registry policy unchanged'
Write-Output "PASS: $script:checks connection contract checks; no browser or provider invoked. Evidence: $root"
