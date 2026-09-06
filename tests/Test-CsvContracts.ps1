# Deterministic CSV contracts. No Copilot, browser, PAD or user data.
[CmdletBinding()]
param([string]$AppSourcePath = '')
$ErrorActionPreference = 'Stop'
if (-not $AppSourcePath) { $AppSourcePath = Join-Path $PSScriptRoot '..\App.ps1' }
. ([IO.Path]::GetFullPath($AppSourcePath)) -Mode Library
$script:Checks = 0
function Assert-True($Condition, [string]$Name) { if (-not $Condition) { throw ('FAIL: ' + $Name) }; $script:Checks++ }
function Assert-Throws([scriptblock]$Action, [string]$Pattern, [string]$Name) {
    $message = ''; try { & $Action | Out-Null } catch { $message = $_.Exception.Message }
    Assert-True ($message -match $Pattern) ($Name + ' (' + $message + ')')
}
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\csv-' + [guid]::NewGuid().ToString('N'))))
[void][IO.Directory]::CreateDirectory($root)
$categories = @('支払','決算','システム','その他')
function Write-Fixture([string]$Name, [int]$Count) {
    $records = @([pscustomobject]@{ values = @('id','本文','任意列') })
    for ($i = 1; $i -le $Count; $i++) {
        $records += [pscustomobject]@{ values = @($i.ToString('00000000000000000000'), ("支払の依頼, 引用`" 100%`r`n" + ('日本語 ' * 25)), $(if ($i % 2 -eq 0) { '=1+1' } else { '' })) }
    }
    $path = Join-Path $root $Name
    [IO.File]::WriteAllText($path, (ConvertTo-AgentCsv $records), (New-Object Text.UTF8Encoding($true)))
    return $path
}
Assert-True ($PSVersionTable.PSVersion.Major -eq 5) 'Windows PowerShell 5.1'
$text = "id,本文,x`r`n001,`"改行`r`nカンマ,引用`"`"保持`",`r`n002,=1+1,`" `"`r`n"
$parsed = ConvertFrom-AgentCsv $text
Assert-True ($parsed.Count -eq 3 -and $parsed[1].values[0] -ceq '001' -and $parsed[1].values[1] -ceq "改行`r`nカンマ,引用`"保持" -and $parsed[1].values[2] -ceq '') 'CSV preserves exact values'
Assert-True ((ConvertTo-AgentCsv (ConvertFrom-AgentCsv (ConvertTo-AgentCsv $parsed))) -ceq (ConvertTo-AgentCsv $parsed)) 'CSV round trip'
Assert-True ((ConvertFrom-AgentCsv 'a,b,')[0].values.Count -eq 3) 'Trailing empty field without newline'
Assert-True ((ConvertFrom-AgentCsv '').Count -eq 0) 'Empty input is empty'
foreach ($bad in @('a,"unclosed', 'a,b"c', 'a,"b"tail', 'a,"b" ')) { Assert-Throws { ConvertFrom-AgentCsv $bad } 'CSV_SYNTAX' 'Malformed CSV rejected' }
foreach ($count in @(1,50,100)) {
    $inputPath = Write-Fixture ("synthetic-$count.csv") $count
    $hash = Get-AgentHash $inputPath
    $manifest = New-AgentCsvManifest @($inputPath)
    Assert-True ($manifest.total_count -eq $count -and $manifest.eligible_count -eq $count) "$count records selected"
    Assert-True ($manifest.rows[0].original_id -ceq '00000000000000000001' -and $manifest.sources[0].bom) 'Long original ID and BOM preserved'
    $results = New-AgentCsvResults $manifest
    $summary = Get-AgentCsvSummary $manifest $results $categories
    Assert-True ($summary.unprocessed -eq $count -and -not $summary.processing_complete) 'Initial rows accounted for'
    foreach ($result in $results) { $result.category = '支払'; $result.reason = '支払の依頼が明記されています。'; $result.status = 'success' }
    $receipt = Export-AgentCsvResults $root $manifest $results $categories
    Assert-True ($receipt.summary.processing_complete -and $receipt.summary.all_success -and -not $receipt.summary.content_approved) 'Structural completion is not human approval'
    Assert-True ((Get-AgentHash $inputPath) -ceq $hash) 'Original file unchanged'
    $canonical = Read-AgentJson $receipt.artifacts[0].path
    Assert-True ($canonical.rows.Count -eq $count -and $canonical.rows[0].values[0] -ceq $manifest.rows[0].values[0]) 'Canonical JSON full reread'
    foreach ($artifact in $receipt.artifacts) { Assert-True ((Get-AgentHash $artifact.path) -ceq $artifact.sha256) 'All published hashes verified' }
    $second = Export-AgentCsvResults $root $manifest $results $categories
    Assert-True ($second.export_id -cne $receipt.export_id -and (Get-AgentHash $receipt.artifacts[0].path) -ceq $receipt.artifacts[0].sha256) 'Export never overwrites existing result'
    if ($count -eq 100) {
        Assert-True (([IO.File]::ReadAllText($receipt.artifacts[1].path)).Length -gt 8193 -and ($receipt.artifacts | Measure-Object bytes -Sum).Sum -gt 32768) 'Full verification exceeds former preview budgets'
        $results[99].category = ''; $results[99].status = 'unknown'; $results[99].reason = '送信後の結果を確認できません。'
        $summary = Get-AgentCsvSummary $manifest $results $categories
        Assert-True ($summary.unknown -eq 1 -and -not $summary.processing_complete -and -not $summary.all_success) 'One unknown prevents completion'
    }
    if ($count -eq 50) { $fifty = $manifest; $fiftyPath = $inputPath }
}
$rows = @($fifty.rows | Select-Object -First 5); $requestId = [guid]::NewGuid().ToString('N')
$response = [pscustomobject]@{ schema_version = 1; request_id = $requestId; results = @($rows | ForEach-Object { [pscustomobject]@{ row_id = $_.row_id; category = '支払'; reason = '支払依頼です。'; status = 'success' } }) }
function Response-Text { return ConvertTo-Json -InputObject $response -Depth 10 -Compress }
$validText = Response-Text
$validated = ConvertFrom-AgentCsvBatchResponse $validText $requestId $rows $categories
Assert-True ($validated.Count -eq 5) 'Structured batch accepted'
[Array]::Reverse($response.results)
$validated = ConvertFrom-AgentCsvBatchResponse (Response-Text) $requestId $rows $categories
Assert-True ($validated[0].row_id -ceq $rows[0].row_id) 'Model order cannot change original order'
$response = ConvertFrom-Json $validText; $response.results[1].row_id = $response.results[0].row_id
Assert-Throws { ConvertFrom-AgentCsvBatchResponse (Response-Text) $requestId $rows $categories } 'CSV_RESPONSE' 'Duplicate row rejected'
$response = ConvertFrom-Json $validText; $response.results[0].category = '候補外'
Assert-Throws { ConvertFrom-AgentCsvBatchResponse (Response-Text) $requestId $rows $categories } 'CSV_RESPONSE' 'Unknown label rejected'
$response = ConvertFrom-Json $validText; $response.results[0].reason = ''
Assert-Throws { ConvertFrom-AgentCsvBatchResponse (Response-Text) $requestId $rows $categories } 'CSV_RESPONSE' 'Missing reason rejected'
$response = ConvertFrom-Json $validText; $response.results = @($response.results | Select-Object -First 4)
Assert-Throws { ConvertFrom-AgentCsvBatchResponse (Response-Text) $requestId $rows $categories } 'CSV_RESPONSE' 'Missing row rejected'
$response = ConvertFrom-Json $validText; $response.request_id = [guid]::NewGuid().ToString('N')
Assert-Throws { ConvertFrom-AgentCsvBatchResponse (Response-Text) $requestId $rows $categories } 'CSV_RESPONSE' 'Late response request ID rejected'
$response = ConvertFrom-Json $validText; $response.results[0] | Add-Member path 'C:\outside.txt'
Assert-Throws { ConvertFrom-AgentCsvBatchResponse (Response-Text) $requestId $rows $categories } 'CSV_RESPONSE' 'Model path argument rejected'
Assert-Throws { ConvertFrom-AgentCsvBatchResponse ($validText.Replace('"schema_version":1', '"schema_version":1,"schema_version":1')) $requestId $rows $categories } 'Duplicate' 'Duplicate JSON keys rejected'
$mixed = New-AgentCsvResults $fifty
for ($i = 0; $i -lt 24; $i++) { $mixed[$i].reason = 'テスト結果'; if ($i -lt 23) { $mixed[$i].category = '支払'; $mixed[$i].status = $(if ($i -lt 20) { 'success' } else { 'needs_review' }) } else { $mixed[$i].status = 'failed' } }
$summary = Get-AgentCsvSummary $fifty $mixed $categories
Assert-True ($summary.total -eq 50 -and $summary.success -eq 20 -and $summary.needs_review -eq 3 -and $summary.failed -eq 1 -and $summary.unprocessed -eq 26 -and -not $summary.processing_complete) 'Partial outcome accounts for all 50 rows'
$partial = Export-AgentCsvResults $root $fifty $mixed $categories
Assert-True ((ConvertFrom-AgentCsv ([IO.File]::ReadAllText($partial.artifacts[2].path))).Count -eq 4 -and (ConvertFrom-AgentCsv ([IO.File]::ReadAllText($partial.artifacts[3].path))).Count -eq 28) 'Review and unfinished exports have correct counts'
$mixed[1].row_id = $mixed[0].row_id
Assert-Throws { Get-AgentCsvSummary $fifty $mixed $categories } 'CSV_RESULTS' 'Duplicate stored result rejected'
$dupPath = Join-Path $root 'duplicates.csv'
[IO.File]::WriteAllText($dupPath, "id,本文`n001,支払`n001,決算`n002,`n,その他`n", $script:AgentEncoding)
$duplicate = New-AgentCsvManifest @($dupPath)
Assert-True ($duplicate.total_count -eq 4 -and $duplicate.eligible_count -eq 0 -and @($duplicate.rows | Select-Object -ExpandProperty row_id -Unique).Count -eq 4) 'Duplicate and blank rows retained separately with exclusions'
$invalidResults = New-AgentCsvResults $duplicate; $invalidResults[0].category = '支払'; $invalidResults[0].status = 'success'
Assert-Throws { Get-AgentCsvSummary $duplicate $invalidResults $categories } 'CSV_RESULTS' 'Excluded rows cannot become successful'
$badPath = Join-Path $root 'bad.csv'
foreach ($bad in @("id,id`na,b", "id,本文`na,b,c", "id,本文", "ID,本文`na,b", "id,`na,b")) { [IO.File]::WriteAllText($badPath, $bad, $script:AgentEncoding); Assert-Throws { New-AgentCsvManifest @($badPath) } 'CSV_(COLUMNS|ROWS)' 'Bad input rejected' }
[IO.File]::WriteAllBytes($badPath, [byte[]]@(0x82, 0xa0, 0x82))
Assert-Throws { Read-AgentCsvSource $badPath } 'CSV_ENCODING' 'Invalid UTF-8 not guessed'
[IO.File]::WriteAllText($badPath, "id,本文`r`n001,支払`r`n", [Text.Encoding]::GetEncoding(932))
$cp932 = New-AgentCsvManifest @($badPath) -EncodingName cp932
Assert-True ($cp932.rows[0].original_text -ceq '支払' -and $cp932.sources[0].encoding -ceq 'cp932') 'Explicit CP932 decoded'
Assert-Throws { Read-AgentCsvSource $fiftyPath cp932 } 'CSV_ENCODING' 'BOM rejects conflicting encoding selection'
$tooMany = Write-Fixture 'too-many.csv' 101
Assert-Throws { New-AgentCsvManifest @($tooMany) } 'CSV_CAPACITY' '101 rows refused'
Assert-Throws { New-AgentCsvManifest @($fiftyPath,$fiftyPath) } 'CSV_TARGET' 'Duplicate file selection refused'
$copyDir = Join-Path $root 'sub'; [void][IO.Directory]::CreateDirectory($copyDir)
$sameName = Join-Path $copyDir ([IO.Path]::GetFileName($dupPath)); [IO.File]::Copy($dupPath, $sameName)
$multiple = New-AgentCsvManifest @($dupPath,$sameName)
Assert-True ($multiple.sources.Count -eq 2 -and $multiple.sources[0].name -ceq $multiple.sources[1].name -and $multiple.sources[0].source_id -cne $multiple.sources[1].source_id -and $multiple.total_count -eq 8) 'Same basename in distinct directories remains distinct'
[IO.File]::AppendAllText($fiftyPath, "051,変更,追加`r`n", $script:AgentEncoding)
Assert-Throws { Assert-AgentCsvSourcesUnchanged $fifty } 'CSV_CHANGED' 'Change after selection detected'
$before = @(Get-ChildItem -LiteralPath $root -Directory).Count
Assert-Throws { Export-AgentCsvResults $root $fifty (New-AgentCsvResults $fifty) $categories } 'CSV_CHANGED' 'Changed source prevents output'
Assert-True (@(Get-ChildItem -LiteralPath $root -Directory).Count -eq $before) 'Rejected export creates no output'
$safe = ConvertFrom-AgentCsv (ConvertTo-AgentCsv @([pscustomobject]@{ values = @('=1+1',' +cmd','@SUM(A1)','-1',"`ttext",'001') }) -ExcelSafe)
Assert-True ($safe[0].values[0] -ceq "'=1+1" -and $safe[0].values[1] -ceq "' +cmd" -and $safe[0].values[4] -ceq "'`ttext" -and $safe[0].values[5] -ceq '001') 'Excel-view formula mitigation explicit; IDs unchanged in CSV'
Write-Output ("PASS: $script:Checks CSV contract checks; live sends 0 (no provider invoked). Evidence: $root")
