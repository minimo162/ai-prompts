# EX03 r8 G1 escape-fidelity analysis

## Conclusion

The failure boundary is fixed between the authoritative r8 teaching source and the normal-M365 generated Robin. The teaching Robin contains zero `\[` and zero `\]`; the generated Robin contains 53 and 53. PAD parsed the generated text as 110 actions and 45 variables, then re-copied 30 affected RunScript lines with each bracket backslash doubled. PAD therefore preserved a literal generated character; it did not introduce the first backslash.

The generated flow also retained one teaching-only scope label and one teaching-only type label. Reversing only the recorded independent data slots in memory produces a 197-line expected fixed adaptation. Removing the generated bracket backslashes and replacing those two stale labels explains that expected text exactly. This normalization is diagnostic only and was not written back to, pasted over, or executed as the generated evidence.

The model's hidden reason for introducing the characters remains unknown. Runtime impact was not tested because the fixed mismatch stop rule fired before Run1.

## Minimum successor change

- Keep the fixed request, grader expectations, independent teaching Robin, and its PAD capture unchanged.
- State that PowerShell square brackets inside the `text` code block are raw characters and must never be prefixed with a backslash.
- Require zero `\[` and zero `\]` in the candidate before output.
- Require teaching-only labels to be replaced with the request data slots.
- If any check fails, output no Robin; do not emit a candidate for later manual repair.

No Copilot send, PAD import/run, fixed-condition change, or GitHub write was performed by this audit.
