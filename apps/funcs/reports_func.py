"""
Reports & Alerts backend functions — 최근 시장 리포트, 투자 신호 알림, 규칙 관리.
mybatis-mapper2sql + sqlite3 연동.
"""
import json
from utils.db_helper import fetch_all, execute_query, load_mapper

load_mapper("sqls/reports.xml")


def get_reports(limit: int = 20) -> list[dict]:
    """최근 생성된 시장 분석 리포트 목록 조회."""
    rows = fetch_all(namespace="reports", sql_id="selectReports", params={"limit": limit})
    result = []
    for idx, r in enumerate(rows):
        features = {}
        if r.get("features_json"):
            try:
                features = json.loads(r["features_json"])
            except Exception:
                features = {}
        title = features.get("title") or r.get("recommendation") or "주간 시장 분석 리포트"
        summary = features.get("summary") or ""
        result.append({
            "id": idx + 1,
            "date": r.get("report_date", "2026-11-06 18:00"),
            "title": title,
            "summary": summary,
            "strategy_name": r.get("strategy_name", ""),
            "score": r.get("score", 72),
        })
    return result


def get_alerts() -> list[dict]:
    """투자 신호 알림 및 최근 발생 이력 조회."""
    rows = fetch_all(namespace="reports", sql_id="selectAlerts", params={})
    result = []
    for r in rows:
        cond = {}
        if r.get("condition_json"):
            try:
                cond = json.loads(r["condition_json"])
            except Exception:
                cond = {}
        result.append({
            "id": r["id"],
            "name": r["name"],
            "condition": cond.get("condition", ""),
            "color": cond.get("color", "green"),
            "channel": r.get("channel", "앱 알림"),
            "enabled": bool(r.get("enabled", 1)),
            "triggered_at": r.get("last_triggered") or "2026-11-06 10:10",
            "message": r.get("last_message") or "",
            "status": r.get("last_status") or "DELIVERED",
        })
    result.sort(key=lambda x: x["id"])
    return result


def get_alert_rules() -> list[dict]:
    return get_alerts()


def get_asset_signals() -> list[dict]:
    """실제 DB KPI 기반 4대 자산군(TQQQ, QQQ, 국채, 현금) 동적 투자 신호 산출."""
    from apps.funcs.dashboard_func import get_dashboard_kpi, get_investment_signal_score
    kpi = get_dashboard_kpi()
    sig = get_investment_signal_score()
    tqqq_score = sig.get("score", 72)
    fed_str = kpi["fed_net_liquidity"]["value"]
    fed_chg = kpi["fed_net_liquidity"]["change"]
    per_str = kpi["forward_per"]["value"]
    fg_str = kpi["cnn_fear_greed"]["value"].split("/")[0].strip()
    fg_lbl = kpi["cnn_fear_greed"]["change"]
    eps_str = kpi["expected_eps"]["value"]
    eps_chg = kpi["expected_eps"]["change"]
    us10_str = kpi["treasury_10y"]["value"]
    us10_chg = kpi["treasury_10y"]["change"]

    tqqq_sig = "분할매수" if tqqq_score >= 65 else ("비중유지" if tqqq_score >= 50 else "비중축소")
    qqq_score = min(95, max(50, tqqq_score - 3))
    bond_score = 62 if float(kpi["treasury_10y"].get("raw", 4.9)) >= 4.5 else 52
    cash_score = max(25, 100 - tqqq_score)

    return [
        {
            "asset": "TQQQ",
            "signal": tqqq_sig,
            "score": tqqq_score,
            "reason": f"유동성 {fed_str}({fed_chg}), Fwd PER {per_str}, 공포탐욕 {fg_str}점({fg_lbl})",
        },
        {
            "asset": "QQQ",
            "signal": "매수/보유" if qqq_score >= 60 else "중립보유",
            "score": qqq_score,
            "reason": f"나스닥100 12M 예상 EPS {eps_str} ({eps_chg}) 이익 체력 견조",
        },
        {
            "asset": "국채",
            "signal": "분할매수/보유" if bond_score >= 60 else "보유",
            "score": bond_score,
            "reason": f"미국채 10Y 스팟 {us10_str} ({us10_chg}) 고금리 캐리 매력",
        },
        {
            "asset": "현금",
            "signal": "분할집행" if tqqq_score >= 65 else "대기유지",
            "score": cash_score,
            "reason": f"{fg_lbl} 구간({fg_str}점) 조정 시 분할매수 재원 활용",
        },
    ]


def create_report(asof_date: str, strategy_id: int, score: float,
                  recommendation: str, features: dict | None = None,
                  data_quality: str = "GOOD") -> None:
    features_json = json.dumps(features or {}, ensure_ascii=False)
    execute_query(namespace="reports", sql_id="insertReport", params={
        "asof_date": asof_date,
        "strategy_id": strategy_id,
        "score": score,
        "recommendation": recommendation,
        "features_json": features_json,
        "data_quality": data_quality,
    })


def save_alert(name: str, condition: dict, channel: str = "앱 알림",
               enabled: bool = True, alert_id: int | None = None) -> None:
    condition_json = json.dumps(condition, ensure_ascii=False)
    if alert_id:
        execute_query(namespace="reports", sql_id="updateAlert", params={
            "id": alert_id,
            "name": name,
            "condition_json": condition_json,
            "channel": channel,
            "enabled": 1 if enabled else 0,
        })
    else:
        execute_query(namespace="reports", sql_id="insertAlert", params={
            "name": name,
            "condition_json": condition_json,
            "channel": channel,
            "enabled": 1 if enabled else 0,
        })
