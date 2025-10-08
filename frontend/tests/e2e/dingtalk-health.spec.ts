import { test, expect } from "@playwright/test";
import { UI_BASE_URL, API_BASE_URL, UI_USERNAME, UI_PASSWORD } from "./support/env";

type ApiCheck = {
  /** 接口相对路径 */
  path: string;
  /** 断言说明 */
  label: string;
  /** 自定义断言 */
  assert?: (payload: any) => void | Promise<void>;
  /** 查询参数 */
  params?: Record<string, string | number>;
};

const USER_AGENT = process.env.UI_USER_AGENT ?? "playwright-dingtalk-health";

const API_CHECKS: ApiCheck[] = [
  {
    path: "/api/dingtalk/configs/",
    label: "钉钉配置列表返回成功",
    assert: body => {
      expect(Array.isArray(body.data), "配置列表应为数组").toBeTruthy();
      expect(body.data.length, "至少包含一个配置").toBeGreaterThan(0);
    }
  },
  {
    path: "/api/dingtalk/logs/",
    label: "同步日志返回成功",
    assert: body => {
      expect(Array.isArray(body.data), "日志列表应为数组").toBeTruthy();
    }
  },
  {
    path: "/api/dingtalk/departments/",
    label: "部门数据返回成功",
    assert: body => {
      expect(Array.isArray(body.data), "部门列表应为数组").toBeTruthy();
    }
  },
  {
    path: "/api/dingtalk/users/",
    label: "人员数据返回成功",
    assert: body => {
      expect(Array.isArray(body.data), "人员列表应为数组").toBeTruthy();
    }
  },
  {
    path: "/api/dingtalk/attendances/",
    label: "考勤记录返回成功",
    assert: body => {
      expect(Array.isArray(body.data), "考勤记录应为数组").toBeTruthy();
    }
  },
  {
    path: "/api/dingtalk/dimission-users/",
    label: "离职人员返回成功",
    assert: body => {
      expect(Array.isArray(body.data), "离职人员列表应为数组").toBeTruthy();
    }
  }
];

test.describe("DingTalk 模块健康检查", () => {
  test("登录后校验钉钉核心接口状态", async ({ page }) => {
    await test.step("打开登录页并登录", async () => {
      await page.goto(`${UI_BASE_URL}/#/login`);
      await page.getByPlaceholder("邮箱/用户名/手机号").fill(UI_USERNAME);
      await page.getByPlaceholder("密码").fill(UI_PASSWORD);
      await Promise.all([
        page.waitForResponse(response =>
          response.url().includes("/api/user/login/") && response.request().method() === "POST"
        ),
        page.getByRole("button", { name: "登录" }).click()
      ]);
      await expect(page).toHaveURL(/#\/(welcome|system\/permission)/);
    });

    // 解析登录后写入的授权 Cookie
    const cookies = await page.context().cookies();
    const tokenCookie = cookies.find(cookie => cookie.name === "authorized-token");
    expect(tokenCookie, "应当获取到授权 Cookie").toBeTruthy();

    let accessToken = "";
    if (tokenCookie) {
      const raw = decodeURIComponent(tokenCookie.value ?? "{}");
      const payload = JSON.parse(raw);
      accessToken = payload?.accessToken ?? "";
    }
    expect(accessToken, "Cookie 中应包含 accessToken").toBeTruthy();

    const commonHeaders = {
      Authorization: `Bearer ${accessToken}`,
      "User-Agent": USER_AGENT
    };

    for (const check of API_CHECKS) {
      // 使用前端上下文请求，以便继承鉴权态
      const response = await page.request.get(`${API_BASE_URL}${check.path}`, {
        headers: commonHeaders,
        params: check.params
      });
      expect(response.status(), `${check.label}：HTTP 状态应为 200`).toBe(200);
      const body = await response.json();
      expect(body.success, `${check.label}：success 字段应为 true`).toBeTruthy();
      if (check.assert) {
        await check.assert(body);
      }
    }
  });
});
