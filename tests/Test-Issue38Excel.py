"""Non-live oracle tests. ZIP mutations are fault injection, never PAD output evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
module=importlib.util.spec_from_file_location('oracle',ROOT/'tools/Verify-Issue38Excel.py')
oracle=importlib.util.module_from_spec(module); module.loader.exec_module(oracle)
NS='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
q=lambda name:f'{{{NS}}}{name}'


def simulated_output(case_id, destination, mutation=None):
    spec=oracle.case_spec(case_id)
    changes=oracle.targets(spec)
    with ZipFile(oracle.BASE/spec['template']) as original, ZipFile(destination,'w') as result:
        for item in original.infolist():
            data=original.read(item.filename)
            for i,sheet in enumerate([spec['inputs'][0]['target_sheet'],spec['inputs'][1]['target_sheet']],2):
                if item.filename!=f'xl/worksheets/sheet{i}.xml': continue
                tree=ET.fromstring(data); rows=tree.find(q('sheetData'))
                for (name,address),(kind,value) in changes.items():
                    if name!=sheet: continue
                    rownum=oracle.coordinate_to_tuple(address)[0]
                    row=next((r for r in rows if r.attrib['r']==str(rownum)),None)
                    if row is None: row=ET.SubElement(rows,q('row'),{'r':str(rownum)})
                    cell=next((c for c in row if c.attrib.get('r')==address),None)
                    if cell is None: cell=ET.SubElement(row,q('c'),{'r':address})
                    for child in list(cell): cell.remove(child)
                    if kind=='text':
                        cell.set('t','inlineStr'); ET.SubElement(ET.SubElement(cell,q('is')),q('t')).text=value
                    else:
                        cell.set('t','n'); ET.SubElement(cell,q('v')).text=str(value)
                if mutation and i==2: mutation(tree)
                data=ET.tostring(tree,encoding='utf-8')
            result.writestr(item,data)


def cell(tree,address):
    return next(c for c in tree.iter(q('c')) if c.attrib.get('r')==address)


class ExcelOracleTests(unittest.TestCase):
    def test_preparation_preserves_template_and_refuses_repeat(self):
        prep_module=importlib.util.spec_from_file_location('prep',ROOT/'tools/Prepare-Issue38Run.py')
        prep=importlib.util.module_from_spec(prep_module); prep_module.loader.exec_module(prep)
        runs=oracle.BASE/'runs'; runs.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runs) as tmp:
            directory=Path(tmp)/'case'
            prep.prepare('EX02',directory)
            template=oracle.BASE/oracle.case_spec('EX02')['template']
            self.assertEqual(oracle.sha(directory/'work.xlsx'),oracle.sha(template))
            self.assertFalse((directory/'result.xlsx').exists())
            with self.assertRaisesRegex(ValueError,'collision'): prep.prepare('EX02',directory)
        oracle.check_frozen()

    def test_frozen_inputs_and_initial_sheet(self):
        oracle.check_frozen()
        self.assertEqual(oracle.verify_fixtures()['target_cells'],{'EX02':12,'EX03':12})

    def check_simulation(self,case_id,mutation=None,passes=False):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'simulation-not-pad.xlsx'
            simulated_output(case_id,target,mutation)
            report=oracle.compare(case_id,target)
            self.assertEqual(report['status']=='PASS_LOGICAL_OUTPUT_ONLY',passes,report)

    def test_correct_ex02_simulation(self): self.check_simulation('EX02',passes=True)
    def test_correct_ex03_simulation(self): self.check_simulation('EX03',passes=True)
    def test_wrong_value(self):
        self.check_simulation('EX02',lambda t:setattr(cell(t,'D4').find(q('v')),'text','999'))
    def test_number_as_text(self):
        def change(t):
            c=cell(t,'D4'); c.remove(c.find(q('v'))); c.set('t','inlineStr')
            ET.SubElement(ET.SubElement(c,q('is')),q('t')).text='12.5'
        self.check_simulation('EX02',change)
    def test_wrong_position(self):
        self.check_simulation('EX02',lambda t:cell(t,'D4').set('r','J4'))
    def test_outside_formula_changed(self):
        self.check_simulation('EX02',lambda t:setattr(cell(t,'B15').find(q('f')),'text','2+4'))
    def test_style_changed(self):
        self.check_simulation('EX02',lambda t:cell(t,'B15').set('s','0'))
    def test_missing_sheet(self):
        spec=copy.deepcopy(oracle.case_spec('EX02')); spec['inputs'][0]['sheet']='Missing Sheet'
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError,'Missing input sheet'):
            oracle.preflight(spec,Path(tmp)/'output.xlsx',Path(tmp)/'work.xlsx')
    def test_invalid_range(self):
        for r in ['D3:B2','A0:B1','A1:XFE2','A1:B1048577','A1','A1:A10001']:
            with self.subTest(r=r),self.assertRaises(ValueError): oracle.rectangle(r)
    def test_same_output(self):
        spec=oracle.case_spec('EX02')
        with tempfile.TemporaryDirectory() as tmp,self.assertRaisesRegex(ValueError,'must differ'):
            oracle.preflight(spec,oracle.BASE/spec['inputs'][0]['file'],Path(tmp)/'work.xlsx')
    def test_existing_output_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'output.xlsx'; out.write_bytes(b'KEEP')
            with self.assertRaisesRegex(ValueError,'collision'):
                oracle.preflight(oracle.case_spec('EX02'),out,Path(tmp)/'work.xlsx')
            self.assertEqual(out.read_bytes(),b'KEEP')


if __name__=='__main__': unittest.main(verbosity=2)
