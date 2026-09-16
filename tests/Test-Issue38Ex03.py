"""EX03 fixed-parameter comparator regression; synthetic outputs are not PAD evidence."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixtures = load('issue38_fixture_tests', 'tests/Test-Issue38Excel.py')
diagnostic = load('issue38_case_diagnostic', 'tools/Compare-Issue38Ex02.py')
typed_transfer = load(
    'issue38_typed_transfer', 'tools/Verify-Issue38Ex02TypedTransfer.py'
)
r7_builder = load(
    'issue38_ex03_r7_builder', 'tools/Build-Issue38Ex03CandidateR7.py'
)
r8_builder = load(
    'issue38_ex03_r8_builder', 'tools/Build-Issue38Ex03CandidateR8.py'
)
r8_source = load(
    'issue38_ex03_r8_source', 'tools/Prepare-Issue38Ex03R8IndependentSource.py'
)
r9_analysis = load(
    'issue38_ex03_r9_analysis', 'tools/Analyze-Issue38Ex03R8Escape.py'
)
r9_builder = load(
    'issue38_ex03_r9_builder', 'tools/Build-Issue38Ex03CandidateR9.py'
)
r9_acceptance = load(
    'issue38_ex03_r9_acceptance', 'tools/Prepare-Issue38Ex03R9Acceptance.py'
)
r9_checkpoint = load(
    'issue38_ex03_r9_checkpoint', 'tools/Verify-Issue38Ex03R9Checkpoint.py'
)
r10_analysis = load(
    'issue38_ex03_r10_analysis',
    'tools/Analyze-Issue38Ex03R9StructuralFidelity.py',
)
r10_builder = load(
    'issue38_ex03_r10_builder', 'tools/Build-Issue38Ex03CandidateR10.py'
)


class Ex03Tests(unittest.TestCase):
    def simulated(self, mutation=None):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        output = Path(directory.name) / 'simulated-ex03.xlsx'
        fixtures.simulated_output('EX03', output, mutation)
        return output

    def test_mappings_come_from_ex03_fixed_parameters(self):
        mappings = typed_transfer.fixed_mappings('EX03')
        self.assertEqual(len(mappings), 12)
        self.assertEqual(
            (mappings[0]['source_path'], mappings[0]['source_sheet'],
             mappings[0]['source_cell'], mappings[0]['target_sheet'],
             mappings[0]['target_cell']),
            ('fixtures/EX03/入力い.xlsx', '受取明細', 'D4', '集計先', 'F7'),
        )
        self.assertEqual(
            (mappings[-1]['source_path'], mappings[-1]['source_sheet'],
             mappings[-1]['source_cell'], mappings[-1]['target_sheet'],
             mappings[-1]['target_cell']),
            ('fixtures/EX03/入力ろ.xlsx', '追加項目', 'D3', '追記先', 'F6'),
        )
        self.assertNotIn(('Target A', 'C4'), {
            (item['target_sheet'], item['target_cell']) for item in mappings
        })

    def test_correct_ex03_simulation_passes_both_read_only_comparators(self):
        output = self.simulated()
        diagnostic_result = diagnostic.compare(output, 'EX03')
        typed_result = typed_transfer.verify_output(output, 'synthetic', 'EX03')
        self.assertEqual(diagnostic_result['status'], 'PASS_LOGICAL_OUTPUT_ONLY')
        self.assertEqual(
            diagnostic_result['checks']['target_values_types_positions']['checked'], 12
        )
        self.assertEqual(typed_result['status'], 'MATCH_FIXED_EX03_TEXT_NUMBER_SCOPE')
        self.assertEqual(typed_result['mismatches'], [])

    def test_ex03_number_as_text_is_detected_at_its_own_target(self):
        def mutate(tree):
            target = fixtures.cell(tree, 'G7')
            target.remove(target.find(fixtures.q('v')))
            target.set('t', 'inlineStr')
            ET.SubElement(ET.SubElement(target, fixtures.q('is')), fixtures.q('t')).text = '21'

        output = self.simulated(mutate)
        typed_result = typed_transfer.verify_output(output, 'synthetic-negative', 'EX03')
        self.assertEqual(typed_result['status'], 'FAIL')
        self.assertEqual(len(typed_result['mismatches']), 1)
        self.assertEqual(typed_result['mismatches'][0]['target_sheet'], '集計先')
        self.assertEqual(typed_result['mismatches'][0]['target_cell'], 'G7')
        self.assertEqual(typed_result['mismatches'][0]['grader_expected'], ['number', 21])
        self.assertEqual(typed_result['mismatches'][0]['target_actual'], ['text', '21'])

    def test_r6_text_write_support_is_bounded_and_exception_safe(self):
        version = ROOT / 'copilot/versions/20260916-excel-r6'
        manifest = json.loads((version / 'manifest.json').read_text(encoding='utf-8'))
        support = (version / manifest['support_files'][0]['path']).read_text(encoding='utf-8')
        self.assertIn(
            r"C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\runs\EX03-attempt1\work.xlsx",
            support,
        )
        self.assertIn("if ($matches.Count -ne 1)", support)
        self.assertIn("$allowedTargets[$sheetName] -cnotcontains $cellAddress", support)
        for target in ['F7', 'F8', 'F9', 'D5', 'D6', 'F5', 'F6']:
            self.assertIn(f"'{target}'", support)
        self.assertEqual(len(re.findall(r"Json = '%TextSource\dJson%'", support)), 7)
        self.assertRegex(
            support,
            re.compile(
                r"try \{\s*\$cell\.NumberFormat = '@'.*?finally \{\s*"
                r"\$cell\.NumberFormat = \$beforeNumberFormat",
                re.S,
            ),
        )
        self.assertIn('Refusing to replace a formula cell', support)
        self.assertIn('Prefix character changed or remained', support)
        self.assertNotIn('Start-Process', support)
        self.assertNotIn('Invoke-Expression', support)

    def test_r6_example_is_prewrite_integration_not_f6_postfix(self):
        examples = (
            ROOT / 'copilot/versions/20260916-excel-r6/knowledge/PAD-Robin-06-Examples.txt'
        ).read_text(encoding='utf-8')
        marker = 'EX03 r6統合構成例（実装者候補。Copilot生成・PAD実行前は未受入）'
        r6 = examples.split(marker, 1)[1]
        script_at = r6.index('Scripting.RunPowershellScript.RunScript')
        first_numeric_at = r6.index('Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource')
        save_at = r6.index('Excel.SaveExcel.SaveAs')
        self.assertLess(script_at, first_numeric_at)
        self.assertLess(first_numeric_at, save_at)
        self.assertEqual(r6.count('Scripting.RunPowershellScript.RunScript'), 1)
        self.assertEqual(
            r6.count('Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource'), 5
        )
        self.assertEqual(r6.count('_ValueTypeMatch TO SourceCellJson = SavedCellJson'), 12)
        self.assertNotIn('Excel.WriteToExcel.WriteCell Instance: Work Value: Data1', r6)
        self.assertNotIn('Excel.WriteToExcel.WriteCell Instance: Work Value: Data2', r6)

    def test_r7_pad_recopy_is_authoritative_and_decodes_to_support(self):
        version = ROOT / 'copilot/versions/20260916-excel-r7'
        capture = ROOT / 'catalog/acceptance/issue38/probes/ex03-r7-robin-source'
        manifest = json.loads((version / 'manifest.json').read_text(encoding='utf-8'))
        pad_capture = json.loads((capture / 'pad-capture.json').read_text(encoding='utf-8'))
        candidate = (capture / 'candidate-full.robin').read_text(encoding='utf-8')
        with (capture / 'pad-recopy-full.robin').open(
            encoding='utf-8', newline=''
        ) as handle:
            recopy = handle.read()
        with (version / 'support/EX03-R7-PAD-Recopy.robin').open(
            encoding='utf-8', newline=''
        ) as handle:
            version_recopy = handle.read()
        with (version / 'support/EX03-TextWrite-FormatSandwich.ps1.txt').open(
            encoding='utf-8', newline=''
        ) as handle:
            script = handle.read()

        normalize = lambda value: value.replace('\r\n', '\n').rstrip('\n')
        self.assertEqual(normalize(candidate), normalize(recopy))
        self.assertEqual(version_recopy, recopy)
        self.assertEqual(recopy.count('\r\n'), 110)
        self.assertEqual(recopy.replace('\r\n', '').count('\n'), 87)
        self.assertEqual(pad_capture['result'], 'PASS_PAD_DESIGNER_SAVE_RECOPY_NO_EXECUTION')
        self.assertFalse(pad_capture['scope']['executed'])
        self.assertFalse(pad_capture['scope']['copilot_send'])
        self.assertFalse(pad_capture['scope']['integrated_ex03_run'])

        prefix = "Scripting.RunPowershellScript.RunScript Script: $'''"
        suffix = "''' ScriptOutput=> PowershellOutput"
        flow = normalize(recopy)
        start = flow.index(prefix)
        end = flow.index(suffix, start) + len(suffix)
        action_lines = flow[start:end].split('\n')
        action = '\n'.join([action_lines[0], *(line[4:] for line in action_lines[1:])])
        self.assertTrue(action.startswith(prefix))
        self.assertTrue(action.endswith(suffix))
        payload = action[len(prefix):-len(suffix)]
        decoded = []
        index = 0
        while index < len(payload):
            if (
                payload[index] == '\\'
                and index + 1 < len(payload)
                and payload[index + 1] in {'\\', "'", '"'}
            ):
                decoded.append(payload[index + 1])
                index += 2
            else:
                decoded.append(payload[index])
                index += 1
        self.assertEqual(normalize(''.join(decoded)), normalize(script))

        script_at = flow.index('Scripting.RunPowershellScript.RunScript')
        numeric_at = flow.index('Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource')
        save_at = flow.index('Excel.SaveExcel.SaveAs')
        self.assertLess(script_at, numeric_at)
        self.assertLess(numeric_at, save_at)
        self.assertEqual(flow.count('Scripting.RunPowershellScript.RunScript'), 1)
        self.assertEqual(
            flow.count('Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource'), 5
        )
        self.assertEqual(flow.count('_ValueTypeMatch TO SourceCellJson = SavedCellJson'), 12)
        self.assertEqual(len(re.findall(r'Json=> TextSource\dJson', flow)), 7)
        self.assertNotIn('Excel.WriteToExcel.WriteCell Instance: Work Value: Data1', flow)
        self.assertNotIn('Excel.WriteToExcel.WriteCell Instance: Work Value: Data2', flow)
        self.assertEqual(
            manifest['status'],
            'FROZEN_CANDIDATE_EX03_PAD_RECOPIED_SOURCE_NOT_COPILOT_OR_RUNTIME_ACCEPTED',
        )
        self.assertEqual(manifest['evidence']['existing_output_guard'], 'STATIC_ONLY_NOT_LIVE_TESTED')

    def test_r7_diagnosis_compares_refusal_to_actual_sent_bundle(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX03-r6-G1'
        refusal = (cycle / 'response-rendered.txt').read_text(encoding='utf-8')
        sent_bundle = (
            ROOT / 'copilot/versions/20260916-excel-r6/knowledge/PAD-Robin-Knowledge-Bundle.txt'
        ).read_text(encoding='utf-8')
        for claimed in [r'=\>', r'\_', r'\[']:
            self.assertNotIn(claimed, sent_bundle)
        self.assertIn(r'=\>', refusal)
        self.assertIn(r'\_', refusal)
        self.assertIn('DataTable添字', refusal)
        self.assertEqual(sent_bundle.count('=>'), 184)
        self.assertEqual(sent_bundle.count('_ValueTypeMatch'), 60)
        self.assertEqual(sent_bundle.count('Data1[0][0]'), 12)

    def test_r7_rebuild_is_byte_identical_and_existing_destination_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'r7'
            r7_builder.build(destination)
            frozen = ROOT / 'copilot/versions' / r7_builder.VERSION
            for path in frozen.rglob('*'):
                if path.is_file():
                    self.assertEqual(
                        path.read_bytes(),
                        (destination / path.relative_to(frozen)).read_bytes(),
                        str(path),
                    )
            with self.assertRaisesRegex(ValueError, 'sealed'):
                r7_builder.build(destination)

    def test_r8_removes_fixed_answer_and_preserves_independent_pad_source(self):
        version = ROOT / 'copilot/versions/20260916-excel-r8'
        r7 = ROOT / 'copilot/versions/20260916-excel-r7'
        capture = ROOT / 'catalog/acceptance/issue38/probes/ex03-r8-independent-source'
        manifest = json.loads((version / 'manifest.json').read_text(encoding='utf-8'))
        independence = json.loads(
            (capture / 'independence-before.json').read_text(encoding='utf-8')
        )
        pad_capture = json.loads((capture / 'pad-capture.json').read_text(encoding='utf-8'))
        def exact(path):
            with path.open(encoding='utf-8', newline='') as handle:
                return handle.read()

        candidate = exact(capture / 'candidate-full.robin')
        recopy = exact(capture / 'pad-recopy-full.robin')
        support = exact(version / 'support/EX03-R8-Independent-PAD-Recopy.robin')
        script = exact(version / 'support/EX03-R8-Independent-FormatSandwich.ps1.txt')
        instruction = (version / 'agent-instructions.txt').read_text(encoding='utf-8')
        bundle = (version / 'knowledge/PAD-Robin-Knowledge-Bundle.txt').read_text(
            encoding='utf-8'
        )

        self.assertEqual(
            independence['decision'], 'FAIL_R7_CONTAINS_FIXED_EX03_COMPLETE_ANSWER'
        )
        self.assertEqual(
            pad_capture['result'],
            'PASS_PAD_DESIGNER_SAVE_RECOPY_INDEPENDENT_SOURCE_NO_EXECUTION',
        )
        self.assertTrue(pad_capture['comparison']['exact_bytes'])
        self.assertFalse(pad_capture['scope']['executed'])
        self.assertFalse(pad_capture['scope']['copilot_send'])
        self.assertFalse(pad_capture['scope']['integrated_ex03_run'])
        self.assertEqual(candidate, recopy)
        self.assertEqual(recopy, support)

        normalize = lambda value: value.replace('\r\n', '\n').rstrip('\n')
        reversed_candidate = candidate
        for old, new, _ in reversed(r8_source.REPLACEMENTS):
            reversed_candidate = reversed_candidate.replace(new, old)
        r7_robin = exact(r7 / 'support/EX03-R7-PAD-Recopy.robin')
        self.assertEqual(normalize(reversed_candidate), normalize(r7_robin))

        for name in [
            'PAD-Robin-01-Basics.txt',
            'PAD-Robin-02-Control.txt',
            'PAD-Robin-03-Files.txt',
            'PAD-Robin-05-UI-Web.txt',
        ]:
            self.assertEqual(
                (version / 'knowledge' / name).read_bytes(),
                (r7 / 'knowledge' / name).read_bytes(),
                name,
            )

        for value in [candidate, instruction, bundle]:
            for term in r8_builder.FIXED_COMPLETION_TERMS:
                self.assertNotIn(term, value)
            for term in r8_builder.UNIQUE_GRADER_STRINGS:
                self.assertNotIn(term, value)
        self.assertNotIn('100%', candidate)
        self.assertNotIn('100%', instruction)
        self.assertNotIn('F6', candidate)

        action = r8_builder.extract_action(recopy)
        decoded = r8_builder.decode_robin_string(r8_builder.action_payload(action))
        self.assertEqual(normalize(decoded), normalize(script))
        self.assertEqual(recopy.count('Scripting.RunPowershellScript.RunScript'), 1)
        self.assertEqual(
            recopy.count('Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource'), 5
        )
        self.assertEqual(
            recopy.count('_ValueTypeMatch TO SourceCellJson = SavedCellJson'), 12
        )
        self.assertEqual(len(re.findall(r'Json=> TextSource\dJson', recopy)), 7)

        self.assertEqual(
            manifest['status'],
            'FROZEN_CANDIDATE_EX03_INDEPENDENT_TEACHING_PAD_RECOPIED_NOT_COPILOT_OR_RUNTIME_ACCEPTED',
        )
        self.assertEqual(manifest['base_candidate'], '20260916-excel-r7')
        self.assertEqual(manifest['base_commit'], '806e4095a926fa0c7e020811c09770b5e5292841')
        self.assertFalse(manifest['inherits_live_acceptance'])
        self.assertEqual(
            manifest['evidence']['teaching_test_independence'],
            'PASS_R8_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_CURRENT_INSTRUCTION_BUNDLE_AND_SUPPORT',
        )
        self.assertEqual(
            manifest['evidence']['prior_refusal_internal_cause'],
            'UNRESOLVED_REFUSAL_ESCAPE_CLAIM_NOT_SUPPORTED_BY_ACTUAL_SENT_BUNDLE_BYTES',
        )
        for key in ['fixed_request', 'fixed_spec', 'grader_expected']:
            self.assertEqual(r8_builder.sha256(r8_builder.INPUTS[key]), r8_builder.EXPECTED[key])

    def test_r8_cause_audit_separates_refusal_from_teaching_coupling(self):
        sent_bundle = r8_builder.INPUTS['actually_sent_r6_bundle'].read_text(encoding='utf-8')
        refusal = r8_builder.INPUTS['r6_refusal'].read_text(encoding='utf-8')
        r8_bundle = (
            ROOT / 'copilot/versions/20260916-excel-r8/knowledge/PAD-Robin-Knowledge-Bundle.txt'
        ).read_text(encoding='utf-8')

        for claimed in [r'=\>', r'\_', r'\[']:
            self.assertNotIn(claimed, sent_bundle)
        self.assertIn(r'=\>', refusal)
        self.assertIn(r'\_', refusal)
        self.assertIn('DataTable添字', refusal)
        for term in r8_builder.FIXED_COMPLETION_TERMS:
            self.assertIn(term, sent_bundle)
            self.assertNotIn(term, r8_bundle)
        self.assertEqual(sent_bundle.count('=>'), 184)
        self.assertEqual(sent_bundle.count('_ValueTypeMatch'), 60)
        self.assertEqual(sent_bundle.count('Data1[0][0]'), 12)

    def test_r8_g1_live_cycle_stops_before_run1_on_pad_recopy_mismatch(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX03-r8-G1'
        generated = (cycle / 'generated.robin').read_text(encoding='utf-8')
        recopy = (cycle / 'pad-recopy-before-run1.robin').read_text(encoding='utf-8')
        diff = json.loads((cycle / 'pad-recopy-diff.json').read_text(encoding='utf-8'))
        pad = json.loads(
            (cycle / 'pad-import-and-recopy.json').read_text(encoding='utf-8')
        )
        status = json.loads(
            (cycle / 'acceptance-status.json').read_text(encoding='utf-8')
        )
        protected = json.loads(
            (cycle / 'protected-files-after.json').read_text(encoding='utf-8')
        )
        run1 = json.loads((cycle / 'run1/not-run.json').read_text(encoding='utf-8'))
        run2 = json.loads((cycle / 'run2/not-run.json').read_text(encoding='utf-8'))

        self.assertEqual(
            r8_builder.sha256(cycle / 'generated.robin'),
            '711bd5b3a5eb1cba48f6872cd5aa8f718ab3534de4d0e069d5fd1eb7b9d1ed89',
        )
        self.assertEqual(
            r8_builder.sha256(cycle / 'pad-recopy-before-run1.robin'),
            '3340cd988d6ed76dc249edc833be33869c530d0b37ddf223807ac86eaef9329f',
        )
        self.assertNotEqual(generated, recopy)
        self.assertEqual(diff['differing_line_count'], 30)
        self.assertEqual(diff['differing_lines'][0], 31)
        self.assertEqual(diff['differing_lines'][-1], 114)
        for record in diff['differences']:
            expected = record['generated'].replace(r'\[', r'\\[').replace(r'\]', r'\\]')
            self.assertEqual(record['pad_recopy'], expected, record['line'])

        self.assertEqual(pad['import']['designer_action_count'], 110)
        self.assertEqual(pad['import']['designer_variable_count'], 45)
        self.assertTrue(pad['import']['saved'])
        self.assertFalse(pad['import']['execution_requested'])
        self.assertFalse(
            pad['recopy_after_save_before_run1']['lf_normalized_exact_generated_robin']
        )
        self.assertEqual(
            pad['decision']['status'], 'FAIL_UNMODIFIED_IMPORT_SAVE_RECOPY_MISMATCH'
        )
        self.assertEqual(status['generation']['normal_m365_send_count'], 1)
        self.assertEqual(status['generation']['resend_count'], 0)
        self.assertFalse(status['decision']['accepted'])
        self.assertEqual(status['runs']['pad_runs_used'], 0)
        self.assertEqual(run1['pad_run_invocations'], 0)
        self.assertEqual(run2['pad_run_invocations'], 0)
        self.assertFalse(run1['runtime_output_exists'])
        self.assertEqual(protected['protected_file_count'], 199)
        self.assertEqual(protected['mismatch_count'], 0)
        self.assertEqual(protected['status'], 'PASS_UNCHANGED')

    def test_r9_escape_audit_fixes_the_failure_boundary_without_repair(self):
        audit_root = ROOT / 'catalog/acceptance/issue38/probes/ex03-r9-escape-fidelity'
        analysis = json.loads((audit_root / 'analysis.json').read_text(encoding='utf-8'))
        generation = analysis['generation_comparison']
        pad = analysis['pad_comparison']

        self.assertEqual(
            analysis['decision'], 'PASS_ROOT_CAUSE_BOUNDARY_READY_FOR_UNSENT_SUCCESSOR'
        )
        self.assertEqual(generation['expected_vs_generated_differing_lines'], 31)
        self.assertEqual(generation['generated_backslash_open_bracket_count'], 53)
        self.assertEqual(generation['generated_backslash_close_bracket_count'], 53)
        self.assertEqual(generation['authoritative_teaching_backslash_open_bracket_count'], 0)
        self.assertEqual(generation['authoritative_teaching_backslash_close_bracket_count'], 0)
        self.assertEqual(generation['stale_teaching_scope_label_count'], 1)
        self.assertEqual(generation['stale_teaching_type_label_count'], 1)
        self.assertTrue(generation['bounded_diagnostic_normalization_equals_expected'])
        self.assertFalse(generation['diagnostic_normalization_applied_to_evidence'])
        self.assertEqual(pad['generated_vs_pad_recopy_differing_lines'], 30)
        self.assertTrue(pad['all_differences_are_bracket_backslash_doubling'])
        self.assertEqual(pad['pad_runs'], 0)
        self.assertFalse(analysis['classification']['manual_repair'])
        self.assertEqual(analysis['scope']['copilot_send'], 0)
        self.assertEqual(analysis['scope']['pad_import'], 0)
        self.assertEqual(analysis['scope']['pad_run'], 0)
        self.assertFalse(
            analysis['minimum_successor_change']['fixed_request_or_expected_change']
        )
        self.assertFalse(analysis['minimum_successor_change']['teaching_robin_change'])

        with tempfile.TemporaryDirectory() as directory:
            rebuilt = Path(directory) / 'audit'
            result = r9_analysis.analyze(rebuilt)
            self.assertEqual(
                result['analysis_sha256'], r9_builder.sha256(audit_root / 'analysis.json')
            )
            self.assertEqual(
                result['report_sha256'], r9_builder.sha256(audit_root / 'report.md')
            )

    def test_r9_keeps_independent_pad_source_and_adds_fidelity_gate_only(self):
        version = ROOT / 'copilot/versions/20260917-excel-r9'
        r8 = ROOT / 'copilot/versions/20260916-excel-r8'
        manifest = json.loads((version / 'manifest.json').read_text(encoding='utf-8'))
        instruction = (version / 'agent-instructions.txt').read_text(encoding='utf-8')
        bundle = (version / 'knowledge/PAD-Robin-Knowledge-Bundle.txt').read_text(
            encoding='utf-8'
        )
        robin = (version / 'support/EX03-R9-Independent-PAD-Recopy.robin').read_bytes()
        script = (
            version / 'support/EX03-R9-Independent-FormatSandwich.ps1.txt'
        ).read_bytes()
        contract = (
            version / 'support/EX03-R9-Escape-Fidelity-Contract.txt'
        ).read_text(encoding='utf-8')

        self.assertEqual(
            robin, (r8 / 'support/EX03-R8-Independent-PAD-Recopy.robin').read_bytes()
        )
        self.assertEqual(
            script, (r8 / 'support/EX03-R8-Independent-FormatSandwich.ps1.txt').read_bytes()
        )
        self.assertEqual(robin.count(b'\\['), 0)
        self.assertEqual(robin.count(b'\\]'), 0)
        self.assertIn('Never prefix them with a backslash', contract)
        self.assertIn('Both counts must be zero', contract)
        self.assertIn('No teaching-only label may remain', contract)
        self.assertIn('backslash-open-bracket', instruction)
        self.assertIn('backslash-close-bracket', instruction)
        self.assertIn('error label', instruction)
        for term in r9_builder.FIXED_COMPLETION_TERMS + r9_builder.UNIQUE_GRADER_STRINGS:
            self.assertNotIn(term, instruction)
            self.assertNotIn(term, bundle)
            self.assertNotIn(term.encode('utf-8'), robin)
        self.assertNotIn(r9_builder.EXPECTED_TEXT, instruction)
        self.assertNotIn(r9_builder.EXPECTED_TEXT.encode('utf-8'), robin)

        self.assertEqual(
            manifest['status'],
            'FROZEN_CANDIDATE_EX03_ESCAPE_FIDELITY_GATE_NOT_COPILOT_OR_RUNTIME_ACCEPTED',
        )
        self.assertEqual(manifest['base_candidate'], '20260916-excel-r8')
        self.assertEqual(manifest['base_commit'], r9_builder.BASE_COMMIT)
        self.assertFalse(manifest['inherits_live_acceptance'])
        self.assertEqual(
            manifest['evidence']['teaching_test_independence'],
            'PASS_R9_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_CURRENT_INSTRUCTION_BUNDLE_AND_SUPPORT',
        )
        self.assertEqual(
            manifest['evidence']['escape_failure_boundary'],
            'CONFIRMED_NORMAL_M365_GENERATED_TEXT_BEFORE_PAD_IMPORT',
        )
        self.assertEqual(manifest['evidence']['escape_failure_hidden_model_cause'], 'UNKNOWN_NOT_CLAIMED')
        self.assertEqual(manifest['evidence']['generated_backslash_open_bracket_count'], 53)
        self.assertEqual(manifest['evidence']['teaching_backslash_open_bracket_count'], 0)
        self.assertTrue(manifest['evidence']['source_reused_exact_bytes'])
        self.assertFalse(manifest['evidence']['source_new_pad_capture_required'])
        self.assertEqual(manifest['evidence']['existing_output_guard'], 'STATIC_ONLY_NOT_LIVE_TESTED')

    def test_r9_rebuild_is_byte_identical_and_existing_destination_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'r9'
            r9_builder.build(destination)
            frozen = ROOT / 'copilot/versions' / r9_builder.VERSION
            for path in frozen.rglob('*'):
                if path.is_file():
                    self.assertEqual(
                        path.read_bytes(),
                        (destination / path.relative_to(frozen)).read_bytes(),
                        str(path),
                    )
            with self.assertRaisesRegex(ValueError, 'sealed'):
                r9_builder.build(destination)

    def test_r9_g1_checkpoint_is_exact_local_only_and_reproducible(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX03-r9-G1'
        body = (cycle / 'submitted-body.txt').read_bytes()
        instruction = (
            ROOT / 'copilot/versions/20260917-excel-r9/agent-instructions.txt'
        ).read_bytes()
        request = (
            ROOT / 'catalog/acceptance/issue38/requests/EX03.txt'
        ).read_bytes()
        plan = json.loads((cycle / 'plan.json').read_text(encoding='utf-8'))
        preflight = json.loads((cycle / 'preflight.json').read_text(encoding='utf-8'))
        protected = json.loads(
            (cycle / 'protected-files-before.json').read_text(encoding='utf-8')
        )

        self.assertEqual(body, instruction + b'\n' + request + b'\n')
        self.assertEqual(
            r9_acceptance.sha(cycle / 'submitted-body.txt'),
            'f6c6e59d719548ba54d6207fc6d6499a9ae7c699339ac855e3d4ea4a6f26aee4',
        )
        self.assertEqual(plan['candidate']['version'], '20260917-excel-r9')
        self.assertFalse(plan['candidate']['inherits_live_acceptance'])
        self.assertTrue(plan['authorization']['r8_authorized_send_consumed'])
        self.assertEqual(plan['authorization']['r8_normal_m365_send_count'], 1)
        self.assertEqual(plan['authorization']['r8_resend_count'], 0)
        self.assertEqual(plan['authorization']['r9_normal_m365_send_count'], 0)
        self.assertFalse(plan['authorization']['r9_browser_staged'])
        self.assertTrue(
            plan['authorization'][
                'r9_action_time_confirmation_required_before_staging_or_send'
            ]
        )
        self.assertEqual(
            plan['external_actions'],
            {
                'browser_staging': 0,
                'copilot_send': 0,
                'pad_import': 0,
                'pad_run': 0,
                'github_write': 0,
            },
        )
        self.assertEqual(
            plan['status'],
            'READY_FOR_NEW_ACTION_TIME_CONFIRMATION_NOT_STAGED_NOT_SENT',
        )
        self.assertEqual(preflight['decision']['local_checkpoint'], 'PASS')
        self.assertEqual(
            preflight['decision']['send'],
            'NOT_SENT_REQUIRES_NEW_ACTION_TIME_CONFIRMATION',
        )
        self.assertEqual(preflight['counts']['protected_files'], 233)
        self.assertEqual(preflight['counts']['submitted_body_utf16_units'], 7548)
        self.assertEqual(preflight['counts']['teaching_backslash_open_bracket'], 0)
        self.assertEqual(preflight['counts']['teaching_backslash_close_bracket'], 0)
        self.assertEqual(len(protected['files']), 233)
        for record in protected['files']:
            self.assertEqual(
                r9_acceptance.sha(ROOT / record['path']), record['sha256'], record['path']
            )
        self.assertFalse((cycle / 'm365-ready-to-send.json').exists())
        self.assertTrue((cycle / 'generated.robin').exists())

        with tempfile.TemporaryDirectory() as directory:
            rebuilt = Path(directory) / 'cycle'
            r9_acceptance.prepare(rebuilt, verify_head=False)
            checkpoint_names = (
                'plan.json',
                'preflight.json',
                'protected-files-before.json',
                'submitted-body.txt',
            )
            for name in checkpoint_names:
                self.assertEqual(
                    (cycle / name).read_bytes(),
                    (rebuilt / name).read_bytes(),
                    name,
                )
            self.assertFalse((rebuilt / 'browser-staging-stop.json').exists())
            self.assertFalse(
                (rebuilt / 'browser-staging-body-mismatch.json').exists()
            )
            with self.assertRaisesRegex(ValueError, 'refusing overwrite'):
                r9_acceptance.prepare(rebuilt, verify_head=False)

    def test_r9_g1_preserves_pre_send_computer_use_stop(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX03-r9-G1'
        evidence = json.loads(
            (cycle / 'browser-staging-stop.json').read_text(encoding='utf-8')
        )

        self.assertEqual(evidence['schema_version'], 1)
        self.assertEqual(evidence['cycle_id'], 'EX03-R9-G1')
        self.assertEqual(
            evidence['checkpoint']['head'],
            '5bc0460010247b8de00fcc4594c9d36020c72e69',
        )
        self.assertEqual(evidence['checkpoint']['action_time_verifier'], 'PASS')
        self.assertEqual(
            evidence['checkpoint']['submitted_body_sha256'],
            r9_acceptance.sha(cycle / 'submitted-body.txt'),
        )
        self.assertEqual(
            evidence['checkpoint']['bundle_sha256'],
            r9_acceptance.sha(
                ROOT
                / 'copilot/versions/20260917-excel-r9/knowledge/'
                'PAD-Robin-Knowledge-Bundle.txt'
            ),
        )
        self.assertEqual(
            evidence['destination'],
            {
                'service': 'Microsoft 365 Copilot Chat',
                'url': 'https://m365.cloud.microsoft/chat?es=SSR',
                'title': '\u30c1\u30e3\u30c3\u30c8 | Microsoft Copilot',
                'normal_chat': True,
                'model_selected': 'Think Deeper',
            },
        )
        self.assertEqual(
            evidence['staging'],
            {
                'browser_opened': True,
                'blank_editor_confirmed': True,
                'model_selected': True,
                'body_staged': False,
                'attachment_staged': False,
                'send_clicked': False,
                'generation_started': False,
            },
        )
        self.assertEqual(
            evidence['pad'],
            {
                'flow_created': False,
                'robin_pasted': False,
                'recopy_performed': False,
                'run1': 'NOT_RUN',
                'run2': 'NOT_RUN',
                'pad_runs_used': 0,
            },
        )
        self.assertEqual(
            evidence['stop']['status'],
            'STOPPED_BEFORE_BODY_OR_ATTACHMENT_STAGING',
        )
        self.assertFalse(evidence['stop']['same_turn_ui_retry'])
        self.assertFalse(evidence['stop']['send_authorization_consumed'])
        self.assertFalse(evidence['github_write'])

    def test_r9_g1_stops_before_send_on_stale_browser_clipboard(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX03-r9-G1'
        evidence = json.loads(
            (cycle / 'browser-staging-body-mismatch.json').read_text(
                encoding='utf-8'
            )
        )

        self.assertEqual(evidence['cycle_id'], 'EX03-R9-G1')
        self.assertEqual(
            evidence['starting_head'],
            '898f923c5537b8dc87ff4240106feb3335878ec2',
        )
        self.assertEqual(evidence['preflight']['status'], 'PASS_BEFORE_BROWSER_STAGING')
        self.assertEqual(evidence['preflight']['protected_file_count'], 233)
        self.assertEqual(evidence['preflight']['protected_mismatch_count'], 0)
        self.assertTrue(evidence['preflight']['work_matches_template'])
        self.assertTrue(evidence['preflight']['output_absent'])
        self.assertEqual(evidence['browser']['model_selected'], 'Think Deeper')
        self.assertTrue(evidence['browser']['initial_editor_blank'])
        self.assertEqual(evidence['browser']['attachment']['upload_count'], 1)
        self.assertTrue(evidence['browser']['attachment']['ui_chip_visible'])
        self.assertEqual(
            evidence['browser']['attachment']['sha256'],
            r9_acceptance.sha(
                ROOT / evidence['browser']['attachment']['path']
            ),
        )
        self.assertEqual(
            evidence['body_staging']['fixed_r9_source']['sha256'],
            r9_acceptance.sha(
                ROOT / evidence['body_staging']['fixed_r9_source']['path']
            ),
        )
        self.assertTrue(evidence['body_staging']['os_clipboard_readback']['exact_r9'])
        browser_clipboard = evidence['body_staging']['browser_clipboard_before_paste']
        self.assertEqual(
            browser_clipboard['sha256'],
            r9_acceptance.sha(ROOT / browser_clipboard['matches_path']),
        )
        self.assertTrue(browser_clipboard['exact_r8'])
        self.assertFalse(browser_clipboard['exact_r9'])
        self.assertEqual(
            evidence['body_staging']['set_value_from_browser_clipboard'],
            'ABORTED_BEFORE_INPUT_ON_HASH_MISMATCH',
        )
        self.assertTrue(
            evidence['body_staging']['os_clipboard_keyboard_paste_attempted']
        )
        editor = evidence['body_staging']['editor_after_paste']
        self.assertTrue(editor['contains_r8_marker'])
        self.assertFalse(editor['contains_r9_marker'])
        self.assertEqual(
            editor['exact_r8_bytes'],
            'NOT_PROVEN_WEB_EDITOR_RENDERING_CHANGED_WHITESPACE',
        )
        self.assertFalse(evidence['body_staging']['post_mismatch_correction_attempted'])
        self.assertEqual(
            evidence['actions'],
            {
                'browser_staging': 1,
                'bundle_upload': 1,
                'normal_m365_send': 0,
                'resend': 0,
                'generation': 0,
                'pad_import': 0,
                'pad_run': 0,
                'github_write': 0,
            },
        )
        self.assertEqual(evidence['pad']['status'], 'NOT_STARTED')
        self.assertEqual(evidence['pad']['run1'], 'NOT_RUN')
        self.assertEqual(evidence['pad']['run2'], 'NOT_RUN')
        self.assertEqual(
            evidence['filesystem']['work_sha256'],
            r9_acceptance.sha(
                ROOT / 'catalog/acceptance/issue38/runs/EX03-attempt1/work.xlsx'
            ),
        )
        self.assertEqual(
            evidence['filesystem']['template_sha256'],
            r9_acceptance.sha(
                ROOT / 'catalog/acceptance/issue38/fixtures/EX03/ひな形.xlsx'
            ),
        )
        self.assertFalse(evidence['filesystem']['output_exists'])
        self.assertEqual(
            evidence['decision']['status'],
            'STOPPED_BEFORE_SEND_STALE_BROWSER_CLIPBOARD_R8_BODY',
        )
        self.assertFalse(evidence['decision']['send_clicked'])
        self.assertFalse(evidence['decision']['send_authorization_consumed'])
        self.assertFalse(evidence['decision']['fixed_conditions_changed'])
        self.assertFalse(evidence['decision']['same_turn_retry_after_editor_mismatch'])

    def test_r9_g1_one_send_stops_before_pad_on_generation_safety_failure(self):
        cycle = ROOT / 'catalog/acceptance/issue38/cycles/EX03-r9-G1'
        live = json.loads((cycle / 'live-send.json').read_text(encoding='utf-8'))
        generation = json.loads(
            (cycle / 'generation-result.json').read_text(encoding='utf-8')
        )
        audit = json.loads(
            (cycle / 'generation-safety-audit.json').read_text(encoding='utf-8')
        )
        status = json.loads(
            (cycle / 'acceptance-status.json').read_text(encoding='utf-8')
        )
        verification = json.loads(
            (cycle / 'verification.json').read_text(encoding='utf-8')
        )
        protected = json.loads(
            (cycle / 'protected-files-after.json').read_text(encoding='utf-8')
        )

        self.assertEqual(live['candidate']['version'], '20260917-excel-r9')
        self.assertTrue(live['independence']['teaching_and_test_independence_confirmed'])
        self.assertEqual(live['actions']['normal_m365_send'], 1)
        self.assertEqual(live['actions']['resend'], 0)
        self.assertEqual(live['actions']['pad_import'], 0)
        self.assertEqual(live['actions']['pad_run'], 0)
        self.assertTrue(live['body']['visible_editor_serialization_exact'])
        self.assertEqual(
            live['body']['sha256'], r9_acceptance.sha(cycle / 'submitted-body.txt')
        )
        self.assertEqual(
            live['attachment']['sha256'],
            r9_acceptance.sha(ROOT / live['attachment']['path']),
        )

        raw = base64.b64decode(
            (cycle / 'generated-robin.clipboard.utf8.b64').read_text(
                encoding='ascii'
            )
        )
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            'dce9d6f01de53252050b53de46283563f56226b1635a2ccdcbd71d2dfd2636bf',
        )
        self.assertEqual(len(raw), 14471)
        self.assertFalse(raw.endswith(b'\r\n'))
        self.assertEqual(raw.count(b'\r\n'), 196)
        generated = (cycle / 'generated.robin').read_bytes()
        self.assertEqual(generated, raw.replace(b'\r\n', b'\n') + b'\n')
        self.assertEqual(
            hashlib.sha256(generated).hexdigest(),
            generation['code_capture']['repository_sha256'],
        )

        lines = raw.decode('utf-8').splitlines()
        self.assertEqual(len(lines), 197)
        self.assertEqual(lines[0], "SET TransferState TO $'''NOT_STARTED'''")
        self.assertEqual(lines[-1], 'END')
        self.assertNotIn(r'\[', raw.decode('utf-8'))
        self.assertNotIn(r'\]', raw.decode('utf-8'))
        self.assertIn(audit['defects'][0]['generated_fragment'], lines[49])
        self.assertIn(audit['defects'][1]['generated_fragment'], lines[89])
        self.assertEqual(audit['comparison']['unexpected_corruption_lines'], [50, 90])
        self.assertEqual(audit['comparison']['expected_r9_label_change_lines'], [63, 66])
        self.assertEqual(audit['powershell_parser']['generated_embedded_script_error_count'], 22)
        self.assertEqual(audit['powershell_parser']['independent_r9_support_script_error_count'], 0)
        self.assertFalse(audit['decision']['pad_import_authorized'])
        self.assertEqual(
            audit['decision']['status'],
            'FAIL_GENERATED_ROBIN_SYNTAX_CORRUPTION_STOP_BEFORE_PAD',
        )

        self.assertEqual(status['pad_import']['unmodified_paste_count'], 0)
        self.assertEqual(status['pad_import']['recopy_match'], 'NOT_RUN')
        self.assertEqual(status['runs']['pad_runs_used'], 0)
        self.assertEqual(status['runs']['run1'], 'NOT_RUN_STOPPED_BEFORE_PAD_IMPORT')
        self.assertEqual(
            status['runs']['run2'], 'NOT_RUN_RUN1_WAS_NOT_AUTHORIZED'
        )
        self.assertFalse(status['decision']['accepted'])
        self.assertEqual(verification['results'][1]['tests_run'], 55)
        self.assertEqual(verification['results'][1]['status'], 'PASS')
        self.assertFalse(verification['live_acceptance']['accepted'])
        self.assertTrue(status['artifacts']['legacy_558_failure_preserved'])
        self.assertEqual(
            status['scope']['existing_output_guard_live_path'],
            'REMAINS_UNCONFIRMED',
        )
        self.assertFalse(
            ROOT.joinpath(
                'catalog/acceptance/issue38/runs/EX03-attempt1/照合結果.xlsx'
            ).exists()
        )
        self.assertEqual(protected['protected_file_count'], 233)
        self.assertEqual(protected['protected_file_mismatch_count'], 0)
        self.assertEqual(len(protected['files']), 233)
        for record in protected['files']:
            self.assertTrue(record['matches'], record['path'])
            self.assertEqual(record['before_sha256'], record['after_sha256'])
            self.assertEqual(
                r9_acceptance.sha(ROOT / record['path']),
                record['after_sha256'],
                record['path'],
            )

    def test_r9_g1_action_time_verifier_is_read_only_and_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'sealed pre-send state'):
            r9_checkpoint.verify()

        frozen = ROOT / 'catalog/acceptance/issue38/cycles/EX03-r9-G1'
        with tempfile.TemporaryDirectory() as directory:
            clean = Path(directory) / 'cycle'
            shutil.copytree(frozen, clean)
            for name in r9_checkpoint.FORBIDDEN_PRE_SEND_FILES:
                path = clean / name
                if path.exists():
                    path.unlink()
            result = r9_checkpoint.verify(clean, verify_commit=False)
        self.assertEqual(
            result['status'],
            'READY_LOCAL_CHECKPOINT_AWAITING_EXPLICIT_AUTHORIZATION',
        )
        self.assertEqual(result['checkpoint_commit'], r9_checkpoint.CHECKPOINT_COMMIT)
        self.assertEqual(result['protected_file_count'], 233)
        self.assertEqual(result['protected_mismatch_count'], 0)
        self.assertTrue(result['work_matches_checkpoint'])
        self.assertTrue(result['output_absent'])
        self.assertFalse(result['live_browser_or_pad_state_inspected'])
        self.assertFalse(result['send_authorized_by_this_verification'])
        self.assertEqual(
            result['recorded_external_actions'],
            {
                'browser_staging': 0,
                'copilot_send': 0,
                'pad_import': 0,
                'pad_run': 0,
                'github_write': 0,
            },
        )

        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / 'cycle'
            shutil.copytree(frozen, changed)
            for name in r9_checkpoint.FORBIDDEN_PRE_SEND_FILES:
                path = changed / name
                if path.exists():
                    path.unlink()
            (changed / 'submitted-body.txt').write_bytes(
                (changed / 'submitted-body.txt').read_bytes() + b'changed'
            )
            with self.assertRaisesRegex(ValueError, 'Checkpoint hash mismatch'):
                r9_checkpoint.verify(changed, verify_commit=False)

    def test_r10_structural_audit_proves_response_boundary_without_repair(self):
        audit_root = (
            ROOT / 'catalog/acceptance/issue38/probes/ex03-r10-structural-fidelity'
        )
        analysis = json.loads((audit_root / 'analysis.json').read_text(encoding='utf-8'))
        comparison = analysis['r9_comparison']
        boundary = analysis['response_boundary']

        self.assertEqual(
            analysis['decision'],
            'PASS_R9_STRUCTURAL_FAILURE_BOUNDARY_READY_FOR_UNSENT_R10',
        )
        self.assertEqual(comparison['expected_vs_generated_differing_line_count'], 2)
        self.assertEqual(
            [item['line'] for item in comparison['differing_lines']], [50, 90]
        )
        self.assertEqual(comparison['backslash_open_bracket_count'], 0)
        self.assertEqual(comparison['backslash_close_bracket_count'], 0)
        self.assertTrue(boundary['dom_equals_raw_clipboard'])
        self.assertFalse(boundary['copy_or_pad_introduced_the_two_corruptions'])
        self.assertEqual(
            boundary['dom_sha256'],
            'dce9d6f01de53252050b53de46283563f56226b1635a2ccdcbd71d2dfd2636bf',
        )
        mismatched = [
            token
            for token, record in comparison['token_inventory'].items()
            if not record['matches_expected']
        ]
        self.assertEqual(
            mismatched,
            [
                '[string]',
                '[StringComparison]',
                '::GetFullPath(',
                '::OrdinalIgnoreCase',
                '::IsNullOrEmpty(',
            ],
        )
        self.assertTrue(
            all(
                item['teaching_count'] == 1 and item['generated_count'] == 0
                for item in comparison['fragment_inventory']['required']
            )
        )
        self.assertTrue(
            all(
                item['teaching_count'] == 0 and item['generated_count'] == 1
                for item in comparison['fragment_inventory']['forbidden']
            )
        )
        self.assertFalse(analysis['classification']['manual_repair'])
        self.assertEqual(analysis['scope']['copilot_send'], 0)
        self.assertEqual(analysis['scope']['pad_run'], 0)

        with tempfile.TemporaryDirectory() as directory:
            rebuilt = Path(directory) / 'audit'
            r10_analysis.analyze(rebuilt)
            self.assertEqual(
                (audit_root / 'analysis.json').read_bytes(),
                (rebuilt / 'analysis.json').read_bytes(),
            )
            self.assertEqual(
                (audit_root / 'report.md').read_bytes(),
                (rebuilt / 'report.md').read_bytes(),
            )

    def test_r10_keeps_independent_source_and_adds_structural_gate_only(self):
        version = ROOT / 'copilot/versions/20260917-excel-r10'
        r9 = ROOT / 'copilot/versions/20260917-excel-r9'
        manifest = json.loads((version / 'manifest.json').read_text(encoding='utf-8'))
        instruction = (version / 'agent-instructions.txt').read_text(encoding='utf-8')
        bundle = (version / 'knowledge/PAD-Robin-Knowledge-Bundle.txt').read_text(
            encoding='utf-8'
        )
        robin = (version / r10_builder.ROBIN_SUPPORT).read_text(encoding='utf-8')
        script = (version / r10_builder.SCRIPT_SUPPORT).read_bytes()
        contract = (version / r10_builder.FIDELITY_SUPPORT).read_text(encoding='utf-8')

        self.assertEqual(
            (version / r10_builder.ROBIN_SUPPORT).read_bytes(),
            (r9 / 'support/EX03-R9-Independent-PAD-Recopy.robin').read_bytes(),
        )
        self.assertEqual(
            script,
            (r9 / 'support/EX03-R9-Independent-FormatSandwich.ps1.txt').read_bytes(),
        )
        for token, count in r10_builder.TOKEN_COUNTS.items():
            self.assertEqual(robin.count(token), count, token)
        for fragment in r10_builder.REQUIRED_INVARIANT_FRAGMENTS:
            self.assertEqual(robin.count(fragment), 1, fragment)
            self.assertIn(fragment, contract)
        for fragment in r10_builder.FORBIDDEN_CORRUPTION_FRAGMENTS:
            self.assertEqual(robin.count(fragment), 0, fragment)
            self.assertIn(fragment, contract)
        self.assertEqual(robin.count(r'\['), 0)
        self.assertEqual(robin.count(r'\]'), 0)
        self.assertIn('Do only the listed data-slot substitutions', contract)
        self.assertIn('source-derived exact token counts', contract)
        self.assertIn('EX03 text mapping', instruction)
        self.assertIn('EX03 text source', instruction)
        for term in r10_builder.FIXED_COMPLETION_TERMS + r10_builder.UNIQUE_GRADER_STRINGS:
            self.assertNotIn(term, instruction)
            self.assertNotIn(term, bundle)
            self.assertNotIn(term, robin)
        self.assertNotIn(r10_builder.EXPECTED_TEXT, instruction)
        self.assertNotIn(r10_builder.EXPECTED_TEXT, robin)

        self.assertEqual(
            manifest['status'],
            'FROZEN_CANDIDATE_EX03_STRUCTURAL_FIDELITY_GATE_NOT_COPILOT_OR_RUNTIME_ACCEPTED',
        )
        self.assertEqual(manifest['base_candidate'], '20260917-excel-r9')
        self.assertEqual(manifest['base_commit'], r10_builder.BASE_COMMIT)
        self.assertFalse(manifest['inherits_live_acceptance'])
        self.assertEqual(
            manifest['evidence']['teaching_test_independence'],
            'PASS_R10_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_CURRENT_INSTRUCTION_BUNDLE_AND_SUPPORT',
        )
        self.assertTrue(manifest['evidence']['r9_response_dom_equals_raw_clipboard'])
        self.assertEqual(manifest['evidence']['expected_vs_generated_differing_lines'], 2)
        self.assertEqual(
            manifest['evidence']['expected_vs_generated_differing_line_numbers'], [50, 90]
        )
        self.assertTrue(manifest['evidence']['source_reused_exact_bytes'])
        self.assertFalse(manifest['evidence']['source_new_pad_capture_required'])
        self.assertTrue(manifest['evidence']['legacy_558_failure_preserved'])
        self.assertEqual(
            manifest['evidence']['existing_output_guard'], 'STATIC_ONLY_NOT_LIVE_TESTED'
        )

    def test_r10_rebuild_is_byte_identical_and_existing_destination_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'r10'
            r10_builder.build(destination)
            frozen = ROOT / 'copilot/versions' / r10_builder.VERSION
            for path in frozen.rglob('*'):
                if path.is_file():
                    self.assertEqual(
                        path.read_bytes(),
                        (destination / path.relative_to(frozen)).read_bytes(),
                        str(path),
                    )
            with self.assertRaisesRegex(ValueError, 'sealed'):
                r10_builder.build(destination)

    def test_r8_rebuild_is_byte_identical_and_existing_destination_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'r8'
            r8_builder.build(destination)
            frozen = ROOT / 'copilot/versions' / r8_builder.VERSION
            for path in frozen.rglob('*'):
                if path.is_file():
                    self.assertEqual(
                        path.read_bytes(),
                        (destination / path.relative_to(frozen)).read_bytes(),
                        str(path),
                    )
            with self.assertRaisesRegex(ValueError, 'sealed'):
                r8_builder.build(destination)


if __name__ == '__main__':
    unittest.main(verbosity=2)
