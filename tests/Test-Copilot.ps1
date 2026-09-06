param([string]$SourcePath=(Join-Path $PSScriptRoot '..\App.ps1'))
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2.0
$script:AgentOfflineTest=$false # Explicit mocked adapter boundary; no production top-level import.
$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile([IO.Path]::GetFullPath($SourcePath),[ref]$null,[ref]$parseErrors)
if ($parseErrors.Count -gt 0) { throw ('PowerShell parse errors: '+$parseErrors.Count) }
# Load definitions only, never the server/launcher top-level code.
$wanted=@('Get-AgentProperty','Get-AgentFullPath','Assert-AgentPathUnder','Assert-AgentNoReparse','Get-AgentHash','Get-AgentVerifiedPriorArtifacts','ConvertTo-AgentRobinLiteral','ConvertFrom-AgentRobinLiteral','Assert-AgentPadPath','Test-AgentRobin','Get-AgentCopilotConfig','Test-AgentCopilotUrl','Test-AgentCopilotAuthUrl','Test-AgentEdgeCommandLine','Test-AgentCopilotSocketUrl','Read-AgentJsonToken','Test-AgentStrictJson','ConvertFrom-AgentCopilotResponse','ConvertFrom-AgentCopilotParts','Assert-AgentCopilotWait','Enter-AgentCopilotMutex','Get-AgentCopilotAttemptPath','Reserve-AgentCopilotAttempt','Test-AgentCopilotTargetRecord','Write-AgentCopilotTargetRecord','Get-AgentCopilotTarget','Assert-AgentCopilotJobBaseline','Set-AgentCopilotJobSendStarted','Wait-AgentCopilotInputReady','Invoke-AgentCopilotExpand','Invoke-AgentCopilot','Get-AgentCopilotDomPrelude','Close-AgentCopilotLaunchTab','Open-AgentCopilot')
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
# The carrier is a sequence of raw UTF-16 string slices, not another JSON envelope.
function New-TestPartFrames([string[]]$Payloads,[string]$RequestId){
    for($i=0;$i -lt $Payloads.Count;$i++){
        $metadata=$RequestId+' '+($i+1)+' '+$Payloads.Count
        $frame='AGENT_PART_V1 '+$metadata+"`nAGENT_DATA "+$Payloads[$i]+"`nAGENT_PART_END_V1 "+$metadata
        if($i -eq ($Payloads.Count-1)){$frame+="`nAGENT_END_"+$RequestId}
        $frame
    }
}
function New-TestParts([string]$Json,[string]$RequestId,[int]$Width=4096){
    $payloads=@();$offset=0
    while($offset -lt $Json.Length){
        $take=[Math]::Min($Width,$Json.Length-$offset)
        if([char]::IsHighSurrogate($Json[$offset+$take-1])){$take--}
        if($take -lt 1){throw 'Invalid test fragment width.'}
        $payloads+=,$Json.Substring($offset,$take);$offset+=$take
    }
    New-TestPartFrames $payloads $RequestId
}
$partValue="  日本語 `"引用`" O'Brien C:\path\raw %FileContents% literal\n`r`n`r`n  "+[char]::ConvertFromUtf32(0x1f642)
$partJson=([ordered]@{request_id='r-parts';robin=($partValue*220)}|ConvertTo-Json -Compress)
$partFrames=@(New-TestParts $partJson 'r-parts')
Assert-Case ($partJson.Length -gt 10000 -and $partFrames.Count -ge 3) 'One long JSON string exceeds the observed 10000-character DOM row limit across three or more parts'
$partActual=ConvertFrom-AgentCopilotParts $partFrames 'r-parts'
Assert-Case ([string]::Equals($partActual,$partJson,[StringComparison]::Ordinal) -and [string]::Equals(($partActual|ConvertFrom-Json).robin,($partValue*220),[StringComparison]::Ordinal)) 'Parts preserve exact JSON and Japanese, quotes, backslashes, percent, blank lines, spaces and emoji in the decoded string'
$escapeJson='{"request_id":"r-escape","value":"  C:\\raw\n\"日本語\"  "}'
foreach($boundary in @(($escapeJson.IndexOf('\\')+1),($escapeJson.IndexOf('\n')+1),($escapeJson.IndexOf('\"')+1))){
    $frames=@(New-TestPartFrames @($escapeJson.Substring(0,$boundary),$escapeJson.Substring($boundary)) 'r-escape')
    Assert-Case ([string]::Equals((ConvertFrom-AgentCopilotParts $frames 'r-escape'),$escapeJson,[StringComparison]::Ordinal)) 'Raw escape sequence can cross a part boundary without added escaping or repair'
}
$singleJson='{"request_id":"r-single","value":"  keep spaces  "}'
$singleFrames=@(New-TestParts $singleJson 'r-single')
Assert-Case ((ConvertFrom-AgentCopilotParts $singleFrames 'r-single') -ceq $singleJson -and $singleFrames.Count -eq 1) 'One framed part uses the same grammar and preserves value whitespace'
# Preserve a complete single ACT-shaped response at the actual 4685-unit regression size.
# The payload is synthetic; saved live output is not a test input.
$boundaryValue="  日本語 `"引用`" O'Brien C:\path\raw %FileContents% `r`n`r`n  "
$boundaryObject=[ordered]@{request_id='r-boundary';state='ACT';message=$boundaryValue;robin='File.ReadTextFromFile.ReadText File: InputPath Encoding: File.TextFileEncoding.UTF8 Content=> FileContents';artifacts=@()}
$boundaryBase=$boundaryObject|ConvertTo-Json -Compress
foreach($boundaryLength in @(4096,4097,4685,8192)){
    $boundaryObject.message=$boundaryValue+('a'*($boundaryLength-$boundaryBase.Length))
    $boundaryJson=$boundaryObject|ConvertTo-Json -Compress
    $boundaryFrames=@(New-TestPartFrames @($boundaryJson) 'r-boundary')
    $boundaryActual=ConvertFrom-AgentCopilotParts $boundaryFrames 'r-boundary'
    Assert-Case ($boundaryJson.Length -eq $boundaryLength -and $boundaryFrames.Count -eq 1 -and [string]::Equals($boundaryActual,$boundaryJson,[StringComparison]::Ordinal) -and [string]::Equals(($boundaryActual|ConvertFrom-Json).message,$boundaryObject.message,[StringComparison]::Ordinal)) ('Complete single ACT-shaped frame preserves '+$boundaryLength+' UTF16 units and exact decoded Japanese, quotes, percent, CRLF and spaces')
    if($boundaryLength -eq 4685){$actualSizedJson=$boundaryJson;$actualSizedFrames=@($boundaryFrames)}
}
$boundaryObject.message+='a'
$oversizedJson=$boundaryObject|ConvertTo-Json -Compress
Assert-Case ($oversizedJson.Length -eq 8193) 'Oversized boundary remains a complete valid JSON object'
Assert-Rejected {ConvertFrom-AgentCopilotParts @(New-TestPartFrames @($oversizedJson) 'r-boundary') 'r-boundary'} 'RESPONSE_INVALID' 'Complete 8193-unit payload is rejected before JSON acceptance'
foreach($boundaryFailure in @('missing_data','missing_end','truncated','wrong_nonce')){
    $broken=@($actualSizedFrames)
    switch($boundaryFailure){
        'missing_data' {$broken[0]=$broken[0].Replace("AGENT_DATA $actualSizedJson`n",'')}
        'missing_end' {$broken[0]=$broken[0].Replace("`nAGENT_END_r-boundary",'')}
        'truncated' {$broken=@(New-TestPartFrames @($actualSizedJson.Substring(0,$actualSizedJson.Length-1)) 'r-boundary')}
        'wrong_nonce' {$broken[0]=$broken[0].Replace('r-boundary','r-other')}
    }
    Assert-Rejected {ConvertFrom-AgentCopilotParts $broken 'r-boundary'} 'RESPONSE_INVALID' ('Actual-sized 4685-unit response rejects '+$boundaryFailure+' without repair')
}
# The longest legal frame has an 8192-unit payload, 128-unit ID, 256/256 and final marker.
$maxFrameId='r'*128
$maxFrameBase='{"request_id":"'+$maxFrameId+'","value":""}'
$maxFrameJson='{"request_id":"'+$maxFrameId+'","value":"'+('a'*(8447-$maxFrameBase.Length))+'"}'
$maxFramePayloads=@(for($i=0;$i -lt 255;$i++){$maxFrameJson.Substring($i,1)})+@($maxFrameJson.Substring(255))
$maxFrames=@(New-TestPartFrames $maxFramePayloads $maxFrameId)
Assert-Case ($maxFrames.Count -eq 256 -and $maxFramePayloads[-1].Length -eq 8192 -and $maxFrames[-1].Length -eq 8648 -and $maxFrames[-1].EndsWith("`nAGENT_END_"+$maxFrameId) -and (ConvertFrom-AgentCopilotParts $maxFrames $maxFrameId) -ceq $maxFrameJson) 'The exact 8648-unit maximum frame with longest nonce, 256/256 and observed final marker is accepted'
Assert-Rejected {ConvertFrom-AgentCopilotParts @($maxFrames[0..254]+@($maxFrames[-1]+'x')) $maxFrameId} 'RESPONSE_INVALID' 'A frame exceeding the exact 8648-unit maximum is rejected'
# Frame size and aggregate size are independent: 129 otherwise legal frames can exceed 1 MiB.
$wholeBase='{"request_id":"r-whole","value":""}'
$wholeJson='{"request_id":"r-whole","value":"'+('a'*(1048576-$wholeBase.Length))+'"}'
$wholeFrames=@(New-TestParts $wholeJson 'r-whole' 8192)
Assert-Case ($wholeJson.Length -eq 1048576 -and $wholeFrames.Count -eq 128 -and [string]::Equals((ConvertFrom-AgentCopilotParts $wholeFrames 'r-whole'),$wholeJson,[StringComparison]::Ordinal)) 'The unchanged aggregate limit accepts exactly 1048576 UTF16 units across 128 full payloads'
$overWholeJson=$wholeJson.Insert($wholeJson.Length-2,'a')
$overWholeFrames=@(New-TestParts $overWholeJson 'r-whole' 8192)
Assert-Case ($overWholeJson.Length -eq 1048577 -and $overWholeFrames.Count -eq 129) 'Aggregate-overflow fixture uses 129 individually bounded frames and valid JSON'
Assert-Rejected {ConvertFrom-AgentCopilotParts $overWholeFrames 'r-whole'} 'RESPONSE_INVALID' 'The aggregate budget rejects 1048577 UTF16 units even though every frame is individually legal'

$countJson='{"request_id":"r-count","value":"'+('a'*(256-('{"request_id":"r-count","value":""}').Length))+'"}'
Assert-Case ($countJson.Length -eq 256) 'Maximum part-count fixture contains exactly 256 raw characters'
$countFrames=@(New-TestParts $countJson 'r-count' 1)
Assert-Case ((ConvertFrom-AgentCopilotParts $countFrames 'r-count') -ceq $countJson -and $countFrames.Count -eq 256) 'Canonical part indices support the explicit upper bound of 256'
foreach($failure in @('missing','duplicate','reverse','wrong_total','wrong_index','leading_zero','missing_end','early_end','wrong_id','wrong_footer','bad_json','extra_row','crlf','double_space','empty_data','oversized_data','surrogate','surrogate_boundary','null_frame','nonstring','too_many','trailing_nbsp','leading_json_space')){
    $frames=@($partFrames);$request='r-parts'
    switch($failure){
        'missing' {$frames=@($frames[1..($frames.Count-1)])}
        'duplicate' {$frames[1]=$frames[0]}
        'reverse' {[array]::Reverse($frames)}
        'wrong_total' {$frames[0]=$frames[0].Replace(' 1 '+$frames.Count,' 1 1')}
        'wrong_index' {$frames[0]=$frames[0].Replace(' 1 '+$frames.Count,' 2 '+$frames.Count)}
        'leading_zero' {$frames[0]=$frames[0].Replace(' 1 '+$frames.Count,' 01 '+$frames.Count)}
        'missing_end' {$frames[-1]=$frames[-1].Replace("`nAGENT_END_r-parts",'')}
        'early_end' {$frames[0]+="`nAGENT_END_r-parts"}
        'wrong_id' {$frames[0]=$frames[0].Replace('r-parts','r-other')}
        'wrong_footer' {$frames[0]=$frames[0].Replace('AGENT_PART_END_V1 r-parts','AGENT_PART_END_V1 r-other')}
        'bad_json' {$frames=@(New-TestPartFrames @('{"request_id":"r-parts","x":}') $request)}
        'extra_row' {$frames[0]+="`nextra"}
        'crlf' {$frames[0]=$frames[0].Replace("`n","`r`n")}
        'double_space' {$frames[0]=$frames[0].Replace('AGENT_PART_V1 ','AGENT_PART_V1  ')}
        'empty_data' {$frames=@(New-TestPartFrames @('') $request)}
        'oversized_data' {$frames=@(New-TestPartFrames @(('a'*8193)) $request)}
        'surrogate' {$frames=@(New-TestPartFrames @('{"request_id":"r-parts","x":"'+[char]0xd800+'"}') $request)}
        'surrogate_boundary' {$frames=@(New-TestPartFrames @('{"request_id":"r-parts","x":"'+[char]0xd83d,[string][char]0xde42+'"}') $request)}
        'null_frame' {$frames[0]=$null}
        'nonstring' {$frames[0]=123}
        'too_many' {$frames=@('x')*257}
        'trailing_nbsp' {$frames[-1]+="`n"+[char]0x00a0}
        'leading_json_space' {$frames=@(New-TestPartFrames @(' '+$singleJson.Replace('r-single','r-parts')) $request)}
    }
    Assert-Rejected {ConvertFrom-AgentCopilotParts $frames $request} 'RESPONSE_INVALID' ('Strict parts reject '+$failure+' without normalization')
}
Assert-Rejected {ConvertFrom-AgentCopilotParts @() 'r-parts'} 'RESPONSE_INVALID' 'Empty frame sequence is not a complete answer'
Assert-Rejected {ConvertFrom-AgentCopilotParts $singleFrames "r-single`n"} 'RESPONSE_INVALID' 'Request ID cannot include a terminal LF'
$partsDefinition=@($ast.FindAll({param($n)$n -is [Management.Automation.Language.FunctionDefinitionAst]},$false)|Where-Object Name -eq 'ConvertFrom-AgentCopilotParts')[0].Extent.Text
Assert-Case ($partsDefinition.Contains("`$observedEnd = `$match.Groups['end'].Value") -and $partsDefinition.Contains('($json+$observedEnd)') -and -not $partsDefinition.Contains('($json+"`nAGENT_END_"+$RequestId)')) 'Parser passes the observed final marker into strict JSON validation without manufacturing one'

$json = '{"request_id":"r1","robin":"SET Path TO $''C:\\folder\\file.txt''\nSET Percent TO 100%","data":"日本語、空白  2つ"}'
$complete=$json+"`nAGENT_END_r1"
$actual=ConvertFrom-AgentCopilotResponse $complete 'r1'
Assert-Case ([string]::Equals($actual,$json,[StringComparison]::Ordinal)) 'Response preserves code, percent, whitespace and legitimate backslashes exactly'
$nbspFramed=$complete+"`n"+[char]0x00a0
Assert-Case ([string]::Equals((ConvertFrom-AgentCopilotResponse $nbspFramed 'r1'),$json,[StringComparison]::Ordinal) -and $nbspFramed.EndsWith("`n"+[char]0x00a0)) 'Existing strict parser accepts the unchanged response frame with one actual trailing NBSP row'
Assert-Rejected {ConvertFrom-AgentCopilotResponse $nbspFramed 'r1' -Collapsed} 'RESPONSE_INVALID' 'Trailing NBSP never bypasses the collapsed response rejection'
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
$longParts=@(New-TestParts $longJson 'r-long-robin')
$longPartsDecoded=(ConvertFrom-AgentCopilotParts $longParts 'r-long-robin')|ConvertFrom-Json
Assert-Case ([string]::Equals($longPartsDecoded.robin,$longRobin,[StringComparison]::Ordinal) -and $longParts.Count -ge 10 -and @(Test-AgentRobin -Robin $longPartsDecoded.robin -RunDirectory $robinRun -Job $robinJob).Count -eq $longWriteCount) 'Framed long response restores the complete production-valid Robin with more than ten direct rows'

$rowRobin=@($longRobinLines | Select-Object -First 25) -join "`r`n"
$rowOutputs=@(Test-AgentRobin -Robin $rowRobin -RunDirectory $robinRun -Job $robinJob)
$rowMessage='original 日本語 "引用" O''Brien C:\path\raw %FileContents% literal\n ' * 90
$rowJson=([ordered]@{request_id='r-multiline-robin';state='ACT';message=$rowMessage;robin=$rowRobin;artifacts=@($rowOutputs)}|ConvertTo-Json -Depth 10)
$rowFrame=$rowJson+"`nAGENT_END_r-multiline-robin"
Assert-Case ($rowFrame.Length -gt 10000 -and @($rowFrame -split '\r?\n' | Where-Object {$_.Length -ge 10000 -or $_.Length -eq 0}).Count -eq 0 -and $rowOutputs.Count -eq 24) 'Multiline transport exceeds 10000 characters with each intact row below 10000 and a production-validated Robin body'
$rowActual=ConvertFrom-AgentCopilotResponse $rowFrame 'r-multiline-robin'
$rowDecoded=ConvertFrom-Json -InputObject $rowActual
Assert-Case ([string]::Equals($rowActual,$rowJson,[StringComparison]::Ordinal) -and [string]::Equals($rowDecoded.robin,$rowRobin,[StringComparison]::Ordinal) -and [string]::Equals($rowDecoded.message,$rowMessage,[StringComparison]::Ordinal)) 'Multiline JSON and decoded Robin preserve all formatting, Unicode, quotes, backslashes, percent references and CRLF exactly'
Assert-Case ([string]::Equals((ConvertFrom-AgentCopilotResponse ($rowFrame+"`n"+[char]0x00a0) 'r-multiline-robin'),$rowJson,[StringComparison]::Ordinal)) 'Optional terminal NBSP preserves the entire multiline JSON object'
Assert-Rejected {ConvertFrom-AgentCopilotResponse $rowFrame 'r-other-multiline'} 'RESPONSE_INVALID' 'Multiline JSON never bypasses the exact terminal nonce'
$missingMiddle=$rowJson.Replace('"ACT"','')
Assert-Rejected {ConvertFrom-AgentCopilotResponse ($missingMiddle+"`nAGENT_END_r-multiline-robin") 'r-multiline-robin'} 'RESPONSE_INVALID' 'Malformed multiline JSON after a middle value loss is not repaired'
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
    Assert-Case ($script:mockInput.StartsWith("Test request`n`n") -and $script:mockInput.Contains('コンパクト JSON') -and $script:mockInput.Contains('1個以上256個以下')) 'Wire prompt requires bounded compact JSON transport parts'
    Assert-Case ($script:mockInput.Contains('request_id は "r-uncertain"') -and $script:mockInput.Contains('AGENT_PART_V1 r-uncertain i N') -and $script:mockInput.Contains('AGENT_PART_END_V1 r-uncertain i N')) 'Wire prompt binds both part headers and footers to this request'
    Assert-Case ($script:mockInput.Contains('第2行 AGENT_DATA にASCIIスペース1個') -and $script:mockInput.Contains('第4行 AGENT_END_r-uncertain') -and $script:mockInput.Contains('8192 UTF-16コード単位以下') -and $script:mockInput.Contains('サロゲートペアの途中で分割しない')) 'Wire prompt states exact carrier rows, final marker, UTF16 limit and Unicode boundary'
    Assert-Case ($script:mockInput.Contains('元の文字を追加・削除・再エスケープしない') -and $script:mockInput.Contains('フェンスの外に前置き、説明、別のコードや文字を一切付けない') -and $script:mockInput -notmatch 'コードフェンス1個だけ|pretty-printed|文字列値は分割せず') 'Wire prompt prohibits repair and conflicting single-fence formatting'
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
    Assert-Case ($script:readyInput.Contains('request_id は "r-ready-uncertain"') -and $script:readyInput.Contains('第4行 AGENT_END_r-ready-uncertain') -and -not $script:readyInput.Contains('AGENT_END_r-uncertain')) 'A separate actual invocation binds its framed compact JSON and final marker to its own request nonce'
    Assert-Case ($script:readyDeadlines[0] -lt $script:readyDeadlines[6] -and $script:readyDeadlines[2] -eq $script:readyDeadlines[3] -and $script:readyFocusCalls -eq 7) 'Each focus step gets fresh preparation time while its busy recheck retains the same deadline'
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
        $script:responseMutation=$null;$script:responseGenerating=$false;$script:responseHeldInput='';$script:responseCancelPath='';$script:responseCancelAtRead=0
        $script:nextTargetId='response-'+$script:responseJob
        $config=Get-AgentCopilotConfig $jobTemp @{} $script:responseJob
        $target=Get-AgentCopilotTarget $config -Create
        if($Baseline.Count -gt 0){Set-AgentCopilotJobSendStarted $config $target}
    }
    function Get-AgentCopilotSnapshot {
        param($Socket,$CancelPath,$Deadline)
        $shown=@($script:responseBaseline)
        if($script:responseSent){
            $script:responseReads++;if($null -ne $script:responseMutation){& $script:responseMutation};$shown+=@($script:responseCandidates)
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
                if($script:responseExpandMode -ceq 'removed_nbsp'){$text=$script:responseCandidates[0].text;$script:responseCandidates[0].text=$text.Substring(0,$text.Length-2)}
                if($script:responseExpandMode -ceq 'changed_nbsp'){$text=$script:responseCandidates[0].text;$script:responseCandidates[0].text=$text.Substring(0,$text.Length-1)+' '}
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
    function New-TestPartsCandidate([string]$RequestId,[int]$Width=4096){
        $json=([ordered]@{request_id=$RequestId;value=("  日本語 `"引用`" C:\raw %FileContents%`r`n  "+[char]::ConvertFromUtf32(0x1f642))}|ConvertTo-Json -Compress)
        return [pscustomobject]@{key='reply-'+$RequestId;text='';frames=@(New-TestParts $json $RequestId $Width);source_kind='fenced_parts';collapsed=$true}
    }
    $partsCandidate=New-TestPartsCandidate 'r-parts-folded' 30
    $partsExpected=ConvertFrom-AgentCopilotParts $partsCandidate.frames 'r-parts-folded'
    Reset-TestResponse 'r-parts-folded' @($partsCandidate)
    Assert-Case ([string]::Equals((Invoke-TestResponse),$partsExpected,[StringComparison]::Ordinal)) 'Production loop accepts only complete known folded carrier frames'
    Assert-Case ($script:responseReads -eq 3 -and $script:responseExpansions -eq 0 -and $script:responseSends -eq 1 -and $script:responseInserts -eq 1) 'Framed folded success requires three stable reads, zero More and exactly one send'
    Assert-Rejected {Invoke-TestResponse} 'RESPONSE_INVALID' 'Framed successful request is never resent'
    $partsOld=New-TestPartsCandidate 'r-parts-baseline' 30
    Reset-TestResponse 'r-parts-baseline' @() @($partsOld)
    Assert-Rejected {Invoke-TestResponse} 'RESPONSE_INVALID' 'Current request nonce in past raw frames is rejected before send'
    Assert-Case ($script:responseSends -eq 0 -and $script:responseInserts -eq 0) 'Past framed request causes no input or send'
    $partsOld=New-TestPartsCandidate 'r-parts-old' 30
    $partsNew=New-TestPartsCandidate 'r-parts-continued' 30
    Reset-TestResponse 'r-parts-continued' @($partsNew) @($partsOld)
    Assert-Case ((Invoke-TestResponse) -ceq (ConvertFrom-AgentCopilotParts $partsNew.frames 'r-parts-continued')) 'Empty text fields in past and new framed responses do not hide fresh framed data'
    $partsNew=New-TestPartsCandidate 'r-parts-old-key' 30;$partsNew.key=$partsOld.key
    Reset-TestResponse 'r-parts-old-key' @($partsNew) @($partsOld)
    Assert-Rejected {Invoke-TestResponse} 'RESPONSE_TIMEOUT' 'Past response key is excluded even if its framed data changes'
    Assert-Case ($script:responseExpansions -eq 0 -and $script:responseSends -eq 1) 'Past response never triggers a More or repeat send'
    Reset-TestResponse 'r-parts-boundaries' @((New-TestPartsCandidate 'r-parts-boundaries' 30))
    $script:responseMutation={if($script:responseReads -eq 3){$script:responseCandidates=@(New-TestPartsCandidate 'r-parts-boundaries' 31)}}
    $null=Invoke-TestResponse
    Assert-Case ($script:responseReads -eq 5 -and $script:responseExpansions -eq 0 -and $script:responseSends -eq 1) 'Same joined JSON with changed raw frame boundaries resets the required three stable reads'
    Reset-TestResponse 'r-parts-key-change' @((New-TestPartsCandidate 'r-parts-key-change' 30))
    $script:responseMutation={if($script:responseReads -eq 3){$script:responseCandidates[0].key='replacement-owned-reply'}}
    $null=Invoke-TestResponse
    Assert-Case ($script:responseReads -eq 5 -and $script:responseExpansions -eq 0) 'Changing the owned response key resets framed stability'
    foreach($mode in @('missing_part','mixed_text','other_fresh','generating','input_present')){
        $request='r-parts-loop-'+$mode;$candidate=New-TestPartsCandidate $request 30
        Reset-TestResponse $request @($candidate)
        if($mode -ceq 'missing_part'){$candidate.frames=@($candidate.frames[1..($candidate.frames.Count-1)])}
        if($mode -ceq 'mixed_text'){$candidate.text='unexpected companion text'}
        if($mode -ceq 'other_fresh'){$script:responseCandidates+=@([pscustomobject]@{key='extra-reply';text='unrelated new answer';source_kind='rendered';collapsed=$false})}
        if($mode -ceq 'generating'){$script:responseGenerating=$true}
        if($mode -ceq 'input_present'){$script:responseHeldInput='unsent draft'}
        $prefix=if($mode -cin @('generating','input_present')){'RESPONSE_TIMEOUT'}else{'RESPONSE_INVALID'}
        Assert-Rejected {Invoke-TestResponse} $prefix ('Production framed response refuses '+$mode)
        Assert-Case ($script:responseExpansions -eq 0 -and $script:responseSends -eq 1 -and $script:responseInserts -eq 1) ('Rejected framed '+$mode+' causes no More or retry')
    }
    foreach($rowMode in @('full','folded','nbsp')){
        $rowRequest='r-multiline-'+$rowMode
        $rowValue="original 日本語 C:\path %FileContents% literal\n`r`n  "
        $rowRaw=([ordered]@{request_id=$rowRequest;value=$rowValue;items=@('first','middle','last')}|ConvertTo-Json -Depth 10)
        $rowText=$rowRaw+"`nAGENT_END_"+$rowRequest
        if($rowMode -ceq 'nbsp'){$rowText+="`n"+[char]0x00a0}
        $rowCandidate=[pscustomobject]@{key='reply-'+$rowRequest;text=$rowText;source_kind='fenced_plaintext';collapsed=$false}
        if($rowMode -cne 'full'){$rowCandidate.source_kind='fenced_collapsed';$rowCandidate.collapsed=$true}
        Reset-TestResponse $rowRequest @($rowCandidate)
        Assert-Case ([string]::Equals((Invoke-TestResponse),$rowRaw,[StringComparison]::Ordinal)) ('Actual adapter preserves the complete multiline JSON: '+$rowMode)
        $expectedReads=if($rowMode -ceq 'full'){3}else{6};$expectedExpansions=if($rowMode -ceq 'full'){0}else{1}
        Assert-Case ($script:responseReads -eq $expectedReads -and $script:responseExpansions -eq $expectedExpansions -and $script:responseSends -eq 1 -and $script:responseInserts -eq 1 -and $rowCandidate.text -ceq $rowText) ('Multiline success requires all stable reads without a repeat input, send or changed tail: '+$rowMode)
    }
    foreach($rowFailure in @('malformed_middle','wrong_nonce','changed_text')){
        $rowRequest='r-multiline-reject-'+$rowFailure
        $rowRaw=([ordered]@{request_id=$rowRequest;value='original middle value';items=@('one','two')}|ConvertTo-Json -Depth 10)
        if($rowFailure -ceq 'malformed_middle'){$rowRaw=$rowRaw -replace '"original middle value"',''}
        $rowText=$rowRaw+"`nAGENT_END_"+$rowRequest
        if($rowFailure -ceq 'wrong_nonce'){$rowText=$rowRaw+"`nAGENT_END_other"}
        Reset-TestResponse $rowRequest @([pscustomobject]@{key='reply-'+$rowRequest;text=$rowText;source_kind='fenced_collapsed';collapsed=$true})
        if($rowFailure -ceq 'changed_text'){$script:responseExpandMode='changed_text'}
        Assert-Rejected {Invoke-TestResponse} 'RESPONSE_INVALID' ('Actual adapter refuses damaged or changed multiline response: '+$rowFailure)
        $expectedExpansions=if($rowFailure -ceq 'changed_text'){1}else{0}
        Assert-Case ($script:responseExpansions -eq $expectedExpansions -and $script:responseSends -eq 1 -and $script:responseInserts -eq 1) ('Multiline rejection never retries input, send or expansion: '+$rowFailure)
    }
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
    $nbspFull=New-TestFolded 'r-full-nbsp';$nbspFull.text+="`n"+[char]0x00a0;$nbspFull.source_kind='fenced_plaintext';$nbspFull.collapsed=$false
    Reset-TestResponse 'r-full-nbsp' @($nbspFull)
    Assert-Case ([string]::Equals((Invoke-TestResponse),$nbspFull.text.Split("`n")[0],[StringComparison]::Ordinal)) 'Known full three-row response is parsed without changing its JSON content'
    Assert-Case ($script:responseReads -eq 3 -and $script:responseExpansions -eq 0 -and $script:responseSends -eq 1) 'A full NBSP-tail response needs three stable reads and no expansion'
    $nbspFold=New-TestFolded 'r-expand-nbsp';$nbspFold.text+="`n"+[char]0x00a0;$nbspExpected=$nbspFold.text
    Reset-TestResponse 'r-expand-nbsp' @($nbspFold)
    Assert-Case ([string]::Equals((Invoke-TestResponse),$nbspExpected.Split("`n")[0],[StringComparison]::Ordinal)) 'Known collapsed three-row response succeeds after one expansion and complete reread'
    Assert-Case ($script:responseExpandExpression.Contains(($nbspExpected|ConvertTo-Json -Compress)) -and $script:responseCandidates[0].text.EndsWith("`n"+[char]0x00a0) -and $script:responseExpansions -eq 1 -and $script:responseReads -eq 6 -and $script:responseSends -eq 1) 'The actual expansion argument and after reads retain the exact final LF and NBSP'
    foreach($mode in @('removed_nbsp','changed_nbsp')){
        $requestId='r-expand-'+$mode;$nbspCandidate=New-TestFolded $requestId;$nbspCandidate.text+="`n"+[char]0x00a0
        Reset-TestResponse $requestId @($nbspCandidate);$script:responseExpandMode=$mode
        Assert-Rejected {Invoke-TestResponse} 'RESPONSE_INVALID' ('Expansion '+$mode+' rejects changed final response characters')
        Assert-Case ($script:responseExpansions -eq 1 -and $script:responseSends -eq 1 -and [IO.File]::Exists((Get-AgentCopilotAttemptPath $jobTemp $requestId))) ('Expansion '+$mode+' cannot normalize the tail or retry the click or send')
    }
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
