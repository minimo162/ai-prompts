"""EX03 fixed-parameter comparator regression; synthetic outputs are not PAD evidence."""
import importlib.util
from pathlib import Path
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
