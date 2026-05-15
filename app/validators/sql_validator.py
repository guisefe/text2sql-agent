import re
from typing import Any

import sqlparse
from sqlparse.sql import Identifier, IdentifierList, Parenthesis
from sqlparse.tokens import Keyword, Literal, Name

FORBIDDEN_KEYWORDS = [
    "insert ", "update ", "delete ", "drop ", "alter ", "create ",
    "attach ", "pragma ", "vacuum ", "union ", "join ", "intersect ",
    "except ", "with ", "replace ", "execute ", "load_extension",
    "randomblob", ";",
]

ALLOWED_SQL_KEYWORDS = {
    "select", "from", "where", "and", "or", "not", "in", "is",
    "null", "order", "by", "limit", "asc", "desc", "group",
    "having", "as", "between", "like", "distinct", "case",
    "when", "then", "else", "end",
}

ALLOWED_FUNCTIONS = {
    "count", "sum", "avg", "min", "max",
    "round", "upper", "lower", "length",
    "coalesce", "ifnull", "abs", "trim", "date",
}

NUMERIC_LITERAL_RE = re.compile(r"^-?\d+(\.\d+)?$")
STRING_LITERAL_RE = re.compile(r"^'(?:''|[^'])*'$")


def is_safe_sql(sql: str, schema_metadata: dict[str, Any]) -> bool:
    if not sql or ";" in sql:
        return False

    lower = sql.lower()
    if any(m in lower for m in ("--", "/*", "*/")):
        return False
    if any(kw in lower for kw in FORBIDDEN_KEYWORDS):
        return False

    statements = [s for s in sqlparse.parse(sql) if s.tokens]
    if len(statements) != 1:
        return False

    stmt = statements[0]
    if stmt.get_type() != "SELECT":
        return False
    if _contains_subquery(stmt):
        return False

    tables = _extract_tables(stmt)
    if len(tables) != 1:
        return False

    allowed_tables = _allowed_tables(schema_metadata)
    if tables[0] not in allowed_tables:
        return False

    allowed_cols = _allowed_columns(schema_metadata, tables[0])
    return _identifiers_allowed(stmt, allowed_tables, allowed_cols)


def query_mentions_schema(user_query: str, schema_metadata: dict[str, Any]) -> bool:
    """Rejects queries that don't mention any table or column from the schema."""
    if not user_query:
        return False

    words = set(re.findall(r"\w+", user_query.lower()))
    terms: set[str] = set()

    for table in schema_metadata.get("tables", []):
        name = table.get("name", "").lower()
        if name:
            terms.add(name)
            if name.endswith("s"):
                terms.add(name[:-1])
        for col in table.get("columns", []):
            col_name = col.get("name", "").lower()
            if col_name:
                terms.add(col_name)

    return bool(words & terms)


def _contains_subquery(token: sqlparse.sql.Token) -> bool:
    if isinstance(token, Parenthesis) and "select" in str(token).lower():
        return True
    return hasattr(token, "tokens") and any(_contains_subquery(c) for c in token.tokens)


def _extract_tables(stmt: sqlparse.sql.Statement) -> list[str]:
    from_seen, tables = False, []
    for token in stmt.tokens:
        if token.is_keyword and token.normalized == "FROM":
            from_seen = True
            continue
        if not from_seen:
            continue
        if isinstance(token, IdentifierList):
            for ident in token.get_identifiers():
                if n := ident.get_real_name():
                    tables.append(n.lower())
            break
        if isinstance(token, Identifier):
            if n := token.get_real_name():
                tables.append(n.lower())
            break
        if token.ttype is Name:
            tables.append(token.value.lower())
            break
        if token.is_keyword:
            break
    return tables


def _allowed_tables(schema_metadata: dict[str, Any]) -> set[str]:
    return {t["name"].lower() for t in schema_metadata.get("tables", [])}


def _allowed_columns(schema_metadata: dict[str, Any], table: str) -> set[str]:
    for t in schema_metadata.get("tables", []):
        if t.get("name", "").lower() == table:
            return {c["name"].lower() for c in t.get("columns", [])}
    return set()


def _is_safe_literal(value: str) -> bool:
    if not STRING_LITERAL_RE.match(value):
        return False
    content = value[1:-1].replace("''", "'").lower()
    return not any(m in content for m in (";", "--", "/*", "*/"))


def _identifiers_allowed(
    stmt: sqlparse.sql.Statement,
    allowed_tables: set[str],
    allowed_cols: set[str],
) -> bool:
    for token in stmt.flatten():
        if token.ttype in Literal.String.Single:
            if not _is_safe_literal(token.value):
                return False
            continue
        if token.ttype in (Name, Keyword):
            for part in token.value.lower().split():
                if part in ALLOWED_SQL_KEYWORDS:
                    continue
                if part in ALLOWED_FUNCTIONS:
                    continue
                if part in allowed_tables:
                    continue
                if part in allowed_cols:
                    continue
                if part == "*":
                    continue
                if NUMERIC_LITERAL_RE.match(part):
                    continue
                return False
    return True
