[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($PSScriptRoot)
$basePath = Join-Path $root 'candidate-scalar-direct.robin'
$actionPath = Join-Path $root 'captured-powershell-format-action-v2.robin'
$outputPath = Join-Path $root 'candidate-format-sandwich-v2.robin'
if (Test-Path -LiteralPath $outputPath) { throw 'Candidate output exists' }
$base = [IO.File]::ReadAllText($basePath, (New-Object Text.UTF8Encoding($false))).Replace("`r`n", "`n")
$action = [IO.File]::ReadAllText($actionPath, (New-Object Text.UTF8Encoding($false))).Replace("`r`n", "`n").TrimEnd("`n")
$needle = "Excel.WriteToExcel.WriteCell Instance: Work Value: SourceText Column: `$'''A''' Row: 2"
$occurrences = ([regex]::Matches($base, [regex]::Escape($needle))).Count
if ($occurrences -ne 1) { throw ('Expected one text WriteCell action, found ' + $occurrences) }
$candidate = $base.Replace($needle, $action)
if ($candidate -ceq $base -or $candidate.Contains($needle)) { throw 'Mechanical replacement failed' }
$oldMarker = "SET ProbeState TO `$'''SCALAR_DIRECT_FINISHED'''"
$newMarker = "SET ProbeState TO `$'''FORMAT_SANDWICH_FINISHED'''"
if (([regex]::Matches($candidate, [regex]::Escape($oldMarker))).Count -ne 1) { throw 'Terminal marker was not unique' }
$candidate = $candidate.Replace($oldMarker, $newMarker)
[IO.File]::WriteAllText($outputPath, $candidate, (New-Object Text.UTF8Encoding($false)))
[pscustomobject]@{
    output = $outputPath
    bytes = (Get-Item -LiteralPath $outputPath).Length
    sha256 = (Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash.ToLowerInvariant()
    replacement_count = $occurrences
    captured_action_sha256 = (Get-FileHash -LiteralPath $actionPath -Algorithm SHA256).Hash.ToLowerInvariant()
} | ConvertTo-Json
