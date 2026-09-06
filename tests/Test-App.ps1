# Local contract tests only: mocked Copilot/PAD are not live acceptance evidence.
[CmdletBinding()]
param([string]$AppSourcePath = '')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'ReleaseFixture.ps1')
if (-not $AppSourcePath) { $AppSourcePath = Join-Path $PSScriptRoot '..\App.ps1' }
. ([IO.Path]::GetFullPath($AppSourcePath)) -Mode Library
$script:ProductionRobin = (Get-Item -LiteralPath Function:\Test-AgentRobin).ScriptBlock
$script:Checks = 0
function Assert-True($Condition, [string]$Name) { if (-not $Condition) { throw ('FAIL: ' + $Name) }; $script:Checks++ }
function Assert-Throws([scriptblock]$Action, [string]$Pattern, [string]$Name) {
    $message = ''
    try { & $Action | Out-Null } catch { $message = $_.Exception.Message }
    Assert-True ($message -match $Pattern) ($Name + ' (received: ' + $message + ')')
}
$workspace = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$testRoot = Join-Path $workspace ('.work\core-test-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($testRoot) | Out-Null
function New-TestJob([string]$TestHome, [string]$Target, [string]$Status = 'queued') {
    $id = [guid]::NewGuid().ToString('N')
    $dir = Get-AgentJobDirectory $TestHome $id
    [IO.Directory]::CreateDirectory($dir) | Out-Null
    $job = [pscustomobject]@{ job_id = $id; status = $Status; goal = "日本語を`n英訳する 100%"; target = $Target; question = ''; final_answer = ''; artifacts = @(); history = @(); error = '' }
    Save-AgentJob $dir $job
    Write-AgentJson (Join-Path $TestHome 'data\latest.json') @{ job_id = $id }
    return $job
}
function New-TestAiCall([string]$TestHome, [string]$Target) {
    $job = New-TestJob $TestHome $Target 'running_pad'
    $directory = Get-AgentJobDirectory $TestHome $job.job_id
    $runId = [guid]::NewGuid().ToString('N'); $callId = [guid]::NewGuid().ToString('N')
    $run = Join-Path $directory ('runs\' + $runId)
    $call = Join-Path $run ('calls\' + $callId)
    [IO.Directory]::CreateDirectory($call) | Out-Null
    $requestPath = Join-Path $call 'request.json'; $resultPath = Join-Path $call 'result.json'
    Write-AgentJson (Join-Path $directory 'active-run.json') @{ job_id = $job.job_id; run_id = $runId; status = 'pad_running'; run_directory = $run; app_path = $script:AgentAppPath }
    $request = [pscustomobject]@{ job_id = $job.job_id; run_id = $runId; ai_call_id = $callId; operation = 'translate'; input_path = $Target; output_format = 'text'; labels = @(); instructions = '英訳。引用符と改行を保持。'; timeout_seconds = 15 }
    Write-AgentJson $requestPath $request
    return [pscustomobject]@{ request = $request; request_path = $requestPath; result_path = $resultPath; directory = $call; job_directory = $directory }
}
try {
    Assert-True ($PSVersionTable.PSVersion.Major -eq 5) 'Suite exercises Windows PowerShell 5.1'
    Assert-True (([IO.File]::ReadAllBytes($script:AgentAppPath)[0..2] -join ',') -ceq '239,187,191') 'App has UTF-8 BOM'
    # Exercise real Move/Replace at the observed long-directory boundary.
    # The old appended backup suffix exceeded MAX_PATH only during an update.
    $jsonBoundaryParent = Join-Path $testRoot ('p' * (216 - $testRoot.Length - 1))
    $jsonBoundaryPath = Join-Path $jsonBoundaryParent 'request.json'
    Assert-True ($jsonBoundaryParent.Length -eq 216 -and $jsonBoundaryPath.Length -eq 229) 'JSON regression uses the observed 216-character parent and 229-character destination'
    Write-AgentJson $jsonBoundaryPath @{ step = 1; text = '初回の内容'; original_only = $true }
    $jsonBoundaryValue = Read-AgentJson $jsonBoundaryPath
    Assert-True ($jsonBoundaryValue.step -eq 1 -and $jsonBoundaryValue.text -ceq '初回の内容') 'First JSON creation succeeds in the long directory'
    Assert-True (([IO.Directory]::GetFileSystemEntries($jsonBoundaryParent) -join '') -ceq $jsonBoundaryPath) 'First JSON creation leaves no temporary files'
    Write-AgentJson $jsonBoundaryPath @{ step = 2; text = "更新 100%`n引用`"を保持" }
    $jsonBoundaryValue = Read-AgentJson $jsonBoundaryPath
    Assert-True ($jsonBoundaryValue.step -eq 2 -and $jsonBoundaryValue.text -ceq "更新 100%`n引用`"を保持" -and $null -eq $jsonBoundaryValue.PSObject.Properties['original_only']) 'Actual long-path Replace publishes the complete new JSON'
    Assert-True (([IO.Directory]::GetFileSystemEntries($jsonBoundaryParent) -join '') -ceq $jsonBoundaryPath) 'Successful long-path Replace removes temporary and backup files'
    $jsonBoundaryHash = Get-AgentHash $jsonBoundaryPath
    $jsonBoundaryLock = [IO.File]::Open($jsonBoundaryPath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    try {
        Assert-Throws { Write-AgentJson $jsonBoundaryPath @{ step = 3; text = '公開されない内容' } } 'Replace' 'A destination held without delete sharing rejects the actual replacement'
    } finally { $jsonBoundaryLock.Dispose() }
    Assert-True ((Get-AgentHash $jsonBoundaryPath) -ceq $jsonBoundaryHash -and (Read-AgentJson $jsonBoundaryPath).step -eq 2) 'Failed replacement preserves the previous JSON bytes'
    Assert-True (([IO.Directory]::GetFileSystemEntries($jsonBoundaryParent) -join '') -ceq $jsonBoundaryPath) 'Failed replacement removes its temporary and backup files'
    $homeDirectory = Initialize-AgentHome (Join-Path $testRoot 'home')
    $source = Join-Path $testRoot 'share'
    [IO.Directory]::CreateDirectory($source) | Out-Null
    [IO.File]::WriteAllText((Join-Path $source 'App.ps1'), "# App-Version: 0.1.0`n# release test", $script:AgentEncoding)
    [IO.File]::WriteAllText((Join-Path $source 'index.html'), '<meta name="app-version" content="0.1.0"><p>初回</p>', $script:AgentEncoding)
    [IO.File]::WriteAllText((Join-Path $source '業務エージェント.cmd'), '@echo off', $script:AgentEncoding)
    Set-TestReleaseBinding $source
    $first = Sync-AgentRelease $homeDirectory $source
    Assert-True (Test-Path -LiteralPath (Join-Path $first 'App.ps1')) 'Initial local release copied'
    $pointer = Join-Path $homeDirectory 'app\current.json'
    $stamp = (Get-Item -LiteralPath $pointer).LastWriteTimeUtc
    $same = Sync-AgentRelease $homeDirectory $source
    Assert-True ($same -ceq $first -and (Get-Item -LiteralPath $pointer).LastWriteTimeUtc -eq $stamp) 'Unchanged release does not rewrite pointer'
    [IO.File]::WriteAllText((Join-Path $homeDirectory 'data\keep.txt'), 'user data')
    [IO.File]::WriteAllText((Join-Path $source 'index.html'), '<meta name="app-version" content="0.1.0"><p>変更</p>', $script:AgentEncoding)
    Set-TestReleaseBinding $source
    $second = Sync-AgentRelease $homeDirectory $source
    Assert-True ($second -cne $first -and (Test-Path -LiteralPath $first)) 'Content change uses immutable new release'
    Assert-True ([IO.File]::ReadAllText((Join-Path $homeDirectory 'data\keep.txt')) -ceq 'user data') 'User data survives update'
    $offline = Sync-AgentRelease $homeDirectory (Join-Path $testRoot 'unavailable-share') -WarningAction SilentlyContinue
    Assert-True ($offline -ceq $second) 'Unavailable source uses verified cache'
    # A retained cache launcher is never an update source, even after a newer release exists.
    $cacheHome = Initialize-AgentHome (Join-Path $testRoot 'cache-regression-home')
    $cacheSource = Join-Path $testRoot 'cache-regression-share'
    [IO.Directory]::CreateDirectory($cacheSource) | Out-Null
    foreach ($file in @('App.ps1','index.html','業務エージェント.cmd')) { [IO.File]::Copy((Join-Path $source $file), (Join-Path $cacheSource $file)) }
    $oldCache = Sync-AgentRelease $cacheHome $cacheSource
    [IO.File]::WriteAllText((Join-Path $cacheHome 'data\keep.txt'), 'unchanged user data', $script:AgentEncoding)
    [IO.File]::WriteAllText((Join-Path $cacheSource 'App.ps1'), "# App-Version: 0.2.0`n# newer release test", $script:AgentEncoding)
    [IO.File]::WriteAllText((Join-Path $cacheSource 'index.html'), '<meta name="app-version" content="0.2.0"><p>新版</p>', $script:AgentEncoding)
    Set-TestReleaseBinding $cacheSource
    $newCache = Sync-AgentRelease $cacheHome $cacheSource
    Assert-True ($newCache -cne $oldCache -and (Get-AgentRelease $newCache).version -ceq '0.2.0') 'Newer release is selected before cache rollback regression'
    $cachePointer = Join-Path $cacheHome 'app\current.json'
    $cachePointerHash = Get-AgentHash $cachePointer
    $cachePointerStamp = (Get-Item -LiteralPath $cachePointer).LastWriteTimeUtc
    $cacheDataHash = Get-AgentHash (Join-Path $cacheHome 'data\keep.txt')
    foreach ($retainedSource in @($oldCache,$newCache)) {
        $retainedResult = Sync-AgentRelease $cacheHome $retainedSource
        Assert-True ($retainedResult -ceq $newCache) 'Old and current cached launchers both resolve the selected current release'
        Assert-True ((Get-AgentHash $cachePointer) -ceq $cachePointerHash -and (Get-Item -LiteralPath $cachePointer).LastWriteTimeUtc -eq $cachePointerStamp) 'Cached source cannot rewrite or roll back current.json'
        Assert-True ((Get-AgentHash (Join-Path $cacheHome 'data\keep.txt')) -ceq $cacheDataHash) 'Cached source leaves user data untouched'
    }
    [IO.File]::WriteAllText((Join-Path $cacheSource 'App.ps1'), "# App-Version: 0.1.0`n# older external release", $script:AgentEncoding)
    [IO.File]::WriteAllText((Join-Path $cacheSource 'index.html'), '<meta name="app-version" content="0.1.0"><p>旧版</p>', $script:AgentEncoding)
    Set-TestReleaseBinding $cacheSource
    Assert-Throws { Sync-AgentRelease $cacheHome $cacheSource } 'RELEASE_DOWNGRADE' 'Older external release is explicitly rejected'
    Assert-True ((Get-AgentHash $cachePointer) -ceq $cachePointerHash -and (Get-Item -LiteralPath $cachePointer).LastWriteTimeUtc -eq $cachePointerStamp -and (Get-AgentCachedRelease $cacheHome) -ceq $newCache) 'Rejected external downgrade preserves selected current release and pointer'
    Assert-True ((Get-AgentHash (Join-Path $cacheHome 'data\keep.txt')) -ceq $cacheDataHash) 'Rejected external downgrade leaves user data untouched'
    # A deliberately failing owned Serve child must be visible to Bootstrap as failure.
    $startupSource = Join-Path $testRoot 'startup-failure-share'
    $startupHome = Join-Path $testRoot 'startup-failure-home'
    [IO.Directory]::CreateDirectory($startupSource) | Out-Null
    [IO.File]::WriteAllText((Join-Path $startupSource 'App.ps1'), "# App-Version: 0.1.0`nparam([string]`$Mode,[string]`$HomePath,[switch]`$NoBrowser,[int]`$Port)`nexit 23", $script:AgentEncoding)
    [IO.File]::WriteAllText((Join-Path $startupSource 'index.html'), '<meta name="app-version" content="0.1.0">', $script:AgentEncoding)
    [IO.File]::WriteAllText((Join-Path $startupSource '業務エージェント.cmd'), '@echo off', $script:AgentEncoding)
    $startupError = Join-Path $testRoot 'startup-error.txt'
    Set-TestReleaseBinding $startupSource
    $startupArguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -STA -File "' + $script:AgentAppPath + '" -Mode Bootstrap -SourcePath "' + $startupSource + '" -HomePath "' + $startupHome + '" -NoBrowser'
    $startupProcess = Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -ArgumentList $startupArguments -WindowStyle Hidden -RedirectStandardError $startupError -PassThru
    try {
        Assert-True ($startupProcess.WaitForExit(7000)) 'Bootstrap promptly detects failed owned Serve process'
        Assert-True ($startupProcess.ExitCode -ne 0 -and [IO.File]::ReadAllText($startupError).Contains('SERVER_FAILED')) 'Bootstrap reports startup failure with a nonzero exit'
    } finally { if (-not $startupProcess.HasExited) { Stop-Process -Id $startupProcess.Id -Force } }
    [IO.File]::WriteAllText((Join-Path $source 'index.html'), '<meta name="app-version" content="9.0.0">', $script:AgentEncoding)
    Assert-Throws { Sync-AgentRelease $homeDirectory $source } 'versions differ' 'Mixed release cannot fall back'
    [IO.File]::Delete((Join-Path $source 'App.ps1'))
    Assert-Throws { Sync-AgentRelease $homeDirectory $source } 'Missing App.ps1' 'Reachable incomplete release cannot fall back'
    [IO.File]::AppendAllText((Join-Path $second 'index.html'), 'corrupt')
    Assert-Throws { Get-AgentCachedRelease $homeDirectory } 'integrity' 'Cache corruption detected'
    $id = [guid]::NewGuid().ToString('N')
    $planner = @{ request_id = $id; state = 'ACT'; message = 'DONEという文字を含む説明'; robin = "SET X TO '日本語 100%`n`"引用`"'"; artifacts = @() } | ConvertTo-Json -Compress
    $parsed = Get-AgentPlannerResponse $planner $id
    Assert-True ($parsed.state -ceq 'ACT' -and $parsed.robin.Contains('100%')) 'Strict state ignores DONE substring and preserves Robin'
    Assert-Throws { Get-AgentPlannerResponse ('```json' + $planner + '```') $id } 'JSON|Invalid' 'Fenced JSON rejected'
    Assert-Throws { Get-AgentPlannerResponse $planner ([guid]::NewGuid().ToString('N')) } 'contract' 'Mismatched request ID rejected'
    Assert-Throws { ConvertFrom-AgentJson '{"a":1,"a":2}' @('a') } 'Duplicate' 'Duplicate JSON fields rejected'
    Assert-Throws { ConvertFrom-AgentJson '{"a":1,"extra":2}' @('a') } 'Unexpected' 'Extra JSON fields rejected'
    $overlongPlan = ConvertFrom-Json -InputObject $planner
    $overlongPlan | Add-Member -NotePropertyName ai_calls -NotePropertyValue @([pscustomobject]@{ ai_call_id = [guid]::NewGuid().ToString('N'); operation = 'summarize'; input_path = (Join-Path $testRoot 'input.txt'); instructions = ''; labels = @(); timeout_seconds = 241 })
    Assert-Throws { Get-AgentPlannerResponse (ConvertTo-Json -InputObject $overlongPlan -Depth 10 -Compress) $id } 'Invalid AI call specification' 'Planner rejects AiCall timeout above 240 seconds'
    Assert-Throws { Assert-AgentPathUnder (Join-Path $testRoot 'other.txt') (Join-Path $testRoot 'root') } 'outside' 'Sibling path rejected'
    Assert-Throws { Assert-AgentPathUnder (Join-Path $testRoot 'root\..\outside.txt') (Join-Path $testRoot 'root') } 'outside' 'Traversal normalized and rejected'
    Assert-Throws { Assert-AgentId '../x' } 'INVALID_ID' 'Traversal job ID rejected'
    Assert-True ((Get-AgentFullPath ([IO.Path]::GetPathRoot($workspace))) -ceq [IO.Path]::GetPathRoot($workspace)) 'Drive root remains absolute'
    $input = Join-Path $testRoot 'input.txt'
    [IO.File]::WriteAllText($input, "最初の行 100%`n次の行 `"引用`"", $script:AgentEncoding)
    $script:AiMode = 'success'; $script:AiSent = 0; $script:AiContext = $null
    function Invoke-AgentCopilot {
        param($Prompt,$RequestId,$Settings,$HomePath,$CancelPath,$TimeoutSeconds)
        $script:AiSent++
        $script:LastAiPrompt = $Prompt
        if ($script:AiMode -ceq 'timeout') { throw 'RESPONSE_TIMEOUT: Test timeout.' }
        if ($script:AiMode -ceq 'auth') { throw 'AUTH_REQUIRED: Test auth.' }
        if ($script:AiMode -ceq 'refusal') { throw 'REFUSAL: Test refusal.' }
        $request = $script:AiContext.request
        $text = "Translated 100%`n`"quoted`""
        if ($script:AiMode -ceq 'empty') { $text = '' }
        $response = @{ request_id = $RequestId; job_id = $request.job_id; run_id = $request.run_id; ai_call_id = $request.ai_call_id; status = 'success'; result = $text; error_type = ''; input_count = 1; output_count = 1 }
        if ($script:AiMode -cin @('review-unknown','review-label')) { $response.status='needs_review'; $response.error_type='review_required'; if($script:AiMode -ceq 'review-label'){$response.result='要確認'} }
        if ($script:AiMode -ceq 'wrong-id') { $response.run_id = [guid]::NewGuid().ToString('N') }
        return ConvertTo-Json -InputObject $response -Compress
    }
    $script:AiContext = New-TestAiCall $homeDirectory $input
    $ai = Invoke-AgentAiCall $homeDirectory $script:AiContext.request_path $script:AiContext.result_path
    Assert-True ($ai.status -ceq 'success' -and $ai.result -ceq "Translated 100%`n`"quoted`"") 'AiCall preserves business text'
    Assert-True ($script:LastAiPrompt.Contains('Return one compact JSON object with exactly request_id,job_id,run_id,ai_call_id,status,result,error_type,input_count,output_count, carried in the numbered text-fence parts defined by the appended transport instructions.') -and $script:LastAiPrompt.Contains('preserve the final JSON schema and escape string newlines using JSON rules.')) 'Actual AiCall prompt preserves its exact JSON schema while using numbered raw JSON fragments'
    Assert-True ($script:LastAiPrompt -notmatch 'Return only JSON|Return exactly one JSON object|For line 1 inside') 'Actual AiCall prompt has no JSON-only whole-response or first-line-only instruction'
    Assert-True ([IO.File]::ReadAllText((Join-Path $script:AiContext.directory 'status.txt')) -ceq 'success') 'PAD status companion written'
    Assert-True ((Read-AgentJson $script:AiContext.result_path).ai_call_id -ceq $script:AiContext.request.ai_call_id) 'Result uses same call ID'
    $before = Get-AgentHash $script:AiContext.result_path
    Assert-Throws { Invoke-AgentAiCall $homeDirectory $script:AiContext.request_path $script:AiContext.result_path } 'REPLAY_BLOCKED' 'Duplicate call never resends'
    Assert-True ($script:AiSent -eq 1 -and (Get-AgentHash $script:AiContext.result_path) -ceq $before) 'Replay preserves original result'
    foreach ($case in @(@('timeout','timeout'),@('auth','auth_required'),@('refusal','refusal'),@('empty','empty_result'),@('wrong-id','invalid_response'))) {
        $script:AiMode = $case[0]; $script:AiContext = New-TestAiCall $homeDirectory $input
        $ai = Invoke-AgentAiCall $homeDirectory $script:AiContext.request_path $script:AiContext.result_path
        Assert-True ($ai.status -ceq 'failed' -and $ai.error_type -ceq $case[1] -and $ai.output_count -eq 0) ('AiCall distinguishes ' + $case[0])
        Assert-True (-not (Test-Path -LiteralPath (Join-Path $script:AiContext.directory 'result.txt'))) ('No success companion for ' + $case[0])
    }
    $script:AiMode = 'success'; $script:AiContext = New-TestAiCall $homeDirectory $input
    $outside = Join-Path $testRoot 'arbitrary-result.json'
    Assert-Throws { Invoke-AgentAiCall $homeDirectory $script:AiContext.request_path $outside } 'Result must' 'Arbitrary result file rejected'
    Assert-True (-not (Test-Path -LiteralPath $outside)) 'Rejected result path not created'
    [IO.File]::WriteAllText((Join-Path $script:AiContext.job_directory 'cancel'), 'stop')
    $sentBefore = $script:AiSent
    $ai = Invoke-AgentAiCall $homeDirectory $script:AiContext.request_path $script:AiContext.result_path
    Assert-True ($ai.status -ceq 'cancelled' -and $script:AiSent -eq $sentBefore) 'Cancellation prevents AI send'
    $script:AiContext = New-TestAiCall $homeDirectory $input
    $active = Join-Path $script:AiContext.job_directory 'active-run.json'
    $value = Read-AgentJson $active; $value.run_id = [guid]::NewGuid().ToString('N'); Write-AgentJson $active $value
    Assert-Throws { Invoke-AgentAiCall $homeDirectory $script:AiContext.request_path $script:AiContext.result_path } 'INVALID_CONTEXT' 'Stale run cannot invoke AI'
    $script:AiContext = New-TestAiCall $homeDirectory $input
    $script:AiContext.request.operation = 'classify'; $script:AiContext.request.labels = @('確認済み','要確認')
    Write-AgentJson $script:AiContext.request_path $script:AiContext.request
    $ai = Invoke-AgentAiCall $homeDirectory $script:AiContext.request_path $script:AiContext.result_path
    Assert-True ($ai.status -ceq 'failed' -and $ai.error_type -ceq 'invalid_response') 'Classification rejects results outside label candidates'
    foreach($reviewMode in @('review-unknown','review-label')) {
        $script:AiMode=$reviewMode; $script:AiContext=New-TestAiCall $homeDirectory $input
        $script:AiContext.request.operation='classify'; $script:AiContext.request.labels=@('確認済み','要確認')
        Write-AgentJson $script:AiContext.request_path $script:AiContext.request
        $ai=Invoke-AgentAiCall $homeDirectory $script:AiContext.request_path $script:AiContext.result_path
        if($reviewMode -ceq 'review-unknown') {
            Assert-True ($ai.status -ceq 'failed' -and $ai.error_type -ceq 'invalid_response' -and -not (Test-Path (Join-Path $script:AiContext.directory 'result.txt'))) 'Needs-review classification cannot pass an unknown label to a PAD ELSE branch'
        } else {
            Assert-True ($ai.status -ceq 'needs_review' -and $ai.result -ceq '要確認' -and $ai.error_type -ceq 'review_required') 'Valid classification label retains needs-review status'
        }
    }
    $script:AiMode='success'
    $script:AiContext = New-TestAiCall $homeDirectory $input
    $script:AiContext.request.operation = 'classify'
    Write-AgentJson $script:AiContext.request_path $script:AiContext.request
    $sentBefore = $script:AiSent
    $ai = Invoke-AgentAiCall $homeDirectory $script:AiContext.request_path $script:AiContext.result_path
    Assert-True ($ai.status -ceq 'failed' -and $script:AiSent -eq $sentBefore) 'Classification requires explicit candidate labels'
    foreach ($timeout in @(240,241)) {
        $script:AiContext = New-TestAiCall $homeDirectory $input
        $script:AiContext.request.timeout_seconds = $timeout
        Write-AgentJson $script:AiContext.request_path $script:AiContext.request
        $sentBefore = $script:AiSent
        $timeoutResult = Invoke-AgentAiCall $homeDirectory $script:AiContext.request_path $script:AiContext.result_path
        if ($timeout -eq 240) { Assert-True ($timeoutResult.status -ceq 'success') 'AiCall accepts the shared 240-second upper boundary' }
        else { Assert-True ($timeoutResult.status -ceq 'failed' -and $script:AiSent -eq $sentBefore) 'AiCall rejects 241 seconds before sending' }
    }
    foreach ($sizeCase in @('ascii200kb','json-expansion','file-over-limit','bounded-ascii')) {
        $sizeInput = Join-Path $testRoot ($sizeCase + '.txt')
        $sizeText = switch ($sizeCase) { 'ascii200kb' { 'a' * 204800 }; 'json-expansion' { ([string][char]1) * 40000 }; 'file-over-limit' { 'a' * 262145 }; default { 'a' * 130000 } }
        [IO.File]::WriteAllText($sizeInput, $sizeText, $script:AgentEncoding)
        $script:AiContext = New-TestAiCall $homeDirectory $sizeInput
        $sentBefore = $script:AiSent
        $sizeResult = Invoke-AgentAiCall $homeDirectory $script:AiContext.request_path $script:AiContext.result_path
        if ($sizeCase -ceq 'bounded-ascii') { Assert-True ($sizeResult.status -ceq 'success' -and $script:LastAiPrompt.Length -le 180000) 'Bounded complete AiCall text is sent without truncation' }
        else { Assert-True ($sizeResult.status -ceq 'failed' -and $sizeResult.error_type -ceq 'input_too_large' -and $script:AiSent -eq $sentBefore) ('AiCall checks complete serialized request before sending: ' + $sizeCase) }
    }
    # Controller-observed bytes become bounded, exact UTF-8 observations and read grants.
    $priorJob = New-TestJob $homeDirectory $input 'running_pad'
    $priorJobDirectory = Get-AgentJobDirectory $homeDirectory $priorJob.job_id
    $priorRunId = [guid]::NewGuid().ToString('N'); $nextRunId = [guid]::NewGuid().ToString('N')
    $priorRun = Join-Path $priorJobDirectory ('runs\' + $priorRunId)
    $nextRun = Join-Path $priorJobDirectory ('runs\' + $nextRunId)
    foreach ($runPath in @($priorRun,$nextRun)) { [IO.Directory]::CreateDirectory((Join-Path $runPath 'artifacts')) | Out-Null }
    $priorFile = Join-Path $priorRun 'artifacts\prior.txt'
    $unobservedFile = Join-Path $priorRun 'artifacts\unobserved.txt'
    $exactObservedText = "  Round-one marker 日本語 100% C:\input\path `"quoted`"`r`nsecond line  `r`n"
    [IO.File]::WriteAllText($priorFile, $exactObservedText, (New-Object Text.UTF8Encoding($true)))
    [IO.File]::WriteAllText($unobservedFile, 'not controller observed', $script:AgentEncoding)
    $priorRecords = Get-AgentObservedArtifacts ([pscustomobject]@{ status = 'success'; artifacts = @($priorFile) }) $priorRun
    Assert-True ($priorRecords[0].content -ceq $exactObservedText -and $priorRecords[0].text_status -ceq 'complete' -and -not $priorRecords[0].truncated) 'Observation preserves exact text including spaces, percent, backslashes, quotes and CRLF'
    Assert-True ($priorRecords[0].byte_count -eq (Get-Item -LiteralPath $priorFile).Length -and $priorRecords[0].sha256 -ceq (Get-AgentHash $priorFile)) 'Observation bytes and hash describe the sampled file including encoding BOM'
    $limited = Get-AgentObservedArtifacts ([pscustomobject]@{ status = 'success'; artifacts = @($priorFile) }) $priorRun 5
    Assert-True ($limited[0].content -ceq $exactObservedText.Substring(0,5) -and $limited[0].truncated -and $limited[0].text_status -ceq 'truncated') 'Observation budget produces an explicitly labeled exact prefix'
    $invalidUtf8 = Join-Path $priorRun 'artifacts\invalid.txt'
    [IO.File]::WriteAllBytes($invalidUtf8, [byte[]]@(255,254,65,0))
    $unavailable = Get-AgentObservedArtifacts ([pscustomobject]@{ status = 'success'; artifacts = @($invalidUtf8) }) $priorRun
    Assert-True ($unavailable[0].text_status -ceq 'unavailable' -and $unavailable[0].text_error -ceq 'invalid_utf8' -and $unavailable[0].content -ceq '') 'Non-UTF8 output is labeled unavailable instead of decoded with another encoding'
    $largeFiles = @()
    foreach ($number in @(1,2,3)) {
        $large = Join-Path $priorRun ('artifacts\large-' + $number + '.txt')
        [IO.File]::WriteAllText($large, ('a' * 12000), $script:AgentEncoding); $largeFiles += $large
    }
    $bounded = Get-AgentObservedArtifacts ([pscustomobject]@{ status = 'success'; artifacts = $largeFiles }) $priorRun 10000
    Assert-True (($bounded | Measure-Object -Property sample_character_count -Sum).Sum -eq 10000 -and $bounded[0].content.Length -eq 8192 -and $bounded[2].content.Length -eq 0) 'Multiple outputs share the total budget and per-file 8192 character cap'
    $priorJob | Add-Member -NotePropertyName observed_artifacts -NotePropertyValue $priorRecords -Force
    Save-AgentJob $priorJobDirectory $priorJob
    $priorRead = 'File.ReadTextFromFile.ReadText File: ' + (ConvertTo-AgentRobinLiteral $priorFile) + ' Encoding: File.TextFileEncoding.UTF8 Content=> PriorText'
    $unobservedRead = 'File.ReadTextFromFile.ReadText File: ' + (ConvertTo-AgentRobinLiteral $unobservedFile) + ' Encoding: File.TextFileEncoding.UTF8 Content=> PriorText'
    $null = & $script:ProductionRobin -Robin $priorRead -RunDirectory $nextRun -Job $priorJob
    Assert-True $true 'Later Robin may read the exact verified prior output'
    Assert-Throws { & $script:ProductionRobin -Robin $unobservedRead -RunDirectory $nextRun -Job $priorJob } 'ROBIN_PATH' 'Later Robin cannot read an unobserved sibling output'
    $callSpec = [pscustomobject]@{ ai_call_id = [guid]::NewGuid().ToString('N'); operation = 'summarize'; input_path = $priorFile; instructions = '要約'; labels = @(); timeout_seconds = 15 }
    $priorTemplate = @(New-AgentAiCallTemplates -Calls @($callSpec) -Job $priorJob -RunDirectory $nextRun -RunId $nextRunId -AppPath $script:AgentAppPath -HomePath $homeDirectory)[0]
    Assert-True ((Read-AgentJson $priorTemplate.request_path).input_path -ceq $priorFile) 'AiCall template accepts only the verified prior file'
    Write-AgentJson (Join-Path $priorJobDirectory 'active-run.json') @{ job_id = $priorJob.job_id; run_id = $nextRunId; status = 'pad_running'; run_directory = $nextRun; app_path = $script:AgentAppPath }
    $script:AiContext = [pscustomobject]@{ request = (Read-AgentJson $priorTemplate.request_path) }; $script:AiMode = 'success'
    $priorAi = Invoke-AgentAiCall $homeDirectory $priorTemplate.request_path $priorTemplate.result_path
    $priorPayload = ConvertFrom-Json -InputObject $script:LastAiPrompt.Substring($script:LastAiPrompt.IndexOf("REQUEST_JSON:`n") + "REQUEST_JSON:`n".Length)
    Assert-True ($priorAi.status -ceq 'success' -and $priorPayload.input -ceq $exactObservedText) 'Later AiCall reads the exact prior bytes and preserves text in its business request'
    $callSpec.ai_call_id = [guid]::NewGuid().ToString('N'); $callSpec.input_path = $unobservedFile
    Assert-Throws { New-AgentAiCallTemplates -Calls @($callSpec) -Job $priorJob -RunDirectory $nextRun -RunId $nextRunId -AppPath $script:AgentAppPath -HomePath $homeDirectory } 'ROBIN_PATH' 'AiCall template denies an unobserved prior file'
    $callSpec.ai_call_id = [guid]::NewGuid().ToString('N'); $callSpec.input_path = $priorFile
    $unobservedTemplate = @(New-AgentAiCallTemplates -Calls @($callSpec) -Job $priorJob -RunDirectory $nextRun -RunId $nextRunId -AppPath $script:AgentAppPath -HomePath $homeDirectory)[0]
    $tamperedInput = Read-AgentJson $unobservedTemplate.request_path; $tamperedInput.input_path = $unobservedFile
    Write-AgentJson $unobservedTemplate.request_path $tamperedInput
    $sentBefore = $script:AiSent
    $unobservedAi = Invoke-AgentAiCall $homeDirectory $unobservedTemplate.request_path $unobservedTemplate.result_path
    Assert-True ($unobservedAi.status -ceq 'failed' -and $script:AiSent -eq $sentBefore) 'AiCall itself denies an unobserved prior file even if request metadata is changed'
    $callSpec.ai_call_id = [guid]::NewGuid().ToString('N'); $callSpec.input_path = $priorFile
    $changedTemplate = @(New-AgentAiCallTemplates -Calls @($callSpec) -Job $priorJob -RunDirectory $nextRun -RunId $nextRunId -AppPath $script:AgentAppPath -HomePath $homeDirectory)[0]
    [IO.File]::AppendAllText($priorFile, 'changed')
    Assert-Throws { & $script:ProductionRobin -Robin $priorRead -RunDirectory $nextRun -Job $priorJob } 'PRIOR_ARTIFACT_CHANGED' 'Later Robin denies a changed prior artifact'
    $callSpec.ai_call_id = [guid]::NewGuid().ToString('N')
    Assert-Throws { New-AgentAiCallTemplates -Calls @($callSpec) -Job $priorJob -RunDirectory $nextRun -RunId $nextRunId -AppPath $script:AgentAppPath -HomePath $homeDirectory } 'PRIOR_ARTIFACT_CHANGED' 'AiCall template denies a changed prior artifact'
    $sentBefore = $script:AiSent
    $changedAi = Invoke-AgentAiCall $homeDirectory $changedTemplate.request_path $changedTemplate.result_path
    Assert-True ($changedAi.status -ceq 'failed' -and $script:AiSent -eq $sentBefore) 'AiCall rechecks prior artifact hash before sending any business data'
    # Fingerprints ignore only controller-issued run/call identities, not business contracts.
    $fingerprintTemplates = @()
    foreach ($fpRun in @($priorRun,$nextRun)) {
        $pair = @()
        foreach ($slot in @(1,2)) { $pair += Get-AgentAiCallTemplate -AiCallId ([guid]::NewGuid().ToString('N')) -Job $priorJob -RunDirectory $fpRun -RunId ([IO.Path]::GetFileName($fpRun)) -AppPath $script:AgentAppPath -HomePath $homeDirectory }
        $fingerprintTemplates += ,$pair
    }
    $fingerprintPlans = @()
    for ($number = 0; $number -lt 2; $number++) {
        $fpRun = @($priorRun,$nextRun)[$number]; $pair = $fingerprintTemplates[$number]
        $contracts = @(
            [pscustomobject]@{ ai_call_id = $pair[0].ai_call_id; operation = 'translate'; input_path = (Join-Path $fpRun 'artifacts\input.txt'); instructions = '日本語を英訳'; labels = @(); timeout_seconds = 120 },
            [pscustomobject]@{ ai_call_id = $pair[1].ai_call_id; operation = 'classify'; input_path = $pair[0].text_path; instructions = '分類'; labels = @('確認済み','要確認'); timeout_seconds = 120 }
        )
        $fingerprintPlans += [pscustomobject]@{ request_id = [guid]::NewGuid().ToString('N'); message = '今回の説明'; robin = ($pair[0].robin + "`r`n" + $pair[1].robin); ai_calls = $contracts }
    }
    $originalRobin = $fingerprintPlans[0].robin
    $firstFingerprint = Get-AgentPlanFingerprint $fingerprintPlans[0] $priorRun $fingerprintTemplates[0]
    $secondFingerprint = Get-AgentPlanFingerprint $fingerprintPlans[1] $nextRun $fingerprintTemplates[1]
    Assert-True ($firstFingerprint -ceq $secondFingerprint -and $fingerprintPlans[0].robin -cne $fingerprintPlans[1].robin) 'New run roots and new reserved IDs do not disguise identical ordered AI operations'
    Assert-True ($fingerprintPlans[0].robin -ceq $originalRobin -and $originalRobin.Contains($fingerprintTemplates[0][0].ai_call_id)) 'Fingerprint normalization never changes executable Robin'
    $canonicalOutput = Join-Path $nextRun 'artifacts\case-output.txt'
    $equivalentOutput = $nextRun.ToUpperInvariant().Replace('\','/') + '/ARTIFACTS/./case-output.txt'
    $readPaths = @($input,$input.ToUpperInvariant().Replace('\','/'))
    $writePaths = @($canonicalOutput,$equivalentOutput)
    $pathPlans = @()
    for ($pathCase = 0; $pathCase -lt 2; $pathCase++) {
        $code = 'File.ReadTextFromFile.ReadText File: ' + (ConvertTo-AgentRobinLiteral $readPaths[$pathCase]) + ' Encoding: File.TextFileEncoding.UTF8 Content=> InputText'
        $code += "`r`nSET Label TO " + (ConvertTo-AgentRobinLiteral 'MiXeD business text')
        $code += "`r`nFile.WriteText File: " + (ConvertTo-AgentRobinLiteral $writePaths[$pathCase]) + ' TextToWrite: Label AppendNewLine: False IfFileExists: File.IfFileExists.Append Encoding: File.FileEncoding.UTF8'
        $null = & $script:ProductionRobin -Robin $code -RunDirectory $nextRun -Job $priorJob
        $pathPlans += [pscustomobject]@{ robin = $code; ai_calls = @() }
    }
    Assert-True ((Get-AgentPlanFingerprint $pathPlans[0] $nextRun @()) -ceq (Get-AgentPlanFingerprint $pathPlans[1] $nextRun @())) 'Validator-accepted case, dot segments and mixed slash paths have the same fingerprint'
    $businessCase = [pscustomobject]@{ robin = $pathPlans[0].robin.Replace('MiXeD business text','mixed business text'); ai_calls = @() }
    Assert-True ((Get-AgentPlanFingerprint $businessCase $nextRun @()) -cne (Get-AgentPlanFingerprint $pathPlans[0] $nextRun @())) 'Fingerprint does not case-normalize general business text'
    $equivalentContract = ConvertFrom-Json -InputObject (ConvertTo-Json -InputObject $fingerprintPlans[1] -Depth 10)
    $equivalentContract.ai_calls[0].input_path = $nextRun.ToUpperInvariant().Replace('\','/') + '/ARTIFACTS/./input.txt'
    Assert-True ((Get-AgentPlanFingerprint $equivalentContract $nextRun $fingerprintTemplates[1]) -ceq $secondFingerprint) 'AiCall input path uses the same canonical Windows path comparison'
    foreach ($contractField in @('operation','instructions','input_path','labels','timeout_seconds')) {
        $altered = ConvertFrom-Json -InputObject (ConvertTo-Json -InputObject $fingerprintPlans[1] -Depth 10)
        switch ($contractField) {
            'operation' { $altered.ai_calls[0].operation = 'summarize' }
            'instructions' { $altered.ai_calls[0].instructions = '別の業務条件で要約' }
            'input_path' { $altered.ai_calls[0].input_path = Join-Path $nextRun 'artifacts\other-input.txt' }
            'labels' { $altered.ai_calls[1].labels = @('新しい分類','要確認') }
            'timeout_seconds' { $altered.ai_calls[0].timeout_seconds = 60 }
        }
        Assert-True ((Get-AgentPlanFingerprint $altered $nextRun $fingerprintTemplates[1]) -cne $firstFingerprint) ('Changed business contract remains distinguishable: ' + $contractField)
    }
    # Run contracts use deterministic adapters and actual local artifact files.
    $script:RunMode = 'success'; $script:Plans = 0; $script:PadRuns = 0; $script:Output = ''; $script:PadRunIds = @()
    $script:ObservedMarker = "  ROUND_ONE_VALUE 日本語 100% C:\data `"quotes`"`r`nline two  `r`n"
    function Invoke-AgentCopilot {
        param($Prompt,$RequestId,$Settings,$HomePath,$CancelPath,$TimeoutSeconds,$Transport)
        $script:Plans++
        $script:LastPlannerPrompt = $Prompt; $script:LastPlannerTransport = $Transport
        $contextStart = $Prompt.IndexOf("CONTEXT_JSON:`n") + "CONTEXT_JSON:`n".Length
        $contextEnd = $Prompt.IndexOf("`nAn optional", $contextStart)
        $script:LastPlannerContext = ConvertFrom-Json -InputObject $Prompt.Substring($contextStart, $contextEnd - $contextStart)
        $plan = @{ request_id = $RequestId; state = 'ACT'; message = '一回実行'; robin = "SET Text TO 'テスト 100%'"; artifacts = @() }
        if ($script:Plans -gt 1 -or $script:RunMode -ceq 'false-done') { $plan.state = 'DONE'; $plan.message = '完了しました。'; $plan.robin = ''; $plan.artifacts = @($script:Output) }
        if ($plan.state -ceq 'DONE' -and $script:RunMode -cin @('aliased-done','truncated-aliased')) { $plan.artifacts=@($script:Output.Replace('\','\\')) }
        if ($script:RunMode -ceq 'blocked') { $plan.state = 'BLOCKED'; $plan.robin = ''; $plan.message = '許可範囲が不明です。' }
        if ($script:RunMode -ceq 'max') { $plan.state = 'ACT'; $plan.robin = 'SET X TO 1' }
        if ($script:RunMode -ceq 'ask' -and $script:Plans -eq 2) { $plan.state = 'ASK_USER'; $plan.robin = ''; $plan.artifacts = @(); $plan.message = '丁寧な英語にしますか？' }
        if ($script:RunMode -ceq 'two-act' -and $script:Plans -eq 2) {
            $plan.state = 'ACT'; $plan.artifacts = @(); $plan.message = '観測した値を次の成果物へ使います。'
            $plan.robin = 'File.ReadTextFromFile.ReadText File: ' + (ConvertTo-AgentRobinLiteral $script:Output) + ' Encoding: File.TextFileEncoding.UTF8 Content=> PriorText'
        }
        if ($script:RunMode -cin @('failed-retry','failed-auth','failed-setup') -and $script:Plans -eq 2) { $plan.state = 'ACT'; $plan.robin = "SET Text TO 'テスト 100%'"; $plan.artifacts = @() }
        if ($script:RunMode -ceq 'failed-clipboard' -and $script:Plans -eq 2) { $plan.state = 'ACT'; $plan.robin = "SET Different TO 'changed action'"; $plan.artifacts = @() }
        if ($script:RunMode -ceq 'failed-replan' -and $script:Plans -eq 2) { $plan.state = 'BLOCKED'; $plan.robin = ''; $plan.artifacts = @(); $plan.message = '失敗内容の確認が必要です。' }
        if ($script:RunMode -ceq 'failed-change' -and $script:Plans -eq 2) { $plan.state = 'ACT'; $plan.robin = 'SET ChangedApproach TO 1'; $plan.artifacts = @(); $plan.message = '観測した失敗を踏まえて手順を変更します。' }
        if ($script:RunMode -cin @('failed-new-ids','failed-new-business') -and $script:Plans -le 2) {
            $template = $script:LastPlannerContext.ai_call_templates[0]
            $plan.state = 'ACT'; $plan.robin = $template.robin; $plan.artifacts = @()
            $instruction = '日本語を英訳する'
            if ($script:RunMode -ceq 'failed-new-business' -and $script:Plans -eq 2) { $instruction = '固有名詞を原文のまま残して英訳する' }
            $plan.ai_calls = @([pscustomobject]@{ ai_call_id = $template.ai_call_id; operation = 'translate'; input_path = $script:LastPlannerContext.target; instructions = $instruction; labels = @(); timeout_seconds = 15 })
        }
        return ConvertTo-Json -InputObject $plan -Depth 10 -Compress
    }
    function Test-AgentRobin { param($Robin,$RunDirectory,$Job) }
    function Invoke-AgentPad {
        param($Robin,$RunDirectory,$RunId,$Job,$Settings,$CancelPath)
        $script:PadRuns++
        $script:PadRunIds += $RunId
        if ($script:RunMode -ceq 'unknown') { return [pscustomobject]@{ status = 'unknown'; error = '実行結果不明'; artifacts = @() } }
        if ($script:RunMode.StartsWith('failed-') -and $script:PadRuns -eq 1) {
            $errorValue = 'PAD_RUNTIME_ERROR: confirmed failure marker'
            if ($script:RunMode -ceq 'failed-auth') { $errorValue = 'AICALL_auth_required' }
            if ($script:RunMode -ceq 'failed-setup') { $errorValue = 'PAD_SETUP: dedicated designer unavailable' }
            if ($script:RunMode -ceq 'failed-clipboard') { $errorValue = 'PAD_CLIPBOARD: original data cannot be captured' }
            return [pscustomobject]@{ status = 'failed'; error = $errorValue; artifacts = @(); ai_calls = @([pscustomobject]@{ ai_call_id = ('f' * 32); status = 'failed'; input_count = 1; output_count = 0; error_type = 'processing_failed' }) }
        }
        if ($script:RunMode -ceq 'two-act' -and $script:PadRuns -eq 2) { $null = & $script:ProductionRobin -Robin $Robin -RunDirectory $RunDirectory -Job $Job }
        $artifacts = Join-Path $RunDirectory 'artifacts'; [IO.Directory]::CreateDirectory($artifacts) | Out-Null
        $script:Output = Join-Path $artifacts 'translated.txt'; [IO.File]::WriteAllText($script:Output, $script:ObservedMarker, $script:AgentEncoding)
        if ($script:RunMode -cin @('truncated','truncated-aliased')) { [IO.File]::WriteAllText($script:Output, ('x' * 9000), $script:AgentEncoding) }
        if ($script:RunMode -ceq 'unavailable') { [IO.File]::WriteAllBytes($script:Output, [byte[]]@(255,254,65,0)) }
        return [pscustomobject]@{ status = 'success'; error = ''; artifacts = @($script:Output) }
    }
    $job = New-TestJob $homeDirectory $input
    $completed = Invoke-AgentRun $homeDirectory $job.job_id
    Assert-True ($completed.status -ceq 'done' -and $script:Plans -eq 2 -and $script:PadRuns -eq 1) 'Run observes PAD then plans DONE without repeating PAD'
    Assert-True ($script:LastPlannerTransport -ceq 'PlannerV2' -and $script:LastPlannerPrompt.Contains('Metadata fields are request_id,state,message,artifacts; the separate body supplies robin.') -and $script:LastPlannerPrompt.Contains('Include ai_calls whenever ACT uses any supplied ai_call_templates[].robin action.') -and -not $script:LastPlannerPrompt.Contains('numbered text-fence parts')) 'Actual Run selects Planner V2 while preserving required AiCall declarations and separating metadata from literal Robin'
    Assert-True ($script:LastPlannerPrompt -notmatch 'Return only JSON|Return exactly one JSON object|For line 1 inside') 'Actual planner prompt has no JSON-only whole-response or first-line-only instruction'
    Assert-True ($script:LastPlannerPrompt -notmatch 'second Planner V2 fence|two text fences') 'Single-fence planner instructions contain no stale second-fence directive'
    Assert-True ($script:LastPlannerPrompt -cnotmatch 'JSON robin string|JSON-encode the whole robin string|four in the response JSON source|then JSON-encode the complete') 'The actual full Planner V2 prompt contains no old whole-Robin JSON serialization instruction'
    Assert-True ($completed.artifacts.Count -eq 1 -and $completed.final_answer -ceq '完了しました。') 'Run exposes final answer and observed artifact'
    Assert-True ($script:LastPlannerContext.observations[0].artifact_observations[0].content -ceq $script:ObservedMarker) 'Second planner request contains actual first-round output content exactly'
    Assert-True ($completed.observed_artifacts[0].sha256 -ceq (Get-AgentHash $script:Output)) 'Durable job state retains the exact verified output grant'
    Assert-Throws { Invoke-AgentRun $homeDirectory $job.job_id } 'REPLAY_BLOCKED' 'Job restart never reexecutes'
    $script:RunMode = 'ask'; $script:Plans = 0; $script:PadRuns = 0
    $job = New-TestJob $homeDirectory $input
    $script:AskAnswerPath = Join-Path (Get-AgentJobDirectory $homeDirectory $job.job_id) 'answer.json'
    function Start-Sleep {
        param($Milliseconds)
        $askingJob = Read-AgentJson (Join-Path ([IO.Path]::GetDirectoryName($script:AskAnswerPath)) 'job.json')
        Write-AgentJson $script:AskAnswerPath @{ question_id = $askingJob.question_id; answer = 'はい。100%そのまま保持してください。' }
    }
    $answered = Invoke-AgentRun $homeDirectory $job.job_id
    Remove-Item -LiteralPath Function:\Start-Sleep
    Assert-True ($answered.status -ceq 'done' -and $script:Plans -eq 3 -and $script:PadRuns -eq 1) 'ASK_USER resumes with one user answer and no repeated PAD run'
    Assert-True ($script:LastPlannerPrompt.Contains('100%そのまま保持してください。')) 'Question answer is preserved in subsequent planner context'
    Assert-True ($answered.question_id -ceq '') 'Question identity is cleared after the matching answer is consumed'
    foreach ($modeValue in @('two-act','aliased-done','truncated','truncated-aliased','unavailable','failed-replan','failed-retry','failed-auth','failed-setup','failed-clipboard','failed-change','failed-new-ids','failed-new-business')) {
        $script:RunMode = $modeValue; $script:Plans = 0; $script:PadRuns = 0; $script:PadRunIds = @()
        $job = New-TestJob $homeDirectory $input
        $checked = Invoke-AgentRun $homeDirectory $job.job_id
        if ($modeValue -ceq 'two-act') {
            Assert-True ($checked.status -ceq 'done' -and $script:Plans -eq 3 -and $script:PadRuns -eq 2) 'Two ACT rounds can read an exact prior output before a final DONE'
            Assert-True ($script:LastPlannerContext.observations[0].artifact_observations[0].content -ceq $script:ObservedMarker -and $script:LastPlannerContext.prior_readable_artifacts.Count -eq 2) 'Later context keeps observed content and exact prior read grants'
        } elseif ($modeValue -ceq 'aliased-done') {
            Assert-True ($checked.status -ceq 'done' -and $checked.artifacts.Count -eq 1 -and $checked.artifacts[0].path -ceq $script:Output -and $script:PadRuns -eq 1) 'DONE resolves repeated path separators to the observed artifact without repeating PAD'
        } elseif ($modeValue -cin @('truncated','truncated-aliased','unavailable')) {
            $expectedTextStatus=if($modeValue -ceq 'truncated-aliased'){'truncated'}else{$modeValue}
            Assert-True ($checked.status -ceq 'blocked' -and $script:LastPlannerContext.observations[0].artifact_observations[0].text_status -ceq $expectedTextStatus) ('DONE is blocked for ' + $modeValue + ' output content')
        } elseif ($modeValue -cin @('failed-change','failed-new-business')) {
            Assert-True ($checked.status -ceq 'done' -and $script:PadRuns -eq 2 -and $script:Plans -eq 3) 'A definite failure may be followed by an explicitly changed planner action'
            Assert-True (($script:PadRunIds | Select-Object -Unique).Count -eq 2) 'Replanned action uses a fresh run identity'
        } else {
            Assert-True ($checked.status -ceq 'blocked' -and $script:PadRuns -eq 1 -and $script:Plans -eq 2) ('Definite failure gets a planner decision without automatic reexecution: ' + $modeValue + '; status=' + $checked.status + '; PAD=' + $script:PadRuns + '; plans=' + $script:Plans + '; error=' + $checked.error)
            Assert-True ($script:LastPlannerContext.observations[0].status -ceq 'failed' -and $script:LastPlannerContext.observations[0].ai_calls[0].ai_call_id -ceq ('f' * 32)) ('Failed observation and AiCall identity reach the next decision: ' + $modeValue)
        }
    }
    $observed = @([pscustomobject]@{ path = $script:Output; sha256 = Get-AgentHash $script:Output })
    $aliasedPlan=[pscustomobject]@{artifacts=@($script:Output.Replace('\','\\'))}
    $resolved=@(Assert-AgentCompletion $aliasedPlan $observed)
    Assert-True ($resolved.Count -eq 1 -and $resolved[0] -ceq $script:Output -and $aliasedPlan.artifacts[0] -cne $script:Output) 'Only filesystem references are canonicalized; the original planner object is unchanged'
    Assert-Throws { Assert-AgentCompletion $aliasedPlan @($observed[0],$observed[0]) } 'not observed' 'Canonicalization does not permit ambiguous observed grants'
    $unobservedCopy=Join-Path ([IO.Path]::GetDirectoryName($script:Output)) 'unobserved-copy.txt'
    [IO.File]::Copy($script:Output,$unobservedCopy)
    Assert-Throws { Assert-AgentCompletion ([pscustomobject]@{artifacts=@($unobservedCopy.Replace('\','\\'))}) $observed } 'not observed' 'Identical bytes at an unobserved path cannot authorize DONE'
    [IO.File]::AppendAllText($script:Output, 'changed')
    Assert-Throws { Assert-AgentCompletion ([pscustomobject]@{ artifacts = @($script:Output) }) $observed } 'changed' 'DONE rejects changed output'
    Assert-Throws { Assert-AgentCompletion $aliasedPlan $observed } 'changed' 'An aliased path cannot bypass the current hash check'
    foreach ($modeValue in @('unknown','false-done','blocked','max')) {
        $script:RunMode = $modeValue; $script:Plans = 0; $script:PadRuns = 0
        $job = New-TestJob $homeDirectory $input
        $result = Invoke-AgentRun $homeDirectory $job.job_id
        $expected = @{ unknown = 'unknown'; 'false-done' = 'failed'; blocked = 'blocked'; max = 'blocked' }[$modeValue]
        Assert-True ($result.status -ceq $expected) ('Run terminal status: ' + $modeValue)
        if ($modeValue -ceq 'unknown') { Assert-True ($script:Plans -eq 1 -and $script:PadRuns -eq 1) 'Unknown PAD outcome is never retried' }
        if ($modeValue -ceq 'max') { Assert-True ($script:Plans -eq 6 -and $script:PadRuns -eq 6) 'Finite maximum rounds enforced' }
    }
    $job = New-TestJob $homeDirectory $input
    [IO.File]::WriteAllText((Join-Path (Get-AgentJobDirectory $homeDirectory $job.job_id) 'cancel'), 'stop')
    $script:Plans = 0
    $cancelled = Invoke-AgentRun $homeDirectory $job.job_id
    Assert-True ($cancelled.status -ceq 'cancelled' -and $script:Plans -eq 0) 'Run cancel prevents planning'
    $interrupted = New-TestJob $homeDirectory $input 'running_pad'
    Repair-AgentInterruptedJobs $homeDirectory
    Assert-True ((Get-AgentJob $homeDirectory $interrupted.job_id).status -ceq 'running_pad') 'Worker startup grace prevents false interrupted state'
    (Get-Item -LiteralPath (Join-Path (Get-AgentJobDirectory $homeDirectory $interrupted.job_id) 'job.json')).LastWriteTimeUtc = [DateTime]::UtcNow.AddSeconds(-11)
    Repair-AgentInterruptedJobs $homeDirectory
    Assert-True ((Get-AgentJob $homeDirectory $interrupted.job_id).status -ceq 'unknown') 'Interrupted jobs recovered as unknown without replay'
    $authority = '127.0.0.1:12345'; $token = 'secret-token'
    $request = [pscustomobject]@{ Headers = @{ Host = $authority; Origin = ('http://' + $authority); 'X-App-Token' = $token }; Url = [uri]('http://' + $authority + '/api/state') }
    Assert-True (Test-AgentHttpRequest $request $authority $token) 'Same-origin token request accepted'
    $request.Headers.Origin = 'https://evil.example'
    Assert-True (-not (Test-AgentHttpRequest $request $authority $token)) 'Cross-origin request rejected'
    $request.Headers.Origin = ''; $request.Headers.Host = 'localhost:12345'
    Assert-True (-not (Test-AgentHttpRequest $request $authority $token)) 'Unexpected Host rejected'
    $request.Headers.Host = $authority; $request.Headers['X-App-Token'] = ''
    Assert-True (-not (Test-AgentHttpRequest $request $authority $token)) 'API token required'
    Assert-Throws { Read-AgentHttpBody ([pscustomobject]@{ ContentLength64 = 131073 }) } '128 KB' 'Declared request size bounded'
    $bodyBytes = [Text.Encoding]::UTF8.GetBytes(('x' * 131073))
    $bodyStream = New-Object IO.MemoryStream(,$bodyBytes)
    try { Assert-Throws { Read-AgentHttpBody ([pscustomobject]@{ ContentLength64 = -1; InputStream = $bodyStream }) } '128 KB' 'Chunked request size bounded' } finally { $bodyStream.Dispose() }
    Write-Output ('PASS: ' + $script:Checks + ' core contract checks; adapters mocked, no live Copilot/PAD claim.')
} finally {
    $safeRoot = Assert-AgentPathUnder $testRoot (Join-Path $workspace '.work')
    if (Test-Path -LiteralPath $safeRoot) { Remove-Item -LiteralPath $safeRoot -Recurse -Force }
}
