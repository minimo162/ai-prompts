#!/usr/bin/env python3
"""Audit the one live EX03 r10 Copilot generation without executing it."""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r10-G1"
R10 = ROOT / "copilot/versions/20260917-excel-r10"
OUTPUT = CYCLE / "generation-safety-audit.json"

RAW_BASE64 = CYCLE / "generated-robin.clipboard.utf8.b64"
RESPONSE_BASE64 = CYCLE / "copilot-response.clipboard.utf8.b64"
GENERATED = CYCLE / "generated.robin"
TEACHING = R10 / "support/EX03-R10-Independent-PAD-Recopy.robin"
TEACHING_SCRIPT = R10 / "support/EX03-R10-Independent-FormatSandwich.ps1.txt"
SOURCE_TOOL = ROOT / "tools/Prepare-Issue38Ex03R8IndependentSource.py"

SELF_REPORTED_SHA256 = (
    "e14b1ae8dd2652eccc6d0537705c01de977f4657536c338580c8b681e020356c"
)

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

LABEL_REPLACEMENTS = {
    "error_scope": "EX03 text mapping",
    "error_type": "EX03 text source",
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def relative(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def normalized(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip("\n")


def load_source_module():
    spec = importlib.util.spec_from_file_location("issue38_r10_source", SOURCE_TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_fixed_from_independent(
    teaching: str, replacements: list[tuple[str, str, str]]
) -> str:
    expected = teaching
    for fixed, independent, label in reversed(replacements):
        replacement = LABEL_REPLACEMENTS.get(label, fixed)
        if expected.count(independent) < 1:
            raise ValueError(f"Independent data slot is missing: {label}")
        expected = expected.replace(independent, replacement)
    return expected


def line_differences(before: str, after: str) -> list[dict[str, object]]:
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


def parse_powershell(source: str) -> list[dict[str, object]]:
    encoded = base64.b64encode(source.encode("utf-8")).decode("ascii")
    command = f"""
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$source = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded}'))
$tokens = $null
$errors = $null
[System.Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$errors) | Out-Null
$result = @($errors | ForEach-Object {{
    [ordered]@{{
        error_id = $_.ErrorId
        message = $_.Message
        line = $_.Extent.StartLineNumber
        column = $_.Extent.StartColumnNumber
        token = $_.Extent.Text
    }}
}})
ConvertTo-Json -InputObject $result -Depth 5 -Compress
"""
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    value = json.loads(completed.stdout.strip() or "[]")
    return value if isinstance(value, list) else [value]


def audit(output: Path = OUTPUT) -> dict[str, object]:
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite: {output}")

    source_module = load_source_module()
    raw_base64 = RAW_BASE64.read_text(encoding="ascii")
    raw = base64.b64decode(raw_base64)
    response_raw = base64.b64decode(RESPONSE_BASE64.read_text(encoding="ascii"))
    response_text = response_raw.decode("utf-8")
    generated_bytes = GENERATED.read_bytes()
    if raw != generated_bytes:
        raise ValueError("Repository generated Robin differs from the raw code-copy payload")
    if b"\r" in raw:
        raise ValueError("The r10 raw code-copy payload is not LF-only as observed")

    generated = normalized(raw.decode("utf-8"))
    if generated not in response_text:
        raise ValueError("The copied full response does not contain the exact code-copy payload")
    if SELF_REPORTED_SHA256 not in response_text:
        raise ValueError("The copied full response is missing the reported generated SHA")
    teaching = normalized(TEACHING.read_text(encoding="utf-8"))
    expected = expected_fixed_from_independent(teaching, source_module.REPLACEMENTS)
    differences = line_differences(expected, generated)
    if [record["line"] for record in differences] != [50, 90]:
        raise ValueError(f"Unexpected r10 structural difference set: {differences}")

    token_inventory = {
        token: {
            "expected_count": expected_count,
            "teaching_count": teaching.count(token),
            "generated_count": generated.count(token),
            "matches_expected": generated.count(token) == expected_count,
        }
        for token, expected_count in TOKEN_COUNTS.items()
    }
    if any(
        record["teaching_count"] != record["expected_count"]
        for record in token_inventory.values()
    ):
        raise ValueError("The r10 independent teaching token inventory changed")

    required_inventory = [
        {
            "fragment": fragment,
            "expected_count": 1,
            "teaching_count": teaching.count(fragment),
            "generated_count": generated.count(fragment),
        }
        for fragment in REQUIRED_INVARIANT_FRAGMENTS
    ]
    forbidden_inventory = [
        {
            "fragment": fragment,
            "expected_count": 0,
            "teaching_count": teaching.count(fragment),
            "generated_count": generated.count(fragment),
        }
        for fragment in FORBIDDEN_CORRUPTION_FRAGMENTS
    ]
    if any(record["teaching_count"] != 1 for record in required_inventory):
        raise ValueError("A required invariant changed in the teaching source")
    if any(record["teaching_count"] != 0 for record in forbidden_inventory):
        raise ValueError("A forbidden corruption exists in the teaching source")

    action = source_module.extract_action(generated)
    embedded_script = source_module.decode_robin_string(
        source_module.action_payload(action)
    )
    generated_errors = parse_powershell(embedded_script)
    teaching_errors = parse_powershell(TEACHING_SCRIPT.read_text(encoding="utf-8"))
    if not generated_errors:
        raise ValueError("The visibly corrupt generated script unexpectedly parsed cleanly")
    if teaching_errors:
        raise ValueError(f"The independent teaching script no longer parses: {teaching_errors}")

    raw_sha256 = sha256_bytes(raw)
    generated_lines = generated.split("\n")
    result = {
        "schema_version": 1,
        "cycle_id": "EX03-R10-G1",
        "recorded_at": datetime.now().astimezone().isoformat(),
        "version": "20260917-excel-r10",
        "inputs": {
            "raw_code_copy_base64": {
                "path": relative(RAW_BASE64),
                "file_sha256": sha256(RAW_BASE64),
                "decoded_sha256": raw_sha256,
            },
            "raw_response_copy_base64": {
                "path": relative(RESPONSE_BASE64),
                "file_sha256": sha256(RESPONSE_BASE64),
                "decoded_sha256": sha256_bytes(response_raw),
            },
            "generated_robin": {
                "path": relative(GENERATED),
                "sha256": sha256(GENERATED),
            },
            "teaching_robin": {
                "path": relative(TEACHING),
                "sha256": sha256(TEACHING),
            },
            "teaching_script": {
                "path": relative(TEACHING_SCRIPT),
                "sha256": sha256(TEACHING_SCRIPT),
            },
        },
        "capture": {
            "utf8_bytes": len(raw),
            "utf16_units": len(generated.encode("utf-16-le")) // 2,
            "line_count": len(generated_lines),
            "line_ending": "LF",
            "final_newline": raw.endswith(b"\n"),
            "first_line": generated_lines[0],
            "last_line": generated_lines[-1],
            "markdown_fence_count": generated.count("```"),
            "nbsp_count": generated.count("\u00a0"),
            "ellipsis_count": generated.count("..."),
            "generated_text_edited": False,
        },
        "comparison": {
            "method": (
                "derive the fixed EX03 candidate from the byte-preserved independent "
                "teaching Robin by reversing only the recorded data-slot substitutions "
                "and applying the two fixed error labels"
            ),
            "expected_line_count": len(expected.split("\n")),
            "generated_line_count": len(generated_lines),
            "differing_content_line_count": len(differences),
            "differing_lines": differences,
            "manual_repair_applied": False,
            "fixed_request_or_expected_changed": False,
        },
        "fidelity": {
            "token_inventory": token_inventory,
            "required_invariant_fragments": required_inventory,
            "forbidden_corruption_fragments": forbidden_inventory,
            "backslash_escaped_open_bracket_count": generated.count(r"\["),
            "backslash_escaped_close_bracket_count": generated.count(r"\]"),
            "adapted_error_label_counts": {
                "EX03 text mapping": generated.count("EX03 text mapping"),
                "EX03 text source": generated.count("EX03 text source"),
            },
            "self_reported_sha256": SELF_REPORTED_SHA256,
            "self_reported_sha256_matches_code_copy": (
                SELF_REPORTED_SHA256 == raw_sha256
            ),
            "full_structural_fidelity_satisfied": False,
            "response_claim_of_fidelity_pass_accepted": False,
        },
        "response_boundary": {
            "response_copy_utf8_bytes": len(response_raw),
            "response_copy_utf16_units": len(response_text.encode("utf-16-le")) // 2,
            "response_copy_line_count": len(response_text.split("\n")),
            "response_copy_line_ending": "LF",
            "response_copy_final_newline": response_raw.endswith(b"\n"),
            "response_copy_contains_exact_code_copy": True,
            "response_copy_contains_self_reported_sha256": True,
            "code_copy_sha256": raw_sha256,
            "self_reported_sha256": SELF_REPORTED_SHA256,
            "sha256_match": SELF_REPORTED_SHA256 == raw_sha256,
        },
        "powershell_parser": {
            "method": (
                "extract the embedded script, decode PAD escaped quote/backslash forms, "
                "and parse with the Windows PowerShell AST parser without execution"
            ),
            "generated_embedded_script_error_count": len(generated_errors),
            "generated_embedded_script_errors": generated_errors,
            "independent_teaching_script_error_count": len(teaching_errors),
            "generated_script_executed_by_audit": False,
        },
        "bounded_side_effect_review": {
            "output_exists_guard": "File.IfFile.Exists" in generated,
            "all_excel_actions_inside_else": all(
                match.start() > generated.index("\nELSE\n")
                for match in re.finditer(r"\bExcel\.", generated)
            ),
            "save_as_count": generated.count("Excel.SaveExcel.SaveAs"),
            "write_action_count": generated.count("Excel.WriteToExcel.WriteCell"),
            "run_powershell_script_count": generated.count(
                "Scripting.RunPowershellScript.RunScript"
            ),
            "read_only_true_count": generated.count("ReadOnly: True"),
            "source_json_actions": sum(
                generated.count(f"Json=> TextSource{index}Json")
                for index in range(1, 8)
            ),
            "saved_json_actions": generated.count("Json=> SavedCellJson"),
            "value_type_match_variables": generated.count("_ValueTypeMatch TO"),
            "delete_or_remove_action_count": sum(
                generated.count(value)
                for value in ("File.Delete", "Folder.Delete", "Remove-Item")
            ),
            "network_or_web_automation_action_count": sum(
                generated.count(value)
                for value in ("WebAutomation.", "HTTP.", "Invoke-WebRequest")
            ),
            "bounded_side_effects_do_not_override_parse_failure": True,
        },
        "scope": {
            "verified_types": [],
            "not_generalized_to": [
                "text",
                "number",
                "blank",
                "boolean",
                "date",
                "error",
                "formula-result",
                "object",
                "other PAD versions or PCs",
            ],
            "probe_success_used_as_generated_flow_success": False,
            "external_checker_used_as_generated_flow_success": False,
        },
        "decision": {
            "status": "FAIL_R10_STRUCTURAL_FIDELITY_STOP_BEFORE_PAD",
            "pad_import_authorized": False,
            "runtime_authorized": False,
            "recopy_required_but_not_reached": True,
            "reason": (
                "The unmodified code-copy payload is missing the required type qualifiers "
                "on lines 50 and 90, contains two forbidden corruption fragments, fails "
                "PowerShell parsing, and does not match the response-reported SHA. The "
                "fixed stop rule prohibits PAD paste, save, re-copy, or Run1."
            ),
            "resend_allowed": False,
        },
    }

    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    result = audit(parser.parse_args().output)
    print(
        json.dumps(
            {
                "status": result["decision"]["status"],
                "generated_sha256": result["inputs"]["generated_robin"]["sha256"],
                "differing_lines": [
                    record["line"] for record in result["comparison"]["differing_lines"]
                ],
                "parser_errors": result["powershell_parser"][
                    "generated_embedded_script_error_count"
                ],
            },
            ensure_ascii=False,
        )
    )
