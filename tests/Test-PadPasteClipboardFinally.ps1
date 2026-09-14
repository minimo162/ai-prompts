param([string]$Root=(Get-Location).Path)
$ErrorActionPreference='Stop'
$path=Join-Path $Root 'tools/Paste-PadRobinLiveByStatus.ps1'
$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($path,[ref]$null,[ref]$errors)
if($errors.Count){throw 'Parse failed'}
$block=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.TryStatementAst] -and $null -ne $n.Finally},$true))[0].Finally
$code=$block.Extent.Text.Trim();$code=$code.Substring(1,$code.Length-2)
$script:restores=0;$script:disposes=0;$script:restoreThrows=$false
$clipboardLease=New-Object PSObject
$clipboardLease | Add-Member ScriptMethod Restore { $script:restores++; if($script:restoreThrows){throw 'restore failed'}; return 'restored_supported_native_formats' }
$nativeClipboard=New-Object PSObject
$nativeClipboard | Add-Member ScriptMethod Dispose { $script:disposes++ }
$settled=$false
. ([scriptblock]::Create($code))
if($script:restores -ne 1 -or $script:disposes -ne 1){throw 'Observation failure must restore and dispose'}
$script:restoreThrows=$true
try{. ([scriptblock]::Create($code));throw 'Expected restoration error'}catch{if($_.Exception.Message -notmatch 'restore failed'){throw}}
if($script:disposes -ne 2){throw 'Restore failure must dispose'}
$clipboardLease=$null
. ([scriptblock]::Create($code))
if($script:restores -ne 2 -or $script:disposes -ne 3){throw 'No lease must not restore'}
if($code -match 'Restore-AgentPadClipboard|Get-AgentPadClipboard'){throw 'Non-atomic fallback forbidden'}
$b=[IO.File]::ReadAllBytes($path)
if($b[0] -ne 239 -or $b[1] -ne 187 -or $b[2] -ne 191){throw 'PS5 localized status matching needs UTF8 BOM'}
'PASS: 5 paste finally/encoding checks; native clipboard not accessed'