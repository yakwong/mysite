# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Pure DRF 是一个全栈 RBAC 权限管理系统，前端使用 Vue 3 + Element Plus，后端使用 Django REST Framework。项目包含完整的部门、角色、权限、用户、日志管理模块，以及完善的前后端鉴权机制。

## 项目结构

```
mysite/
├── frontend/          # Vue 3 前端项目 (基于 Pure Admin)
│   ├── src/
│   │   ├── api/           # API 接口定义
│   │   ├── views/         # 页面组件
│   │   ├── router/        # 路由配置（动态路由）
│   │   ├── store/         # Pinia 状态管理
│   │   ├── directives/    # 自定义指令（包含权限指令）
│   │   └── utils/         # 工具函数
│   └── docs/          # 前端开发文档
└── backend/           # Django REST Framework 后端项目
    ├── apps/
    │   ├── user/          # 用户管理模块
    │   ├── system/        # 系统管理（部门、角色、权限）
    │   ├── monitor/       # 监控日志模块
    │   └── functiontest/  # 功能测试模块
    ├── utils/             # 工具模块
    │   ├── middleware.py      # 中间件（日志记录）
    │   ├── permissions.py     # 权限验证
    │   ├── authenticator.py   # JWT 认证
    │   └── decorators.py      # 装饰器（手动权限包裹）
    └── puredrf/           # Django 项目配置
```

## 常用命令

### 前端 (frontend/)

```bash
# 安装依赖（使用 pnpm）
pnpm install

# 开发模式启动
pnpm dev

# 构建生产环境
pnpm build

# 构建测试环境
pnpm build:staging

# 代码格式化和检查
pnpm lint              # 运行所有检查
pnpm lint:eslint       # ESLint 检查
pnpm lint:prettier     # Prettier 格式化
pnpm lint:stylelint    # 样式检查

# 类型检查
pnpm typecheck

# 清理缓存
pnpm clean:cache
```

### 后端 (backend/)

```bash
# 安装依赖（建议使用虚拟环境）
pip install -r requirements.txt

# 启动开发服务器
python manage.py runserver

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 一键数据库初始化（首次使用）
python dbinit.py

# 生成 SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(50))"

# 代码格式化（使用 black）
black .

# Docker 部署
docker-compose up -d

# 检查路由配置一致性
python backend/check_route_config.py
```

## 访问地址

**本地开发环境：**
- 前端页面：http://127.0.0.1:8848
- 后端 API：http://127.0.0.1:8000
- 后端管理后台：http://127.0.0.1:8000/admin

## 环境配置

### 前端环境变量

- 开发环境：`.env.development`
  - 前端端口：8848
  - 后端接口：http://127.0.0.1:8000
- 生产环境：`.env.production` - 需配置实际部署的后端接口地址

### 后端环境变量

后端必须先创建 `.env` 文件（参考 `.env.example`），主要配置项：

- `SECRET_KEY`: Django 密钥
- `DEBUG`: 调试模式
- `ALLOWED_HOSTS`: 允许的主机
- `DB_ENGINE`: 数据库引擎 (mysql/sqlite3)
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`: 数据库配置
- `USE_REDIS`: 是否启用 Redis
- `API_LOG_ENABLE`: 是否启用 API 日志
- `API_LOG_METHODS`: 记录日志的请求方法

## 核心架构与机制

### 权限系统架构

**后端权限验证（两种方式）：**

1. **中间件自动判断**：通过 `utils/middleware.py` 中的 `ApiLoggingMiddleware` 记录日志
2. **装饰器手动包裹**：使用 `utils/decorators.py` 中的装饰器进行接口级权限控制

权限验证核心代码位于 `backend/utils/permissions.py`，JWT 认证位于 `backend/utils/authenticator.py`

**前端权限控制（三个层级）：**

1. **动态路由**：`frontend/src/router/index.ts` - 根据用户权限动态加载路由
2. **组件级权限**：通过 `frontend/src/store/modules/permission.ts` 管理权限状态
3. **按钮级权限**：使用 `frontend/src/directives/auth/index.ts` 中的 `v-auth` 指令

### 前端路由机制

- 静态路由从 `src/router/modules/` 自动导入
- 动态路由通过 API 获取后由 `usePermissionStore` 处理
- 路由权限过滤通过 `filterNoPermissionTree` 函数实现
- 页面缓存通过 `cachePageList` 状态管理

### 后端应用模块设计

每个 Django app 遵循标准 DRF 结构：

- `models.py`: 数据模型定义
- `serializers.py`: 序列化器
- `views.py`: ViewSet 视图集
- `urls.py`: 路由配置
- `filters.py`: 查询过滤器
- `signals.py`: 信号处理

### 日志记录机制

API 访问日志通过 `utils/middleware.py` 中的 `ApiLoggingMiddleware` 自动记录，日志包含：

- 请求 IP、方法、路径
- 请求参数（密码字段自动脱敏）
- 响应状态、耗时
- 操作用户、浏览器、操作系统信息

日志数据存储在 `apps/monitor/models.py` 的 `OperationLog` 模型中。

## 默认账户

- 超级管理员：admin@kworlds.cn / k12345678
- 预览用户：preview@kworlds.cn / k12345678

## 重要配置说明

### 根路由配置 (首页跳转)

**配置位置:**
- 前端: `frontend/src/router/modules/home.ts` (默认兜底配置)
- 后端数据: `backend/data.json` (初始化数据)
- 运行时数据库: `backend/db.sqlite3` 中的 `system_menu` 表

**当前配置:** 所有位置统一配置为 `redirect: "/welcome"`

**工作机制:**
1. 前端有默认配置作为兜底
2. 后端数据库配置会覆盖前端 (通过 `frontend/src/router/utils.ts:151-158`)
3. `data.json` 用于数据库初始化/重置

**验证命令:**
```bash
python backend/check_route_config.py
```

**扩展用法:**
如需为不同角色配置不同首页,直接修改数据库中根路由的 `redirect` 字段即可实现动态控制。

## 技术栈版本要求

- Node.js: ^18.18.0 || ^20.9.0 || >=22.0.0
- pnpm: >=9
- Python: 3.12.x
- Django: 5.1
- Vue: 3.5.x
