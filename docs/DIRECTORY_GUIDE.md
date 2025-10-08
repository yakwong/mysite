# 项目目录指引

> 适用范围：Pure DRF 全栈 RBAC 权限管理系统（仓库根目录）。最后更新：2025-10-06。

## 1. 顶层结构

| 目录/文件 | 说明 | 维护要点 |
|-----------|------|----------|
| `backend/` | Django + DRF 后端工程主体 | 模块化 apps 目录、统一 utils、脚本配置均位于此处 |
| `frontend/` | Vue 3 管理前端工程 | 采用 Vite 构建，模块化拆分至 `src/modules`，页面入口在 `src/views` |
| `docs/` | 跨端文档与代码索引 | 存放 CODE_OVERVIEW、CODE_FILES 以及本文档等说明 |
| `AGENTS.md` / `CLAUDE.md` | AI 协作开发指南 | 指定代码规范、提交约束、交互守则 |
| `start-*.sh` / `stop-*.sh` | 快捷脚本 | 统一管理本地启动/停止前后端服务 |

## 2. 后端 (`backend/`) 划分

- `apps/`：领域服务模块（`system`、`user`、`monitor`、`hr`、`dingtalk` 等）。
  - 推荐新增模块时同步补充 `apps/<module>/tests/` 与 `serializers.py`、`views.py`、`services/` 等子结构。
- `utils/`：跨模块复用工具（响应封装、权限校验、中间件、日志等）。
- `puredrf/`：Django 全局配置（settings、urls、wsgi/asgi）。
- `script/`：运维脚本与数据导入。
- 根目录辅助文件：`DATABASE_DESIGN.md`（数据库文档）、`ROUTE_CONFIG.md`（API 一览）、`manage.py`（命令入口）。

## 3. 前端 (`frontend/`) 划分

- `src/views/`：与路由直接绑定的页面组件（Page 级）。目前目录按业务域拆分为 `system`、`monitor`、`welcome`、`login`、`account-settings` 等，避免与模块层重复。
- `src/modules/`：可复用业务模块。内部通常包含 `api/`、`store/`、`views/`、`components/`，例如：
  - `dingtalk`：钉钉集成中心（同步列表、日志、配置等）。
  - `hr`：人力资源模块复用逻辑（薪资、员工、考勤共享工具），其路由已直接指向 `modules/hr/views/*`，不再在 `src/views` 内保留薄包装组件。
- `src/router/`、`src/store/`、`src/api/`：全局路由、Pinia store、公共接口封装。
- `src/components/`：跨业务通用组件；建议业务专属组件放置于对应 `src/modules/<domain>/components`。
- `docs/`：前端独立文档站点（VuePress），详见下文。

## 4. 文档 (`docs/` 与 `frontend/docs/`)

- `docs/CODE_OVERVIEW.md`：整体模块职责与最新改动索引。
- `docs/CODE_FILES.{md,json}`：自动生成的文件清单，便于快速定位源码。
- `docs/DIRECTORY_GUIDE.md`（本文档）：整体目录结构、职责与维护要点。
- `frontend/docs/`：VuePress 站点源文件。
  - `devdoc/quickstart.md`、`devdoc/permission.md`：前端开发指南。
  - `devdoc/directory-structure.md`：前端子目录说明（新增文件，见下节）。

## 5. 常见新增文件落位建议

| 新增内容类型 | 建议目录 | 备注 |
|--------------|----------|------|
| 新业务后端接口 | `backend/apps/<module>/` | 遵循模块化拆分，补充单测 |
| 新业务前端页面 | `frontend/src/views/<domain>/`（如需复用逻辑可直接路由到 `src/modules/<domain>/views/*`） | 依据复用需求决定是否保留 Page 包装，避免与模块层重复 |
| 业务公共服务/组件 | `frontend/src/modules/<domain>/` 或 `frontend/src/components/` | 视可复用范围决定 |
| 架构/规范类文档 | `docs/` | 若仅前端相关，则放置 `frontend/docs/devdoc/` |
| 运维脚本 | `backend/script/` | 与数据库导入、同步任务相关 |

## 6. 更新流程建议

1. 新增模块前先在本文档或团队 wiki 中注册目录职责，避免重复建设。
2. 同步更新 `docs/CODE_OVERVIEW.md` 或相关 README，以保持文档与代码一致。
3. 涉及前后端联动时，确保 `frontend/src/modules` 与 `backend/apps` 命名一致，便于跨端检索。

---

如需扩展本文档，请在 PR 中同时描述目录变动原因，方便审阅。