# 路由配置说明

> 2025-10-04 校准：新增 `/api/user/profile/login-notifier/` 登录提醒开关接口，详见 `apps/user/views.py` 与 `docs/CODE_OVERVIEW.md`。

## 概述

本项目采用 **后端完全控制** 的路由配置策略,即后端数据库中的路由配置会覆盖前端默认配置,实现 RBAC 权限系统的动态首页控制。

## 配置文件位置

| 位置 | 文件路径 | 作用 | 优先级 |
|------|---------|------|--------|
| 前端 | `frontend/src/router/modules/home.ts` | 默认兜底配置 | 低 |
| 后端数据 | `backend/data.json` | 数据库初始化数据 | 中 |
| 运行时 | `backend/db.sqlite3` (`system_menu` 表) | 实际生效配置 | **高** |

## 钉钉独立模块接口

钉钉模块已拆分为独立的 `apps.dingtalk`，以下为核心 REST 接口（省略标准 `list`/`retrieve`/`create`/`update`/`destroy` 的 `OPTIONS`）：

| 路径 | 方法 | 权限代码示例 | 说明 |
| ---- | ---- | ------------ | ---- |
| `/api/dingtalk/configs/` | GET/POST | `/api/dingtalk/configs/:read` | 查询或创建钉钉配置，默认返回 `default` 配置 |
| `/api/dingtalk/configs/{id}/` | GET/PUT/PATCH/DELETE | `/api/dingtalk/configs/:change` | 管理指定配置，更新 AppKey 自动重置 Token |
| `/api/dingtalk/configs/{id}/sync_info/` | GET | `/api/dingtalk/configs/sync_info/:read` | 获取最近同步状态、计数与 Token 过期时间 |
| `/api/dingtalk/{config_id}/sync/` | POST | `/api/dingtalk/sync/:add` | 触发指定配置的同步（测试连通、部门、用户、考勤、全量） |
| `/api/dingtalk/sync/` | POST | `/api/dingtalk/sync/:add` | 使用默认配置触发同步 |
| `/api/dingtalk/logs/` | GET | `/api/dingtalk/logs/:read` | 查看同步日志，支持状态/时间过滤 |
| `/api/dingtalk/departments/remote/` | GET | `/api/dingtalk/departments/remote/:read` | 直连钉钉预览远端部门（支持 `config_id`、`limit`） |
| `/api/dingtalk/departments/` | GET | `/api/dingtalk/departments/:read` | 查看本地持久化的部门数据 |
| `/api/dingtalk/users/remote/` | GET | `/api/dingtalk/users/remote/:read` | 直连钉钉预览远端用户 |
| `/api/dingtalk/users/` | GET | `/api/dingtalk/users/:read` | 查看本地持久化的用户数据 |
| `/api/dingtalk/attendances/` | GET | `/api/dingtalk/attendances/:read` | 查看本地持久化的考勤记录 |
| `/api/dingtalk/cursors/` | GET | `/api/dingtalk/cursors/:read` | 查询增量同步游标 |
| `/api/dingtalk/dept-bindings/` | GET/POST | `/api/dingtalk/dept-bindings/:change` | 管理系统部门与钉钉部门的绑定关系 |
| `/api/dingtalk/user-bindings/` | GET/POST | `/api/dingtalk/user-bindings/:change` | 管理系统用户与钉钉用户的绑定关系 |
| `/api/dingtalk/{config_id}/callbacks/` | POST | `/api/dingtalk/callbacks/:add` | 钉钉事件回调入口（需在钉钉管理后台配置 token/aes_key） |

钉钉接口默认使用 JWT 鉴权与 `CanManageDingTalk`/`CanViewDingTalk` 权限类，可在路由管理中按需配置角色-菜单映射。

## 人力资源模块接口

| 路径 | 方法 | 权限代码示例 | 说明 |
| ---- | ---- | ------------ | ---- |
| `/api/hr/departments/` | GET/POST | `/api/hr/departments/:read` | 查询或创建部门，支持 `keyword`、`status` 过滤 |
| `/api/hr/departments/{id}/` | GET/PATCH/DELETE | `/api/hr/departments/:change` | 维护单个部门信息、上下级关系 |
| `/api/hr/departments/import/dingtalk/` | POST | `/api/hr/departments/import/:add` | 从钉钉同步最新部门至 HR 模块 |
| `/api/hr/employees/` | GET/POST | `/api/hr/employees/:read` | 查询或新增员工，支持部门、状态过滤 |
| `/api/hr/employees/{id}/` | GET/PATCH/DELETE | `/api/hr/employees/:change` | 编辑员工基础信息、雇佣状态、薪资参数 |
| `/api/hr/employees/import/dingtalk/` | POST | `/api/hr/employees/import/:add` | 从钉钉导入员工快照（自动匹配部门） |
| `/api/hr/attendance/rules/` | GET/POST | `/api/hr/attendance/rules/:read` | 管理考勤规则，配置工作时间与容忍阈值 |
| `/api/hr/attendance/rules/{id}/` | GET/PATCH/DELETE | `/api/hr/attendance/rules/:change` | 更新或删除指定规则 |
| `/api/hr/attendance/summary/` | GET | `/api/hr/attendance/summary/:read` | 查询考勤统计结果，支持员工、规则、时间段过滤 |
| `/api/hr/attendance/summary/calculate/` | POST | `/api/hr/attendance/summary/:add` | 依据钉钉打卡记录按规则生成考勤汇总 |
| `/api/hr/attendance/summary/status/` | POST | `/api/hr/attendance/summary/:change` | 批量更新统计状态（待确认/已确认） |
| `/api/hr/payroll/rules/` | GET/POST | `/api/hr/payroll/rules/:read` | 管理薪资计算规则（加班倍数、税率、补贴） |
| `/api/hr/payroll/rules/{id}/` | GET/PATCH/DELETE | `/api/hr/payroll/rules/:change` | 更新或删除指定薪资规则 |
| `/api/hr/payroll/records/` | GET | `/api/hr/payroll/records/:read` | 查看薪资发放记录，支持规则、周期过滤 |
| `/api/hr/payroll/records/{id}/` | GET/PATCH/DELETE | `/api/hr/payroll/records/:change` | 调整单条发薪记录（备注、状态等） |
| `/api/hr/payroll/records/calculate/` | POST | `/api/hr/payroll/records/:add` | 按规则和考勤统计批量计算薪资 |

## 当前配置

**所有位置统一配置为:** `redirect: "/welcome"`

```typescript
// frontend/src/router/modules/home.ts
export default {
  path: "/",
  redirect: "/welcome",  // ✅
  // ...
}
```

```json
// backend/data.json (system.menu)
{
  "path": "/",
  "redirect": "/welcome",  // ✅
  // ...
}
```

```sql
-- backend/db.sqlite3 (system_menu 表)
SELECT path, redirect FROM system_menu WHERE path = '/';
-- 结果: '/', '/welcome' ✅
```

## 工作机制

### 1. 前端路由加载流程

```
用户登录
    ↓
调用 initRouter()
    ↓
获取后端路由配置 (API: /api/system/menu/)
    ↓
handleAsyncRoutes() 处理路由
    ↓
检测到后端返回的 "/" 路由 (frontend/src/router/utils.ts:123)
    ↓
捕获为 rootRouteConfig,不重复注册 (避免 Vue Router 冲突)
    ↓
合并 redirect 和 meta 到前端根路由 (utils.ts:151-158)
    ↓
后端配置覆盖前端默认值 ✅
```

### 2. 关键代码位置

**前端路由处理:** `frontend/src/router/utils.ts:149-172`

```typescript
if (rootRouteConfig) {
  const rootOptions = router.options.routes[0];

  // 应用后端的 redirect 配置
  if (rootRouteConfig.redirect) {
    rootOptions.redirect = rootRouteConfig.redirect;
    const currentRoot = router.getRoutes().find(route => route.path === "/");
    if (currentRoot) {
      (currentRoot as any).redirect = rootRouteConfig.redirect;
    }
  }

  // 合并 meta 配置
  if (rootRouteConfig.meta) {
    rootOptions.meta = {
      ...(rootOptions.meta ?? {}),
      ...rootRouteConfig.meta,
      backstage: true
    };
  }
}
```

## 验证配置一致性

### 使用验证脚本

```bash
# 在项目根目录执行
python backend/check_route_config.py
```

**输出示例:**

```
======================================================================
前后端路由配置一致性检查
======================================================================

【1. 前端配置】
文件: frontend/src/router/modules/home.ts
  redirect: "/welcome",
  ✅ redirect = /welcome

【2. 后端初始化数据 (data.json)】
文件: backend/data.json
  菜单 ID: b7965934-3627-4c1d-a919-d52bb61212a9
  名称: 首页
  redirect: /welcome
  ✅ redirect = /welcome

【3. 运行时数据库 (db.sqlite3)】
文件: backend/db.sqlite3
  菜单 ID: b796593436274c1da919d52bb61212a9
  名称: Home
  redirect: /welcome
  ✅ redirect = /welcome

======================================================================
✅ 所有配置一致: redirect = /welcome
======================================================================
```

### 手动验证

#### 1. 检查前端配置

```bash
grep 'redirect:' frontend/src/router/modules/home.ts
```

#### 2. 检查后端数据文件

```bash
python3 << 'EOF'
import json
with open('backend/data.json', 'r') as f:
    data = json.load(f)
    for item in data:
        if item.get('model') == 'system.menu':
            fields = item.get('fields', {})
            if fields.get('path') == '/' and fields.get('parent') is None:
                print(f"redirect: {fields.get('redirect')}")
                break
EOF
```

#### 3. 检查数据库

```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('backend/db.sqlite3')
cursor = conn.cursor()
cursor.execute("SELECT redirect FROM system_menu WHERE path = '/' AND parent_id IS NULL")
print(f"redirect: {cursor.fetchone()[0]}")
conn.close()
EOF
```

## 修改配置

### 场景一: 修改默认首页

**步骤:**

1. 修改数据库 (生效最快)
   ```python
   import sqlite3
   conn = sqlite3.connect('backend/db.sqlite3')
   cursor = conn.cursor()
   cursor.execute("UPDATE system_menu SET redirect = '/new-home' WHERE path = '/' AND parent_id IS NULL")
   conn.commit()
   conn.close()
   ```

2. 修改 data.json (确保重置数据库时生效)
   ```json
   {
     "model": "system.menu",
     "fields": {
       "path": "/",
       "redirect": "/new-home"
     }
   }
   ```

3. 修改前端配置 (可选,作为兜底)
   ```typescript
   export default {
     path: "/",
     redirect: "/new-home"
   }
   ```

4. 验证
   ```bash
   python backend/check_route_config.py
   ```

### 场景二: 为不同角色配置不同首页

**方案 A: 通过菜单权限实现**

不同角色绑定不同的菜单配置,每个菜单配置有不同的根路由 redirect。

**方案 B: 前端动态判断**

在前端 `router/index.ts` 的 `beforeEach` 钩子中,根据用户角色动态修改 redirect:

```typescript
router.beforeEach((to, from, next) => {
  const userInfo = getUserInfo();
  if (to.path === '/' && userInfo) {
    if (userInfo.roles.includes('admin')) {
      next('/admin/dashboard');
    } else if (userInfo.roles.includes('user')) {
      next('/user/profile');
    } else {
      next('/welcome');
    }
  } else {
    next();
  }
});
```

## 部署注意事项

### 1. 首次部署

```bash
# 1. 运行数据库迁移
python backend/manage.py migrate

# 2. 加载初始数据
python backend/manage.py loaddata backend/data.json

# 3. 验证配置
python backend/check_route_config.py
```

### 2. 生产环境部署

确保 `backend/data.json` 与数据库保持一致,避免重置数据库时配置丢失。

### 3. Docker 部署

在 Dockerfile 或 docker-compose.yml 中添加健康检查:

```yaml
healthcheck:
  test: ["CMD", "python", "backend/check_route_config.py"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## 常见问题

### Q1: 登录后跳转到错误页面?

**原因:** 前后端配置不一致或缓存问题

**解决:**
1. 运行 `python backend/check_route_config.py` 检查配置
2. 清除浏览器缓存和 localStorage
3. 重启前后端服务

### Q2: 修改了数据库但不生效?

**原因:** 前端路由缓存或未重新加载路由

**解决:**
1. 退出登录重新登录 (触发路由重新加载)
2. 清除浏览器缓存
3. 检查 `frontend/src/router/utils.ts:151-158` 是否正确应用后端配置

### Q3: data.json 和数据库不一致?

**原因:** 手动修改了数据库但未同步到 data.json

**解决:**
1. 使用 Django 命令导出数据:
   ```bash
   python backend/manage.py dumpdata system.menu --indent 2 > menu_export.json
   ```
2. 手动合并到 data.json
3. 验证: `python backend/check_route_config.py`

## 总结

✅ **最佳实践:**
1. 始终保持三处配置一致 (前端、data.json、数据库)
2. 部署前运行验证脚本
3. 修改配置后记得同步更新所有位置
4. 使用后端控制实现动态首页跳转

✅ **优势:**
- 后端完全控制路由,支持 RBAC 动态权限
- 前端有兜底配置,确保系统稳定性
- data.json 确保数据库重置时配置不丢失
- 验证脚本快速排查配置问题

---

**最后更新:** 2025-10-04
**维护者:** Pure DRF Team
