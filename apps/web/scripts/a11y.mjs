import { chromium } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fs from "node:fs";
import path from "node:path";
const browser = await chromium.launch({
  headless: true,
  ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE
    ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE }
    : {}),
  args: ["--no-sandbox"],
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
});
const page = await context.newPage();
const reports = [];
async function scan(name, selector) {
  let builder = new AxeBuilder({ page }).withTags([
    "wcag2a",
    "wcag2aa",
    "wcag21aa",
  ]);
  if (selector) builder = builder.include(selector);
  const result = await builder.analyze();
  reports.push({ page: name, violations: result.violations });
}
await page.goto(process.env.DEMO_URL || "http://localhost:5173");
await page.getByRole("button", { name: "Enter workspace" }).waitFor();
await scan("Sign in");
await page.getByRole("button", { name: "Enter workspace" }).click();
await page.getByText("Inquiry momentum", { exact: true }).waitFor();
for (const name of [
  "Overview",
  "Lead inbox",
  "All leads",
  "Smart priority",
  "Qualification",
  "Assignment board",
  "Sales pipeline",
  "Follow-ups",
  "Recovery ledger",
  "Analytics",
  "Decision trace",
  "Demo Lab",
  "Team & settings",
]) {
  if (name !== "Overview")
    await page
      .getByRole("navigation")
      .getByRole("button", { name, exact: true })
      .click();
  await page.waitForTimeout(350);
  await scan(name);
}
await page.getByRole("button", { name: "New lead", exact: true }).click();
await scan("Capture dialog", '[role="dialog"]');
await page.getByRole("button", { name: "Close dialog" }).click();
await page
  .getByRole("navigation")
  .getByRole("button", { name: "All leads", exact: true })
  .click();
await page.getByRole("table").getByRole("button").first().click();
await page.getByText("SYNTHETIC CONTACT", { exact: true }).waitFor();
for (const name of ["Overview", "Timeline", "Messages", "Decisions", "Tasks"]) {
  await page
    .getByRole("dialog", { name: "Lead details" })
    .getByRole("button", { name, exact: true })
    .click();
  await scan("Lead detail · " + name, '[role="dialog"]');
}
await page.getByRole("button", { name: "Close lead details" }).click();
await page.getByLabel("Stage filter").selectOption("appointment");
await page
  .getByRole("table")
  .getByText("Appointment", { exact: true })
  .first()
  .waitFor();
await page.getByRole("table").getByRole("button").first().click();
await page.getByText("SYNTHETIC CONTACT", { exact: true }).waitFor();
await page
  .getByRole("dialog", { name: "Lead details" })
  .getByRole("button", { name: "Messages", exact: true })
  .click();
await scan("Lead detail · Populated messages", '[role="dialog"]');
const out = path.resolve("../../docs/verification/accessibility.json");
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, JSON.stringify(reports, null, 2));
console.log(
  JSON.stringify(
    reports.map((r) => ({
      page: r.page,
      violations: r.violations.map((v) => ({
        id: v.id,
        nodes: v.nodes.length,
        examples: v.nodes.slice(0, 2).map((n) => n.failureSummary),
      })),
    })),
    null,
    2,
  ),
);
await browser.close();
if (reports.some((r) => r.violations.length)) process.exitCode = 1;
