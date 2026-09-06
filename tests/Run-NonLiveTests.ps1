# Windows PS5 entrypoint; these results are not live-service or other-PC acceptance.
[CmdletBinding()]
param([ValidateSet('Csv','All')][string]$Suite = 'Csv', [switch]$IncludeUi)
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) { throw 'Run with Windows PowerShell 5.1.' }
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$output = Join-Path $repo ('.work\nonlive-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($output)
$files = @('App.ps1','index.html','業務エージェント.cmd')
function Get-CandidateHashes { $hashes = [ordered]@{}; foreach ($file in $files) { $hashes[$file] = (Get-FileHash -LiteralPath (Join-Path $repo $file) -Algorithm SHA256).Hash.ToLowerInvariant() }; return $hashes }
$before = Get-CandidateHashes
$names = @('Test-CsvContracts.ps1','Test-CsvBatch.ps1','Test-CsvLifecycle.ps1','Test-CsvTypedPlan.ps1','Test-CsvReview.ps1','Test-CsvLateResponse.ps1','Test-QualityDraft.ps1','Test-OfflineDiagnostic.ps1')
if ($Suite -ceq 'All') { $names += @('Test-ConversationScope.ps1','Test-ConnectionContract.ps1','Test-AcceptanceGate.ps1','Test-App.ps1','Test-Pad.ps1','Test-PadRecovery.ps1','Test-Copilot.ps1','Test-CopilotPlannerV2.ps1','Test-PlannerV2Transport.ps1','Test-Http.ps1','Test-Launcher.ps1','Test-ReleaseBinding.ps1','Test-PublishAgentSource.ps1','Test-PublishCrash.ps1','Test-AiCallProcess.ps1','Test-AiCallProviderFailure.ps1','Test-ClipboardSnapshot.ps1') }
$results = @(); $started = [DateTime]::UtcNow.ToString('o')
foreach ($name in $names) {
    $log = Join-Path $output ($name + '.log')
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $exitCode = 1
    try { & (Join-Path $PSHOME 'powershell.exe') -NoProfile -ExecutionPolicy Bypass -STA -File (Join-Path $PSScriptRoot $name) > $log 2>&1; $exitCode = $LASTEXITCODE }
    catch { $_.Exception.Message | Out-File -LiteralPath $log -Append }
    $timer.Stop()
    $results += [pscustomobject]@{ test = $name; kind = 'Windows PS5 non-live contract/process'; status = $(if ($exitCode -eq 0) { 'PASS' } else { 'FAIL' }); exit_code = $exitCode; elapsed_ms = $timer.ElapsedMilliseconds; log = $log }
    Write-Output ($name + ': ' + $results[-1].status)
}
if ($IncludeUi) {
    $uiTests=@('Test-CsvUi.cjs');if($Suite -ceq 'All'){$uiTests+=@('Test-CopilotDom.cjs','Test-PadRecoveryUi.cjs','Test-CsvCrashUi.cjs')}
    foreach($name in $uiTests){
        $log = Join-Path $output ($name+'.log');$exitCode=1
        try { & node (Join-Path $PSScriptRoot $name) > $log 2>&1; $exitCode=$LASTEXITCODE }
        catch { $_.Exception.Message | Out-File -LiteralPath $log -Append }
        $results += [pscustomobject]@{ test=$name; kind='rendered Edge + PS5 HTTP/child + mock external boundary'; status=$(if($exitCode -eq 0){'PASS'}else{'FAIL'});exit_code=$exitCode;log=$log }
        Write-Output ($name+': '+$results[-1].status)
    }
}
$after = Get-CandidateHashes
$unchanged = (ConvertTo-Json $before -Compress) -ceq (ConvertTo-Json $after -Compress)
$passed = $unchanged -and @($results | Where-Object status -cne 'PASS').Count -eq 0
$record = [ordered]@{ schema_version = 1; started_utc = $started; finished_utc = [DateTime]::UtcNow.ToString('o'); candidate_hashes = $before; candidate_unchanged = $unchanged; status = $(if ($passed) { 'PASS' } else { 'FAIL' }); tests = $results; live_m365 = 'NOT_RUN'; native_pad = 'NOT_RUN'; business_quality = 'NOT_RUN'; other_pc = 'NOT_RUN'; release_approved = $false }
$recordPath = Join-Path $output 'verification.json'
[IO.File]::WriteAllText($recordPath, (ConvertTo-Json $record -Depth 20), (New-Object Text.UTF8Encoding($false)))
Write-Output ('Evidence: ' + $recordPath)
if (-not $passed) { exit 1 }
