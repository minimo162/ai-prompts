import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { SpreadsheetFile, Workbook } = await import(
  pathToFileURL(require.resolve("@oai/artifact-tool")),
);

const outputDir = process.argv[2];
if (!outputDir) {
  throw new Error("Usage: node Build-SyntheticProbe.mjs <output-directory>");
}

await fs.mkdir(outputDir, { recursive: true });

function applyHeader(sheet) {
  sheet.getRange("A1:B1").format = {
    fill: "#244A73",
    font: { name: "Yu Gothic", size: 11, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: "#244A73" },
  };
  sheet.getRange("A1:B1").format.rowHeight = 24;
  sheet.getRange("A1:B2").format.columnWidth = 22;
}

async function saveAndPreview(workbook, sheetName, xlsxName, previewName) {
  workbook.recalculate();
  const inspection = await workbook.inspect({
    kind: "table",
    range: `${sheetName}!A1:B2`,
    include: "values,formulas",
    tableMaxRows: 2,
    tableMaxCols: 2,
    maxChars: 4000,
  });
  await fs.writeFile(
    path.join(outputDir, `${xlsxName}.inspect.ndjson`),
    `${inspection.ndjson}\n`,
    "utf8",
  );
  const preview = await workbook.render({
    sheetName,
    range: "A1:B2",
    scale: 2,
    format: "png",
  });
  await fs.writeFile(
    path.join(outputDir, previewName),
    new Uint8Array(await preview.arrayBuffer()),
  );
  const exported = await SpreadsheetFile.exportXlsx(workbook);
  await exported.save(path.join(outputDir, xlsxName));
}

const source = Workbook.create();
const sourceSheet = source.worksheets.add("Source");
sourceSheet.showGridLines = false;
sourceSheet.getRange("A1:B2").values = [
  ["Text source", "Numeric source"],
  ["100%", 42.5],
];
applyHeader(sourceSheet);
sourceSheet.getRange("A2:B2").format = {
  fill: "#EAF2F8",
  font: { name: "Yu Gothic", size: 11, color: "#162A3A" },
  horizontalAlignment: "right",
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: "#8EA9C1" },
};
sourceSheet.getRange("A2").format.numberFormat = "@";
sourceSheet.getRange("B2").format.numberFormat = "0.0";
sourceSheet.getRange("A2:B2").format.rowHeight = 24;
await saveAndPreview(source, "Source", "source.xlsx", "source-preview.png");

const template = Workbook.create();
const targetSheet = template.worksheets.add("Target");
targetSheet.showGridLines = false;
targetSheet.getRange("A1:B2").values = [
  ["Text destination", "Numeric destination"],
  ["BEFORE_TEXT", 7],
];
applyHeader(targetSheet);
targetSheet.getRange("A2").format = {
  fill: "#FFF2CC",
  font: { name: "Yu Gothic", size: 11, italic: true, color: "#7F6000" },
  horizontalAlignment: "left",
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: "#BF9000" },
};
targetSheet.getRange("B2").format = {
  fill: "#E2F0D9",
  font: { name: "Yu Gothic", size: 11, bold: true, color: "#375623" },
  horizontalAlignment: "right",
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: "#70AD47" },
};
targetSheet.getRange("A2").format.numberFormat = "General";
targetSheet.getRange("B2").format.numberFormat = "0.00";
targetSheet.getRange("A2:B2").format.rowHeight = 24;
await saveAndPreview(template, "Target", "template.xlsx", "template-preview.png");

console.log(`WROTE=${path.join(outputDir, "source.xlsx")}`);
console.log(`WROTE=${path.join(outputDir, "template.xlsx")}`);
