import { test, expect } from "@playwright/test";

/**
 * Tests that navigating between the three top-level nav items
 * (Datasets, Domains, Fields) does NOT cause the content area
 * to shift vertically. Every page should have a consistent
 * gray title bar between the AppHeader and the content.
 */

async function getContentTop(page: import("@playwright/test").Page) {
  // The first element after the gray PageTitle/Breadcrumbs bar.
  // We measure the bottom edge of the title bar to detect shifts.
  const titleBar = page.locator('[data-testid="page-title-bar"]');
  const breadcrumbs = page.locator('[data-testid="breadcrumbs-bar"]');

  // Try page-title-bar first, then breadcrumbs-bar
  let box = await titleBar.boundingBox().catch(() => null);
  if (!box) {
    box = await breadcrumbs.boundingBox().catch(() => null);
  }
  return box;
}

test.describe("Layout stability across nav items", () => {
  test("title bar is present and same height on all top-level pages", async ({
    page,
  }) => {
    // Visit Datasets page (home)
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    const datasetsBar = await getContentTop(page);
    expect(datasetsBar, "Datasets page should have a title bar").toBeTruthy();

    // Visit Domains page
    await page.click('a[href="/domains"]');
    await page.waitForLoadState("networkidle");
    const domainsBar = await getContentTop(page);
    expect(domainsBar, "Domains page should have a title bar").toBeTruthy();

    // Visit Fields page
    await page.click('a[href="/fields"]');
    await page.waitForLoadState("networkidle");
    const fieldsBar = await getContentTop(page);
    expect(fieldsBar, "Fields page should have a title bar").toBeTruthy();

    // Visit Vendors page
    await page.click('a[href="/vendors"]');
    await page.waitForLoadState("networkidle");
    const vendorsBar = await getContentTop(page);
    expect(vendorsBar, "Vendors page should have a title bar").toBeTruthy();

    // All four bars should have the same position and dimensions (no vertical or horizontal shift)
    expect(datasetsBar!.x).toBeCloseTo(domainsBar!.x, 0);
    expect(datasetsBar!.x).toBeCloseTo(fieldsBar!.x, 0);
    expect(datasetsBar!.x).toBeCloseTo(vendorsBar!.x, 0);
    expect(datasetsBar!.y).toBeCloseTo(domainsBar!.y, 0);
    expect(datasetsBar!.y).toBeCloseTo(fieldsBar!.y, 0);
    expect(datasetsBar!.y).toBeCloseTo(vendorsBar!.y, 0);
    expect(datasetsBar!.width).toBeCloseTo(domainsBar!.width, 0);
    expect(datasetsBar!.width).toBeCloseTo(fieldsBar!.width, 0);
    expect(datasetsBar!.width).toBeCloseTo(vendorsBar!.width, 0);
    expect(datasetsBar!.height).toBeCloseTo(domainsBar!.height, 0);
    expect(datasetsBar!.height).toBeCloseTo(fieldsBar!.height, 0);
    expect(datasetsBar!.height).toBeCloseTo(vendorsBar!.height, 0);
  });

  test("navigating to /datasets also has title bar", async ({ page }) => {
    await page.goto("/datasets");
    await page.waitForLoadState("networkidle");
    const bar = await getContentTop(page);
    expect(bar, "/datasets page should have a title bar").toBeTruthy();
  });

  test("subpages have breadcrumbs bar at same position", async ({ page }) => {
    // Go to home first to get the baseline position
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    const homeBar = await getContentTop(page);
    expect(homeBar).toBeTruthy();

    // Navigate to a domain detail page (if any domain links exist)
    await page.click('a[href="/domains"]');
    await page.waitForLoadState("networkidle");

    // Click first domain card link if available
    const domainLink = page.locator('a[href^="/domains/"]').first();
    if (await domainLink.isVisible()) {
      await domainLink.click();
      await page.waitForLoadState("networkidle");
      const subBar = await getContentTop(page);
      expect(
        subBar,
        "Domain detail page should have breadcrumbs bar"
      ).toBeTruthy();
      expect(subBar!.y).toBeCloseTo(homeBar!.y, 0);
      expect(subBar!.height).toBeCloseTo(homeBar!.height, 0);
    }
  });
});
