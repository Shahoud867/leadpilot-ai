import { test, expect } from "@playwright/test";
import type { Page } from "@playwright/test";
async function login(page: Page, account = "owner@margalla.example") {
  await page.goto("/");
  await page.getByLabel("Demo account").selectOption(account);
  await page.getByRole("button", { name: "Enter workspace" }).click();
  await expect(
    page.getByRole("heading", { name: /Good afternoon/ }),
  ).toBeVisible();
  await expect(
    page.getByText("Inquiry momentum", { exact: true }),
  ).toBeVisible();
}
async function nav(page: Page, name: string) {
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("button", { name, exact: name !== "Demo Lab" })
    .click();
  await expect(
    page.getByRole("heading", { name, exact: true }).first(),
  ).toBeVisible();
}
async function reset(page: Page) {
  await page.evaluate(async () => {
    const me = await (await fetch("/api/v1/auth/me")).json();
    await fetch("/api/v1/demo/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": me.csrf },
      body: JSON.stringify({ confirmation: "RESET SYNTHETIC DATA" }),
    });
  });
  await page.reload();
  await expect(
    page.getByText("Inquiry momentum", { exact: true }),
  ).toBeVisible();
}
test("all workspaces load without browser errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await login(page);
  for (const name of [
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
    await nav(page, name);
    await expect(page.locator(".error-banner")).toHaveCount(0);
  }
  expect(errors).toEqual([]);
});
test("manual capture persists and converts through guarded steps", async ({
  page,
}) => {
  await login(page);
  await reset(page);
  await page.getByRole("button", { name: "New lead", exact: true }).click();
  const form = page.getByRole("dialog", { name: "Capture a new inquiry" });
  await form.getByLabel("Display name").fill("E2E Ayesha Test");
  await form.getByLabel("Synthetic contact ID").fill("SYN-E2E-AYESHA");
  await form.getByLabel("Budget").fill("65000");
  await form.getByLabel("Consent", { exact: true }).selectOption("granted");
  await form.getByRole("button", { name: "Capture & run agents" }).click();
  const drawer = page.getByRole("dialog", { name: "Lead details" });
  await expect(
    drawer.getByRole("heading", { name: "E2E Ayesha Test" }),
  ).toBeVisible();
  await expect(drawer.getByText("Assigned", { exact: true })).toBeVisible();
  await drawer
    .getByRole("button", { name: "Simulate reply", exact: true })
    .click();
  await page.getByRole("button", { name: "Record reply" }).click();
  await expect(drawer.getByText("Contacted", { exact: true })).toBeVisible();
  await drawer.getByRole("button", { name: "Move stage", exact: true }).click();
  let modal = page.getByRole("dialog", { name: "Move opportunity" });
  await modal.getByLabel("Next stage").selectOption("qualified");
  await modal.getByRole("button", { name: "Confirm stage" }).click();
  await expect(drawer.getByText("Qualified", { exact: true })).toBeVisible();
  await drawer.getByRole("button", { name: "Move stage", exact: true }).click();
  modal = page.getByRole("dialog", { name: "Move opportunity" });
  await modal.getByLabel("Next stage").selectOption("appointment");
  await modal
    .getByLabel("Appointment (your local time)")
    .fill("2026-11-10T12:00");
  await modal.getByRole("button", { name: "Confirm stage" }).click();
  await expect(drawer.getByText("Appointment", { exact: true })).toBeVisible();
  await drawer.getByRole("button", { name: "Move stage", exact: true }).click();
  modal = page.getByRole("dialog", { name: "Move opportunity" });
  await modal.getByLabel("Next stage").selectOption("won");
  await modal.getByLabel("Verified deal value").fill("65000");
  await modal.getByRole("checkbox").check();
  await modal.getByRole("button", { name: "Confirm stage" }).click();
  await expect(drawer.getByText("Won", { exact: true })).toBeVisible();
  await drawer.getByRole("button", { name: "Close lead details" }).click();
  await page.reload();
  await nav(page, "All leads");
  await page.getByLabel("Filter leads").fill("E2E Ayesha Test");
  await expect(
    page.getByRole("button", { name: /E2E Ayesha Test/ }).first(),
  ).toBeVisible();
  await expect(
    page.getByRole("table").getByText("Won", { exact: true }),
  ).toBeVisible();
});
test("CSV preview and duplicate import update the directory", async ({
  page,
}) => {
  await login(page);
  await nav(page, "Lead inbox");
  await page.getByRole("button", { name: "Import CSV" }).first().click();
  const modal = page.getByRole("dialog", { name: "Import synthetic leads" });
  await modal.getByRole("button", { name: "Validate CSV" }).click();
  await expect(modal.getByText(/Preview: 1 new · 1 duplicates/)).toBeVisible();
  await modal.getByRole("button", { name: "Confirm import" }).click();
  await expect(modal.getByText(/Imported: 1 new · 1 duplicates/)).toBeVisible();
  await modal.getByRole("button", { name: "Close dialog" }).click();
  await page.getByLabel("Filter leads").fill("Ayesha CSV Test");
  await expect(
    page.getByRole("button", { name: /Ayesha CSV Test/ }).first(),
  ).toBeVisible();
});
test("Demo Lab exposes missed SLA, override and optimization outcomes", async ({
  page,
}) => {
  await login(page);
  await reset(page);
  await nav(page, "Demo Lab");
  await page.getByRole("button", { name: /The missed admission/ }).click();
  await expect(
    page.getByRole("heading", { name: "Scenario result · Sla" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Inspect lead 1", exact: true })
    .click();
  const drawer = page.getByRole("dialog", { name: "Lead details" });
  await drawer.getByRole("button", { name: "Decisions", exact: true }).click();
  await expect(drawer.getByRole("heading", { name: /Recovery/ })).toBeVisible();
  await drawer.getByRole("button", { name: "Close lead details" }).click();
  await page.getByRole("button", { name: /The manager has context/ }).click();
  await expect(
    page.getByRole("heading", { name: "Scenario result · Override" }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Capacity under pressure/ }).click();
  await expect(
    page.getByRole("heading", { name: "Scenario result · Capacity" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: /20 inquiries, one fair plan/ })
    .click();
  await expect(
    page.getByText("OPTIMIZED UTILITY", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "test-results/demo-lab.png",
    fullPage: true,
  });
});
test("viewer has no workflow write controls", async ({ page }) => {
  await login(page, "viewer@estates.example");
  await expect(
    page.getByRole("button", { name: "New lead", exact: true }),
  ).toHaveCount(0);
  await nav(page, "Demo Lab");
  await expect(
    page.getByRole("button", { name: /A new inquiry arrives/ }),
  ).toBeDisabled();
  const denied = await page.evaluate(async () => {
    const me = await (await fetch("/api/v1/auth/me")).json();
    return (
      await fetch("/api/v1/demo/clock/advance", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": me.csrf,
        },
        body: JSON.stringify({ minutes: 31 }),
      })
    ).status;
  });
  expect(denied).toBe(403);
});
test("mobile overview fits and navigation remains usable", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth + 1,
    ),
  ).toBe(false);
  await page.getByRole("button", { name: "Open navigation" }).click();
  await nav(page, "All leads");
  await expect(page.getByLabel("Filter leads")).toBeVisible();
  await page.screenshot({
    path: "test-results/mobile.png",
    fullPage: true,
  });
});

test("dialogs trap keyboard focus, close with Escape and restore focus", async ({
  page,
}) => {
  await login(page);
  const trigger = page.getByRole("button", { name: "New lead", exact: true });
  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "Capture a new inquiry" });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Close dialog" }).focus();
  await page.keyboard.press("Shift+Tab");
  expect(
    await dialog.evaluate((el) => el.contains(document.activeElement)),
  ).toBe(true);
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(trigger).toBeFocused();
  await nav(page, "All leads");
  await page.getByRole("table").getByRole("button").first().click();
  await expect(
    page.getByRole("dialog", { name: "Lead details" }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Lead details" })).toHaveCount(
    0,
  );
});
