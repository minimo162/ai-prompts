#!/usr/bin/env python3
"""Build one fixed EX03 Robin mechanically from the A4 wiring and components."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "catalog/acceptance/issue38"
A4 = ROOT / "copilot/versions/20260918-excel-r12-fixed-helper-a4"
PROTOTYPE = BASE / "probes/ex03-r12-fixed-helper-mechanical-builder"

BUNDLE = A4 / "knowledge/PAD-Robin-Fixed-Helper-A4-Bundle.txt"
WIRING = A4 / "wiring-spec.json"
ASSEMBLY_RULES = A4 / "assembly-rules.json"
A4_MANIFEST = A4 / "manifest.json"
HELPER = BASE / "probes/ex03-r12-fixed-helper/EX03-R12-Fixed-StringTransfer.ps1"
INVOCATION = BASE / "probes/ex03-r12-fixed-helper-a4/invocation.json"
LAUNCHER = BASE / "probes/ex03-r12-fixed-helper-a4/launcher.ps1"
FIXED_REQUEST = BASE / "requests/EX03.txt"
FIXED_SPEC = BASE / "spec.json"
FIXED_EXPECTED = BASE / "expected.json"

OUTPUT = PROTOTYPE / "generated/EX03-R12-FIXED-HELPER-MECHANICAL-P1.robin"
VERIFICATION = PROTOTYPE / "verification.json"

PROTOTYPE_ID = "EX03-R12-FIXED-HELPER-MECHANICAL-BUILDER-P1"
SOURCE_COMMIT = "6ae505aa9a77ffa7b6ec28e2de748c04ba87def5"
EXPECTED_SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'

EXPECTED_SHA256 = {
    "bundle": "62695ca3c007ab291732657ddaeca66723a57115d151efc7b1730ef5341c514c",
    "wiring": "c62ec6951bdd36e895acfc937d7a1f390e75e8d984b26a9531cc2c88d970f58c",
    "assembly_rules": "57305c13d9bff292d7c7c2bc3e3152bcd75b85fd1bd800679df1671f79c7bc6e",
    "a4_manifest": "525c5450e1e17e68d50dbaf25556e77e6e8393cf2ad2cd15792b54859ae7242f",
    "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
    "invocation": "5c5a2008f55296a48f63fa65178aab971e4212455bb2af58e33149bdcaec40d8",
    "launcher": "a286179f8fb7f8febc87f1915cf10965ee0a50769251ecb17573c00926c174d5",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "fixed_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
}

EXPECTED_COMPONENT_SHA256 = {
    "C01_STATE_INIT": "da87bb12ea194095ca8c672b92d1c4535a873437b3ba6235c7b288c60e386fd4",
    "C02_OUTPUT_GUARD": "0694d74e8c308f95861baab1535dd6436bb749eadb84a4a172b1674f8ef47de5",
    "C03_READONLY_TYPED_RANGE": "918765252d61a3f6a34c9b443f4eaa0aa0161cd86ab97f043c8544ad19842932",
    "C04_JSON_FILE_HANDOFF": "4a33eca4fc68c92ac75fbd00ecae60c9d84cd142f2c3e7c8570428bc080707c5",
    "C05_EDITABLE_WORK_OPEN": "8b661b3545f377c99a6b25e7aa026c96bf613ff110c1346c41092d7511084e93",
    "C06_FIXED_LAUNCHER_RUNSCRIPT": "2e2ddf38c8b51a5e434083db5b2be9a2b6253aa4f475d8888d9197bb0bb870ed",
    "C07_EXACT_SUCCESS_MODE_GATE": "9dc3042fc22af7b0a0e90c784ef208828102af2a28087cf385f331ae1af2d412",
    "C08_TARGET_SHEET_ACTIVATION": "9331dd5b830b9854e943e4b0e2c253d13ecc825c85b39efd436e2b9f61b537e6",
    "C09_NUMERIC_WRITE": "c9745f104b057d9f380b535aadb467fa32a9062d6fa1e3989d5cf464e189be26",
    "C10_SAVE_CLOSE_REOPEN_READBACK": "5cef87e70f5e723ea6bcb3316e6801cd3743a51c378deacb4a9cd2f98e3a85e0",
    "C11_JSON_VALUE_TYPE_COMPARE": "96a84f395b60975c3f51372b2fc05e0f8d0d22e16580d993f369fa3b1e39556f",
    "C12_FAILURE_CLOSE_NO_SAVE": "e8715546a45126cfb1c6d192444d56e61283d7948117455fce390e686f83c194",
}

RULE_COMPONENTS = {
    "AR04_EXPLICIT_JSON_HANDOFF": "C04_JSON_FILE_HANDOFF",
    "AR09_EXPLICIT_NUMERIC_WRITES": "C09_NUMERIC_WRITE",
    "AR10_MULTIPLE_RECTANGLE_READBACK": "C10_SAVE_CLOSE_REOPEN_READBACK",
    "AR11_MULTIPLE_JSON_COMPARISONS": "C11_JSON_VALUE_TYPE_COMPARE",
}

ALLOWED_PARAMETERS = {
    "C01_STATE_INIT": set(),
    "C02_OUTPUT_GUARD": {"guard_path"},
    "C03_READONLY_TYPED_RANGE": {
        "input_path", "instance_name", "sheet", "start_column", "start_row",
        "end_column", "end_row", "range_variable",
    },
    "C04_JSON_FILE_HANDOFF": {
        "source_variable", "source_reference", "source_json_variable",
        "json_path", "indent",
    },
    "C05_EDITABLE_WORK_OPEN": {"work_path"},
    "C06_FIXED_LAUNCHER_RUNSCRIPT": set(),
    "C07_EXACT_SUCCESS_MODE_GATE": set(),
    "C08_TARGET_SHEET_ACTIVATION": {"target_sheet", "indent"},
    "C09_NUMERIC_WRITE": {"source_variable", "target_column", "target_row", "indent"},
    "C10_SAVE_CLOSE_REOPEN_READBACK": {
        "output_path", "sheet", "start_column", "start_row", "end_column",
        "end_row", "readback_variable",
    },
    "C11_JSON_VALUE_TYPE_COMPARE": {
        "source_variable", "source_reference", "saved_variable", "saved_reference", "saved_json_variable",
        "source_json_variable", "result_variable",
    },
    "C12_FAILURE_CLOSE_NO_SAVE": set(),
}

EXPECTED_INPUTS = [
    {
        "input_id": "input1",
        "workbook": "fixtures/EX03/入力い.xlsx",
        "sheet": "受取明細",
        "range": "D4:E6",
        "data_table_variable": "Data1",
        "instance": "SourceBook1",
    },
    {
        "input_id": "input2",
        "workbook": "fixtures/EX03/入力ろ.xlsx",
        "sheet": "追加項目",
        "range": "B2:D3",
        "data_table_variable": "Data2",
        "instance": "SourceBook2",
    },
]

EXPECTED_TEXT_POSITIONS = [
    ("input1", "D4", "集計先", "F7"),
    ("input1", "D5", "集計先", "F8"),
    ("input1", "D6", "集計先", "F9"),
    ("input2", "B2", "追記先", "D5"),
    ("input2", "B3", "追記先", "D6"),
    ("input2", "D2", "追記先", "F5"),
    ("input2", "D3", "追記先", "F6"),
]

EXPECTED_NUMERIC_POSITIONS = [
    ("input1", "E4", "集計先", "G7"),
    ("input1", "E5", "集計先", "G8"),
    ("input1", "E6", "集計先", "G9"),
    ("input2", "C2", "追記先", "E5"),
    ("input2", "C3", "追記先", "E6"),
]

EXPECTED_COMPARISON_POSITIONS = [
    ("input1", "D4", "集計先", "F7", "text"),
    ("input1", "E4", "集計先", "G7", "number"),
    ("input1", "D5", "集計先", "F8", "text"),
    ("input1", "E5", "集計先", "G8", "number"),
    ("input1", "D6", "集計先", "F9", "text"),
    ("input1", "E6", "集計先", "G9", "number"),
    ("input2", "B2", "追記先", "D5", "text"),
    ("input2", "C2", "追記先", "E5", "number"),
    ("input2", "D2", "追記先", "F5", "text"),
    ("input2", "B3", "追記先", "D6", "text"),
    ("input2", "C3", "追記先", "E6", "number"),
    ("input2", "D3", "追記先", "F6", "text"),
]

FORBIDDEN_RUNTIME = (
    "File.Delete", "Folder.Delete", "WebAutomation.", "HTTP.",
    "System.RunDOSCommand", "System.RunApplication", "Start-Process",
    "Remove-Item", "Invoke-WebRequest", "Invoke-RestMethod",
    "Invoke-Expression", "ScriptBlock]::Create", "Add-Type",
    "Set-ExecutionPolicy", "Unblock-File",
)


class BuildError(ValueError):
    """Raised before output bytes are written when a fixed contract is invalid."""


@dataclass(frozen=True)
class BuildResult:
    robin: bytes
    verification: dict[str, Any]
    replacements: tuple[dict[str, Any], ...]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def column_number(column: str) -> int:
    value = 0
    for character in column:
        if not "A" <= character <= "Z":
            raise BuildError(f"invalid column: {column}")
        value = value * 26 + ord(character) - ord("A") + 1
    return value


def split_cell(cell: str) -> tuple[str, int]:
    match = re.fullmatch(r"([A-Z]+)([1-9][0-9]*)", cell)
    if not match:
        raise BuildError(f"invalid cell: {cell}")
    return match.group(1), int(match.group(2))


def split_range(value: str) -> tuple[str, int, str, int]:
    match = re.fullmatch(r"([A-Z]+)([1-9][0-9]*):([A-Z]+)([1-9][0-9]*)", value)
    if not match:
        raise BuildError(f"invalid range: {value}")
    return match.group(1), int(match.group(2)), match.group(3), int(match.group(4))


def cell_index(cell: str, rectangle: str) -> list[int]:
    column, row = split_cell(cell)
    start_column, start_row, end_column, end_row = split_range(rectangle)
    column_offset = column_number(column) - column_number(start_column)
    row_offset = row - start_row
    if not (0 <= column_offset <= column_number(end_column) - column_number(start_column)):
        raise BuildError(f"cell outside fixed range: {cell} not in {rectangle}")
    if not (0 <= row_offset <= end_row - start_row):
        raise BuildError(f"cell outside fixed range: {cell} not in {rectangle}")
    return [row_offset, column_offset]


def robin_path(value: str | Path) -> str:
    return str(value).replace("\\", "\\\\")


def decode_robin_string(value: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(value):
        if value[index] == "\\" and index + 1 < len(value) and value[index + 1] in {"\\", "'", '"'}:
            result.append(value[index + 1])
            index += 2
        else:
            result.append(value[index])
            index += 1
    return "".join(result)


def encode_robin_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')


def embedded_script(robin: str) -> str:
    prefix = "Scripting.RunPowershellScript.RunScript Script: $'''"
    suffix = "''' ScriptOutput=> PowershellOutput"
    if robin.count(prefix) != 1 or robin.count(suffix) != 1:
        raise BuildError("generated Robin must contain one PowerShell wrapper")
    start = robin.index(prefix) + len(prefix)
    end = robin.index(suffix, start)
    return decode_robin_string(robin[start:end])


def extract_components(bundle: bytes, manifest: dict[str, Any]) -> dict[str, str]:
    records = {item["id"]: item for item in manifest["component_records"]}
    if set(records) != set(EXPECTED_COMPONENT_SHA256):
        raise BuildError("A4 component inventory changed")
    components: dict[str, str] = {}
    for component_id, expected_sha in EXPECTED_COMPONENT_SHA256.items():
        begin = f"COMPONENT {component_id} BEGIN\n".encode("utf-8")
        end = f"COMPONENT {component_id} END\n".encode("utf-8")
        if bundle.count(begin) != 1 or bundle.count(end) != 1:
            raise BuildError(f"component marker count changed: {component_id}")
        start = bundle.index(begin) + len(begin)
        finish = bundle.index(end, start)
        raw = bundle[start:finish]
        if sha256_bytes(raw) != expected_sha or records[component_id]["excerpt_sha256"] != expected_sha:
            raise BuildError(f"component SHA changed: {component_id}")
        text = raw.decode("utf-8").replace("\r\n", "\n")
        if "\r" in text or not text.endswith("\n"):
            raise BuildError(f"component line ending changed: {component_id}")
        components[component_id] = text
    return components


def validate_rules(rules: dict[str, Any]) -> None:
    observed = {item["id"]: item for item in rules["rules"]}
    if {rule_id: item["component"] for rule_id, item in observed.items()} != RULE_COMPONENTS:
        raise BuildError("assembly rule inventory changed")
    for rule_id, item in observed.items():
        if "do not create a LOOP" not in item["copy_method"]:
            raise BuildError(f"assembly rule loop guard changed: {rule_id}")
        if not item["line_bindings"] or not item["immutable_parts"] or not item["mutable_parts"]:
            raise BuildError(f"assembly rule is incomplete: {rule_id}")
    events = rules["control_events"]
    if [item["sequence"] for item in events] != list(range(1, 14)):
        raise BuildError("control event sequence changed")
    control = rules["control_validation"]
    if not control["balanced"] or control["failure_close_count"] != 2 or control["failure_save_as_count"] != 0:
        raise BuildError("control validation changed")


def validate_fixed_sources() -> tuple[dict[str, str], dict[str, str], dict[str, Any]]:
    paths = {
        "bundle": BUNDLE,
        "wiring": WIRING,
        "assembly_rules": ASSEMBLY_RULES,
        "a4_manifest": A4_MANIFEST,
        "helper": HELPER,
        "invocation": INVOCATION,
        "launcher": LAUNCHER,
        "fixed_request": FIXED_REQUEST,
        "fixed_spec": FIXED_SPEC,
        "fixed_expected": FIXED_EXPECTED,
    }
    actual = {name: sha256(path) for name, path in paths.items()}
    if actual != EXPECTED_SHA256:
        raise BuildError(f"fixed source SHA mismatch: {actual}")
    manifest = load_json(A4_MANIFEST)
    rules = load_json(ASSEMBLY_RULES)
    if manifest["candidate_id"] != "20260918-excel-r12-fixed-helper-a4":
        raise BuildError("A4 manifest identity changed")
    if manifest["artifacts"]["wiring_spec"]["sha256"] != actual["wiring"]:
        raise BuildError("A4 manifest wiring SHA changed")
    if manifest["artifacts"]["assembly_rules"]["sha256"] != actual["assembly_rules"]:
        raise BuildError("A4 manifest assembly-rules SHA changed")
    validate_rules(rules)
    components = extract_components(BUNDLE.read_bytes(), manifest)
    return actual, components, rules


def source_key(mapping: dict[str, Any]) -> tuple[str, str, str]:
    return mapping["input_workbook"], mapping["input_sheet"], mapping["input_cell"]


def target_key(mapping: dict[str, Any], text: bool) -> tuple[str, str]:
    if text:
        return mapping["helper_target_sheet"], mapping["helper_target_cell"]
    return mapping["target_sheet"], mapping["target_cell"]


def validate_wiring(spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("spec_id") != "EX03-R12-FIXED-HELPER-A4-WIRING":
        raise BuildError("fixed WIRING spec identity changed")
    if spec.get("candidate_id") != "20260918-excel-r12-fixed-helper-a4":
        raise BuildError("fixed WIRING candidate identity changed")
    if spec.get("scope") != "FIXED_EX03_ONLY_NOT_GENERALIZED":
        raise BuildError("fixed WIRING scope changed")
    if spec["inputs"] != [{key: item[key] for key in ("input_id", "workbook", "sheet", "range", "data_table_variable")} for item in EXPECTED_INPUTS]:
        raise BuildError("fixed input rectangles changed")

    runtime = spec["runtime"]
    required_runtime = {
        "fixed_work_absolute": str(BASE / "runs/EX03-attempt1/work.xlsx"),
        "issue_root": str(BASE),
        "fixed_work_relative": "runs/EX03-attempt1/work.xlsx",
        "fixed_output_absolute": str(BASE / "runs/EX03-attempt1/照合結果.xlsx"),
        "fixed_output_relative": "runs/EX03-attempt1/照合結果.xlsx",
        "a4_json_root_absolute": str(BASE / "runs/EX03-attempt1/a4-helper-json"),
        "a4_json_root_relative": "runs/EX03-attempt1/a4-helper-json",
        "mode_json_file": "mode.json",
        "mode_source_variable": "RunMode",
        "normal_mode_literal": "NORMAL",
        "helper_path": str(HELPER),
        "helper_sha256": EXPECTED_SHA256["helper"],
        "invocation_path": str(INVOCATION),
        "invocation_sha256": EXPECTED_SHA256["invocation"],
        "launcher_path": str(LAUNCHER),
        "launcher_sha256": EXPECTED_SHA256["launcher"],
    }
    for key, expected in required_runtime.items():
        if runtime.get(key) != expected:
            raise BuildError(f"fixed runtime field changed: {key}")

    text = spec.get("text_mappings", [])
    numeric = spec.get("numeric_mappings", [])
    readbacks = spec.get("readbacks", [])
    comparisons = spec.get("comparison_contract", {}).get("positions", [])
    if len(text) != 7 or len(numeric) != 5 or len(readbacks) != 2 or len(comparisons) != 12:
        raise BuildError("mapping count missing: expected 7 text, 5 numeric, 2 readbacks, 12 comparisons")
    if spec["comparison_contract"].get("count") != 12 or spec["comparison_contract"].get("order") != "input rectangles in request order, each rectangle row-major":
        raise BuildError("comparison count/order contract changed")

    text_sources = [source_key(item) for item in text]
    numeric_sources = [source_key(item) for item in numeric]
    text_targets = [target_key(item, True) for item in text]
    numeric_targets = [target_key(item, False) for item in numeric]
    if len(set(text_sources + numeric_sources)) != 12:
        raise BuildError("duplicate source mapping")
    if len(set(text_targets + numeric_targets)) != 12:
        raise BuildError("duplicate target mapping")

    inputs = {item["input_id"]: item for item in EXPECTED_INPUTS}
    expected_text = []
    for index, item in enumerate(text, 1):
        input_definition = inputs[item["input_id"]]
        expected_position = EXPECTED_TEXT_POSITIONS[index - 1]
        if (item["input_id"], item["input_cell"], item["helper_target_sheet"], item["helper_target_cell"]) != expected_position:
            raise BuildError(f"text mapping coordinate changed at {index}")
        expected_index = cell_index(item["input_cell"], input_definition["range"])
        expected_reference = f'{input_definition["data_table_variable"]}[{expected_index[0]}][{expected_index[1]}]'
        if item["input_workbook"] != input_definition["workbook"] or item["input_sheet"] != input_definition["sheet"]:
            raise BuildError(f"text mapping source changed at {index}")
        if item["data_table_variable"] != input_definition["data_table_variable"] or item["data_table_index"] != expected_index or item["source_reference"] != expected_reference:
            raise BuildError(f"text mapping DataTable reference changed at {index}")
        expected_json_file = f"source-{index}.json"
        expected_json_path = str(Path(runtime["a4_json_root_absolute"]) / expected_json_file)
        if item["helper_source_index"] != index or item["source_json_file"] != expected_json_file or item["source_json_path"] != expected_json_path:
            raise BuildError(f"text mapping JSON/helper slot changed at {index}")
        expected_text.append((item["source_reference"], item["source_json_path"], item["helper_target_sheet"], item["helper_target_cell"]))

    expected_numeric = []
    for index, item in enumerate(numeric, 1):
        input_definition = inputs[item["input_id"]]
        expected_position = EXPECTED_NUMERIC_POSITIONS[index - 1]
        if item["order"] != index or (item["input_id"], item["input_cell"], item["target_sheet"], item["target_cell"]) != expected_position:
            raise BuildError(f"numeric mapping coordinate changed at {index}")
        expected_index = cell_index(item["input_cell"], input_definition["range"])
        expected_reference = f'{input_definition["data_table_variable"]}[{expected_index[0]}][{expected_index[1]}]'
        if item["input_workbook"] != input_definition["workbook"] or item["input_sheet"] != input_definition["sheet"]:
            raise BuildError(f"numeric mapping source changed at {index}")
        if item["data_table_variable"] != input_definition["data_table_variable"] or item["data_table_index"] != expected_index or item["source_reference"] != expected_reference:
            raise BuildError(f"numeric mapping DataTable reference changed at {index}")
        expected_numeric.append((item["source_reference"], item["target_sheet"], item["target_cell"]))

    expected_readbacks = [
        {"order": 1, "sheet": "集計先", "range": "F7:G9", "variable": "Readback1", "rows": 3, "columns": 2},
        {"order": 2, "sheet": "追記先", "range": "D5:F6", "variable": "Readback2", "rows": 2, "columns": 3},
    ]
    if readbacks != expected_readbacks:
        raise BuildError("readback rectangles changed")

    comparison_sources: list[tuple[str, str, str]] = []
    comparison_targets: list[tuple[str, str]] = []
    for index, item in enumerate(comparisons, 1):
        expected_position = EXPECTED_COMPARISON_POSITIONS[index - 1]
        input_definition = inputs[expected_position[0]]
        saved_rectangle = next(readback for readback in readbacks if readback["sheet"] == expected_position[2])
        expected_source_index = cell_index(expected_position[1], input_definition["range"])
        expected_saved_index = cell_index(expected_position[3], saved_rectangle["range"])
        expected_source_reference = f'{input_definition["data_table_variable"]}[{expected_source_index[0]}][{expected_source_index[1]}]'
        expected_saved_reference = f'{saved_rectangle["variable"]}[{expected_saved_index[0]}][{expected_saved_index[1]}]'
        observed_position = (
            item["source_workbook"], item["source_sheet"], item["source_cell"],
            item["saved_sheet"], item["saved_cell"], item["kind"],
        )
        required_position = (
            input_definition["workbook"], input_definition["sheet"], expected_position[1],
            expected_position[2], expected_position[3], expected_position[4],
        )
        if item["order"] != index or observed_position != required_position:
            raise BuildError(f"comparison coordinate/order changed at {index}")
        if item["source_reference"] != expected_source_reference or item["saved_reference"] != expected_saved_reference:
            raise BuildError(f"comparison variable reference changed at {index}")
        if not item["source_and_saved_positions_immutable"] or not item["per_position_variable_names_may_be_generated"]:
            raise BuildError(f"comparison immutability changed at {index}")
        comparison_sources.append((item["source_workbook"], item["source_sheet"], item["source_cell"]))
        comparison_targets.append((item["saved_sheet"], item["saved_cell"]))

    if set(comparison_sources) != set(text_sources + numeric_sources) or set(comparison_targets) != set(text_targets + numeric_targets):
        raise BuildError("comparison coverage differs from transfer mappings")
    contract = spec["generation_contract"]
    if not contract["explicit_copy_and_connection_from_captured_components_allowed"]:
        raise BuildError("explicit component assembly is no longer allowed")
    if contract["unknown_action_argument_enum_or_control_fabrication_allowed"] or contract["new_pad_loop_allowed"] or contract["cell_or_grader_values_included"]:
        raise BuildError("fixed generation safety contract changed")

    invocation = load_json(INVOCATION)
    if set(invocation) != {"schema_version", "prototype_id", "scope", "target_workbook", "json_root", "text_writes"}:
        raise BuildError("fixed invocation keys changed")
    if invocation["prototype_id"] != "EX03-R12-FIXED-HELPER-A4-VERIFIER" or invocation["scope"] != "FIXED_EX03_ONLY_NOT_GENERALIZED":
        raise BuildError("fixed invocation identity changed")
    projected_writes = [
        {
            "source_index": item["helper_source_index"],
            "source_label": item["source_reference"],
            "sheet": item["helper_target_sheet"],
            "cell": item["helper_target_cell"],
        }
        for item in text
    ]
    if invocation["target_workbook"] != runtime["fixed_work_absolute"] or invocation["json_root"] != runtime["a4_json_root_absolute"] or invocation["text_writes"] != projected_writes:
        raise BuildError("fixed invocation is not an exact WIRING projection")

    return {
        "text_count": len(text),
        "numeric_count": len(numeric),
        "readback_count": len(readbacks),
        "comparison_count": len(comparisons),
        "source_coverage_count": len(set(text_sources + numeric_sources)),
        "target_coverage_count": len(set(text_targets + numeric_targets)),
        "text_mappings": expected_text,
        "numeric_mappings": expected_numeric,
    }


class Renderer:
    def __init__(self, components: dict[str, str]):
        self.components = components
        self.lines = {name: value.rstrip("\n").split("\n") for name, value in components.items()}
        self.replacements: list[dict[str, Any]] = []

    def exact(self, component: str) -> list[str]:
        return list(self.lines[component])

    def line(
        self,
        component: str,
        line_index: int,
        slot: str,
        parameters: list[tuple[str, str, str]],
        indent: int | None = None,
    ) -> str:
        template = self.lines[component][line_index]
        value = template
        parameter_names: list[str] = []
        replacement_records: list[dict[str, str]] = []
        for name, before, after in parameters:
            if name not in ALLOWED_PARAMETERS[component]:
                raise BuildError(f"undeclared parameter for {component}: {name}")
            if value.count(before) != 1:
                raise BuildError(f"template token count changed for {component}/{slot}/{name}")
            value = value.replace(before, after)
            parameter_names.append(name)
            replacement_records.append({"parameter": name, "before": before, "after": after})
        if indent is not None:
            if "indent" not in ALLOWED_PARAMETERS[component]:
                raise BuildError(f"indent is not declared for {component}")
            value = " " * indent + value.lstrip(" ")
            parameter_names.append("indent")
        self.replacements.append({
            "component": component,
            "assembly_rule": (
                "AR09_EXPLICIT_NUMERIC_WRITES"
                if component == "C04_JSON_FILE_HANDOFF" and slot.startswith("number_")
                else next((rule_id for rule_id, rule_component in RULE_COMPONENTS.items() if rule_component == component), None)
            ),
            "slot": slot,
            "template_line_sha256": sha256_bytes((template + "\n").encode("utf-8")),
            "parameters": parameter_names,
            "replacements": replacement_records,
            "result_line_sha256": sha256_bytes((value + "\n").encode("utf-8")),
        })
        return value


def render_c06(components: dict[str, str], launcher: bytes) -> str:
    if sha256_bytes(launcher) != EXPECTED_SHA256["launcher"]:
        raise BuildError("fixed launcher SHA mismatch before generation")
    if not launcher.endswith(b"\n") or b"\r" in launcher:
        raise BuildError("fixed launcher must remain LF-only with one terminal LF")
    launcher_text = launcher.decode("utf-8")
    required = (str(HELPER), str(INVOCATION), EXPECTED_SHA256["helper"], EXPECTED_SHA256["invocation"], EXPECTED_SUCCESS)
    if any(item not in launcher_text for item in required):
        raise BuildError("fixed launcher identity content changed")
    prefix = "    Scripting.RunPowershellScript.RunScript Script: $'''"
    suffix = "''' ScriptOutput=> PowershellOutput\n"
    rendered = prefix + encode_robin_string(launcher_text[:-1]) + suffix
    if rendered != components["C06_FIXED_LAUNCHER_RUNSCRIPT"]:
        raise BuildError("fixed launcher no longer reproduces C06 component")
    if embedded_script(rendered).encode("utf-8") + b"\n" != launcher:
        raise BuildError("decoded C06 launcher differs under the fixed newline rule")
    return rendered.rstrip("\n")


def control_balance(lines: list[str]) -> bool:
    stack: list[bool] = []
    for line in lines:
        value = line.strip()
        if value.startswith("IF ") and value.endswith(" THEN"):
            stack.append(False)
        elif value == "ELSE":
            if not stack or stack[-1]:
                return False
            stack[-1] = True
        elif value == "END":
            if not stack:
                return False
            stack.pop()
    return not stack


def audit_robin(robin: bytes, spec: dict[str, Any], launcher: bytes) -> dict[str, Any]:
    if b"\r" in robin or not robin.endswith(b"\n"):
        raise BuildError("generated Robin must be UTF-8 LF-only with a terminal LF")
    text = robin.decode("utf-8")
    lines = text.rstrip("\n").split("\n")
    if not lines[0].startswith("SET ") or lines[-1] != "END":
        raise BuildError("generated Robin boundary commands changed")
    if not control_balance(lines):
        raise BuildError("generated Robin IF/ELSE/END is unbalanced")

    source_writes = re.findall(r"File\.WriteText File: \$'''([^']*source-(\d)\.json)''' TextToWrite: TextSource(\d)Json", text)
    mode_writes = re.findall(r"File\.WriteText File: \$'''([^']*mode\.json)''' TextToWrite: RunModeJson", text)
    numeric_writes = re.findall(r"Excel\.WriteToExcel\.WriteCell Instance: Work Value: NumberSource(\d+) Column: \$'''([A-Z]+)''' Row: (\d+)", text)
    readbacks = re.findall(r"Excel\.ReadFromExcel\.ReadCells Instance: Reopened StartColumn: \$'''([A-Z]+)''' StartRow: (\d+) EndColumn: \$'''([A-Z]+)''' EndRow: (\d+) GetCellContentsMode: Excel\.GetCellContentsMode\.TypedValues FirstLineIsHeader: False RangeValue=> (Readback\d+)", text)
    comparisons = re.findall(r"SET Position(\d+)ValueTypeMatch TO ([A-Za-z0-9]+Json) = Saved(\d+)Json", text)
    comparison_source_sets = re.findall(r"SET CompareSource(\d+) TO (Data[12]\[\d+\]\[\d+\])", text)
    saved_sets = re.findall(r"SET Saved(\d+) TO (Readback\d+\[\d+\]\[\d+\])", text)
    source_sets = re.findall(r"SET TextSource(\d+) TO (Data[12]\[\d+\]\[\d+\])", text)
    number_sets = re.findall(r"SET NumberSource(\d+) TO (Data[12]\[\d+\]\[\d+\])", text)

    expected_source_sets = [(str(index), item["source_reference"]) for index, item in enumerate(spec["text_mappings"], 1)]
    expected_number_sets = [(str(index), item["source_reference"]) for index, item in enumerate(spec["numeric_mappings"], 1)]
    expected_numeric_writes = []
    for index, item in enumerate(spec["numeric_mappings"], 1):
        column, row = split_cell(item["target_cell"])
        expected_numeric_writes.append((str(index), column, str(row)))
    expected_readbacks = []
    for item in spec["readbacks"]:
        start_column, start_row, end_column, end_row = split_range(item["range"])
        expected_readbacks.append((start_column, str(start_row), end_column, str(end_row), item["variable"]))
    expected_saved_sets = [(str(item["order"]), item["saved_reference"]) for item in spec["comparison_contract"]["positions"]]
    expected_comparison_source_sets = [(str(item["order"]), item["source_reference"]) for item in spec["comparison_contract"]["positions"]]
    expected_comparisons = [
        (str(item["order"]), f'CompareSource{item["order"]}Json', str(item["order"]))
        for item in spec["comparison_contract"]["positions"]
    ]

    json_root = robin_path(spec["runtime"]["a4_json_root_absolute"])
    if source_sets != expected_source_sets or number_sets != expected_number_sets:
        raise BuildError("generated source variable references differ from WIRING")
    if len(source_writes) != 7 or [int(item[1]) for item in source_writes] != list(range(1, 8)) or [int(item[2]) for item in source_writes] != list(range(1, 8)):
        raise BuildError("generated source JSON writes differ from WIRING")
    if not all(item[0].startswith(json_root) for item in source_writes) or len(mode_writes) != 1 or not mode_writes[0].startswith(json_root):
        raise BuildError("generated JSON write root differs from WIRING")
    if numeric_writes != expected_numeric_writes:
        raise BuildError("generated numeric writes differ from WIRING")
    if readbacks != expected_readbacks:
        raise BuildError("generated readbacks differ from WIRING")
    if comparison_source_sets != expected_comparison_source_sets or saved_sets != expected_saved_sets or comparisons != expected_comparisons:
        raise BuildError("generated comparison coordinates or references differ from WIRING")

    output = robin_path(spec["runtime"]["fixed_output_absolute"])
    guard = f"IF (File.IfFile.Exists File: $'''{output}''') THEN"
    success_gate = f"IF PowershellOutput = $'''{encode_robin_string(EXPECTED_SUCCESS)}''' THEN"
    normal_gate = "IF RunMode = $'''NORMAL''' THEN"
    save = "Excel.SaveExcel.SaveAs Instance: Work"
    failure = "        ELSE\n            Excel.CloseExcel.Close Instance: Work"
    positions = {name: text.index(token) for name, token in (
        ("guard", guard),
        ("first_input", "Instance=> SourceBook1"),
        ("work_open", "ReadOnly: False UseMachineLocale: False Instance=> Work"),
        ("runscript", "Scripting.RunPowershellScript.RunScript"),
        ("success", success_gate),
        ("normal", normal_gate),
        ("save", save),
        ("failure", failure),
    )}
    required_order = [positions[name] for name in ("guard", "first_input", "work_open", "runscript", "success", "normal", "save", "failure")]
    if required_order != sorted(required_order):
        raise BuildError("guard/input/work/success/save control order changed")
    if text.count(save) != 1 or save in text[positions["failure"]:]:
        raise BuildError("SaveAs is not confined to the success branch")
    if text.count("Excel.CloseExcel.Close Instance: Work") != 3:
        raise BuildError("Work close count changed")
    if text.count("File.WriteText") != 8 or text.count("Excel.WriteToExcel.WriteCell") != 5 or text.count("RangeValue=> Readback") != 2 or len(comparisons) != 12:
        raise BuildError("required 8/5/2/12 structure changed")
    if text.count("LOOP") or any(text.count(token) for token in FORBIDDEN_RUNTIME):
        raise BuildError("forbidden loop or runtime token generated")

    decoded = embedded_script(text)
    restored = decoded.encode("utf-8") + b"\n"
    if restored != launcher or sha256_bytes(restored) != EXPECTED_SHA256["launcher"]:
        raise BuildError("decoded launcher does not match the fixed SHA")

    return {
        "line_count": len(lines),
        "line_ending": "LF",
        "terminal_lf": True,
        "json_file_write_count": 8,
        "source_json_file_write_count": 7,
        "mode_json_file_write_count": 1,
        "numeric_write_count": 5,
        "readback_rectangle_count": 2,
        "json_value_type_comparison_count": 12,
        "source_variable_reference_count": 12,
        "saved_variable_reference_count": 12,
        "guard_before_inputs_work_and_helper": positions["guard"] < positions["first_input"] < positions["work_open"] < positions["runscript"],
        "save_as_count": 1,
        "save_as_only_after_exact_success_and_normal": positions["success"] < positions["normal"] < positions["save"] < positions["failure"],
        "failure_close_without_save_count": 2,
        "balanced_control_blocks": True,
        "new_pad_loop_count": 0,
        "forbidden_runtime_token_count": 0,
        "decoded_launcher_sha256": sha256_bytes(restored),
        "decoded_launcher_exact": True,
    }


def build(
    *,
    wiring_override: dict[str, Any] | None = None,
    launcher_override: bytes | None = None,
) -> BuildResult:
    actual_sha, components, rules = validate_fixed_sources()
    spec = deepcopy(wiring_override) if wiring_override is not None else load_json(WIRING)
    wiring_validation = validate_wiring(spec)
    launcher = launcher_override if launcher_override is not None else LAUNCHER.read_bytes()
    if sha256_bytes(launcher) != EXPECTED_SHA256["launcher"]:
        raise BuildError("fixed launcher SHA mismatch before generation")

    embedded_begin = b"A4_WIRING_SPEC_JSON_BEGIN\n"
    embedded_end = b"\nA4_WIRING_SPEC_JSON_END"
    bundle_bytes = BUNDLE.read_bytes()
    if bundle_bytes.count(embedded_begin) != 1 or bundle_bytes.count(embedded_end) != 1:
        raise BuildError("embedded WIRING markers changed")
    embedded = bundle_bytes.split(embedded_begin, 1)[1].split(embedded_end, 1)[0]
    if json.loads(embedded.decode("utf-8")) != spec:
        raise BuildError("bundle WIRING differs from the generation input")

    renderer = Renderer(components)
    output_lines: list[str] = []
    output_lines.extend(renderer.exact("C01_STATE_INIT"))

    c02 = renderer.lines["C02_OUTPUT_GUARD"]
    old_guard_path = re.search(r"File: \$'''([^']+)'''", c02[0]).group(1)
    output_lines.append(renderer.line("C02_OUTPUT_GUARD", 0, "guard", [("guard_path", old_guard_path, robin_path(spec["runtime"]["fixed_output_absolute"]))]))
    output_lines.extend(c02[1:])

    c03 = renderer.lines["C03_READONLY_TYPED_RANGE"]
    old_input_path = re.search(r"Path: \$'''([^']+)'''", c03[0]).group(1)
    for item in EXPECTED_INPUTS:
        start_column, start_row, end_column, end_row = split_range(item["range"])
        input_path = BASE / item["workbook"]
        output_lines.append(renderer.line("C03_READONLY_TYPED_RANGE", 0, item["input_id"] + "_open", [
            ("input_path", old_input_path, robin_path(input_path)),
            ("instance_name", "SourceBook", item["instance"]),
        ]))
        output_lines.append(renderer.line("C03_READONLY_TYPED_RANGE", 1, item["input_id"] + "_sheet", [
            ("instance_name", "SourceBook", item["instance"]),
            ("sheet", "Name: $'''Source'''", f"Name: $'''{item['sheet']}'''")
        ]))
        output_lines.append(renderer.line("C03_READONLY_TYPED_RANGE", 2, item["input_id"] + "_range", [
            ("instance_name", "SourceBook", item["instance"]),
            ("start_column", "StartColumn: $'''A'''", f"StartColumn: $'''{start_column}'''") ,
            ("start_row", "StartRow: 2", f"StartRow: {start_row}"),
            ("end_column", "EndColumn: $'''D'''", f"EndColumn: $'''{end_column}'''") ,
            ("end_row", "EndRow: 2", f"EndRow: {end_row}"),
            ("range_variable", "RangeValue=> SourceData", f"RangeValue=> {item['data_table_variable']}")
        ]))
        output_lines.append(renderer.line("C03_READONLY_TYPED_RANGE", 3, item["input_id"] + "_close", [
            ("instance_name", "SourceBook", item["instance"]),
        ]))

    c04 = renderer.lines["C04_JSON_FILE_HANDOFF"]
    set_template_index = 0
    convert_template_index = 4
    source_write_template_index = 10
    old_source_json_path = re.search(r"File: \$'''([^']+)'''", c04[source_write_template_index]).group(1)
    for index, mapping in enumerate(spec["text_mappings"], 1):
        output_lines.append(renderer.line("C04_JSON_FILE_HANDOFF", set_template_index, f"text_{index}_set", [
            ("source_variable", "SET Source1 TO", f"SET TextSource{index} TO"),
            ("source_reference", "SourceData[0][0]", mapping["source_reference"]),
        ]))
    for index in range(1, 8):
        output_lines.append(renderer.line("C04_JSON_FILE_HANDOFF", convert_template_index, f"text_{index}_json", [
            ("source_variable", "CustomObject: { 'probe': Source1 }", f"CustomObject: {{ 'probe': TextSource{index} }}"),
            ("source_json_variable", "Json=> Source1Json", f"Json=> TextSource{index}Json"),
        ]))
    output_lines.extend(c04[8:10])
    for index, mapping in enumerate(spec["text_mappings"], 1):
        output_lines.append(renderer.line("C04_JSON_FILE_HANDOFF", source_write_template_index, f"text_{index}_write", [
            ("json_path", old_source_json_path, robin_path(mapping["source_json_path"])),
            ("source_json_variable", "TextToWrite: Source1Json", f"TextToWrite: TextSource{index}Json"),
        ]))
    old_mode_path = re.search(r"File: \$'''([^']+)'''", c04[14]).group(1)
    output_lines.append(renderer.line("C04_JSON_FILE_HANDOFF", 14, "mode_write", [
        ("json_path", old_mode_path, robin_path(Path(spec["runtime"]["a4_json_root_absolute"]) / spec["runtime"]["mode_json_file"])),
    ]))

    c05 = renderer.lines["C05_EDITABLE_WORK_OPEN"]
    old_work_path = re.search(r"Path: \$'''([^']+)'''", c05[0]).group(1)
    output_lines.append(renderer.line("C05_EDITABLE_WORK_OPEN", 0, "work_open", [
        ("work_path", old_work_path, robin_path(spec["runtime"]["fixed_work_absolute"])),
    ]))
    output_lines.extend(render_c06(components, launcher).split("\n"))
    output_lines.extend(renderer.exact("C07_EXACT_SUCCESS_MODE_GATE"))

    for index, mapping in enumerate(spec["numeric_mappings"], 1):
        output_lines.append(renderer.line("C04_JSON_FILE_HANDOFF", set_template_index, f"number_{index}_set", [
            ("source_variable", "SET Source1 TO", f"SET NumberSource{index} TO"),
            ("source_reference", "SourceData[0][0]", mapping["source_reference"]),
        ], indent=12))
    c08 = renderer.lines["C08_TARGET_SHEET_ACTIVATION"]
    c09 = renderer.lines["C09_NUMERIC_WRITE"]
    current_sheet: str | None = None
    marker_written = False
    for index, mapping in enumerate(spec["numeric_mappings"], 1):
        if mapping["target_sheet"] != current_sheet:
            output_lines.append(renderer.line("C08_TARGET_SHEET_ACTIVATION", 0, f"number_{index}_sheet", [
                ("target_sheet", "Name: $'''Target'''", f"Name: $'''{mapping['target_sheet']}'''")
            ], indent=12))
            current_sheet = mapping["target_sheet"]
            if not marker_written:
                output_lines.append(c09[0])
                marker_written = True
        target_column, target_row = split_cell(mapping["target_cell"])
        output_lines.append(renderer.line("C09_NUMERIC_WRITE", 1, f"number_{index}_write", [
            ("source_variable", "Value: Source4", f"Value: NumberSource{index}"),
            ("target_column", "Column: $'''D'''", f"Column: $'''{target_column}'''") ,
            ("target_row", "Row: 2", f"Row: {target_row}"),
        ], indent=12))

    c10 = renderer.lines["C10_SAVE_CLOSE_REOPEN_READBACK"]
    output_lines.append(c10[0])
    old_save_path = re.search(r"DocumentPath: \$'''([^']+)'''", c10[1]).group(1)
    output_lines.append(renderer.line("C10_SAVE_CLOSE_REOPEN_READBACK", 1, "save_as", [
        ("output_path", old_save_path, robin_path(spec["runtime"]["fixed_output_absolute"])),
    ]))
    output_lines.append(c10[2])
    old_reopen_path = re.search(r"Path: \$'''([^']+)'''", c10[3]).group(1)
    output_lines.append(renderer.line("C10_SAVE_CLOSE_REOPEN_READBACK", 3, "reopen", [
        ("output_path", old_reopen_path, robin_path(spec["runtime"]["fixed_output_absolute"])),
    ]))
    for readback in spec["readbacks"]:
        start_column, start_row, end_column, end_row = split_range(readback["range"])
        output_lines.append(renderer.line("C10_SAVE_CLOSE_REOPEN_READBACK", 4, f"readback_{readback['order']}_sheet", [
            ("sheet", "Name: $'''Target'''", f"Name: $'''{readback['sheet']}'''")
        ]))
        output_lines.append(renderer.line("C10_SAVE_CLOSE_REOPEN_READBACK", 5, f"readback_{readback['order']}_range", [
            ("start_column", "StartColumn: $'''A'''", f"StartColumn: $'''{start_column}'''") ,
            ("start_row", "StartRow: 2", f"StartRow: {start_row}"),
            ("end_column", "EndColumn: $'''D'''", f"EndColumn: $'''{end_column}'''") ,
            ("end_row", "EndRow: 2", f"EndRow: {end_row}"),
            ("readback_variable", "RangeValue=> Readback", f"RangeValue=> {readback['variable']}")
        ]))
    output_lines.append(c10[6])

    c11 = renderer.lines["C11_JSON_VALUE_TYPE_COMPARE"]
    for position in spec["comparison_contract"]["positions"]:
        index = position["order"]
        output_lines.append(renderer.line("C11_JSON_VALUE_TYPE_COMPARE", 0, f"position_{index}_source", [
            ("source_variable", "SET Saved1 TO", f"SET CompareSource{index} TO"),
            ("source_reference", "Readback[0][0]", position["source_reference"]),
        ]))
        output_lines.append(renderer.line("C11_JSON_VALUE_TYPE_COMPARE", 0, f"position_{index}_saved", [
            ("saved_variable", "SET Saved1 TO", f"SET Saved{index} TO"),
            ("saved_reference", "Readback[0][0]", position["saved_reference"]),
        ]))
    for position in spec["comparison_contract"]["positions"]:
        index = position["order"]
        output_lines.append(renderer.line("C11_JSON_VALUE_TYPE_COMPARE", 4, f"position_{index}_source_json", [
            ("source_variable", "CustomObject: { 'probe': Saved1 }", f"CustomObject: {{ 'probe': CompareSource{index} }}"),
            ("source_json_variable", "Json=> Saved1Json", f"Json=> CompareSource{index}Json"),
        ]))
        output_lines.append(renderer.line("C11_JSON_VALUE_TYPE_COMPARE", 4, f"position_{index}_saved_json", [
            ("saved_variable", "CustomObject: { 'probe': Saved1 }", f"CustomObject: {{ 'probe': Saved{index} }}"),
            ("saved_json_variable", "Json=> Saved1Json", f"Json=> Saved{index}Json"),
        ]))
    for position in spec["comparison_contract"]["positions"]:
        index = position["order"]
        output_lines.append(renderer.line("C11_JSON_VALUE_TYPE_COMPARE", 8, f"position_{index}_compare", [
            ("result_variable", "SET Source1VsSaved TO", f"SET Position{index}ValueTypeMatch TO"),
            ("source_json_variable", "Source1Json", f"CompareSource{index}Json"),
            ("saved_json_variable", "Saved1Json", f"Saved{index}Json"),
        ]))
    output_lines.append(c11[12])
    output_lines.extend(renderer.exact("C12_FAILURE_CLOSE_NO_SAVE"))

    robin = ("\n".join(output_lines) + "\n").encode("utf-8")
    structure = audit_robin(robin, spec, launcher)
    replacement_bytes = json.dumps(renderer.replacements, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    verification = {
        "schema_version": 1,
        "prototype_id": PROTOTYPE_ID,
        "source_commit": SOURCE_COMMIT,
        "status": "PASS_LIMITED_NON_LIVE_MECHANICAL_BUILD_ONLY_NOT_COPILOT_OR_PAD_ACCEPTANCE",
        "inputs": {
            name: {"path": relative(path), "sha256": actual_sha[name]}
            for name, path in {
                "bundle": BUNDLE,
                "wiring": WIRING,
                "assembly_rules": ASSEMBLY_RULES,
                "a4_manifest": A4_MANIFEST,
                "helper": HELPER,
                "invocation": INVOCATION,
                "launcher": LAUNCHER,
                "fixed_request": FIXED_REQUEST,
                "fixed_spec": FIXED_SPEC,
                "fixed_expected": FIXED_EXPECTED,
            }.items()
        },
        "component_sources": {
            "count": len(components),
            "ids": list(EXPECTED_COMPONENT_SHA256),
            "sha256": EXPECTED_COMPONENT_SHA256,
        },
        "assembly_rules": {
            "count": len(RULE_COMPONENTS),
            "ids": list(RULE_COMPONENTS),
            "sha256": actual_sha["assembly_rules"],
            "control_event_count": len(rules["control_events"]),
            "new_loop_allowed": False,
        },
        "declared_parameters": {name: sorted(values) for name, values in ALLOWED_PARAMETERS.items()},
        "replacement_record_count": len(renderer.replacements),
        "replacement_records_sha256": sha256_bytes(replacement_bytes),
        "wiring_validation": wiring_validation,
        "structure": structure,
        "generated": {
            "path": relative(OUTPUT),
            "sha256": sha256_bytes(robin),
            "bytes": len(robin),
            "deterministic_inputs_only": True,
        },
        "boundaries": {
            "fixed_expected_values_used_for_generation": False,
            "a4_copilot_generated_robin_used_for_generation": False,
            "a4_generated_robin_modified": False,
            "helper_invocation_launcher_or_wiring_modified": False,
            "copilot_send_count": 0,
            "pad_save_recopy_count": 0,
            "pad_run_count": 0,
            "excel_run_count": 0,
            "full_regression": "NOT_RUN_BY_SCOPE",
            "github_write_count": 0,
            "copilot_generation_pass_inherited": False,
            "ex03_acceptance_pass_claimed": False,
        },
    }
    return BuildResult(robin=robin, verification=verification, replacements=tuple(renderer.replacements))


def verification_bytes(result: BuildResult) -> bytes:
    return (json.dumps(result.verification, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def write_new(result: BuildResult) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists() or VERIFICATION.exists():
        raise FileExistsError("mechanical builder output already exists; use --check")
    with OUTPUT.open("xb") as handle:
        handle.write(result.robin)
    with VERIFICATION.open("xb") as handle:
        handle.write(verification_bytes(result))


def check_existing(result: BuildResult) -> None:
    if not OUTPUT.is_file() or not VERIFICATION.is_file():
        raise FileNotFoundError("mechanical builder output is absent; initialize once with --write")
    if OUTPUT.read_bytes() != result.robin:
        raise BuildError("regenerated Robin is not byte-identical to the committed output")
    if VERIFICATION.read_bytes() != verification_bytes(result):
        raise BuildError("regenerated verification is not byte-identical to the committed output")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="create the fixed output and verification once")
    mode.add_argument("--check", action="store_true", help="regenerate in memory and require byte identity")
    arguments = parser.parse_args()
    result = build()
    if arguments.write:
        write_new(result)
        operation = "WRITE_NEW"
    else:
        check_existing(result)
        operation = "CHECK_BYTE_IDENTICAL"
    print(json.dumps({
        "status": result.verification["status"],
        "operation": operation,
        "prototype_id": PROTOTYPE_ID,
        "generated_sha256": result.verification["generated"]["sha256"],
        "json_writes": result.verification["structure"]["json_file_write_count"],
        "numeric_writes": result.verification["structure"]["numeric_write_count"],
        "readbacks": result.verification["structure"]["readback_rectangle_count"],
        "comparisons": result.verification["structure"]["json_value_type_comparison_count"],
        "pad_runs": result.verification["boundaries"]["pad_run_count"],
    }, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
