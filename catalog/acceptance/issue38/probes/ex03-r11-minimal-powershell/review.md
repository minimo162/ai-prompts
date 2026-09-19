# Issue #38 EX03 r11 local cause analysis and bounded validation

## 判定

`PASS_LOCAL_R11_CAUSE_BOUNDARY_AND_BOUNDED_PAD_VALIDATION_NOT_EX03_ACCEPTANCE`。r9/r10共通の欠落は後段のcopy/save/extract/decodeでは発生しておらず、最初に保全できた応答表現に既に存在した。非公開のmodel/service内部原因は推定しない。

r11は指示だけでなく内包PowerShellを実変更した。88行 / 5011 byteを58行 / 3300 byteへ短縮し、壊れた3静的member表現を廃止した。独立教材のPAD保存・再コピーはPASS、同じ短縮表現の合成2セルprobeはPAD 1 Runと成果物13/13をPASSした。ただしCopilot送信0、EX03統合Run 0なのでEX03受入ではない。

## 変更前後

変更前:

```powershell
if ([string]::Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, [StringComparison]::OrdinalIgnoreCase)) {
if ($afterPrefixCharacter -cne $beforePrefixCharacter -or -not [string]::IsNullOrEmpty($afterPrefixCharacter)) {
```

変更後:

```powershell
$targetPath = [IO.Path]::GetFullPath($targetPath)
if ([IO.Path]::GetFullPath([string]$candidate.FullName) -ieq $targetPath) { $matches += $candidate }
try {
    $cell.NumberFormat = '@'
    $cell.Value2 = [string]$payload.probe
}
finally { $cell.NumberFormat = $beforeNumberFormat }
if ([string]$cell.PrefixCharacter -cne '') { throw (...) }
```

完全diff: `r10-to-r11-script.diff`

## 証拠

- r9境界: `rendered_response_code_dom`。DOMとcode copy SHAは同一。
- r10境界: `copied_full_response`。full responseはcode copyをbyte同一で内包。
- known-good decode: parser error 0。
- 意図的破損負例: 欠落2件をdecode後も保持しparser error 19、未実行。
- 独立教材PAD: 1 paste / 1 save / 1 recopy、110 action / 45 variable、LF正規化一致、実行0。
- 合成PAD: 1 paste / 1 save / 1 recopy / 1 Run。source/immediate/reopenedのtext/number JSON比較6件は全True。
- 成果物: text value/type、number value/type、元書式、prefix空、formulaなし、source/work非改変を含む13/13 PASS。
- 例外復元: inner finally構造と正常経路の元書式復元はPASS。強制例外RunはNOT_RUN。

## 固定版

- version: `20260917-excel-r11`
- instruction SHA-256: `bceb1c7e4f47c0cd6a92ad698d08108175002bffcaaaff492a309ca74a122aa1` (7240 UTF-16 units)
- bundle SHA-256: `2d95ce344ff66195061fd15010d13b75937888575fa2345fb543ae2115242f69`
- manifest SHA-256: `295306ea7e2e45da8cf77dec2784e94ea8ea8333da0df6a4000f83e9228b509e`
- PAD-recopied teaching Robin SHA-256: `148267f09f53d74db1059cee823a4a2e159f2bbebfa249d3a25c996796fa765b`
- embedded script SHA-256: `068e676d70c373a9cf8203d19f6154e38460f609c4fdf774dbef1528f68fc7ae`

固定依頼・spec・expected、r9/r10生成物、旧558差分記録はSHA固定で非改変。既存output guard実機経路は未確認のまま。GitHub書込み0。
