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
            "raw": fed_v,
            "change_num": round(fed_chg, 2),
        },
        "m2_yoy": {
            "value": f"{m2_v:+.1f}%",
            "change": f"{m2_diff:+.1f}%p",
            "direction": "up" if m2_diff >= 0 else "down",
            "raw": m2_v,
            "change_num": round(m2_diff, 2),
        },
        "expected_eps": {
            "value": f"{int(round(eps_v)):,}",
            "change": f"{eps_chg:+.1f}%",
            "direction": "up" if eps_chg >= 0 else "down",
            "raw": eps_v,
            "change_num": round(eps_chg, 2),
        },
        "forward_per": {
            "value": f"{per_v:.2f}배",
            "change": f"{per_chg:+.1f}%",
            "direction": "up" if per_chg >= 0 else "down",
            "raw": per_v,
            "change_num": round(per_chg, 2),
        },
        "cnn_fear_greed": {
            "value": f"{fg_int} / 100",
            "change": fg_label,
            "direction": fg_dir,
            "raw": fg_int,
        },
        "treasury_10y": {
            "value": f"{us10_v:.2f}%",
            "change": f"{us10_diff:+.2f}%p",
            "direction": "up" if us10_diff > 0 else ("down" if us10_diff < 0 else "flat"),
            "raw": us10_v,
            "change_num": round(us10_diff, 2),
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
    """실제 DB 지표 기반 종합 투자 신호 점수(5대 팩터 가중합) 및 근거 동적 산출."""
    kpi = get_dashboard_kpi()
    fed_str = kpi["fed_net_liquidity"]["value"]
    fed_chg = kpi["fed_net_liquidity"]["change"]
    fed_chg_num = float(kpi["fed_net_liquidity"].get("change_num", 1.5))
    m2_raw = float(kpi["m2_yoy"].get("raw", 4.3))

    eps_str = kpi["expected_eps"]["value"]
    eps_chg = kpi["expected_eps"]["change"]
    eps_chg_num = float(kpi["expected_eps"].get("change_num", 2.1))

    per_str = kpi["forward_per"]["value"]
    per_raw = float(kpi["forward_per"].get("raw", 20.48))

    fg_int = int(kpi["cnn_fear_greed"].get("raw", 22))
    fg_lbl = kpi["cnn_fear_greed"]["change"]

    us10_str = kpi["treasury_10y"]["value"]
    us10_raw = float(kpi["treasury_10y"].get("raw", 4.90))
    us10_diff = float(kpi["treasury_10y"].get("change_num", -0.02))

    # 1. 유동성 점수 (30%)
    s_liq = min(95, max(35, int(round(70 + fed_chg_num * 5.0 + max(0.0, m2_raw) * 1.8))))
    liq_status = "good" if s_liq >= 65 else "warn"

    # 2. 기업실적 EPS 점수 (25%)
    s_eps = min(92, max(45, int(round(76 + max(-4.0, min(6.0, eps_chg_num)) * 2.0))))
    eps_status = "good" if s_eps >= 65 else "warn"

    # 3. 밸류에이션 Forward PER 역발상 점수 (20%)
    if per_raw <= 18.5:
        s_per, per_status = 90, "good"
    elif per_raw <= 21.5:
        s_per, per_status = 80, "good"
    elif per_raw <= 24.0:
        s_per, per_status = 65, "good"
    elif per_raw <= 27.0:
        s_per, per_status = 46, "warn"
    else:
        s_per, per_status = 30, "warn"

    # 4. 시장심리 CNN 공포탐욕 역발상 점수 (15%)
    if fg_int <= 25:
        s_fg, fg_status = 90, "good"
    elif fg_int <= 45:
        s_fg, fg_status = 76, "good"
    elif fg_int <= 55:
        s_fg, fg_status = 60, "good"
    elif fg_int <= 75:
        s_fg, fg_status = 42, "warn"
    else:
        s_fg, fg_status = 25, "warn"

    # 5. 국채금리 점수 (10%)
    if us10_diff <= 0 and us10_raw <= 4.6:
        s_rate, rate_status = 78, "good"
    elif us10_diff <= 0:
        s_rate, rate_status = 62, "good"
    else:
        s_rate, rate_status = 48, "warn"

    total_score = int(round(
        s_liq * 0.30
        + s_eps * 0.25
        + s_per * 0.20
        + s_fg * 0.15
        + s_rate * 0.10
    ))

    if total_score >= 70:
        rec = "TQQQ: 분할매수 유리"
    elif total_score >= 58:
        rec = "TQQQ/QQQ: 분할매수 · 비중유지"
    elif total_score >= 45:
        rec = "QQQ 중심 중립 운용"
    else:
        rec = "리스크 관리 · 현금비중 확대"

    bullets = [
        {"label": f"유동성: {fed_str} ({fed_chg})", "status": liq_status},
        {"label": f"실적(EPS): {eps_str} ({eps_chg})", "status": eps_status},
        {"label": f"밸류에이션: Forward PER {per_str}", "status": per_status},
        {"label": f"공포탐욕: {fg_lbl} ({fg_int}점)", "status": fg_status},
        {"label": f"금리: 10년물 {us10_str} ({kpi['treasury_10y']['change']})", "status": rate_status},
    ]

    details = [
        {"name": "유동성 (30%)",     "score": s_liq},
        {"name": "실적 EPS (25%)",   "score": s_eps},
        {"name": "밸류에이션 (20%)", "score": s_per},
        {"name": "시장심리 (15%)",   "score": s_fg},
        {"name": "국채금리 (10%)",   "score": s_rate},
    ]

    return {
        "score": total_score,
        "recommendation": rec,
        "bullets": bullets,
        "details": details,
        "asof_date": datetime.now().strftime("%Y-%m-%d"),
    }


def get_last_updated() -> str:
    return datetime.now().strftime("%Y-%m-%d")


get_kpi_data = get_dashboard_kpi
get_chart_data = get_nasdaq_chart_data
get_signal_score = get_investment_signal_score
