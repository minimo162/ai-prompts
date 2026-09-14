[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$utf8 = [Text.Encoding]::UTF8
$checks = 0

function Check([bool]$Value, [string]$Name) {
    if (-not $Value) { throw ('FAIL: ' + $Name) }
    $script:checks++
}

function FullPath([string]$RelativePath) {
    return [IO.Path]::GetFullPath((Join-Path $Root ($RelativePath.Replace('/', '\'))))
}

function Read-Json([string]$RelativePath) {
    $path = FullPath $RelativePath
    Check (Test-Path -LiteralPath $path -PathType Leaf) ('evidence exists: ' + $RelativePath)
    return ([IO.File]::ReadAllText($path, $utf8) | ConvertFrom-Json)
}

function Hash-File([string]$RelativePath) {
    return (Get-FileHash -LiteralPath (FullPath $RelativePath) -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Hash-Bytes([byte[]]$Bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}

function Read-Utf8([string]$RelativePath) {
    return [IO.File]::ReadAllText((FullPath $RelativePath), $utf8)
}

function Read-ZipEntryText([string]$RelativePath, [string]$EntryName) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead((FullPath $RelativePath))
    try {
        $entry = $zip.GetEntry($EntryName)
        if ($null -eq $entry) { throw ('XLSX_ENTRY: missing ' + $EntryName) }
        $stream = $entry.Open()
        $reader = New-Object IO.StreamReader($stream, $utf8)
        try { return $reader.ReadToEnd() }
        finally { $reader.Dispose(); $stream.Dispose() }
    }
    finally { $zip.Dispose() }
}

function Read-XlsxRows([string]$RelativePath) {
    $ns = New-Object System.Xml.XmlNamespaceManager((New-Object System.Xml.XmlDocument).NameTable)
    $ns.AddNamespace('d', 'http://schemas.openxmlformats.org/spreadsheetml/2006/main')

    $shared = @()
    $sharedXml = Read-ZipEntryText $RelativePath 'xl/sharedStrings.xml'
    $sharedDoc = New-Object System.Xml.XmlDocument
    $sharedDoc.LoadXml($sharedXml)
    foreach ($node in $sharedDoc.SelectNodes('//d:si', $ns)) { $shared += ,$node.InnerText }

    $workbookDoc = New-Object System.Xml.XmlDocument
    $workbookDoc.LoadXml((Read-ZipEntryText $RelativePath 'xl/workbook.xml'))
    $sheet = $workbookDoc.SelectSingleNode('//d:sheet', $ns)
    $sheetName = if ($null -eq $sheet) { $null } else { $sheet.GetAttribute('name') }

    $sheetDoc = New-Object System.Xml.XmlDocument
    $sheetDoc.LoadXml((Read-ZipEntryText $RelativePath 'xl/worksheets/sheet1.xml'))
    $rows = @()
    foreach ($rowNode in $sheetDoc.SelectNodes('//d:sheetData/d:row', $ns)) {
        $values = @()
        foreach ($cell in $rowNode.SelectNodes('./d:c', $ns)) {
            $valueNode = $cell.SelectSingleNode('./d:v', $ns)
            $value = if ($null -eq $valueNode) { '' } else { $valueNode.InnerText }
            $type = $cell.GetAttribute('t')
            if ($type -eq 's' -and $value -match '^\d+$') { $value = $shared[[int]$value] }
            elseif ($type -eq 'inlineStr') {
                $inline = $cell.SelectSingleNode('./d:is', $ns)
                $value = if ($null -eq $inline) { '' } else { $inline.InnerText }
            }
            $values += [string]$value
        }
        $rows += ,$values
    }
    return [pscustomobject]@{ sheet = $sheetName; rows = $rows }
}

$comparisonPath = 'catalog/evidence/t04-independent-current-output-comparison-20260914e.json'
$comparison = Read-Json $comparisonPath
$paste = Read-Json 'catalog/evidence/t04-independent-current-pad-paste-save-20260914e.json'
$run1 = Read-Json 'catalog/evidence/t04-independent-current-pad-run1-20260914e.json'
$run2 = Read-Json 'catalog/evidence/t04-independent-current-pad-run2-20260914e.json'
$result = Read-Json 'catalog/generated/normal-chat-20260914e-t04-independent-live/result.json'

$instruction = 'copilot/agent-instructions.txt'
$bundle = 'copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt'
$manifest = 'copilot/knowledge-bundle-manifest-20260913e.json'
$robin = 'catalog/generated/normal-chat-20260914e-t04-independent-live/robin.txt'
$response = 'catalog/generated/normal-chat-20260914e-t04-independent-live/response.txt'
$recopy = 'catalog/evidence/t04-independent-current-pad-recopy-20260914e.robin'
$xlsx = 'catalog/evidence/t04-independent-current-output-run2-20260914e.xlsx'
$input = 'catalog/fixtures/excel/t04-filter-input.xlsx'

$instructionHash = Hash-File $instruction
$bundleHash = Hash-File $bundle
Check ($instructionHash -ceq '6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c') 'current instruction hash'
Check ($bundleHash -ceq '79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12') 'current bundle hash'
Check (Test-Path -LiteralPath (FullPath $manifest) -PathType Leaf) 'current manifest exists'
Check ([string]$comparison.version.manifest -ceq $manifest) 'comparison names current manifest'
Check ([string]$comparison.version.instruction_sha256 -ceq $instructionHash -and [string]$comparison.version.knowledge_bundle_sha256 -ceq $bundleHash) 'comparison binds current source hashes'
Check ([string]$result.instruction_sha256 -ceq $instructionHash -and [string]$result.knowledge_bundle_sha256 -ceq $bundleHash) 'result binds current source hashes'

Check ([string]$comparison.status -ceq 'PASS_CURRENT_20260914E_INDEPENDENT_T04_GENERATION_PAD_TWO_RUNS_PARTIAL') 'candidate status is preserved'
Check ([string]$comparison.acceptance_scope -ceq 'candidate_partial') 'candidate scope is partial'
Check ([string]$comparison.strict_source_to_generation -ceq 'NOT_ASSESSED') 'strict source-to-generation remains unassessed'
Check ([string]$comparison.not_accepted_reason -match 'Run1.*snapshot.*not captured') 'missing Run1 snapshot is explicit'
Check ([string]$result.status -ceq [string]$comparison.status -and [string]$result.acceptance_scope -ceq 'candidate_partial') 'result does not promote candidate'

Check ([string]$comparison.generation.dom_code.sha256 -ceq 'dd4f39f0700cfb5a9275dfc9912c89bd8d886d72972c9eb74223acf30343569d') 'source Robin SHA contract'
Check ((Hash-File $robin) -ceq [string]$comparison.generation.dom_code.sha256) 'generated Robin file hash'
Check ((Get-Item -LiteralPath (FullPath $robin)).Length -eq 1585) 'generated Robin byte count'
$robinText = Read-Utf8 $robin
Check ([regex]::Matches($robinText, '=>').Count -eq 5) 'generated Robin plain arrow count'
Check ([regex]::Matches($robinText, '\\=>').Count -eq 0) 'generated Robin has no escaped arrows'
Check ([string]$comparison.generation.dom_code.raw_unmodified -eq 'True' -and [string]$result.response_origin_backslash_arrow_count -eq '0') 'response-origin Robin remains unmodified'
Check ($comparison.generation.official_response_copy.raw_unmodified -eq $true) 'official response marked raw unmodified'
$responseText = Read-Utf8 $response
Check ($responseText.EndsWith("`n")) 'official response keeps captured trailing LF'
$responseWithoutLf = $responseText.Substring(0, $responseText.Length - 1)
Check ($responseWithoutLf.Length -eq 1954) 'response no-LF length'
Check ((Hash-Bytes $utf8.GetBytes($responseWithoutLf)) -ceq [string]$comparison.generation.official_response_copy.sha256_without_trailing_lf) 'response no-LF hash'

Check ([string]$paste.flow.source_sha256 -ceq [string]$comparison.generation.dom_code.sha256) 'paste source binds generated Robin'
Check ([int]$paste.flow.source_bytes -eq 1585 -and $paste.flow.paste_confirmed -eq $true) 'paste was confirmed from source'
Check ([int]$paste.flow.designer_action_count -eq 9 -and [int]$paste.flow.visible_action_count -eq 6) 'authoritative action count and virtualized visible count preserved'
Check ($paste.flow.virtualized_list_false_negative -eq $true -and $paste.flow.saved_confirmed -eq $true) 'virtualization and save evidence preserved'
Check ($paste.flow.hand_edit_applied -eq $false) 'no Robin hand edit'
Check ((Hash-File $recopy) -ceq [string]$comparison.pad.recopy_sha256) 'recopy hash'
Check ([int](Get-Item -LiteralPath (FullPath $recopy)).Length -eq [int]$comparison.pad.recopy_bytes) 'recopy byte count'
Check ($comparison.pad.source_to_recopy_crlf_normalized_equal -eq $true -and $comparison.pad.source_to_recopy_strict_bytes -eq $false) 'recopy normalization and strict-byte distinction'
$robinNormalized = (Read-Utf8 $robin) -replace "`r`n", "`n"
$recopyNormalized = (Read-Utf8 $recopy) -replace "`r`n", "`n"
Check ($robinNormalized -ceq $recopyNormalized) 'recopy content matches after CRLF normalization'

Check ([string]$run1.flow_name -ceq [string]$comparison.pad.flow_name -and [string]$run2.flow_name -ceq [string]$comparison.pad.flow_name) 'both runs bind the recorded flow'
Check ([string]$run1.run_status -ceq 'success' -and [string]$run2.run_status -ceq 'success') 'both runs succeeded'
Check ($run1.ready_observed -eq $true -and $run2.ready_observed -eq $true -and $run1.start_enabled_after -eq $true -and $run2.start_enabled_after -eq $true) 'both runs returned to ready state'
Check ([string]$comparison.execution.run1.output_snapshot -ceq 'NOT_CAPTURED' -and [string]$comparison.execution.run2.output_snapshot -ceq 'catalog/evidence/t04-independent-current-output-run2-20260914e.xlsx') 'per-run output boundary is explicit'
Check ([string]$comparison.execution.run2.output_snapshot -ceq 'catalog/evidence/t04-independent-current-output-run2-20260914e.xlsx') 'Run2 output path'
Check ((Hash-File $xlsx) -ceq [string]$comparison.execution.run2.output_sha256 -and (Get-Item -LiteralPath (FullPath $xlsx)).Length -eq [int]$comparison.execution.run2.output_bytes) 'Run2 output hash and size'
Check ([string]$result.run1_output_snapshot -ceq 'NOT_CAPTURED' -and [string]$result.run2_output_snapshot -ceq [string]$comparison.execution.run2.output_snapshot) 'result preserves per-run snapshots'

$book = Read-XlsxRows $xlsx
Check ([string]$book.sheet -ceq 't04-filtered') 'Run2 output sheet name'
$targetLabel = ([char]0x5bfe).ToString() + ([char]0x8c61).ToString()
$expectedRows = @()
$expectedRows += ,@($targetLabel,'A','10')
$expectedRows += ,@($targetLabel,'C','25')
$expectedRows += ,@($targetLabel,'D','5')
Check ($book.rows.Count -eq 3) 'Run2 output row count'
for ($i = 0; $i -lt $expectedRows.Count; $i++) {
    Check ($book.rows[$i].Count -eq 3) ('Run2 output column count row ' + ($i + 1))
    for ($j = 0; $j -lt 3; $j++) { Check ([string]$book.rows[$i][$j] -ceq [string]$expectedRows[$i][$j]) ('Run2 output cell ' + ($i + 1) + ',' + ($j + 1)) }
}

$inputHash = Hash-File $input
Check ($inputHash -ceq [string]$comparison.execution.input_sha256_before -and $inputHash -ceq [string]$comparison.execution.input_sha256_after) 'input SHA before and after'
Check ($comparison.execution.input_unchanged -eq $true -and $comparison.execution.run2.input_and_existing_output_restored -eq $true) 'input and existing outputs restored'

$candidateDir = FullPath 'catalog/generated/normal-chat-20260914e-t04-independent-live'
$run1Xlsx = @(Get-ChildItem -LiteralPath $candidateDir -File | Where-Object { $_.Name -match '(?i)run[-_]?1.*\.xlsx$' })
Check ($run1Xlsx.Count -eq 0) 'no fabricated Run1 xlsx exists'
Check ([string]$comparison.execution.run1.output_snapshot -ceq 'NOT_CAPTURED') 'Run1 remains unmeasured'
Check ([int]$comparison.pad.runs_completed -eq 2 -and [int]$result.runs_completed -eq 2) 'no third run was added'

Write-Output ('PASS: ' + $checks + ' T04 independent evidence checks; candidate_partial preserved and Run1 output remains NOT_CAPTURED.')
