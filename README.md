# Pure DRF - 全栈 RBAC 权限管理系统

[![License](https://img.shields.io/github/license/yakwong/mysite.svg)](LICENSE)

Pure DRF 是一个使用 Vue 3 + Django REST Framework 构建的全栈 RBAC 权限管理系统。

## ✨ 特性

- 🔐 完整的 RBAC 权限管理（部门、角色、权限、用户）
- 🎯 多层级权限控制（路由级、组件级、按钮级）
- 🛡️ 账户安全中心（两步验证、登录提醒、密保问题、备用邮箱等）
- 👥 人力资源模块（部门、员工、考勤、薪资一站式管理，支持钉钉数据引入）
- 📝 完善的操作日志和登录日志
- 🚀 前后端分离架构
- 💻 基于 Vue 3 + Vite + Element Plus
- ⚡️ 基于 Django 5.1 + DRF 3.15
- 🎨 响应式布局，支持深色模式
- 🔑 JWT 认证机制

## 🎯 技术栈

**前端：**
- Vue 3.5 + TypeScript
- Element Plus 组件库
- Pinia 状态管理
- Vue Router 动态路由
- Axios HTTP 客户端
- Vite 构建工具

**后端：**
- Django 5.1
- Django REST Framework 3.15
- PyJWT 认证
- MySQL / SQLite 数据库
- Redis 缓存（可选）

## 📦 快速开始

### 环境要求

- Node.js: ^18.18.0 || ^20.9.0 || >=22.0.0
- pnpm: >=9
- Python: 3.12.x
- MySQL 8.0+ / SQLite 3

### 安装

**1. 克隆项目**

```bash
git clone https://github.com/yakwong/mysite.git
cd mysite
```

**2. 后端安装**

```bash
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库等信息

# 初始化数据库
python dbinit.py

# 启动后端服务
python manage.py runserver
```

**3. 前端安装**

```bash
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

### 访问系统

- 前端地址：http://127.0.0.1:8848
- 后端 API：http://127.0.0.1:8000
- Django 管理后台：http://127.0.0.1:8000/admin

### 默认账户

- **超级管理员**：admin@kworlds.cn / k12345678
- **预览用户**：preview@kworlds.cn / k12345678

## 🚀 快速启动脚本

项目提供了便捷的启动脚本：

```bash
# 启动所有服务（前端 + 后端）
./start-all.sh

# 单独启动后端
./start-backend.sh

# 单独启动前端
./start-frontend.sh

# 重启后端
./restart-backend.sh

# 重启前端
./restart-frontend.sh

# 停止后端
./stop-backend.sh

# 停止前端
./stop-frontend.sh
```

## 📁 项目结构

```
mysite/
├── frontend/              # Vue 3 前端项目
│   ├── src/
│   │   ├── api/          # API 接口定义
│   │   ├── views/        # 页面组件
│   │   ├── router/       # 路由配置
│   │   ├── modules/      # 业务模块（如钉钉中心、人力资源）
│   │   ├── store/        # Pinia 状态管理
│   │   ├── directives/   # 自定义指令（权限指令）
│   │   └── utils/        # 工具函数
│   └── docs/             # 前端开发文档
│
├── backend/              # Django REST Framework 后端
│   ├── apps/
│   │   ├── user/        # 用户管理模块
│   │   ├── system/      # 系统管理（部门、角色、权限）
│   │   ├── monitor/     # 监控日志模块
│   │   ├── hr/          # 人力资源模块（部门/员工/考勤/薪资）
│   │   └── functiontest/# 功能测试模块
│   ├── utils/           # 工具模块
│   │   ├── middleware.py    # 日志中间件
│   │   ├── permissions.py   # 权限验证
│   │   ├── authenticator.py # JWT 认证
│   │   └── decorators.py    # 权限装饰器
│   └── puredrf/         # Django 项目配置
│
├── docs/                # 本次分析生成的代码概览与清单
├── CLAUDE.md            # Claude Code 开发指南
├── AGENTS.md            # 代码规范和提交指南
└── README.md            # 项目说明文档
```

## 📚 代码分析与文档

- `docs/CODE_OVERVIEW.md`：后端/前端模块职责总览，新增登录提醒开关等最新改动说明。
- `docs/CODE_FILES.md`：逐文件统计表（行数、首行内容、路径），便于定位源码。
- `backend/DATABASE_DESIGN.md`：数据库结构与字段描述（已更新至当前模型）。
- `backend/ROUTE_CONFIG.md`：REST API 列表，可配合 `check_route_config.py` 校验。

## 🔐 权限系统

### 后端权限

1. **中间件自动验证**：通过 `ApiLoggingMiddleware` 自动记录和验证
2. **装饰器手动控制**：使用 `@permission_required` 等装饰器精确控制

### 前端权限

1. **路由级权限**：根据用户角色动态加载路由
2. **组件级权限**：通过 Pinia store 控制组件显示
3. **按钮级权限**：使用 `v-auth` 指令控制按钮显示

## 📝 开发指南

### 前端开发

```bash
cd frontend

# 开发模式
pnpm dev

# 代码检查
pnpm lint

# 类型检查
pnpm typecheck

# 构建生产版本
pnpm build
```

### 后端开发

```bash
cd backend

# 创建迁移
python manage.py makemigrations

# 执行迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 代码格式化
black .

# 运行测试
python manage.py test
```

## 🐳 Docker 部署

```bash
cd backend
docker-compose up -d
```

## 📄 许可证

[MIT License](LICENSE)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

- GitHub：[@yakwong](https://github.com/yakwong)
- Email：aaronwang@sina.com

## 🙏 致谢

本项目基于以下优秀开源项目：

- [Pure Admin](https://github.com/pure-admin/vue-pure-admin)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Element Plus](https://element-plus.org/)
