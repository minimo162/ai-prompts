# EX03-R12-FIXED-HELPER-COPILOT-A3-G1 final result

## Decision

`STOPPED_FAIL_REFUSAL`

The fixed A3 submitted body and the same-version bundle were sent exactly once to the normal Microsoft 365 Copilot chat. Copilot completed its response but explicitly declined to provide a paste-ready completed Robin. The response contained no `pre` block and therefore no required single Markdown `text` code block.

The refusal is preserved verbatim in `copilot-response.txt`. The displayed response body had SHA-256 `d5fb79f3fd7a1acbe24050940a4efd3a2105fe9fa016a223a0e6762231738c90`. The stored text adds one terminal LF and has SHA-256 `834fc02ed6d3aea5ad96bcd992a80903dcc7f620e87b870ebcaa7843ddc13ea4`.

## Fixed send identity

- Candidate: `20260918-excel-r12-fixed-helper-a3`
- Route: `EX03-R12-FIXED-HELPER-COPILOT-A3`
- Instruction SHA-256: `87d4fad6445be8371bfcad9d35d2ce8c384758714c7d48e0232a1ce60ab89d98`
- Submitted body SHA-256: `eae9de79a8c0ec4796ee90b3dd9e41b35c72490c483d7f15723891b0441142c3`
- Bundle SHA-256: `50c60d9533b9afb4d698416d6f9bf0b30040dee69206cf1734dea565f740b0c4`
- Helper SHA-256: `08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135`
- Invocation SHA-256: `92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6`
- Launcher SHA-256: `1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1`

## Counts and gates

- Copilot send: 1 / 1
- Required `text` code blocks: 0
- Generated Robin: none
- Syntax and safety audit: NOT_RUN_NO_GENERATED_ROBIN
- PAD save/re-copy: NOT_RUN_STOPPED_ON_REFUSAL
- PAD Run1: NOT_RUN_STOPPED_ON_REFUSAL
- PAD Run2: NOT_RUN_STOPPED_ON_REFUSAL
- Resend: 0
- Manual generated-code edit: 0
- Next candidate: 0
- GitHub write: 0

## Preserved state

- Protected files checked: 26
- Protected mismatches: 0
- Work SHA-256: `881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21`
- Work still matches the fixed template: true
- Output absent: true
- Eight JSON handoff files present: 0
- Formal r12 FAIL remains unchanged.
- Fixed-helper T2 auxiliary PASS is not inherited.
- A1 and A2 refusals remain separate and unchanged.
- The legacy 558-difference record remains preserved and is not reclassified.

The fixed refusal stop condition was applied. No retry, resend, PAD/Excel execution, candidate change, acceptance-condition change, or GitHub write was performed.
