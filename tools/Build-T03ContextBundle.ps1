[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputDirectory = 'catalog/generated/normal-chat-current-revision-t03-20260910'
)

$ErrorActionPreference = 'Stop'
$utf8 = New-Object Text.UTF8Encoding($false)
$relativeFiles = @(
    'copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt',
    'catalog/fixtures/files/copy-input-20260909.txt',
    'catalog/fixtures/files/t03-alpha.txt',
    'catalog/fixtures/files/t03-beta.csv',
    'catalog/fixtures/files/t03-gamma.md'
)
$chunks = New-Object Collections.Generic.List[string]
$hashes = @()
foreach ($relative in $relativeFiles) {
    $path = Join-Path $Root $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "T03_CONTEXT: Missing $relative" }
    $text = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $path), $utf8).TrimEnd("`r", "`n")
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    $chunks.Add("===== BEGIN $relative | SHA-256 $hash =====")
    $chunks.Add($text)
    $chunks.Add("===== END $relative =====")
    $chunks.Add('')
    $hashes += [ordered]@{ path = $relative; sha256 = $hash }
}
$outDir = Join-Path $Root $OutputDirectory
[IO.Directory]::CreateDirectory($outDir) | Out-Null
$contextPath = Join-Path $outDir 'T03-Knowledge-Fixtures-Bundle.txt'
[IO.File]::WriteAllText($contextPath, (($chunks -join "`n").TrimEnd("`n") + "`n"), $utf8)
$contextHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $contextPath).Hash.ToLowerInvariant()
$manifest = [ordered]@{
    schema_version = 1
    bundle_path = $OutputDirectory.Replace('\', '/') + '/T03-Knowledge-Fixtures-Bundle.txt'
    bundle_sha256 = $contextHash
    sources = @($hashes)
}
[IO.File]::WriteAllText((Join-Path $outDir 'T03-context-manifest.json'), (($manifest | ConvertTo-Json -Depth 8) + "`n"), $utf8)
[ordered]@{ context_path = $contextPath; context_sha256 = $contextHash; source_count = $relativeFiles.Count } | ConvertTo-Json -Depth 5
