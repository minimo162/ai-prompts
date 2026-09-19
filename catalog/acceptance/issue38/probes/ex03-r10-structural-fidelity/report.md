# EX03 r9 structural-fidelity analysis

## Conclusion

The r9 response DOM contains the same 2 corrupt lines as the preserved raw code-copy payload. Joining all 197 rendered code lines with CRLF produces SHA-256 `dce9d6f01de53252050b53de46283563f56226b1635a2ccdcbd71d2dfd2636bf`, exactly matching the Windows clipboard capture. The code-copy control, clipboard encoding, LF normalization, and PAD are therefore ruled out as the source of these two corruptions.

The exact fixed adaptation was derived in memory from the independent PAD-recopied teaching Robin using only the recorded data-slot substitutions and exact EX03 error labels. It differs from the r9 generation only on lines 50 and 90. This expected complete Robin was not written to disk or added to the bundle.

## Missing structural tokens

- `[string]`: expected 14, generated 12
- `[StringComparison]`: expected 1, generated 0
- `::GetFullPath(`: expected 1, generated 0
- `::OrdinalIgnoreCase`: expected 1, generated 0
- `::IsNullOrEmpty(`: expected 1, generated 0

The r9 zero-backslash gate passed, but it could not detect deletion or fusion of required tokens. The hidden model or service cause remains unknown.

## Minimum unsent successor

Keep the fixed request, expectations, independent teaching Robin, embedded script, and prior evidence unchanged. Add a source-derived structural gate with exact token counts, two required invariant fragments, and the three observed forbidden corruption fragments. If any check fails, return no Robin. No new PAD capture is required because no teaching/runtime source changes.

This analysis sent no Copilot message, opened or ran no PAD flow, changed no fixed condition, and made no GitHub write.
