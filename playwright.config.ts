/**
 * Playwright config shaped for streaming AI responses.
 *
 * This ships live, in the place Playwright looks for it. Nothing copies it anywhere: point
 * `testDir` at your tests and edit it in place. Pin the exact version:
 *
 *     npm install --save-dev @playwright/test@1.62.0     // Apache-2.0
 *
 * runwAI itself is Python, YAML and Markdown and has no `e2e/` directory, so no gate here
 * runs this. It is exercised structurally — `.runwai/tools/validate_helpers.py` checks that the
 * version above matches the one README.md documents.
 *
 * WHY THIS DIFFERS FROM THE DEFAULT CONFIG
 *
 * Testing a streaming response breaks the assumptions behind most default settings. Tokens
 * arrive incrementally, so the DOM is *continuously* changing rather than settling: any
 * assertion racing the stream is flaky, and `networkidle` never fires while a response is
 * open. The adjustments below exist for that reason and are commented individually.
 *
 * Structure follows vercel/ai (Apache-2.0, eb16508f); the file is our own.
 */

import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",

  // Streaming assertions poll until the stream settles. The default 5s expect timeout
  // fails on a response that is still arriving but perfectly healthy.
  expect: { timeout: 15_000 },

  // A full streamed exchange plus setup is routinely slower than the 30s default.
  timeout: 90_000,

  // Fail the build if a `test.only` was committed. A focused test that reaches main
  // silently disables the rest of the suite.
  forbidOnly: !!process.env.CI,

  // Retries mask flakiness, and flakiness in a streaming test usually means a real race.
  // One retry in CI to absorb genuine network noise; none locally, where you want to see it.
  retries: process.env.CI ? 1 : 0,

  // Streaming tests are IO-bound, not CPU-bound, so they parallelise well — but a shared
  // rate-limited model endpoint does not. Keep CI serial unless you have per-worker keys.
  fullyParallel: true,
  workers: process.env.CI ? 1 : undefined,

  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : [["list"]],

  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:3000",

    // Traces and video only on a retry: they are large, and you only need them for the
    // run that actually failed.
    trace: "on-first-retry",
    video: "retain-on-failure",
    screenshot: "only-on-failure",

    // Individual actions still get a tight bound. It is the *assertion* timeout that needs
    // to be generous for streaming, not the click that starts it.
    actionTimeout: 10_000,
    navigationTimeout: 30_000,
  },

  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],

  webServer: {
    command: "npm run dev",
    url: process.env.BASE_URL ?? "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});

/**
 * PATTERNS FOR ASSERTING ON A STREAM
 *
 * Do NOT use `waitForLoadState("networkidle")` — an open stream means the network is never
 * idle, so this hangs until it times out.
 *
 * Wait for the stream to *finish* rather than for a duration:
 *
 *     await expect(page.getByTestId("response")).toContainText("expected fragment");
 *     await expect(page.getByTestId("stream-status")).toHaveAttribute("data-done", "true");
 *
 * Expose a completion signal from the application (an attribute, a disabled stop button)
 * and assert on that. `expect(...).toContainText()` auto-retries, so it tolerates partial
 * output arriving; `textContent()` read once does not, and is the usual source of flakes.
 *
 * Assert the *shape* of output, never its exact wording. A model that phrases an answer
 * differently has not regressed; a test asserting a verbatim sentence will fail on a
 * correct response, get marked flaky, and then get deleted.
 */
