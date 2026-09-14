[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ArtifactPath,
    [Parameter(Mandatory = $true)][string]$SnapshotPath,
    [Parameter(Mandatory = $true)][string]$EvidencePath,
    [Parameter(Mandatory = $true)][ValidateRange(1, 2)][int]$RunNumber,
    [string]$InputPath = '',
    [string]$ExpectedInputSha256 = '',
    [long]$MinimumBytes = 1
)

$ErrorActionPreference = 'Stop'

function Resolve-ExistingFile([string]$Path, [string]$Name) {
    $full = [IO.Path]::GetFullPath($Path)
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) { throw ('PAD_ARTIFACT_GATE: missing ' + $Name) }
    return $full
}

function Resolve-NewFile([string]$Path, [string]$Name) {
    $full = [IO.Path]::GetFullPath($Path)
    if (Test-Path -LiteralPath $full) { throw ('PAD_ARTIFACT_GATE: destination exists: ' + $Name) }
    $parent = [IO.Path]::GetDirectoryName($full)
    if ([string]::IsNullOrWhiteSpace($parent) -or -not (Test-Path -LiteralPath $parent -PathType Container)) {
        throw ('PAD_ARTIFACT_GATE: destination parent missing: ' + $Name)
    }
    return $full
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

if ($MinimumBytes -lt 1) { throw 'PAD_ARTIFACT_GATE: MinimumBytes must be positive' }
$source = Resolve-ExistingFile $ArtifactPath 'artifact'
$snapshot = Resolve-NewFile $SnapshotPath 'snapshot'
$evidence = Resolve-NewFile $EvidencePath 'evidence'
if ([StringComparer]::OrdinalIgnoreCase.Equals($source, $snapshot)) { throw 'PAD_ARTIFACT_GATE: artifact and snapshot must differ' }

$inputProvided = (-not [string]::IsNullOrWhiteSpace($InputPath)) -or (-not [string]::IsNullOrWhiteSpace($ExpectedInputSha256))
if ($inputProvided -and ([string]::IsNullOrWhiteSpace($InputPath) -or [string]::IsNullOrWhiteSpace($ExpectedInputSha256))) {
    throw 'PAD_ARTIFACT_GATE: InputPath and ExpectedInputSha256 must be provided together'
}
if ($inputProvided -and $ExpectedInputSha256 -notmatch '^[0-9a-fA-F]{64}$') { throw 'PAD_ARTIFACT_GATE: invalid expected input SHA256' }

$sourceBytesBefore = [IO.File]::ReadAllBytes($source)
$sourceBytes = [long]$sourceBytesBefore.Length
$sourceShaBefore = Get-Sha256 $source
$input = $null
$inputShaAfter = ''
$inputUnchanged = $null
if ($inputProvided) { $input = Resolve-ExistingFile $InputPath 'input' }

[IO.File]::Copy($source, $snapshot, $false)
$sourceShaAfter = Get-Sha256 $source
$snapshotSha = Get-Sha256 $snapshot
$snapshotBytes = [long](Get-Item -LiteralPath $snapshot).Length
if ($inputProvided) {
    $inputShaAfter = Get-Sha256 $input
    $inputUnchanged = $inputShaAfter -ceq $ExpectedInputSha256.ToLowerInvariant()
}

$artifactStable = ($sourceShaBefore -ceq $sourceShaAfter)
$snapshotMatches = ($sourceBytes -eq $snapshotBytes -and $sourceShaAfter -ceq $snapshotSha -and $snapshotBytes -ge $MinimumBytes)
$passed = ($artifactStable -and $snapshotMatches -and (($null -eq $inputUnchanged) -or $inputUnchanged))
$reason = if ($passed) { 'snapshot verified before the next run' } else { 'snapshot or input verification failed; do not start the next run' }
$record = [ordered]@{
    schema_version = 1
    kind = 'pad_run_artifact_snapshot'
    observed_at = [DateTime]::UtcNow.ToString('o')
    run_number = $RunNumber
    artifact_path = $ArtifactPath
    snapshot_path = $SnapshotPath
    artifact_bytes_before = $sourceBytes
    artifact_sha256_before = $sourceShaBefore
    artifact_sha256_after = $sourceShaAfter
    snapshot_bytes = $snapshotBytes
    snapshot_sha256 = $snapshotSha
    artifact_stable = $artifactStable
    snapshot_matches_artifact = $snapshotMatches
    minimum_bytes = $MinimumBytes
    input_path = $InputPath
    expected_input_sha256 = $ExpectedInputSha256.ToLowerInvariant()
    input_sha256_after = $inputShaAfter
    input_unchanged = $inputUnchanged
    status = if ($passed) { 'PASS' } else { 'BLOCKED' }
    gate = if ($passed) { 'READY_FOR_NEXT_RUN' } else { 'DO_NOT_START_NEXT_RUN' }
    reason = $reason
}
[IO.File]::WriteAllText($evidence, ($record | ConvertTo-Json -Depth 8), (New-Object Text.UTF8Encoding($false)))
$record | ConvertTo-Json -Depth 8
if (-not $passed) { exit 2 }
