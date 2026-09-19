#!/usr/bin/env python3
"""Classify the EX03 r8 G1 square-bracket escape failure without repairing it.

The fixed request, expected values, independent r8 PAD source, actual Copilot
generation, and PAD save/re-copy are immutable inputs.  This analysis derives
the expected fixed adaptation in memory only, proves the minimal textual
transform that explains the failure, and writes a bounded audit.  It does not
send to Copilot, modify a Robin, or execute PAD.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
R8 = ROOT / "copilot/versions/20260916-excel-r8"
CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r8-G1"
DEFAULT_OUTPUT = ROOT / "catalog/acceptance/issue38/probes/ex03-r9-escape-fidelity"

INPUTS = {
    "r8_manifest": R8 / "manifest.json",
    "r8_instruction": R8 / "agent-instructions.txt",
    "r8_bundle": R8 / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "r8_teaching_robin": R8 / "support/EX03-R8-Independent-PAD-Recopy.robin",
    "generated": CYCLE / "generated.robin",
    "pad_recopy": CYCLE / "pad-recopy-before-run1.robin",
    "pad_recopy_diff": CYCLE / "pad-recopy-diff.json",
    "generation_result": CYCLE / "generation-result.json",
    "pad_import": CYCLE / "pad-import-and-recopy.json",
    "acceptance_status": CYCLE / "acceptance-status.json",
    "fixed_request": ROOT / "catalog/acceptance/issue38/requests/EX03.txt",
    "fixed_spec": ROOT / "catalog/acceptance/issue38/spec.json",
    "grader_expected": ROOT / "catalog/acceptance/issue38/expected.json",
}

EXPECTED_HASHES = {
    "r8_manifest": "9025c8869b84d27e4f39512ce157a114a5231041e641ae12ef36c061eae29d3e",
    "r8_instruction": "57f0cdb656e919f8fd83252a6adcd4d12788dac9bf6833db2f2e942eada23bcb",
    "r8_bundle": "164c99e59204efd863f4fe283e8f84ce2902ee760ab90e45cf7c5336631aaddb",
    "r8_teaching_robin": "6d9c23eabfacbcd65b1a18eabf5681805494e41171f94a9b01a28b24452815bb",
    "generated": "711bd5b3a5eb1cba48f6872cd5aa8f718ab3534de4d0e069d5fd1eb7b9d1ed89",
    "pad_recopy": "3340cd988d6ed76dc249edc833be33869c530d0b37ddf223807ac86eaef9329f",
    "pad_recopy_diff": "a0e81e09e8d2cf57bdeac50be9151ae736877d8c413c87667737f089e8d93dd0",
    "generation_result": "69129ae79bf2f6c67f21afac7f008bfc5240b2148e2d6fcf7eac7445acffa760",
    "pad_import": "6449f83d403e0a7a77a0ad518f29cd59609a1a7ba3300e630766a5b2df08e24f",
    "acceptance_status": "2f9a7dea1319496ff955bd19cf116fde67f90822021e20eca1c1016a6076a53d",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "grader_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
}

TEACHING_SCOPE = "independent teaching text mapping"
FIXED_SCOPE = "fixed EX03 text mapping"
TEACHING_TYPE = "Teaching text source"
FIXED_TYPE = "Fixed text source"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_exact(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def normalize(value: str) -> str:
    return value.replace("\r\n", "\n")


def relative(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def load_r8_source_module():
    path = ROOT / "tools/Prepare-Issue38Ex03R8IndependentSource.py"
    spec = importlib.util.spec_from_file_location("issue38_r8_source", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_fixed_from_independent(teaching: str, replacements) -> tuple[str, list[dict]]:
    expected = teaching
    applied = []
    for fixed, independent, label in reversed(replacements):
        count = expected.count(independent)
        if count < 1:
            raise ValueError(f"Independent data slot is missing: {label}")
        expected = expected.replace(independent, fixed)
        applied.append({"label": label, "count": count})
    return expected, applied


def line_differences(before: str, after: str) -> list[dict]:
    before_lines = before.rstrip("\n").split("\n")
    after_lines = after.rstrip("\n").split("\n")
    if len(before_lines) != len(after_lines):
        raise ValueError(
            f"Line counts differ: expected {len(before_lines)}, actual {len(after_lines)}"
        )
    return [
        {"line": index + 1, "expected": left, "actual": right}
        for index, (left, right) in enumerate(zip(before_lines, after_lines))
        if left != right
    ]


def write_new(path: Path, text: str) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite: {path}")
    path.write_text(text, encoding="utf-8", newline="\n")


def analyze(output: Path = DEFAULT_OUTPUT) -> dict:
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Audit directory already exists: {output}")

    actual_hashes = {name: sha256(path) for name, path in INPUTS.items()}
    if actual_hashes != EXPECTED_HASHES:
        raise ValueError(f"Protected input hash mismatch: {actual_hashes}")

    source_module = load_r8_source_module()
    teaching = normalize(read_exact(INPUTS["r8_teaching_robin"]))
    generated = normalize(read_exact(INPUTS["generated"]))
    pad_recopy = normalize(read_exact(INPUTS["pad_recopy"]))
    expected, replacement_counts = expected_fixed_from_independent(
        teaching, source_module.REPLACEMENTS
    )

    expected_diffs = line_differences(expected, generated)
    generated_to_pad = line_differences(generated, pad_recopy)
    if len(expected_diffs) != 31:
        raise ValueError(f"Expected 31 generated differences, found {len(expected_diffs)}")
    if len(generated_to_pad) != 30:
        raise ValueError(f"Expected 30 PAD re-copy differences, found {len(generated_to_pad)}")

    escaped_open = generated.count(r"\[")
    escaped_close = generated.count(r"\]")
    if (escaped_open, escaped_close) != (53, 53):
        raise ValueError(
            f"Unexpected generated bracket escape counts: {escaped_open}/{escaped_close}"
        )
    if teaching.count(r"\[") or teaching.count(r"\]"):
        raise ValueError("Authoritative independent teaching Robin has bracket backslashes")

    diagnostic_normalization = (
        generated.replace(r"\[", "[")
        .replace(r"\]", "]")
        .replace(TEACHING_SCOPE, FIXED_SCOPE)
        .replace(TEACHING_TYPE, FIXED_TYPE)
    )
    if diagnostic_normalization != expected:
        raise ValueError("Bounded diagnostic normalization does not explain the generation")

    recorded_diff = json.loads(INPUTS["pad_recopy_diff"].read_bytes())
    if recorded_diff["differing_line_count"] != len(generated_to_pad):
        raise ValueError("Recorded PAD diff count changed")
    for difference in generated_to_pad:
        doubled = difference["expected"].replace(r"\[", r"\\[").replace(
            r"\]", r"\\]"
        )
        if difference["actual"] != doubled:
            raise ValueError(
                f"PAD difference is not bracket-backslash doubling: {difference['line']}"
            )

    generation = json.loads(INPUTS["generation_result"].read_bytes())
    pad = json.loads(INPUTS["pad_import"].read_bytes())
    acceptance = json.loads(INPUTS["acceptance_status"].read_bytes())
    if generation["generation_requests_used"] != 1:
        raise ValueError("Generation request evidence changed")
    if generation["rendered_response"]["refusal"]:
        raise ValueError("r8 G1 unexpectedly records a refusal")
    if pad["import"]["execution_requested"] or acceptance["runs"]["pad_runs_used"]:
        raise ValueError("The stopped cycle now records a PAD execution")

    analysis = {
        "schema_version": 1,
        "probe_id": "EX03-R9-ESCAPE-FIDELITY",
        "purpose": "Determine the exact r8 G1 generation/PAD re-copy mismatch without repairing or executing it",
        "inputs": {
            name: {"path": relative(path), "sha256": actual_hashes[name]}
            for name, path in INPUTS.items()
        },
        "expected_derivation": {
            "source": relative(INPUTS["r8_teaching_robin"]),
            "method": "reverse only the recorded r8 independent data-slot substitutions in memory",
            "written_as_complete_robin": False,
            "replacement_counts": replacement_counts,
            "line_count": 197,
        },
        "generation_comparison": {
            "expected_vs_generated_differing_lines": len(expected_diffs),
            "differing_line_numbers": [item["line"] for item in expected_diffs],
            "generated_backslash_open_bracket_count": escaped_open,
            "generated_backslash_close_bracket_count": escaped_close,
            "authoritative_teaching_backslash_open_bracket_count": teaching.count(r"\["),
            "authoritative_teaching_backslash_close_bracket_count": teaching.count(r"\]"),
            "stale_teaching_scope_label_count": generated.count(TEACHING_SCOPE),
            "stale_teaching_type_label_count": generated.count(TEACHING_TYPE),
            "bounded_diagnostic_normalization_equals_expected": True,
            "diagnostic_normalization_applied_to_evidence": False,
        },
        "pad_comparison": {
            "generated_vs_pad_recopy_differing_lines": len(generated_to_pad),
            "differing_line_numbers": [item["line"] for item in generated_to_pad],
            "all_differences_are_bracket_backslash_doubling": True,
            "designer_action_count": pad["import"]["designer_action_count"],
            "designer_variable_count": pad["import"]["designer_variable_count"],
            "saved": pad["import"]["saved"],
            "pad_runs": acceptance["runs"]["pad_runs_used"],
        },
        "classification": {
            "confirmed": "The normal-M365 generated code introduced literal backslashes before PowerShell square brackets and retained two teaching-only error labels. PAD did not originate those backslashes; its save/re-copy doubled them to preserve the literal characters.",
            "not_claimed": "The model's hidden internal reason for adding the characters is not known.",
            "runtime_effect": "NOT_EXECUTED_BY_FIXED_STOP_RULE",
            "manual_repair": False,
        },
        "minimum_successor_change": {
            "fixed_request_or_expected_change": False,
            "teaching_robin_change": False,
            "instruction_and_bundle_contract": [
                "PowerShell square brackets inside the text code block must remain raw [ and ] characters",
                "backslash-open-bracket and backslash-close-bracket counts must both be zero before output",
                "teaching-only labels must be replaced consistently with the request data slots",
                "if any check fails, return no Robin instead of emitting a repairable candidate",
            ],
            "new_pad_capture_required": False,
            "reason_no_new_capture": "The authoritative bracket-only independent teaching Robin is unchanged and already has exact PAD paste/save/re-copy evidence.",
        },
        "scope": {
            "copilot_send": 0,
            "pad_import": 0,
            "pad_run": 0,
            "github_write": 0,
            "legacy_558_failure_preserved": True,
            "existing_output_guard_live_path": "REMAINS_UNCONFIRMED",
        },
        "decision": "PASS_ROOT_CAUSE_BOUNDARY_READY_FOR_UNSENT_SUCCESSOR",
    }

    report = f"""# EX03 r8 G1 escape-fidelity analysis

## Conclusion

The failure boundary is fixed between the authoritative r8 teaching source and the normal-M365 generated Robin. The teaching Robin contains zero `\\[` and zero `\\]`; the generated Robin contains {escaped_open} and {escaped_close}. PAD parsed the generated text as 110 actions and 45 variables, then re-copied 30 affected RunScript lines with each bracket backslash doubled. PAD therefore preserved a literal generated character; it did not introduce the first backslash.

The generated flow also retained one teaching-only scope label and one teaching-only type label. Reversing only the recorded independent data slots in memory produces a 197-line expected fixed adaptation. Removing the generated bracket backslashes and replacing those two stale labels explains that expected text exactly. This normalization is diagnostic only and was not written back to, pasted over, or executed as the generated evidence.

The model's hidden reason for introducing the characters remains unknown. Runtime impact was not tested because the fixed mismatch stop rule fired before Run1.

## Minimum successor change

- Keep the fixed request, grader expectations, independent teaching Robin, and its PAD capture unchanged.
- State that PowerShell square brackets inside the `text` code block are raw characters and must never be prefixed with a backslash.
- Require zero `\\[` and zero `\\]` in the candidate before output.
- Require teaching-only labels to be replaced with the request data slots.
- If any check fails, output no Robin; do not emit a candidate for later manual repair.

No Copilot send, PAD import/run, fixed-condition change, or GitHub write was performed by this audit.
"""

    output.mkdir(parents=True, exist_ok=False)
    write_new(
        output / "analysis.json",
        json.dumps(analysis, ensure_ascii=False, indent=2) + "\n",
    )
    write_new(output / "report.md", report)
    return {
        "output": relative(output),
        "analysis_sha256": sha256(output / "analysis.json"),
        "report_sha256": sha256(output / "report.md"),
        "decision": analysis["decision"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    print(json.dumps(analyze(parser.parse_args().output), ensure_ascii=False, indent=2))
