"""
Liquidity backend functions — Fed 순유동성, M2, MMF, 지급준비금.
mybatis-mapper2sql + sqlite3 실시간 DB 연동.
"""
from utils.db_helper import fetch_all, load_mapper

load_mapper("sqls/liquidity.xml", force=True)


def get_liquidity_kpi() -> dict:
    """시장 유동성 4대 KPI 카드 데이터 및 실제 변화율 조회."""
    rows = fetch_all(namespace="liquidity", sql_id="selectLiquidityKPI", params={})
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

    mmf_v, mmf_p = _vals("MMMFFAQ027S", 6.74, 6.78)
    mmf_chg = ((mmf_v - mmf_p) / mmf_p * 100.0) if mmf_p else 0.0

    res_v, res_p = _vals("WRESBAL", 3.33, 3.30)
    res_chg = ((res_v - res_p) / res_p * 100.0) if res_p else 0.0

    return {
        "fed_net_liquidity": {
            "value": f"${fed_v:.2f}조",
            "change": f"{fed_chg:+.2f}% (최근)",
            "direction": "up" if fed_chg >= 0 else "down",
        },
        "m2_yoy": {
            "value": f"{m2_v:+.1f}%",
            "change": f"{m2_diff:+.2f}%p",
            "direction": "up" if m2_diff >= 0 else "down",
            "highlight": True,
        },
        "mmf_balance": {
            "value": f"${mmf_v:.2f}조",
            "change": f"{mmf_chg:+.2f}%",
            "direction": "up" if mmf_chg >= 0 else "down",
        },
        "reserves": {
            "value": f"${res_v:.2f}조",
            "change": f"{res_chg:+.2f}%",
            "direction": "up" if res_chg >= 0 else "down",
        },
    }


def get_fed_liquidity_chart_data() -> dict:
    """Fed 순유동성 및 구성요소 시계열 데이터 조회 (월별 집계로 주간/월간 시리즈 정합)."""
    rows = fetch_all(namespace="liquidity", sql_id="selectFedLiquidity", params={})
    by_ym: dict[str, dict] = {}
    for r in rows:
        ym = r["observation_date"][:7]
        if ym not in by_ym:
            by_ym[ym] = {}
        for k in ("net_liquidity", "fed_balance", "tga", "rrp", "m2", "m2_yoy", "mmf", "reserves"):
            val = float(r.get(k) or 0.0)
            if val != 0.0:
                by_ym[ym][k] = val

    dates = sorted(by_ym.keys())
    # carry-forward 결측 보정
    last_vals = {
        "net_liquidity": 5.8,
        "fed_balance": 7.0,
        "tga": 0.7,
        "rrp": 0.4,
        "m2": 21.0,
        "m2_yoy": 4.0,
        "mmf": 6.5,
        "reserves": 3.3,
    }
    out = {k: [] for k in last_vals}
    for d in dates:
        item = by_ym[d]
        for k in last_vals:
            if k in item:
                last_vals[k] = item[k]
            out[k].append(round(last_vals[k], 2))

    return {
        "dates": dates,
        "net_liquidity": out["net_liquidity"],
        "fed_assets": out["fed_balance"],
        "tga": out["tga"],
        "rrp": out["rrp"],
        "m2": out["m2"],
        "m2_yoy": out["m2_yoy"],
        "mmf": out["mmf"],
        "reserves": out["reserves"],
    }


def get_m2_chart_data() -> dict:
    data = get_fed_liquidity_chart_data()
    return {"dates": data["dates"], "m2": data["m2"], "m2_yoy": data["m2_yoy"]}


def get_mmf_chart_data() -> dict:
    data = get_fed_liquidity_chart_data()
    return {"dates": data["dates"], "mmf_total": data["mmf"], "reserves": data["reserves"]}


def get_liquidity_summary_table() -> list[dict]:
    """DB 실제 관측치 기반 유동성 요약 테이블 조회."""
    kpi = get_liquidity_kpi()
    items = [
        ("Fed 순유동성", kpi["fed_net_liquidity"]),
        ("M2 증가율",    kpi["m2_yoy"]),
        ("MMF 잔액",     kpi["mmf_balance"]),
        ("지급준비금",   kpi["reserves"]),
    ]
    result = []
    for label, d in items:
        is_up = d["direction"] == "up"
        arrow = "▲" if is_up else "▼"
        chg_clean = d["change"].replace("(최근)", "").strip()
        result.append({
            "지표": label,
            "현재값": d["value"],
            "변화(주간)": f"{arrow} {chg_clean}",
            "direction": d["direction"],
        })
    return result


get_fed_liquidity_chart = get_fed_liquidity_chart_data
get_liquidity_summary = get_liquidity_summary_table
