import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: {
    timeout: 10_000
  },
  use: {
    baseURL: process.env.UI_BASE_URL ?? "http://127.0.0.1:8848",
    headless: true,
    ignoreHTTPSErrors: true,
    chromiumSandbox: false,
    launchOptions: {
      args: ["--no-sandbox", "--disable-dev-shm-usage"]
    }
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ]
});
