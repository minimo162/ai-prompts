# Actual PS5 persistence and host batch contracts with a replaced provider; no live sends.
[CmdletBinding()]
param([string]$AppSourcePath = '')
$ErrorActionPreference = 'Stop'
if (-not $AppSourcePath) { $AppSourcePath = Join-Path $PSScriptRoot '..\App.ps1' }
. ([IO.Path]::GetFullPath($AppSourcePath)) -Mode Library
$script:Checks = 0; $script:Calls = 0; $script:Failure = ''; $script:Prompts = @()
function Assert-True($Condition, [string]$Name) { if (-not $Condition) { throw ('FAIL: ' + $Name) }; $script:Checks++ }
function Assert-Throws([scriptblock]$Action, [string]$Pattern, [string]$Name) {
    $message = ''; try { & $Action | Out-Null } catch { $message = $_.Exception.Message }
    Assert-True ($message -match $Pattern) ($Name + ' (' + $message + ')')
}
function Invoke-AgentCopilot {
    param($Prompt,$RequestId,$JobId,$Settings,$HomePath,$CancelPath,$TimeoutSeconds)
    $script:Calls++; $script:Prompts += $Prompt
    if ($script:Failure -ceq 'auth') { throw 'AUTH_REQUIRED: synthetic login failure' }
    Reserve-AgentCopilotAttempt $HomePath $RequestId
    if ($script:Failure -ceq 'timeout') { throw 'RESPONSE_TIMEOUT: synthetic post-send timeout' }
    if ($script:Failure -ceq 'invalid') { return '{"schema_version":1,"request_id":"wrong","results":[]}' }
    $payload = ConvertFrom-Json ($Prompt.Substring($Prompt.IndexOf("REQUEST_JSON:`n") + "REQUEST_JSON:`n".Length))
    return ConvertTo-Json -Depth 10 -Compress @{ schema_version = 1; request_id = $RequestId; results = @($payload.rows | ForEach-Object { @{ row_id = $_.row_id; category = '支払'; reason = '合成応答。意味精度の証拠ではありません。'; status = 'success' } }) }
}
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\csv-batch-' + [guid]::NewGuid().ToString('N'))))
$testHome = Initialize-AgentHome $root
$inputFile = Join-Path $root 'synthetic.csv'
$records = @([pscustomobject]@{ values = @('id','本文','非送信列') })
for ($i = 1; $i -le 50; $i++) { $records += [pscustomobject]@{ values = @($i.ToString('000'), ("合成本文 $i, 100% 引用`"`r`nパスC:\DATA\x"), 'DO_NOT_SEND_OPTIONAL_COLUMN') } }
[IO.File]::WriteAllText($inputFile, (ConvertTo-AgentCsv $records), $script:AgentEncoding)
$manifest = New-AgentCsvManifest @($inputFile); $categories = @('支払','決算','システム','その他'); $instructions = '担当分野で分け、不明なものは要確認。'
$plan = New-AgentCsvBatches $manifest @($manifest.rows | ForEach-Object row_id) $categories $instructions
Assert-True ($plan.batches.Count -eq 10 -and $plan.selected_count -eq 50 -and $plan.oversized_row_ids.Count -eq 0) '50 records partition into ten finite batches'
Assert-True (@($plan.batches | ForEach-Object row_ids | Select-Object -Unique).Count -eq 50) 'Every row appears once'
Assert-True (@($plan.batches | Where-Object { $_.prompt.Length -gt 24000 -or $_.row_ids.Count -gt 5 }).Count -eq 0) 'Serialized request and row bounds enforced'
Assert-True (-not ($plan.batches[0].prompt.Contains('DO_NOT_SEND_OPTIONAL_COLUMN')) -and -not ($plan.batches[0].prompt.Contains($inputFile))) 'Only opaque row ID and selected text sent'
Assert-Throws { New-AgentCsvBatches $manifest @([guid]::NewGuid().ToString('N')) $categories $instructions } 'CSV_TARGET' 'Unknown target rejected before provider'
Assert-Throws { New-AgentCsvBatches $manifest @($manifest.rows[0].row_id,$manifest.rows[0].row_id) $categories $instructions } 'CSV_TARGET' 'Repeated target rejected before provider'
$jobId = [guid]::NewGuid().ToString('N'); $jobDir = Get-AgentJobDirectory $root $jobId; [void][IO.Directory]::CreateDirectory($jobDir)
$result = Invoke-AgentCsvBatch $root $jobId $manifest $plan.batches[0] $categories $instructions
Assert-True ($result.phase -ceq 'committed' -and $result.results.Count -eq 5 -and $result.status -ceq 'success') 'Provider output persisted and reread'
$disk = Read-AgentJson (Join-Path $jobDir ('csv-attempts\' + $result.request_id + '\attempt.json'))
Assert-True ($disk.result_sha256 -ceq (Get-AgentHash (Join-Path $jobDir ('csv-attempts\' + $result.request_id + '\result.json'))) -and $disk.phase -ceq 'committed') 'Attempt binds committed result hash'
$before = $script:Calls
Assert-Throws { Invoke-AgentCsvBatch $root $jobId $manifest $plan.batches[0] $categories $instructions } 'CSV_REPLAY' 'Used batch cannot resend'
Assert-True ($script:Calls -eq $before) 'Replay prevention before provider'
$script:Failure = 'auth'
$auth = Invoke-AgentCsvBatch $root $jobId $manifest $plan.batches[1] $categories $instructions
Assert-True ($auth.phase -ceq 'not_sent' -and $auth.status -ceq 'unprocessed' -and $auth.error_type -ceq 'AUTH_REQUIRED') 'Pre-send auth preserves unprocessed state'
$script:Failure = 'timeout'
$timeout = Invoke-AgentCsvBatch $root $jobId $manifest $plan.batches[2] $categories $instructions
Assert-True ($timeout.phase -ceq 'send_uncertain' -and $timeout.status -ceq 'unknown' -and $timeout.error_type -ceq 'RESPONSE_TIMEOUT') 'Post-reservation timeout remains unknown'
$script:Failure = 'invalid'
$invalid = Invoke-AgentCsvBatch $root $jobId $manifest $plan.batches[3] $categories $instructions
Assert-True ($invalid.phase -ceq 'response_rejected' -and $invalid.status -ceq 'failed' -and $invalid.results.Count -eq 0) 'Bad response cannot publish rows'
$script:Failure = ''
[IO.File]::WriteAllText((Join-Path $jobDir 'cancel'), 'stop', $script:AgentEncoding)
$before = $script:Calls
$cancelled = Invoke-AgentCsvBatch $root $jobId $manifest $plan.batches[4] $categories $instructions
Assert-True ($cancelled.phase -ceq 'not_sent' -and $cancelled.error_type -ceq 'CANCELLED' -and $script:Calls -eq $before) 'Stop before provider has zero calls'
$large = ConvertFrom-Json (ConvertTo-Json $manifest -Depth 20)
$large.rows[0].original_text = '大' * 25000
$sized = New-AgentCsvBatches $large @($large.rows | ForEach-Object row_id) $categories $instructions
Assert-True ($sized.oversized_row_ids.Count -eq 1 -and $sized.oversized_row_ids[0] -ceq $large.rows[0].row_id -and @($sized.batches | ForEach-Object row_ids).Count -eq 49) 'Oversized row reported separately, never truncated or lost'
$large.rows[0].original_text = '中' * 12000; $large.rows[1].original_text = '中' * 12000
$sized = New-AgentCsvBatches $large @($large.rows[0].row_id,$large.rows[1].row_id) $categories $instructions
Assert-True ($sized.batches.Count -eq 2 -and $sized.oversized_row_ids.Count -eq 0) 'Byte-independent serialized character limit splits batches'
$selected = New-AgentCsvBatches $manifest @($manifest.rows[30].row_id,$manifest.rows[48].row_id) $categories '要確認の2行だけ、追加条件で分類。'
Assert-True ($selected.selected_count -eq 2 -and ($selected.batches[0].row_ids -join ',') -ceq (@($manifest.rows[30].row_id,$manifest.rows[48].row_id) -join ',')) 'Follow-up selection cannot reprocess unrelated rows'
Write-Output ("PASS: $script:Checks CSV batch checks; $script:Calls mock provider entries, live sends 0. Evidence: $root")
