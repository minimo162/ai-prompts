$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../App.ps1') -Mode Library -OfflineTest
$root=Join-Path $PSScriptRoot ('../.work/document-robin-'+[guid]::NewGuid().ToString('N'))
$root=[IO.Path]::GetFullPath($root);$inputs=Join-Path $root 'inputs';$run=Join-Path $root 'run';$output=Join-Path $run 'artifacts'
foreach($path in @($inputs,$output)){[void][IO.Directory]::CreateDirectory($path)}
foreach($name in @('source-a.pdf','source-b.pdf')){[IO.File]::Copy((Join-Path $PSScriptRoot ('../catalog/fixtures/pdf/'+$name)),(Join-Path $inputs $name))}
$job=[pscustomobject]@{target=$inputs};$checks=0
function Accept($code){$null=Test-AgentRobin $code $run $job;$script:checks++}
function Reject($code,$expected){$message='';try{$null=Test-AgentRobin $code $run $job}catch{$message=$_.Exception.Message};if($message -notlike ($expected+':*')){throw ('Check '+$script:checks+': expected '+$expected+', got '+$message)};$script:checks++}
function Read-Capture($relative){return [IO.File]::ReadAllText((Join-Path $PSScriptRoot ('../catalog/'+$relative)),[Text.Encoding]::UTF8)}
function Map-Outputs($code){
 $literal='\$\x27{3}(?:[^\x27\\\r\n]|\\[\\\x27\x22])*\x27{3}'
 return [regex]::Replace($code,'(DocumentPath|ExtractedPDFPath|MergedPDFPath|ImagesFolder|CSVFile): ('+$literal+')',[Text.RegularExpressions.MatchEvaluator]{param($m) $path=ConvertFrom-AgentRobinLiteral $m.Groups[2].Value;return $m.Groups[1].Value+': '+(ConvertTo-AgentRobinLiteral (Join-Path $output ([IO.Path]::GetFileName($path))))})
}
$office=Map-Outputs (Read-Capture 'flows/office-roundtrip/roundtrip.robin')
Accept $office
$plan=Test-AgentRobin $office $run $job -Detailed
if($plan.outputs.Count -ne 3 -or @($plan.documents.instances.Values|Where-Object {$_.open}).Count){throw 'Bad Office lifecycle plan'};$checks++
$pdf=Map-Outputs (Read-Capture 'flows/pdf-variants/assembled.robin')
$pdf=$pdf.Replace('C:\\Temp\\AiPromptsPdfCatalog_20260907\\',($inputs+'\').Replace('\','\\'))
Accept $pdf
$csv=Map-Outputs (Read-Capture 'flows/pdf-table-csv/roundtrip.robin')
$csv=$csv.Replace('C:\\Temp\\AiPromptsPdfCatalog_20260907\\',($inputs+'\').Replace('\','\\'))
Accept $csv
Reject ($csv.Replace('[0].DataTable','[0].Password')) ROBIN_ACTION
Reject ($csv.Replace('[0].DataTable','[100].DataTable')) ROBIN_ACTION
Reject ($csv.Replace('VariableToWrite: PdfTablesHeaders[0].DataTable','VariableToWrite: PdfTablesHeaders')) ROBIN_TYPE
Reject ($csv.Replace('ColumnsSeparator.Comma','ColumnsSeparator.Tab')) ROBIN_ACTION
Reject ($office.Replace('Excel.CloseExcel.Close Instance: ExcelInstance','')) ROBIN_INSTANCE
Reject ($office.Replace('Word.CloseWord.Close Instance: WordInstance','')) ROBIN_INSTANCE
Reject ($office.Replace('PowerPoint.ClosePowerPoint.Close Instance: PowerPointInstance','')) ROBIN_INSTANCE
Reject ($office.Replace('Word.ReadFromWord.Read Instance: WordInstance','Word.ReadFromWord.Read Instance: ExcelInstance')) ROBIN_INSTANCE
Reject ($office.Replace('Word.ReadFromWord.Read Instance: WordInstance','Word.ReadFromWord.Read Instance: Missing')) ROBIN_INSTANCE
Reject ($office.Replace('Excel.SaveExcel.SaveAs','Excel.SaveExcel.Save')) ROBIN_ACTION
Reject ($office.Replace('OfficeCatalog', '=WEBSERVICE')) ROBIN_FORMULA
Reject ($office.Replace('OfficeCatalog', ' +SUM')) ROBIN_FORMULA
Reject ($office.Replace('OfficeCatalog', '%Missing%')) ROBIN_FORMULA
Reject ($office.Replace("Column: `$'''A''' Row: 1","Column: `$'''XFE''' Row: 1")) ROBIN_DOCUMENT
Reject ($office.Replace(' Row: 1',' Row: 0')) ROBIN_DOCUMENT
Reject ($office.Replace('SlidePosition: SlideIndex','SlidePosition: Missing')) ROBIN_TYPE
Reject ($office.Replace('SlidePosition: SlideIndex','SlidePosition: 0')) ROBIN_DOCUMENT
$overwrite=$office.Replace('excel-catalog.xlsx','existing.xlsx');[IO.File]::WriteAllText((Join-Path $output 'existing.xlsx'),'do not modify')
Reject $overwrite ROBIN_WRITE
Reject ($office.Replace((ConvertTo-AgentRobinLiteral (Join-Path $output 'excel-catalog.xlsx')),(ConvertTo-AgentRobinLiteral (Join-Path $inputs 'outside.xlsx')))) ROBIN_PATH
Reject ($office.Replace('Word.ReadFromWord.Read Instance: WordInstance WordData=> WordData','Word.ReadFromWord.Read Instance: WordInstance WordData=> WordInstance')) ROBIN_INSTANCE
Reject ($pdf.Replace('FromPageNumber: 2 ToPageNumber: 3','FromPageNumber: 3 ToPageNumber: 2')) ROBIN_DOCUMENT
Reject ($pdf.Replace('PageNumber: 2','PageNumber: 0')) ROBIN_DOCUMENT
Reject ($pdf.Replace("PageSelection: `$'''2-3'''","PageSelection: `$'''3-2'''")) ROBIN_DOCUMENT
Reject ($pdf.Replace('Pdf.IfFileExists.DoNotModifyFiles','Pdf.IfFileExists.Overwrite')) ROBIN_ACTION
Reject ($pdf.Replace('ImagesName: '+(ConvertTo-AgentRobinLiteral 'CatalogImage'),'ImagesName: '+(ConvertTo-AgentRobinLiteral '..\escape'))) ROBIN_WRITE
$indented=(@($office -split '\r?\n'|Where-Object {$_}|ForEach-Object {'    '+$_}) -join "`r`n")
Reject ("SET Flag TO `$'''yes'''`r`nIF Flag = `$'''yes''' THEN`r`n"+$indented+"`r`nEND") ROBIN_DOCUMENT_BLOCK
$source=Join-Path $inputs 'input.pptx';[IO.File]::WriteAllText($source,'snapshot')
$open='PowerPoint.LaunchPowerPoint.LaunchAndOpen Path: '+(ConvertTo-AgentRobinLiteral $source)+' ReadOnly: False Instance=> Ppt'
$code=$open+"`r`n"+'PowerPoint.ClosePowerPoint.Close Instance: Ppt'
$detail=Test-AgentRobin $code $run $job -Detailed
$execution=Get-AgentDocumentExecutionRobin $code $detail $run
if($execution -ceq $code -or $execution -notlike '*control*inputs*' -or [IO.File]::ReadAllText($source) -cne 'snapshot'){throw 'Input staging did not isolate the source'};$checks++
$unchanged=Get-AgentDocumentExecutionRobin 'SET TextValue TO 0' @{documents=@{reads=@{}}} $run
if($unchanged -cne 'SET TextValue TO 0'){throw 'Staging changed non-document code'};$checks++
foreach($extension in @('pdf','xlsx','docx','pptx')){[IO.File]::WriteAllText((Join-Path $inputs ('target.'+$extension)),'fixture');$rules=Get-AgentPlannerRules (Join-Path $inputs ('target.'+$extension));if($rules -notlike '*TARGET_READ_ROBIN_JSON_STRING:*' -or $rules -notlike '*Captured full formats:*'){throw 'Document guide not connected'};$checks++}
Write-Output "PASS: $checks document Robin checks; no native Office/PAD/Copilot execution."
