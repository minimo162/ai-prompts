param([string]$Root=(Get-Location).Path)
$ErrorActionPreference='Stop'
$path=Join-Path $Root 'tools/Paste-PadRobinLiveByStatus.ps1'
$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($path,[ref]$null,[ref]$errors)
if($errors.Count){throw 'Parse failed'}
$block=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.TryStatementAst] -and $null -ne $n.Finally},$true))[0].Finally
$code=$block.Extent.Text.Trim();$code=$code.Substring(1,$code.Length-2)
$script:restores=0;$script:seq=10;$script:clip='owned'
function Get-AgentPadClipboardSequence {return $script:seq}
function Get-AgentPadClipboardText {if($script:changeDuringRead){$script:seq++};return $script:clip}
function Restore-AgentPadClipboard($Snapshot){if($Snapshot -cne 'original'){throw 'Wrong snapshot'};$script:restores++}
$text='owned';$beforeClipboard='original';$pasteSequence=10;$settled=$false
. ([scriptblock]::Create($code))
if($script:restores -ne 1){throw 'Failure path must restore owned clipboard'}
$script:seq=11
. ([scriptblock]::Create($code))
if($script:restores -ne 1){throw 'Must preserve a newer clipboard sequence'}
$script:seq=10;$script:clip='user changed text'
. ([scriptblock]::Create($code))
if($script:restores -ne 1){throw 'Must preserve changed clipboard text'}
$pasteSequence=$null;$script:clip='owned'
. ([scriptblock]::Create($code))
if($script:restores -ne 1){throw 'No paste ownership, no restoration'}
$pasteSequence=10;$script:seq=10;$script:changeDuringRead=$true
. ([scriptblock]::Create($code))
if($script:restores -ne 1){throw 'Must preserve a sequence changed during text read'}
$b=[IO.File]::ReadAllBytes($path)
if($b[0] -ne 239 -or $b[1] -ne 187 -or $b[2] -ne 191){throw 'PS5 localized status matching needs UTF8 BOM'}
'PASS: 6 paste clipboard/encoding checks; native clipboard not accessed'
