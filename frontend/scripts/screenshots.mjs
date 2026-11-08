// Screenshot every page at phone, tablet and desktop width, light and dark, logged in.
// Usage: node scripts/screenshots.mjs [baseUrl] [outDir] [passphrase] [paths...]
import { chromium } from "playwright";

const [base = "http://127.0.0.1:5173", out = "screenshots", pass = "local-dev", ...paths] = process.argv.slice(2);
const pages = paths.length ? paths : ["/"];
const widths = [390, 768, 1440];
const browser = await chromium.launch();
for (const scheme of ["light", "dark"]) {
  for (const width of widths) {
    const context = await browser.newContext({ viewport: { width, height: width === 390 ? 844 : 1000 }, colorScheme: scheme });
    await context.addInitScript((p) => localStorage.setItem("jbsearch.passphrase", p), pass);
    const page = await context.newPage();
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
    for (const path of pages) {
      await page.goto(base + path, { waitUntil: "networkidle" });
      await page.waitForTimeout(900);
      const name = `${out}/${(path.replace(/\W+/g, "-").replace(/^-|-$/g, "") || "home")}-${width}-${scheme}.png`;
      await page.screenshot({ path: name, fullPage: false });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      console.log(`${name}${overflow ? "  ⚠ horizontal overflow" : ""}`);
    }
    if (errors.length) console.log(`  console errors at ${width}/${scheme}:`, errors);
    await context.close();
  }
}
await browser.close();
