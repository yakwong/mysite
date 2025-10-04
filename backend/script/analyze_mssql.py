#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""MSSQL ERP 元数据分析工具。"""
import argparse
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import environ
import pyodbc


@dataclass
class ColumnInfo:
    """列结构信息。"""

    name: str
    data_type: str
    max_length: Optional[int]
    precision: Optional[int]
    scale: Optional[int]
    is_nullable: bool
    is_identity: bool
    is_computed: bool
    description: Optional[str]


@dataclass
class ForeignKeyInfo:
    """外键约束信息。"""

    name: str
    columns: List[str]
    referenced_table: str
    referenced_columns: List[str]


@dataclass
class TableInfo:
    """表的综合信息。"""

    object_id: int
    schema: str
    name: str
    row_count: int
    create_date: Optional[str]
    modify_date: Optional[str]
    description: Optional[str]
    columns: List[ColumnInfo] = field(default_factory=list)
    primary_key: List[str] = field(default_factory=list)
    foreign_keys: List[ForeignKeyInfo] = field(default_factory=list)
    referenced_by: List[ForeignKeyInfo] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        return f"{self.schema}.{self.name}" if self.schema else self.name


MODULE_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "采购（进）": {
        "table": [
            "purchase",
            "procure",
            "inbound",
            "receipt",
            "receive",
            "inorder",
            "supplier",
            "vendor",
            "wms_in",
            "入库",
            "采购",
            "进货",
        ],
        "column": [
            "supplier",
            "vendor",
            "purchase",
            "receive",
            "到货",
            "采购",
            "入库",
        ],
    },
    "销售（销）": {
        "table": [
            "sale",
            "order",
            "invoice",
            "delivery",
            "shipment",
            "outbound",
            "customer",
            "so",
            "发货",
            "出库",
            "销售",
        ],
        "column": [
            "customer",
            "client",
            "sales",
            "order",
            "发货",
            "出库",
            "销售",
        ],
    },
    "库存（存）": {
        "table": [
            "inventory",
            "stock",
            "warehouse",
            "wh",
            "balance",
            "ledger",
            "lot",
            "batch",
            "仓库",
            "库存",
            "存量",
        ],
        "column": [
            "stock",
            "inventory",
            "warehouse",
            "qty",
            "quantity",
            "批次",
            "仓库",
            "库存",
        ],
    },
    "商品资料": {
        "table": [
            "product",
            "item",
            "sku",
            "goods",
            "material",
            "catalog",
            "master",
            "物料",
            "商品",
        ],
        "column": [
            "product",
            "item",
            "sku",
            "goods",
            "material",
            "品名",
            "规格",
            "条码",
        ],
    },
    "往来结算": {
        "table": [
            "account",
            "payable",
            "receivable",
            "settlement",
            "payment",
            "cash",
            "finance",
            "ledger",
            "aging",
            "往来",
            "应收",
            "应付",
        ],
        "column": [
            "payable",
            "receivable",
            "balance",
            "amount",
            "payment",
            "收款",
            "付款",
            "对账",
            "往来",
            "应收",
            "应付",
        ],
    },
}


class SQLServerAnalyzer:
    """执行 MSSQL 元数据分析的主体类。"""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.env = environ.Env()
        base_dir = Path(__file__).resolve().parent.parent
        dotenv_path = base_dir / ".env"
        if dotenv_path.exists():
            environ.Env.read_env(str(dotenv_path))
        self.config = self._build_config()

    def _build_config(self) -> Dict[str, str]:
        cfg = {
            "server": self.args.server
            or self.env("MSSQL_SERVER", default=None),
            "port": self.args.port
            or self.env.int("MSSQL_PORT", default=None),
            "database": self.args.database
            or self.env("MSSQL_DATABASE", default=None),
            "user": self.args.user
            or self.env("MSSQL_USER", default=None),
            "password": self.args.password
            or self.env("MSSQL_PASSWORD", default=None),
            "driver": self.args.driver
            or self.env("MSSQL_DRIVER", default="ODBC Driver 17 for SQL Server"),
            "trusted": self.args.trusted
            if self.args.trusted is not None
            else self.env.bool("MSSQL_TRUSTED", default=False),
            "encrypt": self.args.encrypt
            if self.args.encrypt is not None
            else self.env.bool("MSSQL_ENCRYPT", default=False),
            "trust_cert": self.args.trust_cert
            if self.args.trust_cert is not None
            else self.env.bool("MSSQL_TRUST_CERT", default=False),
        }

        if not cfg["server"]:
            raise ValueError("未提供 MSSQL 服务器地址，可通过 --server 或环境变量 MSSQL_SERVER 设置。")
        if cfg["trusted"]:
            cfg.setdefault("user", "")
            cfg.setdefault("password", "")
        else:
            if not cfg["user"] or not cfg["password"]:
                raise ValueError("未提供数据库账号或密码，可通过参数或环境变量提供，或改用受信任连接。")
        if not cfg["database"]:
            raise ValueError("未提供数据库名称，可通过 --database 或环境变量 MSSQL_DATABASE 设置。")
        return cfg

    def _build_connection_string(self) -> str:
        server_target = self.config["server"]
        if self.config.get("port"):
            server_target = f"{server_target},{self.config['port']}"
        parts = [
            f"DRIVER={{{self.config['driver']}}}",
            f"SERVER={server_target}",
            f"DATABASE={self.config['database']}",
        ]
        if self.config["trusted"]:
            parts.append("Trusted_Connection=yes")
        else:
            parts.append(f"UID={self.config['user']}")
            parts.append(f"PWD={self.config['password']}")
        if self.config["encrypt"]:
            parts.append("Encrypt=yes")
        else:
            parts.append("Encrypt=no")
        if self.config["trust_cert"]:
            parts.append("TrustServerCertificate=yes")
        return ";".join(parts)

    def _connect(self) -> pyodbc.Connection:
        try:
            return pyodbc.connect(
                self._build_connection_string(),
                timeout=self.args.timeout,
                autocommit=True,
            )
        except pyodbc.InterfaceError as exc:
            raise ConnectionError(f"ODBC 连接失败：{exc}")
        except pyodbc.Error as exc:
            raise ConnectionError(f"数据库连接出错：{exc}")

    def _fetch_tables(self, cursor: pyodbc.Cursor) -> Dict[int, TableInfo]:
        sql = """
        SELECT
            t.object_id AS object_id,
            s.name AS schema_name,
            t.name AS table_name,
            CAST(ISNULL(ep.value, '') AS NVARCHAR(MAX)) AS table_description,
            t.create_date,
            t.modify_date,
            SUM(p.rows) AS row_count
        FROM sys.tables AS t
        INNER JOIN sys.schemas AS s ON t.schema_id = s.schema_id
        INNER JOIN sys.partitions AS p ON t.object_id = p.object_id AND p.index_id IN (0, 1)
        LEFT JOIN sys.extended_properties AS ep
            ON ep.major_id = t.object_id AND ep.minor_id = 0 AND ep.name = 'MS_Description'
        WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
        GROUP BY t.object_id, s.name, t.name, ep.value, t.create_date, t.modify_date
        ORDER BY s.name, t.name;
        """
        cursor.execute(sql)
        tables: Dict[int, TableInfo] = {}
        for row in cursor.fetchall():
            object_id = int(row.object_id)
            tables[object_id] = TableInfo(
                object_id=object_id,
                schema=str(row.schema_name),
                name=str(row.table_name),
                row_count=int(row.row_count or 0),
                create_date=row.create_date.isoformat() if row.create_date else None,
                modify_date=row.modify_date.isoformat() if row.modify_date else None,
                description=str(row.table_description) if row.table_description else None,
            )
        return tables

    def _fetch_columns(self, cursor: pyodbc.Cursor, tables: Dict[int, TableInfo]) -> None:
        sql = """
        SELECT
            c.object_id,
            c.column_id,
            c.name AS column_name,
            tp.name AS data_type,
            c.max_length,
            c.precision,
            c.scale,
            c.is_nullable,
            COLUMNPROPERTY(c.object_id, c.name, 'IsIdentity') AS is_identity,
            COLUMNPROPERTY(c.object_id, c.name, 'IsComputed') AS is_computed,
            CAST(ISNULL(ep.value, '') AS NVARCHAR(MAX)) AS column_description
        FROM sys.columns AS c
        INNER JOIN sys.tables AS t ON c.object_id = t.object_id
        INNER JOIN sys.schemas AS s ON t.schema_id = s.schema_id
        INNER JOIN sys.types AS tp ON c.user_type_id = tp.user_type_id
        LEFT JOIN sys.extended_properties AS ep
            ON ep.major_id = c.object_id AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
        WHERE s.name NOT IN ('sys', 'INFORMATION_SCHEMA')
        ORDER BY c.object_id, c.column_id;
        """
        cursor.execute(sql)
        for row in cursor.fetchall():
            object_id = int(row.object_id)
            table = tables.get(object_id)
            if not table:
                continue
            table.columns.append(
                ColumnInfo(
                    name=str(row.column_name),
                    data_type=str(row.data_type),
                    max_length=int(row.max_length) if row.max_length is not None else None,
                    precision=int(row.precision) if row.precision is not None else None,
                    scale=int(row.scale) if row.scale is not None else None,
                    is_nullable=bool(row.is_nullable),
                    is_identity=bool(row.is_identity),
                    is_computed=bool(row.is_computed),
                    description=str(row.column_description) if row.column_description else None,
                )
            )

    def _fetch_primary_keys(self, cursor: pyodbc.Cursor, tables: Dict[int, TableInfo]) -> None:
        sql = """
        SELECT
            kc.parent_object_id AS object_id,
            c.name AS column_name,
            ic.key_ordinal
        FROM sys.key_constraints AS kc
        INNER JOIN sys.index_columns AS ic
            ON kc.parent_object_id = ic.object_id AND kc.unique_index_id = ic.index_id
        INNER JOIN sys.columns AS c
            ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE kc.[type] = 'PK'
        ORDER BY kc.parent_object_id, ic.key_ordinal;
        """
        cursor.execute(sql)
        pk_map: Dict[int, List[str]] = defaultdict(list)
        for row in cursor.fetchall():
            pk_map[int(row.object_id)].append(str(row.column_name))
        for object_id, columns in pk_map.items():
            table = tables.get(object_id)
            if table:
                table.primary_key = columns

    def _fetch_foreign_keys(self, cursor: pyodbc.Cursor, tables: Dict[int, TableInfo]) -> None:
        sql = """
        SELECT
            fk.name AS fk_name,
            fkc.constraint_column_id,
            fkc.parent_object_id AS parent_object_id,
            fkc.referenced_object_id AS referenced_object_id,
            cp.name AS parent_column,
            cr.name AS referenced_column,
            OBJECT_SCHEMA_NAME(fkc.parent_object_id) AS parent_schema,
            OBJECT_NAME(fkc.parent_object_id) AS parent_table,
            OBJECT_SCHEMA_NAME(fkc.referenced_object_id) AS referenced_schema,
            OBJECT_NAME(fkc.referenced_object_id) AS referenced_table
        FROM sys.foreign_key_columns AS fkc
        INNER JOIN sys.foreign_keys AS fk ON fkc.constraint_object_id = fk.object_id
        INNER JOIN sys.columns AS cp
            ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
        INNER JOIN sys.columns AS cr
            ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
        ORDER BY fk.name, fkc.constraint_column_id;
        """
        cursor.execute(sql)
        child_map: Dict[int, Dict[str, ForeignKeyInfo]] = defaultdict(dict)
        parent_map: Dict[int, Dict[str, ForeignKeyInfo]] = defaultdict(dict)
        for row in cursor.fetchall():
            fk_name = str(row.fk_name)
            parent_object_id = int(row.parent_object_id)
            referenced_object_id = int(row.referenced_object_id)
            child_entry = child_map[parent_object_id].setdefault(
                fk_name,
                ForeignKeyInfo(
                    name=fk_name,
                    columns=[],
                    referenced_table=f"{row.referenced_schema}.{row.referenced_table}",
                    referenced_columns=[],
                ),
            )
            parent_entry = parent_map[referenced_object_id].setdefault(
                fk_name,
                ForeignKeyInfo(
                    name=fk_name,
                    columns=[],
                    referenced_table=f"{row.parent_schema}.{row.parent_table}",
                    referenced_columns=[],
                ),
            )
            child_entry.columns.append(str(row.parent_column))
            child_entry.referenced_columns.append(str(row.referenced_column))
            parent_entry.columns.append(str(row.referenced_column))
            parent_entry.referenced_columns.append(str(row.parent_column))
        for object_id, fk_dict in child_map.items():
            table = tables.get(object_id)
            if table:
                table.foreign_keys = [
                    ForeignKeyInfo(
                        name=item.name,
                        columns=list(dict.fromkeys(item.columns)),
                        referenced_table=item.referenced_table,
                        referenced_columns=list(dict.fromkeys(item.referenced_columns)),
                    )
                    for item in fk_dict.values()
                ]
        for object_id, fk_dict in parent_map.items():
            table = tables.get(object_id)
            if table:
                table.referenced_by = [
                    ForeignKeyInfo(
                        name=item.name,
                        columns=list(dict.fromkeys(item.columns)),
                        referenced_table=item.referenced_table,
                        referenced_columns=list(dict.fromkeys(item.referenced_columns)),
                    )
                    for item in fk_dict.values()
                ]

    def _analyze_modules(self, tables: Dict[int, TableInfo]) -> Dict[str, List[Dict[str, object]]]:
        summary: Dict[str, List[Dict[str, object]]] = {}
        for module, patterns in MODULE_PATTERNS.items():
            candidates: List[Dict[str, object]] = []
            for table in tables.values():
                score = 0
                reasons: List[str] = []
                name_lower = table.name.lower()
                schema_lower = table.schema.lower() if table.schema else ""
                description_lower = (table.description or "").lower()
                for keyword in patterns.get("table", []):
                    kw = keyword.lower()
                    if kw in name_lower or kw in schema_lower:
                        score += 3
                        reasons.append(f"表名命中关键词 `{keyword}`")
                    elif kw and kw in description_lower:
                        score += 2
                        reasons.append(f"表描述命中关键词 `{keyword}`")
                for column in table.columns:
                    col_name_lower = column.name.lower()
                    col_desc_lower = (column.description or "").lower()
                    for keyword in patterns.get("column", []):
                        kw = keyword.lower()
                        if kw in col_name_lower:
                            score += 1
                            reasons.append(f"字段 `{column.name}` 命中关键词 `{keyword}`")
                        elif kw and kw in col_desc_lower:
                            score += 1
                            reasons.append(f"字段 `{column.name}` 描述命中 `{keyword}`")
                if score:
                    upstream = sorted({fk.referenced_table for fk in table.foreign_keys})
                    downstream = sorted({fk.referenced_table for fk in table.referenced_by})
                    candidates.append(
                        {
                            "table": table.full_name,
                            "score": score,
                            "row_count": table.row_count,
                            "primary_key": table.primary_key,
                            "upstream": upstream,
                            "downstream": downstream,
                            "reasons": sorted(set(reasons))[:6],
                        }
                    )
            summary[module] = sorted(
                candidates,
                key=lambda item: (item["score"], item["row_count"]),
                reverse=True,
            )[: self.args.top]
        return summary

    def _export_json(
        self,
        tables: Dict[int, TableInfo],
        module_summary: Dict[str, List[Dict[str, object]]],
        output_path: Path,
    ) -> None:
        payload = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "server": self.config["server"],
            "database": self.config["database"],
            "table_count": len(tables),
            "modules": module_summary,
            "tables": {
                table.full_name: {
                    "schema": table.schema,
                    "name": table.name,
                    "row_count": table.row_count,
                    "create_date": table.create_date,
                    "modify_date": table.modify_date,
                    "description": table.description,
                    "primary_key": table.primary_key,
                    "columns": [
                        {
                            "name": column.name,
                            "data_type": column.data_type,
                            "max_length": column.max_length,
                            "precision": column.precision,
                            "scale": column.scale,
                            "is_nullable": column.is_nullable,
                            "is_identity": column.is_identity,
                            "is_computed": column.is_computed,
                            "description": column.description,
                        }
                        for column in table.columns
                    ],
                    "foreign_keys": [
                        {
                            "name": fk.name,
                            "columns": fk.columns,
                            "referenced_table": fk.referenced_table,
                            "referenced_columns": fk.referenced_columns,
                        }
                        for fk in table.foreign_keys
                    ],
                    "referenced_by": [
                        {
                            "name": fk.name,
                            "columns": fk.columns,
                            "source_table": fk.referenced_table,
                            "source_columns": fk.referenced_columns,
                        }
                        for fk in table.referenced_by
                    ],
                }
                for table in tables.values()
            },
        }
        with output_path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)

    def _export_markdown(
        self,
        tables: Dict[int, TableInfo],
        module_summary: Dict[str, List[Dict[str, object]]],
        output_path: Path,
    ) -> None:
        lines: List[str] = []
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")
        lines.append("# MSSQL 元数据分析报告")
        lines.append("")
        lines.append(f"- 生成时间：{now_str}")
        lines.append(f"- 目标服务器：{self.config['server']}")
        lines.append(f"- 数据库：{self.config['database']}")
        lines.append(f"- 表总数：{len(tables)}")
        lines.append("")
        lines.append("## 重点业务模块匹配结果")
        for module, items in module_summary.items():
            lines.append("")
            lines.append(f"### {module}")
            if not items:
                lines.append("- 未找到明显相关的表。")
                continue
            for idx, item in enumerate(items, start=1):
                lines.append(
                    f"{idx}. `{item['table']}`（得分 {item['score']}，行数 {item['row_count']}）"
                )
                if item.get("reasons"):
                    lines.append("   - 依据：" + "；".join(item["reasons"]))
                if item.get("primary_key"):
                    lines.append("   - 主键：" + ", ".join(item["primary_key"]))
                if item.get("upstream"):
                    lines.append("   - 上游相关表：" + ", ".join(item["upstream"]))
                if item.get("downstream"):
                    lines.append("   - 下游相关表：" + ", ".join(item["downstream"]))
        lines.append("")
        lines.append("## 数据量 Top 15 表")
        top_tables = sorted(
            tables.values(),
            key=lambda tbl: tbl.row_count,
            reverse=True,
        )[:15]
        for table in top_tables:
            lines.append(
                f"- `{table.full_name}`：{table.row_count} 行，最近修改 {table.modify_date or '未知'}"
            )
        with output_path.open("w", encoding="utf-8") as fp:
            fp.write("\n".join(lines))

    def run(self) -> Dict[str, Path]:
        try:
            connection = self._connect()
        except ConnectionError as exc:
            raise SystemExit(str(exc))
        with connection:
            cursor = connection.cursor()
            tables = self._fetch_tables(cursor)
            if not tables:
                raise SystemExit("未检索到任何用户表，请检查数据库或权限。")
            self._fetch_columns(cursor, tables)
            self._fetch_primary_keys(cursor, tables)
            self._fetch_foreign_keys(cursor, tables)
        module_summary = self._analyze_modules(tables)
        output_dir = Path(self.args.output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_dir / f"mssql_analysis_{timestamp}.json"
        markdown_path = output_dir / f"mssql_analysis_{timestamp}.md"
        self._export_json(tables, module_summary, json_path)
        self._export_markdown(tables, module_summary, markdown_path)
        return {"json": json_path, "markdown": markdown_path}


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="连接 MSSQL 数据库并输出 ERP 进销存模块的元数据分析报告",
    )
    parser.add_argument("--server", help="MSSQL 服务器地址，可包含实例名，例如 192.168.1.10\\SQLEXPRESS")
    parser.add_argument("--port", type=int, help="MSSQL 端口，默认 1433", default=None)
    parser.add_argument("--database", help="目标数据库名称")
    parser.add_argument("--user", help="数据库用户名")
    parser.add_argument("--password", help="数据库密码")
    parser.add_argument(
        "--driver",
        default=None,
        help="ODBC 驱动名称，默认 ODBC Driver 17 for SQL Server",
    )
    parser.add_argument(
        "--trusted",
        dest="trusted",
        action="store_true",
        help="启用受信任连接（Windows 集成认证）",
    )
    parser.add_argument(
        "--no-trusted",
        dest="trusted",
        action="store_false",
        help="禁用受信任连接",
    )
    parser.set_defaults(trusted=None)
    parser.add_argument(
        "--encrypt",
        dest="encrypt",
        action="store_true",
        help="启用加密传输",
    )
    parser.add_argument(
        "--no-encrypt",
        dest="encrypt",
        action="store_false",
        help="禁用加密传输",
    )
    parser.set_defaults(encrypt=None)
    parser.add_argument(
        "--trust-cert",
        dest="trust_cert",
        action="store_true",
        help="信任服务器证书（配合 Encrypt 使用）",
    )
    parser.add_argument(
        "--no-trust-cert",
        dest="trust_cert",
        action="store_false",
        help="不信任服务器证书",
    )
    parser.set_defaults(trust_cert=None)
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="连接超时时间（秒），默认 15",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / "output"),
        help="分析结果输出目录，默认脚本目录下的 output/",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=8,
        help="每个业务模块展示的候选表数量，默认 8",
    )
    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()
    try:
        analyzer = SQLServerAnalyzer(args)
    except ValueError as exc:
        parser.error(str(exc))
    outputs = analyzer.run()
    print("分析完成！")
    print(f"JSON 结果：{outputs['json']}")
    print(f"Markdown 报告：{outputs['markdown']}")


if __name__ == "__main__":
    main()
