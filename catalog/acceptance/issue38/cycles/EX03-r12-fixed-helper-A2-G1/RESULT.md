# EX03-R12-FIXED-HELPER-COPILOT-A2-G1 result

- Candidate: `20260918-excel-r12-fixed-helper-a2`
- Route: `EX03-R12-FIXED-HELPER-COPILOT-A2`
- Base commit: `e768b2a14dd8d154ee987554d7c13c53ca644b0f`
- Destination: normal Microsoft 365 Copilot Chat
- Send: exactly one send; the precise click timestamp was not separately captured
- Submitted body SHA-256: `1f151cee4d822ca4b9a5585683d4f0efbf766e21b5d0b67fd1eaa3d7041531c6`
- Attached bundle SHA-256: `009a830d7a1bb431c1f02933e45933c2d7466260c616e46114255605dc3e5b1c`
- Copilot response SHA-256: `0f9f298fbdbe23c0750f7582e8733ff801b0eec4bae9c793d3cf3f82c82370fc` before the repository text file's terminal LF
- Copilot result: `FAIL_REFUSAL_NO_ROBIN`
- Required `text` code blocks: expected 1, observed 0
- PAD save/re-copy: `NOT_RUN_STOPPED_ON_REFUSAL`
- PAD Run1/Run2: `NOT_RUN_STOPPED_ON_REFUSAL`
- Resend: not performed and forbidden by the one-send limit

Before send, the normal Microsoft 365 Copilot destination, one exact attachment filename, and fixed 10,119-character submitted body were checked. Excluding the editor's `aria-hidden` Lexical marker, the UI body SHA-256 exactly matched the fixed submitted-body SHA. A transient unsent editor value from the browser clipboard was discarded before send and was not submitted.

Copilot stated that the bundle only supplied measured source for 4 JSON values, one `WriteCell`, one readback rectangle, and four comparisons. It requested measured or completed Robin source for the requested 7 JSON slots, five writes, two readback rectangles, twelve comparisons, and the C01-C12 connection. It explicitly declined to output a Robin code block.

This was a fixed stop condition. No Copilot resend, generated-code edit, PAD save/re-copy, PAD/Excel run, next candidate, or GitHub write occurred. The response was preserved in `copilot-response.txt`. All 20 protected files retained their preflight SHA-256 values. The runtime work copy remained identical to the template, the output remained absent, and all eight JSON handoff files remained absent.

Formal r12 remains `FAIL`. The earlier T2 fixed-helper auxiliary result remains `PASS` only in its original auxiliary scope and was not inherited by A2-G1. A1 remains a separate refusal record and was not reused as the A2 result.
