import { test, expect } from "@playwright/test";
import { UI_BASE_URL, UI_USERNAME, UI_PASSWORD } from "./support/env";

test.describe("钉钉离职人员同步联调", () => {
  test("触发同步并校验离职人员显示完整信息", async ({ page }, testInfo) => {
    const loginResponse = {
      success: true,
      data: {
        avatar: "",
        username: "admin",
        nickname: "管理员",
        roles: ["admin"],
        permissions: ["dingtalk.view"],
        accessToken: "mock-access-token",
        refreshToken: "mock-refresh-token",
        expires: "2099/12/31 23:59:59"
      },
      msg: "ok"
    };

    const asyncRoutesResponse = {
      success: true,
      data: [],
      msg: "ok"
    };

    const configResponse = {
      success: true,
      data: [
        {
          id: "default",
          name: "默认钉钉配置",
          tenant_id: "tenant-1",
          app_key: "demo-key",
          app_secret: "demo-secret",
          agent_id: "100000",
          enabled: true,
          sync_users: true,
          sync_departments: true,
          sync_attendance: false,
          callback_url: "",
          callback_token: "",
          callback_aes_key: "",
          schedule: {},
          remark: "playwright"
        }
      ],
      msg: "ok",
      page: 1,
      limit: 10,
      total: 1
    };

    const activeUsersResponse = {
      success: true,
      data: [],
      msg: "ok",
      page: 1,
      limit: 10,
      total: 0
    };

    const dimissionUsersResponse = {
      success: true,
      data: [
        {
          id: "dimission-1",
          userid: "playwright-demo-user",
          config_id: "default",
          name: "张同步",
          mobile: "+86-13100001111",
          main_dept_name: "技术中心",
          last_work_day: "2025-09-30",
          leave_time: "2025-10-01T09:30:00+08:00",
          leave_reason: "个人原因",
          status: 2,
          handover_userid: "manager-1",
          job_number: "J9001",
          voluntary_reasons: [],
          passive_reasons: [],
          dept_ids: [101],
          source_info: {},
          create_time: "2025-10-01T09:31:00+08:00",
          update_time: "2025-10-01T09:31:00+08:00"
        }
      ],
      msg: "ok",
      page: 1,
      limit: 10,
      total: 1
    };

    await test.step("准备接口拦截", async () => {
      await page.route("**/api/user/login/**", async route => {
        if (route.request().method() === "POST") {
          await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(loginResponse) });
        } else {
          await route.fallback();
        }
      });

      await page.route("**/api/system/asyncroutes/**", async route => {
        if (route.request().method() === "GET") {
          await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(asyncRoutesResponse) });
        } else {
          await route.fallback();
        }
      });

      await page.route("**/api/dingtalk/configs/**", async route => {
        if (route.request().method() === "GET") {
          await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(configResponse) });
        } else {
          await route.fallback();
        }
      });

      await page.route("**/api/dingtalk/users/**", async route => {
        if (route.request().method() === "GET") {
          await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(activeUsersResponse) });
        } else {
          await route.fallback();
        }
      });

      await page.route("**/api/dingtalk/dimission-users/**", async route => {
        if (route.request().method() === "GET") {
          await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(dimissionUsersResponse) });
        } else {
          await route.fallback();
        }
      });
    });

    await test.step("登录后台", async () => {
      await page.goto(`${UI_BASE_URL}/#/login`);
      await page.getByPlaceholder("邮箱/用户名/手机号").fill(UI_USERNAME);
      await page.getByPlaceholder("密码").fill(UI_PASSWORD);
      await Promise.all([page.waitForResponse(response => response.url().includes("/api/user/login/") && response.status() === 200), page.getByRole("button", { name: "登录" }).click()]);
      await expect(page).toHaveURL(/#/);
    });

    await test.step("导航至人员数据页并切换到离职人员", async () => {
      await page.goto(`${UI_BASE_URL}/#/dingtalk/users`);
      await page.waitForLoadState("networkidle");
      await expect(page).toHaveURL(/dingtalk\/users/);
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

      await Promise.all([page.waitForResponse(response => response.url().includes("/api/dingtalk/") && response.request().method() === "POST"), page.getByRole("button", { name: "同步离职人员" }).click()]);

      await expect(page.getByText("已触发离职人员同步任务")).toBeVisible();
    });

    await test.step("校验离职人员信息完整并截图", async () => {
      const targetRow = page.locator(".el-table__body-wrapper tbody tr", { hasText: "playwright-demo-user" });
      await expect(targetRow).toContainText("张同步");
      await expect(targetRow).toContainText("13100001111");
      await expect(targetRow).toContainText("2025-09-30");
      await expect(targetRow).toContainText("2025-10-01 09:30:00");
      await expect(targetRow).toContainText("个人原因");

      const screenshotPath = testInfo.outputPath("dimission-table.png");
      await page.screenshot({ path: screenshotPath, fullPage: true });
      await testInfo.attach("dimission-table", { path: screenshotPath, contentType: "image/png" });
    });
  });
});
