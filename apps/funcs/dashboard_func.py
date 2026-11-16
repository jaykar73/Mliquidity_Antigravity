"""
Dashboard backend functions — KPI, 5Y chart data, composite signal score.
mybatis-mapper2sql + sqlite3 실시간 DB 데이터 연동.
"""
import json
from datetime import datetime
from utils.db_helper import fetch_all, fetch_one, load_mapper

load_mapper("sqls/dashboard.xml", force=True)


def get_dashboard_kpi() -> dict:
    """대시보드 6대 핵심 KPI 및 직전 관측치 대비 실제 변화율 조회."""
    rows = fetch_all(namespace="dashboard", sql_id="selectKPI", params={})
    by_code = {r["code"]: r for r in rows}

    def _vals(code: str, def_val: float, def_prev: float) -> tuple[float, float]:
        item = by_code.get(code, {})
        v = float(item.get("value") if item.get("value") is not None else def_val)
        p = float(item.get("prev_value") if item.get("prev_value") is not None else def_prev)
        return v, p

    fed_v, fed_p = _vals("FED_NET_LIQ", 5.81, 5.72)
    fed_chg = ((fed_v - fed_p) / fed_p * 100.0) if fed_p else 0.0

    m2_v, m2_p = _vals("M2_YOY", 4.3, 4.1)
    m2_diff = m2_v - m2_p

    eps_v, eps_p = _vals("FORWARD_EPS", 1378.0, 1350.0)
    eps_chg = ((eps_v - eps_p) / eps_p * 100.0) if eps_p else 0.0

    per_v, per_p = _vals("FORWARD_PER", 18.07, 18.55)
    per_chg = ((per_v - per_p) / per_p * 100.0) if per_p else 0.0

    fg_v, _ = _vals("CNN_FG", 22, 28)
    fg_int = int(round(fg_v))
    if fg_int <= 25:
        fg_label, fg_dir = "극단적 공포", "badge_red"
    elif fg_int <= 45:
        fg_label, fg_dir = "공포 구간", "down"
    elif fg_int <= 55:
        fg_label, fg_dir = "중립 구간", "flat"
    elif fg_int <= 75:
        fg_label, fg_dir = "탐욕 구간", "up"
    else:
        fg_label, fg_dir = "극단적 탐욕", "up"

    us10_v, us10_p = _vals("US10Y", 4.90, 4.94)
    us10_diff = us10_v - us10_p

    return {
        "fed_net_liquidity": {
            "value": f"${fed_v:.2f}조",
            "change": f"{fed_chg:+.1f}%",
            "direction": "up" if fed_chg >= 0 else "down",
        },
        "m2_yoy": {
            "value": f"{m2_v:+.1f}%",
            "change": f"{m2_diff:+.1f}%p",
            "direction": "up" if m2_diff >= 0 else "down",
        },
        "expected_eps": {
            "value": f"{int(round(eps_v)):,}",
            "change": f"{eps_chg:+.1f}%",
            "direction": "up" if eps_chg >= 0 else "down",
        },
        "forward_per": {
            "value": f"{per_v:.2f}배",
            "change": f"{per_chg:+.1f}%",
            "direction": "up" if per_chg >= 0 else "down",
        },
        "cnn_fear_greed": {
            "value": f"{fg_int} / 100",
            "change": fg_label,
            "direction": fg_dir,
        },
        "treasury_10y": {
            "value": f"{us10_v:.2f}%",
            "change": f"{us10_diff:+.2f}%p",
            "direction": "up" if us10_diff > 0 else ("down" if us10_diff < 0 else "flat"),
        },
    }


def get_nasdaq_chart_data(symbol: str = "NDX") -> dict:
    """나스닥100 지수, Fed 순유동성, Forward PER 5년 시계열 데이터 조회."""
    mp_rows = fetch_all(
        "SELECT trade_date, close FROM market_price WHERE symbol = :sym ORDER BY trade_date",
        {"sym": symbol},
    )
    liq_rows = fetch_all(
        """
        SELECT io.observation_date, io.value
        FROM indicator_observation io
        JOIN indicator_catalog ic ON ic.id = io.indicator_id
        WHERE ic.code = 'FED_NET_LIQ'
        ORDER BY io.observation_date
        """
    )
    per_rows = fetch_all(
        """
        SELECT io.observation_date, io.value
        FROM indicator_observation io
        JOIN indicator_catalog ic ON ic.id = io.indicator_id
        WHERE ic.code = 'FORWARD_PER'
        ORDER BY io.observation_date
        """
    )

    # 월별(YYYY-MM) 기준으로 정렬 및 매칭
    liq_by_ym = {r["observation_date"][:7]: float(r["value"]) for r in liq_rows}
    per_by_ym = {r["observation_date"][:7]: float(r["value"]) for r in per_rows}

    dates = []
    ndx = []
    liq = []
    per = []

    last_l = float(liq_rows[-1]["value"]) if liq_rows else 5.81
    last_p = float(per_rows[-1]["value"]) if per_rows else 18.07
    cur_l = float(liq_rows[0]["value"]) if liq_rows else 5.5
    cur_p = float(per_rows[0]["value"]) if per_rows else 20.0

    seen_ym = set()
    for r in mp_rows:
        ym = r["trade_date"][:7]
        if ym < "2021-01" or ym in seen_ym:
            continue
        seen_ym.add(ym)
        if ym in liq_by_ym:
            cur_l = liq_by_ym[ym]
        if ym in per_by_ym:
            cur_p = per_by_ym[ym]
        dates.append(ym)
        ndx.append(round(float(r["close"]), 1))
        liq.append(round(cur_l, 2))
        per.append(round(cur_p, 2))

    if liq:
        liq[-1] = round(last_l, 2)
    if per:
        per[-1] = round(last_p, 2)

    return {
        "dates": dates,
        "nasdaq100": ndx,
        "fed_liquidity": liq,
        "forward_per": per,
    }


def get_investment_signal_score() -> dict:
    """실제 DB 지표 기반 종합 투자 신호 점수 및 5대 근거 동적 산출."""
    kpi = get_dashboard_kpi()
    fed_str = kpi["fed_net_liquidity"]["value"]
    fed_chg = kpi["fed_net_liquidity"]["change"]
    eps_str = kpi["expected_eps"]["value"]
    eps_chg = kpi["expected_eps"]["change"]
    per_str = kpi["forward_per"]["value"]
    fg_str = kpi["cnn_fear_greed"]["value"].split("/")[0].strip()
    fg_lbl = kpi["cnn_fear_greed"]["change"]
    us10_str = kpi["treasury_10y"]["value"]

    row = fetch_one(namespace="dashboard", sql_id="selectSignalScore", params={})
    score = int(round(float(row.get("score", 72)))) if row else 72
    rec = (row.get("recommendation") if row else None) or "TQQQ: 분할매수 유리"

    bullets = [
        {"label": f"유동성: {fed_str} ({fed_chg})", "status": "good"},
        {"label": f"실적(EPS): {eps_str} ({eps_chg})", "status": "good"},
        {"label": f"밸류에이션: Forward PER {per_str}", "status": "good"},
        {"label": f"공포탐욕: {fg_lbl} ({fg_str}점)", "status": "good"},
        {"label": f"금리: 10년물 {us10_str}", "status": "warn"},
    ]

    return {
        "score": score,
        "recommendation": rec,
        "bullets": bullets,
        "asof_date": datetime.now().strftime("%Y-%m-%d"),
    }


def get_last_updated() -> str:
    return datetime.now().strftime("%Y-%m-%d")


get_kpi_data = get_dashboard_kpi
get_chart_data = get_nasdaq_chart_data
get_signal_score = get_investment_signal_score
