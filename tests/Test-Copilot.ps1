param([string]$SourcePath=(Join-Path $PSScriptRoot '..\App.ps1'))
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2.0
$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile([IO.Path]::GetFullPath($SourcePath),[ref]$null,[ref]$parseErrors)
if ($parseErrors.Count -gt 0) { throw ('PowerShell parse errors: '+$parseErrors.Count) }
# Load definitions only, never the server/launcher top-level code.
$wanted=@('Get-AgentCopilotConfig','Test-AgentCopilotUrl','Test-AgentCopilotAuthUrl','Test-AgentEdgeCommandLine','Test-AgentCopilotSocketUrl','Read-AgentJsonToken','Test-AgentStrictJson','ConvertFrom-AgentCopilotResponse','Assert-AgentCopilotWait','Enter-AgentCopilotMutex','Get-AgentCopilotAttemptPath','Reserve-AgentCopilotAttempt','Test-AgentCopilotTargetRecord','Write-AgentCopilotTargetRecord','Get-AgentCopilotTarget','Assert-AgentCopilotJobBaseline','Set-AgentCopilotJobSendStarted','Invoke-AgentCopilot','Get-AgentCopilotDomPrelude')
foreach($name in $wanted){
    $definition=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false) | Where-Object Name -eq $name)
    if($definition.Count -ne 1){throw ('Missing or duplicate function: '+$name)}
    . ([scriptblock]::Create($definition[0].Extent.Text))
}
$script:checks=0
function Assert-Case([bool]$Actual,[string]$Name){if(-not $Actual){throw ('FAIL: '+$Name)};$script:checks++}
function Assert-Rejected([scriptblock]$Action,[string]$Prefix,[string]$Name){
    $caught=$false
    try{& $Action | Out-Null}catch{if($_.Exception.Message -notlike ($Prefix+':*')){throw};$caught=$true}
    Assert-Case $caught $Name
}

foreach($url in @('https://m365.cloud.microsoft/chat','https://m365.cloud.microsoft/chat/','https://m365.cloud.microsoft/chat/?auth=2','https://m365.cloud.microsoft/chat/conversation-id')){
    Assert-Case (Test-AgentCopilotUrl $url) ('Trusted URL: '+$url)
}
foreach($url in @('http://m365.cloud.microsoft/chat/','https://m365.cloud.microsoft.evil.test/chat/','https://m365.cloud.microsoft:444/chat/','https://user@m365.cloud.microsoft/chat/','https://m365.cloud.microsoft/chatter','https://m365.cloud.microsoft/chat%2fevil','https://m365.cloud.microsoft/chat/%2e%2e/','https://m365.cloud.microsoft/CHAT/','https://m365.cloud.microsoft\chat/','https://evil.test/?next=https://m365.cloud.microsoft/chat/')){
    Assert-Case (-not (Test-AgentCopilotUrl $url)) ('Reject URL: '+$url)
}
Assert-Case (Test-AgentCopilotAuthUrl 'https://login.microsoftonline.com/common/oauth2/authorize') 'Authentication URL'
Assert-Case (-not (Test-AgentCopilotAuthUrl 'https://login.microsoftonline.com.evil.test/')) 'Authentication lookalike'
Assert-Case (Test-AgentCopilotSocketUrl 'ws://127.0.0.1:9223/devtools/page/abc' 9223 'abc') 'Owned socket'
foreach($url in @('ws://127.0.0.1:9224/devtools/page/abc','ws://localhost:9223/devtools/page/abc','ws://127.0.0.1:9223/devtools/page/other','ws://127.0.0.1:9223/devtools/page/abc?x=1','wss://127.0.0.1:9223/devtools/page/abc','ws://evil.test:9223/devtools/page/abc')){
    Assert-Case (-not (Test-AgentCopilotSocketUrl $url 9223 'abc')) ('Reject socket: '+$url)
}
$profile='C:\Test Profile\edge-profile'
$command='"C:\Program Files\Microsoft\Edge\msedge.exe" --user-data-dir="C:\Test Profile\edge-profile" --remote-debugging-port=9223 about:blank'
Assert-Case (Test-AgentEdgeCommandLine $command $profile 9223) 'Exact profile and port'
Assert-Case (-not (Test-AgentEdgeCommandLine $command ($profile+'-other') 9223)) 'Profile suffix mismatch'
Assert-Case (-not (Test-AgentEdgeCommandLine ($command.Replace('9223','92230')) $profile 9223)) 'Port substring mismatch'
Assert-Case (-not (Test-AgentEdgeCommandLine ($command+' --remote-debugging-port=9224') $profile 9223)) 'Duplicate port switch'
Assert-Case (-not (Test-AgentEdgeCommandLine ($command+' --user-data-dir="C:\Other"') $profile 9223)) 'Duplicate profile switch'
Assert-Case (-not (Test-AgentEdgeCommandLine ('--remote-debugging-port=9223 '+$profile) $profile 9223)) 'Bare profile substring'

foreach($json in @('{"request_id":"r1"}','{"items":[0,-1,1.5,1e+2,true,false,null],"object":{"x":"日本語"}}','{"x":"C:\\folder\\a.txt","newline":"a\nb","quote":"\"","unicode":"\u0031"}')){
    Assert-Case (Test-AgentStrictJson $json) ('Valid JSON: '+$json)
}
foreach($json in @('{"x":1,}','[1,]','{"x":01}','{"x":NaN}','{"x":1} trailing','{"x":1} {"y":2}','{"x":1,"x":2}','{"x":1,"\u0078":2}','{"x":"bad\q"}','{"x":"unterminated}','{"x":/* comment */1}','{"x":[1 2]}')){
    Assert-Case (-not (Test-AgentStrictJson $json)) ('Invalid JSON: '+$json)
}
$json = '{"request_id":"r1","robin":"SET Path TO $''C:\\folder\\file.txt''\nSET Percent TO 100%","data":"日本語、空白  2つ"}'
$complete=$json+"`nAGENT_END_r1"
$actual=ConvertFrom-AgentCopilotResponse $complete 'r1'
Assert-Case ([string]::Equals($actual,$json,[StringComparison]::Ordinal)) 'Response preserves code, percent, whitespace and legitimate backslashes exactly'
Assert-Rejected {ConvertFrom-AgentCopilotResponse $complete 'r2'} 'RESPONSE_INVALID' 'Wrong marker'
Assert-Rejected {ConvertFrom-AgentCopilotResponse ("{"+"`nAGENT_END_r1") 'r1'} 'RESPONSE_INVALID' 'Truncated JSON'
Assert-Rejected {ConvertFrom-AgentCopilotResponse ($json+"`nAGENT_END_r1`nextra") 'r1'} 'RESPONSE_INVALID' 'Trailing output'
Assert-Rejected {ConvertFrom-AgentCopilotResponse ($json+"`nAGENT_END_r1") 'r1' -Collapsed} 'RESPONSE_INVALID' 'Collapsed code'
Assert-Rejected {ConvertFrom-AgentCopilotResponse $complete 'r1' -BaselineTexts @($complete)} 'RESPONSE_INVALID' 'Past turn is never accepted'
Assert-Rejected {ConvertFrom-AgentCopilotResponse ("{`"request_id`":`"other`"}`nAGENT_END_r1") 'r1'} 'RESPONSE_INVALID' 'Wrong JSON request ID'
Assert-Rejected {ConvertFrom-AgentCopilotResponse ('```json'+"`n"+$complete+"`n"+'```') 'r1'} 'RESPONSE_INVALID' 'Markdown fences not repaired'
Assert-Rejected {ConvertFrom-AgentCopilotResponse '申し訳ありません。この依頼には対応できません。' 'r1'} 'REFUSAL' 'Refusal distinct from business output'
Assert-Rejected {ConvertFrom-AgentCopilotResponse '' 'r1'} 'EMPTY_RESPONSE' 'Empty response distinct from success'
Assert-Rejected {Assert-AgentCopilotWait '' ([datetime]::UtcNow.AddSeconds(-1))} 'RESPONSE_TIMEOUT' 'Timeout classification'
$temp=Join-Path ([IO.Path]::GetTempPath()) ('ai-prompts-copilot-tests-'+[guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($temp)|Out-Null
try{
    $cancel=Join-Path $temp 'cancel';[IO.File]::WriteAllText($cancel,'cancel')
    Assert-Case ((Get-AgentCopilotConfig $temp ([pscustomobject]@{})).Port -eq 9223) 'Default port with empty settings'
    Assert-Case ((Get-AgentCopilotConfig $temp @{copilot_port=9333}).Port -eq 9333) 'Explicit port'
    Assert-Rejected {Assert-AgentCopilotWait $cancel ([datetime]::UtcNow.AddSeconds(2))} 'CANCELLED' 'Cancellation classification'
    Assert-Rejected {Enter-AgentCopilotMutex ([pscustomobject]@{Profile=$temp}) $cancel ([datetime]::UtcNow.AddSeconds(2))} 'CANCELLED' 'Mutex acquisition respects cancellation'
    Reserve-AgentCopilotAttempt $temp 'r1'
    Assert-Case ([IO.File]::Exists((Get-AgentCopilotAttemptPath $temp 'r1'))) 'Durable attempt reservation'
    Assert-Rejected {Reserve-AgentCopilotAttempt $temp 'r1'} 'RESPONSE_INVALID' 'Uncertain or completed attempt cannot be replayed'
    Assert-Rejected {Get-AgentCopilotAttemptPath $temp '..\escape'} 'RESPONSE_INVALID' 'Attempt ID path traversal rejected'
}finally{
    [IO.File]::Delete((Join-Path $temp 'cancel'))
    if([IO.File]::Exists((Join-Path $temp 'data\copilot-attempts\r1.attempt'))){[IO.File]::Delete((Join-Path $temp 'data\copilot-attempts\r1.attempt'))}
    if([IO.Directory]::Exists((Join-Path $temp 'data\copilot-attempts'))){[IO.Directory]::Delete((Join-Path $temp 'data\copilot-attempts'))}
    if([IO.Directory]::Exists((Join-Path $temp 'data'))){[IO.Directory]::Delete((Join-Path $temp 'data'))}
    [IO.Directory]::Delete($temp)
}
# CDP test doubles exercise the production target selection path; no Edge/network is used.
$jobTemp=Join-Path ([IO.Path]::GetTempPath()) ('ai-prompts-copilot-jobtests-'+[guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($jobTemp)|Out-Null
function Assert-AgentCopilotOwnership { param($Config) }
function New-TestCopilotPage([string]$Id){ return [pscustomobject]@{id=$Id;type='page';url='https://m365.cloud.microsoft/chat/';webSocketDebuggerUrl=('ws://127.0.0.1:9223/devtools/page/'+$Id)} }
$script:mockPages=@((New-TestCopilotPage 'legacy'));$script:createdTargets=0;$script:nextTargetId='job-a'
function Invoke-AgentCopilotHttp {
    param($Config,[string]$Path,[string]$Method='GET')
    if($Path -ceq '/json/list'){return $script:mockPages}
    if($Path.StartsWith('/json/new?') -and $Method -ceq 'PUT'){
        $script:createdTargets++
        $page=New-TestCopilotPage $script:nextTargetId
        if(@($script:mockPages | Where-Object id -ceq $page.id).Count -eq 0){$script:mockPages+=@($page)}
        return $page
    }
    throw ('Unexpected CDP operation in target test: '+$Path)
}
try{
    $signin=Get-AgentCopilotConfig $jobTemp @{}
    $legacy=[pscustomobject]@{id='legacy';port=$signin.Port;profile=$signin.Profile}
    Write-AgentCopilotTargetRecord $signin $legacy
    $jobA=Get-AgentCopilotConfig $jobTemp @{} ('a'*32)
    $jobB=Get-AgentCopilotConfig $jobTemp @{} ('b'*32)
    Assert-Case ($jobA.TargetPath -cne $signin.TargetPath -and $jobA.TargetPath -cne $jobB.TargetPath) 'Each job has its own target record, separate from sign-in'
    Assert-Case (-not (Test-AgentCopilotTargetRecord $jobA $legacy)) 'Legacy global target record cannot authorize a job send'
    $targetA=Get-AgentCopilotTarget $jobA -Create
    Assert-Case ($targetA.id -ceq 'job-a' -and $targetA.agent_first_job_send -and $script:createdTargets -eq 1) 'First job creates a new target despite existing legacy tab'
    Assert-Case ((Get-AgentCopilotTarget $jobA -Create).id -ceq 'job-a' -and $script:createdTargets -eq 1) 'Planner and AiCall in same job reuse its target'
    $script:nextTargetId='job-b';$targetB=Get-AgentCopilotTarget $jobB -Create
    Assert-Case ($targetB.id -ceq 'job-b' -and $script:createdTargets -eq 2) 'Next job creates a different target'
    Assert-Case (@($script:mockPages | Where-Object id -in @('legacy','job-a')).Count -eq 2) 'Previous tabs remain open'
    $empty=[pscustomobject]@{inputCount=1;inputText='';generating=$false;assistants=@()}
    Assert-AgentCopilotJobBaseline $targetA $empty
    Assert-Case $true 'Empty first-turn baseline accepted'
    $old=[pscustomobject]@{inputCount=1;inputText='';generating=$false;assistants=@([pscustomobject]@{text='Old assistant reply';collapsed=$false})}
    Assert-Rejected {Assert-AgentCopilotJobBaseline $targetA $old} 'RESPONSE_INVALID' 'Restored assistant history rejected before first input'
    Assert-Rejected {Assert-AgentCopilotJobBaseline $targetA $old -AfterInput} 'RESPONSE_INVALID' 'History arriving during input rejected before send'
    Assert-Rejected {Assert-AgentCopilotJobBaseline $targetA ([pscustomobject]@{inputText='';assistants=@([pscustomobject]@{text=''})})} 'RESPONSE_INVALID' 'Empty assistant placeholder also rejects new conversation claim'
    Assert-Rejected {Assert-AgentCopilotJobBaseline $targetA ([pscustomobject]@{inputText='old draft';assistants=@()})} 'RESPONSE_INVALID' 'Restored draft is not cleared and overwritten'
    Set-AgentCopilotJobSendStarted $jobA $targetA
    $continued=Get-AgentCopilotTarget $jobA
    Assert-Case (-not $continued.agent_first_job_send) 'First send state persists for same-job continuation'
    Assert-AgentCopilotJobBaseline $continued $old
    Assert-Case $true 'Same-job history remains available after first send'
    $migrated=Get-AgentCopilotConfig $jobTemp @{} ('d'*32)
    Write-AgentCopilotTargetRecord $migrated $legacy
    Assert-Rejected {Get-AgentCopilotTarget $migrated -Create} 'CDP_UNAVAILABLE' 'Copying old global record into job directory cannot adopt it'
    $script:nextTargetId='legacy';$badCreate=Get-AgentCopilotConfig $jobTemp @{} ('e'*32)
    Assert-Rejected {Get-AgentCopilotTarget $badCreate -Create} 'CDP_UNAVAILABLE' 'CDP new-target response cannot bind an existing target'
    Assert-Case (-not [IO.File]::Exists($badCreate.TargetPath)) 'Rejected existing target is not persisted as a job target'
    $script:mockPages=@($script:mockPages | Where-Object id -cne 'job-a')
    Assert-Rejected {Get-AgentCopilotTarget $jobA -Create} 'CDP_UNAVAILABLE' 'Missing job target never falls back to another conversation'
    # Exercise Invoke itself and confirm the first-turn guard precedes all input/send commands.
    $script:nextTargetId='job-c';$script:evalCalls=0
    function Connect-AgentCopilotSocket {param($Config,$Target);$s=[pscustomobject]@{};$s|Add-Member -MemberType ScriptMethod -Name Dispose -Value {};return $s}
    function Get-AgentCopilotSnapshot {param($Socket,$CancelPath,$Deadline);return [pscustomobject]@{inputCount=1;inputText='';generating=$false;assistants=@([pscustomobject]@{text='Restored old conversation';collapsed=$false})}}
    function Invoke-AgentCopilotEval {param($Socket,$Expression,$CancelPath,$Deadline);$script:evalCalls++;throw 'Unexpected input/send command.'}
    Assert-Rejected {Invoke-AgentCopilot -Prompt 'Test request' -RequestId 'r-stale' -JobId ('c'*32) -Settings @{} -HomePath $jobTemp -TimeoutSeconds 5} 'RESPONSE_INVALID' 'Real invocation rejects restored conversation on newly created target'
    Assert-Case ($script:evalCalls -eq 0 -and -not [IO.File]::Exists((Get-AgentCopilotAttemptPath $jobTemp 'r-stale'))) 'Rejected history produces neither input/send nor an attempt reservation'
    $script:nextTargetId='job-f';$script:mockInput=''
    function Get-AgentCopilotSnapshot {param($Socket,$CancelPath,$Deadline);return [pscustomobject]@{inputCount=1;inputText=$script:mockInput;generating=$false;assistants=@()}}
    function Invoke-AgentCopilotCdp {param($Socket,$Method,$Params,$CancelPath,$Deadline);if($Method -ceq 'Input.insertText'){$script:mockInput=$Params.text}}
    function Invoke-AgentCopilotEval {param($Socket,$Expression,$CancelPath,$Deadline);if($Expression.Contains('sends[0].click()')){throw 'CDP_UNAVAILABLE: Simulated uncertain send.'};return $true}
    Assert-Rejected {Invoke-AgentCopilot -Prompt 'Test request' -RequestId 'r-uncertain' -JobId ('f'*32) -Settings @{} -HomePath $jobTemp -TimeoutSeconds 5} 'CDP_UNAVAILABLE' 'Uncertain first send fails without retry'
    $uncertainConfig=Get-AgentCopilotConfig $jobTemp @{} ('f'*32)
    $uncertainRecord=[IO.File]::ReadAllText($uncertainConfig.TargetPath,[Text.Encoding]::UTF8)|ConvertFrom-Json
    Assert-Case (-not $uncertainRecord.has_sent -and [IO.File]::Exists((Get-AgentCopilotAttemptPath $jobTemp 'r-uncertain'))) 'Uncertain send preserves fresh-history guard and durable no-replay reservation'
}finally{
    $resolvedJobTemp=[IO.Path]::GetFullPath($jobTemp)
    $expectedParent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')+'\'
    if(-not $resolvedJobTemp.StartsWith($expectedParent,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($resolvedJobTemp) -notmatch '^ai-prompts-copilot-jobtests-[0-9a-f]{32}$'){throw 'Unsafe test cleanup path.'}
    Remove-Item -LiteralPath $resolvedJobTemp -Recurse -Force
}
Write-Output ('PASS: '+$script:checks+' Copilot contract checks. Live M365/Edge integration was not exercised.')
