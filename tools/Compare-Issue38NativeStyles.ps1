[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$TemplatePath,
    [Parameter(Mandatory)][string]$OutputPath,
    [Parameter(Mandatory)][string]$EvidencePath,
    [switch]$IncludeSnapshots
)
# Read-only Excel-effective format comparison for the fixed EX02 contract area.
# This complements, but never rewrites, the frozen legacy openpyxl result.
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../catalog/acceptance/issue38'))
$paths = @($TemplatePath, $OutputPath) | ForEach-Object { (Resolve-Path -LiteralPath $_).Path }
$evidence = [IO.Path]::GetFullPath($EvidencePath)
foreach ($path in @($paths) + @($evidence)) {
    if (-not $path.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Dedicated Issue38 paths only'
    }
}
if (Test-Path -LiteralPath $evidence) { throw 'Evidence exists' }
if ($paths[0].Equals($paths[1], [StringComparison]::OrdinalIgnoreCase)) { throw 'Reference and output must differ' }
if (@($paths | Where-Object { [IO.Path]::GetExtension($_) -ne '.xlsx' }).Count) { throw 'Only xlsx inputs are supported' }

$rowCount = 16
$columnCount = 10
$deadline = [DateTime]::UtcNow.AddMinutes(5)
$borderNames = [ordered]@{
    diagonal_down = 5
    diagonal_up = 6
    left = 7
    top = 8
    bottom = 9
    right = 10
}

function ConvertTo-StableValue {
    param($Value)
    if ($null -eq $Value -or $Value -is [DBNull]) { return $null }
    if ($Value -is [decimal]) { return [double]$Value }
    return $Value
}

function ConvertTo-StableJson {
    param($Value)
    return ConvertTo-Json -InputObject $Value -Depth 20 -Compress
}

function Get-TextSha256 {
    param([string]$Text)
    $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $algorithm.Dispose() }
}

function Get-CellSnapshot {
    param($Cell)
    $font = $null
    $interior = $null
    $style = $null
    try {
        $font = $Cell.Font
        $interior = $Cell.Interior
        $style = $Cell.Style
        $borders = [ordered]@{}
        foreach ($entry in $borderNames.GetEnumerator()) {
            $border = $null
            try {
                $border = $Cell.Borders.Item($entry.Value)
                $borders[$entry.Key] = [ordered]@{
                    line_style = ConvertTo-StableValue $border.LineStyle
                    weight = ConvertTo-StableValue $border.Weight
                    color = ConvertTo-StableValue $border.Color
                    color_index = ConvertTo-StableValue $border.ColorIndex
                    theme_color = ConvertTo-StableValue $border.ThemeColor
                    tint_and_shade = ConvertTo-StableValue $border.TintAndShade
                }
            } finally {
                if ($border) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($border) }
            }
        }
        return [ordered]@{
            font = [ordered]@{
                name = ConvertTo-StableValue $font.Name
                name_ascii = ConvertTo-StableValue $font.NameAscii
                name_far_east = ConvertTo-StableValue $font.NameFarEast
                name_other = ConvertTo-StableValue $font.NameOther
                name_complex_script = ConvertTo-StableValue $font.NameComplexScript
                size = ConvertTo-StableValue $font.Size
                bold = ConvertTo-StableValue $font.Bold
                italic = ConvertTo-StableValue $font.Italic
                font_style = ConvertTo-StableValue $font.FontStyle
                color = ConvertTo-StableValue $font.Color
                color_index = ConvertTo-StableValue $font.ColorIndex
                theme_color = ConvertTo-StableValue $font.ThemeColor
                tint_and_shade = ConvertTo-StableValue $font.TintAndShade
                underline = ConvertTo-StableValue $font.Underline
                strikethrough = ConvertTo-StableValue $font.Strikethrough
                subscript = ConvertTo-StableValue $font.Subscript
                superscript = ConvertTo-StableValue $font.Superscript
                shadow = ConvertTo-StableValue $font.Shadow
                outline = ConvertTo-StableValue $font.Outline
            }
            fill = [ordered]@{
                color = ConvertTo-StableValue $interior.Color
                color_index = ConvertTo-StableValue $interior.ColorIndex
                pattern = ConvertTo-StableValue $interior.Pattern
                pattern_color = ConvertTo-StableValue $interior.PatternColor
                pattern_color_index = ConvertTo-StableValue $interior.PatternColorIndex
                theme_color = ConvertTo-StableValue $interior.ThemeColor
                tint_and_shade = ConvertTo-StableValue $interior.TintAndShade
                pattern_theme_color = ConvertTo-StableValue $interior.PatternThemeColor
                pattern_tint_and_shade = ConvertTo-StableValue $interior.PatternTintAndShade
            }
            number_format = [ordered]@{
                invariant = ConvertTo-StableValue $Cell.NumberFormat
                local = ConvertTo-StableValue $Cell.NumberFormatLocal
            }
            alignment = [ordered]@{
                horizontal = ConvertTo-StableValue $Cell.HorizontalAlignment
                vertical = ConvertTo-StableValue $Cell.VerticalAlignment
                wrap_text = ConvertTo-StableValue $Cell.WrapText
                orientation = ConvertTo-StableValue $Cell.Orientation
                shrink_to_fit = ConvertTo-StableValue $Cell.ShrinkToFit
                indent_level = ConvertTo-StableValue $Cell.IndentLevel
                add_indent = ConvertTo-StableValue $Cell.AddIndent
                reading_order = ConvertTo-StableValue $Cell.ReadingOrder
            }
            protection = [ordered]@{
                locked = ConvertTo-StableValue $Cell.Locked
                formula_hidden = ConvertTo-StableValue $Cell.FormulaHidden
            }
            merge_cells = ConvertTo-StableValue $Cell.MergeCells
            # NameLocal is a UI-language label (for example Normal/標準), not
            # workbook formatting identity. Compare Excel's invariant Name.
            style_name = ConvertTo-StableValue $style.Name
            borders = $borders
        }
    } finally {
        if ($style -and [Runtime.InteropServices.Marshal]::IsComObject($style)) {
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($style)
        }
        if ($interior) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($interior) }
        if ($font) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($font) }
    }
}

function Get-WorkbookSnapshot {
    param($Excel, [string]$Path)
    $book = $null
    try {
        $book = $Excel.Workbooks.Open($Path, 0, $true)
        $sheetSnapshots = [ordered]@{}
        foreach ($sheet in $book.Worksheets) {
            try {
                if ([DateTime]::UtcNow -gt $deadline) { throw 'Effective-format comparison deadline exceeded' }
                $rows = [ordered]@{}
                for ($row = 1; $row -le $rowCount; $row++) {
                    if ([DateTime]::UtcNow -gt $deadline) { throw 'Effective-format comparison deadline exceeded' }
                    $rowRange = $null
                    try {
                        $rowRange = $sheet.Rows.Item($row)
                        $rows[[string]$row] = [ordered]@{
                            height = ConvertTo-StableValue $rowRange.RowHeight
                            hidden = ConvertTo-StableValue $rowRange.Hidden
                        }
                    } finally {
                        if ($rowRange) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($rowRange) }
                    }
                }
                $columns = [ordered]@{}
                for ($column = 1; $column -le $columnCount; $column++) {
                    if ([DateTime]::UtcNow -gt $deadline) { throw 'Effective-format comparison deadline exceeded' }
                    $columnRange = $null
                    try {
                        $columnRange = $sheet.Columns.Item($column)
                        $columns[[string]$column] = [ordered]@{
                            width = ConvertTo-StableValue $columnRange.ColumnWidth
                            hidden = ConvertTo-StableValue $columnRange.Hidden
                        }
                    } finally {
                        if ($columnRange) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($columnRange) }
                    }
                }
                $cells = [ordered]@{}
                for ($row = 1; $row -le $rowCount; $row++) {
                    for ($column = 1; $column -le $columnCount; $column++) {
                        if ([DateTime]::UtcNow -gt $deadline) { throw 'Effective-format comparison deadline exceeded' }
                        $cell = $null
                        try {
                            $cell = $sheet.Cells.Item($row, $column)
                            $address = $cell.Address($false, $false)
                            $cells[$address] = Get-CellSnapshot $cell
                        } finally {
                            if ($cell) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
                        }
                    }
                }
                $sheetSnapshots[$sheet.Name] = [ordered]@{
                    rows = $rows
                    columns = $columns
                    cells = $cells
                }
            } finally {
                [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)
            }
        }
        return $sheetSnapshots
    } finally {
        if ($book) {
            $book.Close($false)
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)
        }
    }
}

function Add-AttributeDifferences {
    param(
        [System.Collections.ArrayList]$Differences,
        [string]$Category,
        [string]$Sheet,
        [string]$Location,
        $Before,
        $After,
        [string[]]$Attributes
    )
    foreach ($attribute in $Attributes) {
        $beforeValue = $Before[$attribute]
        $afterValue = $After[$attribute]
        if ((ConvertTo-StableJson $beforeValue) -cne (ConvertTo-StableJson $afterValue)) {
            [void]$Differences.Add([ordered]@{
                category = $Category
                sheet = $Sheet
                location = $Location
                attribute = $attribute
                before = $beforeValue
                after = $afterValue
            })
        }
    }
}

$hashes = @($paths | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant() })
$excel = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AutomationSecurity = 3
    $reference = Get-WorkbookSnapshot $excel $paths[0]
    $output = Get-WorkbookSnapshot $excel $paths[1]
} finally {
    if ($excel) {
        $excel.Quit()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
    }
}
$afterHashes = @($paths | ForEach-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant() })
if (($hashes -join ',') -cne ($afterHashes -join ',')) { throw 'Read-only hash invariant failed' }

$differences = [Collections.ArrayList]::new()
$allSheets = @($reference.Keys) + @($output.Keys) | Sort-Object -Unique
foreach ($sheetName in $allSheets) {
    if (-not $reference.Contains($sheetName) -or -not $output.Contains($sheetName)) {
        [void]$differences.Add([ordered]@{
            category = 'sheet_structure'
            sheet = $sheetName
            location = $sheetName
            attribute = 'presence'
            before = $reference.Contains($sheetName)
            after = $output.Contains($sheetName)
        })
        continue
    }
    for ($row = 1; $row -le $rowCount; $row++) {
        Add-AttributeDifferences $differences 'row_dimension' $sheetName ([string]$row) `
            $reference[$sheetName].rows[[string]$row] $output[$sheetName].rows[[string]$row] @('height', 'hidden')
    }
    for ($column = 1; $column -le $columnCount; $column++) {
        Add-AttributeDifferences $differences 'column_dimension' $sheetName ([string]$column) `
            $reference[$sheetName].columns[[string]$column] $output[$sheetName].columns[[string]$column] @('width', 'hidden')
    }
    foreach ($address in $reference[$sheetName].cells.Keys) {
        Add-AttributeDifferences $differences 'cell_style' $sheetName $address `
            $reference[$sheetName].cells[$address] $output[$sheetName].cells[$address] `
            @('font', 'fill', 'number_format', 'alignment', 'protection', 'merge_cells', 'style_name', 'borders')
    }
}

$categoryCounts = [ordered]@{}
$locationCounts = [ordered]@{}
foreach ($category in @('cell_style', 'row_dimension', 'column_dimension', 'sheet_structure')) {
    $categoryItems = @($differences | Where-Object { $_.category -eq $category })
    $categoryCounts[$category] = $categoryItems.Count
    $locationCounts[$category] = @($categoryItems | ForEach-Object { "$($_.sheet)!$($_.location)" } | Sort-Object -Unique).Count
}
$referenceJson = ConvertTo-StableJson $reference
$outputJson = ConvertTo-StableJson $output
$result = [ordered]@{
    schema_version = 3
    kind = 'EX02_EXCEL_EFFECTIVE_FORMAT_COMPARISON'
    observed_at = [DateTime]::UtcNow.ToString('o')
    read_only = $true
    paths = [ordered]@{ reference = $paths[0]; output = $paths[1] }
    sha256_before = [ordered]@{ reference = $hashes[0]; output = $hashes[1] }
    sha256_after = [ordered]@{ reference = $afterHashes[0]; output = $afterHashes[1] }
    bounds = [ordered]@{
        sheets = @($reference.Keys)
        rows_per_sheet = $rowCount
        columns_per_sheet = $columnCount
        checked_cells = @($reference.Keys).Count * $rowCount * $columnCount
        checked_rows = @($reference.Keys).Count * $rowCount
        checked_columns = @($reference.Keys).Count * $columnCount
    }
    attributes = [ordered]@{
        cell = @('font', 'fill', 'number_format', 'alignment', 'protection', 'merge_cells', 'invariant style_name', 'six edge and diagonal borders')
        row = @('height', 'hidden')
        column = @('width', 'hidden')
    }
    comparison_policy = [ordered]@{
        named_style_identity = 'Excel COM Style.Name (invariant)'
        localized_style_label = 'Style.NameLocal excluded because it is a UI-language label, not formatting identity'
    }
    snapshot_sha256 = [ordered]@{
        reference = Get-TextSha256 $referenceJson
        output = Get-TextSha256 $outputJson
    }
    difference_attribute_counts = $categoryCounts
    difference_location_counts = $locationCounts
    differences = @($differences)
    status = if ($differences.Count) { 'DIFFERENCES_FOUND' } else { 'MATCH_EFFECTIVE_FORMAT' }
    scope = 'Excel-effective formatting and dimensions in the fixed EX02 A1:J16 contract area'
    acceptance_boundary = 'Does not grade values, types, formulas, outside-sheet metadata, PAD completion, or Copilot provenance.'
}
if ($IncludeSnapshots) {
    $result.reference_snapshot = $reference
    $result.output_snapshot = $output
}
$parent = Split-Path -Parent $evidence
if (-not (Test-Path -LiteralPath $parent)) { [void][IO.Directory]::CreateDirectory($parent) }
[IO.File]::WriteAllText($evidence, (($result | ConvertTo-Json -Depth 30) + "`n"), [Text.UTF8Encoding]::new($false))
[pscustomobject]$result | Select-Object kind, status, difference_attribute_counts, difference_location_counts, bounds, acceptance_boundary | ConvertTo-Json -Depth 8
