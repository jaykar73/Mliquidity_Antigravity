"""
TQQQ Lab - DB Helper
mybatis-mapper2sql 기반 SQL XML 로드 + sqlite3 편의 유틸리티
"""
import os
import re
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Union

import mybatis_mapper2sql
import mybatis_mapper2sql.params

from conf.config import DB_PATH, SQL_DIR

# ── sqlite3 named parameter(:name) 호환 패치 ─────────────────
def _sqlite_replace_params(param: dict) -> None:
    """mybatis #{param} 구문을 sqlite3 :param 구문으로 변환."""
    param['mock_value'] = ':' + param['name']

mybatis_mapper2sql.params.replace_params = _sqlite_replace_params

# ── 매퍼 캐시: {namespace: {stmt_id: sql}} ───────────────────
_mapper_cache: Dict[str, Dict[str, str]] = {}


def _ensure_db_dir() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """sqlite3 커넥션 반환 (WAL 모드, Row 팩토리)."""
    _ensure_db_dir()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def connection(db_path: str = DB_PATH):
    """Context-managed 커넥션."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _resolve_xml_path(xml_filename: str) -> Tuple[str, str]:
    """xml 파일 경로와 namespace 이름을 반환."""
    clean_name = os.path.basename(xml_filename)
    if not clean_name.endswith(".xml"):
        clean_name += ".xml"
    namespace = os.path.splitext(clean_name)[0]
    xml_path = os.path.join(SQL_DIR, clean_name)
    return namespace, xml_path


def load_mapper(xml_filename: str, force: bool = False) -> Dict[str, str]:
    """
    sqls/ 폴더에 있는 XML 매퍼 파일을 mybatis-mapper2sql로 로드하고
    {statement_id: sql_string} 딕셔너리로 반환 및 캐시한다.
    """
    namespace, xml_path = _resolve_xml_path(xml_filename)
    if not force and namespace in _mapper_cache:
        return _mapper_cache[namespace]

    if not os.path.isfile(xml_path):
        raise FileNotFoundError(f"SQL XML not found: {xml_path}")

    mapper, _ = mybatis_mapper2sql.create_mapper(xml=xml_path)
    stmt_list = mybatis_mapper2sql.get_statement(mapper, result_type="list")

    statements: Dict[str, str] = {}
    for item in stmt_list:
        for stmt_id, sql_text in item.items():
            # 혹시 남아있는 #{param} 패턴이 있다면 :param 으로 치환
            converted = re.sub(r"#\{(\w+)[^}]*\}", r":\1", sql_text)
            statements[stmt_id] = converted.strip()

    _mapper_cache[namespace] = statements
    return statements


def get_sql(namespace_or_file: str, stmt_id: str) -> str:
    """매퍼(namespace 또는 파일명)에서 statement ID로 SQL 문자열 반환."""
    stmts = load_mapper(namespace_or_file)
    if stmt_id not in stmts:
        raise KeyError(f"Statement '{stmt_id}' not found in '{namespace_or_file}'")
    return stmts[stmt_id]


def _resolve_sql_and_params(
    sql_or_none: Optional[str],
    params: Optional[Union[Tuple, Dict]],
    namespace: Optional[str],
    sql_id: Optional[str],
) -> Tuple[str, Union[Tuple, Dict]]:
    """직접 전달된 SQL 또는 (namespace, sql_id) 매퍼 호출을 모두 지원."""
    if namespace and sql_id:
        sql = get_sql(namespace, sql_id)
    elif sql_or_none:
        sql = sql_or_none
    else:
        raise ValueError("Either sql string or (namespace, sql_id) must be provided.")
    return sql, (params if params is not None else {})


# ── 쿼리 실행 편의 함수 ───────────────────────────────────────
def execute_query(
    sql: Optional[str] = None,
    params: Optional[Union[Tuple, Dict]] = None,
    db_path: str = DB_PATH,
    *,
    namespace: Optional[str] = None,
    sql_id: Optional[str] = None,
) -> int:
    """INSERT / UPDATE / DELETE 실행, 영향받은 row 수 반환."""
    resolved_sql, resolved_params = _resolve_sql_and_params(sql, params, namespace, sql_id)
    with connection(db_path) as conn:
        cur = conn.execute(resolved_sql, resolved_params)
        return cur.rowcount


def fetch_all(
    sql: Optional[str] = None,
    params: Optional[Union[Tuple, Dict]] = None,
    db_path: str = DB_PATH,
    *,
    namespace: Optional[str] = None,
    sql_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """SELECT 실행 → list[dict] 반환."""
    resolved_sql, resolved_params = _resolve_sql_and_params(sql, params, namespace, sql_id)
    with connection(db_path) as conn:
        cur = conn.execute(resolved_sql, resolved_params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]


def fetch_one(
    sql: Optional[str] = None,
    params: Optional[Union[Tuple, Dict]] = None,
    db_path: str = DB_PATH,
    *,
    namespace: Optional[str] = None,
    sql_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """SELECT 실행 → 단건 dict 또는 None."""
    resolved_sql, resolved_params = _resolve_sql_and_params(sql, params, namespace, sql_id)
    with connection(db_path) as conn:
        cur = conn.execute(resolved_sql, resolved_params)
        row = cur.fetchone()
        return dict(row) if row else None


def execute_script(sql_script: str, db_path: str = DB_PATH) -> None:
    """여러 문장(세미콜론 구분) 일괄 실행."""
    with connection(db_path) as conn:
        conn.executescript(sql_script)
