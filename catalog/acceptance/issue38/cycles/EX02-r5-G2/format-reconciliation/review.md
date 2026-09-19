# EX02 legacy 558 format reconciliation

## Conclusion

All 558 preserved legacy failures are serialization or comparison-method differences within the fixed EX02 contract area. None is an Excel-effective formatting or dimension change in the no-edit SaveAs control, G2 Run1, or G2 Run2. This conclusion is based on per-location raw before/after inspection plus read-only Excel-effective attribute comparison; it is not inferred from the repeated count alone.

The old `acceptance-status.json` and its `FAIL_558_UNRESOLVED` decision remain unchanged. `classification.json` is a separate adjudication record.

- Preserved old acceptance SHA-256: `634298a3619039ff2e2fad0028e407e71b29ced8749bbbe6788176476b257292`
- Common Excel-effective snapshot SHA-256 for the template, no-edit SaveAs, Run1 and Run2: `28a5ca0636f95e679c3d4834e13ec248fef5e5fd8829463051759a8250186ea4`

## Cause counts

- 480 cell-style failures: Excel SaveAs adds `font.charset=128` and `font.family=3` for Yu Gothic and serializes five absent border sides as explicit empty sides. Excel-effective font, fill, number format, alignment, protection, merge state, style and six edge/diagonal border values are unchanged at every cell.
- 48 row-dimension failures: raw height changes from `22` to `14.65`. Excel opens both the template and each output at `14.7` points with the same hidden state.
- 30 column-dimension failures: ten separate raw column records per sheet are coalesced into one equivalent `min=1,max=10,width=20` record. Excel opens every column at width `19.42` with the same hidden state.

`classification.json` contains one entry for each of the 558 legacy failures, including the raw attribute changes, reproduction in the no-edit SaveAs control and Run2, Excel-effective before/after hashes, and final classification. Its totals are 558 serialization/comparison differences, zero actual effective changes, and zero unresolved entries.

## Comparator correction

The legacy comparator remains available to reproduce the old FAIL. Its defect is using `str(openpyxl style object)` and sparse row/column record identity as formatting truth. That treats omitted defaults versus explicit defaults, unit-normalized row heights, and equivalent coalesced column records as changes.

`tools/Compare-Issue38NativeStyles.ps1` now performs the corrected read-only comparison over all three sheets and the full fixed `A1:J16` area: 480 cells, 48 rows, and 30 columns. It compares Excel-effective font details, fill, number format, alignment, protection, merge state, style, six border directions, row height/hidden, and column width/hidden. It records attribute-level differences, location counts, input hashes before/after, snapshot hashes, and an optional full snapshot.

The first negative rerun also exposed a comparator-specific localization issue: COM returned `Style.NameLocal` as `Normal` in the source and `標準` in the edited copy although the invariant style identity was `Normal` on both. The corrected comparator therefore records and compares `Style.Name`, not the UI-language label `Style.NameLocal`. This removes a locale-dependent false attribute without suppressing the deliberate fill, row-height or column-width changes.

## Positive and negative results

- No-edit SaveAs, Run1 and Run2: `MATCH_EFFECTIVE_FORMAT`; the reference and output snapshot SHA are identical.
- Deliberate negative: exactly three effective changes detected — `Target A!C4` fill, row 2 height `14.7 -> 30.0`, and column B width `19.42 -> 23.42`.
- Deliberate negative workbook SHA-256: `4ebf7b15d34b67c59dcc36c4c4b58a332354c7cfdc9ed2111a870416001212ea`.
- The deliberate negative retains all twelve target values/types/positions and all 468 outside values/types/formulas. Its saved render visibly shows the red cell, taller row and wider column.
- The old comparator still reports its legacy representation noise for the negative (`column_dimensions=30`) while also detecting the real row and fill changes. It is therefore retained as historical evidence, not used as the corrected format verdict.

## Acceptance impact and limits

The 558 formatting/dimension blocker is resolved for the fixed template, no-edit SaveAs control, G2 Run1, G2 Run2, and this Excel environment. The functional G2 status remains `PASS_FIXED_EX02_TEXT_NUMBER_SCOPE`.

This does not generalize to other templates, other Excel/PAD versions, other PCs, or unconfirmed cell types. No Copilot generation, PAD run, candidate-version change or GitHub write occurred. The candidate remains `20260915-excel-r5`. The existing-output guard branch remains not live-tested and stays open, so overall Issue #38 acceptance is not declared complete and no acceptance condition is relaxed.
