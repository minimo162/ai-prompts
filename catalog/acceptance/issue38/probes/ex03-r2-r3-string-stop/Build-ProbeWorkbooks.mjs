import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { SpreadsheetFile, Workbook } = await import(
  pathToFileURL(require.resolve("@oai/artifact-tool")),
);

const outputDir = path.resolve(path.dirname(new URL(import.meta.url).pathname.slice(1)));

function styleHeader(sheet) {
  sheet.getRange("A1:D1").format = {
    fill: "#244A73",
    font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: "#244A73" },
  };
  sheet.getRange("A1:D1").format.rowHeight = 24;
  sheet.getRange("A1:D2").format.columnWidth = 25;
}

async function saveWorkbook(workbook, sheetName, fileName, previewName) {
  workbook.recalculate();
  const inspection = await workbook.inspect({
    kind: "table",
    range: `${sheetName}!A1:D2`,
    include: "values,formulas",
    tableMaxRows: 2,
    tableMaxCols: 4,
    maxChars: 6000,
  });
  await fs.writeFile(
    path.join(outputDir, `${fileName}.inspect.ndjson`),
    `${inspection.ndjson}\n`,
    "utf8",
  );
  const preview = await workbook.render({
    sheetName,
    range: "A1:D2",
    scale: 2,
    format: "png",
  });
  await fs.writeFile(
    path.join(outputDir, previewName),
    new Uint8Array(await preview.arrayBuffer()),
  );
  const exported = await SpreadsheetFile.exportXlsx(workbook);
  await exported.save(path.join(outputDir, fileName));
}

await fs.mkdir(outputDir, { recursive: true });

const source = Workbook.create();
const sourceSheet = source.worksheets.add("Source");
sourceSheet.showGridLines = false;
sourceSheet.getRange("A1:D2").values = [
  ["Apostrophe", "Quotes and line break", "Percent text", "Number"],
  ["O'Brien", "He said \"Go\"\nSecond line 'quoted'", "100%", 42.5],
];
styleHeader(sourceSheet);
sourceSheet.getRange("A2:C2").format = {
  fill: "#EAF2F8",
  font: { name: "Arial", size: 10, color: "#162A3A" },
  horizontalAlignment: "left",
  verticalAlignment: "center",
  wrapText: true,
  borders: { preset: "outside", style: "thin", color: "#8EA9C1" },
};
sourceSheet.getRange("D2").format = {
  fill: "#E2F0D9",
  font: { name: "Arial", size: 10, color: "#375623" },
  horizontalAlignment: "right",
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: "#70AD47" },
};
sourceSheet.getRange("A2:C2").format.numberFormat = "@";
sourceSheet.getRange("D2").format.numberFormat = "0.00";
sourceSheet.getRange("A2:D2").format.rowHeight = 38;
await saveWorkbook(source, "Source", "source.xlsx", "source-preview.png");

const template = Workbook.create();
const targetSheet = template.worksheets.add("Target");
targetSheet.showGridLines = false;
targetSheet.getRange("A1:D2").values = [
  ["Apostrophe target", "Quoted target", "Percent target", "Numeric target"],
  ["BEFORE_A", "BEFORE_B", "BEFORE_C", 7],
];
styleHeader(targetSheet);
targetSheet.getRange("A2:C2").format = {
  fill: "#FFF2CC",
  font: { name: "Arial", size: 10, italic: true, color: "#7F6000" },
  horizontalAlignment: "left",
  verticalAlignment: "center",
  wrapText: true,
  borders: { preset: "outside", style: "thin", color: "#BF9000" },
};
targetSheet.getRange("D2").format = {
  fill: "#E2F0D9",
  font: { name: "Arial", size: 10, bold: true, color: "#375623" },
  horizontalAlignment: "right",
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: "#70AD47" },
};
targetSheet.getRange("A2").format.numberFormat = "General";
targetSheet.getRange("B2").format.numberFormat = "0.00";
targetSheet.getRange("C2").format.numberFormat = "General";
targetSheet.getRange("D2").format.numberFormat = "0.00";
targetSheet.getRange("A2:D2").format.rowHeight = 38;
await saveWorkbook(template, "Target", "template.xlsx", "template-preview.png");

console.log(`WROTE=${path.join(outputDir, "source.xlsx")}`);
console.log(`WROTE=${path.join(outputDir, "template.xlsx")}`);

// artifact-tool can leave a non-zero exit code after successful rendering.
process.exitCode = 0;
