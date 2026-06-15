from __future__ import annotations
from typing import Dict, Any, List
from shared.domain_model import (
    UnifiedDomainModel, DatabaseArtifact, TableDef, ColumnDef,
)


class DatabaseAgent:
    """Phase 3: Generate table definitions and multi-dialect DDL."""

    def execute(self, model: UnifiedDomainModel, params: Dict[str, Any]) -> Dict[str, Any]:
        domain_model = model.domain_model
        if not domain_model or not domain_model.use_cases:
            return {"error": "No use cases found. Complete Phase 2 first."}

        tables = self._generate_tables(domain_model)
        artifact = DatabaseArtifact()
        artifact.tables = tables
        artifact.ddl_mysql = self._generate_ddl(tables, "mysql")
        artifact.ddl_postgres = self._generate_ddl(tables, "postgres")
        artifact.ddl_sqlite = self._generate_ddl(tables, "sqlite")
        artifact.plantuml_er = self._generate_er_diagram(tables)
        artifact.uc_links = self._build_uc_links(tables, domain_model)

        model.database = artifact
        return {
            "tables": [t.to_dict() for t in tables],
            "ddl_mysql": artifact.ddl_mysql,
            "ddl_postgres": artifact.ddl_postgres,
            "ddl_sqlite": artifact.ddl_sqlite,
            "plantuml_er": artifact.plantuml_er,
        }

    def _generate_tables(self, domain_model) -> List[TableDef]:
        tables = [
            TableDef("users", [
                ColumnDef("id", "BIGINT", nullable=False, pk=True, comment="主键ID"),
                ColumnDef("username", "VARCHAR(50)", nullable=False, comment="用户名"),
                ColumnDef("password_hash", "VARCHAR(255)", nullable=False, comment="密码哈希"),
                ColumnDef("email", "VARCHAR(100)", comment="邮箱"),
                ColumnDef("phone", "VARCHAR(20)", comment="手机号"),
                ColumnDef("status", "TINYINT", nullable=False, default="1", comment="状态: 1=启用, 0=禁用"),
                ColumnDef("created_at", "DATETIME", nullable=False, default="CURRENT_TIMESTAMP", comment="创建时间"),
                ColumnDef("updated_at", "DATETIME", nullable=False, default="CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP", comment="更新时间"),
            ], "用户表"),
            TableDef("roles", [
                ColumnDef("id", "BIGINT", nullable=False, pk=True, comment="主键ID"),
                ColumnDef("name", "VARCHAR(50)", nullable=False, comment="角色名称"),
                ColumnDef("code", "VARCHAR(50)", nullable=False, comment="角色编码"),
                ColumnDef("description", "VARCHAR(255)", comment="角色描述"),
                ColumnDef("created_at", "DATETIME", nullable=False, default="CURRENT_TIMESTAMP", comment="创建时间"),
            ], "角色表"),
            TableDef("user_roles", [
                ColumnDef("id", "BIGINT", nullable=False, pk=True, comment="主键ID"),
                ColumnDef("user_id", "BIGINT", nullable=False, fk="users.id", comment="用户ID"),
                ColumnDef("role_id", "BIGINT", nullable=False, fk="roles.id", comment="角色ID"),
            ], "用户角色关联表"),
            TableDef("operation_logs", [
                ColumnDef("id", "BIGINT", nullable=False, pk=True, comment="主键ID"),
                ColumnDef("user_id", "BIGINT", nullable=False, fk="users.id", comment="操作用户ID"),
                ColumnDef("action", "VARCHAR(100)", nullable=False, comment="操作类型"),
                ColumnDef("target_type", "VARCHAR(50)", comment="操作对象类型"),
                ColumnDef("target_id", "VARCHAR(50)", comment="操作对象ID"),
                ColumnDef("detail", "TEXT", comment="操作详情"),
                ColumnDef("ip_address", "VARCHAR(45)", comment="IP地址"),
                ColumnDef("created_at", "DATETIME", nullable=False, default="CURRENT_TIMESTAMP", comment="创建时间"),
            ], "操作日志表"),
        ]

        combined = ""
        if hasattr(domain_model, 'use_cases'):
            for uc in domain_model.use_cases:
                combined += f" {uc.name} {uc.description}"

        if "商品" in combined or "product" in combined.lower():
            tables.append(TableDef("products", [
                ColumnDef("id", "BIGINT", nullable=False, pk=True, comment="主键ID"),
                ColumnDef("name", "VARCHAR(200)", nullable=False, comment="商品名称"),
                ColumnDef("description", "TEXT", comment="商品描述"),
                ColumnDef("price", "DECIMAL(10,2)", nullable=False, comment="价格"),
                ColumnDef("stock", "INT", nullable=False, default="0", comment="库存数量"),
                ColumnDef("category_id", "BIGINT", fk="categories.id", comment="分类ID"),
                ColumnDef("status", "TINYINT", nullable=False, default="1", comment="状态: 1=上架, 0=下架"),
                ColumnDef("created_at", "DATETIME", nullable=False, default="CURRENT_TIMESTAMP", comment="创建时间"),
                ColumnDef("updated_at", "DATETIME", nullable=False, default="CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP", comment="更新时间"),
            ], "商品表"))
            tables.append(TableDef("categories", [
                ColumnDef("id", "BIGINT", nullable=False, pk=True, comment="主键ID"),
                ColumnDef("name", "VARCHAR(100)", nullable=False, comment="分类名称"),
                ColumnDef("parent_id", "BIGINT", fk="categories.id", comment="父分类ID"),
                ColumnDef("sort_order", "INT", default="0", comment="排序"),
                ColumnDef("created_at", "DATETIME", nullable=False, default="CURRENT_TIMESTAMP", comment="创建时间"),
            ], "分类表"))
            tables.append(TableDef("orders", [
                ColumnDef("id", "BIGINT", nullable=False, pk=True, comment="主键ID"),
                ColumnDef("order_no", "VARCHAR(50)", nullable=False, comment="订单编号"),
                ColumnDef("user_id", "BIGINT", nullable=False, fk="users.id", comment="用户ID"),
                ColumnDef("total_amount", "DECIMAL(10,2)", nullable=False, comment="总金额"),
                ColumnDef("status", "VARCHAR(20)", nullable=False, default="pending", comment="订单状态"),
                ColumnDef("created_at", "DATETIME", nullable=False, default="CURRENT_TIMESTAMP", comment="创建时间"),
                ColumnDef("updated_at", "DATETIME", nullable=False, default="CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP", comment="更新时间"),
            ], "订单表"))

        return tables

    def _generate_ddl(self, tables: List[TableDef], dialect: str) -> str:
        type_map = {
            "mysql": {
                "BIGINT": "BIGINT",
                "VARCHAR(50)": "VARCHAR(50)",
                "VARCHAR(100)": "VARCHAR(100)",
                "VARCHAR(200)": "VARCHAR(200)",
                "VARCHAR(255)": "VARCHAR(255)",
                "VARCHAR(20)": "VARCHAR(20)",
                "TEXT": "TEXT",
                "TINYINT": "TINYINT",
                "INT": "INT",
                "DECIMAL(10,2)": "DECIMAL(10,2)",
                "DATETIME": "DATETIME",
            },
            "postgres": {
                "BIGINT": "BIGSERIAL",
                "VARCHAR(50)": "VARCHAR(50)",
                "VARCHAR(100)": "VARCHAR(100)",
                "VARCHAR(200)": "VARCHAR(200)",
                "VARCHAR(255)": "VARCHAR(255)",
                "VARCHAR(20)": "VARCHAR(20)",
                "TEXT": "TEXT",
                "TINYINT": "SMALLINT",
                "INT": "INTEGER",
                "DECIMAL(10,2)": "NUMERIC(10,2)",
                "DATETIME": "TIMESTAMP",
            },
            "sqlite": {
                "BIGINT": "INTEGER",
                "VARCHAR(50)": "TEXT",
                "VARCHAR(100)": "TEXT",
                "VARCHAR(200)": "TEXT",
                "VARCHAR(255)": "TEXT",
                "VARCHAR(20)": "TEXT",
                "TEXT": "TEXT",
                "TINYINT": "INTEGER",
                "INT": "INTEGER",
                "DECIMAL(10,2)": "REAL",
                "DATETIME": "TEXT",
            },
        }

        mapping = type_map.get(dialect, type_map["mysql"])
        lines = [f"-- {dialect.upper()} DDL generated by Waterfall Agent"]
        if dialect == "mysql":
            lines.append("SET NAMES utf8mb4;")
            lines.append("SET FOREIGN_KEY_CHECKS = 0;")
        lines.append("")

        for table in tables:
            lines.append(f"CREATE TABLE IF NOT EXISTS `{table.name}` (")
            col_lines = []
            for col in table.columns:
                dt = mapping.get(col.dtype, col.dtype)
                null_str = "NOT NULL" if not col.nullable else "DEFAULT NULL"
                pk_str = "AUTO_INCREMENT" if col.pk and dialect == "mysql" else ""
                if col.pk and dialect == "postgres":
                    pk_str = ""
                default_str = ""
                if col.default and col.default != "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP":
                    if col.default == "CURRENT_TIMESTAMP":
                        default_str = f"DEFAULT {col.default}" if dialect != "sqlite" else "DEFAULT CURRENT_TIMESTAMP"
                    else:
                        default_str = f"DEFAULT {col.default}"

                col_def = f"  `{col.name}` {dt}"
                if pk_str:
                    col_def += f" {pk_str}"
                col_def += f" {null_str}"
                if default_str:
                    col_def += f" {default_str}"
                if col.comment and dialect == "mysql":
                    col_def += f" COMMENT '{col.comment}'"
                col_lines.append(col_def)

            pk_cols = [f"`{c.name}`" for c in table.columns if c.pk]
            if pk_cols:
                col_lines.append(f"  PRIMARY KEY ({', '.join(pk_cols)})")

            fk_cols = [c for c in table.columns if c.fk]
            for c in fk_cols:
                ref_parts = c.fk.split(".")
                if len(ref_parts) == 2:
                    col_lines.append(f"  CONSTRAINT fk_{table.name}_{c.name} FOREIGN KEY (`{c.name}`) REFERENCES `{ref_parts[0]}` (`{ref_parts[1]}`)")

            lines.append(",\n".join(col_lines))
            if dialect == "mysql":
                lines.append(f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{table.comment}';")
            else:
                lines.append(");")
            lines.append("")

        if dialect == "mysql":
            lines.append("SET FOREIGN_KEY_CHECKS = 1;")
        return "\n".join(lines)

    def _generate_er_diagram(self, tables: List[TableDef]) -> str:
        lines = ["@startuml", "!theme plain", "skinparam backgroundColor #FEFEFE", ""]
        for table in tables:
            lines.append(f"entity \"{table.name}\" as {table.name} {{")
            for col in table.columns:
                pk_mark = " [PK]" if col.pk else ""
                fk_mark = f" [FK: {col.fk}]" if col.fk else ""
                lines.append(f"  * {col.name} : {col.dtype}{pk_mark}{fk_mark}")
            lines.append("}")
            lines.append("")
        for table in tables:
            for col in table.columns:
                if col.fk:
                    ref = col.fk.split(".")[0]
                    lines.append(f"{table.name}}}|--||{ref}")
        lines.append("@enduml")
        return "\n".join(lines)

    def _build_uc_links(self, tables: List[TableDef], domain_model) -> Dict[str, List[str]]:
        links = {}
        if hasattr(domain_model, 'use_cases'):
            for uc in domain_model.use_cases:
                uc_name_lower = uc.name.lower()
                linked_tables = [t.name for t in tables if any(
                    word in uc_name_lower for word in t.name.lower().replace("_", " ").split()
                )]
                if linked_tables:
                    links[uc.uc_id] = linked_tables
        return links
