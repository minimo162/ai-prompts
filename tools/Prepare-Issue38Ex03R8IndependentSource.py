#!/usr/bin/env python3
"""Separate the r7 fixed-answer Robin into an independent r8 teaching example.

The fixed EX03 request, specification, expected values, fixtures, and r7 are
read-only inputs.  This script changes only example data (paths, sheets,
ranges, and target cells), preserves the measured action structure, and emits
a candidate for a dedicated PAD Designer paste/save/re-copy check.  It does
not send to Copilot and does not execute either the example or EX03.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
R7 = ROOT / "copilot/versions/20260916-excel-r7"
REQUEST = ROOT / "catalog/acceptance/issue38/requests/EX03.txt"
SPEC = ROOT / "catalog/acceptance/issue38/spec.json"
EXPECTED_VALUES = ROOT / "catalog/acceptance/issue38/expected.json"
OUTPUT = ROOT / "catalog/acceptance/issue38/probes/ex03-r8-independent-source"

INPUTS = {
    "r7_manifest": R7 / "manifest.json",
    "r7_instruction": R7 / "agent-instructions.txt",
    "r7_bundle": R7 / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "r7_robin": R7 / "support/EX03-R7-PAD-Recopy.robin",
    "r7_script": R7 / "support/EX03-TextWrite-FormatSandwich.ps1.txt",
    "fixed_request": REQUEST,
    "fixed_spec": SPEC,
    "grader_expected": EXPECTED_VALUES,
}

EXPECTED_HASHES = {
    "r7_manifest": "38517f37be934b1bcf37c0e12f9f33c9e803fa174af15e41579ccdd612dc4e3f",
    "r7_instruction": "b888b7497c2c5a7fb79860c22da6be4b62f013731ab920e87dbb503ef1f0d7fa",
    "r7_bundle": "228329f60f17192f87878fb6393abf22520d051a1225d9905f2f71354216f1ed",
    "r7_robin": "529d66dd598c395c6313a6f6d6b44c80049effb79de96b675a37f7dc99596d89",
    "r7_script": "d0a5df36516fcf4e27f6d789300ee5a03789aba8176571b1ab86fe84f15fba1a",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "grader_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
}

TARGET_ROOT = r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38"
EXAMPLE_ROOT = r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\teaching\\excel-r8-example"

# Ordered, non-overlapping data substitutions.  Action names, argument names,
# modes, DataTable indices, variable dependency order, and block structure are
# intentionally not changed.
REPLACEMENTS = [
    (
        TARGET_ROOT + r"\\runs\\EX03-attempt1\\照合結果.xlsx",
        EXAMPLE_ROOT + r"\\example-result.xlsx",
        "output_path",
    ),
    (
        TARGET_ROOT + r"\\fixtures\\EX03\\入力い.xlsx",
        EXAMPLE_ROOT + r"\\source-one.xlsx",
        "source_one_path",
    ),
    (
        TARGET_ROOT + r"\\fixtures\\EX03\\入力ろ.xlsx",
        EXAMPLE_ROOT + r"\\source-two.xlsx",
        "source_two_path",
    ),
    (
        TARGET_ROOT + r"\\runs\\EX03-attempt1\\work.xlsx",
        EXAMPLE_ROOT + r"\\work-copy.xlsx",
        "work_path",
    ),
    (
        "StartColumn: $'''D''' StartRow: 4 EndColumn: $'''E''' EndRow: 6",
        "StartColumn: $'''H''' StartRow: 3 EndColumn: $'''I''' EndRow: 5",
        "source_one_range",
    ),
    (
        "StartColumn: $'''B''' StartRow: 2 EndColumn: $'''D''' EndRow: 3",
        "StartColumn: $'''C''' StartRow: 7 EndColumn: $'''E''' EndRow: 8",
        "source_two_range",
    ),
    (
        "StartColumn: $'''F''' StartRow: 7 EndColumn: $'''G''' EndRow: 9",
        "StartColumn: $'''J''' StartRow: 4 EndColumn: $'''K''' EndRow: 6",
        "readback_one_range",
    ),
    (
        "StartColumn: $'''D''' StartRow: 5 EndColumn: $'''F''' EndRow: 6",
        "StartColumn: $'''B''' StartRow: 10 EndColumn: $'''D''' EndRow: 11",
        "readback_two_range",
    ),
    ("受取明細", "教材入力一", "source_one_sheet"),
    ("追加項目", "教材入力二", "source_two_sheet"),
    ("集計先", "教材出力一", "target_one_sheet"),
    ("追記先", "教材出力二", "target_two_sheet"),
    ("F7", "J4", "target_one_text_1"),
    ("G7", "K4", "target_one_number_1"),
    ("F8", "J5", "target_one_text_2"),
    ("G8", "K5", "target_one_number_2"),
    ("F9", "J6", "target_one_text_3"),
    ("G9", "K6", "target_one_number_3"),
    ("D5", "B10", "target_two_text_1"),
    ("E5", "C10", "target_two_number_1"),
    ("F5", "D10", "target_two_text_2"),
    ("D6", "B11", "target_two_text_3"),
    ("E6", "C11", "target_two_number_2"),
    ("F6", "D11", "target_two_text_4"),
    ("fixed EX03 text mapping", "independent teaching text mapping", "error_scope"),
    ("Fixed text source", "Teaching text source", "error_type"),
]

ACTION_PREFIX = "Scripting.RunPowershellScript.RunScript Script: $'''"
ACTION_SUFFIX = "''' ScriptOutput=> PowershellOutput"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text_exact(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def normalized(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip("\n")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def extract_action(flow: str) -> str:
    content = normalized(flow)
    start = content.index(ACTION_PREFIX)
    end = content.index(ACTION_SUFFIX, start) + len(ACTION_SUFFIX)
    lines = content[start:end].split("\n")
    return "\n".join([lines[0], *(line[4:] for line in lines[1:])]) + "\n"


def action_payload(action: str) -> str:
    value = action.rstrip("\r\n")
    if not value.startswith(ACTION_PREFIX) or not value.endswith(ACTION_SUFFIX):
        raise ValueError("RunScript wrapper is not the captured PAD form")
    return value[len(ACTION_PREFIX) : -len(ACTION_SUFFIX)]


def decode_robin_string(value: str) -> str:
    decoded: list[str] = []
    index = 0
    while index < len(value):
        if (
            value[index] == "\\"
            and index + 1 < len(value)
            and value[index + 1] in {"\\", "'", '"'}
        ):
            decoded.append(value[index + 1])
            index += 2
        else:
            decoded.append(value[index])
            index += 1
    return "".join(decoded)


def write_new(path: Path, data: bytes) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite: {path}")
    path.write_bytes(data)


def main() -> None:
    actual_hashes = {name: sha256(path) for name, path in INPUTS.items()}
    if actual_hashes != EXPECTED_HASHES:
        raise ValueError(f"Protected input mismatch: {actual_hashes}")
    if OUTPUT.exists():
        raise FileExistsError(f"Capture directory already exists: {OUTPUT}")

    r7_manifest = json.loads(INPUTS["r7_manifest"].read_bytes())
    if r7_manifest["version"] != "20260916-excel-r7":
        raise ValueError("Unexpected base candidate")
    request = read_text_exact(REQUEST)
    spec = json.loads(SPEC.read_bytes())
    grader = json.loads(EXPECTED_VALUES.read_bytes())
    r7_instruction = read_text_exact(INPUTS["r7_instruction"])
    r7_bundle = read_text_exact(INPUTS["r7_bundle"])
    r7_robin = read_text_exact(INPUTS["r7_robin"])

    ex03_spec = next(case for case in spec["cases"] if case["id"] == "EX03")
    fixed_identifiers = {
        "source_one_file": ex03_spec["inputs"][0]["file"],
        "source_one_sheet": ex03_spec["inputs"][0]["sheet"],
        "source_one_range": ex03_spec["inputs"][0]["range"],
        "source_one_target_sheet": ex03_spec["inputs"][0]["target_sheet"],
        "source_one_target_start": ex03_spec["inputs"][0]["target_start"],
        "source_two_file": ex03_spec["inputs"][1]["file"],
        "source_two_sheet": ex03_spec["inputs"][1]["sheet"],
        "source_two_range": ex03_spec["inputs"][1]["range"],
        "source_two_target_sheet": ex03_spec["inputs"][1]["target_sheet"],
        "source_two_target_start": ex03_spec["inputs"][1]["target_start"],
        "output": ex03_spec["output"],
    }
    required_request_terms = [
        "入力い.xlsx", "入力ろ.xlsx", "受取明細", "追加項目",
        "D4:E6", "B2:D3", "集計先", "追記先", "F7", "D5",
        "work.xlsx", "照合結果.xlsx",
    ]
    if not all(term in request for term in required_request_terms):
        raise ValueError("Fixed request no longer contains its frozen identifiers")

    r7_completion_terms = [
        TARGET_ROOT + r"\\fixtures\\EX03\\入力い.xlsx",
        TARGET_ROOT + r"\\fixtures\\EX03\\入力ろ.xlsx",
        TARGET_ROOT + r"\\runs\\EX03-attempt1\\work.xlsx",
        TARGET_ROOT + r"\\runs\\EX03-attempt1\\照合結果.xlsx",
        "受取明細", "追加項目", "集計先", "追記先",
        "F7", "G7", "F8", "G8", "F9", "G9",
        "D5", "E5", "F5", "D6", "E6", "F6",
    ]
    if not all(term in r7_robin for term in r7_completion_terms):
        raise ValueError("r7 no longer contains the fixed-answer completion terms")

    candidate = r7_robin
    replacement_counts = {}
    for old, new, label in REPLACEMENTS:
        count = candidate.count(old)
        if count < 1:
            raise ValueError(f"Expected replacement source not found: {label}: {old}")
        replacement_counts[label] = count
        candidate = candidate.replace(old, new)

    leaked_terms = [term for term in r7_completion_terms if term in candidate]
    if leaked_terms:
        raise ValueError(f"Fixed EX03 completion terms leaked into example: {leaked_terms}")
    example_terms = [
        EXAMPLE_ROOT, "source-one.xlsx", "source-two.xlsx", "work-copy.xlsx",
        "example-result.xlsx", "教材入力一", "教材入力二", "教材出力一",
        "教材出力二", "J4", "K4", "J6", "K6", "B10", "C10",
        "D10", "B11", "C11", "D11",
    ]
    if not all(term in candidate for term in example_terms):
        raise ValueError("Independent example is missing one or more fixed example identifiers")

    reversed_candidate = candidate
    for old, new, _ in reversed(REPLACEMENTS):
        reversed_candidate = reversed_candidate.replace(new, old)
    if normalized(reversed_candidate) != normalized(r7_robin):
        raise ValueError("Example differs from r7 outside the explicit data substitution map")

    candidate_action = extract_action(candidate)
    candidate_script = decode_robin_string(action_payload(candidate_action)) + "\n"
    expected_strings = [
        value
        for matrix in grader["matrices"]["EX03"]
        for row in matrix
        for value in row
        if isinstance(value, str)
    ]
    unique_expected_strings = [value for value in expected_strings if value != "100%"]
    if any(value in candidate for value in unique_expected_strings):
        raise ValueError("A unique grader-only string leaked into the teaching Robin")

    OUTPUT.mkdir(parents=True)
    candidate_path = OUTPUT / "candidate-full.robin"
    action_path = OUTPUT / "candidate-action.robin"
    script_path = OUTPUT / "candidate-script.ps1.txt"
    write_new(candidate_path, candidate.encode("utf-8"))
    write_new(action_path, candidate_action.encode("utf-8"))
    write_new(script_path, candidate_script.encode("utf-8"))

    before = {
        "schema_version": 1,
        "audit_id": "EX03-R7-TEACHING-INDEPENDENCE",
        "audited_utc": datetime.now(timezone.utc).isoformat(),
        "base_commit": "806e4095a926fa0c7e020811c09770b5e5292841",
        "base_version": "20260916-excel-r7",
        "decision": "FAIL_R7_CONTAINS_FIXED_EX03_COMPLETE_ANSWER",
        "fixed_inputs": {
            name: {"path": relative(path), "sha256": actual_hashes[name]}
            for name, path in INPUTS.items()
            if name in {"fixed_request", "fixed_spec", "grader_expected"}
        },
        "fixed_identifiers": fixed_identifiers,
        "findings": {
            "all_fixed_paths_present_in_complete_robin": True,
            "all_fixed_sheet_names_present_in_complete_robin": True,
            "all_fixed_target_cells_present_in_complete_robin": True,
            "complete_flow_includes_guard_read_write_save_reopen_compare": True,
            "grader_only_values_literal_in_robin": False,
            "independence_failure_reason": (
                "The r7 PAD-recopied full Robin is a complete answer for the exact "
                "fixed EX03 paths, sheets, ranges, output, and twelve target cells."
            ),
        },
        "causal_boundary": (
            "This audit establishes teaching/test coupling. It does not claim that "
            "literal grader-only values were exposed or infer Copilot internals."
        ),
        "r7_instruction_contains_fixed_answer_directive": (
            "同じ固定EX03では06のPAD再コピー完全原文を生成元として逐語出力します"
            in r7_instruction
        ),
        "r7_bundle_contains_full_fixed_robin": normalized(r7_robin) in normalized(r7_bundle),
    }
    write_new(
        OUTPUT / "independence-before.json",
        (json.dumps(before, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )

    preflight = {
        "schema_version": 1,
        "capture_id": "EX03-R8-INDEPENDENT-SOURCE",
        "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "Dedicated PAD paste/save/re-copy of an independent teaching example; "
            "no Copilot send and no example or EX03 execution"
        ),
        "source": {
            "path": relative(INPUTS["r7_robin"]),
            "sha256": actual_hashes["r7_robin"],
        },
        "candidate": {
            "path": relative(candidate_path),
            "sha256": sha256(candidate_path),
            "utf8_bytes": candidate_path.stat().st_size,
            "lines": len(candidate.splitlines()),
        },
        "candidate_action": {
            "path": relative(action_path),
            "sha256": sha256(action_path),
        },
        "candidate_script": {
            "path": relative(script_path),
            "sha256": sha256(script_path),
        },
        "example_conditions": {
            "source_one": {
                "path": "catalog/teaching/excel-r8-example/source-one.xlsx",
                "sheet": "教材入力一",
                "range": "H3:I5",
                "target_sheet": "教材出力一",
                "target_start": "J4",
            },
            "source_two": {
                "path": "catalog/teaching/excel-r8-example/source-two.xlsx",
                "sheet": "教材入力二",
                "range": "C7:E8",
                "target_sheet": "教材出力二",
                "target_start": "B10",
            },
            "work": "catalog/teaching/excel-r8-example/work-copy.xlsx",
            "output": "catalog/teaching/excel-r8-example/example-result.xlsx",
        },
        "replacement_counts": replacement_counts,
        "mechanical_checks": {
            "fixed_request_spec_expected_hashes_preserved": True,
            "r7_identified_as_complete_fixed_answer": True,
            "example_diff_is_only_explicit_data_substitution": True,
            "fixed_completion_terms_absent_from_candidate": True,
            "unique_grader_strings_absent_from_candidate": True,
            "expected_string_100_percent_not_used_by_candidate": "100%" not in candidate,
            "action_structure_and_dependency_order_preserved": True,
            "candidate_has_one_run_script": candidate.count(
                "Scripting.RunPowershellScript.RunScript"
            ) == 1,
            "candidate_has_five_numeric_writes": candidate.count(
                "Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource"
            ) == 5,
            "candidate_has_twelve_json_comparisons": candidate.count(
                "_ValueTypeMatch TO SourceCellJson = SavedCellJson"
            ) == 12,
        },
        "live_limits": {
            "dedicated_pad_paste_save_recopy_only": True,
            "execute_example": False,
            "execute_ex03": False,
            "copilot_send": False,
            "github_write": False,
        },
    }
    if not all(preflight["mechanical_checks"].values()):
        raise ValueError(f"Preflight failed: {preflight['mechanical_checks']}")
    write_new(
        OUTPUT / "preflight.json",
        (json.dumps(preflight, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    print(json.dumps({
        "decision": before["decision"],
        "candidate_sha256": sha256(candidate_path),
        "candidate_action_sha256": sha256(action_path),
        "candidate_script_sha256": sha256(script_path),
        "mechanical_checks": preflight["mechanical_checks"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
