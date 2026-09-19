#!/usr/bin/env python3
"""Audit the sole EX03-r12-G1 Copilot response without executing it in PAD."""

from __future__ import annotations

import difflib
import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CYCLE = BASE / "cycles/EX03-r12-G1"
VERSION = ROOT / "copilot/versions/20260917-excel-r12"

GENERATED = CYCLE / "generated.robin"
RESPONSE = CYCLE / "copilot-response.visible.txt"
RESPONSE_DOM = CYCLE / "response-dom-inspection.json"
LIVE_SEND = CYCLE / "live-send.json"
TEACHING = VERSION / "support/EX03-R12-Prepared-Normal.robin"
TEACHING_SCRIPT = VERSION / "support/EX03-R12-JSON-File-Handoff.ps1.txt"
SOURCE_TOOL = ROOT / "tools/Prepare-Issue38Ex03R8IndependentSource.py"
R12_EXTRACTOR_TOOL = ROOT / "tools/Build-Issue38Ex03CandidateR12.py"
PARSER_TOOL = ROOT / "tools/Analyze-Issue38Ex03R11Generation.py"

EXPECTED = {
    "instruction": "11321acdbb96632221b02b7b737d12ba816ea4cf9f35f933a114c7f857539c06",
    "bundle": "ddee43a1eddc966f62095b63a23b135df184f3cbe0ded635cbf72520e6744b97",
    "manifest": "a6f65db93d56c1e0a212a8059f034240489b29ee4cfd4abc6b998e73ea2cefb1",
    "teaching": "7bde8bb20bb7f347c97722d77a4141bf8348bb40d97aaca435e01998e8b9d3a3",
    "teaching_script": "314b687ce8d1848558d80340b414d32c8d3baca2c5e699541db0eb062f96ba1c",
    "body": "cf25fb4aa54375d992e00545d336058b67055ab7de934e52ce284dffcd9924cc",
    "request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
}

EXPECTED_STRING_TARGETS = {
    ("集計先", "F7"), ("集計先", "F8"), ("集計先", "F9"),
    ("追記先", "D5"), ("追記先", "D6"), ("追記先", "F5"), ("追記先", "F6"),
}
EXPECTED_NUMBER_WRITES = {
    ("NumberSource1", "G", "7"), ("NumberSource2", "G", "8"),
    ("NumberSource3", "G", "9"), ("NumberSource4", "E", "5"),
    ("NumberSource5", "E", "6"),
}
FORBIDDEN_RUNTIME = [
    "File.Delete", "Folder.Delete", "WebAutomation.", "HTTP.",
    "System.RunDOSCommand", "System.RunApplication", "Start-Process",
    "Remove-Item", "Invoke-WebRequest", "Invoke-Expression",
]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


source_tool = load("issue38_r12_source", SOURCE_TOOL)
r12_extractor_tool = load("issue38_r12_extractor", R12_EXTRACTOR_TOOL)
parser_tool = load("issue38_r12_parser", PARSER_TOOL)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def normalized(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip("\n")


def extract_embedded_script(robin: str) -> str:
    """Extract an r12 RunScript payload without legacy flow-indent removal."""
    return r12_extractor_tool.embedded_script(robin)


def expected_adaptation(teaching: str) -> tuple[str, list[dict[str, object]]]:
    value = teaching
    counts: list[dict[str, object]] = []
    for fixed, independent, label in reversed(source_tool.REPLACEMENTS):
        independent = independent.replace("excel-r8-example", "excel-r12-example")
        count = value.count(independent)
        if count:
            value = value.replace(independent, fixed)
        elif label not in {"error_scope", "error_type"}:
            raise ValueError(f"Missing r12 teaching slot: {label}")
        counts.append({"label": label, "count": count})
    teaching_root = (
        r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\teaching\\excel-r12-example"
    )
    fixed_json_root = (
        r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38"
        r"\\runs\\EX03-attempt1"
    )
    root_count = value.count(teaching_root)
    if root_count != 9:
        raise ValueError(f"Unexpected remaining r12 teaching-root count: {root_count}")
    value = value.replace(teaching_root, fixed_json_root)
    counts.append({"label": "json_handoff_root", "count": root_count})
    return value, counts


def diff_hunks(expected: str, actual: str) -> list[dict[str, object]]:
    before = expected.split("\n")
    after = actual.split("\n")
    records: list[dict[str, object]] = []
    for tag, a1, a2, b1, b2 in difflib.SequenceMatcher(None, before, after).get_opcodes():
        if tag != "equal":
            records.append({
                "operation": tag,
                "expected_lines": [a1 + 1, a2],
                "actual_lines": [b1 + 1, b2],
                "expected": before[a1:a2],
                "actual": after[b1:b2],
            })
    return records


def extract_string_targets(script: str) -> set[tuple[str, str]]:
    pattern = re.compile(
        r"@\('Data[12]\[\d\]\[\d\]', '([^']+)', '([^']+)', \[string\]\$payloads\[\d\]\.probe\)"
    )
    return {tuple(match.groups()) for match in pattern.finditer(script)}


def extract_number_writes(robin: str) -> set[tuple[str, str, str]]:
    pattern = re.compile(
        r"Excel\.WriteToExcel\.WriteCell Instance: Work Value: (NumberSource\d+) "
        r"Column: \$'''([^']+)''' Row: (\d+)"
    )
    return {tuple(match.groups()) for match in pattern.finditer(robin)}


def write_json_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def audit() -> dict[str, object]:
    for name, path in {
        "instruction": VERSION / "agent-instructions.txt",
        "bundle": VERSION / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
        "manifest": VERSION / "manifest.json",
        "teaching": TEACHING,
        "teaching_script": TEACHING_SCRIPT,
        "body": CYCLE / "submitted-body.txt",
        "request": BASE / "requests/EX03.txt",
    }.items():
        if sha256(path) != EXPECTED[name]:
            raise ValueError(f"Protected {name} SHA changed: {sha256(path)}")

    raw = GENERATED.read_bytes()
    generated_text = raw.decode("utf-8")
    generated = normalized(generated_text)
    teaching = normalized(TEACHING.read_text(encoding="utf-8"))
    expected, replacement_counts = expected_adaptation(teaching)
    expected = normalized(expected)
    hunks = diff_hunks(expected, generated)

    embedded = extract_embedded_script(generated)
    teaching_embedded = extract_embedded_script(teaching)
    if teaching_embedded != TEACHING_SCRIPT.read_text(encoding="utf-8").rstrip("\r\n"):
        raise ValueError("Prepared r12 Robin no longer embeds the fixed teaching script")
    parser_errors = parser_tool.parse_powershell(embedded)
    teaching_parser_errors = parser_tool.parse_powershell(teaching_embedded)
    dom = json.loads(RESPONSE_DOM.read_bytes())
    send = json.loads(LIVE_SEND.read_bytes())
    response_text = RESPONSE.read_text(encoding="utf-8")

    forbidden = {fragment: generated.count(fragment) for fragment in FORBIDDEN_RUNTIME}
    string_targets = extract_string_targets(embedded)
    number_writes = extract_number_writes(generated)
    structure = {
        "run_script_count": generated.count("Scripting.RunPowershellScript.RunScript"),
        "source_json_write_count": len(re.findall(r"File\.WriteText File: .*source-[1-7]\.json", generated)),
        "mode_json_write_count": len(re.findall(r"File\.WriteText File: .*mode\.json", generated)),
        "source_json_read_count": len(re.findall(r"Get-Content -LiteralPath .*source-[1-7]\.json", generated)),
        "mode_json_read_count": len(re.findall(r"Get-Content -LiteralPath .*mode\.json", generated)),
        "inner_format_finally_count": generated.count("finally {\n                $cell.NumberFormat = $beforeFormat\n            }"),
        "exact_success_gate_count": generated.count(
            "IF PowershellOutput = $'''{\\\"status\\\":\\\"OK\\\",\\\"mode\\\":\\\"NORMAL\\\",\\\"text_writes\\\":7,\\\"formats_restored\\\":true}''' THEN"
        ),
        "normal_gate_count": generated.count("IF RunMode = $'''NORMAL''' THEN"),
        "numeric_write_count": generated.count("Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource"),
        "save_as_count": generated.count("Excel.SaveExcel.SaveAs"),
        "json_comparison_count": generated.count("_ValueTypeMatch TO SourceCellJson = SavedCellJson"),
        "convert_to_json_compress_count": generated.count("ConvertTo-Json -Compress"),
        "corrupt_press_pipeline_count": generated.count("$result | press"),
        "direct_text_json_interpolation_count": len(re.findall(r"%TextSource[1-7]Json%", generated)),
    }
    structure_pass = all([
        structure["run_script_count"] == 1,
        structure["source_json_write_count"] == 7,
        structure["mode_json_write_count"] == 1,
        structure["source_json_read_count"] == 7,
        structure["mode_json_read_count"] == 1,
        structure["inner_format_finally_count"] == 1,
        structure["exact_success_gate_count"] == 1,
        structure["normal_gate_count"] == 1,
        structure["numeric_write_count"] == 5,
        structure["save_as_count"] == 1,
        structure["json_comparison_count"] == 12,
        structure["convert_to_json_compress_count"] == 1,
        structure["corrupt_press_pipeline_count"] == 0,
        structure["direct_text_json_interpolation_count"] == 0,
        string_targets == EXPECTED_STRING_TARGETS,
        number_writes == EXPECTED_NUMBER_WRITES,
        all(count == 0 for count in forbidden.values()),
    ])
    delivery_pass = all([
        dom["rendered_response"]["completed"],
        not dom["rendered_response"]["refusal"],
        dom["code_block"]["actual_text_code_block_count"] == 1,
        dom["code_block"]["clipboard_plain_matches_dom_lines"],
        not dom["code_block"]["clipboard_plain_has_language_label"],
        not dom["code_block"]["clipboard_plain_has_markdown_fence"],
        not dom["code_block"]["clipboard_plain_has_visual_line_numbers"],
        not dom["code_block"]["clipboard_plain_has_expand_control"],
    ])
    payload_pass = all([
        not hunks,
        not parser_errors,
        not teaching_parser_errors,
        structure_pass,
        generated.split("\n")[0].startswith("SET "),
        generated.split("\n")[-1] == "END",
    ])
    decision = (
        "PASS_READY_FOR_DEDICATED_PAD"
        if delivery_pass and payload_pass
        else "FAIL_GENERATED_ROBIN_MISMATCH_AND_POWERSHELL_PARSE_ERROR_STOP_BEFORE_PAD"
    )
    result = {
        "schema_version": 1,
        "cycle_id": "EX03-r12-G1",
        "recorded_at": datetime.now().astimezone().isoformat(),
        "version": "20260917-excel-r12",
        "inputs": {
            "generated_robin": {"path": rel(GENERATED), "sha256": sha256(GENERATED)},
            "visible_response": {"path": rel(RESPONSE), "sha256": sha256(RESPONSE)},
            "response_dom": {"path": rel(RESPONSE_DOM), "sha256": sha256(RESPONSE_DOM)},
            "live_send": {"path": rel(LIVE_SEND), "sha256": sha256(LIVE_SEND)},
            "prepared_normal": {"path": rel(TEACHING), "sha256": sha256(TEACHING)},
        },
        "generation": {
            "send_count": send["send_count"],
            "send_limit": send["send_limit"],
            "conversation_url": send["conversation_url"],
            "refusal": dom["rendered_response"]["refusal"],
            "completed": dom["rendered_response"]["completed"],
            "regeneration_requested": False,
        },
        "delivery_contract": {
            "required_text_code_block_count": 1,
            "actual_text_code_block_count": dom["code_block"]["actual_text_code_block_count"],
            "language_badge": dom["code_block"]["language_badge"],
            "clipboard_plain_matches_rendered_code_lines": dom["code_block"]["clipboard_plain_matches_dom_lines"],
            "clipboard_plain_excludes_ui_label_line_numbers_and_expand_control": all([
                not dom["code_block"]["clipboard_plain_has_language_label"],
                not dom["code_block"]["clipboard_plain_has_visual_line_numbers"],
                not dom["code_block"]["clipboard_plain_has_expand_control"],
            ]),
            "pass": delivery_pass,
        },
        "capture": {
            "method": "normal M365 Copilot code-block copy text/plain captured without editing",
            "sha256": sha256(GENERATED),
            "utf8_bytes": len(raw),
            "utf16_units": len(generated_text.encode("utf-16-le")) // 2,
            "line_count": len(generated.split("\n")),
            "line_ending": "CRLF" if b"\r\n" in raw else "LF",
            "final_newline": raw.endswith((b"\r", b"\n")),
            "first_line": generated.split("\n")[0],
            "last_line": generated.split("\n")[-1],
            "manual_edit_applied": False,
        },
        "adapted_source_comparison": {
            "method": "replace only recorded r12 teaching data slots and teaching-only labels/root",
            "replacement_counts": replacement_counts,
            "expected_line_count": len(expected.split("\n")),
            "actual_line_count": len(generated.split("\n")),
            "difference_hunk_count": len(hunks),
            "difference_hunks": hunks,
            "exact_match": not hunks,
        },
        "powershell_parser": {
            "extractor": "r12 prefix/suffix extraction without legacy four-character deindent",
            "generated_error_count": len(parser_errors),
            "generated_errors": parser_errors,
            "prepared_script_error_count": len(teaching_parser_errors),
            "prepared_embedded_matches_support_without_final_newline": True,
            "executed": False,
        },
        "structure": {
            **structure,
            "string_targets": sorted([list(item) for item in string_targets]),
            "number_writes": sorted([list(item) for item in number_writes]),
            "forbidden_runtime_fragments": forbidden,
            "pass": structure_pass,
        },
        "response_contains_refusal_language": any(
            value in response_text for value in ["生成できません", "拒否します", "対応できません"]
        ),
        "decision": decision,
        "stop": {
            "reason": "Generated copy changed four non-slot blank lines and replaced ConvertTo-Json -Compress with invalid '| press', causing a PowerShell parse error.",
            "pad_save": 0,
            "pad_recopy": 0,
            "pad_run": 0,
            "manual_repair": 0,
            "resend": 0,
            "successor_created": 0,
            "github_write": 0,
        },
    }
    return result


if __name__ == "__main__":
    audit_path = CYCLE / "generation-safety-audit.json"
    result_path = CYCLE / "generation-result.json"
    if audit_path.exists() or result_path.exists():
        raise FileExistsError("Refusing to overwrite r12 generation evidence")
    result = audit()
    write_json_new(audit_path, result)
    write_json_new(result_path, {
        "schema_version": 1,
        "cycle_id": result["cycle_id"],
        "version": result["version"],
        "decision": result["decision"],
        "generated_robin_sha256": result["inputs"]["generated_robin"]["sha256"],
        "send_count": result["generation"]["send_count"],
        "delivery_contract_pass": result["delivery_contract"]["pass"],
        "adapted_source_exact_match": result["adapted_source_comparison"]["exact_match"],
        "powershell_parser_error_count": result["powershell_parser"]["generated_error_count"],
        "structure_pass": result["structure"]["pass"],
        "pad_save_recopy_runs": 0,
    })
    print(result["decision"])
