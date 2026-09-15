// Synthetic acceptance inputs only. Does not generate Robin or a claimed PAD result.
// NODE_PATH must point to the bundled workspace node_modules.
import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const { Workbook, SpreadsheetFile } = await import(pathToFileURL(require.resolve('@oai/artifact-tool')));
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const base = path.join(root, 'catalog/acceptance/issue38');
try { await fs.access(path.join(base, 'freeze.json')); throw new Error('Frozen fixtures: do not regenerate'); }
catch (e) { if (e.code !== 'ENOENT') throw e; }
const sets = [
  {id:'EX02', files:['input-a.xlsx','input-b.xlsx','template.xlsx'], sheets:['Source A','Source B','Target A','Target B'], ranges:['B2:D3','A3:B5'], starts:['C4','B3'], values:[[['Alpha',12.5,0],['Beta',-3,100]],[['Gamma',7],['Delta',8],['Epsilon',9]]]},
  {id:'EX03', files:['入力い.xlsx','入力ろ.xlsx','ひな形.xlsx'], sheets:['受取明細','追加項目','集計先','追記先'], ranges:['D4:E6','B2:D3'], starts:['F7','D5'], values:[[['春',21],['夏',0],['秋',-4.5]],[['項目甲',42,'日本語'],['項目乙',6.25,'100%']]]},
];
const specs = [], expected = {};
for (const s of sets) {
  const dir = path.join(base, 'fixtures', s.id);
  await fs.mkdir(dir, {recursive:true});
  for (let i=0;i<3;i++) {
    const wb = Workbook.create();
    const decoy = wb.worksheets.add('Decoy');
    decoy.getRange('A1').values = [['DO NOT READ THIS SHEET']];
    decoy.getRange('B2:E6').values = [['WRONG_SHEET']];
    const names = i<2 ? [s.sheets[i]] : s.sheets.slice(2);
    for (const name of names) {
      const sheet = wb.worksheets.add(name);
      sheet.getRange('A1').values = [[i<2 ? 'SYNTHETIC INPUT' : 'KEEP TEMPLATE']];
      if (i<2) sheet.getRange(s.ranges[i]).values=s.values[i];
      else {
        sheet.getRange('A15').values=[['KEEP OUTSIDE']];
        sheet.getRange('B15').formulas=[['=2+3']];
        sheet.getRange('A15:B15').format.fill='#DDEBF7';
        sheet.getRange('B15').format.numberFormat='0.00';
        sheet.getRange('C3:H10').format.fill='#FFF2CC';
      }
    }
    for (let j=0;j<names.length+1;j++) {
      const sheet = wb.worksheets.getItemAt(j);
      sheet.getRange('A1:J16').format.font={name:'Yu Gothic',size:11};
      sheet.getRange('A1:J16').format.columnWidth=20;
      sheet.getRange('A1:J16').format.rowHeight=22;
    }
    wb.recalculate();
    const output=await SpreadsheetFile.exportXlsx(wb);
    await output.save(path.join(dir,s.files[i]));
    // Render all sheets to an ignored directory. Data/active-tab checked independently after export.
    const previews=path.join(root,'.local/issue38/previews',s.id);
    await fs.mkdir(previews,{recursive:true});
    for(let j=0;j<names.length+1;j++) {
      const name=wb.worksheets.getItemAt(j).name;
      const blob=await wb.render({sheetName:name,range:'A1:J16',scale:1,format:'png'});
      await fs.writeFile(path.join(previews,`${i}-${j}.png`),new Uint8Array(await blob.arrayBuffer()));
    }
  }
  specs.push({id:s.id,inputs:s.files.slice(0,2).map((file,i)=>({file:`fixtures/${s.id}/${file}`,sheet:s.sheets[i],range:s.ranges[i],target_sheet:s.sheets[i+2],target_start:s.starts[i]})),template:`fixtures/${s.id}/${s.files[2]}`,output:s.id==='EX02'?'result.xlsx':'照合結果.xlsx',initial_sheet:'Decoy'});
  expected[s.id]=s.values;
}
await fs.writeFile(path.join(base,'spec.json'),JSON.stringify({schema_version:1,cases:specs},null,2)+'\n');
await fs.writeFile(path.join(base,'expected.json'),JSON.stringify({schema_version:1,grader_only:true,matrices:expected},null,2)+'\n');
console.log('Synthetic fixture authoring complete; freeze only after independent readback.');
