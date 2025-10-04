<h1>Pure-drf 开源RBAC后台管理系统</h1>

*该页为后端代码，后端项目请前往[前端代码：pure-drf-admin](https://github.com/immrk/pure-drf-admin)*

[![license](https://img.shields.io/github/license/pure-admin/vue-pure-admin.svg)](LICENSE)

## 介绍

Pure drf 是一个使用Vue作为前端、Django(DRF)作为后端的RBAC开源管理后台框架

- **拥有完整的部门、角色、权限、用户、日志管理模块；**
- **账户安全中心**：支持密码强度检测、手机/备用邮箱绑定、密保问题、两步验证与登录提醒开关。
- **完善的前后端鉴权机制包括：**
  前端权限：动态路由、 组件、按钮；
  后端权限： 接口鉴权（中间件自动判断 / 装饰器手动包裹）

* [前端代码：pure-drf-admin](https://github.com/immrk/pure-drf-admin) ：前端代码基于[Pure admin](https://pure-admin.cn/) 开源前端框架二次开发，以适配DRF后端需求，前端代码fork同步[vue-pure-admin官方精简版](https://github.com/pure-admin/pure-admin-thin)
* [后端代码：pure-drf-admin-backend](https://github.com/immrk/pure-drf-admin-backend)： 后端代码采用标准化drf文件结构开发，包含redis、MySQL、docker部署等

## 预览

[点击前往预览➡️](https://puredrf.kworlds.cn)
预览账号: user@kworlds.cn
账号密码：k12345678

## 配套开发文档

[点我查看 PureDRF 文档➡️](https://puredrf.kworlds.cn/docs/)

- 仓库内新增 `docs/CODE_OVERVIEW.md`、`docs/CODE_FILES.md`，用于对照当前后端代码结构与逐文件详情。

## MSSQL 元数据分析脚本

- 依赖安装：`pip install -r script/requirements_mssql.txt`（需要预先安装对应的 ODBC 驱动）。
- 基本用法：`python script/analyze_mssql.py --server <服务器> --database <库名> --user <账号> --password <密码>`。
- 默认会在 `script/output/` 目录生成 JSON 与 Markdown 两份分析结果，内容包含表结构、主外键与进销存业务模块的候选表清单。
- 也支持通过 `.env` 定义 `MSSQL_SERVER`、`MSSQL_DATABASE`、`MSSQL_USER`、`MSSQL_PASSWORD` 等变量，并使用 `--trusted`、`--encrypt` 等选项适配不同环境。

## 维护者

[RoyKe](https://github.com/immrk)

## 合作联系

keyajian@gmail.com
注明标题：puredrf合作邮件

## 许可证

[MIT © 2024-present, puredrf](./LICENSE)
