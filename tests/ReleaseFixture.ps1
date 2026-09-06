# Seals intentionally synthetic test packages using the same maintainer tool as real candidates.
function Set-TestReleaseBinding([string]$Directory) {
    $app = Join-Path $Directory 'App.ps1'
    $text = [IO.File]::ReadAllText($app,[Text.Encoding]::UTF8)
    if ($text -notmatch '(?m)^# Release-Binding: ') { $text += "`r`n# Release-Binding: UNSEALED`r`n" }
    if ($text -notmatch '(?m)^# State-Contract: ') { $text += "`r`n# State-Contract: 2`r`n" }
    [IO.File]::WriteAllText($app,$text,(New-Object Text.UTF8Encoding($true)))
    & (Join-Path $PSScriptRoot '..\tools\Seal-AgentRelease.ps1') -Directory $Directory -Channel development | Out-Null
}
