# 代码架构概览

本文件根据 2025-10-04 的仓库状态生成，结合 `docs/CODE_FILES.md` 中的逐文件清单，对后端 Django 与前端 Vue 子项目进行结构化说明，帮助快速掌握代码现状。

## 数据概览

- **代码文件总数**：326（排除依赖目录与自动生成的构建产物）。
- **后端（`backend/`）**：约 11.6K 行，包含 62 个业务文件、22 个脚本、12 个工具模块以及静态资源与路由/数据库设计文档。
- **前端（`frontend/`）**：约 20K 行，157 个源码文件覆盖 API、组件、布局、页面、指令、状态管理等。
- **逐文件明细**：详见 `docs/CODE_FILES.md`（表格）或 `docs/CODE_FILES.json`（机器可读）。

## 后端（Django / DRF）

### 全局配置
- `backend/puredrf/settings.py`：定义 Django 配置，启用自定义用户模型、JWT 认证、REST Framework、缓存与国际化。
- `backend/puredrf/urls.py`：汇总 API 路由，挂载 `system`、`user`、`monitor` 应用及 Swagger/Redoc 文档。
- `backend/check_route_config.py`：根据 `ROUTE_CONFIG.md` 校验后端路由与文档的一致性。
- `backend/ROUTE_CONFIG.md`：列出对外暴露的 REST API，记录路径、方法、权限要求。

### 公共工具 `backend/utils/`
- `authenticator.py`：封装 JWT 鉴权，兼容自定义 `User` 模型。
- `decorators.py` & `permissions.py`：提供细粒度权限控制装饰器/DRF Permission 类。
- `middleware.py`：`ApiLoggingMiddleware` 记录请求元数据与响应状态，配合 `logsFormat.py` 统一日志格式。
- `request_util.py`：封装 IP 解析、User-Agent 识别等请求辅助函数。
- `response.py`、`viewset.py`、`pagination.py`：统一响应结构并扩展批量 CRUD 行为。
- `exception.py`：集中处理业务异常类型。

### 应用模块

#### `apps/system`
- `models.py`：定义 `Role`、`Menu`、`MenuMeta`、`DeptInfo` 等 RBAC 核心模型（支持菜单/权限树、部门层级、菜单元数据）。
- `serializers.py`：配套序列化、路由生成器，`RouteSerializer` 将菜单与权限字典打平注入前端。
- `views.py`：基于 `CustomModelViewSet` 提供角色/菜单/部门 CRUD；`AsyncRoutesView` 根据用户角色输出动态路由及权限码集合。
- `filters.py`：为角色、菜单、部门提供筛选字段，配合 DjangoFilterBackend。
- `urls.py`：通过 `DefaultRouter` 注册上述视图。
- `tests.py`：覆盖角色/菜单 CRUD、路由获取与部门层级接口。

#### `apps/user`
- `models.py`：自定义 `User` 模型扩展头像、昵称、手机号验证、备用邮箱、密保问题、两步验证与登录提醒等字段。
- `serializers.py`：
  - `UserProfileSerializer` 等序列化器。
  - `ChangePasswordSerializer`、`SendCodeSerializer`、`PhoneBindingSerializer` 等封装验证规则。
  - **新增** `LoginNotifierSerializer` 支持登录提醒开关。
- `views.py`：
  - `UserViewSet` 提供个人资料、头像上传、安全配置（绑定手机/邮箱、密保、两步验证、登录提醒、密码修改）。
  - `LoginView` 提供账号/邮箱/手机号登录与 JWT 发放。
  - `send_security_code`、`toggle_two_factor` 等 action 集中实现安全流程。
  - **新增** `toggle_login_notifier` action，配合前端开关登录提醒。
- `signals.py`：监听登录成功/失败记录。
- `tests.py`：覆盖密码修改、手机号绑定、备用邮箱、密保、登录提醒、账号安全概览等全流程。

#### `apps/monitor`
- `models.py`：登录日志、操作日志模型，记录 IP、浏览器、执行状态等。
- `views.py`（位于 `apps/user` 中复用）：日志数据在 `UserViewSet.security_logs` 中返回。
- `serializers.py`：格式化日志摘要与地理信息。
- `filters.py`：提供基于 IP/状态筛选能力。

#### `apps/dingtalk`
- **模型**：`DingTalkConfig`、`DingTalkDepartment`、`DingTalkUser`、`DingTalkAttendanceRecord`、`SyncCursor` 等集中到新应用，`enabled_configs()`、`load()` 封装默认配置回退。
- **序列化/视图**：`DingTalkConfigViewSet` 支持 Token 重置与增量同步信息，`SyncCommandView` 统一处理测试连通/同步入口，异常统一落库 `DingTalkSyncLog`。
- **服务层**：`services.client.DingTalkClient` 负责调用钉钉开放平台、令牌管理，`services.sync.SyncService` 封装部门/用户/考勤同步及日志写入，`services.scheduler` 预留计划任务挂钩。
- **权限**：`CanManageDingTalk` 限制管理操作仅限 `is_staff` 用户，`CanViewDingTalk` 允许普通登录用户浏览同步结果。
- **测试**：`tests/test_api.py` 覆盖配置列表、同步命令、远端预览、考勤写入等关键路径。

#### `apps/functiontest`
- 包含演示用视图/URL 模块，用于 DRF 基础功能验证。

### 运维与脚本
- `backend/script/analyze_mssql.py`：MSSQL 元数据分析工具，连接 ERP 库输出表/列/外键信息。
- `backend/script/sql/`：数据库初始化 SQL，包括部门、角色、菜单、用户等种子数据。
- `backend/dbinit.py`、`script/dbinit.py`：封装数据迁移/初始化流程。
- `backend/DATABASE_DESIGN.md`：图文解释数据表结构、关系、字段说明。

### 静态资源
- `backend/static/`：包含 Django admin 与 DRF 文档所需前端资源，未做业务改动。

## 前端（Vue 3 + Element Plus）

### 全局结构
- `src/main.ts`：初始化应用，注册路由、Pinia、i18n、Element Plus。
- `src/config/index.ts`：应用配置（主题、请求前缀、动态路由开关等）。
- `src/style/`：Tailwind/Element Plus 覆写、暗黑模式、重置样式。

### API 层 `src/api/`
- `user.ts`：封装与后端一致的接口，包括个人资料、安全操作、验证码、登录提醒（新增 `toggleLoginNotifier`）。
- `system.ts`、`monitor.ts`、`routes.ts`：与系统管理、监控等对应。
- 全部通过 `utils/http` 统一请求拦截、错误处理。

### 布局与组件
- `src/layout/`：导航栏、侧边栏、标签页、设置面板等布局组件；`hooks` 提供布局状态管理。
- `src/components/`：大量复用组件（ReDialog、ReIcon、RePureTableBar 等），支持权限控制与主题适配。
- `src/directives/`：自定义指令如 `v-auth`、`v-copy`、`v-longpress`。

### 页面视图 `src/views/`
### 模块化钉钉前端 `src/modules/dingtalk`
- `views/`：包含 Dashboard、Logs、Departments、Users、Attendance、Settings 等二级页面，与后端接口一一对应。
- `api/index.ts`：封装 `/api/dingtalk/**` 请求、分页响应与同步命令参数类型。
- `store/useDingtalkStore.ts`：简单管理当前选中配置与配置列表，便于多配置切换。

- `account-settings/`：个人中心（Profile、Preferences、SecurityLog、AccountManagement）。
  - `AccountManagement.vue`：整合密码、密保、备用邮箱、两步验证、**登录提醒开关** 等安全项。
  - `Preferences.vue`：新增基于远端 `login_notifier` + 本地偏好（系统消息、待办任务）管理，支持本地持久化。
- `system/`：部门、角色、权限、用户管理页面，对应后端 CRUD。
- `monitor/`：登录、操作日志表格。
- 其他如 `login/`、`home/`、`error/` 系列提供登陆与状态页。

### 状态与路由
- `src/router/`：
  - `index.ts` 配置基础路由与守卫。
  - `modules/*.ts` 管理业务路由分组，支持后端动态扩展。
  - `utils.ts` 负责路由转换、权限校验。
- `src/store/`：Pinia modules 管理权限标签、用户信息、应用设置。

### 工具库 `src/utils/`
- `auth.ts` 管理 Token 与本地缓存。
- `message.ts` 封装 Element Plus 消息提示。
- `tree.ts`、`responsive.ts`、`progress/` 等提供通用工具。

### 其他资源
- `locales/*.yaml`：中英文翻译。
- `types/`：声明全局组件、Pinia、Router 类型，确保 TypeScript 体验。
- `docs/`：前端二级文档（部署、升级指南等）。

## 数据初始化说明（新增）

- `backend/data_base.json`：抽取自现网默认数据，用于快速导入基础角色、菜单、管理员账号。
- `backend/data_custom.json`：示例性定制数据，可在导入基础数据后按需叠加部门/角色结构。
- 两份 JSON 与 `backend/script/sql/` SQL 初始化互补，可根据部署环境选择其一；使用 JSON 时建议通过 `python manage.py loaddata` 执行。

## 文档资源更新

- `docs/CODE_FILES.md`：新增逐文件统计表，可快速检索每个文件的行数与首行内容。
- `docs/CODE_FILES.json`：对应的机器可读数据源，便于二次分析或生成报表。
- 本概览文件总结了主要模块职责，建议搭配 `backend/DATABASE_DESIGN.md` 与 `backend/ROUTE_CONFIG.md` 获取更细节的接口/数据结构说明。

## 后续建议

1. 若需要更深入的代码审计，可基于 `CODE_FILES.json` 按目录筛选重点文件进行人工复查。
2. 建议在 CI 中接入脚本，定期重建文件清单，确保文档与代码保持同步。
3. 前后端已实现登录提醒开关与安全设置，后续可补充自动化测试覆盖前端交互逻辑。
