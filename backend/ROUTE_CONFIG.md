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
