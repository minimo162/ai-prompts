[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$coveragePath = Join-Path $repo 'catalog\coverage.json'
if (-not (Test-Path -LiteralPath $coveragePath -PathType Leaf)) { throw 'Missing coverage record' }
$coverage = [IO.File]::ReadAllText($coveragePath, [Text.Encoding]::UTF8) | ConvertFrom-Json
$recordRelative = [string]$coverage.current_package.t01_prepared
if ([string]::IsNullOrWhiteSpace($recordRelative)) { throw 'Missing current-package T01 preparation reference' }
$recordPath = Join-Path $repo ('catalog\' + $recordRelative.Replace('/','\'))
if (-not (Test-Path -LiteralPath $recordPath -PathType Leaf)) { throw 'Missing T01 preparation record' }
$record = [IO.File]::ReadAllText($recordPath, [Text.Encoding]::UTF8) | ConvertFrom-Json
$checks = 0
function Check([bool]$Value, [string]$Name) { if (-not $Value) { throw ('FAIL: ' + $Name) }; $script:checks++ }
function Hash([string]$Path) { return (Get-FileHash -LiteralPath (Join-Path $repo $Path) -Algorithm SHA256).Hash.ToLowerInvariant() }

Check ($record.status -ceq 'READY_FOR_FRESH_CHAT_SEND') 'record is ready for send'
Check ($record.send_status -ceq 'NOT_SENT') 'T01 has not been sent by this preparation test'
$instruction = 'copilot\agent-instructions.txt'
$bundle = 'copilot\knowledge\PAD-Robin-Knowledge-Bundle.txt'
Check ((Hash $instruction) -ceq $record.instruction_sha256) 'instruction hash matches record'
Check ((Hash $bundle) -ceq $record.bundle_sha256) 'bundle hash matches record'
Check ((Hash $bundle) -ceq $coverage.current_package.knowledge_bundle_sha256) 'bundle hash matches current coverage'
$promptPath = Join-Path $repo $record.prompt_source
Check ((Get-FileHash -LiteralPath $promptPath -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $record.prompt_sha256) 'prompt hash matches record'
$promptText = [IO.File]::ReadAllText($promptPath, [Text.Encoding]::UTF8)
Check ($promptText.Length -eq $record.prompt_utf16) 'prompt UTF-16 length matches record'
$fixturePath = Join-Path $repo $record.fixture.path
Check ((Get-FileHash -LiteralPath $fixturePath -Algorithm SHA256).Hash.ToLowerInvariant() -ceq $record.fixture.sha256) 'fixture hash matches record'
Check ((Get-Item -LiteralPath $fixturePath).Length -eq $record.fixture.bytes) 'fixture byte count matches record'
$parts = $record.expected_output.replacement -split ' -> ', 2
Check ($parts.Count -eq 2) 'replacement contract has two terms'
$fixtureText = [IO.File]::ReadAllText($fixturePath, [Text.Encoding]::UTF8)
$expectedText = $fixtureText.Replace($parts[0], $parts[1])
$contentBytes = [Text.Encoding]::UTF8.GetBytes($expectedText)
$expectedBytes = New-Object byte[] ($contentBytes.Length + 3)
$expectedBytes[0] = 239
$expectedBytes[1] = 187
$expectedBytes[2] = 191
[Array]::Copy($contentBytes, 0, $expectedBytes, 3, $contentBytes.Length)
$sha = [Security.Cryptography.SHA256]::Create()
$expectedHash = (($sha.ComputeHash($expectedBytes) | ForEach-Object { $_.ToString('x2') }) -join '')
Check ($expectedHash -ceq $record.expected_output.sha256) 'fixed expected output hash matches fixture replacement'
Check ($expectedBytes.Length -eq $record.expected_output.bytes) 'fixed expected output byte count matches record'
Check ($record.expected_output.utf8_bom -eq $true) 'UTF-8 output BOM contract matches measured PAD behavior'
Check ($record.expected_output.additional_newline -eq $false) 'no additional newline contract'
Write-Output ('PASS: ' + $checks + ' current-bundle T01 preparation contract checks; no Copilot/PAD actions.')
