[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputDirectory = 'catalog/generated/normal-chat-current-revision-t10-20260910'
)

$ErrorActionPreference = 'Stop'
$utf8 = New-Object Text.UTF8Encoding($false)
$bundleRelative = 'copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt'
$flowRelative = 'catalog/generated/office-three-apps/generated.robin'
$bundlePath = Join-Path $Root $bundleRelative
$flowPath = Join-Path $Root $flowRelative
foreach ($path in @($bundlePath, $flowPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "T10_CONTEXT: Missing $path" }
}
$bundleText = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $bundlePath), $utf8).TrimEnd("`r", "`n")
$flowText = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $flowPath), $utf8).TrimEnd("`r", "`n")
$bundleHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $bundlePath).Hash.ToLowerInvariant()
$flowHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $flowPath).Hash.ToLowerInvariant()
$outDir = Join-Path $Root $OutputDirectory
[IO.Directory]::CreateDirectory($outDir) | Out-Null
$context = @(
    "===== BEGIN $bundleRelative | SHA-256 $bundleHash =====",
    $bundleText,
    "===== END $bundleRelative =====",
    '',
    "===== BEGIN $flowRelative | SHA-256 $flowHash =====",
    $flowText,
    "===== END $flowRelative ====="
) -join "`n"
$contextPath = Join-Path $outDir 'T10-Knowledge-Flow-Bundle.txt'
[IO.File]::WriteAllText($contextPath, $context + "`n", $utf8)
$contextHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $contextPath).Hash.ToLowerInvariant()
$manifest = [ordered]@{
    schema_version = 1
    bundle_path = $OutputDirectory.Replace('\', '/') + '/T10-Knowledge-Flow-Bundle.txt'
    bundle_sha256 = $contextHash
    source_bundle_sha256 = $bundleHash
    source_flow_sha256 = $flowHash
    sources = @(
        [ordered]@{ path = $bundleRelative; sha256 = $bundleHash },
        [ordered]@{ path = $flowRelative; sha256 = $flowHash }
    )
}
$manifestPath = Join-Path $outDir 'T10-context-manifest.json'
[IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 8) + "`n", $utf8)
[ordered]@{ context_path = $contextPath; context_sha256 = $contextHash; source_bundle_sha256 = $bundleHash; source_flow_sha256 = $flowHash } | ConvertTo-Json -Depth 5
