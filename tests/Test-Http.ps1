# Actual loopback HTTP checks; no browser, Copilot, PAD or business operation is started.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$testHome = Join-Path ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\.work'))) ('http-test-' + [guid]::NewGuid().ToString('N'))
$server = $null
try {
    $server = Start-AgentProcess -AppPath $script:AgentAppPath -HomePath $testHome -Mode Serve -NoBrowser
    $runtimePath = Join-Path $testHome 'data\server.json'
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    while (-not (Test-Path -LiteralPath $runtimePath) -and [DateTime]::UtcNow -lt $deadline -and -not $server.HasExited) { Start-Sleep -Milliseconds 100 }
    if (-not (Test-Path -LiteralPath $runtimePath)) { throw ('Server did not start. Exited=' + $server.HasExited) }
    $runtime = Read-AgentJson $runtimePath
    $url = 'http://127.0.0.1:' + $runtime.port
    $headers = @{ 'X-App-Token' = $runtime.token }
    $state = Invoke-RestMethod -Uri ($url + '/api/state') -Headers $headers -TimeoutSec 3
    if (-not $state.ok -or $state.version -cne '0.1.0') { throw 'Unexpected state response.' }
    $html = Invoke-WebRequest -Uri ($url + '/') -UseBasicParsing -TimeoutSec 3
    if ($html.Content -notmatch 'app-version') { throw 'HTML not served.' }
    $unauthorized = 0
    try { $null = Invoke-WebRequest -Uri ($url + '/api/state') -UseBasicParsing -TimeoutSec 3 } catch { $unauthorized = [int]$_.Exception.Response.StatusCode }
    if ($unauthorized -ne 403) { throw 'Missing token not rejected.' }
    $originDenied = 0
    try { $null = Invoke-WebRequest -Uri ($url + '/api/state') -Headers @{ 'X-App-Token' = $runtime.token; Origin = 'https://evil.example' } -UseBasicParsing -TimeoutSec 3 } catch { $originDenied = [int]$_.Exception.Response.StatusCode }
    if ($originDenied -ne 403) { throw 'Cross origin not rejected.' }
    $hostDenied = 0
    try { $null = Invoke-WebRequest -Uri ($url + '/api/state') -Headers @{ 'X-App-Token' = $runtime.token; Host = 'attacker.invalid' } -UseBasicParsing -TimeoutSec 3 } catch { $hostDenied = [int]$_.Exception.Response.StatusCode }
    if ($hostDenied -ne 403) { throw 'Unexpected Host not rejected.' }
    $slowClient = New-Object Net.Sockets.TcpClient
    try {
        $slowClient.Connect('127.0.0.1', $runtime.port)
        $slowClient.ReceiveTimeout = 15000
        $slowStream = $slowClient.GetStream()
        $slowHeaders = "POST /api/settings HTTP/1.1`r`nHost: 127.0.0.1:$($runtime.port)`r`nX-App-Token: $($runtime.token)`r`nContent-Length: 100`r`n`r`n"
        $slowBytes = [Text.Encoding]::ASCII.GetBytes($slowHeaders)
        $clock = [Diagnostics.Stopwatch]::StartNew()
        $slowStream.Write($slowBytes, 0, $slowBytes.Length)
        $reader = New-Object IO.StreamReader($slowStream)
        $statusLine = $reader.ReadLine()
        $clock.Stop()
        if (($null -ne $statusLine -and $statusLine -cne 'HTTP/1.1 400 Bad Request') -or $clock.Elapsed.TotalSeconds -gt 13) { throw 'Slow request body was not rejected within the bounded deadline.' }
    } finally { $slowClient.Close() }
    $state = Invoke-RestMethod -Uri ($url + '/api/state') -Headers $headers -TimeoutSec 3
    if (-not $state.ok) { throw 'Server did not recover after slow request.' }
    $reopened = Start-AgentProcess -AppPath $script:AgentAppPath -HomePath $testHome -Mode Serve -NoBrowser
    if (-not $reopened.WaitForExit(7000) -or $reopened.ExitCode -ne 0) { throw 'Server reopen failed.' }
    if ((Read-AgentJson $runtimePath).pid -ne $runtime.pid) { throw 'Server duplicated.' }
    $null = Invoke-RestMethod -Uri ($url + '/api/settings') -Method Post -ContentType 'application/json' -Body '{"copilot_port":9224,"pad_flow_name":"TestFlow","max_rounds":3}' -Headers $headers -TimeoutSec 3
    $state = Invoke-RestMethod -Uri ($url + '/api/state') -Headers $headers -TimeoutSec 3
    if ($state.settings.max_rounds -ne 3) { throw 'Settings did not persist.' }
    # A server-owned question ID and atomic move prevent duplicate/stale tab answers.
    $questionJobId = [guid]::NewGuid().ToString('N')
    $questionDirectory = Get-AgentJobDirectory $testHome $questionJobId
    [IO.Directory]::CreateDirectory($questionDirectory) | Out-Null
    $questionId = [guid]::NewGuid().ToString('N')
    $questionJob = [pscustomobject]@{ job_id=$questionJobId; status='waiting_user'; question='test'; question_id=$questionId; history=@() }
    Save-AgentJob $questionDirectory $questionJob
    $firstBody = ConvertTo-Json -Compress @{ job_id=$questionJobId; question_id=$questionId; answer='first answer' }
    $null = Invoke-RestMethod -Uri ($url + '/api/answer') -Method Post -ContentType 'application/json' -Body $firstBody -Headers $headers -TimeoutSec 3
    $answerPath = Join-Path $questionDirectory 'answer.json'
    $firstHash = Get-AgentHash $answerPath
    $duplicateRejected = $false
    try { $null = Invoke-RestMethod -Uri ($url + '/api/answer') -Method Post -ContentType 'application/json' -Body ($firstBody.Replace('first answer','second answer')) -Headers $headers -TimeoutSec 3 } catch { $duplicateRejected = $_.ErrorDetails.Message -match 'ANSWER_ALREADY_RECEIVED' }
    if (-not $duplicateRejected -or (Get-AgentHash $answerPath) -cne $firstHash) { throw 'Duplicate answer overwrote the first response.' }
    [IO.File]::Delete($answerPath)
    $questionJob.question_id = [guid]::NewGuid().ToString('N')
    Save-AgentJob $questionDirectory $questionJob
    $staleRejected = $false
    try { $null = Invoke-RestMethod -Uri ($url + '/api/answer') -Method Post -ContentType 'application/json' -Body $firstBody -Headers $headers -TimeoutSec 3 } catch { $staleRejected = $_.ErrorDetails.Message -match 'QUESTION_CHANGED' }
    if (-not $staleRejected -or [IO.File]::Exists($answerPath)) { throw 'Stale answer was accepted for a new question.' }
    $questionJob.status = 'cancelled'
    Save-AgentJob $questionDirectory $questionJob
    # A new immutable app path replaces an idle old server on the next launch.
    $replacementDirectory = Join-Path $testHome 'replacement-app'
    [IO.Directory]::CreateDirectory($replacementDirectory) | Out-Null
    $replacementApp = Join-Path $replacementDirectory 'App.ps1'
    [IO.File]::Copy($script:AgentAppPath, $replacementApp)
    [IO.File]::Copy((Join-Path ([IO.Path]::GetDirectoryName($script:AgentAppPath)) 'index.html'), (Join-Path $replacementDirectory 'index.html'))
    $oldServer = $server
    $server = Start-AgentProcess -AppPath $replacementApp -HomePath $testHome -Mode Serve -NoBrowser
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        Start-Sleep -Milliseconds 100
        $replacementRuntime = Read-AgentJson $runtimePath
    } while ($replacementRuntime.pid -ne $server.Id -and [DateTime]::UtcNow -lt $deadline)
    if ($replacementRuntime.pid -ne $server.Id -or -not $oldServer.WaitForExit(3000)) { throw 'Idle server was not replaced with the newly pinned app.' }
    $url = 'http://127.0.0.1:' + $replacementRuntime.port
    $headers = @{ 'X-App-Token' = $replacementRuntime.token }
    $state = Invoke-RestMethod -Uri ($url + '/api/state') -Headers $headers -TimeoutSec 3
    if ($state.settings.max_rounds -ne 3) { throw 'User settings were not preserved during server replacement.' }
    $null = Invoke-RestMethod -Uri ($url + '/api/restart') -Method Post -ContentType 'application/json' -Body '{}' -Headers $headers -TimeoutSec 3
    if (-not $server.WaitForExit(3000)) { throw 'Idle server did not shut down.' }
    'PASS: real Windows PowerShell5.1 localhost HTML/state, token/Host/origin denial, slow-body deadline, singleton reopen, settings, duplicate/stale answer rejection, version handover, graceful shutdown.'
} finally {
    if ($null -ne $server -and -not $server.HasExited) { Stop-Process -Id $server.Id -Force }
    if (Test-Path -LiteralPath $testHome) { $safe = Assert-AgentPathUnder $testHome ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\.work'))); Remove-Item -LiteralPath $safe -Recurse -Force }
}
