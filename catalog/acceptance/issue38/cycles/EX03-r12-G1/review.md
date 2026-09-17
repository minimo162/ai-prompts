# EX03-r12-G1 one-send result

## Outcome

`FAIL_GENERATED_ROBIN_MISMATCH_AND_POWERSHELL_PARSE_ERROR_STOP_BEFORE_PAD`. The authorized normal Microsoft 365 Copilot send was used once. The response was not a refusal and exposed one code-preview block whose copied `text/plain` excluded the UI language badge, visual line numbers, and expansion control. The unmodified payload nevertheless failed the fixed fidelity and syntax gates, so no PAD save, re-copy, or Run was attempted.

## Fixed inputs

- candidate: `20260917-excel-r12` at `0f6e47197ecb5f4316e00aa319efa6c4213f696f`
- instruction SHA-256: `11321acdbb96632221b02b7b737d12ba816ea4cf9f35f933a114c7f857539c06`
- bundle SHA-256: `ddee43a1eddc966f62095b63a23b135df184f3cbe0ded635cbf72520e6744b97`
- submitted body SHA-256: `cf25fb4aa54375d992e00545d336058b67055ab7de934e52ce284dffcd9924cc`
- generated Robin SHA-256: `64b6c7de822a448a4696910cc683c77ebfc57920c91aa966851947e136b5a366`

## New observations

- Send history: no local r12 cycle and no Copilot chat-search result for the full version ID before this cycle.
- Destination/model: normal Microsoft 365 Copilot new chat / Think Deeper.
- Send count: 1 of 1; no retry or regeneration.
- Delivery: one copyable code-preview block; clipboard content starts with a PAD action and ends with `END`.
- Fidelity: expected 276 lines versus generated 272 lines. Four blank lines outside the authorized data-slot substitutions were deleted.
- Blocking corruption: expected `[Console]::Out.Write([string]($result | ConvertTo-Json -Compress))''' ScriptOutput=> PowershellOutput`; generated `[Console]::Out.Write([string]($result | press)''' ScriptOutput=> PowershellOutput`.
- PowerShell AST: prepared script 0 errors; generated embedded script 4 errors (missing closing parenthesis and three cascading missing braces).
- PAD: save 0, re-copy 0, Run1 0, Run2 0, comparison 0.
- Run workspace: `work.xlsx` remains SHA-256 `881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21` and `照合結果.xlsx` is absent.
- Protected evidence: 4563 files checked, mismatch 0.

## Preserved scope

r11's formal delivery-contract failure, its separately identified auxiliary result, the legacy 558 raw-difference failure, fixed request/spec/expected data, and all older evidence remain unchanged. The generated payload was not repaired, and no successor candidate or GitHub write was made.
