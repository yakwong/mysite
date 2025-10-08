import { test, expect } from "@playwright/test";
import { UI_BASE_URL, UI_USERNAME, UI_PASSWORD } from "./support/env";

test.describe("钉钉离职人员同步联调", () => {
  test("触发同步并校验离职人员显示完整信息", async ({ page }, testInfo) => {
    await test.step("登录后台", async () => {
      await page.goto(`${UI_BASE_URL}/#/login`);
      await page.getByPlaceholder("邮箱/用户名/手机号").fill(UI_USERNAME);
      await page.getByPlaceholder("密码").fill(UI_PASSWORD);
      await Promise.all([
        page.waitForResponse(response => response.url().includes("/api/user/login/") && response.status() === 200),
        page.getByRole("button", { name: "登录" }).click()
      ]);
      await expect(page).toHaveURL(/#/);
    });

    await test.step("导航至人员数据页并切换到离职人员", async () => {
      await page.goto(`${UI_BASE_URL}/#/dingtalk/users`);
      await page.waitForLoadState("networkidle");
      await page.getByRole("tab", { name: "离职人员" }).click();
      await page.waitForTimeout(500); // 等待表格完成渲染
    });

    await test.step("拦截同步请求并触发一次同步", async () => {
      await page.route("**/api/dingtalk/**/sync/", async route => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ success: true, data: {}, msg: "离职人员同步完成" })
        });
      });

      await Promise.all([
        page.waitForResponse(response => response.url().includes("/api/dingtalk/") && response.request().method() === "POST"),
        page.getByRole("button", { name: "同步离职人员" }).click()
      ]);

      await expect(page.getByText("已触发离职人员同步任务")).toBeVisible();
    });

    await test.step("校验离职人员信息完整并截图", async () => {
      const targetRow = page.locator(".el-table__body-wrapper tbody tr", { hasText: "playwright-demo-user" });
      await expect(targetRow).toContainText("张同步");
      await expect(targetRow).toContainText("13100001111");

      const screenshotPath = testInfo.outputPath("dimission-table.png");
      await page.screenshot({ path: screenshotPath, fullPage: true });
      await testInfo.attach("dimission-table", { path: screenshotPath, contentType: "image/png" });
    });
  });
});
