[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))

$instruction = Join-Path $repo 'copilot\agent-instructions.txt'
$knowledge = @(
    'PAD-Robin-00-Index.txt', 'PAD-Robin-01-Basics.txt', 'PAD-Robin-02-Control.txt',
    'PAD-Robin-03-Files.txt', 'PAD-Robin-04-Office-PDF.txt', 'PAD-Robin-05-UI-Web.txt',
    'PAD-Robin-06-Examples.txt'
)
if (-not (Test-Path -LiteralPath $instruction -PathType Leaf)) { throw 'Missing agent instructions' }
foreach ($name in $knowledge) {
    $path = Join-Path $repo ('copilot\knowledge\' + $name)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw ('Missing knowledge file: ' + $name) }
}

$bytes = [IO.File]::ReadAllBytes($instruction)
if ($bytes.Length -ge 3 -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191) { throw 'Agent instructions must be UTF-8 BOM-less' }
$text = [IO.File]::ReadAllText($instruction)
if ($text.Length -gt 8000) { throw ('Agent instructions exceed 8000 UTF-16 units: ' + $text.Length) }
if ($text.Length -gt 7000) { throw ('Agent instructions exceed 7000 target units: ' + $text.Length) }

$utf8 = New-Object System.Text.UTF8Encoding($false)
$index = [IO.File]::ReadAllText((Join-Path $repo 'catalog\index.json'), $utf8) | ConvertFrom-Json
$coverage = [IO.File]::ReadAllText((Join-Path $repo 'catalog\coverage.json'), $utf8) | ConvertFrom-Json
if ($coverage.left_panel_scope.complete -ne $false) { throw 'Coverage must not claim a complete left-panel inventory' }
if ($coverage.observed_actions.Count -ne $index.actions.Count) { throw 'Coverage observed action count does not match index' }
if ($coverage.required_checks.Count -lt 7) { throw 'Coverage is missing required A-G checks' }

Write-Output ('PASS: Copilot Robin package; instructions_utf16=' + $text.Length + '; knowledge_files=' + $knowledge.Count + '; observed_actions=' + $coverage.observed_actions.Count)
