"""Finalize the separately identified EX03-r11 downloaded-file PAD evidence."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1"
FORMAL = ROOT / "catalog/acceptance/issue38/cycles/EX03-r11-G1"
RUNTIME = ROOT / "catalog/acceptance/issue38/runs/EX03-attempt1"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
SPEC = BASE / "spec.json"
EXPECTED = BASE / "expected.json"
EXPECTED_SPEC_SHA = "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380"
EXPECTED_VALUES_SHA = "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d"
EXPECTED_WORK_SHA = "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21"
EXPECTED_GENERATED_SHA = "a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875"
EXPECTED_LEGACY_COUNTS = {"styles": 480, "row_dimensions": 48, "column_dimensions": 30}
EXPECTED_NATIVE_COUNTS = {
    "cell_style": 0,
    "row_dimension": 0,
    "column_dimension": 0,
    "sheet_structure": 0,
}
EXPECTED_NATIVE_ATTRIBUTES = {
    "cell": [
        "font",
        "fill",
        "number_format",
        "alignment",
        "protection",
        "merge_cells",
        "invariant style_name",
        "six edge and diagonal borders",
    ],
    "row": ["height", "hidden"],
    "column": ["width", "hidden"],
}
EXPECTED_EXCLUDED_TYPES = [
    "blank",
    "boolean",
    "date",
    "error",
    "formula-result",
    "object",
]
FORMAT_ROWS_PER_SHEET = 16
FORMAT_COLUMNS_PER_SHEET = 10
FORMAL_FAILURE = "FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD"
CELL_PATTERN = re.compile(r"^([A-Z]+)([1-9][0-9]*)$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def require_keys(value: object, keys: set[str], label: str) -> dict:
    require(isinstance(value, dict), f"{label} must be an object")
    missing = sorted(keys - set(value))
    require(not missing, f"{label} missing required keys: {missing}")
    return value


def recorded_path(value: object, label: str) -> Path:
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be a path")
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path.resolve()


def path_is(value: object, expected: Path, label: str) -> bool:
    return recorded_path(value, label) == expected.resolve()


def column_number(value: str) -> int:
    result = 0
    for character in value:
        result = result * 26 + ord(character) - ord("A") + 1
    return result


def column_name(value: int) -> str:
    result = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def cell_parts(value: str, label: str) -> tuple[int, int]:
    require(isinstance(value, str), f"{label} must be a cell address")
    match = CELL_PATTERN.fullmatch(value)
    require(match is not None, f"{label} is not an A1 cell address: {value!r}")
    return int(match.group(2)), column_number(match.group(1))


def typed_value(value: object) -> list[object]:
    if isinstance(value, bool):
        raise ValueError("Boolean is outside the fixed EX03 text/number scope")
    if isinstance(value, (int, float)):
        return ["number", value]
    if isinstance(value, str):
        return ["text", value]
    raise ValueError(f"Unsupported fixed EX03 expected value: {value!r}")


def fixed_contract() -> dict:
    require(sha256(SPEC) == EXPECTED_SPEC_SHA, "fixed spec SHA mismatch")
    require(sha256(EXPECTED) == EXPECTED_VALUES_SHA, "fixed expected-values SHA mismatch")
    spec_document = require_keys(load(SPEC), {"schema_version", "cases"}, "spec")
    expected_document = require_keys(
        load(EXPECTED), {"schema_version", "grader_only", "matrices"}, "expected"
    )
    require(spec_document["schema_version"] == 1, "spec schema mismatch")
    require(expected_document["schema_version"] == 1, "expected schema mismatch")
    require(expected_document["grader_only"] is True, "expected grader-only boundary mismatch")
    require(isinstance(spec_document["cases"], list), "spec cases must be an array")
    matrices_document = require_keys(expected_document["matrices"], {"EX03"}, "expected matrices")
    cases = [
        item
        for item in spec_document["cases"]
        if isinstance(item, dict) and item.get("id") == "EX03"
    ]
    require(len(cases) == 1, "spec must contain exactly one EX03 case")
    case = require_keys(
        cases[0], {"id", "inputs", "template", "output", "initial_sheet"}, "EX03 spec"
    )
    require(isinstance(case["inputs"], list), "EX03 inputs must be an array")
    matrices = matrices_document["EX03"]
    require(isinstance(matrices, list), "expected matrices must contain EX03")
    require(len(case["inputs"]) == len(matrices), "EX03 input/matrix count mismatch")

    mappings = []
    for input_index, (item, matrix) in enumerate(zip(case["inputs"], matrices)):
        item = require_keys(
            item,
            {"file", "sheet", "range", "target_sheet", "target_start"},
            f"EX03 input {input_index}",
        )
        require(isinstance(item["range"], str) and ":" in item["range"], "Invalid EX03 range")
        source_start, source_end = item["range"].split(":", 1)
        source_r1, source_c1 = cell_parts(source_start, "source range start")
        source_r2, source_c2 = cell_parts(source_end, "source range end")
        target_r1, target_c1 = cell_parts(item["target_start"], "target start")
        rows = source_r2 - source_r1 + 1
        columns = source_c2 - source_c1 + 1
        require(rows > 0 and columns > 0, "EX03 range must be forward and non-empty")
        require(isinstance(matrix, list) and len(matrix) == rows, "EX03 expected row count mismatch")
        for row_offset, expected_row in enumerate(matrix):
            require(
                isinstance(expected_row, list) and len(expected_row) == columns,
                "EX03 expected column count mismatch",
            )
            for column_offset, expected_value in enumerate(expected_row):
                mappings.append(
                    {
                        "source_path": item["file"],
                        "source_sheet": item["sheet"],
                        "source_cell": (
                            f"{column_name(source_c1 + column_offset)}{source_r1 + row_offset}"
                        ),
                        "target_sheet": item["target_sheet"],
                        "target_cell": (
                            f"{column_name(target_c1 + column_offset)}{target_r1 + row_offset}"
                        ),
                        "grader_expected": typed_value(expected_value),
                    }
                )
    require(len(mappings) == 12, f"Fixed EX03 mapping count must be 12, found {len(mappings)}")

    source_paths = sorted({mapping["source_path"] for mapping in mappings})
    source_hashes = {path: sha256(BASE / path) for path in source_paths}
    sheet_names = [case["initial_sheet"]]
    for item in case["inputs"]:
        if item["target_sheet"] not in sheet_names:
            sheet_names.append(item["target_sheet"])
    return {
        "case": case,
        "mappings": mappings,
        "source_hashes": source_hashes,
        "template": BASE / case["template"],
        "sheet_names": sheet_names,
        "target_coordinates": {
            (mapping["target_sheet"], mapping["target_cell"]) for mapping in mappings
        },
    }


def validate_artifact(artifact: dict, result: Path, work: Path) -> tuple[str, str]:
    require_keys(
        artifact,
        {
            "schema_version",
            "runtime_output_path",
            "preserved_output_path",
            "output_sha256",
            "output_bytes",
            "preserved_output_exact",
            "runtime_work_path",
            "preserved_work_path",
            "work_sha256",
            "preserved_work_exact",
            "status",
        },
        "artifact",
    )
    require(result.is_file(), f"Missing preserved result: {result}")
    require(work.is_file(), f"Missing preserved work: {work}")
    result_sha = sha256(result)
    work_sha = sha256(work)
    require(artifact["schema_version"] == 1, "artifact schema mismatch")
    require(artifact["status"] == "PASS_ARTIFACT_PRESERVED", "artifact status mismatch")
    require(artifact["preserved_output_exact"] is True, "artifact output exact flag mismatch")
    require(artifact["preserved_work_exact"] is True, "artifact work exact flag mismatch")
    require(artifact["output_sha256"] == result_sha, "artifact output SHA mismatch")
    require(artifact["output_bytes"] == result.stat().st_size, "artifact output size mismatch")
    require(artifact["work_sha256"] == work_sha == EXPECTED_WORK_SHA, "artifact work SHA mismatch")
    require(
        path_is(artifact["preserved_output_path"], result, "artifact preserved output path"),
        "artifact preserved output path does not identify this Run",
    )
    require(
        path_is(artifact["preserved_work_path"], work, "artifact preserved work path"),
        "artifact preserved work path does not identify this Run",
    )
    require(
        path_is(artifact["runtime_output_path"], OUTPUT, "artifact runtime output path"),
        "artifact runtime output path does not identify fixed EX03",
    )
    require(
        path_is(artifact["runtime_work_path"], WORK, "artifact runtime work path"),
        "artifact runtime work path does not identify fixed EX03",
    )
    return result_sha, work_sha


def validate_pad_records(
    pad_run: dict, pad_variables: dict, run_number: int, mappings: list[dict]
) -> None:
    test_id = f"EX03-R11-FILE-AUX1-RUN{run_number}"
    require_keys(
        pad_run,
        {
            "schema_version",
            "test_id",
            "flow_name",
            "flow_window_id",
            "run_index",
            "run_invocations_total",
            "terminal_observation",
            "status",
        },
        "pad-run",
    )
    terminal = require_keys(
        pad_run["terminal_observation"],
        {"status_bar", "run_button_enabled", "stop_button_disabled", "designer_error_observed"},
        "pad-run terminal observation",
    )
    require(pad_run["schema_version"] == 1, "pad-run schema mismatch")
    require(pad_run["test_id"] == test_id, "pad-run case/Run mismatch")
    require(pad_run["run_index"] == run_number, "pad-run index mismatch")
    require(pad_run["run_invocations_total"] == run_number, "pad-run invocation count mismatch")
    require(pad_run["status"] == "PASS_TERMINAL_READY_NO_ERROR_OBSERVED", "pad-run status mismatch")
    require(
        terminal
        == {
            "status_bar": "READY",
            "run_button_enabled": True,
            "stop_button_disabled": True,
            "designer_error_observed": False,
        },
        "pad-run terminal state mismatch",
    )

    require_keys(
        pad_variables,
        {
            "schema_version",
            "test_id",
            "flow_name",
            "execution_requested_during_observation",
            "transfer_state",
            "value_type_matches",
            "counts",
            "status",
        },
        "pad-variables",
    )
    require(pad_variables["schema_version"] == 1, "pad-variables schema mismatch")
    require(pad_variables["test_id"] == test_id, "pad-variables case/Run mismatch")
    require(pad_variables["flow_name"] == pad_run["flow_name"], "PAD flow identity mismatch")
    require(
        pad_variables["execution_requested_during_observation"] is False,
        "PAD observation unexpectedly requested execution",
    )
    require(
        pad_variables["transfer_state"]
        == {"observed_value": "SAVED_REOPENED_12_JSON_COMPARISONS_READY", "match": True},
        "PAD transfer state mismatch",
    )
    expected_variables = {
        f"{mapping['target_sheet']}_{mapping['target_cell']}_ValueTypeMatch"
        for mapping in mappings
    }
    actual_variables = pad_variables["value_type_matches"]
    require(isinstance(actual_variables, dict), "PAD type matches must be an object")
    require(set(actual_variables) == expected_variables, "PAD type-match target set mismatch")
    require(
        all(value == {"observed_value": True, "match": True} for value in actual_variables.values()),
        "PAD type-match value mismatch",
    )
    require(pad_variables["counts"] == {"true": 12, "false": 0, "total": 12}, "PAD counts mismatch")
    require(
        pad_variables["status"] == "PASS_12_OF_12_PAD_JSON_VALUE_AND_TYPE_MATCH",
        "PAD type-match status mismatch",
    )


def validate_typed_report(
    typed: dict, run_number: int, result: Path, result_sha: str, contract: dict,
    *, expected_run_label: str | None = None,
) -> None:
    require_keys(
        typed,
        {
            "kind",
            "run_label",
            "status",
            "scope",
            "output",
            "originals_sha256_before",
            "originals_sha256_after",
            "originals_unchanged_by_verifier",
            "mappings",
            "mismatches",
        },
        "typed report",
    )
    require(typed["kind"] == "EX03_FIXED_TEXT_NUMBER_TYPED_TRANSFER", "typed case mismatch")
    require(
        typed["run_label"] == (
            f"EX03-R11-FILE-AUX1-RUN{run_number}"
            if expected_run_label is None else expected_run_label
        ),
        "typed Run label mismatch",
    )
    require(typed["status"] == "MATCH_FIXED_EX03_TEXT_NUMBER_SCOPE", "typed status mismatch")
    scope = require_keys(
        typed["scope"],
        {"allowed_types", "explicitly_not_generalized_to", "fixed_mapping_count", "method"},
        "typed scope",
    )
    require(scope["allowed_types"] == ["number", "text"], "typed allowed-type scope mismatch")
    require(
        scope["explicitly_not_generalized_to"] == EXPECTED_EXCLUDED_TYPES,
        "typed excluded-type scope mismatch",
    )
    require(scope["fixed_mapping_count"] == len(contract["mappings"]) == 12, "typed mapping count mismatch")
    require(isinstance(scope["method"], str) and bool(scope["method"]), "typed method missing")

    output = require_keys(
        typed["output"],
        {"path", "sha256_before", "sha256_after", "unchanged_by_verifier"},
        "typed output",
    )
    require(path_is(output["path"], result, "typed output path"), "typed output path mismatch")
    require(
        output["sha256_before"] == output["sha256_after"] == result_sha,
        "typed output SHA does not identify the preserved artifact",
    )
    require(output["unchanged_by_verifier"] is True, "typed output immutable flag mismatch")
    require(
        typed["originals_sha256_before"]
        == typed["originals_sha256_after"]
        == contract["source_hashes"],
        "typed source SHA set mismatch",
    )
    require(typed["originals_unchanged_by_verifier"] is True, "typed source immutable flag mismatch")
    require(isinstance(typed["mappings"], list), "typed mappings must be a list")
    require(len(typed["mappings"]) == len(contract["mappings"]) == 12, "typed mappings must contain all 12 cells")
    mapping_keys = {
        "source_path",
        "source_sheet",
        "source_cell",
        "target_sheet",
        "target_cell",
        "grader_expected",
        "source_actual",
        "target_actual",
        "source_matches_expected",
        "target_matches_expected",
        "source_matches_target",
    }
    fixed_keys = [
        "source_path",
        "source_sheet",
        "source_cell",
        "target_sheet",
        "target_cell",
        "grader_expected",
    ]
    for index, (actual, expected) in enumerate(zip(typed["mappings"], contract["mappings"])):
        actual = require_keys(actual, mapping_keys, f"typed mapping {index}")
        require(
            {key: actual[key] for key in fixed_keys} == expected,
            f"typed mapping {index} does not match fixed EX03 coordinates",
        )
        require(actual["source_actual"] == expected["grader_expected"], f"typed source {index} mismatch")
        require(actual["target_actual"] == expected["grader_expected"], f"typed target {index} mismatch")
        require(
            actual["source_matches_expected"] is True
            and actual["target_matches_expected"] is True
            and actual["source_matches_target"] is True,
            f"typed mapping {index} match flags failed",
        )
    require(typed["mismatches"] == [], "typed report contains mismatches")


def validate_legacy_report(legacy: dict, result_sha: str, contract: dict) -> None:
    require_keys(
        legacy,
        {
            "status",
            "kind",
            "legacy",
            "failure_counts",
            "checks",
            "cells",
            "output_sha_before",
            "output_sha_after",
            "originals_sha256",
        },
        "legacy report",
    )
    require(legacy["kind"] == "EX03_INDEPENDENT_DIAGNOSTIC", "legacy case mismatch")
    require(legacy["status"] == "FAIL", "legacy raw FAIL was not preserved")
    require(
        legacy["output_sha_before"] == legacy["output_sha_after"] == result_sha,
        "legacy output SHA does not identify the preserved artifact",
    )
    expected_originals = {
        **contract["source_hashes"],
        contract["case"]["template"]: sha256(contract["template"]),
    }
    require(legacy["originals_sha256"] == expected_originals, "legacy source/template SHA set mismatch")
    require(legacy["failure_counts"] == EXPECTED_LEGACY_COUNTS, "legacy 558 category count mismatch")
    require(sum(legacy["failure_counts"].values()) == 558, "legacy 558 total mismatch")

    legacy_summary = require_keys(
        legacy["legacy"],
        {"status", "case", "checked_cells", "target_cells", "failures", "output_sha256"},
        "legacy summary",
    )
    require(legacy_summary["status"] == "FAIL", "legacy summary status mismatch")
    require(legacy_summary["case"] == "EX03", "legacy summary case mismatch")
    require(legacy_summary["checked_cells"] == 480, "legacy checked-cell count mismatch")
    require(legacy_summary["target_cells"] == 12, "legacy target-cell count mismatch")
    require(legacy_summary["output_sha256"] == result_sha, "legacy summary output SHA mismatch")
    require(isinstance(legacy_summary["failures"], list) and len(legacy_summary["failures"]) == 558, "legacy failure list must contain 558 items")

    checks = require_keys(
        legacy["checks"],
        {"target_values_types_positions", "outside_values_types_formulas"},
        "legacy checks",
    )
    require(
        checks["target_values_types_positions"]
        == {"checked": 12, "mismatches": [], "status": "MATCH_SAVED_XLSX_ONLY"},
        "legacy target check mismatch",
    )
    require(
        checks["outside_values_types_formulas"]
        == {"checked": 468, "mismatches": [], "status": "MATCH_SAVED_XLSX_ONLY"},
        "legacy outside-cell check mismatch",
    )

    require(isinstance(legacy["cells"], list) and len(legacy["cells"]) == 480, "legacy cells must contain 480 entries")
    expected_cells = {
        (sheet, f"{column_name(column)}{row}")
        for sheet in contract["sheet_names"]
        for row in range(1, FORMAT_ROWS_PER_SHEET + 1)
        for column in range(1, FORMAT_COLUMNS_PER_SHEET + 1)
    }
    actual_cells = set()
    actual_targets = set()
    for index, cell in enumerate(legacy["cells"]):
        cell = require_keys(
            cell, {"sheet", "cell", "target", "expected", "actual", "match"}, f"legacy cell {index}"
        )
        coordinate = (cell["sheet"], cell["cell"])
        actual_cells.add(coordinate)
        if cell["target"] is True:
            actual_targets.add(coordinate)
        require(cell["expected"] == cell["actual"] and cell["match"] is True, f"legacy cell {index} mismatch")
    require(actual_cells == expected_cells, "legacy cell coordinate coverage mismatch")
    require(actual_targets == contract["target_coordinates"], "legacy target coordinate coverage mismatch")


def validate_native_report(
    native: dict, result: Path, result_sha: str, contract: dict
) -> None:
    require_keys(
        native,
        {
            "schema_version",
            "kind",
            "observed_at",
            "read_only",
            "paths",
            "sha256_before",
            "sha256_after",
            "bounds",
            "attributes",
            "comparison_policy",
            "snapshot_sha256",
            "difference_attribute_counts",
            "difference_location_counts",
            "differences",
            "status",
            "scope",
            "acceptance_boundary",
        },
        "native report",
    )
    require(native["schema_version"] == 3, "native schema mismatch")
    # The frozen r11 record retains the shared comparator's historical EX02
    # kind label.  Bind it to EX03 through the fixed reference/output paths,
    # hashes, sheets, and bounds below instead of rewriting original evidence.
    require(
        native["kind"] == "EX02_EXCEL_EFFECTIVE_FORMAT_COMPARISON",
        "native comparator kind mismatch",
    )
    require(isinstance(native["observed_at"], str) and bool(native["observed_at"]), "native observation time missing")
    require(native["read_only"] is True, "native comparison was not read-only")
    paths = require_keys(native["paths"], {"reference", "output"}, "native paths")
    require(path_is(paths["reference"], contract["template"], "native reference path"), "native reference is not the fixed EX03 template")
    require(path_is(paths["output"], result, "native output path"), "native output path does not identify this Run")
    reference_sha = sha256(contract["template"])
    before = require_keys(native["sha256_before"], {"reference", "output"}, "native SHA before")
    after = require_keys(native["sha256_after"], {"reference", "output"}, "native SHA after")
    require(
        before == after == {"reference": reference_sha, "output": result_sha},
        "native SHA set does not identify the fixed reference and Run artifact",
    )
    expected_bounds = {
        "sheets": contract["sheet_names"],
        "rows_per_sheet": FORMAT_ROWS_PER_SHEET,
        "columns_per_sheet": FORMAT_COLUMNS_PER_SHEET,
        "checked_cells": len(contract["sheet_names"]) * FORMAT_ROWS_PER_SHEET * FORMAT_COLUMNS_PER_SHEET,
        "checked_rows": len(contract["sheet_names"]) * FORMAT_ROWS_PER_SHEET,
        "checked_columns": len(contract["sheet_names"]) * FORMAT_COLUMNS_PER_SHEET,
    }
    require(native["bounds"] == expected_bounds, "native bounds do not cover the fixed EX03 scope")
    require(native["attributes"] == EXPECTED_NATIVE_ATTRIBUTES, "native attribute scope mismatch")
    require(isinstance(native["comparison_policy"], dict) and native["comparison_policy"], "native comparison policy missing")
    snapshot = require_keys(native["snapshot_sha256"], {"reference", "output"}, "native snapshot SHA")
    require(
        snapshot["reference"] == snapshot["output"]
        and isinstance(snapshot["reference"], str)
        and re.fullmatch(r"[0-9a-f]{64}", snapshot["reference"]) is not None,
        "native effective snapshot identity mismatch",
    )
    require(native["difference_attribute_counts"] == EXPECTED_NATIVE_COUNTS, "native attribute counts mismatch")
    require(native["difference_location_counts"] == EXPECTED_NATIVE_COUNTS, "native location counts mismatch")
    require(native["differences"] == [], "native report contains differences")
    require(native["status"] == "MATCH_EFFECTIVE_FORMAT", "native status mismatch")
    require(isinstance(native["scope"], str) and bool(native["scope"]), "native scope missing")
    require(isinstance(native["acceptance_boundary"], str) and bool(native["acceptance_boundary"]), "native acceptance boundary missing")


def validate_f6_report(f6: dict, result: Path, result_sha: str, contract: dict) -> None:
    require_keys(
        f6,
        {
            "schema_version",
            "kind",
            "output_path",
            "output_sha256_before",
            "output_sha256_after",
            "template_f6",
            "saved_f6",
            "checks",
            "status",
            "scope",
        },
        "F6 report",
    )
    percent_mapping = [
        mapping for mapping in contract["mappings"] if mapping["grader_expected"] == ["text", "100%"]
    ]
    require(len(percent_mapping) == 1, "Fixed EX03 must contain one text 100% target")
    target = percent_mapping[0]
    require(f6["schema_version"] == 1, "F6 schema mismatch")
    require(f6["kind"] == "EX03_R11_F6_EXCEL_NATIVE_READ_ONLY_INSPECTION", "F6 kind mismatch")
    require(path_is(f6["output_path"], result, "F6 output path"), "F6 output path mismatch")
    require(
        f6["output_sha256_before"] == f6["output_sha256_after"] == result_sha,
        "F6 output SHA does not identify the preserved artifact",
    )
    require(
        f6["template_f6"]
        == {
            "sheet": target["target_sheet"],
            "address": target["target_cell"],
            "value2": None,
            "value2_dotnet_type": None,
            "text": "",
            "has_formula": False,
            "formula": None,
            "number_format_invariant": "G/標準",
            "number_format_local": "G/標準",
            "prefix_character": "",
        },
        "F6 template reference mismatch",
    )
    require(
        f6["saved_f6"]
        == {
            "sheet": target["target_sheet"],
            "address": target["target_cell"],
            "value2": "100%",
            "value2_dotnet_type": "System.String",
            "text": "100%",
            "has_formula": False,
            "formula": None,
            "number_format_invariant": "G/標準",
            "number_format_local": "G/標準",
            "prefix_character": "",
        },
        "F6 saved value/type/format mismatch",
    )
    checks = require_keys(
        f6["checks"],
        {
            "output_unchanged_by_read",
            "value_is_exact_text_100_percent",
            "displayed_text_is_100_percent",
            "number_format_invariant_preserved",
            "number_format_local_preserved",
            "prefix_character_preserved_empty",
            "no_formula",
        },
        "F6 checks",
    )
    require(all(value is True for value in checks.values()), "F6 checks did not all pass")
    require(
        f6["status"] == "PASS_F6_SYSTEM_STRING_100_PERCENT_ORIGINAL_FORMAT_EMPTY_PREFIX_NO_FORMULA",
        "F6 status mismatch",
    )
    require(isinstance(f6["scope"], str) and bool(f6["scope"]), "F6 scope missing")


def validate_run(run_number: int) -> dict:
    require(run_number in (1, 2), f"Unsupported FILE-AUX1 Run: {run_number}")
    run = CYCLE / f"run{run_number}"
    pad_run = load(run / "pad-run.json")
    pad_variables = load(run / "pad-variables.json")
    artifact = load(run / "artifact.json")
    typed = load(run / "typed-transfer.json")
    legacy = load(run / "comparison.json")
    native = load(run / "native-styles.json")
    f6 = load(run / "f6-native.json")
    result = run / "result.xlsx"
    work = run / "work.xlsx"
    contract = fixed_contract()
    result_sha, work_sha = validate_artifact(artifact, result, work)
    validate_pad_records(pad_run, pad_variables, run_number, contract["mappings"])
    validate_typed_report(typed, run_number, result, result_sha, contract)
    validate_legacy_report(legacy, result_sha, contract)
    validate_native_report(native, result, result_sha, contract)
    validate_f6_report(f6, result, result_sha, contract)
    checks = {
        "pad_terminal_ready": True,
        "pad_run_index": True,
        "pad_json_12_true": True,
        "artifact_preserved": True,
        "result_sha": result_sha == artifact["output_sha256"],
        "work_frozen": work_sha == EXPECTED_WORK_SHA,
        "typed_transfer_bound_to_artifact_case_run_and_fixed_mapping": True,
        "legacy_comparison_bound_to_artifact_sources_and_fixed_coordinates": True,
        "effective_format_bound_to_artifact_reference_and_fixed_bounds": True,
        "f6_contract_bound_to_artifact_and_fixed_target": True,
    }
    require(all(checks.values()), f"Run{run_number} aggregate verification failed")
    return {
        "checks": checks,
        "pad_run": pad_run,
        "pad_variables": pad_variables,
        "artifact": artifact,
        "typed": typed,
        "legacy": legacy,
        "native": native,
        "f6": f6,
    }


def validate_two_run_report(two_run: dict, run1: dict, run2: dict) -> None:
    require_keys(
        two_run,
        {
            "kind",
            "status",
            "run1",
            "run2",
            "binary_sha_equal",
            "semantic_equal",
            "scope",
            "checked_cells",
            "note",
        },
        "two-run report",
    )
    require(
        two_run["kind"] == "EX03_TWO_POSITIVE_RUN_SEMANTIC_COMPARISON",
        "two-run case mismatch",
    )
    for run_number, aggregate in ((1, run1), (2, run2)):
        record = require_keys(
            two_run[f"run{run_number}"],
            {"path", "sha256_before", "sha256_after"},
            f"two-run Run{run_number}",
        )
        result = CYCLE / f"run{run_number}/result.xlsx"
        expected_sha = aggregate["artifact"]["output_sha256"]
        require(
            path_is(record["path"], result, f"two-run Run{run_number} path"),
            f"two-run Run{run_number} path mismatch",
        )
        require(
            record["sha256_before"] == record["sha256_after"] == expected_sha == sha256(result),
            f"two-run Run{run_number} SHA mismatch",
        )
    require(two_run["status"] == "MATCH", "two-run status mismatch")
    require(two_run["semantic_equal"] is True, "two-run semantic mismatch")
    require(
        two_run["binary_sha_equal"]
        == (run1["artifact"]["output_sha256"] == run2["artifact"]["output_sha256"]),
        "two-run binary identity flag mismatch",
    )
    require(two_run["checked_cells"] == 480, "two-run checked-cell count mismatch")
    require(isinstance(two_run["scope"], str) and bool(two_run["scope"]), "two-run scope missing")
    require(isinstance(two_run["note"], str) and bool(two_run["note"]), "two-run note missing")


def main() -> int:
    final_paths = [
        CYCLE / "run2/verification.json",
        CYCLE / "run2/runtime-output-after-run2.xlsx",
        CYCLE / "protected-after.json",
        CYCLE / "acceptance-status.json",
        CYCLE / "verification.json",
        CYCLE / "review.md",
        CYCLE / "artifact-manifest.json",
    ]
    existing = [str(path) for path in final_paths if path.exists()]
    if existing:
        raise ValueError(f"Refusing to overwrite final evidence: {existing}")

    source = load(CYCLE / "source-identity.json")
    recopy = load(CYCLE / "pad-recopy.json")
    run1 = validate_run(1)
    run2 = validate_run(2)
    two_run = load(CYCLE / "two-run-semantic.json")
    formal = load(FORMAL / "acceptance-status.json")
    formal_plan = load(FORMAL / "plan.json")

    if not (
        source.get("all_three_identical") is True
        and source["sha256"]["copilot_download"] == EXPECTED_GENERATED_SHA
        and source["sha256"]["preserved_generated_robin"] == EXPECTED_GENERATED_SHA
        and source["sha256"]["safety_audit_recorded_target"] == EXPECTED_GENERATED_SHA
    ):
        raise ValueError("Downloaded, preserved, and safety-audit Robin identity failed")
    if not (
        recopy.get("result") == "PASS_UNMODIFIED_PAD_SAVE_RECOPY_BEFORE_RUN1"
        and recopy["comparison"]["lf_normalized_exact"] is True
        and recopy["observation"]["actions_after_paste"] == 110
        and recopy["observation"]["variables_after_paste"] == 45
    ):
        raise ValueError("PAD save/re-copy gate failed")
    if not (
        formal["generation"]["failure_code"] == FORMAL_FAILURE
        and formal["generation"]["delivery_contract"] == "FAIL"
        and formal["pad_import"]["dedicated_flow_opened"] is False
        and formal["runs"]["pad_runs_used"] == 0
        and formal["decision"]["accepted"] is False
    ):
        raise ValueError("Formal EX03-r11-G1 failure boundary changed")
    validate_two_run_report(two_run, run1, run2)
    if not WORK.is_file() or sha256(WORK) != EXPECTED_WORK_SHA:
        raise ValueError("Runtime work.xlsx is not the frozen template")
    if not OUTPUT.is_file() or sha256(OUTPUT) != run2["artifact"]["output_sha256"]:
        raise ValueError("Runtime output does not match preserved Run2")

    run2_verification = {
        "schema_version": 1,
        "test_id": "EX03-R11-FILE-AUX1-RUN2",
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "checks": run2["checks"],
        "fixed_scope": {
            "target_cells": 12,
            "target_mismatches": 0,
            "outside_cells": 468,
            "outside_value_type_formula_mismatches": 0,
            "pad_json_value_and_type_true": 12,
            "pad_json_value_and_type_false": 0,
        },
        "legacy_raw_diagnostic": {
            "status": "FAIL_PRESERVED_NOT_USED_AS_EFFECTIVE_FORMAT_GATE",
            "failure_counts": run2["legacy"]["failure_counts"],
            "total": sum(run2["legacy"]["failure_counts"].values()),
        },
        "two_run_semantic_comparison": {
            "status": two_run["status"],
            "checked_cells": two_run["checked_cells"],
            "binary_sha_equal": two_run["binary_sha_equal"],
            "semantic_equal": two_run["semantic_equal"],
        },
        "status": "PASS_AUXILIARY_RUN2_AND_TWO_RUN_SEMANTIC_MATCH",
        "formal_ex03_r11_g1_result": f"{FORMAL_FAILURE}_PRESERVED",
    }
    write_json(CYCLE / "run2/verification.json", run2_verification)

    runtime_output_sha = sha256(OUTPUT)
    moved_output = CYCLE / "run2/runtime-output-after-run2.xlsx"
    shutil.move(str(OUTPUT), str(moved_output))
    if OUTPUT.exists() or sha256(moved_output) != runtime_output_sha:
        raise ValueError("Final Run2 runtime output move was not exact")
    if sha256(WORK) != EXPECTED_WORK_SHA:
        raise ValueError("Runtime work changed during final output preservation")

    protected_before_path = CYCLE / "protected-before.json"
    protected_before = load(protected_before_path)
    mismatches = []
    for item in protected_before["files"]:
        path = ROOT / item["path"]
        actual = sha256(path) if path.is_file() else None
        if actual != item["sha256"]:
            mismatches.append(
                {"path": item["path"], "before_sha256": item["sha256"], "after_sha256": actual}
            )
    protected_after = {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "base_commit": protected_before["base_commit"],
        "protected_before_sha256": sha256(protected_before_path),
        "checked_file_count": len(protected_before["files"]),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "runtime_work_sha256": sha256(WORK),
        "runtime_work_matches_frozen_template": sha256(WORK) == EXPECTED_WORK_SHA,
        "runtime_output_absent_after_preservation": not OUTPUT.exists(),
        "status": "PASS_ALL_PROTECTED_FILES_UNCHANGED" if not mismatches else "FAIL",
    }
    if mismatches:
        raise ValueError(f"Protected files changed: {mismatches[:5]}")
    write_json(CYCLE / "protected-after.json", protected_after)

    f6_saved = run2["f6"]["saved_f6"]
    candidate = formal_plan["candidate"]
    submission = formal_plan["submission"]
    acceptance = {
        "schema_version": 1,
        "cycle_id": "EX03-R11-FILE-AUX1",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "candidate": {
            "version": candidate["version"],
            "instruction_sha256": candidate["instruction_sha256"],
            "bundle_sha256": candidate["bundle_sha256"],
            "manifest_sha256": candidate["manifest_sha256"],
            "submitted_body_sha256": submission["body_sha256"],
            "generated_robin_sha256": EXPECTED_GENERATED_SHA,
        },
        "formal_ex03_r11_g1": {
            "normal_m365_send_count": formal["generation"]["normal_m365_send_count"],
            "generation_completed": formal["generation"]["completed"],
            "refusal": formal["generation"]["refusal"],
            "generated_file_static_safety": formal["generation"]["generated_file_static_safety"],
            "response_code_blocks": {
                "required": formal["generation"]["required_text_code_block_count"],
                "actual": formal["generation"]["actual_text_code_block_count"],
            },
            "delivery_contract": formal["generation"]["delivery_contract"],
            "failure_code": formal["generation"]["failure_code"],
            "formal_pad_runs": formal["runs"]["pad_runs_used"],
            "accepted": False,
            "status": "FORMAL_FAIL_PRESERVED",
        },
        "auxiliary_downloaded_file_validation": {
            "classification": "SEPARATELY_IDENTIFIED_AUXILIARY_NOT_FORMAL_ACCEPTANCE",
            "source_identity": "PASS_DOWNLOAD_PRESERVED_AUDIT_SHA_IDENTICAL",
            "pad_flow": {"name": recopy["flow_name"], "window_id": recopy["flow_window_id"]},
            "save_recopy": recopy["result"],
            "pad_run_count": 2,
            "run1": {
                "terminal": run1["pad_run"]["status"],
                "pad_json_type_matches": run1["pad_variables"]["counts"],
                "artifact_sha256": run1["artifact"]["output_sha256"],
                "typed_transfer": run1["typed"]["status"],
                "effective_format": run1["native"]["status"],
                "legacy_raw_difference_count": sum(run1["legacy"]["failure_counts"].values()),
                "f6": run1["f6"]["status"],
            },
            "run2": {
                "terminal": run2["pad_run"]["status"],
                "pad_json_type_matches": run2["pad_variables"]["counts"],
                "artifact_sha256": run2["artifact"]["output_sha256"],
                "typed_transfer": run2["typed"]["status"],
                "effective_format": run2["native"]["status"],
                "legacy_raw_difference_count": sum(run2["legacy"]["failure_counts"].values()),
                "f6": run2["f6"]["status"],
            },
            "two_run_semantic": {
                "status": two_run["status"],
                "checked_cells": two_run["checked_cells"],
                "binary_sha_equal": two_run["binary_sha_equal"],
                "semantic_equal": two_run["semantic_equal"],
            },
            "fixed_cell_checks": {
                "targets": 12,
                "target_mismatches_each_run": 0,
                "outside_cells": 468,
                "outside_mismatches_each_run": 0,
            },
            "f6_saved": f6_saved,
            "status": "PASS_AUXILIARY_DOWNLOADED_FILE_TWO_RUN_VALIDATION",
        },
        "preservation": protected_after,
        "remaining": {
            "formal_r11_delivery_contract_fail": True,
            "legacy_raw_558_fail_not_hidden": True,
            "existing_output_guard_live_path": "REMAINS_UNCONFIRMED",
            "unconfirmed_type_or_shape_generalization": False,
            "github_write": False,
        },
        "decision": {
            "formal_ex03_r11_g1_accepted": False,
            "auxiliary_validation_passed": True,
            "issue38_closed_by_this_auxiliary": False,
            "reason": (
                "The downloaded file independently passed the dedicated two-run PAD path, "
                "but the fixed formal r11 response delivery contract had already failed; "
                "auxiliary success cannot replace that failure."
            ),
        },
    }
    write_json(CYCLE / "acceptance-status.json", acceptance)

    verification = {
        "schema_version": 1,
        "cycle_id": "EX03-R11-FILE-AUX1",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "gates": {
            "source_sha_identity": True,
            "unmodified_pad_save_recopy": True,
            "run1_terminal_and_all_fixed_gates": True,
            "run1_artifact_preserved_before_run2": True,
            "run2_terminal_and_all_fixed_gates": True,
            "two_run_semantic_match": True,
            "protected_files_unchanged": True,
            "runtime_output_absent_after_preservation": True,
        },
        "diagnostics": {
            "legacy_raw_status": "FAIL",
            "legacy_raw_difference_count_each_run": 558,
            "excel_effective_difference_count_each_run": 0,
        },
        "formal_boundary": {
            "ex03_r11_g1_failure_code": FORMAL_FAILURE,
            "formal_acceptance": False,
            "auxiliary_acceptance": True,
        },
        "status": "PASS_AUXILIARY_ONLY_FORMAL_FAIL_PRESERVED",
    }
    write_json(CYCLE / "verification.json", verification)

    review = f"""# EX03-r11 downloaded-file auxiliary PAD validation

## Decision

- Formal `EX03-r11-G1`: **NOT ACCEPTED**. Its one normal-M365 response delivered zero of the one required text code blocks, so `{FORMAL_FAILURE}` remains unchanged and its formal PAD count remains 0.
- Separately identified downloaded-file auxiliary path: **PASS** for the fixed EX03 text/number case only. This does not offset the formal delivery-contract failure and does not close Issue #38.

## Fixed identity

- Version: `{candidate['version']}`
- Instruction SHA-256: `{candidate['instruction_sha256']}`
- Bundle SHA-256: `{candidate['bundle_sha256']}`
- Manifest SHA-256: `{candidate['manifest_sha256']}`
- Submitted body SHA-256: `{submission['body_sha256']}`
- Copilot downloaded / preserved / safety-audit target Robin SHA-256: `{EXPECTED_GENERATED_SHA}` (all identical)
- PAD flow: `{recopy['flow_name']}` (window `{recopy['flow_window_id']}`, Power Fx OFF), 110 actions and 45 flow variables
- Save/re-copy: LF-normalized exact match; no generated Robin repair

## Two PAD runs

| Gate | Run1 | Run2 |
| --- | --- | --- |
| Terminal READY, no designer error | PASS | PASS |
| PAD JSON value-and-type flags | 12 True / 0 False | 12 True / 0 False |
| Fixed target values/types/positions | 12/12, mismatch 0 | 12/12, mismatch 0 |
| Outside values/types/formulas | 468 checked, mismatch 0 | 468 checked, mismatch 0 |
| Excel-effective format/dimensions | 480 cells + 48 rows + 30 columns, difference 0 | same, difference 0 |
| Legacy raw comparator | FAIL 558 preserved (480 styles, 48 rows, 30 columns) | same |
| Artifact SHA-256 | `{run1['artifact']['output_sha256']}` | `{run2['artifact']['output_sha256']}` |

The two XLSX archives have different binary SHA values, which is expected for separately saved ZIP packages, while the full 480-cell semantic comparison is `MATCH`.

## F6 fixed text edge case

Both runs independently read saved/reopened `追記先!F6` as:

- value: `100%`
- .NET type: `System.String`
- number format: `G/標準` (unchanged from the template)
- prefix character: empty
- formula: none

## Preservation and remaining work

- All {protected_after['checked_file_count']} pre-existing tracked files match the pre-run SHA snapshot.
- Runtime `work.xlsx` remains `{EXPECTED_WORK_SHA}` and the fixed output path is absent after recoverable evidence preservation.
- Existing-output guard live behavior remains unconfirmed.
- The old raw 558-result is retained and is not relabeled as PASS; the separate Excel-effective comparison records zero actual format/dimension changes.
- No type or shape beyond the fixed EX03 text/number mapping is generalized.
- No GitHub write was performed.
"""
    with (CYCLE / "review.md").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(review)

    manifest_entries = []
    manifest_path = CYCLE / "artifact-manifest.json"
    for path in sorted(CYCLE.rglob("*")):
        if path.is_file() and path != manifest_path:
            manifest_entries.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
            )
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "cycle_id": "EX03-R11-FILE-AUX1",
            "file_count": len(manifest_entries),
            "files": manifest_entries,
        },
    )

    print(
        json.dumps(
            {
                "status": verification["status"],
                "formal_failure": FORMAL_FAILURE,
                "auxiliary_runs": 2,
                "run1_sha256": run1["artifact"]["output_sha256"],
                "run2_sha256": run2["artifact"]["output_sha256"],
                "semantic_equal": two_run["semantic_equal"],
                "legacy_raw_differences_each_run": 558,
                "effective_differences_each_run": 0,
                "protected_mismatches": len(mismatches),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
