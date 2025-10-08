import { test, expect, Page } from "@playwright/test";
import { UI_BASE_URL, UI_USERNAME, UI_PASSWORD } from "./support/env";

const escapeRegex = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const expectHeaderCell = async (page: Page, label: string) => {
  const tableWithHeader = page
    .getByRole("table")
    .filter({ has: page.getByRole("cell", { name: label }) });

  if (await tableWithHeader.count()) {
    await expect(tableWithHeader.first().getByRole("cell", { name: label })).toBeVisible();
    return;
  }

  const fallbackHeader = page
    .locator(".el-table__header th")
    .filter({ hasText: label })
    .first();
  await expect(fallbackHeader).toBeVisible();
};

type Section = {
  path: string;
  assert: (page: Page) => Promise<void>;
};

const HR_SECTIONS: Section[] = [
  {
    path: "/#/hr/departments",
    assert: async page => {
      await expect(page.getByRole("button", { name: "新增部门" })).toBeVisible();
      await expectHeaderCell(page, "名称");
    }
  },
  {
    path: "/#/hr/employees",
    assert: async page => {
      await expect(page.getByRole("button", { name: "新增员工" })).toBeVisible();
      await expectHeaderCell(page, "工号");
    }
  },
  {
    path: "/#/hr/attendance/rules",
    assert: async page => {
      await expect(page.getByRole("button", { name: "新增考勤规则" })).toBeVisible();
      await expectHeaderCell(page, "上班时间");
    }
  },
  {
    path: "/#/hr/attendance/summary",
    assert: async page => {
      await expect(page.getByRole("button", { name: "生成统计" })).toBeVisible();
      await expectHeaderCell(page, "员工");
    }
  },
  {
    path: "/#/hr/payroll/rules",
    assert: async page => {
      await expect(page.getByRole("button", { name: "新增薪资规则" })).toBeVisible();
      await expectHeaderCell(page, "加班倍数");
    }
  },
  {
    path: "/#/hr/payroll/records",
    assert: async page => {
      await expect(
        page.locator(".el-breadcrumb").getByRole("link", { name: "薪资发放" })
      ).toBeVisible();
    }
  }
];

test.describe("HR module navigation", () => {
  test("user can login and view key HR routes", async ({ page }) => {
    await page.goto(`${UI_BASE_URL}/#/login`);

    await page.getByPlaceholder("邮箱/用户名/手机号").fill(UI_USERNAME);
    await page.getByPlaceholder("密码").fill(UI_PASSWORD);
    await page.getByRole("button", { name: "登录" }).click();

    await expect(page).toHaveURL(/#\/(welcome|system\/permission)/);

    for (const section of HR_SECTIONS) {
      await page.goto(`${UI_BASE_URL}${section.path}`);
      await expect(page).toHaveURL(new RegExp(escapeRegex(section.path)));
      await section.assert(page);
    }
  });
});
