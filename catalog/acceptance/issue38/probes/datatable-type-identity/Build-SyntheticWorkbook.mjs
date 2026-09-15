import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

// NODE_PATH must point to the bundled workspace node_modules.
const require = createRequire(import.meta.url);
const { SpreadsheetFile, Workbook } = await import(
  pathToFileURL(require.resolve("@oai/artifact-tool")),
);

const outputPath = process.argv[2];
if (!outputPath) {
  throw new Error("Usage: node Build-SyntheticWorkbook.mjs <output.xlsx>");
}

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("TypeProbe");

sheet.showGridLines = false;
sheet.getRange("A1:B2").values = [
  ["数値セル", "文字列セル"],
  [1, "1"],
];
sheet.getRange("A1:B2").format.font = { name: "Arial", size: 11, color: "#172033" };
sheet.getRange("A1:B1").format = {
  fill: "#274060",
  font: { name: "Arial", size: 11, bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: "#274060" },
};
sheet.getRange("A2:B2").format = {
  fill: "#F7F9FC",
  font: { name: "Arial", size: 11, color: "#172033" },
  horizontalAlignment: "right",
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: "#BCC7D6" },
};
sheet.getRange("A2").format.numberFormat = "0";
sheet.getRange("B2").format.numberFormat = "@";
sheet.getRange("A1:B2").format.columnWidth = 18;
sheet.getRange("A1:B1").format.rowHeight = 24;
sheet.getRange("A2:B2").format.rowHeight = 24;

workbook.recalculate();

const inspected = await workbook.inspect({
  kind: "table",
  range: "TypeProbe!A1:B2",
  include: "values,formulas",
  tableMaxRows: 2,
  tableMaxCols: 2,
  maxChars: 3000,
});
console.log(inspected.ndjson);

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
