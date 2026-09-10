[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputDirectory = 'catalog/generated/normal-chat-current-revision-t08-20260910'
)

$ErrorActionPreference = 'Stop'
$utf8 = New-Object Text.UTF8Encoding($false)
$files = @(
    'copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt',
    'catalog/actions/file-read-text/utf8.robin'
)
$chunks = @()
$sources = @()
foreach ($relative in $files) {
    $path = Join-Path $Root $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "T08_CONTEXT: Missing $relative" }
    $text = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $path), $utf8).TrimEnd("`r", "`n")
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    $chunks += "===== BEGIN $relative | SHA-256 $hash ====="
    $chunks += $text
    $chunks += "===== END $relative ====="
    $chunks += ''
    $sources += [ordered]@{ path = $relative; sha256 = $hash }
}
$outDir = Join-Path $Root $OutputDirectory
[IO.Directory]::CreateDirectory($outDir) | Out-Null
$contextPath = Join-Path $outDir 'T08-Knowledge-Action-Bundle.txt'
[IO.File]::WriteAllText($contextPath, (($chunks -join "`n").TrimEnd("`n") + "`n"), $utf8)
$contextHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $contextPath).Hash.ToLowerInvariant()
$manifest = [ordered]@{ schema_version = 1; bundle_path = $OutputDirectory.Replace('\', '/') + '/T08-Knowledge-Action-Bundle.txt'; bundle_sha256 = $contextHash; sources = @($sources) }
[IO.File]::WriteAllText((Join-Path $outDir 'T08-context-manifest.json'), (($manifest | ConvertTo-Json -Depth 8) + "`n"), $utf8)
[ordered]@{ context_path = $contextPath; context_sha256 = $contextHash; source_count = $files.Count } | ConvertTo-Json -Depth 5
