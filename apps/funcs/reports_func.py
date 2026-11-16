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
    return [
        {"asset": "TQQQ", "signal": "분할매수", "score": 72, "reason": "유동성 +1.5%, PER 18.07배, 공포탐욕 22"},
        {"asset": "QQQ",  "signal": "매수/보유", "score": 68, "reason": "예상 EPS 1,378 (+2.1%) 견조한 성장"},
        {"asset": "국채", "signal": "보유",     "score": 55, "reason": "10Y 스팟 4.90% (-0.04%p) 안정화"},
        {"asset": "현금", "signal": "일부집행", "score": 40, "reason": "극단적 공포 구간 분할매수 재원 활용"},
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
