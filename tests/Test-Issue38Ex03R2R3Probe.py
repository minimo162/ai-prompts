#!/usr/bin/env python3
"""Non-live gates for the EX03 R2/R3 string handoff and stop probe."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "catalog/acceptance/issue38/probes/ex03-r2-r3-string-stop"
BUILDER_PATH = PROBE / "Build-Probe.py"
SPEC = importlib.util.spec_from_file_location("issue38_r2_r3_probe", BUILDER_PATH)
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)


def powershell_ast_errors(path: Path) -> list[str]:
    literal_path = str(path).replace("'", "''")
    command = (
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
        f"$path='{literal_path}';$tokens=$null;$errors=$null;"
        "[void][System.Management.Automation.Language.Parser]::ParseFile("
        "$path,[ref]$tokens,[ref]$errors);"
        "@($errors|ForEach-Object Message)|ConvertTo-Json -Compress"
    )
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    value = completed.stdout.strip()
    if not value:
        return []
    decoded = json.loads(value)
    return decoded if isinstance(decoded, list) else [decoded]


def decode_robin_string(value: str) -> str:
    decoded: list[str] = []
    index = 0
    while index < len(value):
        if value[index] == "\\" and index + 1 < len(value) and value[index + 1] in {"\\", "'", '"'}:
            decoded.append(value[index + 1])
            index += 2
        else:
            decoded.append(value[index])
            index += 1
    return "".join(decoded)


def embedded_script(flow: str) -> str:
    prefix = "Scripting.RunPowershellScript.RunScript Script: $'''"
    suffix = "''' ScriptOutput=> PowershellOutput"
    start = flow.index(prefix) + len(prefix)
    end = flow.index(suffix, start)
    return decode_robin_string(flow[start:end])


class Issue38Ex03R2R3ProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((PROBE / "plan.json").read_text(encoding="utf-8"))
        cls.postfix_plan = json.loads((PROBE / "postfix-plan.json").read_text(encoding="utf-8"))
        cls.script = (PROBE / "embedded-safe.ps1.txt").read_text(encoding="utf-8")
        cls.live_normal_path = PROBE / "candidate-normal.robin"
        cls.live_normal = cls.live_normal_path.read_text(encoding="utf-8")
        cls.live_negative = (PROBE / "candidate-negative.robin").read_text(encoding="utf-8")
        cls.normal = (PROBE / "candidate-normal-postfix.robin").read_text(encoding="utf-8")
        cls.negative = (PROBE / "candidate-negative-postfix.robin").read_text(encoding="utf-8")

    def test_frozen_r11_and_r1_objects_match_f8765ea(self):
        for path, expected in {
            "copilot/versions/20260917-excel-r11": self.plan["preserved_git_objects"]["r11_candidate"],
            "copilot/versions/20260917-excel-r11/support/EX03-R11-Independent-PAD-Recopy.robin": self.plan["preserved_git_objects"]["r11_robin"],
            "copilot/versions/20260917-excel-r11/support/EX03-R11-Independent-Minimal-FormatSandwich.ps1.txt": self.plan["preserved_git_objects"]["r11_script"],
            "tools/Finalize-Issue38Ex03R11FileAux.py": self.plan["preserved_git_objects"]["r1_finalizer"],
            "tests/Test-Issue38Ex03R11FileAuxFinalizer.py": self.plan["preserved_git_objects"]["r1_test"],
        }.items():
            actual = subprocess.check_output(
                ["git", "rev-parse", f"f8765ea:{path}"], cwd=ROOT, text=True
            ).strip()
            self.assertEqual(actual, expected, path)

    def test_r11_interpolated_obrien_is_rejected_without_execution(self):
        errors = powershell_ast_errors(PROBE / "r11-unsafe-interpolated-obrien.ps1.txt")
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Unexpected token" in message or "terminator" in message for message in errors))

    def test_safe_script_parses_and_contains_no_data_interpolation(self):
        self.assertEqual(powershell_ast_errors(PROBE / "embedded-safe.ps1.txt"), [])
        for value in ("%Source1Json%", "%TextSource1Json%", "O'Brien", 'He said "Go"', "100%", "42.5"):
            self.assertNotIn(value, self.script)
        for forbidden in ("Invoke-Expression", "iex ", "ScriptBlock]::Create", "Add-Type", "Start-Process"):
            self.assertNotIn(forbidden, self.script)
        self.assertIn("Get-Content -LiteralPath", self.script)
        self.assertIn("ConvertFrom-Json", self.script)
        self.assertIn("$numberPayload -isnot [double] -and $numberPayload -isnot [decimal]", self.script)

    def test_live_candidate_is_frozen_and_postfix_is_separate(self):
        live_hash = hashlib.sha256(self.live_normal_path.read_bytes()).hexdigest()
        self.assertEqual(live_hash, self.postfix_plan["live_run_candidate_sha256"])
        canonical = self.live_normal_path.read_bytes()
        self.assertEqual(canonical.count(b"\r\n"), 63)
        escaped_success = BUILDER.robin_literal(BUILDER.SUCCESS_OUTPUT).encode("utf-8")
        raw_success = ("$'''" + BUILDER.SUCCESS_OUTPUT + "'''").encode("utf-8")
        lf_only = canonical.replace(b"\r\n", b"\n")
        self.assertEqual(lf_only.count(escaped_success), 1)
        reconstructed_initial = lf_only.replace(escaped_success, raw_success, 1)
        self.assertEqual(
            hashlib.sha256(reconstructed_initial).hexdigest(),
            json.loads((PROBE / "static-analysis.json").read_text(encoding="utf-8"))[
                "candidate_sha256"
            ]["normal"],
        )
        self.assertIn("$payloads[3].probe -isnot [double]", embedded_script(self.live_normal))
        self.assertNotIn("$numberPayload", embedded_script(self.live_normal))
        self.assertIn("$numberPayload", embedded_script(self.normal))
        self.assertEqual(self.postfix_plan["live_rerun"], "NOT_RUN_STOP_CONDITION")

    def test_postfix_changes_only_the_observed_number_type_gate(self):
        live_script = embedded_script(self.live_normal)
        expected_script = live_script.replace(
            "    if ($payloads[3].probe -isnot [double]) { throw 'NUMBER_PAYLOAD_TYPE' }",
            "    $numberPayload = $payloads[3].probe\n"
            "    if ($numberPayload -isnot [double] -and $numberPayload -isnot [decimal]) {\n"
            "        throw 'NUMBER_PAYLOAD_TYPE'\n"
            "    }",
            1,
        )
        self.assertEqual(embedded_script(self.normal), expected_script)
        self.assertEqual(
            self.live_normal.replace(live_script.replace("\\", "\\\\").replace("'", "\\'"), "<SCRIPT>", 1),
            self.normal.replace(expected_script.replace("\\", "\\\\").replace("'", "\\'"), "<SCRIPT>", 1),
        )

    def test_windows_powershell_restores_actual_numeric_json_as_decimal(self):
        path = str(PROBE / "runtime/source-4.json").replace("'", "''")
        command = (
            f"$p='{path}';"
            "(Get-Content -LiteralPath $p -Raw -Encoding UTF8 | "
            "ConvertFrom-Json).probe.GetType().FullName"
        )
        completed = subprocess.run(
            [
                str(Path.home() / "AppData/Local/Microsoft/WindowsApps/powershell.exe")
                if (Path.home() / "AppData/Local/Microsoft/WindowsApps/powershell.exe").is_file()
                else "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(completed.stdout.strip(), "System.Decimal")

    def test_actual_pad_json_bytes_are_fixed_utf8_bom_records(self):
        expected = [
            '{"probe":"O\'Brien"}',
            '{"probe":"He said \\"Go\\"\\nSecond line \'quoted\'"}',
            '{"probe":"100%"}',
            '{"probe":42.5}',
        ]
        for index, value in enumerate(expected, start=1):
            with self.subTest(index=index):
                raw = (PROBE / f"runtime/source-{index}.json").read_bytes()
                self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
                self.assertEqual(raw.decode("utf-8-sig"), value)
        mode = (PROBE / "runtime/mode.json").read_bytes()
        self.assertTrue(mode.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(mode.decode("utf-8-sig"), '{"probe":"NORMAL"}')

    def test_run_observation_is_bound_to_preserved_files(self):
        observation = json.loads((PROBE / "run-observation.json").read_text(encoding="utf-8"))
        self.assertEqual(
            observation["flow"]["initial_paste_candidate_sha256"],
            json.loads((PROBE / "static-analysis.json").read_text(encoding="utf-8"))[
                "candidate_sha256"
            ]["normal"],
        )
        self.assertEqual(
            hashlib.sha256(self.live_normal_path.read_bytes()).hexdigest(),
            observation["flow"]["candidate_sha256"],
        )
        self.assertTrue(observation["flow"]["saved_recopy_exact"])
        for record in observation["actual_pad_json"]:
            path = PROBE / record["path"]
            raw = path.read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
            self.assertEqual(raw.decode("utf-8-sig"), record["json"])
        self.assertEqual(observation["normal_run"]["invocations"], 1)
        self.assertFalse(observation["normal_run"]["script_gate_passed"])
        self.assertFalse(observation["normal_run"]["numeric_write_entered"])
        self.assertFalse(observation["normal_run"]["save_as_entered"])
        self.assertFalse((PROBE / "runtime/result.xlsx").exists())
        self.assertEqual(observation["negative_run"]["invocations"], 0)

    def test_robin_embeds_the_exact_safe_script(self):
        expected = self.script.replace("\r\n", "\n").rstrip("\n")
        for label, flow in (("normal", self.normal), ("negative", self.negative)):
            with self.subTest(label=label):
                self.assertEqual(embedded_script(flow).replace("\r\n", "\n"), expected)
                self.assertEqual(flow.count("Scripting.RunPowershellScript.RunScript"), 1)

    def test_actual_json_is_file_handoff_before_script(self):
        for flow in (self.live_normal, self.live_negative, self.normal, self.negative):
            script_at = flow.index("Scripting.RunPowershellScript.RunScript")
            self.assertEqual(flow.count("Variables.ConvertCustomObjectToJson"), 9)
            self.assertEqual(flow.count("File.WriteText File:"), 5)
            self.assertTrue(all(flow.index(f"source-{index}.json") < script_at for index in range(1, 5)))
            self.assertLess(flow.index("mode.json"), script_at)
            self.assertNotIn("%Source", embedded_script(flow))
            self.assertNotIn("%RunMode", embedded_script(flow))

    def test_save_and_numeric_write_are_inside_exact_success_and_normal_gate(self):
        for flow in (self.normal, self.negative):
            script_at = flow.index("Scripting.RunPowershellScript.RunScript")
            success_gate = flow.index(
                f"IF PowershellOutput = {BUILDER.robin_literal(BUILDER.SUCCESS_OUTPUT)} THEN"
            )
            mode_gate = flow.index("IF RunMode = $'''NORMAL''' THEN", success_gate)
            numeric_write = flow.index("Excel.WriteToExcel.WriteCell Instance: Work")
            save_as = flow.index("Excel.SaveExcel.SaveAs Instance: Work")
            false_close = flow.index("SET ProbeState TO $'''SCRIPT_NOT_SUCCESS_NO_SAVE'''", save_as)
            self.assertLess(script_at, success_gate)
            self.assertLess(success_gate, mode_gate)
            self.assertLess(mode_gate, numeric_write)
            self.assertLess(numeric_write, save_as)
            self.assertLess(save_as, false_close)
            self.assertEqual(flow.count("Excel.SaveExcel.SaveAs"), 1)
            self.assertEqual(flow.count("Excel.WriteToExcel.WriteCell Instance: Work"), 1)

    def test_normal_and_negative_candidates_differ_only_by_fixed_mode(self):
        for normal, negative in (
            (self.live_normal, self.live_negative),
            (self.normal, self.negative),
        ):
            normalized_negative = negative.replace(
                "SET RunMode TO $'''INJECT_AFTER_FORMAT_CHANGE'''",
                "SET RunMode TO $'''NORMAL'''",
                1,
            )
            self.assertEqual(normal, normalized_negative)

    def test_gate_rejects_error_missing_output_and_negative_mode(self):
        def passes(output: str | None, mode: str) -> bool:
            return output == BUILDER.SUCCESS_OUTPUT and mode == "NORMAL"

        self.assertTrue(passes(BUILDER.SUCCESS_OUTPUT, "NORMAL"))
        self.assertFalse(passes(None, "NORMAL"))
        self.assertFalse(passes("", "NORMAL"))
        self.assertFalse(passes('{"status":"ERROR"}', "NORMAL"))
        self.assertFalse(passes(BUILDER.SUCCESS_OUTPUT, "INJECT_AFTER_FORMAT_CHANGE"))
        self.assertFalse(
            passes(
                '{"status":"EXPECTED_ERROR","mode":"INJECT_AFTER_FORMAT_CHANGE","format_restored":true,"value_unchanged":true}',
                "INJECT_AFTER_FORMAT_CHANGE",
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
