# Pure DRF 数据库设计文档

> 2025-10-04 更新：`user` 表的登录提醒（`login_notifier_enabled`）、备用邮箱、安全问题字段等描述已与最新代码同步，更多映射见 `docs/CODE_OVERVIEW.md`。

## 概述

**项目名称:** Pure DRF 全栈 RBAC 权限管理系统
**数据库类型:** SQLite 3
**数据库文件:** `backend/db.sqlite3`
**设计模式:** RBAC (基于角色的访问控制)
**表总数:** 20 张
**最后更新:** 2025-10-04

---

## 目录

- [一、数据库模块划分](#一数据库模块划分)
- [二、用户模块 (User Module)](#二用户模块-user-module)
- [三、系统管理模块 (System Module)](#三系统管理模块-system-module)
- [四、监控日志模块 (Monitor Module)](#四监控日志模块-monitor-module)
- [五、Django 系统表](#五django-系统表)
- [六、数据库关系图](#六数据库关系图)
- [七、RBAC 权限设计](#七rbac-权限设计)
- [八、索引和约束](#八索引和约束)
- [九、数据示例](#九数据示例)

---

## 一、数据库模块划分

| 模块 | 表数量 | 说明 |
|------|--------|------|
| **用户模块** | 4 | 用户信息、用户角色关联 |
| **系统管理模块** | 6 | 角色、部门、菜单/权限 |
| **监控日志模块** | 2 | 登录日志、操作日志 |
| **Django 系统表** | 4 | Session、迁移记录等 |
| **认证权限表** | 3 | Django Auth 基础表 |
| **内容类型表** | 1 | Django ContentType |

**总计:** 20 张表

---

## 二、用户模块 (User Module)

### 2.1 用户表 (user_user)

**表说明:** 核心用户表,存储所有用户信息
**数据量:** 2 条记录

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY | 用户 ID (自增) |
| `username` | VARCHAR(100) | UNIQUE, NOT NULL | 用户名 (登录方式1) |
| `email` | VARCHAR(254) | UNIQUE, NOT NULL | 邮箱 (登录方式2) |
| `phone` | VARCHAR(11) | UNIQUE, NULL | 手机号 (登录方式3) 🆕 |
| `password` | VARCHAR(128) | NOT NULL | 密码 (PBKDF2 加密) |
| `nickname` | VARCHAR(100) | NULL | 昵称/显示名称 |
| `avatar` | VARCHAR(100) | NULL | 头像 URL |
| `status` | BOOLEAN | NOT NULL | 状态 (True=启用, False=禁用) |
| `is_staff` | BOOLEAN | NOT NULL | 后台访问权限 |
| `is_superuser` | BOOLEAN | NOT NULL | 超级管理员标志 |
| `dept_id` | CHAR(32) | FK → system_deptinfo | 所属部门 ID |
| `create_time` | DATETIME | NOT NULL | 创建时间 |
| `last_login` | DATETIME | NULL | 最后登录时间 |

**索引:**
- `PRIMARY KEY (id)`
- `UNIQUE (username)`
- `UNIQUE (email)`
- `UNIQUE INDEX idx_user_phone (phone) WHERE phone IS NOT NULL`
- `INDEX (dept_id)`

**特点:**
- ✅ 支持三种登录方式 (邮箱/用户名/手机号)
- ✅ 密码使用 PBKDF2-SHA256 加密
- ✅ 软删除 (通过 status 字段)
- ✅ 支持超级管理员绕过权限检查

---

### 2.2 用户角色关联表 (user_user_role)

**表说明:** 用户与角色的多对多关联中间表
**数据量:** 2 条记录

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY | 关联 ID (自增) |
| `user_id` | BIGINT | FK → user_user | 用户 ID |
| `role_id` | CHAR(32) | FK → system_role | 角色 ID |

**索引:**
- `UNIQUE (user_id, role_id)` - 防止重复关联

---

### 2.3 用户组表 (user_user_groups)

**表说明:** Django Auth 用户组关联 (预留)
**数据量:** 0 条记录

---

### 2.4 用户权限表 (user_user_user_permissions)

**表说明:** Django Auth 用户权限关联 (预留)
**数据量:** 0 条记录

---

## 三、系统管理模块 (System Module)

### 3.1 角色表 (system_role)

**表说明:** 角色定义表,RBAC 权限体系核心
**数据量:** 5 条记录

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | CHAR(32) | PRIMARY KEY | 角色 ID (UUID) |
| `name` | VARCHAR(128) | NOT NULL | 角色名称 |
| `code` | VARCHAR(128) | UNIQUE, NOT NULL | 角色代码 (英文标识) |
| `status` | BOOLEAN | NOT NULL | 状态 (启用/禁用) |
| `parent_id` | CHAR(32) | FK → system_role | 父角色 ID (层级结构) |
| `create_time` | DATETIME | NOT NULL | 创建时间 |
| `update_time` | DATETIME | NOT NULL | 更新时间 |

**示例数据:**
- 超级管理员 (superadmin) - 拥有全部 29 个权限
- 平台用户管理员 (useradmin) - 拥有 11 个用户管理权限
- 销售员 (sales)
- 店长 (storemanager)
- 管理员 (admins)

**特点:**
- ✅ 支持角色层级 (parent_id)
- ✅ 角色代码用于程序判断
- ✅ 角色与权限多对多关联

---

### 3.2 角色菜单关联表 (system_role_menu)

**表说明:** 角色与菜单/权限的多对多关联
**数据量:** 40 条记录

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY | 关联 ID |
| `role_id` | CHAR(32) | FK → system_role | 角色 ID |
| `menu_id` | CHAR(32) | FK → system_menu | 菜单/权限 ID |

---

### 3.3 部门表 (system_deptinfo)

**表说明:** 组织架构/部门信息表
**数据量:** 2 条记录

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | CHAR(32) | PRIMARY KEY | 部门 ID (UUID) |
| `name` | VARCHAR(128) | NOT NULL | 部门名称 |
| `code` | VARCHAR(128) | UNIQUE, NOT NULL | 部门代码 |
| `rank` | INTEGER | NOT NULL | 层级 |
| `status` | BOOLEAN | NOT NULL | 状态 |
| `type` | SMALLINT | NOT NULL | 部门类型 |
| `auto_bind` | BOOLEAN | NOT NULL | 自动绑定 |
| `parent_id` | CHAR(32) | FK → system_deptinfo | 父部门 ID |
| `create_time` | DATETIME | NOT NULL | 创建时间 |
| `update_time` | DATETIME | NOT NULL | 更新时间 |

**示例数据:**
- 总部 (base)
- 管理部门 (management) - 2 个用户

**特点:**
- ✅ 树形结构 (parent_id)
- ✅ 支持多级部门层级
- ✅ 部门代码唯一标识

---

### 3.4 菜单/权限表 (system_menu)

**表说明:** 菜单和权限的统一管理表
**数据量:** 30 条记录

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | CHAR(32) | PRIMARY KEY | 菜单 ID (UUID) |
| `name` | VARCHAR(128) | NOT NULL | 菜单/权限名称 |
| `path` | VARCHAR(255) | NULL | 路由路径 |
| `component` | VARCHAR(255) | NULL | 前端组件路径 |
| `menu_type` | SMALLINT | NOT NULL | 类型 (1=菜单, 2=权限) |
| `code` | VARCHAR(128) | NULL | 权限代码 |
| `redirect` | VARCHAR(255) | NULL | 重定向路径 |
| `method` | VARCHAR(10) | NULL | HTTP 方法 |
| `status` | BOOLEAN | NOT NULL | 状态 |
| `parent_id` | CHAR(32) | FK → system_menu | 父菜单 ID |
| `meta_id` | CHAR(32) | FK → system_menumeta | 元数据 ID |
| `create_time` | DATETIME | NOT NULL | 创建时间 |
| `update_time` | DATETIME | NOT NULL | 更新时间 |

**menu_type 说明:**
- `1` - 菜单 (Menu): 前端显示的导航菜单
- `2` - 权限 (Permission): 后端 API 权限控制

**权限代码格式:**
```
/api/{module}/{resource}/:action

示例:
- /api/user/:read    - 用户查看权限
- /api/user/:add     - 用户新增权限
- /api/user/:delete  - 用户删除权限
```

**示例一级菜单:**
- Home (/) - 首页,redirect=/welcome
- 功能测试 (/test) - 1 个子菜单
- 系统管理 (/system) - 4 个子菜单
- 系统监控 (/monitor) - 2 个子菜单

**特点:**
- ✅ 菜单和权限统一管理
- ✅ 树形结构支持多级菜单
- ✅ 权限代码用于后端验证
- ✅ 路由路径用于前端动态路由

---

### 3.5 菜单元数据表 (system_menumeta)

**表说明:** 菜单的额外元数据 (图标、标题等)
**数据量:** 30 条记录

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | CHAR(32) | PRIMARY KEY | 元数据 ID (UUID) |
| `icon` | VARCHAR(128) | NULL | 图标名称 |
| `title` | VARCHAR(128) | NULL | 显示标题 |
| `rank` | INTEGER | NULL | 排序 |
| `showLink` | BOOLEAN | NULL | 是否显示链接 |
| `backstage` | BOOLEAN | NULL | 是否后台菜单 |
| `create_time` | DATETIME | NOT NULL | 创建时间 |
| `update_time` | DATETIME | NOT NULL | 更新时间 |

---

## 四、监控日志模块 (Monitor Module)

### 4.1 操作日志表 (monitor_operationlog)

**表说明:** 记录所有 API 操作日志
**数据量:** 30 条记录

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY | 日志 ID (自增) |
| `request_modular` | VARCHAR(255) | NULL | 请求模块 |
| `request_path` | TEXT | NULL | 请求路径 |
| `request_method` | VARCHAR(10) | NULL | 请求方法 (GET/POST...) |
| `request_msg` | TEXT | NULL | 请求参数 |
| `request_ip` | VARCHAR(32) | NULL | 请求 IP |
| `response_code` | INTEGER | NULL | 响应状态码 |
| `json_result` | TEXT | NULL | 响应结果 |
| `creator_id` | BIGINT | NULL | 操作用户 ID |
| `dept_belong_id` | CHAR(32) | NULL | 所属部门 ID |
| `create_time` | DATETIME | NOT NULL | 创建时间 |
| `update_time` | DATETIME | NOT NULL | 更新时间 |

**记录方式:**
- 通过中间件 `ApiLoggingMiddleware` 自动记录
- 支持配置哪些 HTTP 方法需要记录
- 自动脱敏敏感字段 (password)

---

### 4.2 登录日志表 (monitor_loginlog)

**表说明:** 记录用户登录历史
**数据量:** 23 条记录

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY | 日志 ID (自增) |
| `username` | VARCHAR(150) | NULL | 用户名 |
| `ip` | VARCHAR(32) | NULL | 登录 IP |
| `agent` | VARCHAR(255) | NULL | User-Agent |
| `browser` | VARCHAR(200) | NULL | 浏览器 |
| `os` | VARCHAR(200) | NULL | 操作系统 |
| `login_type` | SMALLINT | NULL | 登录类型 |
| `create_time` | DATETIME | NOT NULL | 登录时间 |
| `update_time` | DATETIME | NOT NULL | 更新时间 |

**登录类型:**
- `1` - 邮箱登录
- `2` - 用户名登录
- `3` - 手机号登录 🆕

---

## 五、Django 系统表

### 5.1 Session 表 (django_session)

**表说明:** Django Session 存储
**存储引擎:** Database

### 5.2 迁移记录表 (django_migrations)

**表说明:** 数据库迁移历史记录

### 5.3 内容类型表 (django_content_type)

**表说明:** Django ContentType 框架

### 5.4 管理日志表 (django_admin_log)

**表说明:** Django Admin 后台操作日志

---

## 六、数据库关系图

```
                            ┌──────────────┐
                            │ system_menu  │ 菜单/权限表
                            │ (30条记录)   │
                            ├──────────────┤
                            │ id (UUID)    │
                            │ name         │
                            │ path         │
                            │ menu_type    │ ◄── 1=菜单, 2=权限
                            │ code         │ ◄── 权限代码
                            │ parent_id    │ ◄── 树形结构
                            └──────┬───────┘
                                   │
                                   │ M:N (system_role_menu)
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        │                          ▼                          │
        │                  ┌──────────────┐                   │
        │                  │ system_role  │ 角色表             │
        │                  │ (5条记录)    │                   │
        │                  ├──────────────┤                   │
        │                  │ id (UUID)    │                   │
        │                  │ name         │                   │
        │                  │ code         │                   │
        │                  │ parent_id    │ ◄── 角色层级       │
        │                  └──────┬───────┘                   │
        │                         │                           │
        │                         │ M:N (user_user_role)      │
        │                         │                           │
        │                         ▼                           │
        │               ┌──────────────────┐                  │
        │               │   user_user      │ 用户表           │
        │               │   (2条记录)      │                  │
        │               ├──────────────────┤                  │
        │               │ id (主键)        │                  │
        │               │ username (唯一)  │ ◄── 登录方式1    │
        │               │ email (唯一)     │ ◄── 登录方式2    │
        │               │ phone (唯一) 🆕  │ ◄── 登录方式3    │
        │               │ password (加密)  │                  │
        │               │ status           │                  │
        │               │ is_superuser     │                  │
        │               │ dept_id          │──┐               │
        │               └──────────────────┘  │               │
        │                                     │ N:1           │
        │                                     │               │
        │                                     ▼               │
        │                           ┌──────────────┐          │
        │                           │system_deptinfo│ 部门表   │
        │                           │ (2条记录)    │          │
        │                           ├──────────────┤          │
        │                           │ id (UUID)    │          │
        │                           │ name         │          │
        │                           │ code         │          │
        │                           │ parent_id    │ ◄── 树形结构
        │                           └──────────────┘          │
        │                                                     │
        ▼                                                     ▼
┌──────────────────┐                            ┌──────────────────┐
│ monitor_loginlog │ 登录日志                    │monitor_operation │ 操作日志
│  (23条记录)      │                            │  (30条记录)      │
├──────────────────┤                            ├──────────────────┤
│ username         │                            │ request_path     │
│ ip               │                            │ request_method   │
│ browser          │                            │ response_code    │
│ create_time      │                            │ creator_id       │
└──────────────────┘                            └──────────────────┘
```

---

## 七、RBAC 权限设计

### 7.1 权限流程

```
用户登录
    ↓
查询用户角色 (user_user_role)
    ↓
查询角色权限 (system_role_menu)
    ↓
过滤 menu_type=2 的权限
    ↓
提取 code 字段
    ↓
返回权限代码列表
    ↓
后端验证 API 权限
```

### 7.2 权限验证位置

**后端验证 (两种方式):**

1. **中间件自动判断**
   - 文件: `backend/utils/middleware.py`
   - 类: `ApiLoggingMiddleware`
   - 自动记录并验证所有 API 请求

2. **装饰器手动包裹**
   - 文件: `backend/utils/decorators.py`
   - 用于特定接口的精细控制

**前端控制 (三个层级):**

1. **动态路由** - 根据用户权限动态加载路由
2. **组件级权限** - 通过 `permission` store 管理
3. **按钮级权限** - 使用 `v-auth` 指令

### 7.3 超级管理员特权

```python
if user.is_superuser:
    return True  # 绕过所有权限检查
```

---

## 八、索引和约束

### 8.1 主键索引

所有表都有主键索引 (自动创建)

### 8.2 唯一索引

```sql
-- 用户表
CREATE UNIQUE INDEX user_user_username ON user_user(username);
CREATE UNIQUE INDEX user_user_email ON user_user(email);
CREATE UNIQUE INDEX idx_user_phone ON user_user(phone) WHERE phone IS NOT NULL;

-- 角色表
CREATE UNIQUE INDEX system_role_code ON system_role(code);

-- 部门表
CREATE UNIQUE INDEX system_deptinfo_code ON system_deptinfo(code);
```

### 8.3 外键约束

```sql
-- 用户 → 部门
ALTER TABLE user_user
ADD CONSTRAINT fk_user_dept
FOREIGN KEY (dept_id) REFERENCES system_deptinfo(id) ON DELETE PROTECT;

-- 用户角色关联
ALTER TABLE user_user_role
ADD CONSTRAINT fk_user_role_user
FOREIGN KEY (user_id) REFERENCES user_user(id) ON DELETE CASCADE;

ALTER TABLE user_user_role
ADD CONSTRAINT fk_user_role_role
FOREIGN KEY (role_id) REFERENCES system_role(id) ON DELETE CASCADE;

-- 角色菜单关联
ALTER TABLE system_role_menu
ADD CONSTRAINT fk_role_menu_role
FOREIGN KEY (role_id) REFERENCES system_role(id) ON DELETE CASCADE;

ALTER TABLE system_role_menu
ADD CONSTRAINT fk_role_menu_menu
FOREIGN KEY (menu_id) REFERENCES system_menu(id) ON DELETE CASCADE;
```

---

## 九、数据示例

### 9.1 用户数据

| 用户名 | 邮箱 | 手机号 | 部门 | 角色 |
|--------|------|--------|------|------|
| admin | admin@kworlds.cn | 13800138000 | 管理部门 | 超级管理员 |
| 平台用户管理员 | useradmin@163.com | 13900139000 | 管理部门 | 平台用户管理员 |

### 9.2 角色权限

| 角色 | 代码 | 权限数量 |
|------|------|---------|
| 超级管理员 | superadmin | 29 |
| 平台用户管理员 | useradmin | 11 |
| 销售员 | sales | 2 |
| 店长 | storemanager | 0 |
| 管理员 | admins | 0 |

### 9.3 菜单结构

| 菜单名称 | 路径 | 类型 | 子项数量 |
|---------|------|------|---------|
| Home | / | 菜单 | 1 |
| 功能测试 | /test | 菜单 | 1 |
| 系统管理 | /system | 菜单 | 4 |
| 系统监控 | /monitor | 菜单 | 2 |

---

## 十、数据库维护

### 10.1 备份命令

```bash
# 完整备份
cp backend/db.sqlite3 backup/db_$(date +%Y%m%d).sqlite3

# 导出 SQL
sqlite3 backend/db.sqlite3 .dump > backup/dump_$(date +%Y%m%d).sql
```

### 10.2 恢复命令

```bash
# 从备份恢复
cp backup/db_20250104.sqlite3 backend/db.sqlite3

# 从 SQL 导入
sqlite3 backend/db.sqlite3 < backup/dump_20250104.sql
```

### 10.3 清理日志

```bash
# 清理 30 天前的操作日志
sqlite3 backend/db.sqlite3 "DELETE FROM monitor_operationlog WHERE create_time < datetime('now', '-30 days')"

# 清理 90 天前的登录日志
sqlite3 backend/db.sqlite3 "DELETE FROM monitor_loginlog WHERE create_time < datetime('now', '-90 days')"
```

### 10.4 数据库优化

```bash
# 真空整理
sqlite3 backend/db.sqlite3 "VACUUM;"

# 分析统计
sqlite3 backend/db.sqlite3 "ANALYZE;"
```

---

## 十一、常用查询 SQL

### 11.1 用户及其权限

```sql
-- 查询用户的所有权限
SELECT u.username, m.name as permission_name, m.code as permission_code
FROM user_user u
JOIN user_user_role ur ON u.id = ur.user_id
JOIN system_role r ON ur.role_id = r.id
JOIN system_role_menu rm ON r.id = rm.role_id
JOIN system_menu m ON rm.menu_id = m.id
WHERE m.menu_type = 2  -- 只查权限,不查菜单
  AND u.username = 'admin';
```

### 11.2 部门用户统计

```sql
-- 按部门统计用户数
SELECT d.name, COUNT(u.id) as user_count
FROM system_deptinfo d
LEFT JOIN user_user u ON d.id = u.dept_id
GROUP BY d.id;
```

### 11.3 登录统计

```sql
-- 最近7天登录统计
SELECT DATE(create_time) as date, COUNT(*) as login_count
FROM monitor_loginlog
WHERE create_time >= datetime('now', '-7 days')
GROUP BY DATE(create_time)
ORDER BY date;
```

---

## 十二、升级历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2024-09-06 | 初始版本 |
| 1.1.0 | 2025-10-04 | 新增 phone 字段,支持手机号登录 |

---

**文档维护者:** Pure DRF Team
**最后更新:** 2025-10-04
