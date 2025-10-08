# 前端目录结构说明

> 适用版本：Pure DRF Admin 前端（更新于 2025-10-06）。本文档补充 `src/` 目录功能划分，配合根仓库 `docs/DIRECTORY_GUIDE.md` 使用。

## 1. 顶层结构

| 目录/文件 | 说明 |
|-----------|------|
| `src/` | 核心源码目录，包含页面、业务模块、全局配置等 |
| `docs/` | VuePress 文档站点（当前目录） |
| `public/` | 静态资源（favicon、登录背景等） |
| `build/` | 构建脚本与自定义打包配置 |
| `tests/`、`test-results/` | Playwright 等自动化测试脚本与输出 |
| `types/` | 全局 TypeScript 类型声明 |
| `vite.config.ts`、`tsconfig.json` | 构建与编译配置 |

## 2. `src/` 目录速览

| 子目录 | 职责 | 说明 |
|--------|------|------|
| `api/` | 全局接口封装 | 基于 `@/utils/http` 定义后台 API 请求，跨页面共享 |
| `assets/` | 静态资源 | 仅少量图标/样式，绝大多数静态资产位于 `public/` |
| `components/` | 通用组件 | 适用于多业务复用的 UI 组件；领域专属组件建议放在 `src/modules/<domain>/components` |
| `composables/` | 组合式函数 | 可复用的逻辑抽象（权限、主题等） |
| `directives/` | 自定义指令 | 例如 `v-auth` 权限指令 |
| `layouts/` | 布局组件 | 包括主框架、空白布局等 |
| `modules/` | 业务模块 | 领域层封装（钉钉、HR 等），提供接口、store、内部视图与组件 |
| `router/` | 前端路由 | 动态/静态路由表、路由守卫 |
| `store/` | Pinia 状态 | 全局状态与模块化 store |
| `utils/` | 工具函数 | 日期、权限、缓存等辅助方法 |
| `views/` | 路由页面 | 与 Router 直接挂钩的 Page 级组件；按业务域拆分子目录，如无额外装配需求可跳过 |

## 3. `src/views/` 与 `src/modules/` 协作

- `views/` 聚焦页面装配：负责必要时的布局挂载、参数适配等逻辑；若模块视图可直接用于路由，可省略对应 `views` 包装。
- `modules/` 聚焦领域复用：包含 API、Store、局部组件和内部页面，供多个 `views` 或弹窗复用。
- 推荐流程：
  1. 在 `modules/<domain>` 中封装接口、store、组件、视图；
  2. 视业务复杂度决定是否在 `views/<domain>` 中创建包装页面；
  3. 路由层可直接指向 `modules/<domain>/views/*`，避免重复组件。

## 4. 现有业务模块

| 模块 | 位置 | 功能概览 |
|------|------|----------|
| 钉钉中心 | `src/modules/dingtalk/` | 配置管理、部门/用户/考勤同步、日志查询 |
| 人力资源 | `src/modules/hr/` | 员工、薪资、考勤等 HR 公共逻辑；路由已直接指向模块视图，无需 `views/hr` 包装 |

> 若后续需要为 `system`、`monitor` 等领域复用逻辑，可按上述模式新增模块，并在 PR 中同步更新本文档。

## 5. 新建目录约定

| 场景 | 推荐位置 | 备注 |
|------|----------|------|
| 新增路由页面 | `src/views/<domain>/<Page>.vue`（或直接复用 `modules/<domain>/views/*`） | 根据是否需要额外装配决定 |
| 领域内复用组件 | `src/modules/<domain>/components/` | 例如钉钉列表、HR 表格片段 |
| 领域 API/Store | `src/modules/<domain>/api/`、`src/modules/<domain>/store/` | 保持 index.ts 输出统一类型 |
| 全局公共组件 | `src/components/` | 业务无关或多领域通用组件 |
| 全局工具方法 | `src/utils/` | 注意 TypeScript 类型声明 |

## 6. 维护建议

1. **同步更新文档**：目录新增或职责调整时，更新本文档与根目录 `docs/DIRECTORY_GUIDE.md`。
2. **命名统一**：业务命名与后端 `backend/apps/<module>` 保持一致，便于跨端检索。
3. **模块粒度控制**：模块应包含可复用逻辑，过于单页的功能保持在 `views/` 即可，避免过度拆分。
4. **读者指引**：页面入口 README/注释中可链接到模块文档，帮助新同学快速理解依赖关系。

---

如需扩展本文档，请在 PR 中说明目录变化的动机、影响范围以及对应的路由/API 调整。