param(
 [string]$SourcePath=(Join-Path $PSScriptRoot '..\App.ps1'),
 [string]$EvidencePath=''
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2.0
$transportSource=[IO.Path]::GetFullPath($SourcePath)
$transportSourceSha=(Get-FileHash -LiteralPath $transportSource).Hash.ToLowerInvariant()
$parseErrors=$null;$tokens=$null
$transportAst=[Management.Automation.Language.Parser]::ParseFile($transportSource,[ref]$tokens,[ref]$parseErrors)
if($parseErrors.Count){throw ('PowerShell parse errors: '+$parseErrors.Count)}
# Definitions only: never import the server/launcher top level or operate a browser.
$wanted=@('Get-AgentProperty','Get-AgentFullPath','Assert-AgentId','Assert-AgentPathUnder','Assert-AgentNoReparse','Get-AgentHash','Get-AgentTextHash','Get-AgentCopilotConfig','Test-AgentCopilotUrl','Test-AgentCopilotAuthUrl','Test-AgentCopilotSocketUrl','Read-AgentJsonToken','Test-AgentStrictJson','ConvertFrom-AgentJson','Get-AgentPlannerResponse','ConvertFrom-AgentCopilotResponse','ConvertFrom-AgentCopilotParts','ConvertFrom-AgentCopilotPlannerV2','Assert-AgentCopilotWait','Enter-AgentCopilotMutex','Get-AgentCopilotAttemptPath','Reserve-AgentCopilotAttempt','Test-AgentCopilotTargetRecord','Write-AgentCopilotTargetRecord','Get-AgentCopilotTarget','Assert-AgentCopilotJobBaseline','Set-AgentCopilotJobSendStarted','Wait-AgentCopilotInputReady','Invoke-AgentCopilotExpand','Invoke-AgentCopilot','Get-AgentCopilotDomPrelude')
$definitions=@($transportAst.FindAll({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst]},$false))
# Permit private V2 parser helpers to evolve without importing executable top-level statements.
$wanted+=@($definitions|Where-Object {$_.Name -like '*PlannerV2*'}|ForEach-Object Name)
foreach($name in @($wanted|Select-Object -Unique)){
 $definition=@($definitions|Where-Object Name -ceq $name)
 if($definition.Count -ne 1){throw ('Missing or duplicate definition: '+$name)}
 . ([scriptblock]::Create($definition[0].Extent.Text))
}
$script:transportChecks=New-Object 'Collections.Generic.List[object]'
function Assert-Transport([bool]$Condition,[string]$Name){$script:transportChecks.Add([pscustomobject]@{name=$Name;passed=$Condition});if(-not $Condition){throw ('FAIL: '+$Name)}}
function Assert-TransportRejected([scriptblock]$Action,[string]$Prefix,[string]$Name){
 $caught='';try{& $Action|Out-Null}catch{$caught=$_.Exception.Message}
 Assert-Transport ($caught.StartsWith($Prefix+':',[StringComparison]::Ordinal)) ($Name+'; expected '+$Prefix+', received '+$(if($caught){$caught.Split(':')[0]}else{'success'}))
}
function New-TransportV2([string]$RequestId,[string]$State='ACT',[string]$Body='', [switch]$PrettyMeta){
 if($State -ceq 'ACT' -and $Body -ceq ''){$Body="SET Probe TO `$'''  日本語 C:\raw\path %FileContents% literal\n  '''`n`n  SET Tail TO `$'''O'Brien `"quote`" '''"}
 $meta=[ordered]@{request_id=$RequestId;state=$State;message='Synthetic planner reply';artifacts=@()}
 $metaText=if($PrettyMeta){ConvertTo-Json -InputObject $meta -Depth 12}else{ConvertTo-Json -InputObject $meta -Depth 12 -Compress}
 $metaText=$metaText.Replace("`r`n","`n")
 $frame1='AGENT_META_V2 '+$RequestId+"`n"+$metaText+"`nAGENT_META_END_V2 "+$RequestId
 $wireRows=@();if($Body -cne ''){foreach($row in $Body.Split([char]10)){if($row -ceq ''){$wireRows+=,('AGENT_EMPTY_V2 '+$RequestId)}else{$wireRows+=,$row}}}
 $frame2='AGENT_ROBIN_V2 '+$RequestId+"`n"+$(if($wireRows.Count){($wireRows -join "`n")+"`n"}else{''})+'AGENT_ROBIN_END_V2 '+$RequestId+"`nAGENT_END_"+$RequestId
 return [pscustomobject]@{key='reply-'+$RequestId;text='';frames=@($frame1,$frame2);source_kind='fenced_planner_v2';collapsed=$true;expected_robin=$Body;expected_state=$State}
}
function New-TransportV1([string]$RequestId,[int]$Width=70){
 $raw=ConvertTo-Json -InputObject ([ordered]@{request_id=$RequestId;status='success';text="  日本語 C:\raw literal\n %Value%`n  ";items=@()}) -Depth 8 -Compress
 $pieces=@();for($offset=0;$offset -lt $raw.Length;$offset+=$Width){$pieces+=,$raw.Substring($offset,[Math]::Min($Width,$raw.Length-$offset))}
 $frames=@();for($i=0;$i -lt $pieces.Count;$i++){$pin=$RequestId+' '+($i+1)+' '+$pieces.Count;$frame='AGENT_PART_V1 '+$pin+"`nAGENT_DATA "+$pieces[$i]+"`nAGENT_PART_END_V1 "+$pin;if($i -eq $pieces.Count-1){$frame+="`nAGENT_END_"+$RequestId};$frames+=,$frame}
 return [pscustomobject]@{key='reply-'+$RequestId;text='';frames=$frames;source_kind='fenced_parts';collapsed=$true;expected_raw=$raw}
}
function New-TransportPage([string]$Id){return [pscustomobject]@{id=$Id;type='page';url='https://m365.cloud.microsoft/chat/';webSocketDebuggerUrl=('ws://127.0.0.1:9223/devtools/page/'+$Id)}}
$transportTemp=Join-Path ([IO.Path]::GetTempPath()) ('ai-prompts-planner-v2-'+[guid]::NewGuid().ToString('N'))
$null=[IO.Directory]::CreateDirectory($transportTemp)
$script:transportPages=@();$script:transportCreated=0;$script:transportConnects=0;$script:transportDisposed=0;$script:transportOwnership=0
# The only replaced functions are external browser/DOM boundaries. Target records,
# attempt reservation, requested transport, parsers and the response loop remain real.
function Assert-AgentCopilotOwnership {param($Config);$script:transportOwnership++;if($script:transportLoseOwnershipAt -gt 0 -and $script:transportReads -ge $script:transportLoseOwnershipAt){throw 'CDP_UNAVAILABLE: Synthetic ownership loss after final response snapshot.'}}
function Invoke-AgentCopilotHttp {
 param($Config,[string]$Path,[string]$Method='GET')
 if($Path -ceq '/json/list'){return $script:transportPages}
 if($Path.StartsWith('/json/new?',[StringComparison]::Ordinal) -and $Method -ceq 'PUT'){$script:transportCreated++;$page=New-TransportPage $script:transportNextTarget;$script:transportPages+=,$page;return $page}
 throw ('Unexpected synthetic HTTP call: '+$Path)
}
function Connect-AgentCopilotSocket {param($Config,$Target);$script:transportConnects++;$socket=[pscustomobject]@{};$socket|Add-Member -MemberType ScriptMethod -Name Dispose -Value {$script:transportDisposed++};return $socket}
function Reset-Transport([string]$RequestId,[object[]]$Candidates=@(),[object[]]$Baseline=@(),[string]$JobId=''){
 $script:transportRequest=$RequestId;$script:transportJob=if($JobId){$JobId}else{[guid]::NewGuid().ToString('N')}
 $script:transportCandidates=$Candidates;$script:transportBaseline=$Baseline;$script:transportInput='';$script:transportSent=$false
 $script:transportSends=0;$script:transportKeys=0;$script:transportInserts=0;$script:transportReads=0;$script:transportMore=0;$script:transportCopy=0;$script:transportWire=''
 $script:transportMutation=$null;$script:transportGenerating=$false;$script:transportHeldInput='';$script:transportCancel='';$script:transportCancelAt=0;$script:transportSendUncertain=$false;$script:transportLoseOwnershipAt=0;$script:transportDelayAtRead=0
 $script:transportNextTarget='synthetic-'+$script:transportJob
 $config=Get-AgentCopilotConfig $transportTemp @{} $script:transportJob;$target=Get-AgentCopilotTarget $config -Create
 if($Baseline.Count){Set-AgentCopilotJobSendStarted $config $target}
}
function Get-AgentCopilotSnapshot {
 param($Socket,$CancelPath,$Deadline)
 $shown=@($script:transportBaseline)
 if($script:transportSent){$script:transportReads++;if($null -ne $script:transportMutation){& $script:transportMutation};$shown+=@($script:transportCandidates);if($script:transportCancelAt -eq $script:transportReads){[IO.File]::WriteAllText($script:transportCancel,'cancel')};if($script:transportDelayAtRead -eq $script:transportReads){[Threading.Thread]::Sleep(4000)}}
 return [pscustomobject]@{inputCount=1;inputText=$(if($script:transportSent -and $script:transportHeldInput){$script:transportHeldInput}else{$script:transportInput});generating=($script:transportSent -and $script:transportGenerating);assistants=$shown}
}
function Invoke-AgentCopilotEval {
 param($Socket,$Expression,$CancelPath,$Deadline)
 if($Expression.Contains('sends[0].click()')){$script:transportSends++;if($script:transportSendUncertain){throw 'CDP_UNAVAILABLE: Synthetic uncertain send acknowledgement.'};$script:transportSent=$true;$script:transportInput=''}
 if($Expression.Contains('HTMLButtonElement.prototype.click.call(more)')){$script:transportMore++;throw 'TEST_FORBIDDEN: V2/framed transport must not click More.'}
 if($Expression -match 'clipboard\.(read|write)|execCommand\(.?copy|dispatchEvent\(.?copy'){$script:transportCopy++;throw 'TEST_FORBIDDEN: Browser clipboard use is forbidden.'}
 return $true
}
function Invoke-AgentCopilotCdp {
 param($Socket,$Method,$Params,$CancelPath,$Deadline)
 if($Method -ceq 'Input.insertText'){$script:transportInserts++;$script:transportInput=$Params.text;$script:transportWire=$Params.text;return}
 if($Method -ceq 'Input.dispatchKeyEvent'){$script:transportKeys++;if($Params.key -cnotin @('a','Backspace')){if($Params.key -ceq 'c'){$script:transportCopy++};throw 'TEST_FORBIDDEN: Unexpected browser key.'};return}
 throw ('Unexpected synthetic CDP method: '+$Method)
}
function Invoke-Transport([string]$Transport='PlannerV2',[switch]$OmitTransport){
 $params=@{Prompt='Synthetic transport controller test';RequestId=$script:transportRequest;JobId=$script:transportJob;Settings=@{};HomePath=$transportTemp;CancelPath=$script:transportCancel;TimeoutSeconds=5}
 if(-not $OmitTransport){$params.Transport=$Transport}
 return Invoke-AgentCopilot @params
}
function Assert-TransportOneSend([string]$Name){
 Assert-Transport ($script:transportSends -eq 1 -and $script:transportInserts -eq 1 -and $script:transportKeys -eq 4 -and $script:transportMore -eq 0 -and $script:transportCopy -eq 0 -and [IO.File]::Exists((Get-AgentCopilotAttemptPath $transportTemp $script:transportRequest))) ($Name+' retains exactly one input/send attempt, zero More and zero Copy')
}
$transportPassed=$false;$transportFailure=''
try{
 $invokeDefinition=@($definitions|Where-Object Name -ceq 'Invoke-AgentCopilot')[0]
 $transportParameter=@($invokeDefinition.Body.ParamBlock.Parameters|Where-Object {$_.Name.VariablePath.UserPath -ceq 'Transport'})
 Assert-Transport ($transportParameter.Count -eq 1 -and $transportParameter[0].DefaultValue.Value -ceq 'JsonPartsV1') 'The public adapter defaults to JsonPartsV1'
 $actual=New-TransportV2 'v2-complete';Reset-Transport 'v2-complete' @($actual)
 $json=Invoke-Transport;$decoded=Get-AgentPlannerResponse $json 'v2-complete'
 Assert-Transport ([string]::Equals($decoded.robin,$actual.expected_robin,[StringComparison]::Ordinal) -and $decoded.state -ceq 'ACT') 'Actual response loop restores literal Robin and explicit empty-line sentinels through actual planner validation'
 Assert-Transport ($script:transportReads -eq 3) 'V2 requires exactly three stable reads'
 Assert-TransportOneSend 'V2 accepted response'
 Assert-Transport ($script:transportWire.Contains('AGENT_META_V2 v2-complete') -and $script:transportWire.Contains('AGENT_ROBIN_V2 v2-complete') -and $script:transportWire.Contains('AGENT_EMPTY_V2 v2-complete') -and -not $script:transportWire.Contains('AGENT_PART_V1 v2-complete')) 'Only requested V2 prompt is sent, including current empty-row marker and nonce'
 Assert-TransportRejected {Invoke-Transport} 'RESPONSE_INVALID' 'Accepted V2 request cannot be replayed'
 Assert-TransportOneSend 'Rejected V2 replay'

 foreach($state in @('DONE','ASK_USER','BLOCKED')){
  $id='v2-state-'+$state.ToLowerInvariant();$candidate=New-TransportV2 $id $state;Reset-Transport $id @($candidate)
  $decoded=Get-AgentPlannerResponse (Invoke-Transport) $id
  Assert-Transport ($decoded.state -ceq $state -and $decoded.robin -ceq '' -and $candidate.frames[1].Split([char]10).Count -eq 3) ('V2 '+$state+' accepts exactly zero Robin body rows')
  Assert-Transport ($script:transportReads -eq 3) ($state+' has three stable reads');Assert-TransportOneSend $state
 }
 $literal="SET Probe TO `$'''"+[char]0x00a0+"  C:\raw\path %value% literal\n ""quoted""  '''`n`n  SET Tail TO `$'''end'''"
 $candidate=New-TransportV2 'v2-literal' 'ACT' $literal -PrettyMeta;Reset-Transport 'v2-literal' @($candidate)
 $decoded=Get-AgentPlannerResponse (Invoke-Transport) 'v2-literal'
 Assert-Transport ([string]::Equals($decoded.robin,$literal,[StringComparison]::Ordinal)) 'Pretty metadata does not alter Robin NBSP, spaces, blank row, backslashes, quotes or percent'

 # Genuine same-job continuation exercises persisted target ownership and nonce baselines.
 $mixedJob=[guid]::NewGuid().ToString('N');$mixedBefore=$script:transportCreated
 $first=New-TransportV2 'v2-mixed-first';Reset-Transport 'v2-mixed-first' @($first) @() $mixedJob;$null=Invoke-Transport;Assert-TransportOneSend 'Mixed first planner'
 $mixedConfig=Get-AgentCopilotConfig $transportTemp @{} $mixedJob;$firstTarget=(Get-AgentCopilotTarget $mixedConfig).id
 $ai=New-TransportV1 'v1-mixed-ai';Reset-Transport 'v1-mixed-ai' @($ai) @($first) $mixedJob
 Assert-Transport ((Invoke-Transport -OmitTransport) -ceq $ai.expected_raw) 'Default V1 AiCall succeeds after V2 planner in the same job'
 Assert-Transport ($script:transportWire.Contains('AGENT_PART_V1 v1-mixed-ai') -and -not $script:transportWire.Contains('AGENT_META_V2 v1-mixed-ai')) 'AiCall default prompt stays V1 within mixed conversation';Assert-TransportOneSend 'Mixed AiCall'
 $last=New-TransportV2 'v2-mixed-last' 'DONE';Reset-Transport 'v2-mixed-last' @($last) @($first,$ai) $mixedJob
 $decoded=Get-AgentPlannerResponse (Invoke-Transport) 'v2-mixed-last'
 Assert-Transport ($decoded.state -ceq 'DONE' -and $decoded.robin -ceq '') 'Second V2 planner succeeds after same-job V1 AiCall'
 Assert-Transport ((Get-AgentCopilotTarget $mixedConfig).id -ceq $firstTarget -and $script:transportCreated -eq $mixedBefore+1) 'Mixed V2 to V1 to V2 keeps one job-owned target'
 Assert-TransportOneSend 'Mixed last planner'
 Assert-Transport (@(Get-ChildItem -LiteralPath (Join-Path $transportTemp 'data\copilot-attempts') -Filter '*mixed*.attempt').Count -eq 3) 'Mixed conversation owns three distinct durable attempts'

 # Stability is identity of the raw carrier and key, not merely decoded JSON.
 Reset-Transport 'v2-key-reset' @((New-TransportV2 'v2-key-reset'))
 $script:transportMutation={if($script:transportReads -eq 3){$script:transportCandidates[0].key='changed-owned-key'}}
 $null=Invoke-Transport;Assert-Transport ($script:transportReads -eq 5) 'Changing V2 response key on third read restarts three-read stability';Assert-TransportOneSend 'Changed key'
 Reset-Transport 'v2-frame-reset' @((New-TransportV2 'v2-frame-reset'))
 $script:transportMutation={if($script:transportReads -eq 3){$script:transportCandidates=@(New-TransportV2 'v2-frame-reset' -PrettyMeta)}}
 $null=Invoke-Transport;Assert-Transport ($script:transportReads -eq 5) 'Semantically identical metadata with different raw frame rows restarts stability';Assert-TransportOneSend 'Changed raw frame'
 Reset-Transport 'v2-kind-reset' @((New-TransportV2 'v2-kind-reset'))
 $script:transportMutation={if($script:transportReads -eq 3){$script:transportCandidates[0].source_kind='fenced_parts'};if($script:transportReads -eq 4){$script:transportCandidates[0].source_kind='fenced_planner_v2'}}
 $null=Invoke-Transport;Assert-Transport ($script:transportReads -eq 6) 'Wrong source kind on third read invalidates stability before V2 provenance returns';Assert-TransportOneSend 'Changed source kind'
 Reset-Transport 'v2-generating-reset' @((New-TransportV2 'v2-generating-reset'))
 $script:transportMutation={$script:transportGenerating=($script:transportReads -eq 3)}
 $null=Invoke-Transport;Assert-Transport ($script:transportReads -eq 6) 'Generating transition resets otherwise stable complete V2 response'
 Reset-Transport 'v2-input-reset' @((New-TransportV2 'v2-input-reset'))
 $script:transportMutation={$script:transportHeldInput=if($script:transportReads -eq 3){'unsent draft'}else{''}}
 $null=Invoke-Transport;Assert-Transport ($script:transportReads -eq 6) 'Nonempty composer transition resets otherwise stable complete V2 response'

 $old=New-TransportV2 'v2-old-nonce';Reset-Transport 'v2-old-nonce' @() @($old)
 Assert-TransportRejected {Invoke-Transport} 'RESPONSE_INVALID' 'Current nonce in baseline V2 frames is never sent again'
 Assert-Transport ($script:transportSends -eq 0 -and $script:transportInserts -eq 0 -and -not [IO.File]::Exists((Get-AgentCopilotAttemptPath $transportTemp 'v2-old-nonce'))) 'Used baseline nonce rejects before input or durable attempt'
 $old=New-TransportV2 'v2-old-body';$new=New-TransportV2 'v2-old-key';$new.key=$old.key;Reset-Transport 'v2-old-key' @($new) @($old)
 Assert-TransportRejected {Invoke-Transport} 'RESPONSE_TIMEOUT' 'Old response key excludes changed V2 body';Assert-TransportOneSend 'Old key timeout'
 $old=New-TransportV2 'v2-old-frames';$duplicate=New-TransportV2 'v2-old-frames';$duplicate.key='new-key-for-old-frames';Reset-Transport 'v2-unseen-current' @($duplicate) @($old)
 Assert-TransportRejected {Invoke-Transport} 'RESPONSE_TIMEOUT' 'Old raw V2 frames are excluded even under a new response key';Assert-TransportOneSend 'Old frames timeout'

 foreach($mode in @('extra-rendered','extra-empty-unknown','generating','input-present','wrong-nonce','missing-footer','third-frame','mixed-text','raw-empty-row','wrong-empty-nonce','legacy-carrier','v1-carrier','rendered-v2')){
  $id='v2-reject-'+$mode;$candidate=New-TransportV2 $id;Reset-Transport $id @($candidate)
  switch($mode){
   'extra-rendered' {$script:transportCandidates+=,[pscustomobject]@{key='unrelated-fresh';text='another fresh answer';source_kind='rendered';collapsed=$false}}
   'extra-empty-unknown' {$script:transportCandidates+=,[pscustomobject]@{key='unknown-fresh';text='';source_kind='unknown';collapsed=$false}}
   'generating' {$script:transportGenerating=$true}
   'input-present' {$script:transportHeldInput='unsent draft'}
   'wrong-nonce' {$candidate.frames[0]=$candidate.frames[0].Replace($id,'different-request')}
   'missing-footer' {$candidate.frames[1]=$candidate.frames[1].Replace("`nAGENT_END_"+$id,'')}
   'third-frame' {$candidate.frames+=,'unexpected frame'}
   'mixed-text' {$candidate.text='extra text outside frames'}
   'raw-empty-row' {$candidate.frames[1]=$candidate.frames[1].Replace('AGENT_EMPTY_V2 '+$id,'')}
   'wrong-empty-nonce' {$candidate.frames[1]=$candidate.frames[1].Replace('AGENT_EMPTY_V2 '+$id,'AGENT_EMPTY_V2 another-request')}
   'legacy-carrier' {$raw=ConvertTo-Json -InputObject ([ordered]@{request_id=$id;state='DONE';message='Done';robin='';artifacts=@()}) -Compress;$script:transportCandidates=@([pscustomobject]@{key='legacy-'+$id;text=($raw+"`nAGENT_END_"+$id);source_kind='fenced_plaintext';collapsed=$false})}
   'v1-carrier' {$script:transportCandidates=@(New-TransportV1 $id)}
   'rendered-v2' {$candidate.source_kind='rendered';$candidate.text=$candidate.frames -join "`n"}
  }
  $prefix=if($mode -cin @('generating','input-present')){'RESPONSE_TIMEOUT'}else{'RESPONSE_INVALID'}
  Assert-TransportRejected {Invoke-Transport} $prefix ('Requested V2 rejects '+$mode);Assert-TransportOneSend $mode
  Assert-TransportRejected {Invoke-Transport} 'RESPONSE_INVALID' ('Rejected '+$mode+' cannot replay');Assert-TransportOneSend ($mode+' replay')
 }
 Reset-Transport 'v1-reject-v2' @((New-TransportV2 'v1-reject-v2'))
 Assert-TransportRejected {Invoke-Transport -OmitTransport} 'RESPONSE_INVALID' 'Default V1 request rejects unsolicited V2 carrier';Assert-TransportOneSend 'V1 carrier mismatch'
 $v1=New-TransportV1 'v1-compatible';Reset-Transport 'v1-compatible' @($v1)
 Assert-Transport ((Invoke-Transport -OmitTransport) -ceq $v1.expected_raw -and $script:transportReads -eq 3) 'Existing folded V1 frames preserve exact raw JSON and three stable reads';Assert-TransportOneSend 'V1 compatible'
 Reset-Transport 'v1-boundary-reset' @((New-TransportV1 'v1-boundary-reset' 50))
 $script:transportMutation={if($script:transportReads -eq 3){$script:transportCandidates=@(New-TransportV1 'v1-boundary-reset' 51)}}
 $null=Invoke-Transport -OmitTransport;Assert-Transport ($script:transportReads -eq 5) 'Existing V1 raw part boundary change continues to reset three-read stability';Assert-TransportOneSend 'V1 boundary reset'
 $legacyRaw='{"request_id":"v1-legacy","value":"old supported carrier"}';Reset-Transport 'v1-legacy' @([pscustomobject]@{key='legacy';text=($legacyRaw+"`nAGENT_END_v1-legacy");source_kind='fenced_plaintext';collapsed=$false})
 Assert-Transport ((Invoke-Transport -OmitTransport) -ceq $legacyRaw -and $script:transportReads -eq 3) 'Default V1 preserves supported complete legacy fence behavior';Assert-TransportOneSend 'V1 legacy'
 Reset-Transport 'v2-uncertain-send' @((New-TransportV2 'v2-uncertain-send'));$script:transportSendUncertain=$true
 Assert-TransportRejected {Invoke-Transport} 'CDP_UNAVAILABLE' 'Uncertain V2 send fails once before response polling';Assert-TransportOneSend 'Uncertain V2 send'
 Assert-Transport ($script:transportReads -eq 0) 'Unacknowledged send does not begin response polling'
 Assert-TransportRejected {Invoke-Transport} 'RESPONSE_INVALID' 'Uncertain send is never retried';Assert-TransportOneSend 'Uncertain send replay'
 foreach($at in @(1,3)){
  $id='v2-cancel-read-'+$at;Reset-Transport $id @((New-TransportV2 $id));$script:transportCancel=Join-Path $transportTemp ($id+'.cancel');$script:transportCancelAt=$at
  Assert-TransportRejected {Invoke-Transport} 'CANCELLED' ('Cancellation during response read '+$at+' prevents acceptance');Assert-TransportOneSend ('Cancellation read '+$at)
  Assert-Transport ($script:transportReads -eq $at) ('Cancellation read '+$at+' causes no further response snapshot')
 }
 Reset-Transport 'v2-final-owner-loss' @((New-TransportV2 'v2-final-owner-loss'));$script:transportLoseOwnershipAt=3
 Assert-TransportRejected {Invoke-Transport} 'CDP_UNAVAILABLE' 'Ownership loss after the final stable snapshot prevents acceptance';Assert-TransportOneSend 'Final ownership loss'
 Assert-Transport ($script:transportReads -eq 3) 'Final ownership loss does not reread or retry the response'
 Reset-Transport 'v2-final-deadline' @((New-TransportV2 'v2-final-deadline'));$script:transportDelayAtRead=3
 Assert-TransportRejected {Invoke-Transport} 'RESPONSE_TIMEOUT' 'Actual deadline expiry within the final stable snapshot prevents acceptance';Assert-TransportOneSend 'Final deadline expiry'
 Assert-Transport ($script:transportReads -eq 3) 'Final deadline expiry does not reread or retry the response'
 Assert-Transport ($script:transportConnects -eq $script:transportDisposed) 'Every synthetic socket is disposed after accepted, rejected, cancelled and uncertain attempts'
 Assert-Transport ((Get-FileHash -LiteralPath $transportSource).Hash.ToLowerInvariant() -ceq $transportSourceSha) 'Source remains byte-identical during the complete suite'
 $transportPassed=$true
}catch{$transportFailure=$_.Exception.Message;throw}
finally{
 if($EvidencePath){
  $report=[ordered]@{status=$(if($transportPassed){'passed'}else{'failed'});source_path=$transportSource;source_sha256=$transportSourceSha;checks=$script:transportChecks.ToArray();count=$script:transportChecks.Count;failure=$transportFailure;ps_version=$PSVersionTable.PSVersion.ToString();ps_edition=$PSVersionTable.PSEdition;x64=[Environment]::Is64BitProcess;apartment=[string][Threading.Thread]::CurrentThread.ApartmentState;actual_browser_calls=0;actual_clipboard_calls=0;actual_provider_calls=0;actual_pad_calls=0;utc=[DateTime]::UtcNow.ToString('o')}
  $output=[IO.Path]::GetFullPath($EvidencePath);$bytes=[Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $report -Depth 10));$stream=[IO.File]::Open($output,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
 }
 # Verify a unique direct child of the actual temp root before a native one-shell cleanup.
 if([IO.Directory]::Exists($transportTemp)){
  $resolved=[IO.Path]::GetFullPath($transportTemp);$tempRoot=([IO.Path]::GetFullPath([IO.Path]::GetTempPath())).TrimEnd('\')+'\';$parent=([IO.Path]::GetDirectoryName($resolved)).TrimEnd('\')+'\'
  if($parent -cne $tempRoot -or [IO.Path]::GetFileName($resolved) -cnotmatch '\Aai-prompts-planner-v2-[a-f0-9]{32}\z' -or ((Get-Item -LiteralPath $resolved -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Unsafe transport test cleanup path.'}
  Remove-Item -LiteralPath $resolved -Recurse -Force
 }
}
Write-Output ('Planner V2 transport checks passed: '+$script:transportChecks.Count)
