import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const cycleDir = path.join(
  root,
  "catalog",
  "acceptance",
  "issue38",
  "cycles",
  "EX03-r11-file-aux1-existing-output-neg1",
);
const outputPath = path.join(
  root,
  "catalog",
  "acceptance",
  "issue38",
  "runs",
  "EX03-attempt1",
  "照合結果.xlsx",
);
const previewPath = path.join(cycleDir, "fixture-preview.png");
const inspectionPath = path.join(cycleDir, "fixture-workbook-inspection.json");

for (const target of [outputPath, previewPath, inspectionPath]) {
  try {
    await fs.access(target);
    throw new Error(`Refusing to overwrite existing fixture artifact: ${target}`);
  } catch (error) {
    if (error?.code !== "ENOENT") throw error;
  }
}

await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(cycleDir, { recursive: true });

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("GuardSentinel");
sheet.showGridLines = false;
sheet.getRange("A1:B6").values = [
  ["EX03-r11 existing-output guard fixture", null],
  ["Test ID", "EX03-R11-FILE-AUX1-EXISTING-OUTPUT-NEG1"],
  ["Purpose", "Pre-existing writable output; PAD must not overwrite it"],
  ["Expected branch", "OUTPUT_EXISTS_NO_WRITE"],
  ["Expected write/save actions", 0],
  ["Fixture status", "SYNTHETIC_WRITABLE_XLSX"],
];
sheet.getRange("A1:B6").format.font = { name: "Arial", size: 10, color: "#1F2937" };
sheet.getRange("A1:B1").format = {
  fill: "#1F4E78",
  font: { name: "Arial", size: 14, bold: true, color: "#FFFFFF" },
};
sheet.getRange("A2:A6").format = {
  fill: "#D9EAF7",
  font: { name: "Arial", size: 10, bold: true, color: "#1F2937" },
};
sheet.getRange("A1:B6").format.verticalAlignment = "center";
sheet.getRange("A2:A6").format.borders = {
  preset: "outside",
  style: "thin",
  color: "#9CA3AF",
};
sheet.getRange("B2:B6").format.borders = {
  preset: "outside",
  style: "thin",
  color: "#9CA3AF",
};
sheet.getRange("A1:A6").format.columnWidth = 34;
sheet.getRange("B1:B6").format.columnWidth = 58;
sheet.getRange("A1:B6").format.rowHeight = 22;

workbook.recalculate();
const tableInspection = await workbook.inspect({
  kind: "table",
  range: "GuardSentinel!A1:B6",
  include: "values,formulas",
  tableMaxRows: 10,
  tableMaxCols: 4,
  maxChars: 6000,
});
const errorInspection = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 50 },
  summary: "fixture formula error scan",
});

const preview = await workbook.render({
  sheetName: "GuardSentinel",
  range: "A1:B6",
  scale: 2,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
await fs.writeFile(
  inspectionPath,
  `${JSON.stringify(
    {
      schema_version: 1,
      test_id: "EX03-R11-FILE-AUX1-EXISTING-OUTPUT-NEG1",
      workbook: {
        sheets: ["GuardSentinel"],
        key_range: "GuardSentinel!A1:B6",
        intended_output_path: outputPath,
      },
      table_inspection_ndjson: tableInspection.ndjson,
      formula_error_scan_ndjson: errorInspection.ndjson,
      rendered_preview: previewPath,
      status: "PASS_CREATED_SIMPLE_SYNTHETIC_WRITABLE_XLSX",
    },
    null,
    2,
  )}\n`,
  "utf8",
);

console.log(
  JSON.stringify(
    {
      status: "PASS_CREATED_SIMPLE_SYNTHETIC_WRITABLE_XLSX",
      outputPath,
      previewPath,
      inspectionPath,
    },
    null,
    2,
  ),
);
