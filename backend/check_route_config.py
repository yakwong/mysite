#!/usr/bin/env python3
"""
路由配置一致性检查脚本

检查前端、后端数据文件、数据库三处的根路由 redirect 配置是否一致
用于部署前验证或排查路由跳转问题

使用方法:
    python check_route_config.py
"""

import json
import sqlite3
import os
import re
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_ROUTE_FILE = PROJECT_ROOT / "frontend" / "src" / "router" / "index.ts"
BACKEND_DATA_FILE = PROJECT_ROOT / "backend" / "data.json"
BACKEND_DB_FILE = PROJECT_ROOT / "backend" / "db.sqlite3"


def check_frontend_config():
    """检查前端路由配置"""
    print("\n【1. 前端配置】")
    print(f"文件: {FRONTEND_ROUTE_FILE.relative_to(PROJECT_ROOT)}")

    if not FRONTEND_ROUTE_FILE.exists():
        print("  ❌ 文件不存在!")
        return None

    with open(FRONTEND_ROUTE_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
        pattern = r"const\s+staticRootRoute[^=]*=\s*{.*?redirect:\s*\"([^\"]+)\""
        match = re.search(pattern, content, re.S)
        if not match:
            print("  ❌ 未找到 staticRootRoute.redirect 配置")
            return None
        redirect = match.group(1)
        print(f"  redirect: {redirect}")
        if redirect == "/welcome":
            print("  ✅ redirect = /welcome")
        elif redirect == "/home":
            print("  ⚠️  redirect = /home")
        else:
            print(f"  ⚠️ 尝试解析到 redirect = {redirect}")
        return redirect
    return None


def check_data_json():
    """检查 data.json 配置"""
    print("\n【2. 后端初始化数据 (data.json)】")
    print(f"文件: {BACKEND_DATA_FILE.relative_to(PROJECT_ROOT)}")

    if not BACKEND_DATA_FILE.exists():
        print("  ❌ 文件不存在!")
        return None

    with open(BACKEND_DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for item in data:
            if item.get('model') == 'system.menu':
                fields = item.get('fields', {})
                if fields.get('path') == '/' and fields.get('parent') is None:
                    redirect = fields.get('redirect')
                    print(f"  菜单 ID: {item['pk']}")
                    print(f"  名称: {fields.get('name')}")
                    print(f"  redirect: {redirect}")

                    if redirect == '/welcome':
                        print("  ✅ redirect = /welcome")
                    elif redirect == '/home':
                        print("  ⚠️  redirect = /home")
                    else:
                        print(f"  ❌ redirect = {redirect}")
                    return redirect
    return None


def check_database():
    """检查数据库配置"""
    print("\n【3. 运行时数据库 (db.sqlite3)】")
    print(f"文件: {BACKEND_DB_FILE.relative_to(PROJECT_ROOT)}")

    if not BACKEND_DB_FILE.exists():
        print("  ❌ 数据库文件不存在!")
        return None

    try:
        conn = sqlite3.connect(BACKEND_DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, path, redirect
            FROM system_menu
            WHERE path = '/' AND parent_id IS NULL
            LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()

        if result:
            menu_id, name, path, redirect = result
            print(f"  菜单 ID: {menu_id}")
            print(f"  名称: {name}")
            print(f"  redirect: {redirect}")

            if redirect == '/welcome':
                print("  ✅ redirect = /welcome")
            elif redirect == '/home':
                print("  ⚠️  redirect = /home")
            else:
                print(f"  ❌ redirect = {redirect}")
            return redirect
        else:
            print("  ❌ 未找到根路由配置!")
            return None
    except Exception as e:
        print(f"  ❌ 数据库查询失败: {e}")
        return None


def main():
    print("=" * 70)
    print("前后端路由配置一致性检查")
    print("=" * 70)

    # 检查三处配置
    frontend_redirect = check_frontend_config()
    datajson_redirect = check_data_json()
    database_redirect = check_database()

    # 汇总结果
    print("\n" + "=" * 70)
    print("检查结果汇总:")
    print("=" * 70)

    configs = {
        '前端配置': frontend_redirect,
        'data.json': datajson_redirect,
        '数据库': database_redirect
    }

    # 检查是否一致
    unique_values = set(v for v in configs.values() if v is not None)

    if len(unique_values) == 1:
        redirect_value = unique_values.pop()
        print(f"\n✅ 所有配置一致: redirect = {redirect_value}")
        print("\n📝 说明:")
        print("  - 前端配置作为默认兜底")
        print("  - 后端数据库配置会覆盖前端")
        print("  - data.json 用于初始化/重置数据库")
        print("  - 当前三者保持一致,配置正确!")
        return 0
    else:
        print("\n❌ 配置不一致,请检查!")
        for name, value in configs.items():
            if value:
                print(f"  {name}: {value}")
            else:
                print(f"  {name}: (未找到或读取失败)")

        print("\n🔧 建议:")
        print("  1. 确定使用哪个 redirect 值 (/welcome 或 /home)")
        print("  2. 统一修改三处配置")
        print("  3. 重新运行本脚本验证")
        return 1


if __name__ == '__main__':
    exit(main())
