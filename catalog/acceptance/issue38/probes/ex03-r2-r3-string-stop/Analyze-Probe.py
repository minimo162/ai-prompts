#!/usr/bin/env python3
"""Record the non-executing safety analysis required before PAD runs."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


PROBE = Path(__file__).resolve().parent
SAFE = PROBE / "embedded-safe.ps1.txt"
UNSAFE = PROBE / "r11-unsafe-interpolated-obrien.ps1.txt"
LIVE_NORMAL = PROBE / "candidate-normal.robin"
LIVE_NEGATIVE = PROBE / "candidate-negative.robin"
NORMAL = PROBE / "candidate-normal-postfix.robin"
NEGATIVE = PROBE / "candidate-negative-postfix.robin"
RUNTIME = PROBE / "runtime"
SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":3,"formats_restored":true}'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_errors(path: Path) -> list[str]:
    literal = str(path).replace("'", "''")
    command = (
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
        f"$path='{literal}';$tokens=$null;$errors=$null;"
        "[void][System.Management.Automation.Language.Parser]::ParseFile("
        "$path,[ref]$tokens,[ref]$errors);"
        "@($errors|ForEach-Object Message)|ConvertTo-Json -Compress"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if not completed.stdout.strip():
        return []
    value = json.loads(completed.stdout)
    return value if isinstance(value, list) else [value]


def gate(output: str | None, mode: str) -> bool:
    return output == SUCCESS and mode == "NORMAL"


def main() -> int:
    safe_text = SAFE.read_text(encoding="utf-8")
    normal_text = NORMAL.read_text(encoding="utf-8")
    negative_text = NEGATIVE.read_text(encoding="utf-8")
    unsafe_errors = parse_errors(UNSAFE)
    safe_errors = parse_errors(SAFE)
    if safe_errors:
        raise ValueError(f"Safe script has AST errors: {safe_errors}")
    if not unsafe_errors:
        raise ValueError("Unsafe r11 interpolation did not reproduce an AST failure")

    expected_json = [
        json.dumps({"probe": "O'Brien"}, ensure_ascii=False, separators=(",", ":")),
        json.dumps(
            {"probe": 'He said "Go"\nSecond line \'quoted\''},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        json.dumps({"probe": "100%"}, ensure_ascii=False, separators=(",", ":")),
        json.dumps({"probe": 42.5}, ensure_ascii=False, separators=(",", ":")),
    ]
    actual_json = [
        (RUNTIME / f"source-{index}.json").read_text(encoding="utf-8-sig")
        for index in range(1, 5)
    ]
    if actual_json != expected_json:
        raise ValueError(f"Actual PAD JSON differs: {actual_json!r}")
    actual_mode_json = (RUNTIME / "mode.json").read_text(encoding="utf-8-sig")
    if actual_mode_json != '{"probe":"NORMAL"}':
        raise ValueError(f"Actual PAD mode JSON differs: {actual_mode_json!r}")
    for value in ("O'Brien", 'He said "Go"', "100%", "42.5"):
        if value in safe_text:
            raise ValueError(f"Data value leaked into safe script: {value}")
    if "%Source" in safe_text or "%RunMode" in safe_text:
        raise ValueError("PAD data interpolation remains in the safe script")
    normalized_negative = negative_text.replace(
        "SET RunMode TO $'''INJECT_AFTER_FORMAT_CHANGE'''",
        "SET RunMode TO $'''NORMAL'''",
        1,
    )
    if normalized_negative != normal_text:
        raise ValueError("Normal and negative Robin differ outside the fixed mode selector")

    result = {
        "schema_version": 1,
        "kind": "ISSUE38_EX03_R2_R3_NON_EXECUTING_PREFLIGHT",
        "executed_embedded_scripts": False,
        "r11_unsafe_interpolated_example": {
            "path": UNSAFE.relative_to(PROBE).as_posix(),
            "sha256": sha256(UNSAFE),
            "ast_error_count": len(unsafe_errors),
            "ast_errors": unsafe_errors,
            "result": "REJECT_BEFORE_EXECUTION",
        },
        "safe_script": {
            "path": SAFE.relative_to(PROBE).as_posix(),
            "sha256": sha256(SAFE),
            "ast_error_count": 0,
            "pad_data_placeholders": 0,
            "fixed_json_file_reads": 5,
            "result": "PASS_STATIC_ONLY",
        },
        "actual_pad_json": actual_json,
        "actual_pad_json_utf8_bom": [
            (RUNTIME / f"source-{index}.json").read_bytes().startswith(b"\xef\xbb\xbf")
            for index in range(1, 5)
        ],
        "actual_pad_mode_json": actual_mode_json,
        "actual_pad_mode_utf8_bom": (RUNTIME / "mode.json").read_bytes().startswith(
            b"\xef\xbb\xbf"
        ),
        "handoff": {
            "method": "PAD ConvertCustomObjectToJson -> UTF-8 fixed files -> PowerShell Get-Content -Raw -> ConvertFrom-Json",
            "json_is_powershell_source_code": False,
            "normal_and_negative_robin_differ_only_by_mode": True,
        },
        "gate_simulation": {
            "exact_success_normal": gate(SUCCESS, "NORMAL"),
            "missing_output_normal": gate(None, "NORMAL"),
            "empty_output_normal": gate("", "NORMAL"),
            "error_output_normal": gate('{"status":"ERROR"}', "NORMAL"),
            "exact_success_negative_mode": gate(SUCCESS, "INJECT_AFTER_FORMAT_CHANGE"),
            "expected_error_negative_mode": gate(
                '{"status":"EXPECTED_ERROR","mode":"INJECT_AFTER_FORMAT_CHANGE","format_restored":true,"value_unchanged":true}',
                "INJECT_AFTER_FORMAT_CHANGE",
            ),
        },
        "candidate_sha256": {
            "live_normal": sha256(LIVE_NORMAL),
            "live_negative_not_run": sha256(LIVE_NEGATIVE),
            "normal": sha256(NORMAL),
            "negative": sha256(NEGATIVE),
        },
        "live_result": "NORMAL_STOPPED_NUMBER_PAYLOAD_TYPE_NEGATIVE_NOT_RUN",
        "decision": "POSTFIX_STATIC_PASS_LIVE_RERUN_NOT_RUN_STOP_CONDITION",
    }
    (PROBE / "postfix-static-analysis.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
