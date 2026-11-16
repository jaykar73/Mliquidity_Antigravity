"""
Treasury backend functions — 5년·10년·30년 스팟 금리, 스프레드, 수익률 곡선.
mybatis-mapper2sql + sqlite3 연동.
"""
from utils.db_helper import fetch_all, load_mapper

load_mapper("sqls/treasury.xml")


def get_treasury_kpi() -> dict:
    """국채 금리 5대 KPI (5Y, 10Y, 30Y, 10Y-5Y, 30Y-10Y) 조회."""
    rows = fetch_all(namespace="treasury", sql_id="selectTreasuryKPI", params={})
    by_code = {r["code"]: r for r in rows}

    def _get(code: str, def_val: float, def_prev: float):
        item = by_code.get(code, {})
        val = float(item.get("value", def_val))
        prev = float(item.get("prev_value") or def_prev)
        return val, round(val - prev, 2)

    r5, c5 = _get("US05Y", 4.65, 4.68)
    r10, c10 = _get("US10Y", 4.90, 4.94)
    r30, c30 = _get("US30Y", 5.37, 5.42)
    s10_5 = round(r10 - r5, 2)
    s30_10 = round(r30 - r10, 2)

    return {
        "5y":     {"rate": r5,    "change": c5},
        "10y":    {"rate": r10,   "change": c10},
        "30y":    {"rate": r30,   "change": c30},
        "10y_5y": {"spread": s10_5},
        "30y_10y":{"spread": s30_10},
    }


def get_treasury_history() -> dict:
    """5년/10년/30년 국채 스팟 금리 5년 시계열 조회."""
    rows = fetch_all(namespace="treasury", sql_id="selectTreasuryTrend", params={})
    pivoted: dict[str, dict] = {}
    for r in rows:
        dt = r["observation_date"][:7]
        if dt not in pivoted:
            pivoted[dt] = {}
        pivoted[dt][r["code"]] = round(float(r["value"]), 2)

    dates = sorted(pivoted.keys())
    return {
        "dates": dates,
        "5y":  [pivoted[d].get("US05Y", 4.5) for d in dates],
        "10y": [pivoted[d].get("US10Y", 4.8) for d in dates],
        "30y": [pivoted[d].get("US30Y", 5.2) for d in dates],
    }


def get_treasury_spread() -> dict:
    """10Y-5Y 및 30Y-10Y 금리 스프레드 시계열 조회."""
    rows = fetch_all(namespace="treasury", sql_id="selectSpreadData", params={})
    pivoted: dict[str, dict] = {}
    for r in rows:
        dt = r["observation_date"][:7]
        if dt not in pivoted:
            pivoted[dt] = {}
        pivoted[dt][r["code"]] = round(float(r["value"]), 2)

    dates = sorted(pivoted.keys())
    return {
        "dates": dates,
        "10y_5y":  [pivoted[d].get("US10Y_US05Y_SPREAD", 0.25) for d in dates],
        "30y_10y": [pivoted[d].get("US30Y_US10Y_SPREAD", 0.47) for d in dates],
    }


def get_yield_curve() -> dict:
    """현재 스팟 금리 수익률 곡선 조회."""
    rows = fetch_all(namespace="treasury", sql_id="selectYieldCurve", params={})
    by_code = {r["code"]: round(float(r["value"]), 2) for r in rows}
    return {
        "maturities": ["3M", "1Y", "2Y", "5Y", "10Y", "30Y"],
        "rates": [
            by_code.get("US3M", 4.35),
            by_code.get("US1Y", 4.42),
            by_code.get("US02Y", 4.52),
            by_code.get("US05Y", 4.65),
            by_code.get("US10Y", 4.90),
            by_code.get("US30Y", 5.37),
        ],
    }


# 하위 호환 별칭
get_treasury_trend = get_treasury_history
get_spread_data = get_treasury_spread
