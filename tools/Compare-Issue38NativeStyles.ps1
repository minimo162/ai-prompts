[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$TemplatePath,
    [Parameter(Mandatory)][string]$OutputPath,
    [Parameter(Mandatory)][string]$EvidencePath
)
# Supplemental read-only diagnosis. Does not grade values, PAD completion or Copilot.
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../catalog/acceptance/issue38'))
$paths=@($TemplatePath,$OutputPath) | ForEach-Object { (Resolve-Path -LiteralPath $_).Path }
$evidence=[IO.Path]::GetFullPath($EvidencePath)
foreach($p in @($paths)+@($evidence)) {
    if(-not $p.StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Dedicated Issue38 paths only'}
}
if(Test-Path -LiteralPath $evidence){throw 'Evidence exists'}
$hashes=@($paths | ForEach-Object {(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash})
$excel=$null;$book=$null;$snapshots=@();$deadline=[DateTime]::UtcNow.AddSeconds(90)
try {
    $excel=New-Object -ComObject Excel.Application
    $excel.Visible=$false;$excel.DisplayAlerts=$false;$excel.AutomationSecurity=3
    foreach($p in $paths){
        $book=$excel.Workbooks.Open($p,0,$true)
        $snapshot=[ordered]@{}
        foreach($sheet in $book.Worksheets){
            $prefix=$sheet.Name
            for($r=1;$r -le 16;$r++){
                if([DateTime]::UtcNow -gt $deadline){throw 'Read-only diagnostic deadline exceeded'}
                $snapshot["$prefix/row/$r"]=@($sheet.Rows.Item($r).RowHeight,$sheet.Rows.Item($r).Hidden)
                for($c=1;$c -le 10;$c++){
                    $cell=$sheet.Cells.Item($r,$c)
                    $snapshot["$prefix/cell/$r/$c"]=@(
                        $cell.Font.Name,$cell.Font.Size,$cell.Font.Bold,$cell.Font.Italic,$cell.Font.Color,
                        $cell.Font.Underline,$cell.Font.Strikethrough,$cell.Interior.Color,$cell.Interior.Pattern,
                        $cell.NumberFormat,$cell.HorizontalAlignment,$cell.VerticalAlignment,$cell.WrapText,
                        $cell.Orientation,$cell.ShrinkToFit,$cell.IndentLevel,$cell.Locked,$cell.FormulaHidden,
                        $cell.MergeCells,
                        @(@(5,6,7,8,9,10) | ForEach-Object { $border=$cell.Borders.Item($_); @($border.LineStyle,$border.Weight,$border.Color) })
                    )
                    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)
                }
            }
            for($c=1;$c -le 10;$c++){ $snapshot["$prefix/column/$c"]=@($sheet.Columns.Item($c).ColumnWidth,$sheet.Columns.Item($c).Hidden) }
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
        }
        $snapshots+=,$snapshot
        $book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book);$book=$null
    }
} finally {
    if($book){$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
    if($excel){$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}
}
$after=@($paths | ForEach-Object {(Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash})
if(($hashes -join ',') -cne ($after -join ',')){throw 'Read-only hash invariant failed'}
$differences=@()
foreach($key in @($snapshots[0].Keys)+@($snapshots[1].Keys) | Sort-Object -Unique){
    $a=ConvertTo-Json -InputObject $snapshots[0][$key] -Depth 8 -Compress
    $b=ConvertTo-Json -InputObject $snapshots[1][$key] -Depth 8 -Compress
    if($a -cne $b){$differences+=@{key=$key;template=$snapshots[0][$key];output=$snapshots[1][$key]}}
}
$result=[ordered]@{kind='SUPPLEMENTAL_NATIVE_STYLE_COMPARISON';observed_at=[DateTime]::UtcNow.ToString('o');paths=$paths;sha_before=$hashes;sha_after=$after;checked_cells=480;bounds='Each existing sheet A1:J16';attributes='font,fill,number format,alignment,protection,merge,borders,row/column size and hidden';differences=$differences;status=$(if($differences.Count){'DIFFERENCES_FOUND'}else{'MATCH_WITHIN_RECORDED_SCOPE'});acceptance='NOT_PROVEN; excludes values, types, formulas, other sheet metadata, PAD completion and Copilot'}
[IO.File]::WriteAllText($evidence,($result|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))
[pscustomobject]$result | Select-Object kind,status,checked_cells,acceptance | ConvertTo-Json
