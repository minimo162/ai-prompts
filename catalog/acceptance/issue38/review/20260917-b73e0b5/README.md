# Issue #38 / EX01–EX05 review snapshot

This is a documentation-only review snapshot built from checkpoint
`b73e0b5a1a2c3f854ced3046b2a2648ddd0b8184`. It does not change a candidate,
fixed request, expected value, comparator verdict, or acceptance condition. It
does not add a Copilot send or PAD run, and it does not declare Issue #38
complete.

The authoritative machine-readable summary is [case-matrix.json](case-matrix.json).
The reproducible archive is `issue38-review-b73e0b5.zip`; its SHA-256 and entry
count are recorded in `archive.json` and `issue38-review-b73e0b5.zip.sha256`.

## Current evidence boundary

| Case | Used version | Formal route | Separate auxiliary evidence | Review decision |
|---|---|---|---|---|
| EX01 | `20260915-excel-r3` | Normal M365 generation, unmodified PAD save/re-copy, two runs | None | Two-run display value and position match only. Individual cell types were not directly observed. |
| EX02 | `20260915-excel-r5` | Normal M365 generation and unmodified G2 PAD two-run fixed text/number path | One-cell same-display type negative; later effective-format reconciliation; separate r5 existing-output guard | Fixed EX02 text/number function has passing evidence. The old pre-reconciliation `FAIL_558_UNRESOLVED` record remains immutable, while the later all-item adjudication classifies all 558 as serialization/comparison-method differences: effective changes 0, unresolved 0. This snapshot makes no new acceptance declaration. |
| EX03 | `20260917-excel-r11` | One normal M365 send; downloaded Robin passed static checks, but the response had 0 required text code blocks, so formal PAD import and runs were stopped | The SHA-identical downloaded Robin passed unmodified PAD save/re-copy and two functional runs in `FILE-AUX1`; its unchanged existing-output branch later passed one guard run | Formal r11 remains FAIL. The two-run and guard PASS records remain auxiliary and do not replace the formal failure. |
| EX04 | `20260915-excel-r3`, plus unchanged r5/r11 flows for live guard evidence | Four r3 negative requests each stopped at generation with no code | Existing-output branch passed once in the unchanged r5 G2 flow and once in the unchanged r11 FILE-AUX1 flow | Generation-stop coverage is 4/4. Live PAD coverage is limited to the existing-output branch; missing-sheet, invalid-range, and same-input/output runtime paths remain unassessed. Guard runs do not assess transferred cell types. |
| EX05 | `20260915-excel-r3` | Values-only and full-copy boundary requests; no code/PAD run | None | Scope distinction passed. A complete generated/runtime flow was not achieved. |

## r11 identity

- Version: `20260917-excel-r11`
- Instructions SHA-256: `bceb1c7e4f47c0cd6a92ad698d08108175002bffcaaaff492a309ca74a122aa1`
- Bundle SHA-256: `2d95ce344ff66195061fd15010d13b75937888575fa2345fb543ae2115242f69`
- Manifest SHA-256: `295306ea7e2e45da8cf77dec2784e94ea8ea8333da0df6a4000f83e9228b509e`
- Generated Robin SHA-256: `a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875`
- Formal EX03 r11 result: `FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD`
- FILE-AUX1 result: `PASS_AUXILIARY_DOWNLOADED_FILE_TWO_RUN_VALIDATION`
- Existing-output guard result: `PASS_FIXED_R11_FILE_AUX1_EXISTING_OUTPUT_GUARD`

## 558 differences

The legacy raw comparator's 558 differences remain visible as historical
evidence. The later fixed-scope attribute-by-attribute reconciliation classified
all of them:

- cell style: 480 serialization/comparison-method differences;
- row dimension: 48 serialization/comparison-method differences;
- column dimension: 30 serialization/comparison-method differences;
- actual effective format/dimension changes: 0;
- unresolved: 0.

The corrected comparator also detected the intentional three-change negative
(fill, row height, and column width). Therefore the 558 count is not carried
forward as unresolved real workbook corruption. This conclusion is limited to
the fixed EX02/EX03 workbook scope represented by the preserved evidence.

## Residuals

| Residual | Impact |
|---|---|
| Formal EX03 r11 delivery contract failed | EX03 formal acceptance remains FAIL even though the SHA-identical downloaded file passed the auxiliary route. |
| EX01 per-cell runtime types were not observed | EX01 proves displayed values and positions only. |
| EX02/EX03 type evidence covers the fixed text/number cells only | Blank, Boolean, date, error, formula-result, object, other PAD versions, and other PCs are not generalized. |
| Existing-output guard runs did not enter the write path | Their type-transfer result is `NOT_ASSESSED`, not PASS or FAIL. |
| EX04 has no live PAD runtime evidence for three negative branches | Missing-sheet, invalid-range, and same-input/output runtime handling remain open. |
| EX05 has no generated runnable flow | Only the values-only/full-copy scope boundary is established. |
| Overall Issue #38 | Not declared complete by this review snapshot. |

## Archive contents

The ZIP contains the complete r11 candidate set, both unmodified copies of the
generated Robin, selected implementation/comparator/test diffs, current selected
review code, the key formal and auxiliary decision records, all 558
classifications, and the synthetic EX02/EX03 input/template/output workbooks
needed for independent comparison. It intentionally excludes screenshots,
browser captures, and bulk protected-file inventories.

