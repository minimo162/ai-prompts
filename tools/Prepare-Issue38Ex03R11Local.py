#!/usr/bin/env python3
"""Isolate the r9/r10 loss boundary and prepare an unsent r11 local source.

This tool never sends to Copilot and never runs PAD.  It preserves the r9/r10
captures as immutable inputs, exercises the Robin extraction/decoding path with
both a known-good source and an intentionally corrupt negative, and creates two
new local-only candidates:

* an independent full EX03-shaped teaching Robin with a shorter embedded
  PowerShell implementation; and
* a two-cell synthetic PAD probe using the same reduced expression pattern.

PAD save/re-copy and runtime evidence are added separately after UI execution.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "catalog/acceptance/issue38/probes/ex03-r11-minimal-powershell"
R9_CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r9-G1"
R10_CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r10-G1"
R10 = ROOT / "copilot/versions/20260917-excel-r10"
PERCENT = ROOT / "catalog/acceptance/issue38/probes/percent-text-write"
SOURCE_TOOL = ROOT / "tools/Prepare-Issue38Ex03R8IndependentSource.py"

INPUTS = {
    "r9_raw_code_copy_base64": R9_CYCLE / "generated-robin.clipboard.utf8.b64",
    "r9_saved_robin": R9_CYCLE / "generated.robin",
    "r9_response_dom": ROOT
    / "catalog/acceptance/issue38/probes/ex03-r10-structural-fidelity/r9-dom-code-confirmation.json",
    "r10_response_copy_base64": R10_CYCLE / "copilot-response.clipboard.utf8.b64",
    "r10_raw_code_copy_base64": R10_CYCLE / "generated-robin.clipboard.utf8.b64",
    "r10_saved_robin": R10_CYCLE / "generated.robin",
    "r10_teaching_robin": R10 / "support/EX03-R10-Independent-PAD-Recopy.robin",
    "r10_teaching_script": R10
    / "support/EX03-R10-Independent-FormatSandwich.ps1.txt",
    "source_tool": SOURCE_TOOL,
    "synthetic_base_robin": PERCENT / "captured-final.robin",
    "synthetic_source": PERCENT / "source.xlsx",
    "synthetic_template": PERCENT / "template.xlsx",
    "fixed_request": ROOT / "catalog/acceptance/issue38/requests/EX03.txt",
    "fixed_spec": ROOT / "catalog/acceptance/issue38/spec.json",
    "fixed_expected": ROOT / "catalog/acceptance/issue38/expected.json",
}

EXPECTED_HASHES = {
    "r9_raw_code_copy_base64": "42a03537c81e2300834a240932fde5a1de4bde23cf0bdcdf4bb611fbf773d894",
    "r9_saved_robin": "7a02ea0d073adde698578b8fa578f5701c728114ee55fbf20aa0ecdaaa32cb14",
    "r9_response_dom": "a78e4cf2f309b733ae8e9c6d6c268de16206ca8df17d2863d07f512cbcefb34f",
    "r10_response_copy_base64": "89d297796148810d5c99b57977b5a7a316d5cf7a8d08e42f861df47e9c16064a",
    "r10_raw_code_copy_base64": "b329276f3447290034680790936a4d88fb99e0d38bb579882440d22ff586016e",
    "r10_saved_robin": "4946431c9ce47f986b841115fbfd328036356c4e12ae7cbe912c2bf06e2b1ed3",
    "r10_teaching_robin": "6d9c23eabfacbcd65b1a18eabf5681805494e41171f94a9b01a28b24452815bb",
    "r10_teaching_script": "65b86b0e5be4ec2da30e57a6bd858e395d1103da2d05ab2e7607362772d1dfd9",
    "source_tool": "9c8f2cab7e154e38351251327c4f31fe6b53ff0fc5665c8bc8f6504c14545746",
    "synthetic_base_robin": "0b86dd150dac532e2c73f5a407a7c396b4153bbc3052e03a65a8c84c6dab6f46",
    "synthetic_source": "dda07aac129a7f2f55bbd40067eda426b4b8f4f997254e7e9f69059803ac5874",
    "synthetic_template": "13855dcaf2fa8a9dd8d282197fd74c2f138d9ebc5552debbedbc5886296d2bde",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "fixed_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
}

R9_RAW_SHA256 = "dce9d6f01de53252050b53de46283563f56226b1635a2ccdcbd71d2dfd2636bf"
R10_RAW_SHA256 = "4946431c9ce47f986b841115fbfd328036356c4e12ae7cbe912c2bf06e2b1ed3"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalized(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip("\n")


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_new(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(value)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def encode_robin_string(value: str) -> str:
    result: list[str] = []
    for character in value:
        if character in {"\\", "'", '"'}:
            result.append("\\")
        result.append(character)
    return "".join(result)


def action_from_script(script: str, source_module) -> str:
    return (
        source_module.ACTION_PREFIX
        + encode_robin_string(normalized(script))
        + source_module.ACTION_SUFFIX
        + "\n"
    )


def replace_action(flow: str, action: str, source_module) -> str:
    content = normalized(flow)
    start = content.index(source_module.ACTION_PREFIX)
    end = content.index(source_module.ACTION_SUFFIX, start) + len(
        source_module.ACTION_SUFFIX
    )
    action_lines = action.rstrip("\n").split("\n")
    embedded = "\n".join([action_lines[0], *("    " + line for line in action_lines[1:])])
    return content[:start] + embedded + content[end:]


def decoded_script(flow: str, source_module) -> str:
    action = source_module.extract_action(flow)
    return source_module.decode_robin_string(source_module.action_payload(action))


def line_record(source: str, line: int) -> str:
    return normalized(source).split("\n")[line - 1]


def independent_script() -> str:
    return r"""$ErrorActionPreference = 'Stop'
$targetPath = 'C:\Users\yuuki\ai-prompts-issue38\catalog\teaching\excel-r8-example\work-copy.xlsx'
$writes = @(
    @('Data1[0][0]', '教材出力一', 'J4', '%TextSource1Json%'),
    @('Data1[1][0]', '教材出力一', 'J5', '%TextSource2Json%'),
    @('Data1[2][0]', '教材出力一', 'J6', '%TextSource3Json%'),
    @('Data2[0][0]', '教材出力二', 'B10', '%TextSource4Json%'),
    @('Data2[1][0]', '教材出力二', 'B11', '%TextSource5Json%'),
    @('Data2[0][2]', '教材出力二', 'D10', '%TextSource6Json%'),
    @('Data2[1][2]', '教材出力二', 'D11', '%TextSource7Json%')
)
$targetPath = [IO.Path]::GetFullPath($targetPath)
$excel = [Runtime.InteropServices.Marshal]::GetActiveObject('Excel.Application')
$workbook = $null
try {
    $matches = @()
    for ($index = 1; $index -le $excel.Workbooks.Count; $index++) {
        $candidate = $excel.Workbooks.Item($index)
        if ([IO.Path]::GetFullPath([string]$candidate.FullName) -ieq $targetPath) { $matches += $candidate }
        else { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($candidate) }
    }
    if ($matches.Count -ne 1) {
        foreach ($match in $matches) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($match) }
        throw ('Expected one exact target workbook, found ' + $matches.Count)
    }
    $workbook = $matches[0]
    foreach ($write in $writes) {
        $worksheet = $null
        $cell = $null
        try {
            $sheetName = [string]$write[1]
            $cellAddress = [string]$write[2]
            $payload = [string]$write[3] | ConvertFrom-Json
            if ($payload.probe -isnot [string]) { throw ('Teaching text source is not a string: ' + $write[0]) }
            $worksheet = $workbook.Worksheets.Item($sheetName)
            $cell = $worksheet.Range($cellAddress)
            if ([bool]$cell.HasFormula) { throw ('Refusing to replace a formula cell: ' + $sheetName + '!' + $cellAddress) }
            $beforeNumberFormat = [string]$cell.NumberFormat
            try {
                $cell.NumberFormat = '@'
                $cell.Value2 = [string]$payload.probe
            }
            finally { $cell.NumberFormat = $beforeNumberFormat }
            if ($cell.Value2 -isnot [string] -or [string]$cell.Value2 -cne [string]$payload.probe) { throw ('Text value/type was not preserved: ' + $sheetName + '!' + $cellAddress) }
            if ([string]$cell.NumberFormat -cne $beforeNumberFormat) { throw ('Original number format was not restored: ' + $sheetName + '!' + $cellAddress) }
            if ([string]$cell.PrefixCharacter -cne '') { throw ('Prefix character changed or remained: ' + $sheetName + '!' + $cellAddress) }
            if ([bool]$cell.HasFormula) { throw ('A formula remained after text write: ' + $sheetName + '!' + $cellAddress) }
        }
        finally {
            if ($null -ne $cell) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
            if ($null -ne $worksheet) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet) }
        }
    }
}
finally {
    if ($null -ne $workbook) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) }
    if ($null -ne $excel) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) }
}
"""


def synthetic_script(probe_root: Path) -> str:
    target = (probe_root / "runtime/work.xlsx").resolve()
    return f"""$ErrorActionPreference = 'Stop'
$targetPath = '{target}'
$payload = [string]'%SourceTextJson%' | ConvertFrom-Json
if ($payload.probe -isnot [string]) {{ throw 'Synthetic source is not a string' }}
$targetPath = [IO.Path]::GetFullPath($targetPath)
$excel = [Runtime.InteropServices.Marshal]::GetActiveObject('Excel.Application')
$workbook = $null
$worksheet = $null
$cell = $null
try {{
    $matches = @()
    for ($index = 1; $index -le $excel.Workbooks.Count; $index++) {{
        $candidate = $excel.Workbooks.Item($index)
        if ([IO.Path]::GetFullPath([string]$candidate.FullName) -ieq $targetPath) {{ $matches += $candidate }}
        else {{ [void][Runtime.InteropServices.Marshal]::ReleaseComObject($candidate) }}
    }}
    if ($matches.Count -ne 1) {{
        foreach ($match in $matches) {{ [void][Runtime.InteropServices.Marshal]::ReleaseComObject($match) }}
        throw ('Expected one exact target workbook, found ' + $matches.Count)
    }}
    $workbook = $matches[0]
    $worksheet = $workbook.Worksheets.Item('Target')
    $cell = $worksheet.Range('A2')
    if ([bool]$cell.HasFormula) {{ throw 'Refusing to replace a formula cell' }}
    $beforeNumberFormat = [string]$cell.NumberFormat
    try {{
        $cell.NumberFormat = '@'
        $cell.Value2 = [string]$payload.probe
    }}
    finally {{ $cell.NumberFormat = $beforeNumberFormat }}
    if ($cell.Value2 -isnot [string] -or [string]$cell.Value2 -cne [string]$payload.probe) {{ throw 'Text value/type was not preserved' }}
    if ([string]$cell.NumberFormat -cne $beforeNumberFormat) {{ throw 'Original number format was not restored' }}
    if ([string]$cell.PrefixCharacter -cne '') {{ throw 'Prefix character changed or remained' }}
    if ([bool]$cell.HasFormula) {{ throw 'A formula remained after text write' }}
}}
finally {{
    if ($null -ne $cell) {{ [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }}
    if ($null -ne $worksheet) {{ [void][Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet) }}
    if ($null -ne $workbook) {{ [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) }}
    if ($null -ne $excel) {{ [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) }}
}}
"""


def prepare(output: Path = OUTPUT) -> dict[str, object]:
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite local probe: {output}")

    actual_hashes = {name: sha256(path) for name, path in INPUTS.items()}
    if actual_hashes != EXPECTED_HASHES:
        raise ValueError(f"Protected input hash mismatch: {actual_hashes}")

    source_module = load_module("issue38_r11_source", SOURCE_TOOL)
    parser_module = load_module(
        "issue38_r11_parser", ROOT / "tools/Analyze-Issue38Ex03R10Generation.py"
    )

    r9_raw = base64.b64decode(
        INPUTS["r9_raw_code_copy_base64"].read_text(encoding="ascii")
    )
    r9_saved = INPUTS["r9_saved_robin"].read_bytes()
    r9_dom = json.loads(INPUTS["r9_response_dom"].read_bytes())
    if sha256_bytes(r9_raw) != R9_RAW_SHA256:
        raise ValueError("r9 decoded code-copy changed")
    if normalized(r9_raw.decode("utf-8")) != normalized(r9_saved.decode("utf-8")):
        raise ValueError("r9 code-copy and saved Robin differ beyond newline serialization")
    if r9_dom["code_dom"]["sha256"] != R9_RAW_SHA256:
        raise ValueError("r9 response DOM no longer matches the code-copy")

    r10_response = base64.b64decode(
        INPUTS["r10_response_copy_base64"].read_text(encoding="ascii")
    )
    r10_raw = base64.b64decode(
        INPUTS["r10_raw_code_copy_base64"].read_text(encoding="ascii")
    )
    r10_saved = INPUTS["r10_saved_robin"].read_bytes()
    if sha256_bytes(r10_raw) != R10_RAW_SHA256 or r10_raw != r10_saved:
        raise ValueError("r10 code-copy and saved Robin are no longer byte-identical")
    if r10_raw not in r10_response:
        raise ValueError("r10 full response no longer contains the exact code-copy")

    r9_extracted = decoded_script(r9_saved.decode("utf-8"), source_module)
    r10_extracted = decoded_script(r10_saved.decode("utf-8"), source_module)
    teaching_robin = INPUTS["r10_teaching_robin"].read_text(encoding="utf-8")
    teaching_script = INPUTS["r10_teaching_script"].read_text(encoding="utf-8")
    teaching_decoded = decoded_script(teaching_robin, source_module)
    if normalized(teaching_decoded) != normalized(teaching_script):
        raise ValueError("Known-good teaching Robin does not decode exactly to its script")
    teaching_errors = parser_module.parse_powershell(teaching_decoded)
    if teaching_errors:
        raise ValueError(f"Known-good teaching script parse failure: {teaching_errors}")

    bad_robin = teaching_robin.replace(
        "[string]::Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, [StringComparison]::OrdinalIgnoreCase)",
        ":Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, :OrdinalIgnoreCase)",
    ).replace(
        "[string]::IsNullOrEmpty($afterPrefixCharacter)",
        ":IsNullOrEmpty($afterPrefixCharacter)",
    )
    if bad_robin == teaching_robin:
        raise ValueError("Intentional negative mutation did not apply")
    bad_decoded = decoded_script(bad_robin, source_module)
    if ":Equals([IO.Path]::GetFullPath" not in bad_decoded:
        raise ValueError("Extractor repaired or lost the first intentional corruption")
    if "-not :IsNullOrEmpty(" not in bad_decoded:
        raise ValueError("Extractor repaired or lost the second intentional corruption")
    bad_errors = parser_module.parse_powershell(bad_decoded)
    if not bad_errors:
        raise ValueError("Intentionally corrupt negative parsed cleanly")

    new_script = independent_script()
    new_action = action_from_script(new_script, source_module)
    new_robin = replace_action(teaching_robin, new_action, source_module) + "\n"
    if normalized(decoded_script(new_robin, source_module)) != normalized(new_script):
        raise ValueError("New independent Robin does not round-trip to the new script")
    new_errors = parser_module.parse_powershell(new_script)
    if new_errors:
        raise ValueError(f"New independent script parse failure: {new_errors}")

    output.mkdir(parents=True)
    shutil.copyfile(INPUTS["synthetic_source"], output / "source.xlsx")
    shutil.copyfile(INPUTS["synthetic_template"], output / "template.xlsx")
    (output / "runtime").mkdir()
    shutil.copyfile(output / "template.xlsx", output / "runtime/work.xlsx")

    synth_script = synthetic_script(output)
    synth_errors = parser_module.parse_powershell(synth_script)
    if synth_errors:
        raise ValueError(f"Synthetic script parse failure: {synth_errors}")
    synth_action = action_from_script(synth_script, source_module)
    synth_base = normalized(INPUTS["synthetic_base_robin"].read_text(encoding="utf-8"))
    synth = replace_action(synth_base, synth_action, source_module)
    old_root = normalized(str(PERCENT.resolve())).replace("\\", "\\\\")
    new_root = normalized(str(output.resolve())).replace("\\", "\\\\")
    synth = synth.replace(old_root, new_root)
    close_action = "Excel.CloseExcel.Close Instance: SourceBook"
    if synth.count(close_action) != 1:
        raise ValueError("Synthetic source close action is not unique")
    synth = synth.replace(close_action + "\n", "", 1)
    suffix = source_module.ACTION_SUFFIX
    if synth.count(suffix) != 1:
        raise ValueError("Synthetic RunScript suffix is not unique")
    synth = synth.replace(suffix, suffix + "\n" + close_action, 1)
    synth = synth.replace(
        "SET ProbeState TO $'''FORMAT_SANDWICH_FINISHED'''",
        "SET ProbeState TO $'''R11_MINIMAL_FINISHED'''",
    )
    if normalized(decoded_script(synth, source_module)) != normalized(synth_script):
        raise ValueError("Synthetic Robin does not round-trip to its script")
    if synth.index(close_action) < synth.index(source_module.ACTION_SUFFIX):
        raise ValueError("Synthetic source workbook is not kept open through exact selection")

    old_script_lines = len(normalized(teaching_script).split("\n"))
    new_script_lines = len(normalized(new_script).split("\n"))
    old_script_bytes = len(normalized(teaching_script).encode("utf-8"))
    new_script_bytes = len(normalized(new_script).encode("utf-8"))
    if new_script_lines >= old_script_lines or new_script_bytes >= old_script_bytes:
        raise ValueError("The successor script was not reduced")

    fixed_hashes = {
        name: actual_hashes[name]
        for name in ("fixed_request", "fixed_spec", "fixed_expected")
    }
    result = {
        "schema_version": 1,
        "probe_id": "EX03-R11-MINIMAL-POWERSHELL",
        "recorded_at": datetime.now().astimezone().isoformat(),
        "base_commit": "ac90b0943d2ff4e1172c23712ef49fe93787b7b2",
        "pipeline_boundary": {
            "r9": {
                "response_source": "complete rendered code DOM serialization; full prose response was not separately captured",
                "response_code_sha256": r9_dom["code_dom"]["sha256"],
                "code_copy_decoded_sha256": sha256_bytes(r9_raw),
                "response_equals_code_copy": True,
                "code_copy_equals_saved_robin_after_newline_normalization": True,
                "saved_robin_sha256": sha256_bytes(r9_saved),
                "extracted_script_sha256": sha256_bytes(
                    normalized(r9_extracted).encode("utf-8")
                ),
                "defect_lines": {
                    "robin_50": line_record(r9_saved.decode("utf-8"), 50),
                    "script_23": line_record(r9_extracted, 23),
                    "robin_90": line_record(r9_saved.decode("utf-8"), 90),
                    "script_63": line_record(r9_extracted, 63),
                },
                "earliest_confirmed_missing_stage": "rendered_response_code_dom",
            },
            "r10": {
                "response_copy_sha256": sha256_bytes(r10_response),
                "code_copy_decoded_sha256": sha256_bytes(r10_raw),
                "response_contains_exact_code_copy": True,
                "code_copy_equals_saved_robin_bytes": True,
                "saved_robin_sha256": sha256_bytes(r10_saved),
                "extracted_script_sha256": sha256_bytes(
                    normalized(r10_extracted).encode("utf-8")
                ),
                "defect_lines": {
                    "robin_50": line_record(r10_saved.decode("utf-8"), 50),
                    "script_23": line_record(r10_extracted, 23),
                    "robin_90": line_record(r10_saved.decode("utf-8"), 90),
                    "script_63": line_record(r10_extracted, 63),
                },
                "earliest_confirmed_missing_stage": "copied_full_response",
            },
            "classification": "ACQUISITION_COPY_SAVE_EXTRACTION_DECODE_NOT_CAUSAL",
            "hidden_model_or_service_cause": "UNKNOWN_NOT_CLAIMED",
        },
        "extraction_decode_tests": {
            "good": {
                "source": relative(INPUTS["r10_teaching_robin"]),
                "decoded_equals_support_script": True,
                "parser_error_count": len(teaching_errors),
            },
            "intentional_negative": {
                "path": "broken-extraction-negative.robin",
                "mutations_preserved_exactly": True,
                "parser_error_count": len(bad_errors),
                "first_error": bad_errors[0],
                "executed": False,
            },
        },
        "local_successor": {
            "version_id": "20260917-excel-r11",
            "status": "LOCAL_SOURCE_CANDIDATE_NOT_SENT_NOT_INTEGRATED",
            "script": "independent-minimal-format-sandwich.ps1.txt",
            "robin": "independent-candidate.robin",
            "old_script_lines": old_script_lines,
            "new_script_lines": new_script_lines,
            "line_reduction": old_script_lines - new_script_lines,
            "old_script_utf8_bytes_without_final_newline": old_script_bytes,
            "new_script_utf8_bytes_without_final_newline": new_script_bytes,
            "byte_reduction": old_script_bytes - new_script_bytes,
            "avoided_fragments": [
                "[string]::Equals(",
                "[StringComparison]::OrdinalIgnoreCase",
                "[string]::IsNullOrEmpty(",
            ],
            "preserved_contracts": [
                "one exact normalized FullName match using -ieq",
                "source JSON primitive must be System.String",
                "destination Value2 remains System.String and exact value",
                "original NumberFormat restored by inner finally",
                "PrefixCharacter empty and HasFormula false",
                "COM references released by finally",
            ],
            "parser_error_count": len(new_errors),
            "pad_save_recopy": "PENDING",
            "integrated_ex03_run": "NOT_AUTHORIZED_NOT_RUN",
        },
        "synthetic_probe": {
            "robin": "synthetic-candidate.robin",
            "script": "synthetic-minimal-format-sandwich.ps1.txt",
            "source": "source.xlsx",
            "template": "template.xlsx",
            "work": "runtime/work.xlsx",
            "output": "runtime/result.xlsx",
            "keeps_source_and_work_open_during_exact_selection": True,
            "parser_error_count": len(synth_errors),
            "pad_run": "PENDING",
        },
        "fixed_inputs": fixed_hashes,
        "scope": {
            "copilot_send": 0,
            "copilot_regeneration": 0,
            "integrated_ex03_run": 0,
            "github_write": 0,
            "r9_r10_generated_outputs_modified": False,
            "legacy_558_failure_preserved": True,
            "existing_output_guard_live_path": "REMAINS_UNCONFIRMED",
        },
        "decision": "PASS_BOUNDARY_AND_LOCAL_CANDIDATES_PREPARED_PAD_EVIDENCE_PENDING",
    }

    write_new(
        output / "independent-minimal-format-sandwich.ps1.txt",
        new_script.encode("utf-8"),
    )
    write_new(output / "independent-candidate.robin", new_robin.encode("utf-8"))
    write_new(output / "broken-extraction-negative.robin", bad_robin.encode("utf-8"))
    write_new(
        output / "synthetic-minimal-format-sandwich.ps1.txt",
        synth_script.encode("utf-8"),
    )
    write_new(output / "synthetic-candidate.robin", (synth + "\n").encode("utf-8"))
    write_new(
        output / "analysis.json",
        (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    report = f"""# EX03 r9/r10 pipeline boundary and r11 local source

## Conclusion

Both live failures are already present in the earliest preserved response-code representation. r9's complete 197-line rendered code DOM is byte-identical to its raw code-copy. r10's copied full response contains its raw code-copy byte-for-byte. Later code-copy, repository save, Robin action extraction, and PAD-string decoding preserve the two broken expressions; they do not remove the type qualifiers.

The known-good independent teaching Robin decodes exactly to its support script and parses with 0 errors. An intentionally corrupted copy preserves both corruptions through extraction/decoding and fails the PowerShell parser with {len(bad_errors)} errors. The extractor therefore requires no repair.

## Local successor change

The unsent `20260917-excel-r11` local source changes the actual embedded implementation, not only an inspection instruction. It removes the three fragile static-member fragments and reduces the embedded script from {old_script_lines} to {new_script_lines} lines ({old_script_bytes} to {new_script_bytes} UTF-8 bytes without the final newline). It keeps exact normalized FullName selection, source and destination string checks, original NumberFormat restoration in an inner `finally`, empty PrefixCharacter, non-formula checks, and COM cleanup.

Before:

```powershell
if ([string]::Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, [StringComparison]::OrdinalIgnoreCase)) {{
if ($afterPrefixCharacter -cne $beforePrefixCharacter -or -not [string]::IsNullOrEmpty($afterPrefixCharacter)) {{
```

After:

```powershell
$targetPath = [IO.Path]::GetFullPath($targetPath)
if ([IO.Path]::GetFullPath([string]$candidate.FullName) -ieq $targetPath) {{ $matches += $candidate }}
if ([string]$cell.PrefixCharacter -cne '') {{ throw (...) }}
```

This record is local preparation only. Copilot send, EX03 integrated execution, and GitHub write are all 0. PAD save/re-copy and the dedicated synthetic run remain pending at this point.
"""
    write_new(output / "report.md", report.encode("utf-8"))

    try:
        output_label = relative(output)
    except ValueError:
        output_label = str(output.resolve())
    return {
        "output": output_label,
        "analysis_sha256": sha256(output / "analysis.json"),
        "independent_robin_sha256": sha256(output / "independent-candidate.robin"),
        "independent_script_sha256": sha256(
            output / "independent-minimal-format-sandwich.ps1.txt"
        ),
        "synthetic_robin_sha256": sha256(output / "synthetic-candidate.robin"),
        "negative_parser_errors": len(bad_errors),
        "decision": result["decision"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    print(json.dumps(prepare(parser.parse_args().output), ensure_ascii=False, indent=2))
