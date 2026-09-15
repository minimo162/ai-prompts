"""EX02 diagnostics and reproducible package regression; synthetic fault injection only."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


old_tests = load('old_tests', 'tests/Test-Issue38Excel.py')
new = load('diagnostic', 'tools/Compare-Issue38Ex02.py')
builder = load('builder', 'tools/Build-Issue38Ex02Candidate.py')


class Ex02Tests(unittest.TestCase):
    def simulate(self, mutate=None):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'simulated.xlsx'
            old_tests.simulated_output('EX02', output, mutate)
            return new.compare(output)

    def test_positive_independent_output_is_not_runtime_pass(self):
        result = self.simulate()
        self.assertEqual(result['status'], 'PASS_LOGICAL_OUTPUT_ONLY')
        self.assertEqual(result['checks']['target_values_types_positions']['checked'], 12)
        self.assertEqual(result['checks']['outside_values_types_formulas']['checked'], 468)
        self.assertEqual(result['flow_internal_type_check'], 'NOT_PROVEN')
        self.assertEqual(result['pad_execution'], 'NOT_ASSERTED')

    def test_number_one_and_text_one_remain_different(self):
        self.assertNotEqual(new.legacy.typed(1), new.legacy.typed('1'))
        self.assertNotEqual(new.legacy.typed(True), new.legacy.typed(1))
        def mutate(tree):
            cell = old_tests.cell(tree, 'D4')
            cell.remove(cell.find(old_tests.q('v')))
            cell.set('t', 'inlineStr')
            ET.SubElement(ET.SubElement(cell, old_tests.q('is')), old_tests.q('t')).text = '12.5'
        result = self.simulate(mutate)
        mismatch = result['checks']['target_values_types_positions']['mismatches'][0]
        self.assertEqual(mismatch['expected'], ['number', 12.5])
        self.assertEqual(mismatch['actual'], ['text', '12.5'])
        self.assertEqual(result['status'], 'FAIL')

    def test_wrong_value_detected(self):
        result = self.simulate(lambda t: setattr(old_tests.cell(t, 'D4').find(old_tests.q('v')), 'text', '999'))
        self.assertEqual(result['failure_counts']['values_types_positions'], 1)

    def test_wrong_position_detected(self):
        def move(tree):
            row = next(r for r in tree.iter(old_tests.q('row')) if r.attrib['r'] == '4')
            # Remove the existing empty J4 so the injection is a valid moved cell,
            # not duplicate XML addresses where openpyxl can keep the later cell.
            row.remove(old_tests.cell(tree, 'J4'))
            old_tests.cell(tree, 'D4').set('r', 'J4')
        result = self.simulate(move)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(len(result['checks']['outside_values_types_formulas']['mismatches']), 1)

    def test_outside_formula_detected(self):
        result = self.simulate(lambda t: setattr(old_tests.cell(t, 'B15').find(old_tests.q('f')), 'text', '2+4'))
        self.assertEqual(result['checks']['outside_values_types_formulas']['mismatches'][0]['actual'], ['formula', '=2+4'])

    def test_style_and_dimension_negatives_remain_fail(self):
        def row_height(t):
            next(t.iter(old_tests.q('row'))).set('ht', '99')
        for mutate, category in [(lambda t: old_tests.cell(t, 'B15').set('s', '0'), 'styles'),
                                 (row_height, 'row_dimensions')]:
            with self.subTest(category=category):
                result = self.simulate(mutate)
                self.assertEqual(result['status'], 'FAIL')
                self.assertGreater(result['failure_counts'][category], 0)

    def test_legacy_558_failures_are_preserved(self):
        result = new.compare(new.legacy.BASE / 'probes/matrix-write/run2/result.xlsx')
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(len(result['legacy']['failures']), 558)
        self.assertEqual(result['checks']['target_values_types_positions']['mismatches'], [])
        self.assertEqual(result['checks']['outside_values_types_formulas']['mismatches'], [])
        self.assertEqual(result['native_styles'], 'NOT_RUN_BY_THIS_COMPARATOR')

    def test_rebuild_is_byte_identical_and_existing_version_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / 'r4'
            builder.build(dest)
            frozen = ROOT / 'copilot/versions' / builder.VERSION
            for p in frozen.rglob('*'):
                if p.is_file():
                    self.assertEqual(p.read_bytes(), (dest / p.relative_to(frozen)).read_bytes(), str(p))
            with self.assertRaisesRegex(ValueError, 'sealed'):
                builder.build(dest)

    def test_example_does_not_write_outside_missing_output_branch(self):
        lines = builder.assembled_example().splitlines()
        self.assertEqual(lines[3], 'ELSE')
        self.assertEqual(lines[-1], 'END')
        self.assertTrue(all(l.startswith('    ') for l in lines if l.lstrip().startswith('Excel.')))
        self.assertFalse(any(l.strip() == 'EXIT' for l in lines))
        self.assertIn("    SET TypeState TO $'''NOT_PROVEN'''", lines)
        self.assertEqual(sum(l.strip() == 'IF SourceCell = SavedCell THEN' for l in lines), 12)


if __name__ == '__main__':
    unittest.main(verbosity=2)
