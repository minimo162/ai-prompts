# EX03-R12-FIXED-HELPER-A4-G1 final result

## Decision

`STOPPED_FAIL_GENERATED_ROBIN_WIRING_AND_FIXED_LAUNCHER_MISMATCH`

The fixed A4 submitted body and same-version bundle were sent exactly once to the normal Microsoft 365 Copilot chat. Copilot produced one Plain Text code preview. The code-copy payload was preserved without editing as `generated.robin` with SHA-256 `eb5648631466da3431a21cf8df98fb06e5fece8876c3705b6483b4d74b58e290`.

The generated Robin was rejected before PAD. C06 decodes to SHA-256 `b4674b8c3c50685c30e58af42388525723823841ab9b3bc25b7f43c653c8dae5`, not the fixed launcher SHA-256 `a286179f8fb7f8febc87f1915cf10965ee0a50769251ecb17573c00926c174d5`. The decoded payload has 7 lines instead of 60, contains neither the fixed helper invocation nor the helper/invocation SHA checks, and has 1 PowerShell parser error(s).

C11 contains 7 of 12 required comparisons. Missing fixed positions: 入力ろ.xlsx!追加項目!C2 -> 追記先!E5, 入力ろ.xlsx!追加項目!D2 -> 追記先!F5, 入力ろ.xlsx!追加項目!B3 -> 追記先!D6, 入力ろ.xlsx!追加項目!C3 -> 追記先!E6, 入力ろ.xlsx!追加項目!D3 -> 追記先!F6. Lines 98, 100, and 102 also use an uncaptured inline `Variables.ConvertCustomObjectToJson(...)` expression rather than the captured PAD action/output form. These failures independently trigger the fixed stop condition.

## Fixed identity

- Candidate: `20260918-excel-r12-fixed-helper-a4`
- Route: `EX03-R12-FIXED-HELPER-COPILOT-A4`
- Instruction SHA-256: `93cfd7aa5d0f1c380e1a5c50f764794a7bab2e676f1d064c9fe9b349788f3829`
- Submitted body SHA-256: `8924f824256a161f035f686b221ea58bf2033a66e0ef359c8968506c338f9647`
- Bundle SHA-256: `62695ca3c007ab291732657ddaeca66723a57115d151efc7b1730ef5341c514c`
- WIRING SHA-256: `c62ec6951bdd36e895acfc937d7a1f390e75e8d984b26a9531cc2c88d970f58c`
- Helper SHA-256: `08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135`
- Invocation SHA-256: `5c5a2008f55296a48f63fa65178aab971e4212455bb2af58e33149bdcaec40d8`
- Fixed launcher SHA-256: `a286179f8fb7f8febc87f1915cf10965ee0a50769251ecb17573c00926c174d5`
- Generated Robin SHA-256: `eb5648631466da3431a21cf8df98fb06e5fece8876c3705b6483b4d74b58e290`
- Copilot response text SHA-256: `3a241e5fab1ad0055266d162309ee26defc4ffa8959b9fb5bb2caeb5634e5451`
- Conversation: `https://m365.cloud.microsoft/chat/conversation/442418c7-e760-4245-965d-9c08a1daa2de?es=SSR`

## Checks and stop boundary

- Copilot send: 1 / 1
- Plain Text code previews: 1
- Browser code-copy payload: unmodified, LF-only, no final newline, 113 lines
- PAD IF/ELSE/END balance: PASS
- Embedded PowerShell parser: 1 error(s)
- Static forbidden-token and fixed-path safety audit: PASS
- Fixed launcher exactness: FAIL
- Text source JSON mappings/writes: 7 / 7 (fixed launcher gate FAIL; no transfer was run)
- Numeric writes: 5 / 5
- Readback rectangles: 2 / 2
- JSON value/type comparisons: 7 / 12, FAIL
- Uncaptured inline expression shapes: 3, FAIL
- PAD save/re-copy: NOT_RUN
- PAD Run1 / Run2: NOT_RUN / NOT_RUN
- Resend / manual repair / additional run / next candidate / GitHub write: 0 / 0 / 0 / 0 / 0

## Preserved state

- Protected files checked: 25
- Protected mismatches: 0
- Work SHA-256: `881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21`
- Work still matches the fixed template: true
- Output absent: true
- A4 JSON handoff directory absent: true
- Formal r12 FAIL remains unchanged.
- Fixed-helper T2 auxiliary PASS is not inherited.
- A3 refusal remains separate and unchanged.
- The legacy 558-difference record remains preserved and is not reclassified.

No PAD/Excel operation was performed after the generated-Robin mismatch was found.
