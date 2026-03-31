import { test, expect } from "@playwright/test";

test("vendors page loads", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(err.message));

  const response = await page.goto("/vendors");
  console.log("Vendors status:", response?.status());

  if (response?.status() === 500) {
    const body = await page.textContent("body");
    console.log("Vendors body:", body?.slice(0, 500));
  }

  // Try the API directly
  const apiRes = await page.request.get("/api/search?q=&all=datasets");
  console.log("API status:", apiRes.status());
  if (apiRes.status() !== 200) {
    console.log("API body:", (await apiRes.text()).slice(0, 500));
  }
});

test("datasets page loads with vendor filter", async ({ page }) => {
  const response = await page.goto("/datasets?vendor=fred");
  console.log("Datasets status:", response?.status());

  if (response?.status() === 500) {
    const body = await page.textContent("body");
    console.log("Datasets body:", body?.slice(0, 500));
  }
});
