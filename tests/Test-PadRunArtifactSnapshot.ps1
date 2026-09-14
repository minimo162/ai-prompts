[CmdletBinding()]
param(
    [string]$Root = ''
)

$ErrorActionPreference = 'Stop'
$checks = 0
if ([string]::IsNullOrWhiteSpace($Root)) { $Root = (Get-Location).Path }

function Check([bool]$Value, [string]$Name) {
    if (-not $Value) { throw ('FAIL: ' + $Name) }
    $script:checks++
}

function Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$tool = [IO.Path]::GetFullPath((Join-Path $Root 'tools\Save-PadRunArtifactSnapshot.ps1'))
$temp = Join-Path ([IO.Path]::GetTempPath()) ('pad-run-artifact-gate-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($temp)
$ps5 = (Get-Command powershell.exe -ErrorAction Stop).Source
function Invoke-Gate([string[]]$Arguments) {
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $text = @(& $ps5 -NoProfile -ExecutionPolicy Bypass -File $tool @Arguments 2>&1)
        return [pscustomobject]@{ exit_code = $LASTEXITCODE; output = $text }
    }
    finally { $ErrorActionPreference = $oldPreference }
}

$artifact = Join-Path $temp 'run1.xlsx'
$snapshot = Join-Path $temp 'run1-snapshot.xlsx'
$evidence = Join-Path $temp 'run1-evidence.json'
$input = Join-Path $temp 'input.xlsx'
[IO.File]::WriteAllBytes($artifact, [byte[]](1, 2, 3, 4, 5))
[IO.File]::WriteAllBytes($input, [byte[]](9, 8, 7))
$inputSha = Sha256 $input
$gate1 = Invoke-Gate @('-ArtifactPath', $artifact, '-SnapshotPath', $snapshot, '-EvidencePath', $evidence, '-RunNumber', '1', '-InputPath', $input, '-ExpectedInputSha256', $inputSha)
$exitCode = $gate1.exit_code
Check ($exitCode -eq 0) 'successful gate exits zero'
$record = Get-Content -Raw -LiteralPath $evidence | ConvertFrom-Json
Check ($record.status -ceq 'PASS' -and $record.gate -ceq 'READY_FOR_NEXT_RUN') 'successful gate is ready for next run'
Check ($record.run_number -eq 1 -and $record.artifact_stable -and $record.snapshot_matches_artifact) 'successful gate binds run and stable artifact'
Check ($record.input_unchanged -eq $true) 'successful gate verifies input unchanged'
Check ((Sha256 $artifact) -ceq (Sha256 $snapshot) -and (Get-Item -LiteralPath $snapshot).Length -eq 5) 'snapshot bytes and SHA equal source'

$artifact2 = Join-Path $temp 'run2.xlsx'
$snapshot2 = Join-Path $temp 'run2-snapshot.xlsx'
$evidence2 = Join-Path $temp 'run2-evidence.json'
[IO.File]::WriteAllBytes($artifact2, [byte[]](6, 7, 8))
[IO.File]::WriteAllText($snapshot2, 'existing')
$gate2 = Invoke-Gate @('-ArtifactPath', $artifact2, '-SnapshotPath', $snapshot2, '-EvidencePath', $evidence2, '-RunNumber', '2')
$exitCode2 = $gate2.exit_code
Check ($exitCode2 -ne 0) 'existing snapshot blocks the next gate'
Check (-not (Test-Path -LiteralPath $evidence2 -PathType Leaf) -and [IO.File]::ReadAllText($snapshot2) -ceq 'existing') 'blocked destination leaves existing evidence and snapshot untouched'

$artifact3 = Join-Path $temp 'run3.xlsx'
$snapshot3 = Join-Path $temp 'run3-snapshot.xlsx'
$evidence3 = Join-Path $temp 'run3-evidence.json'
$input3 = Join-Path $temp 'input3.xlsx'
[IO.File]::WriteAllBytes($artifact3, [byte[]](10, 11, 12))
[IO.File]::WriteAllBytes($input3, [byte[]](13, 14))
$expectedInput3 = Sha256 $input3
[IO.File]::WriteAllBytes($input3, [byte[]](15, 16))
$gate3 = Invoke-Gate @('-ArtifactPath', $artifact3, '-SnapshotPath', $snapshot3, '-EvidencePath', $evidence3, '-RunNumber', '2', '-InputPath', $input3, '-ExpectedInputSha256', $expectedInput3)
$exitCode3 = $gate3.exit_code
Check ($exitCode3 -eq 2) 'changed input blocks the next gate with dedicated exit code'
$record3 = Get-Content -Raw -LiteralPath $evidence3 | ConvertFrom-Json
Check ($record3.status -ceq 'BLOCKED' -and $record3.gate -ceq 'DO_NOT_START_NEXT_RUN' -and $record3.input_unchanged -eq $false) 'changed input is explicit and non-promoting'
Check ((Sha256 $artifact3) -ceq (Sha256 $snapshot3)) 'blocked gate still preserves the copied raw snapshot'

Write-Output ('PASS: ' + $checks + ' PAD run artifact snapshot gate checks; no PAD or Copilot invoked.')
