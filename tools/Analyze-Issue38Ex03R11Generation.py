#!/usr/bin/env python3
"""Audit the single live EX03 r11 Copilot generation without executing it.

The Copilot response substituted a downloadable Robin file for the required
single ``text`` code block.  This tool preserves that distinction: it audits
the downloaded bytes as an unmodified generated payload, but it cannot turn a
delivery-contract mismatch into authorization to paste or run the flow.
"""

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
CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r11-G1"
R11 = ROOT / "copilot/versions/20260917-excel-r11"
OUTPUT = CYCLE / "generation-safety-audit.json"

GENERATED = CYCLE / "generated.robin"
RESPONSE = CYCLE / "copilot-response.visible.txt"
RESPONSE_DOM = CYCLE / "response-dom-inspection.json"
TEACHING = R11 / "support/EX03-R11-Independent-PAD-Recopy.robin"
TEACHING_SCRIPT = R11 / "support/EX03-R11-Independent-Minimal-FormatSandwich.ps1.txt"
SOURCE_TOOL = ROOT / "tools/Prepare-Issue38Ex03R8IndependentSource.py"

EXPECTED_GENERATED_SHA256 = (
    "a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875"
)

TOKEN_COUNTS = {
    "[string]": 12,
    "[bool]": 2,
    "[void]": 6,
    "[Runtime.InteropServices.Marshal]": 7,
    "[IO.Path]": 2,
    "::GetFullPath(": 2,
    "-ieq": 1,
    "$matches[0]": 1,
    "$beforeNumberFormat": 3,
}

REQUIRED_INVARIANT_FRAGMENTS = [
    "if ([IO.Path]::GetFullPath([string]$candidate.FullName) -ieq $targetPath) { $matches += $candidate }",
    "$cell.Value2 = [string]$payload.probe",
    "finally { $cell.NumberFormat = $beforeNumberFormat }",
    "$cell.Value2 -isnot [string]",
    "if ([string]$cell.PrefixCharacter -cne \\'\\')",
]

FORBIDDEN_CORRUPTION_FRAGMENTS = [
    "[string]::Equals(",
    "[StringComparison]::OrdinalIgnoreCase",
    "[string]::IsNullOrEmpty(",
    ":Equals([IO.Path]",
    "-not :IsNullOrEmpty(",
    "[IO.Path]::GetFulling]",
]

FORBIDDEN_RUNTIME_FRAGMENTS = [
    "File.Delete",
    "Folder.Delete",
    "WebAutomation.",
    "HTTP.",
    "System.RunDOSCommand",
    "System.RunApplication",
    "Start-Process",
    "Remove-Item",
    "Invoke-WebRequest",
]

LABEL_REPLACEMENTS = {
    "error_scope": "EX03 text mapping",
    "error_type": "EX03 text source",
}

EXPECTED_STRING_TARGETS = {
    ("集計先", "F7", "%TextSource1Json%"),
    ("集計先", "F8", "%TextSource2Json%"),
    ("集計先", "F9", "%TextSource3Json%"),
    ("追記先", "D5", "%TextSource4Json%"),
    ("追記先", "D6", "%TextSource5Json%"),
    ("追記先", "F5", "%TextSource6Json%"),
    ("追記先", "F6", "%TextSource7Json%"),
}

EXPECTED_NUMBER_WRITES = {
    ("NumberSource1", "G", "7"),
    ("NumberSource2", "G", "8"),
    ("NumberSource3", "G", "9"),
    ("NumberSource4", "E", "5"),
    ("NumberSource5", "E", "6"),
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def relative(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def normalized(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip("\n")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_fixed_from_independent(
    teaching: str, replacements: list[tuple[str, str, str]]
) -> str:
    expected = teaching
    optional_absent_labels = {"error_scope"}
    for fixed, independent, label in reversed(replacements):
        count = expected.count(independent)
        if count == 0:
            if label in optional_absent_labels:
                continue
            raise ValueError(f"Independent data slot is missing: {label}")
        replacement = LABEL_REPLACEMENTS.get(label, fixed)
        expected = expected.replace(independent, replacement)
    return expected


def line_differences(before: str, after: str) -> list[dict[str, object]]:
    before_lines = before.split("\n")
    after_lines = after.split("\n")
    count = max(len(before_lines), len(after_lines))
    records: list[dict[str, object]] = []
    for index in range(count):
        expected = before_lines[index] if index < len(before_lines) else None
        actual = after_lines[index] if index < len(after_lines) else None
        if expected != actual:
            records.append({"line": index + 1, "expected": expected, "actual": actual})
    return records


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


def extract_string_targets(script: str) -> set[tuple[str, str, str]]:
    pattern = re.compile(
        r"@\('Data[12]\[\d\]\[\d\]', '([^']+)', '([^']+)', '([^']+)'\)"
    )
    return {tuple(match.groups()) for match in pattern.finditer(script)}


def extract_number_writes(robin: str) -> set[tuple[str, str, str]]:
    pattern = re.compile(
        r"Excel\.WriteToExcel\.WriteCell Instance: Work Value: (NumberSource\d+) "
        r"Column: \$'''([^']+)''' Row: (\d+)"
    )
    return {tuple(match.groups()) for match in pattern.finditer(robin)}


def audit(output: Path | None = OUTPUT) -> dict[str, object]:
    output = Path(output) if output is not None else None
    if output is not None and output.exists():
        raise FileExistsError(f"Refusing to overwrite: {output}")

    source_module = load_module("issue38_r11_source", SOURCE_TOOL)
    raw = GENERATED.read_bytes()
    if sha256_bytes(raw) != EXPECTED_GENERATED_SHA256:
        raise ValueError("Preserved generated Robin differs from the downloaded bytes")
    generated_text = raw.decode("utf-8")
    generated = normalized(generated_text)
    response_text = RESPONSE.read_text(encoding="utf-8")
    response_dom = json.loads(RESPONSE_DOM.read_bytes())
    teaching = normalized(TEACHING.read_text(encoding="utf-8"))
    expected = normalized(
        expected_fixed_from_independent(teaching, source_module.REPLACEMENTS)
    )
    differences = line_differences(expected, generated)

    action = source_module.extract_action(generated)
    embedded_script = source_module.decode_robin_string(
        source_module.action_payload(action)
    )
    generated_errors = parse_powershell(embedded_script)
    teaching_errors = parse_powershell(TEACHING_SCRIPT.read_text(encoding="utf-8"))

    token_inventory = {
        token: {
            "expected_count": expected_count,
            "teaching_count": teaching.count(token),
            "generated_count": generated.count(token),
            "matches_expected": generated.count(token) == expected_count,
        }
        for token, expected_count in TOKEN_COUNTS.items()
    }
    required_inventory = [
        {
            "fragment": fragment,
            "expected_count": 1,
            "teaching_count": teaching.count(fragment),
            "generated_count": generated.count(fragment),
            "matches_expected": generated.count(fragment) == 1,
        }
        for fragment in REQUIRED_INVARIANT_FRAGMENTS
    ]
    forbidden_inventory = [
        {
            "fragment": fragment,
            "expected_count": 0,
            "teaching_count": teaching.count(fragment),
            "generated_count": generated.count(fragment),
            "matches_expected": generated.count(fragment) == 0,
        }
        for fragment in FORBIDDEN_CORRUPTION_FRAGMENTS
    ]

    string_targets = extract_string_targets(embedded_script)
    number_writes = extract_number_writes(generated)
    runtime_forbidden = {
        fragment: generated.count(fragment) + embedded_script.count(fragment)
        for fragment in FORBIDDEN_RUNTIME_FRAGMENTS
    }

    exact_payload_pass = all(
        [
            not differences,
            not generated_errors,
            not teaching_errors,
            all(record["matches_expected"] for record in token_inventory.values()),
            all(record["matches_expected"] for record in required_inventory),
            all(record["matches_expected"] for record in forbidden_inventory),
            generated.count(r"\[") == 0,
            generated.count(r"\]") == 0,
            string_targets == EXPECTED_STRING_TARGETS,
            number_writes == EXPECTED_NUMBER_WRITES,
            all(count == 0 for count in runtime_forbidden.values()),
            generated.count("Scripting.RunPowershellScript.RunScript") == 1,
            generated.count("Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource") == 5,
            generated.count("_ValueTypeMatch TO SourceCellJson = SavedCellJson") == 12,
            sum(
                generated.count(f"Json=> TextSource{index}Json")
                for index in range(1, 8)
            )
            == 7,
        ]
    )

    response_contract_pass = all(
        [
            response_dom["rendered_response"]["completed"],
            not response_dom["rendered_response"]["refusal"],
            response_dom["rendered_response"]["pre_code_element_count"] == 1,
            response_dom["contract_observation"]["actual_text_code_block_count"] == 1,
            not response_dom["contract_observation"][
                "download_file_substituted_for_required_code_block"
            ],
        ]
    )

    generated_lines = generated.split("\n")
    result = {
        "schema_version": 1,
        "cycle_id": "EX03-R11-G1",
        "recorded_at": datetime.now().astimezone().isoformat(),
        "version": "20260917-excel-r11",
        "inputs": {
            "generated_robin": {
                "path": relative(GENERATED),
                "sha256": sha256(GENERATED),
            },
            "visible_response": {
                "path": relative(RESPONSE),
                "sha256": sha256(RESPONSE),
            },
            "response_dom_inspection": {
                "path": relative(RESPONSE_DOM),
                "sha256": sha256(RESPONSE_DOM),
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
            "method": "single Copilot response blob download; copied byte-identically into cycle evidence",
            "utf8_bytes": len(raw),
            "utf16_units": len(generated_text.encode("utf-16-le")) // 2,
            "line_count": len(generated_lines),
            "line_ending": "CRLF" if b"\r\n" in raw else "LF",
            "carriage_return_count": raw.count(b"\r"),
            "final_newline": raw.endswith((b"\n", b"\r")),
            "first_line": generated_lines[0],
            "last_line": generated_lines[-1],
            "markdown_fence_count": generated.count("```"),
            "nbsp_count": generated.count("\u00a0"),
            "ellipsis_count": generated.count("..."),
            "generated_text_edited": False,
        },
        "response_delivery_contract": {
            "completed": response_dom["rendered_response"]["completed"],
            "refusal": response_dom["rendered_response"]["refusal"],
            "required_single_text_code_block": True,
            "actual_text_code_block_count": response_dom["contract_observation"][
                "actual_text_code_block_count"
            ],
            "download_file_substituted_for_required_code_block": response_dom[
                "contract_observation"
            ]["download_file_substituted_for_required_code_block"],
            "response_explicitly_admits_code_block_absent": (
                "この回答では不完全なコードブロックを出していません" in response_text
            ),
            "response_explicitly_says_download_is_not_acceptance": (
                "これはコードブロックの代替による受入完了を意味しません"
                in response_text
            ),
            "fixed_contract_satisfied": response_contract_pass,
        },
        "comparison": {
            "method": (
                "derive fixed EX03 from the byte-preserved independent r11 teaching "
                "Robin by reversing only recorded data-slot substitutions and the "
                "teaching error label"
            ),
            "expected_line_count": len(expected.split("\n")),
            "generated_line_count": len(generated_lines),
            "differing_content_line_count": len(differences),
            "differing_lines": differences,
            "exact_adapted_teaching_match": not differences,
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
                "EX03 text source": generated.count("EX03 text source"),
            },
            "string_targets": sorted([list(item) for item in string_targets]),
            "number_writes": sorted([list(item) for item in number_writes]),
            "downloaded_payload_static_fidelity_pass": exact_payload_pass,
        },
        "powershell_parser": {
            "method": (
                "extract and decode the embedded script, then parse it with the "
                "Windows PowerShell AST parser without execution"
            ),
            "generated_embedded_script_error_count": len(generated_errors),
            "generated_embedded_script_errors": generated_errors,
            "independent_teaching_script_error_count": len(teaching_errors),
            "generated_script_executed_by_audit": False,
        },
        "target_workbook_and_side_effect_review": {
            "output_exists_guard_count": generated.count("File.IfFile.Exists"),
            "all_excel_actions_inside_else": all(
                match.start() > generated.index("\nELSE\n")
                for match in re.finditer(r"\bExcel\.", generated)
            ),
            "normalized_exact_fullname_match_count": generated.count(
                "if ([IO.Path]::GetFullPath([string]$candidate.FullName) -ieq $targetPath)"
            ),
            "exactly_one_workbook_required_count": generated.count(
                "$matches.Count -ne 1"
            ),
            "selected_match_zero_index_count": generated.count("$matches[0]"),
            "save_as_count": generated.count("Excel.SaveExcel.SaveAs"),
            "write_action_count": generated.count("Excel.WriteToExcel.WriteCell"),
            "run_powershell_script_count": generated.count(
                "Scripting.RunPowershellScript.RunScript"
            ),
            "read_only_true_count": generated.count("ReadOnly: True"),
            "read_only_false_count": generated.count("ReadOnly: False"),
            "source_json_actions": sum(
                generated.count(f"Json=> TextSource{index}Json")
                for index in range(1, 8)
            ),
            "saved_json_actions": generated.count("Json=> SavedCellJson"),
            "value_type_match_variables": generated.count(
                "_ValueTypeMatch TO SourceCellJson = SavedCellJson"
            ),
            "forbidden_runtime_fragments": runtime_forbidden,
            "payload_static_safety_pass": exact_payload_pass,
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
            "static_payload_pass_used_as_pad_acceptance": False,
        },
        "decision": {
            "status": "FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD",
            "downloaded_payload_static_safety": (
                "PASS" if exact_payload_pass else "FAIL"
            ),
            "response_delivery_contract": (
                "PASS" if response_contract_pass else "FAIL"
            ),
            "pad_import_authorized": False,
            "runtime_authorized": False,
            "recopy_required_but_not_reached": True,
            "reason": (
                "The single response supplied zero text code blocks and substituted "
                "a blob-download file, contrary to the fixed one-code-block contract. "
                "The downloaded bytes statically match the expected r11 adaptation "
                "and parse cleanly, but the fixed mismatch stop rule prohibits PAD "
                "paste, save, re-copy, Run1, or Run2."
            ),
            "resend_allowed": False,
        },
    }

    if output is not None:
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = audit(None if args.verify else args.output)
    print(
        json.dumps(
            {
                "status": result["decision"]["status"],
                "generated_sha256": result["inputs"]["generated_robin"]["sha256"],
                "static_payload_safety": result["decision"][
                    "downloaded_payload_static_safety"
                ],
                "delivery_contract": result["decision"][
                    "response_delivery_contract"
                ],
                "differing_lines": result["comparison"][
                    "differing_content_line_count"
                ],
                "parser_errors": result["powershell_parser"][
                    "generated_embedded_script_error_count"
                ],
            },
            ensure_ascii=False,
        )
    )
