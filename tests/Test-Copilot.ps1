param([string]$SourcePath=(Join-Path $PSScriptRoot '..\App.ps1'))
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2.0
$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile([IO.Path]::GetFullPath($SourcePath),[ref]$null,[ref]$parseErrors)
if ($parseErrors.Count -gt 0) { throw ('PowerShell parse errors: '+$parseErrors.Count) }
# Load definitions only, never the server/launcher top-level code.
$wanted=@('Get-AgentProperty','Get-AgentFullPath','Assert-AgentPathUnder','Assert-AgentNoReparse','Get-AgentHash','Get-AgentVerifiedPriorArtifacts','ConvertTo-AgentRobinLiteral','ConvertFrom-AgentRobinLiteral','Assert-AgentPadPath','Test-AgentRobin','Get-AgentCopilotConfig','Test-AgentCopilotUrl','Test-AgentCopilotAuthUrl','Test-AgentEdgeCommandLine','Test-AgentCopilotSocketUrl','Read-AgentJsonToken','Test-AgentStrictJson','ConvertFrom-AgentCopilotResponse','Assert-AgentCopilotWait','Enter-AgentCopilotMutex','Get-AgentCopilotAttemptPath','Reserve-AgentCopilotAttempt','Test-AgentCopilotTargetRecord','Write-AgentCopilotTargetRecord','Get-AgentCopilotTarget','Assert-AgentCopilotJobBaseline','Set-AgentCopilotJobSendStarted','Wait-AgentCopilotInputReady','Invoke-AgentCopilotExpand','Invoke-AgentCopilot','Get-AgentCopilotDomPrelude','Close-AgentCopilotLaunchTab','Open-AgentCopilot')
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
# This is a complete Robin flow assembled from the supported ReadText/WriteText
# forms in pad-robin-prompts.md.  Test-AgentRobin accepts it before it is put in
# the response frame, so the parser test cannot pass with a malformed-only fake.
$robinTemp=Join-Path ([IO.Path]::GetTempPath()) ('ai-prompts-copilot-robin-'+[guid]::NewGuid().ToString('N'))
try{
$robinRun=Join-Path $robinTemp 'run';$robinTarget=Join-Path $robinTemp 'target';$robinArtifacts=Join-Path $robinRun 'artifacts'
[IO.Directory]::CreateDirectory($robinArtifacts)|Out-Null
[IO.Directory]::CreateDirectory($robinTarget)|Out-Null
$robinInput=Join-Path $robinTarget 'input.txt'
[IO.File]::WriteAllText($robinInput,"  日本語 100% \\path\\raw.txt `"引用`"  `r`n")
$robinJob=[pscustomobject]@{target=$robinTarget;observed_artifacts=@()}
$robinRead='File.ReadTextFromFile.ReadText File: '+(ConvertTo-AgentRobinLiteral $robinInput)+' Encoding: File.TextFileEncoding.UTF8 Content=> FileContents'
$robinValue='  引用: "日本語" O''Brien C:\path\raw  '
$robinSet='SET Quote TO '+(ConvertTo-AgentRobinLiteral $robinValue)
$robinVariable='$'+"'''%FileContents%'''"
$robinWrite='File.WriteText File: '+(ConvertTo-AgentRobinLiteral (Join-Path $robinArtifacts 'log.txt'))+' TextToWrite: '+$robinVariable+' AppendNewLine: True IfFileExists: File.IfFileExists.Append Encoding: File.FileEncoding.UTF8'
$robinQuoteWrite='File.WriteText File: '+(ConvertTo-AgentRobinLiteral (Join-Path $robinArtifacts 'quoted.txt'))+' TextToWrite: Quote AppendNewLine: True IfFileExists: File.IfFileExists.Append Encoding: File.FileEncoding.UTF8'
$robinFixture=@($robinRead,$robinSet,$robinWrite,$robinQuoteWrite) -join "`r`n"
$robinOutputs=@(Test-AgentRobin -Robin $robinFixture -RunDirectory $robinRun -Job $robinJob)
Assert-Case ($robinOutputs.Count -eq 2) 'Complete ReadText/WriteText Robin fixture passes the production validator'
$robinJson=([ordered]@{request_id='r-full-robin';robin=$robinFixture}|ConvertTo-Json -Compress)
$robinFramed="`r`n`t"+$robinJson+"`r`nAGENT_END_r-full-robin`r`n  "
$robinActualJson=ConvertFrom-AgentCopilotResponse $robinFramed 'r-full-robin'
$robinDecoded=ConvertFrom-Json -InputObject $robinActualJson
Assert-Case ([string]::Equals([string]$robinDecoded.robin,$robinFixture,[StringComparison]::Ordinal)) 'Complete Robin preserves decoded Japanese, quotes, apostrophe, backslashes, percent variable reference, CRLF and text whitespace'
Assert-Case ($robinValue.StartsWith('  ') -and $robinValue.EndsWith('  ') -and $robinFixture.Contains("`r`n")) 'Complete Robin fixture contains leading/trailing text whitespace and multiple lines'
# Stay below the production Robin line/character limits while exercising a
# response large enough to catch accidental truncation or character assumptions.
# Build the largest fixture that fits this machine's actual temporary path.
$longRobinLimit=62000
$longRobinLines=@($robinRead)
for($longIndex=1;$longIndex -le 249;$longIndex++){
    $longPath=Join-Path $robinArtifacts ('long-{0:D3}.txt' -f $longIndex)
    $longLine='File.WriteText File: '+(ConvertTo-AgentRobinLiteral $longPath)+' TextToWrite: '+$robinVariable+' AppendNewLine: True IfFileExists: File.IfFileExists.Append Encoding: File.FileEncoding.UTF8'
    $candidate=($longRobinLines+@($longLine))-join "`r`n"
    if($candidate.Length -ge $longRobinLimit){break}
    $longRobinLines+=@($longLine)
}
$longRobin=$longRobinLines -join "`r`n"
$longOutputs=@(Test-AgentRobin -Robin $longRobin -RunDirectory $robinRun -Job $robinJob)
$longWriteCount=$longRobinLines.Count-1
Assert-Case ($longWriteCount -eq $longOutputs.Count -and $longWriteCount -ge 120 -and $longRobin.Length -lt 64000 -and @($longRobin -split '\r?\n').Count -le 250) 'Long complete Robin fixture stays within production line and character limits'
$longJson=([ordered]@{request_id='r-long-robin';robin=$longRobin}|ConvertTo-Json -Compress)
Assert-Case ($longJson.Length -gt 40000 -and $longJson.Length -lt 1048576) 'Long complete Robin response stays within the actual strict JSON response limit'
$longFramed="`r`n  "+$longJson+"`r`nAGENT_END_r-long-robin`r`n`t"
$longActualJson=ConvertFrom-AgentCopilotResponse $longFramed 'r-long-robin'
$longDecoded=ConvertFrom-Json -InputObject $longActualJson
Assert-Case ([string]::Equals([string]$longDecoded.robin,$longRobin,[StringComparison]::Ordinal)) 'Long complete Robin response is decoded without truncation'
}finally{
    if(Test-Path -LiteralPath $robinTemp){
        $resolvedRobinTemp=[IO.Path]::GetFullPath($robinTemp).TrimEnd('\')
        $expectedTempRoot=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')+'\'
        $resolvedRobinParent=([IO.Path]::GetDirectoryName($resolvedRobinTemp)).TrimEnd('\')+'\'
        if($resolvedRobinParent -cne $expectedTempRoot -or [IO.Path]::GetFileName($resolvedRobinTemp) -notmatch '^ai-prompts-copilot-robin-[0-9a-f]{32}$') { throw 'Unsafe test cleanup path.' }
        $resolvedRobinItem=Get-Item -LiteralPath $resolvedRobinTemp -Force
        if($resolvedRobinItem.Attributes -band [IO.FileAttributes]::ReparsePoint){ throw 'Unsafe test cleanup reparse point.' }
        Remove-Item -LiteralPath $resolvedRobinTemp -Recurse -Force
    }
}
Assert-Rejected {ConvertFrom-AgentCopilotResponse $complete 'r2'} 'RESPONSE_INVALID' 'Wrong marker'
Assert-Rejected {ConvertFrom-AgentCopilotResponse $json 'r1'} 'RESPONSE_INVALID' 'Complete JSON without its required marker is rejected'
Assert-Rejected {ConvertFrom-AgentCopilotResponse ("{"+"`nAGENT_END_r1") 'r1'} 'RESPONSE_INVALID' 'Truncated JSON'
Assert-Rejected {ConvertFrom-AgentCopilotResponse ("Here is the result:`n"+$complete) 'r1'} 'RESPONSE_INVALID' 'Leading explanation is rejected'
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
    Assert-Case ($script:mockInput.StartsWith("Test request`n`n") -and $script:mockInput.Contains('応答全体は言語ラベル text のコードフェンス1個だけにしてください。') -and $script:mockInput.Contains('フェンス内部は厳密に2行です。')) 'Actual inserted wire prompt requires one text fence containing exactly two logical lines'
    Assert-Case ($script:mockInput.Contains('内部の第1行: 指定された単一の JSON オブジェクト。') -and $script:mockInput.Contains('request_id は "r-uncertain"') -and $script:mockInput.Contains('改行・引用符・バックスラッシュは JSON の規則でエスケープしてください。')) 'Actual inserted wire prompt binds first-line JSON to the current request ID and JSON escaping'
    Assert-Case ($script:mockInput.Contains('内部の第2行: AGENT_END_r-uncertain だけを出力してください。')) 'Actual inserted wire prompt requires only the current nonce marker on the second fenced line'
    Assert-Case ($script:mockInput.Contains('フェンスの外に前置き、説明、別のコードや文字を一切付けないでください。') -and $script:mockInput.Contains('JSON のエスケープ以外に Markdown 用の手作業エスケープを追加しないでください。') -and $script:mockInput -notmatch 'JSON オブジェクトだけを 1 行で返してください|Return only JSON|Return exactly one JSON object|ほかの文字、Markdown、コードフェンス') 'Actual inserted wire prompt forbids outer text and additional Markdown escaping without contradicting fenced transport'
    $uncertainConfig=Get-AgentCopilotConfig $jobTemp @{} ('f'*32)
    $uncertainRecord=[IO.File]::ReadAllText($uncertainConfig.TargetPath,[Text.Encoding]::UTF8)|ConvertFrom-Json
    Assert-Case (-not $uncertainRecord.has_sent -and [IO.File]::Exists((Get-AgentCopilotAttemptPath $jobTemp 'r-uncertain'))) 'Uncertain send preserves fresh-history guard and durable no-replay reservation'
    # Startup busy may recur between a ready snapshot and focus. Only that false result is waitable.
    function Reset-TestReadiness {
        $script:readySnapshots=New-Object 'Collections.Generic.Queue[object]'
        $script:readyFocus=New-Object 'Collections.Generic.Queue[object]'
        $script:readyEvents=New-Object 'Collections.Generic.List[string]'
        $script:readyDeadlines=New-Object 'Collections.Generic.List[long]'
        $script:readyInput='';$script:readyAlwaysBusy=$false;$script:readyMissingInput=$false;$script:readyOwnershipFails=$false;$script:readyFocusCalls=0;$script:readySnapshotCalls=0;$script:readyKeyCalls=0;$script:readyInsertCalls=0;$script:readySendCalls=0
    }
    function New-TestReadySnapshot([bool]$Busy=$false,[string]$Text='',[object[]]$Assistants=@()){
        return [pscustomobject]@{inputCount=1;inputText=$Text;generating=$Busy;assistants=$Assistants}
    }
    function Assert-AgentCopilotOwnership {
        param($Config)
        $script:readyEvents.Add('ownership')
        if($script:readyOwnershipFails){throw 'CDP_UNAVAILABLE: Simulated lost ownership.'}
    }
    function Get-AgentCopilotSnapshot {
        param($Socket,$CancelPath,$Deadline)
        $script:readySnapshotCalls++;$script:readyEvents.Add('snapshot')
        if($script:readySnapshots.Count -gt 0){return $script:readySnapshots.Dequeue()}
        $state=New-TestReadySnapshot $script:readyAlwaysBusy $script:readyInput
        if($script:readyMissingInput){$state.inputCount=0}
        return $state
    }
    function Invoke-AgentCopilotEval {
        param($Socket,$Expression,$CancelPath,$Deadline)
        if($Expression.Contains('sends[0].click()')){$script:readySendCalls++;throw 'CDP_UNAVAILABLE: Simulated uncertain send.'}
        $script:readyFocusCalls++;$script:readyEvents.Add('focus');$script:readyDeadlines.Add($Deadline.Ticks)
        if($script:readyFocus.Count -gt 0){
            $result=$script:readyFocus.Dequeue()
            if($result -is [string] -and $result -ceq 'throw'){throw 'CDP_UNAVAILABLE: Simulated focus failure.'}
            return $result
        }
        return $true
    }
    function Invoke-AgentCopilotCdp {
        param($Socket,$Method,$Params,$CancelPath,$Deadline)
        if($Method -ceq 'Input.dispatchKeyEvent'){$script:readyKeyCalls++;$script:readyEvents.Add('key:'+($Params.type)+':'+($Params.key));return}
        if($Method -ceq 'Input.insertText'){$script:readyInsertCalls++;$script:readyInput=$Params.text;return}
        throw 'Unexpected command in readiness test.'
    }
    $freshTarget=[pscustomobject]@{agent_first_job_send=$true}
    $continuingTarget=[pscustomobject]@{agent_first_job_send=$false}
    Reset-TestReadiness
    $script:readySnapshots.Enqueue((New-TestReadySnapshot $true))
    $script:readyFocus.Enqueue($false);$script:readyFocus.Enqueue($true)
    $readyState=Wait-AgentCopilotInputReady $jobB $freshTarget $null '' ([datetime]::UtcNow.AddSeconds(5)) ([datetime]::UtcNow.AddSeconds(3))
    Assert-Case ($script:readySnapshotCalls -eq 3 -and $script:readyFocusCalls -eq 2 -and -not $readyState.generating) 'Busy snapshot and focus-time busy are reobserved before readiness succeeds'
    Assert-Case ($script:readyEvents[0] -ceq 'ownership' -and $script:readyEvents.IndexOf('focus') -gt 3 -and $script:readyKeyCalls -eq 0 -and $script:readyInsertCalls -eq 0 -and $script:readySendCalls -eq 0) 'Busy readiness sends no key, text or provider request and rechecks ownership'
    Reset-TestReadiness;$script:readyFocus.Enqueue('throw')
    Assert-Rejected {Wait-AgentCopilotInputReady $jobB $freshTarget $null '' ([datetime]::UtcNow.AddSeconds(5)) ([datetime]::UtcNow.AddSeconds(3))} 'CDP_UNAVAILABLE' 'A real focus or CDP exception is not treated as transient busy'
    Assert-Case ($script:readySnapshotCalls -eq 1 -and $script:readyFocusCalls -eq 1) 'Focus failure is not retried'
    Reset-TestReadiness;$script:readyFocus.Enqueue('false')
    Assert-Rejected {Wait-AgentCopilotInputReady $jobB $freshTarget $null '' ([datetime]::UtcNow.AddSeconds(5)) ([datetime]::UtcNow.AddSeconds(3))} 'CDP_UNAVAILABLE' 'A nonboolean focus response is invalid rather than waitable'
    Assert-Case ($script:readyFocusCalls -eq 1) 'Invalid focus response is not retried'
    foreach($changed in @((New-TestReadySnapshot $true 'restored draft'),(New-TestReadySnapshot $true '' @([pscustomobject]@{text='restored history'})))){
        Reset-TestReadiness;$script:readySnapshots.Enqueue($changed)
        Assert-Rejected {Wait-AgentCopilotInputReady $jobB $freshTarget $null '' ([datetime]::UtcNow.AddSeconds(5)) ([datetime]::UtcNow.AddSeconds(3))} 'RESPONSE_INVALID' 'Restored input or conversation rejects even while busy'
        Assert-Case ($script:readyFocusCalls -eq 0 -and $script:readySnapshotCalls -eq 1) 'Restored data is rejected before focus and is not cleared'
    }
    Reset-TestReadiness;$script:readyInput='in-progress input'
    $afterInput=Wait-AgentCopilotInputReady $jobB $freshTarget $null '' ([datetime]::UtcNow.AddSeconds(5)) ([datetime]::UtcNow.AddSeconds(3)) -AfterInput
    Assert-Case ($afterInput.inputText -ceq 'in-progress input') 'AfterInput preserves existing input without repeating the initial empty-draft rule'
    Reset-TestReadiness;$priorReply=New-TestReadySnapshot $false '' @([pscustomobject]@{text='completed previous reply'})
    $script:readySnapshots.Enqueue($priorReply)
    $continuedState=Wait-AgentCopilotInputReady $jobB $continuingTarget $null '' ([datetime]::UtcNow.AddSeconds(5)) ([datetime]::UtcNow.AddSeconds(3))
    Assert-Case ($continuedState.assistants[0].text -ceq 'completed previous reply') 'A continuing job retains completed previous responses'
    Reset-TestReadiness;$script:readyMissingInput=$true
    Assert-Rejected {Wait-AgentCopilotInputReady $jobB $freshTarget $null '' ([datetime]::UtcNow.AddSeconds(5)) ([datetime]::UtcNow.AddSeconds(3))} 'CDP_UNAVAILABLE' 'Disappearing input during focus preparation is not retried as busy'
    Assert-Case ($script:readySnapshotCalls -eq 1 -and $script:readyFocusCalls -eq 0) 'Missing input fails before focus'
    Reset-TestReadiness;$script:readyOwnershipFails=$true
    Assert-Rejected {Wait-AgentCopilotInputReady $jobB $freshTarget $null '' ([datetime]::UtcNow.AddSeconds(5)) ([datetime]::UtcNow.AddSeconds(3))} 'CDP_UNAVAILABLE' 'Lost ownership stops readiness'
    Assert-Case ($script:readySnapshotCalls -eq 0 -and $script:readyFocusCalls -eq 0) 'Lost ownership precedes all browser reads or focus'
    Reset-TestReadiness;$script:readyAlwaysBusy=$true
    Assert-Rejected {Wait-AgentCopilotInputReady $jobB $freshTarget $null '' ([datetime]::UtcNow.AddSeconds(5)) ([datetime]::UtcNow.AddMilliseconds(100))} 'CDP_UNAVAILABLE' 'Persistent busy exhausts the shared preparation deadline'
    Assert-Case ($script:readyFocusCalls -eq 0) 'Preparation timeout causes no focus or input'
    Reset-TestReadiness
    Assert-Rejected {Wait-AgentCopilotInputReady $jobB $freshTarget $null '' ([datetime]::UtcNow.AddSeconds(-1)) ([datetime]::UtcNow.AddSeconds(3))} 'RESPONSE_TIMEOUT' 'Overall deadline takes precedence over preparation deadline'
    Assert-Case ($script:readySnapshotCalls -eq 0) 'Expired overall deadline performs no browser read'
    $readyCancel=Join-Path $jobTemp 'ready-cancel';[IO.File]::WriteAllText($readyCancel,'cancel')
    Reset-TestReadiness
    Assert-Rejected {Wait-AgentCopilotInputReady $jobB $freshTarget $null $readyCancel ([datetime]::UtcNow.AddSeconds(5)) ([datetime]::UtcNow.AddSeconds(3))} 'CANCELLED' 'Cancellation takes precedence while waiting to prepare input'
    Assert-Case ($script:readySnapshotCalls -eq 0) 'Cancellation performs no browser read'
    # Exercise all real pre-send focus call sites with one focus-time busy race; each input command remains single-shot.
    Reset-TestReadiness;$script:nextTargetId='job-ready';$script:readyFocus.Enqueue($true);$script:readyFocus.Enqueue($true);$script:readyFocus.Enqueue($false)
    Assert-Rejected {Invoke-AgentCopilot -Prompt 'Test request' -RequestId 'r-ready-uncertain' -JobId ('7'*32) -Settings @{} -HomePath $jobTemp -TimeoutSeconds 30} 'CDP_UNAVAILABLE' 'Invocation tolerates pre-key busy but still fails an uncertain single send'
    Assert-Case ($script:readyKeyCalls -eq 4 -and $script:readyInsertCalls -eq 1 -and $script:readySendCalls -eq 1) 'Transient pre-key busy does not replay keys, insert or send'
    Assert-Case ($script:readyInput.Contains('request_id は "r-ready-uncertain"') -and $script:readyInput.Contains('第2行: AGENT_END_r-ready-uncertain だけを出力してください。') -and -not $script:readyInput.Contains('AGENT_END_r-uncertain')) 'A separate actual invocation binds both response lines to its own request nonce'
    Assert-Case (@($script:readyDeadlines | Select-Object -Unique).Count -eq 1 -and $script:readyFocusCalls -eq 7) 'All focus call sites share one preparation deadline including a busy recheck'
    Assert-Case ([IO.File]::Exists((Get-AgentCopilotAttemptPath $jobTemp 'r-ready-uncertain'))) 'Uncertain send after readiness retains the no-replay reservation'
    # The original input-appearance timeout is separate from focus preparation and stays AUTH_REQUIRED.
    Reset-TestReadiness;$script:readyMissingInput=$true;$script:nextTargetId='job-no-input'
    Assert-Rejected {Invoke-AgentCopilot -Prompt 'Test request' -RequestId 'r-no-input' -JobId ('8'*32) -Settings @{} -HomePath $jobTemp -TimeoutSeconds 20} 'AUTH_REQUIRED' 'Missing initial input still expires its original 15-second authentication wait'
    Assert-Case ($script:readyFocusCalls -eq 0 -and $script:readyKeyCalls -eq 0 -and $script:readyInsertCalls -eq 0 -and $script:readySendCalls -eq 0) 'Focus preparation never begins when the initial input wait expires'
    function Assert-AgentCopilotOwnership {param($Config)}
    # Run the production response loop with local CDP doubles; only the DOM reader can supply fenced provenance.
    function Reset-TestResponse([string]$RequestId,[object[]]$Candidates=@(),[object[]]$Baseline=@()) {
        $script:responseRequest=$RequestId;$script:responseJob=[guid]::NewGuid().ToString('N')
        $script:responseCandidates=$Candidates;$script:responseBaseline=$Baseline
        $script:responseInput='';$script:responseSent=$false
        $script:responseSends=0;$script:responseKeys=0;$script:responseInserts=0;$script:responseReads=0
        $script:responseExpansions=0;$script:responseExpansionAtRead=0;$script:responseExpandExpression='';$script:responseExpandMode='success'
        $script:responseGenerating=$false;$script:responseHeldInput='';$script:responseCancelPath='';$script:responseCancelAtRead=0
        $script:nextTargetId='response-'+$script:responseJob
        $config=Get-AgentCopilotConfig $jobTemp @{} $script:responseJob
        $target=Get-AgentCopilotTarget $config -Create
        if($Baseline.Count -gt 0){Set-AgentCopilotJobSendStarted $config $target}
    }
    function Get-AgentCopilotSnapshot {
        param($Socket,$CancelPath,$Deadline)
        $shown=@($script:responseBaseline)
        if($script:responseSent){
            $script:responseReads++;$shown+=@($script:responseCandidates)
            if($script:responseCancelAtRead -eq $script:responseReads){[IO.File]::WriteAllText($script:responseCancelPath,'cancel')}
        }
        $inputValue=if($script:responseSent -and $script:responseHeldInput){$script:responseHeldInput}else{$script:responseInput}
        return [pscustomobject]@{inputCount=1;inputText=$inputValue;generating=($script:responseSent -and $script:responseGenerating);assistants=@($shown)}
    }
    function Invoke-AgentCopilotEval {
        param($Socket,$Expression,$CancelPath,$Deadline)
        if($Expression.Contains('sends[0].click()')){$script:responseSends++;$script:responseSent=$true;$script:responseInput=''}
        if($Expression.Contains('HTMLButtonElement.prototype.click.call(more)')){
            $script:responseExpansions++;$script:responseExpansionAtRead=$script:responseReads;$script:responseExpandExpression=$Expression
            if($script:responseExpandMode -ceq 'uncertain'){throw 'CDP_UNAVAILABLE: Simulated uncertain expansion acknowledgement.'}
            if($script:responseExpandMode -ceq 'false_ack'){return $false}
            if($script:responseExpandMode -cne 'refold'){
                $script:responseCandidates[0].source_kind='fenced_plaintext';$script:responseCandidates[0].collapsed=$false
                if($script:responseExpandMode -ceq 'changed_text'){$script:responseCandidates[0].text=$script:responseCandidates[0].text.Replace('original','changed')}
                if($script:responseExpandMode -ceq 'changed_key'){$script:responseCandidates[0].key='different-reply'}
                if($script:responseExpandMode -ceq 'unknown_after'){$script:responseCandidates[0].source_kind='rendered'}
            }
        }
        return $true
    }
    function Invoke-AgentCopilotCdp {
        param($Socket,$Method,$Params,$CancelPath,$Deadline)
        if($Method -ceq 'Input.insertText'){$script:responseInserts++;$script:responseInput=$Params.text;return}
        if($Method -ceq 'Input.dispatchKeyEvent'){$script:responseKeys++;return}
        throw ('Unexpected response-test CDP method: '+$Method)
    }
    function Invoke-TestResponse {Invoke-AgentCopilot -Prompt 'Synthetic response test' -RequestId $script:responseRequest -JobId $script:responseJob -Settings @{} -HomePath $jobTemp -CancelPath $script:responseCancelPath -TimeoutSeconds 5}
    $acceptedRaw='{"request_id":"r-fenced","value":"  日本語 C:\\path\\raw  "}'
    $accepted=[pscustomobject]@{text=($acceptedRaw+"`nAGENT_END_r-fenced");source_kind='fenced_plaintext';collapsed=$false}
    Reset-TestResponse 'r-fenced' @($accepted)
    Assert-Case ([string]::Equals((Invoke-TestResponse),$acceptedRaw,[StringComparison]::Ordinal)) 'Actual adapter accepts exact JSON from a measured fenced source'
    Assert-Case ($script:responseReads -eq 3 -and $script:responseSends -eq 1 -and $script:responseKeys -eq 4 -and $script:responseInserts -eq 1) 'Fenced success requires three stable reads after exactly one input and send sequence'
    Assert-Rejected {Invoke-TestResponse} 'RESPONSE_INVALID' 'Successful fenced request ID cannot be replayed'
    Assert-Case ($script:responseSends -eq 1 -and $script:responseInserts -eq 1) 'Replay rejection performs no second insert or send'
    foreach($mode in @('rendered','missing','collapsed','refusal')){
        $requestId='r-origin-'+$mode;$raw='{"request_id":"'+$requestId+'","value":"日本語 C:\\path\\raw"}'
        $candidate=[pscustomobject]@{text=($raw+"`nAGENT_END_"+$requestId);source_kind='fenced_plaintext';collapsed=$false}
        if($mode -ceq 'rendered'){$candidate.source_kind='rendered'}
        if($mode -ceq 'missing'){$candidate.PSObject.Properties.Remove('source_kind')}
        if($mode -ceq 'collapsed'){$candidate.collapsed=$true}
        if($mode -ceq 'refusal'){$candidate.text='Sorry, I cannot help with this request.';$candidate.source_kind='rendered'}
        Reset-TestResponse $requestId @($candidate)
        $prefix=if($mode -ceq 'refusal'){'REFUSAL'}else{'RESPONSE_INVALID'}
        Assert-Rejected {Invoke-TestResponse} $prefix ('Actual adapter rejects '+$mode+' response with its specific diagnosis')
        Assert-Case ($script:responseSends -eq 1 -and $script:responseInserts -eq 1 -and [IO.File]::Exists((Get-AgentCopilotAttemptPath $jobTemp $requestId))) ('Rejected '+$mode+' response retains one durable attempt without resending')
    }
    Reset-TestResponse 'r-old-fenced' @() @([pscustomobject]@{text="{`"request_id`":`"r-old-fenced`"}`nAGENT_END_r-old-fenced";source_kind='fenced_plaintext';collapsed=$false})
    Assert-Rejected {Invoke-TestResponse} 'RESPONSE_INVALID' 'Fenced provenance never promotes a request already present in the old baseline'
    Assert-Case ($script:responseSends -eq 0 -and $script:responseInserts -eq 0 -and -not [IO.File]::Exists((Get-AgentCopilotAttemptPath $jobTemp 'r-old-fenced'))) 'Old fenced baseline is rejected before input and attempt reservation'
    Reset-TestResponse 'r-fenced-timeout'
    Assert-Rejected {Invoke-TestResponse} 'RESPONSE_TIMEOUT' 'Missing fenced response reaches the bounded existing response timeout'
    Assert-Case ($script:responseSends -eq 1 -and $script:responseInserts -eq 1 -and [IO.File]::Exists((Get-AgentCopilotAttemptPath $jobTemp 'r-fenced-timeout'))) 'Response timeout retains its single attempt without resending'
    function New-TestFolded([string]$RequestId){
        $raw='{"request_id":"'+$RequestId+'","value":"original EXPAND_ARGUMENTS REQUEST_ID RESPONSE_TEXT C:\\path\\raw %FileContents%"}'
        return [pscustomobject]@{key='reply-'+$RequestId;text=($raw+"`nAGENT_END_"+$RequestId);source_kind='fenced_collapsed';collapsed=$true}
    }
    $folded=New-TestFolded 'r-expand-ok';$foldedText=$folded.text
    Reset-TestResponse 'r-expand-ok' @($folded)
    Assert-Case ([string]::Equals((Invoke-TestResponse),$foldedText.Split("`n")[0],[StringComparison]::Ordinal)) 'Collapsed response succeeds only after expansion and exact complete response validation'
    Assert-Case ($script:responseExpansions -eq 1 -and $script:responseExpansionAtRead -eq 3 -and $script:responseReads -eq 6 -and $script:responseSends -eq 1 -and $script:responseInserts -eq 1) 'One expansion follows three folded reads and is followed by three full reads without resending'
    Assert-Case ($script:responseExpandExpression.Contains(($foldedText|ConvertTo-Json -Compress))) 'Expansion expression preserves literal placeholder names and original escaped body through one JSON argument substitution'
    Assert-Rejected {Invoke-TestResponse} 'RESPONSE_INVALID' 'Successful expanded request cannot be replayed'
    Assert-Case ($script:responseExpansions -eq 1 -and $script:responseSends -eq 1) 'Replay does not send or expand again'
    foreach($mode in @('uncertain','false_ack','refold','changed_text','changed_key','unknown_after')){
        $requestId='r-expand-'+$mode;Reset-TestResponse $requestId @((New-TestFolded $requestId));$script:responseExpandMode=$mode
        Assert-Rejected {Invoke-TestResponse} 'RESPONSE_INVALID' ('Expansion '+$mode+' fails closed')
        Assert-Case ($script:responseExpansions -eq 1 -and $script:responseSends -eq 1 -and [IO.File]::Exists((Get-AgentCopilotAttemptPath $jobTemp $requestId))) ('Expansion '+$mode+' retains exactly one send and expansion reservation')
    }
    foreach($mode in @('malformed','wrong_nonce','unknown_dom','generating','input_present','multiple')){
        $requestId='r-no-expand-'+$mode;$candidate=New-TestFolded $requestId;Reset-TestResponse $requestId @($candidate)
        if($mode -ceq 'malformed'){$candidate.text='{broken'+"`nAGENT_END_"+$requestId}
        if($mode -ceq 'wrong_nonce'){$candidate.text=$candidate.text.Replace('AGENT_END_'+$requestId,'AGENT_END_other')}
        if($mode -ceq 'unknown_dom'){$candidate.source_kind='rendered'}
        if($mode -ceq 'generating'){$script:responseGenerating=$true}
        if($mode -ceq 'input_present'){$script:responseHeldInput='new unsent text'}
        if($mode -ceq 'multiple'){$other=New-TestFolded $requestId;$other.key='second-reply';$script:responseCandidates+=@($other)}
        $prefix=if($mode -ceq 'generating'){'RESPONSE_TIMEOUT'}else{'RESPONSE_INVALID'}
        Assert-Rejected {Invoke-TestResponse} $prefix ('Ineligible '+$mode+' candidate is not expanded')
        Assert-Case ($script:responseExpansions -eq 0 -and $script:responseSends -eq 1) ('Ineligible '+$mode+' candidate causes no expansion or second send')
    }
    $oldFolded=New-TestFolded 'r-prior-request'
    Reset-TestResponse 'r-prior-folded-key' @() @($oldFolded)
    # Simulate a reflow changing old displayed text while preserving its old response key.
    $oldFolded.text='reflowed old text';$reflowed=New-TestFolded 'r-prior-folded-key';$reflowed.key=$oldFolded.key;$script:responseCandidates=@($reflowed)
    Assert-Rejected {Invoke-TestResponse} 'RESPONSE_TIMEOUT' 'An old folded response key remains excluded when its displayed text changes'
    Assert-Case ($script:responseExpansions -eq 0 -and $script:responseSends -eq 1) 'Old folded response is not expanded on behalf of a new request'
    Reset-TestResponse 'r-expand-cancel' @((New-TestFolded 'r-expand-cancel'))
    $script:responseCancelPath=Join-Path $jobTemp 'expand-cancel';$script:responseCancelAtRead=3
    Assert-Rejected {Invoke-TestResponse} 'CANCELLED' 'Cancellation at the expansion boundary wins before the helper invocation'
    Assert-Case ($script:responseExpansions -eq 0 -and $script:responseSends -eq 1) 'Cancellation does not expand or resend'
    Reset-TestResponse 'r-expand-expired' @((New-TestFolded 'r-expand-expired'))
    $expiredFold=$script:responseCandidates[0]
    Assert-Rejected {Invoke-AgentCopilotExpand $null $script:responseRequest $expiredFold.key $expiredFold.text '' ([DateTime]::UtcNow.AddSeconds(-1))} 'RESPONSE_TIMEOUT' 'Expired overall deadline stops the expansion helper before CDP'
    Assert-Case ($script:responseExpansions -eq 0) 'Expired expansion deadline invokes no click'
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
    $closed=Close-AgentCopilotLaunchTab $launchConfig $launchUrl $activeSignin ([datetime]::UtcNow.AddSeconds(5))
    Assert-Case ($closed.status -ceq 'closed' -and [string]::IsNullOrEmpty([string]$closed.warning)) 'Verified nonce close reports closed only after target disappearance'
    Assert-Case ($script:closeCalls -eq 1 -and @($script:mockPages | Where-Object id -ceq 'app-launch').Count -eq 0) 'First launch removes only its nonce blank after Copilot is ready'
    Assert-Case (@($script:mockPages | Where-Object { $_.id -ceq 'user-blank' -and $_.url -ceq 'about:blank' }).Count -eq 1) 'Existing user about blank is untouched'
    Assert-Case (@($script:mockPages | Where-Object id -ceq 'extension-welcome').Count -eq 1) 'Extension welcome tab is untouched'
    Assert-Case ((Get-AgentCopilotTarget $launchConfig -Create -AllowAuthentication).id -ceq 'launch-copilot') 'Sign-in target remains recorded and reusable'
    Assert-Rejected {Close-AgentCopilotLaunchTab $launchConfig 'about:blank' $activeSignin ([datetime]::UtcNow.AddSeconds(5))} 'CDP_UNAVAILABLE' 'Plain blank cannot be claimed as app-owned'
    $absent=Close-AgentCopilotLaunchTab $launchConfig $launchUrl $activeSignin ([datetime]::UtcNow.AddSeconds(5))
    Assert-Case ($absent.status -ceq 'not_found' -and $absent.warning -match '閉じていません' -and $script:closeCalls -eq 1) 'Missing exact nonce is an explicit nonfatal no-close result'
    Assert-Case (@($script:mockPages | Where-Object { $_.id -ceq 'user-blank' -and $_.url -ceq 'about:blank' }).Count -eq 1) 'Missing nonce never adopts an unrelated blank'
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
        if($script:openCleanupStatus -ceq 'not_found'){return [pscustomobject]@{status='not_found';warning='今回の起動タブは確認できませんでした。ほかのタブは閉じていません。'}}
        return [pscustomobject]@{status='closed';warning=''}
    }
    try {
        ${env:ProgramFiles(x86)}=$fakeProgramFiles
        $firstLaunchUrl=''
        foreach($launchCase in @(1,2)){
            $script:openEvents=New-Object 'Collections.Generic.List[string]'
            $script:openOwned=$false;$script:openLaunchCalls=0;$script:openCleanupCalls=0;$script:openLaunchUrl='';$script:openArguments='';$script:openCleanupStatus='closed'
            $opened=Open-AgentCopilot -HomePath (Join-Path $jobTemp 'open-orchestration') -Settings @{}
            Assert-Case ($opened.status -ceq 'opened' -and $opened.target_id -ceq 'orchestration-copilot' -and $opened.launch_cleanup -ceq 'closed' -and [string]::IsNullOrEmpty([string]$opened.warning)) ('Real Open first-launch result '+$launchCase)
            Assert-Case ($script:openLaunchCalls -eq 1 -and $script:openCleanupCalls -eq 1) ('Real Open launches once and cleans up once '+$launchCase)
            Assert-Case ($script:openEvents.IndexOf('ownership:True') -gt $script:openEvents.IndexOf('launch') -and $script:openEvents.IndexOf('target') -gt $script:openEvents.IndexOf('ownership:True')) ('Real Open establishes ownership before target retrieval '+$launchCase)
            Assert-Case ($script:openEvents.IndexOf('target') -lt $script:openEvents.IndexOf('bring-to-front') -and $script:openEvents.IndexOf('bring-to-front') -lt $script:openEvents.IndexOf('cleanup')) ('Real Open verifies and foregrounds Copilot before nonce cleanup '+$launchCase)
            Assert-Case ($script:openArguments.Contains('--remote-debugging-address=127.0.0.1') -and $script:openArguments.Contains('--remote-debugging-port=9223') -and $script:openArguments.Contains($script:openLaunchUrl)) ('Real Open passes dedicated listener and exact cleanup nonce '+$launchCase)
            if($launchCase -eq 1){$firstLaunchUrl=$script:openLaunchUrl}else{Assert-Case ($script:openLaunchUrl -cne $firstLaunchUrl) 'Separate Open launches generate different nonce URLs'}
        }
        $script:openEvents=New-Object 'Collections.Generic.List[string]'
        $script:openOwned=$false;$script:openLaunchCalls=0;$script:openCleanupCalls=0;$script:openLaunchUrl='';$script:openArguments='';$script:openCleanupStatus='not_found'
        $opened=Open-AgentCopilot -HomePath (Join-Path $jobTemp 'open-orchestration') -Settings @{}
        Assert-Case ($opened.status -ceq 'opened' -and $opened.launch_cleanup -ceq 'not_found' -and $opened.warning -match '閉じていません') 'Missing nonce cleanup keeps a confirmed Copilot open successful'
        Assert-Case ($script:openLaunchCalls -eq 1 -and $script:openCleanupCalls -eq 1 -and $script:openEvents.IndexOf('bring-to-front') -lt $script:openEvents.IndexOf('cleanup')) 'Missing nonce warning follows target confirmation and has one cleanup inspection'
        $script:openEvents=New-Object 'Collections.Generic.List[string]'
        $script:openOwned=$true;$script:openLaunchCalls=0;$script:openCleanupCalls=0;$script:openLaunchUrl='';$script:openArguments='';$script:openCleanupStatus='closed'
        $opened=Open-AgentCopilot -HomePath (Join-Path $jobTemp 'open-orchestration') -Settings @{}
        Assert-Case ($script:openLaunchCalls -eq 0 -and $script:openCleanupCalls -eq 0 -and -not $script:openEvents.Contains('listener-check')) 'Already-owned Open performs neither process launch nor blank cleanup'
        Assert-Case ($opened.target_id -ceq 'orchestration-copilot' -and $opened.launch_cleanup -ceq 'not_requested' -and [string]::IsNullOrEmpty([string]$opened.warning) -and $script:openEvents.IndexOf('target') -ge 0 -and $script:openEvents.IndexOf('bring-to-front') -gt $script:openEvents.IndexOf('target')) 'Already-owned Open retrieves and foregrounds the recorded sign-in target'
    } finally { ${env:ProgramFiles(x86)}=$savedProgramFiles86 }
}finally{
    $resolvedJobTemp=[IO.Path]::GetFullPath($jobTemp)
    $expectedParent=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')+'\'
    if(-not $resolvedJobTemp.StartsWith($expectedParent,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($resolvedJobTemp) -notmatch '^ai-prompts-copilot-jobtests-[0-9a-f]{32}$'){throw 'Unsafe test cleanup path.'}
    Remove-Item -LiteralPath $resolvedJobTemp -Recurse -Force
}
Write-Output ('PASS: '+$script:checks+' Copilot contract checks. Live M365/Edge integration was not exercised.')
