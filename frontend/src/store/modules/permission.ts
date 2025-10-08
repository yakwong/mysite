import { defineStore } from "pinia";
import { type cacheType, store, debounce, ascending, getKeyList, filterTree, constantMenus, filterNoPermissionTree, formatFlatteningRoutes } from "../utils";

const hideHomeMenu = import.meta.env.VITE_HIDE_HOME === "true";
import { useMultiTagsStoreHook } from "./multiTags";

export const usePermissionStore = defineStore("pure-permission", {
  state: () => ({
    // 静态路由生成的菜单
    constantMenus,
    // 整体路由生成的菜单（静态、动态）
    wholeMenus: [],
    // 整体路由（一维数组格式）
    flatteningRoutes: [],
    // 缓存页面keepAlive
    cachePageList: []
  }),
  actions: {
    /** 组装整体路由生成的菜单 */
    handleWholeMenus(routes: any[]) {
      const rawMenus = filterNoPermissionTree(filterTree(ascending(this.constantMenus.concat(routes))));
      const menus = rawMenus.map((route: any) => {
        if (route.path === "/") {
          const firstChild = route.children?.[0];
          return {
            ...route,
            path: firstChild?.path || "/welcome",
            name: firstChild?.name || "Welcome",
            redirect: undefined,
            children: undefined,
            noShowingChildren: true,
            meta: {
              ...(route.meta ?? {}),
              ...(firstChild?.meta ?? {}),
              icon: firstChild?.meta?.icon || route.meta?.icon || "ep/home-filled",
              title: firstChild?.meta?.title || route.meta?.title || "首页",
              showLink: true,
              showParent: false,
              backstage: false
            }
          };
        }
        return route;
      });
      if (!hideHomeMenu) {
        const hasHome = menus.some((item: any) => item.path === "/welcome" || item.path === "/");
        if (!hasHome) {
          menus.unshift({
            path: "/welcome",
            name: "Welcome",
            meta: {
              title: "首页",
              icon: "ep/home-filled",
              showLink: true
            }
          } as any);
        }
      }
      this.wholeMenus = menus;
      this.flatteningRoutes = formatFlatteningRoutes(this.constantMenus.concat(routes) as any);
    },
    cacheOperate({ mode, name }: cacheType) {
      const delIndex = this.cachePageList.findIndex(v => v === name);
      switch (mode) {
        case "refresh":
          this.cachePageList = this.cachePageList.filter(v => v !== name);
          break;
        case "add":
          this.cachePageList.push(name);
          break;
        case "delete":
          delIndex !== -1 && this.cachePageList.splice(delIndex, 1);
          break;
      }
      /** 监听缓存页面是否存在于标签页，不存在则删除 */
      debounce(() => {
        let cacheLength = this.cachePageList.length;
        const nameList = getKeyList(useMultiTagsStoreHook().multiTags, "name");
        while (cacheLength > 0) {
          nameList.findIndex(v => v === this.cachePageList[cacheLength - 1]) === -1 && this.cachePageList.splice(this.cachePageList.indexOf(this.cachePageList[cacheLength - 1]), 1);
          cacheLength--;
        }
      })();
    },
    /** 清空缓存页面 */
    clearAllCachePage() {
      this.wholeMenus = [];
      this.cachePageList = [];
    }
  }
});

export function usePermissionStoreHook() {
  return usePermissionStore(store);
}
