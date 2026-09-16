"""EX03 fixed-parameter comparator regression; synthetic outputs are not PAD evidence."""
import importlib.util
import json
from pathlib import Path
import re
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
