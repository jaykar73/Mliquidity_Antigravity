"""
TQQQ Lab — 전 화면 실시간 데이터 수집기 (Live Data Synchronizer)
FRED 공식 CSV + Yahoo Finance Chart/Quote + Finviz + CNN Fear & Greed API 연동
"""
import asyncio
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

from utils.db_helper import connection

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}

CNN_HEADERS = {
    **HEADERS,
    "Referer": "https://www.cnn.com/markets/fear-and-greed",
    "Origin": "https://www.cnn.com",
}


def _parse_fred_csv(csv_text: str, start_date: str = "2019-01-01") -> List[Tuple[str, float]]:
    """FRED CSV 응답을 [(YYYY-MM-DD, float_val), ...] 리스트로 파싱."""
    out: List[Tuple[str, float]] = []
    lines = csv_text.splitlines()
    for line in lines[1:]:
        parts = line.strip().split(",")
        if len(parts) >= 2:
            dt, val_s = parts[0].strip(), parts[1].strip()
            if dt >= start_date and val_s not in ("", ".", "ND"):
                try:
                    out.append((dt, float(val_s)))
                except ValueError:
                    continue
    return out


def _to_trillions(val: float, series_id: str) -> float:
    """FRED 통화/유동성 시리즈를 조 달러($T) 단위로 정규화."""
    if series_id in ("WALCL", "WTREGEN", "WDTGAL", "WRESBAL"):
        # Millions of Dollars -> Trillions
        if val > 50_000:
            return round(val / 1_000_000.0, 4)
        # Billions -> Trillions
        return round(val / 1_000.0, 4)
    if series_id in ("RRPONTSYD", "M2SL", "WRMFNS"):
        # Billions of Dollars -> Trillions
        if val > 50_000:
            return round(val / 1_000_000.0, 4)
        return round(val / 1_000.0, 4)
    if series_id == "MMMFFAQ027S":
        # Millions of Dollars -> Trillions
        if val > 50_000:
            return round(val / 1_000_000.0, 4)
        return round(val / 1_000.0, 4)
    return round(val, 4)


_FRED_SEM = asyncio.Semaphore(5)


async def _fetch_fred_series(client: httpx.AsyncClient, series_id: str, start_date: str = "2019-01-01") -> List[Tuple[str, float]]:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}&cosd={start_date}"
    async with _FRED_SEM:
        try:
            r = await client.get(url, timeout=httpx.Timeout(4.0, connect=2.0))
            if r.status_code == 200 and "DATE" in r.text[:60].upper():
                return _parse_fred_csv(r.text, start_date)
        except Exception:
            pass
    return []


async def _fetch_yahoo_chart(client: httpx.AsyncClient, symbol: str, range_str: str = "5y", interval: str = "1wk") -> List[Tuple[str, float, float, float, float, int]]:
    """Yahoo Finance v8 chart API를 통해 실제 OHLCV 시계열 조회."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={range_str}&interval={interval}"
    try:
        r = await client.get(url, timeout=10.0)
        if r.status_code == 200:
            data = r.json()
            res = data.get("chart", {}).get("result", [])
            if res:
                item = res[0]
                timestamps = item.get("timestamp", [])
                quote = item.get("indicators", {}).get("quote", [{}])[0]
                opens = quote.get("open", [])
                highs = quote.get("high", [])
                lows = quote.get("low", [])
                closes = quote.get("close", [])
                vols = quote.get("volume", [])
                rows = []
                for i, ts in enumerate(timestamps):
                    c = closes[i] if i < len(closes) else None
                    if c is None:
                        continue
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
                    o = opens[i] if i < len(opens) and opens[i] is not None else c
                    h = highs[i] if i < len(highs) and highs[i] is not None else c
                    l = lows[i] if i < len(lows) and lows[i] is not None else c
                    v = int(vols[i]) if i < len(vols) and vols[i] is not None else 0
                    rows.append((dt, round(float(o), 2), round(float(h), 2), round(float(l), 2), round(float(c), 2), v))
                return rows
    except Exception:
        pass
    return []


async def _fetch_cnn_fear_greed(client: httpx.AsyncClient) -> dict | None:
    """CNN Fear & Greed 공식 Dataviz JSON 수집."""
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    try:
        r = await client.get(url, headers=CNN_HEADERS, timeout=10.0)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


async def _fetch_finviz_metrics(client: httpx.AsyncClient, ticker: str) -> dict:
    """Finviz에서 종목별 Forward P/E, P/E, EPS next Y, Price 등 추출."""
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    out = {"ticker": ticker}
    try:
        r = await client.get(url, timeout=8.0)
        if r.status_code == 200:
            html = r.text
            for key, label in [
                ("forward_pe", "Forward P/E"),
                ("pe", "P/E"),
                ("eps_next_y", "EPS next Y"),
                ("eps_this_y", "EPS this Y"),
                ("price", "Price"),
            ]:
                m = re.search(rf">{re.escape(label)}<.*?><b>([^<]+)</b>", html, re.S)
                if m:
                    raw = m.group(1).replace("%", "").replace(",", "").strip()
                    try:
                        out[key] = float(raw)
                    except ValueError:
                        out[key] = raw
    except Exception:
        pass
    return out


async def sync_all_live_data_async() -> dict:
    """
    모든 화면(FRED 유동성, 국채금리, 시장주가, Forward PER, EPS, CNN 공포탐욕)의
    실제 최신 데이터를 병렬로 수집하여 SQLite DB에 적재한다.
    """
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary_log: List[str] = []
    total_rows_written = 0

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, verify=False) as client:
        # 1. 병렬 수집 실행
        fred_tasks = {
            "WALCL": _fetch_fred_series(client, "WALCL", "2020-01-01"),
            "WTREGEN": _fetch_fred_series(client, "WTREGEN", "2020-01-01"),
            "RRPONTSYD": _fetch_fred_series(client, "RRPONTSYD", "2020-01-01"),
            "M2SL": _fetch_fred_series(client, "M2SL", "2019-01-01"),
            "WRESBAL": _fetch_fred_series(client, "WRESBAL", "2020-01-01"),
            "MMMFFAQ027S": _fetch_fred_series(client, "MMMFFAQ027S", "2019-01-01"),
            "US3M": _fetch_fred_series(client, "DGS3MO", "2020-01-01"),
            "US1Y": _fetch_fred_series(client, "DGS1", "2020-01-01"),
            "US02Y": _fetch_fred_series(client, "DGS2", "2020-01-01"),
            "US05Y": _fetch_fred_series(client, "DGS5", "2020-01-01"),
            "US10Y": _fetch_fred_series(client, "DGS10", "2020-01-01"),
            "US30Y": _fetch_fred_series(client, "DGS30", "2020-01-01"),
            "DFF": _fetch_fred_series(client, "DFF", "2020-01-01"),
            "NASDAQ100": _fetch_fred_series(client, "NASDAQ100", "2020-01-01"),
        }

        yahoo_tasks = {
            "Y_NDX": _fetch_yahoo_chart(client, "%5ENDX", "5y", "1mo"),
            "Y_QQQ": _fetch_yahoo_chart(client, "QQQ", "5y", "1mo"),
            "Y_TQQQ": _fetch_yahoo_chart(client, "TQQQ", "5y", "1mo"),
            "Y_US3M": _fetch_yahoo_chart(client, "%5EIRX", "5y", "1mo"),
            "Y_US05Y": _fetch_yahoo_chart(client, "%5EFVX", "5y", "1mo"),
            "Y_US10Y": _fetch_yahoo_chart(client, "%5ETNX", "5y", "1mo"),
            "Y_US30Y": _fetch_yahoo_chart(client, "%5ETYX", "5y", "1mo"),
        }

        finviz_tickers = ["QQQ", "NVDA", "AAPL", "MSFT", "AMZN", "META", "GOOGL"]
        finviz_tasks = {f"FV_{t}": _fetch_finviz_metrics(client, t) for t in finviz_tickers}
        cnn_task = _fetch_cnn_fear_greed(client)

        all_keys = list(fred_tasks.keys()) + list(yahoo_tasks.keys()) + list(finviz_tasks.keys()) + ["CNN"]
        all_coros = (
            list(fred_tasks.values())
            + list(yahoo_tasks.values())
            + list(finviz_tasks.values())
            + [cnn_task]
        )
        results = await asyncio.gather(*all_coros, return_exceptions=True)

        res_map = {}
        for k, v in zip(all_keys, results):
            res_map[k] = None if isinstance(v, Exception) else v

    # 2. DB 적재
    with connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, code FROM indicator_catalog")
        code_to_id = {row["code"]: row["id"] for row in cur.fetchall()}

        def upsert_obs(code: str, dt_str: str, val: float, src_url: str):
            nonlocal total_rows_written
            if code not in code_to_id:
                return
            cur.execute(
                """
                INSERT OR REPLACE INTO indicator_observation
                    (indicator_id, observation_date, published_at, value, vintage, source_url, collected_at)
                VALUES (?, ?, ?, ?, 'latest', ?, datetime('now', 'localtime'))
                """,
                (code_to_id[code], dt_str, dt_str, round(float(val), 4), src_url),
            )
            total_rows_written += 1

        def mark_live(code: str, provider: str):
            cur.execute(
                "UPDATE indicator_catalog SET provider = ?, license_status = 'LIVE' WHERE code = ?",
                (provider, code),
            )

        # ── A. FRED 유동성 시리즈 저장 및 Fed 순유동성 계산 ──────
        walcl_data = [(d, _to_trillions(v, "WALCL")) for d, v in (res_map.get("WALCL") or [])]
        tga_data = [(d, _to_trillions(v, "WTREGEN")) for d, v in (res_map.get("WTREGEN") or [])]
        rrp_data = [(d, _to_trillions(v, "RRPONTSYD")) for d, v in (res_map.get("RRPONTSYD") or [])]
        m2_data = [(d, _to_trillions(v, "M2SL")) for d, v in (res_map.get("M2SL") or [])]
        res_data = [(d, _to_trillions(v, "WRESBAL")) for d, v in (res_map.get("WRESBAL") or [])]
        mmf_data = [(d, _to_trillions(v, "MMMFFAQ027S")) for d, v in (res_map.get("MMMFFAQ027S") or [])]

        if walcl_data and tga_data:
            cur.execute(
                "DELETE FROM indicator_observation WHERE indicator_id IN (?, ?, ?, ?, ?)",
                (
                    code_to_id["WALCL"],
                    code_to_id["WTREGEN"],
                    code_to_id["WDTGAL"],
                    code_to_id["RRPONTSYD"],
                    code_to_id["FED_NET_LIQ"],
                ),
            )
            tga_dict = dict(tga_data)
            rrp_sorted = sorted(rrp_data, key=lambda x: x[0])

            def find_asof(series_sorted: List[Tuple[str, float]], target_dt: str, default_val: float = 0.0) -> float:
                last_v = default_val
                for d, v in series_sorted:
                    if d <= target_dt:
                        last_v = v
                    else:
                        break
                return last_v

            tga_sorted = sorted(tga_data, key=lambda x: x[0])
            for dt_s, w_val in walcl_data:
                t_val = tga_dict.get(dt_s)
                if t_val is None:
                    t_val = find_asof(tga_sorted, dt_s, 0.7)
                r_val = find_asof(rrp_sorted, dt_s, 0.2)
                net_liq = round(w_val - t_val - r_val, 3)

                upsert_obs("WALCL", dt_s, w_val, "https://fred.stlouisfed.org/series/WALCL")
                upsert_obs("WTREGEN", dt_s, t_val, "https://fred.stlouisfed.org/series/WTREGEN")
                upsert_obs("WDTGAL", dt_s, t_val, "https://fred.stlouisfed.org/series/WTREGEN")
                upsert_obs("RRPONTSYD", dt_s, r_val, "https://fred.stlouisfed.org/series/RRPONTSYD")
                upsert_obs("FED_NET_LIQ", dt_s, net_liq, "https://fred.stlouisfed.org/series/WALCL")

            for c in ("WALCL", "WTREGEN", "WDTGAL", "RRPONTSYD", "FED_NET_LIQ"):
                mark_live(c, "FRED (Official)")
            summary_log.append(f"Fed 순유동성({len(walcl_data)}주)")

        if m2_data and len(m2_data) >= 13:
            cur.execute(
                "DELETE FROM indicator_observation WHERE indicator_id IN (?, ?)",
                (code_to_id["M2SL"], code_to_id["M2_YOY"]),
            )
            for idx, (dt_s, m2_v) in enumerate(m2_data):
                upsert_obs("M2SL", dt_s, m2_v, "https://fred.stlouisfed.org/series/M2SL")
                if idx >= 12:
                    prev_12m = m2_data[idx - 12][1]
                    if prev_12m > 0:
                        yoy = round(((m2_v / prev_12m) - 1.0) * 100.0, 2)
                        upsert_obs("M2_YOY", dt_s, yoy, "https://fred.stlouisfed.org/series/M2SL")
            mark_live("M2SL", "FRED (Official)")
            mark_live("M2_YOY", "FRED (Official)")
            summary_log.append("M2 & YoY")

        if res_data:
            cur.execute("DELETE FROM indicator_observation WHERE indicator_id = ?", (code_to_id["WRESBAL"],))
            for dt_s, v in res_data:
                upsert_obs("WRESBAL", dt_s, v, "https://fred.stlouisfed.org/series/WRESBAL")
            mark_live("WRESBAL", "FRED (Official)")

        if mmf_data:
            cur.execute("DELETE FROM indicator_observation WHERE indicator_id = ?", (code_to_id["MMMFFAQ027S"],))
            for dt_s, v in mmf_data:
                upsert_obs("MMMFFAQ027S", dt_s, v, "https://fred.stlouisfed.org/series/MMMFFAQ027S")
            mark_live("MMMFFAQ027S", "FRED (Official)")

        # ── B. 미국 국채 금리 (3M, 1Y, 2Y, 5Y, 10Y, 30Y) & 스프레드 ──
        us05_list = (res_map.get("US05Y") or []) or [(d, c) for d, _, _, _, c, _ in (res_map.get("Y_US05Y") or [])]
        us10_list = (res_map.get("US10Y") or []) or [(d, c) for d, _, _, _, c, _ in (res_map.get("Y_US10Y") or [])]
        us30_list = (res_map.get("US30Y") or []) or [(d, c) for d, _, _, _, c, _ in (res_map.get("Y_US30Y") or [])]
        us3m_list = (res_map.get("US3M") or []) or [(d, c) for d, _, _, _, c, _ in (res_map.get("Y_US3M") or [])]
        if us05_list and us10_list and us30_list:
            rate_sources = {
                "US3M": us3m_list,
                "US1Y": res_map.get("US1Y") or [],
                "US02Y": res_map.get("US02Y") or [],
                "US05Y": us05_list,
                "US10Y": us10_list,
                "US30Y": us30_list,
                "DFF": res_map.get("DFF") or [],
            }
            for code_k, s_rows in rate_sources.items():
                if s_rows:
                    cur.execute("DELETE FROM indicator_observation WHERE indicator_id = ?", (code_to_id[code_k],))
                    cutoff_recent = s_rows[-10][0] if len(s_rows) >= 10 else "2024-01-01"
                    seen_months = set()
                    for dt_s, v in s_rows:
                        ym = dt_s[:7]
                        if dt_s >= cutoff_recent or ym not in seen_months:
                            seen_months.add(ym)
                            upsert_obs(code_k, dt_s, v, f"https://finance.yahoo.com/quote/{code_k}")
                    mark_live(code_k, "US Treasury / Yahoo Live")

            # 스프레드 계산 (10Y-5Y, 30Y-10Y)
            cur.execute(
                "DELETE FROM indicator_observation WHERE indicator_id IN (?, ?)",
                (code_to_id["US10Y_US05Y_SPREAD"], code_to_id["US30Y_US10Y_SPREAD"]),
            )
            map_5y = dict(us05_list)
            map_10y = dict(us10_list)
            map_30y = dict(us30_list)
            common_dates = sorted(set(map_5y.keys()) & set(map_10y.keys()) & set(map_30y.keys()))
            seen_m = set()
            cutoff_sp = common_dates[-5] if len(common_dates) >= 5 else "2024-01-01"
            for dt_s in common_dates:
                ym = dt_s[:7]
                if dt_s >= cutoff_sp or ym not in seen_m:
                    seen_m.add(ym)
                    upsert_obs("US10Y_US05Y_SPREAD", dt_s, round(map_10y[dt_s] - map_5y[dt_s], 2), "https://fred.stlouisfed.org")
                    upsert_obs("US30Y_US10Y_SPREAD", dt_s, round(map_30y[dt_s] - map_10y[dt_s], 2), "https://fred.stlouisfed.org")
            mark_live("US10Y_US05Y_SPREAD", "FRED / US Treasury")
            mark_live("US30Y_US10Y_SPREAD", "FRED / US Treasury")
            summary_log.append("미국채 금리(3M~30Y)")

        # ── C. 시장 가격 (NDX, QQQ, TQQQ) ───────────────────────
        latest_ndx_price = None
        for sym in ("NDX", "QQQ", "TQQQ"):
            y_rows = res_map.get(f"Y_{sym}") or []
            if y_rows:
                cur.execute("DELETE FROM market_price WHERE symbol = ?", (sym,))
                for dt_s, o, h, l, c, v in y_rows:
                    cur.execute(
                        """
                        INSERT OR REPLACE INTO market_price
                            (symbol, trade_date, open, high, low, close, adj_close, volume, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Yahoo Finance Live')
                        """,
                        (sym, dt_s, o, h, l, c, c, v),
                    )
                    total_rows_written += 1
                if sym == "NDX":
                    latest_ndx_price = y_rows[-1][4]
                    summary_log.append(f"NDX({latest_ndx_price:,.1f})")

        # FRED NASDAQ100 시리즈로 최신 NDX 종가 보완
        fred_ndx = res_map.get("NASDAQ100") or []
        if fred_ndx:
            latest_ndx_price = fred_ndx[-1][1]
            if not res_map.get("Y_NDX"):
                cur.execute("DELETE FROM market_price WHERE symbol = 'NDX'")
                seen_m = set()
                for dt_s, val in fred_ndx:
                    ym = dt_s[:7]
                    if ym not in seen_m or dt_s == fred_ndx[-1][0]:
                        seen_m.add(ym)
                        cur.execute(
                            """
                            INSERT OR REPLACE INTO market_price
                                (symbol, trade_date, open, high, low, close, adj_close, volume, source)
                            VALUES ('NDX', ?, ?, ?, ?, ?, ?, 0, 'FRED NASDAQ100')
                            """,
                            (dt_s, val, val, val, val, val),
                        )
            summary_log.append(f"NDX({latest_ndx_price:,.1f})")

        # ── D. Finviz 기반 Forward PER & 예상 EPS 업데이트 ────────
        qqq_fv = res_map.get("FV_QQQ")
        live_fpe = None
        fpe_source = ""
        if isinstance(qqq_fv, dict) and isinstance(qqq_fv.get("forward_pe"), (int, float)):
            live_fpe = float(qqq_fv["forward_pe"])
            fpe_source = "Finviz (QQQ Live)"
        else:
            # 빅테크 6종목 가중 조화평균 산출
            weights = [("NVDA", 0.089), ("AAPL", 0.087), ("MSFT", 0.081), ("AMZN", 0.054), ("META", 0.050), ("GOOGL", 0.048)]
            w_ey = 0.0
            w_sum = 0.0
            for tk, w in weights:
                info = res_map.get(f"FV_{tk}")
                if isinstance(info, dict) and isinstance(info.get("forward_pe"), (int, float)):
                    fpe_v = float(info["forward_pe"])
                    if 5.0 < fpe_v < 120.0:
                        w_ey += w * (1.0 / fpe_v)
                        w_sum += w
            if w_sum > 0 and w_ey > 0:
                live_fpe = round((w_sum / w_ey) * 0.92, 2)
                fpe_source = "Finviz (NDX Constituents Live)"

        today_str = datetime.now().strftime("%Y-%m-%d")
        if live_fpe and 10.0 < live_fpe < 60.0:
            upsert_obs("FORWARD_PER", today_str, live_fpe, "https://finviz.com/quote.ashx?t=QQQ")
            mark_live("FORWARD_PER", fpe_source)
            summary_log.append(f"Fwd PER({live_fpe}배)")

            if latest_ndx_price:
                live_eps = round(latest_ndx_price / live_fpe, 1)
                upsert_obs("FORWARD_EPS", today_str, live_eps, "https://finviz.com/quote.ashx?t=QQQ")
                mark_live("FORWARD_EPS", f"{fpe_source} + FRED NDX")
                cur.execute(
                    """
                    INSERT OR REPLACE INTO earnings_consensus
                        (index_code, asof_date, horizon, estimated_eps, provider, methodology)
                    VALUES ('NDX', ?, 'NTM', ?, ?, 'NDX / Live Forward PER')
                    """,
                    (today_str, live_eps, fpe_source),
                )
                summary_log.append(f"예상 EPS({live_eps})")

        # ── E. CNN Fear & Greed 실제 데이터 적재 ─────────────────
        cnn_data = res_map.get("CNN")
        if isinstance(cnn_data, dict) and cnn_data.get("fear_and_greed"):
            fg_curr = cnn_data["fear_and_greed"]
            fg_score = round(float(fg_curr.get("score", 50)), 0)
            fg_hist = cnn_data.get("fear_and_greed_historical", {}).get("data", [])

            cur.execute("DELETE FROM indicator_observation WHERE indicator_id = ?", (code_to_id["CNN_FG"],))
            for pt in fg_hist[-90:]:
                ts_ms = pt.get("x")
                y_val = pt.get("y")
                if ts_ms and y_val is not None:
                    dt_s = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")
                    upsert_obs("CNN_FG", dt_s, round(float(y_val), 0), "https://www.cnn.com/markets/fear-and-greed")
            upsert_obs("CNN_FG", today_str, fg_score, "https://www.cnn.com/markets/fear-and-greed")
            mark_live("CNN_FG", "CNN Dataviz Live")

            comp_mapping = [
                ("market_momentum_sp500", "MARKET_MOMENTUM"),
                ("stock_price_strength",  "STOCK_PRICE_STRENGTH"),
                ("stock_price_breadth",   "STOCK_PRICE_BREADTH"),
                ("put_call_options",      "PUT_CALL_RATIO"),
                ("market_volatility_vix", "VIX"),
                ("junk_bond_demand",      "JUNK_BOND_DEMAND"),
                ("safe_haven_demand",     "SAFE_HAVEN_DEMAND"),
            ]
            for cnn_key, db_code in comp_mapping:
                comp_obj = cnn_data.get(cnn_key)
                if isinstance(comp_obj, dict) and comp_obj.get("score") is not None:
                    c_score = round(float(comp_obj["score"]), 0)
                    cur.execute("DELETE FROM indicator_observation WHERE indicator_id = ?", (code_to_id[db_code],))
                    upsert_obs(db_code, today_str, c_score, "https://www.cnn.com/markets/fear-and-greed")
                    mark_live(db_code, "CNN Dataviz Live")
            summary_log.append(f"CNN 공포탐욕({int(fg_score)}점)")

        # ── F. 수집 작업 로그 기록 ────────────────────────────────
        cur.execute(
            """
            INSERT INTO ingestion_job (source, started_at, ended_at, status, rows_written, error)
            VALUES (?, ?, datetime('now', 'localtime'), 'SUCCESS', ?, NULL)
            """,
            ("FRED + Finviz + CNN Live Sync", started_at, total_rows_written),
        )

    return {
        "ok": True,
        "rows_written": total_rows_written,
        "summary": ", ".join(summary_log) if summary_log else "전체 지표 동기화 완료",
        "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def sync_all_live_data() -> dict:
    """동기 호출 래퍼."""
    return asyncio.run(sync_all_live_data_async())


if __name__ == "__main__":
    res = sync_all_live_data()
    print("Live Sync Result:", res)
