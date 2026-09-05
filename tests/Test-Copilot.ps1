param([string]$SourcePath=(Join-Path $PSScriptRoot '..\App.ps1'))
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2.0
$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile([IO.Path]::GetFullPath($SourcePath),[ref]$null,[ref]$parseErrors)
if ($parseErrors.Count -gt 0) { throw ('PowerShell parse errors: '+$parseErrors.Count) }
# Load definitions only, never the server/launcher top-level code.
$wanted=@('Get-AgentCopilotConfig','Test-AgentCopilotUrl','Test-AgentCopilotAuthUrl','Test-AgentEdgeCommandLine','Test-AgentCopilotSocketUrl','Read-AgentJsonToken','Test-AgentStrictJson','ConvertFrom-AgentCopilotResponse','Assert-AgentCopilotWait','Enter-AgentCopilotMutex','Get-AgentCopilotAttemptPath','Reserve-AgentCopilotAttempt','Test-AgentCopilotTargetRecord','Write-AgentCopilotTargetRecord','Get-AgentCopilotTarget','Assert-AgentCopilotJobBaseline','Set-AgentCopilotJobSendStarted','Invoke-AgentCopilot','Get-AgentCopilotDomPrelude','Close-AgentCopilotLaunchTab','Open-AgentCopilot')
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
    # First browser launch has a nonce blank plus any unrelated user/extension tabs.
    $launchConfig=Get-AgentCopilotConfig (Join-Path $jobTemp 'launch') @{}
    $launchUrl='about:blank#ai-prompts-launch-'+('1'*32)
    $ownedBlank=New-TestCopilotPage 'app-launch';$ownedBlank.url=$launchUrl
    $userBlank=New-TestCopilotPage 'user-blank';$userBlank.url='about:blank'
    $extensionTab=New-TestCopilotPage 'extension-welcome';$extensionTab.url='chrome-extension://example/welcome.html'
    $script:mockPages=@($ownedBlank,$userBlank,$extensionTab);$script:nextTargetId='launch-copilot'
    $activeSignin=Get-AgentCopilotTarget $launchConfig -Create -AllowAuthentication
    $script:closeCalls=0;$script:launchCloseMode='close';$script:expectedLaunchUrl=$launchUrl
    function Connect-AgentCopilotSocket {param($Config,$Target);$s=[pscustomobject]@{target_id=$Target.id};$s|Add-Member -MemberType ScriptMethod -Name Dispose -Value {};return $s}
    function Invoke-AgentCopilotCdp {
        param($Socket,$Method,$Params,$CancelPath,$Deadline)
        if($Method -cne 'Runtime.evaluate' -or -not $Params.expression.Contains('if(location.href!==') -or -not $Params.expression.Contains(($script:expectedLaunchUrl|ConvertTo-Json -Compress)) -or -not $Params.expression.Contains('window.close()')){throw 'Unexpected or unguarded close operation.'}
        $script:closeCalls++
        $current=@($script:mockPages | Where-Object id -ceq $Socket.target_id)[0]
        if($script:launchCloseMode -ceq 'changed'){$current.url='https://example.test/user-page';return [pscustomobject]@{result=[pscustomobject]@{value=$false}}}
        if($script:launchCloseMode -ceq 'uncertain'){throw 'CDP_UNAVAILABLE: simulated uncertain close'}
        $script:mockPages=@($script:mockPages | Where-Object id -cne $Socket.target_id)
        if($script:launchCloseMode -ceq 'closed-before-ack'){throw 'CDP_UNAVAILABLE: socket closed before acknowledgement'}
        return [pscustomobject]@{result=[pscustomobject]@{value=$true}}
    }
    Close-AgentCopilotLaunchTab $launchConfig $launchUrl $activeSignin ([datetime]::UtcNow.AddSeconds(5))
    Assert-Case ($script:closeCalls -eq 1 -and @($script:mockPages | Where-Object id -ceq 'app-launch').Count -eq 0) 'First launch removes only its nonce blank after Copilot is ready'
    Assert-Case (@($script:mockPages | Where-Object { $_.id -ceq 'user-blank' -and $_.url -ceq 'about:blank' }).Count -eq 1) 'Existing user about blank is untouched'
    Assert-Case (@($script:mockPages | Where-Object id -ceq 'extension-welcome').Count -eq 1) 'Extension welcome tab is untouched'
    Assert-Case ((Get-AgentCopilotTarget $launchConfig -Create -AllowAuthentication).id -ceq 'launch-copilot') 'Sign-in target remains recorded and reusable'
    Assert-Rejected {Close-AgentCopilotLaunchTab $launchConfig 'about:blank' $activeSignin ([datetime]::UtcNow.AddSeconds(5))} 'CDP_UNAVAILABLE' 'Plain blank cannot be claimed as app-owned'
    $ownedBlank=New-TestCopilotPage 'app-launch';$ownedBlank.url=$launchUrl;$script:mockPages+=@($ownedBlank)
    $duplicate=New-TestCopilotPage 'duplicate-nonce';$duplicate.url=$launchUrl;$script:mockPages+=@($duplicate)
    $beforeClose=$script:closeCalls
    Assert-Rejected {Close-AgentCopilotLaunchTab $launchConfig $launchUrl $activeSignin ([datetime]::UtcNow.AddSeconds(5))} 'CDP_UNAVAILABLE' 'Ambiguous nonce match fails closed'
    Assert-Case ($script:closeCalls -eq $beforeClose) 'Ambiguity sends no close command'
    $script:mockPages=@($script:mockPages | Where-Object id -cne 'duplicate-nonce');$script:launchCloseMode='changed'
    Assert-Rejected {Close-AgentCopilotLaunchTab $launchConfig $launchUrl $activeSignin ([datetime]::UtcNow.AddSeconds(5))} 'CDP_UNAVAILABLE' 'Tab navigated after discovery is not closed'
    Assert-Case (@($script:mockPages | Where-Object { $_.id -ceq 'app-launch' -and $_.url -ceq 'https://example.test/user-page' }).Count -eq 1) 'Changed tab content is preserved'
    @($script:mockPages | Where-Object id -ceq 'app-launch')[0].url=$launchUrl
    $script:launchCloseMode='uncertain';$beforeClose=$script:closeCalls
    Assert-Rejected {Close-AgentCopilotLaunchTab $launchConfig $launchUrl $activeSignin ([datetime]::UtcNow.AddSeconds(5))} 'CDP_UNAVAILABLE' 'Uncertain close remains a failure while the exact target exists'
    Assert-Case ($script:closeCalls -eq ($beforeClose+1)) 'Uncertain close is never retried'
    $script:launchCloseMode='closed-before-ack'
    Close-AgentCopilotLaunchTab $launchConfig $launchUrl $activeSignin ([datetime]::UtcNow.AddSeconds(5))
    Assert-Case (@($script:mockPages | Where-Object id -ceq 'app-launch').Count -eq 0) 'Socket close is accepted only after exact target disappearance is confirmed'
    # Exercise the real Open orchestrator. Every process, listener and CDP boundary is mocked;
    # the inert temporary executable is only an existence fixture and is never executed.
    $fakeProgramFiles=Join-Path $jobTemp 'program-files-fixture'
    $script:fakeEdgePath=Join-Path $fakeProgramFiles 'Microsoft\Edge\Application\msedge.exe'
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($script:fakeEdgePath))|Out-Null
    [IO.File]::WriteAllBytes($script:fakeEdgePath,[byte[]]@())
    $savedProgramFiles86=${env:ProgramFiles(x86)}
    function Enter-AgentCopilotMutex {
        param($Config,$CancelPath,$Deadline)
        $script:openEvents.Add('lock')
        $m=[pscustomobject]@{}
        $m|Add-Member -MemberType ScriptMethod -Name ReleaseMutex -Value {$script:openEvents.Add('unlock')}
        $m|Add-Member -MemberType ScriptMethod -Name Dispose -Value {$script:openEvents.Add('mutex-dispose')}
        return $m
    }
    function Test-AgentCopilotOwnership {
        param($Config)
        $script:openEvents.Add(('ownership:'+([string]$script:openOwned)))
        return $script:openOwned
    }
    function Get-NetTCPConnection {
        param($State,$LocalPort,$ErrorAction)
        if($State -cne 'Listen' -or $LocalPort -ne 9223){throw 'Unexpected listener query.'}
        $script:openEvents.Add('listener-check')
        return @()
    }
    function Start-Process {
        param($FilePath,$ArgumentList,$WindowStyle)
        if($FilePath -cne $script:fakeEdgePath -or $WindowStyle -cne 'Normal'){throw 'Unexpected process launch.'}
        $script:openEvents.Add('launch');$script:openLaunchCalls++
        $script:openArguments=[string]$ArgumentList
        $nonceMatches=[regex]::Matches($script:openArguments,'(?:^|\s)(about:blank#ai-prompts-launch-[0-9a-f]{32})(?=\s|$)')
        if($nonceMatches.Count -ne 1){throw 'Launch must contain one unique app nonce URL.'}
        $script:openLaunchUrl=$nonceMatches[0].Groups[1].Value
        $script:openOwned=$true
    }
    function Get-AgentCopilotTarget {
        param($Config,[switch]$Create,[switch]$AllowAuthentication)
        if(-not $script:openOwned -or -not $Create -or -not $AllowAuthentication -or $Config.JobId){throw 'Target retrieval must follow ownership and retain sign-in semantics.'}
        $script:openEvents.Add('target')
        return (New-TestCopilotPage 'orchestration-copilot')
    }
    function Connect-AgentCopilotSocket {
        param($Config,$Target)
        if($Target.id -cne 'orchestration-copilot'){throw 'Unexpected foreground target.'}
        $script:openEvents.Add('connect')
        $s=[pscustomobject]@{}
        $s|Add-Member -MemberType ScriptMethod -Name Dispose -Value {$script:openEvents.Add('socket-dispose')}
        return $s
    }
    function Invoke-AgentCopilotCdp {
        param($Socket,$Method,$Params,$CancelPath,$Deadline)
        if($Method -cne 'Page.bringToFront'){throw 'Open must only bring the recorded Copilot tab forward.'}
        $script:openEvents.Add('bring-to-front')
        return [pscustomobject]@{}
    }
    function Close-AgentCopilotLaunchTab {
        param($Config,$LaunchUrl,$ActiveTarget,$Deadline)
        if($LaunchUrl -cne $script:openLaunchUrl -or $ActiveTarget.id -cne 'orchestration-copilot'){throw 'Cleanup must receive the exact launched nonce and confirmed Copilot target.'}
        $script:openEvents.Add('cleanup');$script:openCleanupCalls++
    }
    try {
        ${env:ProgramFiles(x86)}=$fakeProgramFiles
        $firstLaunchUrl=''
        foreach($launchCase in @(1,2)){
            $script:openEvents=New-Object 'Collections.Generic.List[string]'
            $script:openOwned=$false;$script:openLaunchCalls=0;$script:openCleanupCalls=0;$script:openLaunchUrl='';$script:openArguments=''
            $opened=Open-AgentCopilot -HomePath (Join-Path $jobTemp 'open-orchestration') -Settings @{}
            Assert-Case ($opened.status -ceq 'opened' -and $opened.target_id -ceq 'orchestration-copilot') ('Real Open first-launch result '+$launchCase)
            Assert-Case ($script:openLaunchCalls -eq 1 -and $script:openCleanupCalls -eq 1) ('Real Open launches once and cleans up once '+$launchCase)
            Assert-Case ($script:openEvents.IndexOf('ownership:True') -gt $script:openEvents.IndexOf('launch') -and $script:openEvents.IndexOf('target') -gt $script:openEvents.IndexOf('ownership:True')) ('Real Open establishes ownership before target retrieval '+$launchCase)
            Assert-Case ($script:openEvents.IndexOf('target') -lt $script:openEvents.IndexOf('bring-to-front') -and $script:openEvents.IndexOf('bring-to-front') -lt $script:openEvents.IndexOf('cleanup')) ('Real Open verifies and foregrounds Copilot before nonce cleanup '+$launchCase)
            Assert-Case ($script:openArguments.Contains('--remote-debugging-address=127.0.0.1') -and $script:openArguments.Contains('--remote-debugging-port=9223') -and $script:openArguments.Contains($script:openLaunchUrl)) ('Real Open passes dedicated listener and exact cleanup nonce '+$launchCase)
            if($launchCase -eq 1){$firstLaunchUrl=$script:openLaunchUrl}else{Assert-Case ($script:openLaunchUrl -cne $firstLaunchUrl) 'Separate Open launches generate different nonce URLs'}
        }
        $script:openEvents=New-Object 'Collections.Generic.List[string]'
        $script:openOwned=$true;$script:openLaunchCalls=0;$script:openCleanupCalls=0;$script:openLaunchUrl='';$script:openArguments=''
        $opened=Open-AgentCopilot -HomePath (Join-Path $jobTemp 'open-orchestration') -Settings @{}
        Assert-Case ($script:openLaunchCalls -eq 0 -and $script:openCleanupCalls -eq 0 -and -not $script:openEvents.Contains('listener-check')) 'Already-owned Open performs neither process launch nor blank cleanup'
        Assert-Case ($opened.target_id -ceq 'orchestration-copilot' -and $script:openEvents.IndexOf('target') -ge 0 -and $script:openEvents.IndexOf('bring-to-front') -gt $script:openEvents.IndexOf('target')) 'Already-owned Open retrieves and foregrounds the recorded sign-in target'
    } finally { ${env:ProgramFiles(x86)}=$savedProgramFiles86 }
}finally{
    $resolvedJobTemp=[IO.Path]::GetFullPath($jobTemp)
    $expectedParent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')+'\'
    if(-not $resolvedJobTemp.StartsWith($expectedParent,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($resolvedJobTemp) -notmatch '^ai-prompts-copilot-jobtests-[0-9a-f]{32}$'){throw 'Unsafe test cleanup path.'}
    Remove-Item -LiteralPath $resolvedJobTemp -Recurse -Force
}
Write-Output ('PASS: '+$script:checks+' Copilot contract checks. Live M365/Edge integration was not exercised.')
