#!/usr/bin/env python3
"""Non-live tests for the separate EX03 r12 fixed-helper prototype."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "catalog/acceptance/issue38/probes/ex03-r12-fixed-helper"
HELPER = PROTOTYPE / "EX03-R12-Fixed-StringTransfer.ps1"
INVOCATION = PROTOTYPE / "invocation.json"
LAUNCHER = PROTOTYPE / "launcher.ps1"
MANIFEST = PROTOTYPE / "manifest.json"
PARSER_PATH = ROOT / "tools/Analyze-Issue38Ex03R11Generation.py"
EXPECTED_SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'
PRODUCTION_HELPER_PATH = (
    r"C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes"
    r"\ex03-r12-fixed-helper\EX03-R12-Fixed-StringTransfer.ps1"
)
PRODUCTION_INVOCATION_PATH = (
    r"C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes"
    r"\ex03-r12-fixed-helper\invocation.json"
)


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PARSER = load("issue38_fixed_helper_parser", PARSER_PATH)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def ps_literal(value: str) -> str:
    return value.replace("'", "''")


class Issue38Ex03FixedHelperPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.helper = HELPER.read_text(encoding="utf-8")
        cls.invocation = json.loads(INVOCATION.read_text(encoding="utf-8"))
        cls.launcher = LAUNCHER.read_text(encoding="utf-8")

    def render_stub_launcher(
        self,
        helper_path: Path,
        helper_sha256: str,
        invocation_path: Path,
        invocation_sha256: str,
    ) -> str:
        replacements = {
            PRODUCTION_HELPER_PATH: str(helper_path),
            PRODUCTION_INVOCATION_PATH: str(invocation_path),
            self.manifest["artifacts"]["helper"]["sha256"]: helper_sha256,
            self.manifest["artifacts"]["invocation"]["sha256"]: invocation_sha256,
        }
        rendered = self.launcher
        for old, new in replacements.items():
            self.assertEqual(rendered.count(old), 1, old)
            rendered = rendered.replace(old, new, 1)
        return rendered

    def make_stub(self, output: str | None) -> str:
        lines = [
            "param([string]$InvocationPath)",
            "[IO.File]::WriteAllText('@@MARKER_PATH@@', 'INVOKED', [Text.UTF8Encoding]::new($false))",
        ]
        if output is not None:
            lines.append("Write-Output -NoEnumerate '" + ps_literal(output) + "'")
        return "\n".join(lines) + "\n"

    def run_stub_case(
        self,
        stub_text: str | None,
        *,
        mutate_after_render: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], bool]:
        with tempfile.TemporaryDirectory(prefix="issue38-fixed-helper-") as temporary:
            directory = Path(temporary)
            helper_path = directory / "stub-helper.ps1"
            invocation_path = directory / "stub-invocation.json"
            launcher_path = directory / "stub-launcher.ps1"
            marker = directory / "helper-invoked.txt"
            invocation_bytes = b'{"schema_version":1}\n'
            invocation_path.write_bytes(invocation_bytes)

            if stub_text is None:
                helper_bytes = b"missing"
            else:
                stub_text = stub_text.replace("@@MARKER_PATH@@", ps_literal(str(marker)))
                helper_path.write_text(stub_text, encoding="utf-8", newline="\n")
                helper_bytes = helper_path.read_bytes()

            launcher_path.write_text(
                self.render_stub_launcher(
                    helper_path,
                    sha256_bytes(helper_bytes),
                    invocation_path,
                    sha256_bytes(invocation_bytes),
                ),
                encoding="utf-8",
                newline="\n",
            )
            if mutate_after_render:
                with helper_path.open("a", encoding="utf-8", newline="\n") as handle:
                    handle.write("# verifier-negative mutation\n")

            completed = subprocess.run(
                [
                    "powershell.exe",
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-File",
                    str(launcher_path),
                ],
                cwd=directory,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertFalse(any(path.suffix.lower() == ".xlsx" for path in directory.iterdir()))
            return completed, marker.exists()

    def test_manifest_hashes_and_verifier_owned_launcher_literals_match(self):
        for name, path in (
            ("helper", HELPER),
            ("invocation", INVOCATION),
            ("launcher", LAUNCHER),
        ):
            with self.subTest(name=name):
                record = self.manifest["artifacts"][name]
                self.assertEqual(sha256(path), record["sha256"])
                self.assertEqual(path.stat().st_size, record["bytes"])
        self.assertIn(self.manifest["artifacts"]["helper"]["sha256"], self.launcher)
        self.assertIn(self.manifest["artifacts"]["invocation"]["sha256"], self.launcher)
        self.assertEqual(
            self.manifest["launcher_contract"]["expected_helper_sha256_source"],
            "VERIFIER_COMPUTED_FROM_LOCAL_BYTES_BEFORE_LAUNCHER_CREATION",
        )

    def test_helper_and_launcher_parse_and_keep_static_safety_contracts(self):
        self.assertEqual(PARSER.parse_powershell(self.helper), [])
        self.assertEqual(PARSER.parse_powershell(self.launcher), [])
        for forbidden in (
            "%TextSource",
            "%RunMode",
            "Invoke-Expression",
            "ScriptBlock]::Create",
            "Start-Process",
            "Remove-Item",
            "Invoke-WebRequest",
        ):
            self.assertNotIn(forbidden, self.helper)
            self.assertNotIn(forbidden, self.launcher)
        for index in range(1, 8):
            self.assertEqual(self.helper.count(f"source-{index}.json"), 1)
        self.assertIn("$mappings.Count -ne 7", self.helper)
        self.assertIn("GetActiveObject('Excel.Application')", self.helper)
        self.assertIn("$matches.Count -ne 1", self.helper)
        self.assertIn("$cell.NumberFormat = $beforeFormat", self.helper)
        self.assertIn("$cell.Value2 -isnot [string]", self.helper)
        self.assertIn("ConvertTo-Json -Compress", self.helper)
        temporary_format = self.helper.index("$cell.NumberFormat = '@'")
        forced_exception = self.helper.index("throw 'ISSUE38_INTENTIONAL_AFTER_FORMAT_CHANGE'")
        value_write = self.helper.index("$cell.Value2 = [string]$write[3]")
        finally_restore = self.helper.index(
            "finally {\n                $cell.NumberFormat = $beforeFormat"
        )
        negative_restore_check = self.helper.index("throw 'NEGATIVE_FORMAT_NOT_RESTORED'")
        self.assertLess(temporary_format, forced_exception)
        self.assertLess(forced_exception, value_write)
        self.assertLess(value_write, finally_restore)
        self.assertLess(finally_restore, negative_restore_check)
        self.assertLess(
            self.helper.index("$writesCompleted -ne 7"),
            self.helper.index("status = 'OK'"),
        )
        self.assertLess(
            self.launcher.index("HELPER_SHA256_MISMATCH"),
            self.launcher.index("& $helperPath"),
        )
        self.assertLess(
            self.launcher.index("& $helperPath"),
            self.launcher.index("HELPER_SUCCESS_OUTPUT_MISSING"),
        )

    def test_fixed_ex03_routing_is_outside_helper_and_teaching_bundle(self):
        for fixed_term in (
            "EX03-attempt1",
            "集計先",
            "追記先",
            "Data1[0][0]",
            "F7",
            "F6",
            "春",
            "項目甲",
            "100%",
        ):
            self.assertNotIn(fixed_term, self.helper, fixed_term)
        mappings = self.invocation["text_writes"]
        self.assertEqual(len(mappings), 7)
        self.assertEqual([item["source_index"] for item in mappings], list(range(1, 8)))
        self.assertEqual(
            [(item["source_label"], item["sheet"], item["cell"]) for item in mappings],
            [
                ("Data1[0][0]", "集計先", "F7"),
                ("Data1[1][0]", "集計先", "F8"),
                ("Data1[2][0]", "集計先", "F9"),
                ("Data2[0][0]", "追記先", "D5"),
                ("Data2[1][0]", "追記先", "D6"),
                ("Data2[0][2]", "追記先", "F5"),
                ("Data2[1][2]", "追記先", "F6"),
            ],
        )
        bundle = ROOT / "copilot/versions/20260917-excel-r12/knowledge/PAD-Robin-Knowledge-Bundle.txt"
        self.assertNotIn("EX03-R12-FIXED-HELPER-P1", bundle.read_text(encoding="utf-8"))

    def test_r12_fixed_inputs_and_formal_code_block_requirement_are_preserved(self):
        preserved = self.manifest["preserved_inputs"]
        paths = {
            "r12_instruction_sha256": ROOT / "copilot/versions/20260917-excel-r12/agent-instructions.txt",
            "r12_bundle_sha256": ROOT / "copilot/versions/20260917-excel-r12/knowledge/PAD-Robin-Knowledge-Bundle.txt",
            "r12_manifest_sha256": ROOT / "copilot/versions/20260917-excel-r12/manifest.json",
            "fixed_request_sha256": ROOT / "catalog/acceptance/issue38/requests/EX03.txt",
            "fixed_spec_sha256": ROOT / "catalog/acceptance/issue38/spec.json",
            "fixed_expected_sha256": ROOT / "catalog/acceptance/issue38/expected.json",
            "legacy_extractor_sha256": ROOT / "tools/Prepare-Issue38Ex03R8IndependentSource.py",
        }
        for key, path in paths.items():
            with self.subTest(key=key):
                self.assertEqual(sha256(path), preserved[key])
        instruction = paths["r12_instruction_sha256"].read_text(encoding="utf-8")
        self.assertIn("回答は全工程を一つのtextコードブロックへ入れます", instruction)
        self.assertFalse(self.manifest["replaces_r12"])
        self.assertFalse(self.manifest["scope"]["inherits_prior_acceptance"])

    def test_harmless_stub_normal_output_passes(self):
        stub = self.make_stub(EXPECTED_SUCCESS)
        completed, invoked = self.run_stub_case(stub)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, EXPECTED_SUCCESS)
        self.assertTrue(invoked)

    def test_missing_helper_stops_before_invocation(self):
        completed, invoked = self.run_stub_case(None)
        self.assertEqual(completed.returncode, 41)
        self.assertEqual(
            completed.stdout,
            '{"status":"ERROR","error_code":"HELPER_NOT_FOUND"}',
        )
        self.assertFalse(invoked)

    def test_modified_helper_sha_stops_before_invocation(self):
        stub = self.make_stub(EXPECTED_SUCCESS)
        completed, invoked = self.run_stub_case(stub, mutate_after_render=True)
        self.assertEqual(completed.returncode, 43)
        self.assertEqual(
            completed.stdout,
            '{"status":"ERROR","error_code":"HELPER_SHA256_MISMATCH"}',
        )
        self.assertFalse(invoked)

    def test_missing_success_output_is_rejected_after_harmless_invocation(self):
        stub = self.make_stub(None)
        completed, invoked = self.run_stub_case(stub)
        self.assertEqual(completed.returncode, 46)
        self.assertEqual(
            completed.stdout,
            '{"status":"ERROR","error_code":"HELPER_SUCCESS_OUTPUT_MISSING"}',
        )
        self.assertTrue(invoked)


if __name__ == "__main__":
    unittest.main(verbosity=2)
