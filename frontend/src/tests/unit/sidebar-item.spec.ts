import { describe, it, expect } from "vitest";
import SidebarItem from "@/layout/components/lay-sidebar/components/SidebarItem.vue";
import { mount } from "@vue/test-utils";

describe("SidebarItem fallback path", () => {
  it("uses redirect when no children provided", () => {
    const wrapper = mount(SidebarItem, {
      props: {
        item: {
          path: "/",
          redirect: "/welcome",
          meta: { title: "首页" },
          children: []
        }
      }
    });
    const menuItem = wrapper.find(".el-menu-item");
    expect(menuItem.exists()).toBe(true);
    expect(menuItem.attributes("index")).toBe("/welcome");
  });
});
