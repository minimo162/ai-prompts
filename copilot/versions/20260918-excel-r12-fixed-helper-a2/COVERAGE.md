# 20260918-excel-r12-fixed-helper-a2 teaching coverage

This is a non-live coverage record for the same-version A2 bundle. It does not
claim Copilot generation, PAD save/re-copy, PAD/Excel execution, or acceptance.

| Requirement | Covered by | Source condition | New-combination boundary |
| --- | --- | --- | --- |
| R01 — state initialization | C01_STATE_INIT | captured and executed only in the R2/R3 one-row probe | COVERED; A2 composition NOT_RUN |
| R02 — existing-output no-write guard | C02_OUTPUT_GUARD | captured and executed around the complete R2/R3 normal probe; dedicated output-guard recopy is separately SHA-pinned | COVERED; A2 composition NOT_RUN |
| R03 — read-only input, sheet activation, TypedValues read | C03_READONLY_TYPED_RANGE | captured and executed for one read-only source range in the R2/R3 probe; scalar/type recopy is separately SHA-pinned | COVERED; A2 composition NOT_RUN |
| R04 — JSON primitive conversion and UTF-8 handoff save | C04_JSON_FILE_HANDOFF | captured and executed only with four source values plus mode in R2/R3 | COVERED; A2 composition NOT_RUN |
| R05 — editable work-copy open | C05_EDITABLE_WORK_OPEN | captured and executed only in the R2/R3 work-copy probe | COVERED; A2 composition NOT_RUN |
| R06 — complete RunScript with fixed launcher | C06_FIXED_LAUNCHER_RUNSCRIPT | captured, saved, re-copied, and executed only in fixed-helper T2 auxiliary Run1 | COVERED; A2 composition NOT_RUN |
| R07 — exact-success and NORMAL branching | C07_EXACT_SUCCESS_MODE_GATE | captured, saved, re-copied, and executed only in fixed-helper T2 auxiliary Run1 | COVERED; A2 composition NOT_RUN |
| R08 — explicit target-sheet activation and numeric WriteCell | C08_TARGET_SHEET_ACTIVATION, C09_NUMERIC_WRITE | captured and executed only for the R2/R3 target sheet; success-gate nesting is a new composition<br>captured and executed for one numeric write in the R2/R3 one-row probe | COVERED; A2 composition NOT_RUN |
| R09 — SaveAs and close/reopen readback | C10_SAVE_CLOSE_REOPEN_READBACK | captured and executed for one readback rectangle in the R2/R3 one-row probe | COVERED; A2 composition NOT_RUN |
| R10 — saved value/type comparison through JSON | C11_JSON_VALUE_TYPE_COMPARE | captured and executed for four positions in the R2/R3 one-row probe | COVERED; A2 composition NOT_RUN |
| R11 — failure close/no-save | C12_FAILURE_CLOSE_NO_SAVE | captured in R2/R3; script-rejection branch executed by its forced-exception negative run | COVERED; A2 composition NOT_RUN |

## Limited non-live conclusions

- Missing required syntax steps: none.
- Every raw block is byte-identical to its cited source line slice.
- C06 decodes to the fixed launcher after restoring only its captured terminal LF.
- Fixed helper, invocation, launcher, request, spec, expected data, runtime path,
  and formal output contract are unchanged.
- A2 parameter substitution, repetition, and full ordering remain an unexecuted new combination.
- The bundle omits the complete fixed-EX03 answer, grader values, and fixed-EX03 full wiring.
