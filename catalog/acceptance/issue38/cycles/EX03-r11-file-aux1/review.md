# EX03-r11 downloaded-file auxiliary PAD validation

## Decision

- Formal `EX03-r11-G1`: **NOT ACCEPTED**. Its one normal-M365 response delivered zero of the one required text code blocks, so `FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD` remains unchanged and its formal PAD count remains 0.
- Separately identified downloaded-file auxiliary path: **PASS** for the fixed EX03 text/number case only. This does not offset the formal delivery-contract failure and does not close Issue #38.

## Fixed identity

- Version: `20260917-excel-r11`
- Instruction SHA-256: `bceb1c7e4f47c0cd6a92ad698d08108175002bffcaaaff492a309ca74a122aa1`
- Bundle SHA-256: `2d95ce344ff66195061fd15010d13b75937888575fa2345fb543ae2115242f69`
- Manifest SHA-256: `295306ea7e2e45da8cf77dec2784e94ea8ea8333da0df6a4000f83e9228b509e`
- Submitted body SHA-256: `4bd51be17353634c8b38cabbee91a9235a1dd1af87243675f5d42500f40c5984`
- Copilot downloaded / preserved / safety-audit target Robin SHA-256: `a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875` (all identical)
- PAD flow: `無題 (10)` (window `71280`, Power Fx OFF), 110 actions and 45 flow variables
- Save/re-copy: LF-normalized exact match; no generated Robin repair

## Two PAD runs

| Gate | Run1 | Run2 |
| --- | --- | --- |
| Terminal READY, no designer error | PASS | PASS |
| PAD JSON value-and-type flags | 12 True / 0 False | 12 True / 0 False |
| Fixed target values/types/positions | 12/12, mismatch 0 | 12/12, mismatch 0 |
| Outside values/types/formulas | 468 checked, mismatch 0 | 468 checked, mismatch 0 |
| Excel-effective format/dimensions | 480 cells + 48 rows + 30 columns, difference 0 | same, difference 0 |
| Legacy raw comparator | FAIL 558 preserved (480 styles, 48 rows, 30 columns) | same |
| Artifact SHA-256 | `ddcd8fdd443262edeba6ad2f1523e175ca4d94431d9df14122605bb4fc34a38f` | `d41fb0ac1b142c1aa1ffa3ce2f542a8cd70b4483593173c08a084dc8340ccb34` |

The two XLSX archives have different binary SHA values, which is expected for separately saved ZIP packages, while the full 480-cell semantic comparison is `MATCH`.

## F6 fixed text edge case

Both runs independently read saved/reopened `追記先!F6` as:

- value: `100%`
- .NET type: `System.String`
- number format: `G/標準` (unchanged from the template)
- prefix character: empty
- formula: none

## Preservation and remaining work

- All 4397 pre-existing tracked files match the pre-run SHA snapshot.
- Runtime `work.xlsx` remains `881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21` and the fixed output path is absent after recoverable evidence preservation.
- Existing-output guard live behavior remains unconfirmed.
- The old raw 558-result is retained and is not relabeled as PASS; the separate Excel-effective comparison records zero actual format/dimension changes.
- No type or shape beyond the fixed EX03 text/number mapping is generalized.
- No GitHub write was performed.
