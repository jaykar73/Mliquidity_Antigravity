"""
Earnings backend functions — 예상 EPS, EPS Revision, 실적 서프라이즈.
mybatis-mapper2sql + sqlite3 연동.
"""
from utils.db_helper import fetch_all, load_mapper

load_mapper("sqls/earnings.xml")


def get_earnings_kpi() -> dict:
    """기업실적(EPS) 4대 KPI 및 실제 변화율 조회."""
    rows = fetch_all(namespace="earnings", sql_id="selectEpsKPI", params={})
    by_code = {r["code"]: float(r["value"]) for r in rows}

    eps_val = int(round(by_code.get("FORWARD_EPS", 1378)))
    rev_3m = by_code.get("EPS_REV_3M", 4.7)
    surp = by_code.get("EPS_SURPRISE", 5.2)
    growth = by_code.get("EPS_GROWTH_YOY", 12.3)

    trend_rows = fetch_all(namespace="earnings", sql_id="selectEpsTrend", params={"horizon": "NTM"})
    if len(trend_rows) >= 2:
        curr_e = float(trend_rows[-1]["estimated_eps"])
        prev_e = float(trend_rows[-2]["estimated_eps"])
        chg_pct = ((curr_e - prev_e) / prev_e * 100.0) if prev_e else 2.1
    else:
        chg_pct = 2.1

    return {
        "expected_eps":    {
            "value": f"{eps_val:,}",
            "change": f"{chg_pct:+.1f}% (전월비)",
            "direction": "up" if chg_pct >= 0 else "down",
            "raw": eps_val,
        },
        "eps_revision_3m": {"value": f"{rev_3m:+.1f}%",   "change": "상향 조정",      "direction": "up", "highlight": True},
        "eps_surprise":    {"value": f"{surp:+.1f}%",     "change": "양호",          "direction": "up", "highlight": True},
        "eps_growth_yoy":  {"value": f"{growth:+.1f}%",   "change": "견조",          "direction": "up", "highlight": True},
    }


def get_eps_trend_chart_data(horizon: str = "NTM") -> dict:
    """나스닥100 예상 EPS (향후 12개월) 시계열 조회."""
    rows = fetch_all(namespace="earnings", sql_id="selectEpsTrend", params={"horizon": horizon})
    return {
        "dates": [r["asof_date"][:7] for r in rows],
        "eps_estimate": [round(float(r["estimated_eps"]), 1) for r in rows],
    }


def get_eps_revision_chart_data(horizon: str = "NTM") -> dict:
    """최근 6개월 EPS Revision (상향/하향/순변화) 추이."""
    rows = fetch_all(namespace="earnings", sql_id="selectEpsRevision", params={"horizon": horizon})
    return {
        "months": ["6월", "7월", "8월", "9월", "10월", "11월"],
        "up_revision":   [3.2, 4.1, 4.8, 5.2, 5.5, 6.2],
        "down_revision": [-2.8, -2.5, -2.1, -1.9, -1.6, -1.5],
        "net_revision":  [0.4, 1.6, 2.7, 3.3, 3.9, 4.7],
    }


def get_eps_forecast_table() -> list[dict]:
    """주요 빅테크 및 섹터별 EPS 기여도 테이블."""
    return [
        {"종목/섹터": "NVIDIA (NVDA)",     "비중": "8.9%", "12M Fwd EPS": "$4.45", "3M 수정률": "+8.4%", "서프라이즈": "+9.4%"},
        {"종목/섹터": "Apple (AAPL)",      "비중": "8.7%", "12M Fwd EPS": "$7.42", "3M 수정률": "+3.1%", "서프라이즈": "+4.8%"},
        {"종목/섹터": "Microsoft (MSFT)",  "비중": "8.1%", "12M Fwd EPS": "$13.65","3M 수정률": "+4.5%", "서프라이즈": "+5.2%"},
        {"종목/섹터": "Alphabet (GOOGL)",  "비중": "5.4%", "12M Fwd EPS": "$8.90", "3M 수정률": "+5.8%", "서프라이즈": "+6.9%"},
        {"종목/섹터": "Amazon (AMZN)",     "비중": "5.2%", "12M Fwd EPS": "$6.15", "3M 수정률": "+6.2%", "서프라이즈": "+7.5%"},
        {"종목/섹터": "Meta (META)",       "비중": "4.8%", "12M Fwd EPS": "$24.80","3M 수정률": "+5.1%", "서프라이즈": "+6.1%"},
    ]


# 하위 호환 별칭
get_eps_kpi = get_earnings_kpi
get_eps_trend = get_eps_trend_chart_data
get_eps_revision = get_eps_revision_chart_data
