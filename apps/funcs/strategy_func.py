"""
Strategy backend functions — 투자 전략 목록, 매수·매도 규칙, 추천 포트폴리오 비중.
mybatis-mapper2sql + sqlite3 연동.
"""
import json
from utils.db_helper import fetch_all, fetch_one, execute_query, load_mapper

load_mapper("sqls/strategy.xml")


def get_strategies() -> list[dict]:
    """DB에 저장된 투자 전략 목록 조회."""
    rows = fetch_all(namespace="strategy", sql_id="selectStrategies", params={})
    result = []
    for r in rows:
        params = {}
        if r.get("params_json"):
            try:
                params = json.loads(r["params_json"])
            except Exception:
                params = {}
        result.append({
            "id": r["id"],
            "name": r["name"],
            "version": r.get("version", "1.0"),
            "desc": params.get("description", ""),
            "profile": params.get("profile", "성장형 (TQQQ 중심)"),
            "allocation": params.get("allocation", []),
            "rules": params.get("rules", []),
            "enabled": bool(r.get("enabled", 1)),
            "latest_score": r.get("latest_score") or 72,
            "latest_recommendation": r.get("latest_recommendation") or "TQQQ: 분할매수 유리",
        })
    # id 오름차순 정렬
    result.sort(key=lambda x: x["id"])
    return result


def get_strategy_detail(strategy_id: int = 1) -> dict:
    """단일 전략 상세 조회."""
    row = fetch_one(namespace="strategy", sql_id="selectStrategyDetail", params={"strategy_id": strategy_id})
    if not row:
        strats = get_strategies()
        return strats[0] if strats else {}
    params = {}
    if row.get("params_json"):
        try:
            params = json.loads(row["params_json"])
        except Exception:
            params = {}
    return {
        "id": row["id"],
        "name": row["name"],
        "version": row.get("version", "1.0"),
        "desc": params.get("description", ""),
        "profile": params.get("profile", "성장형 (TQQQ 중심)"),
        "allocation": params.get("allocation", []),
        "rules": params.get("rules", []),
    }


def get_trade_rules(strategy_id: int = 1) -> list[dict]:
    detail = get_strategy_detail(strategy_id)
    return detail.get("rules", [])


def get_portfolio_allocation(strategy_id: int = 1) -> list[dict]:
    detail = get_strategy_detail(strategy_id)
    return detail.get("allocation", [])


def get_signal_score() -> dict:
    return {
        "score": 72,
        "label": "TQQQ: 분할매수 유리",
        "details": [
            {"name": "유동성 (30%)",     "score": 78},
            {"name": "실적 EPS (25%)",   "score": 82},
            {"name": "밸류에이션 (20%)", "score": 80},
            {"name": "시장심리 (15%)",   "score": 68},
            {"name": "국채금리 (10%)",   "score": 52},
        ],
    }


def save_strategy(name: str, version: str, params: dict, enabled: bool = True, strategy_id: int | None = None) -> None:
    params_json = json.dumps(params, ensure_ascii=False)
    if strategy_id:
        execute_query(namespace="strategy", sql_id="updateStrategy", params={
            "id": strategy_id,
            "name": name,
            "version": version,
            "params_json": params_json,
            "enabled": 1 if enabled else 0,
        })
    else:
        execute_query(namespace="strategy", sql_id="insertStrategy", params={
            "name": name,
            "version": version,
            "params_json": params_json,
            "enabled": 1 if enabled else 0,
        })
