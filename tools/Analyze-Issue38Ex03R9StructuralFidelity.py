#!/usr/bin/env python3
"""Classify the EX03 r9 structural-fidelity failure without repairing it.

The r9 package, live Copilot response, raw clipboard capture, and fixed EX03
inputs are immutable inputs.  This analysis derives the exact fixed adaptation
in memory only and proves whether the corruption is in the response DOM or a
later copy/PAD layer.  It sends nothing and does not create or run a PAD flow.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
R9 = ROOT / "copilot/versions/20260917-excel-r9"
CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r9-G1"
DEFAULT_OUTPUT = (
    ROOT / "catalog/acceptance/issue38/probes/ex03-r10-structural-fidelity"
)
DOM_CONFIRMATION = DEFAULT_OUTPUT / "r9-dom-code-confirmation.json"

INPUTS = {
    "r9_manifest": R9 / "manifest.json",
    "r9_instruction": R9 / "agent-instructions.txt",
    "r9_bundle": R9 / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "r9_teaching_robin": R9 / "support/EX03-R9-Independent-PAD-Recopy.robin",
    "r9_teaching_script": R9 / "support/EX03-R9-Independent-FormatSandwich.ps1.txt",
    "r8_source_tool": ROOT / "tools/Prepare-Issue38Ex03R8IndependentSource.py",
    "raw_clipboard_base64": CYCLE / "generated-robin.clipboard.utf8.b64",
    "generated": CYCLE / "generated.robin",
    "live_send": CYCLE / "live-send.json",
    "generation_result": CYCLE / "generation-result.json",
    "safety_audit": CYCLE / "generation-safety-audit.json",
    "acceptance_status": CYCLE / "acceptance-status.json",
    "dom_confirmation": DOM_CONFIRMATION,
    "fixed_request": ROOT / "catalog/acceptance/issue38/requests/EX03.txt",
    "fixed_spec": ROOT / "catalog/acceptance/issue38/spec.json",
    "grader_expected": ROOT / "catalog/acceptance/issue38/expected.json",
}

EXPECTED_HASHES = {
    "r9_manifest": "1b64005c85aee3215160c9381d956a64531863b5d838d9091009fded5007f540",
    "r9_instruction": "a699dd910a4b0529fc71c9b8045b845bf49b8a407df9da88027a0ca0ab0f51fa",
    "r9_bundle": "b402a6c78fb39cb68dd4111590122b9f9be3364609358fd58a9ad3880d29b993",
    "r9_teaching_robin": "6d9c23eabfacbcd65b1a18eabf5681805494e41171f94a9b01a28b24452815bb",
    "r9_teaching_script": "65b86b0e5be4ec2da30e57a6bd858e395d1103da2d05ab2e7607362772d1dfd9",
    "r8_source_tool": "9c8f2cab7e154e38351251327c4f31fe6b53ff0fc5665c8bc8f6504c14545746",
    "raw_clipboard_base64": "42a03537c81e2300834a240932fde5a1de4bde23cf0bdcdf4bb611fbf773d894",
    "generated": "7a02ea0d073adde698578b8fa578f5701c728114ee55fbf20aa0ecdaaa32cb14",
    "live_send": "9d096d6c84bdcf056d838c7b813249494426aec7e380c15a29cfdb89b236e7f2",
    "generation_result": "2051065a60419e7c6f2c7ec0ef36302f3364489f114874f277f48b299f03914e",
    "safety_audit": "375e225bcd494e9204a31a633b719dd6915e4d4d4ad01be89ee44cf05c1fa8c1",
    "acceptance_status": "d3677a6e026e1a20b5cf109795a848036568182014c0f87bc4e0c119dd373d9b",
    "dom_confirmation": "a78e4cf2f309b733ae8e9c6d6c268de16206ca8df17d2863d07f512cbcefb34f",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "grader_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
}

RAW_CLIPBOARD_SHA256 = (
    "dce9d6f01de53252050b53de46283563f56226b1635a2ccdcbd71d2dfd2636bf"
)

LABEL_REPLACEMENTS = {
    "error_scope": "EX03 text mapping",
    "error_type": "EX03 text source",
}

TOKEN_COUNTS = {
    "[ordered]": 8,
    "[string]": 14,
    "[bool]": 2,
    "[void]": 5,
    "[Runtime.InteropServices.Marshal]": 6,
    "[IO.Path]": 1,
    "[StringComparison]": 1,
    "::GetFullPath(": 1,
    "::OrdinalIgnoreCase": 1,
    "::IsNullOrEmpty(": 1,
    "$matches[0]": 1,
    "$allowedTargets[$sheetName]": 1,
}

REQUIRED_INVARIANT_FRAGMENTS = [
    (
        "[string]::Equals([IO.Path]::GetFullPath([string]$candidate.FullName), "
        "$targetPath, [StringComparison]::OrdinalIgnoreCase)"
    ),
    "[string]::IsNullOrEmpty($afterPrefixCharacter)",
]

FORBIDDEN_CORRUPTION_FRAGMENTS = [
    "[IO.Path]::GetFulling]",
    ", :OrdinalIgnoreCase",
    "-not :IsNullOrEmpty(",
]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def normalized(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip("\n")


def relative(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def load_source_module():
    path = INPUTS["r8_source_tool"]
    spec = importlib.util.spec_from_file_location("issue38_r8_source_r10", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_fixed_from_independent(teaching: str, replacements) -> tuple[str, list[dict]]:
    expected = teaching
    applied = []
    for fixed, independent, label in reversed(replacements):
        replacement = LABEL_REPLACEMENTS.get(label, fixed)
        count = expected.count(independent)
        if count < 1:
            raise ValueError(f"Independent data slot is missing: {label}")
        expected = expected.replace(independent, replacement)
        applied.append(
            {
                "label": label,
                "source_count": count,
                "replacement_kind": (
                    "fixed-request data" if label not in LABEL_REPLACEMENTS else "fixed error label"
                ),
            }
        )
    return expected, applied


def line_differences(before: str, after: str) -> list[dict]:
    before_lines = before.split("\n")
    after_lines = after.split("\n")
    if len(before_lines) != len(after_lines):
        raise ValueError(
            f"Line counts differ: expected {len(before_lines)}, actual {len(after_lines)}"
        )
    return [
        {"line": index + 1, "expected": left, "actual": right}
        for index, (left, right) in enumerate(zip(before_lines, after_lines))
        if left != right
    ]


def write_new(path: Path, value: str) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite: {path}")
    path.write_text(value, encoding="utf-8", newline="\n")


def analyze(output: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    output = Path(output)
    analysis_path = output / "analysis.json"
    report_path = output / "report.md"
    if analysis_path.exists() or report_path.exists():
        raise FileExistsError(f"Structural audit output already exists: {output}")

    actual_hashes = {name: sha256(path) for name, path in INPUTS.items()}
    if actual_hashes != EXPECTED_HASHES:
        raise ValueError(f"Protected r9/fixed input hash mismatch: {actual_hashes}")

    source_module = load_source_module()
    teaching = normalized(INPUTS["r9_teaching_robin"].read_text(encoding="utf-8"))
    generated = normalized(INPUTS["generated"].read_text(encoding="utf-8"))
    expected, replacement_counts = expected_fixed_from_independent(
        teaching, source_module.REPLACEMENTS
    )
    differences = line_differences(expected, generated)
    if [item["line"] for item in differences] != [50, 90]:
        raise ValueError(f"Unexpected r9 structural difference set: {differences}")

    raw_base64 = INPUTS["raw_clipboard_base64"].read_text(encoding="ascii")
    raw = base64.b64decode(raw_base64)
    if sha256_bytes(raw) != RAW_CLIPBOARD_SHA256:
        raise ValueError("Decoded raw clipboard hash changed")
    if raw.decode("utf-8").replace("\r\n", "\n") != generated:
        raise ValueError("Repository generated Robin is not the normalized raw clipboard")

    live_send = json.loads(INPUTS["live_send"].read_bytes())
    generation = json.loads(INPUTS["generation_result"].read_bytes())
    safety = json.loads(INPUTS["safety_audit"].read_bytes())
    acceptance = json.loads(INPUTS["acceptance_status"].read_bytes())
    dom = json.loads(INPUTS["dom_confirmation"].read_bytes())
    if live_send["actions"]["normal_m365_send"] != 1:
        raise ValueError("r9 one-send evidence changed")
    if live_send["actions"]["resend"] != 0:
        raise ValueError("r9 now records a resend")
    if generation["rendered_response"]["refusal"]:
        raise ValueError("r9 unexpectedly records a refusal")
    if acceptance["runs"]["pad_runs_used"] != 0:
        raise ValueError("Stopped r9 cycle now records a PAD run")
    if safety["decision"]["status"] != (
        "FAIL_GENERATED_ROBIN_SYNTAX_CORRUPTION_STOP_BEFORE_PAD"
    ):
        raise ValueError("r9 safety decision changed")
    if dom["code_dom"]["sha256"] != RAW_CLIPBOARD_SHA256:
        raise ValueError("DOM confirmation no longer matches the raw clipboard")
    if not dom["code_dom"]["matches_preserved_windows_clipboard_utf8"]:
        raise ValueError("DOM/clipboard equality is not confirmed")

    token_inventory = {
        token: {
            "expected_count": count,
            "teaching_count": teaching.count(token),
            "generated_count": generated.count(token),
            "matches_expected": generated.count(token) == count,
        }
        for token, count in TOKEN_COUNTS.items()
    }
    if any(record["teaching_count"] != record["expected_count"] for record in token_inventory.values()):
        raise ValueError(f"Independent source token counts changed: {token_inventory}")
    mismatched_tokens = [
        token for token, record in token_inventory.items() if not record["matches_expected"]
    ]
    if mismatched_tokens != [
        "[string]",
        "[StringComparison]",
        "::GetFullPath(",
        "::OrdinalIgnoreCase",
        "::IsNullOrEmpty(",
    ]:
        raise ValueError(f"Unexpected r9 token mismatch set: {mismatched_tokens}")

    fragment_inventory = {
        "required": [
            {
                "fragment": fragment,
                "teaching_count": teaching.count(fragment),
                "generated_count": generated.count(fragment),
            }
            for fragment in REQUIRED_INVARIANT_FRAGMENTS
        ],
        "forbidden": [
            {
                "fragment": fragment,
                "teaching_count": teaching.count(fragment),
                "generated_count": generated.count(fragment),
            }
            for fragment in FORBIDDEN_CORRUPTION_FRAGMENTS
        ],
    }
    if any(item["teaching_count"] != 1 for item in fragment_inventory["required"]):
        raise ValueError("Required invariant fragment changed in the teaching source")
    if any(item["generated_count"] != 0 for item in fragment_inventory["required"]):
        raise ValueError("r9 unexpectedly preserved a required invariant fragment")
    if any(item["teaching_count"] != 0 for item in fragment_inventory["forbidden"]):
        raise ValueError("Forbidden corruption fragment exists in the teaching source")
    if any(item["generated_count"] != 1 for item in fragment_inventory["forbidden"]):
        raise ValueError("Unexpected forbidden-fragment counts in r9")

    analysis = {
        "schema_version": 1,
        "probe_id": "EX03-R10-STRUCTURAL-FIDELITY",
        "purpose": (
            "Prove the r9 structural corruption boundary and define the minimal "
            "unsent successor gate without repairing or executing the generated Robin"
        ),
        "inputs": {
            name: {"path": relative(path), "sha256": actual_hashes[name]}
            for name, path in INPUTS.items()
        },
        "expected_derivation": {
            "source": relative(INPUTS["r9_teaching_robin"]),
            "method": (
                "reverse only the recorded independent data-slot substitutions in memory; "
                "use exact EX03 error labels"
            ),
            "written_as_complete_robin": False,
            "replacement_counts": replacement_counts,
            "line_count": len(expected.split("\n")),
        },
        "r9_comparison": {
            "expected_vs_generated_differing_line_count": len(differences),
            "differing_lines": differences,
            "backslash_open_bracket_count": generated.count(r"\["),
            "backslash_close_bracket_count": generated.count(r"\]"),
            "token_inventory": token_inventory,
            "fragment_inventory": fragment_inventory,
        },
        "response_boundary": {
            "dom_line_count": dom["code_dom"]["line_node_count"],
            "dom_utf8_bytes": dom["code_dom"]["utf8_bytes"],
            "dom_sha256": dom["code_dom"]["sha256"],
            "raw_clipboard_sha256": sha256_bytes(raw),
            "dom_equals_raw_clipboard": True,
            "copy_or_pad_introduced_the_two_corruptions": False,
            "hidden_model_or_service_cause": "UNKNOWN_NOT_CLAIMED",
        },
        "classification": {
            "confirmed": (
                "The exact requested adaptation differs only at Robin lines 50 and 90. "
                "Both defects already exist in the rendered code DOM, whose full CRLF "
                "serialization exactly matches the preserved system clipboard payload."
            ),
            "r9_gate_limit": (
                "The zero bracket-backslash gate passed but did not verify required type/member "
                "tokens or the two invariant PowerShell expressions."
            ),
            "runtime_effect": "NOT_EXECUTED_BY_FIXED_STOP_RULE",
            "manual_repair": False,
        },
        "minimum_successor_change": {
            "fixed_request_or_expected_change": False,
            "teaching_robin_change": False,
            "embedded_script_change": False,
            "new_pad_capture_required": False,
            "instruction_and_bundle_contract": [
                "retain the r9 zero bracket-backslash gate",
                "require the source-derived structural token counts exactly",
                "require each invariant expression fragment exactly once",
                "forbid the three observed corruption fragments",
                "derive output only by listed data-slot substitution, not paraphrase or rewrite",
                "emit no Robin when any count or fragment gate fails",
            ],
            "reason_no_new_capture": (
                "The independent teaching Robin and embedded script remain byte-identical to "
                "the already PAD paste/save/re-copy verified source."
            ),
        },
        "scope": {
            "copilot_send": 0,
            "copilot_regeneration": 0,
            "pad_import": 0,
            "pad_run": 0,
            "github_write": 0,
            "legacy_558_failure_preserved": True,
            "existing_output_guard_live_path": "REMAINS_UNCONFIRMED",
        },
        "decision": "PASS_R9_STRUCTURAL_FAILURE_BOUNDARY_READY_FOR_UNSENT_R10",
    }

    report = f"""# EX03 r9 structural-fidelity analysis

## Conclusion

The r9 response DOM contains the same {len(differences)} corrupt lines as the preserved raw code-copy payload. Joining all {dom['code_dom']['line_node_count']} rendered code lines with CRLF produces SHA-256 `{RAW_CLIPBOARD_SHA256}`, exactly matching the Windows clipboard capture. The code-copy control, clipboard encoding, LF normalization, and PAD are therefore ruled out as the source of these two corruptions.

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
"""

    output.mkdir(parents=True, exist_ok=True)
    write_new(analysis_path, json.dumps(analysis, ensure_ascii=False, indent=2) + "\n")
    write_new(report_path, report)
    try:
        output_label = relative(output)
    except ValueError:
        output_label = str(output.resolve())
    return {
        "output": output_label,
        "analysis_sha256": sha256(analysis_path),
        "report_sha256": sha256(report_path),
        "decision": analysis["decision"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    print(json.dumps(analyze(parser.parse_args().output), ensure_ascii=False, indent=2))
