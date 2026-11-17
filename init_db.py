"""
TQQQ Lab - DB 초기화 스크립트
설계서 논리 모델 기반 SQLite 테이블 생성 + 9개 화면용 리얼리스틱 샘플 데이터 삽입
"""
import json
import math
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta

# 프로젝트 루트를 path 에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conf.config import DB_PATH

DDL = """
-- 1. 지표 카탈로그
CREATE TABLE IF NOT EXISTS indicator_catalog (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    code           TEXT NOT NULL UNIQUE,
    name           TEXT NOT NULL,
    unit           TEXT,
    frequency      TEXT DEFAULT 'daily',
    provider       TEXT DEFAULT 'FRED',
    license_status TEXT DEFAULT 'PUBLIC'
);

-- 2. 지표 관측값
CREATE TABLE IF NOT EXISTS indicator_observation (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id     INTEGER NOT NULL REFERENCES indicator_catalog(id),
    observation_date TEXT NOT NULL,
    published_at     TEXT,
    value            REAL NOT NULL,
    vintage          TEXT DEFAULT 'latest',
    source_url       TEXT,
    collected_at     TEXT DEFAULT (datetime('now')),
    UNIQUE(indicator_id, observation_date, vintage)
);

-- 3. 시장 가격
CREATE TABLE IF NOT EXISTS market_price (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol     TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    open       REAL,
    high       REAL,
    low        REAL,
    close      REAL NOT NULL,
    adj_close  REAL,
    volume     INTEGER,
    source     TEXT DEFAULT 'Market',
    UNIQUE(symbol, trade_date)
);

-- 4. 기업실적 컨센서스
CREATE TABLE IF NOT EXISTS earnings_consensus (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    index_code    TEXT NOT NULL,
    asof_date     TEXT NOT NULL,
    horizon       TEXT NOT NULL,
    estimated_eps REAL NOT NULL,
    provider      TEXT DEFAULT 'Consensus',
    methodology   TEXT DEFAULT 'Bottom-Up',
    UNIQUE(index_code, asof_date, horizon)
);

-- 5. 투자 전략 정의
CREATE TABLE IF NOT EXISTS strategy_definition (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    version     TEXT NOT NULL DEFAULT '1.0',
    params_json TEXT,
    enabled     INTEGER DEFAULT 1,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- 6. 종합 신호 스냅샷
CREATE TABLE IF NOT EXISTS signal_snapshot (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    asof_date      TEXT NOT NULL,
    strategy_id    INTEGER NOT NULL REFERENCES strategy_definition(id),
    score          REAL NOT NULL,
    recommendation TEXT,
    features_json  TEXT,
    data_quality   TEXT DEFAULT 'GOOD'
);

-- 7. 백테스트 실행
CREATE TABLE IF NOT EXISTS backtest_run (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_version TEXT NOT NULL,
    period_start     TEXT NOT NULL,
    period_end       TEXT NOT NULL,
    costs_json       TEXT,
    metrics_json     TEXT,
    status           TEXT DEFAULT 'COMPLETED',
    created_at       TEXT DEFAULT (datetime('now'))
);

-- 8. 백테스트 거래 로그
CREATE TABLE IF NOT EXISTS backtest_trade (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id     INTEGER NOT NULL REFERENCES backtest_run(id),
    trade_date TEXT NOT NULL,
    symbol     TEXT NOT NULL,
    side       TEXT NOT NULL,
    quantity   REAL NOT NULL,
    price      REAL NOT NULL,
    fee        REAL DEFAULT 0.0
);

-- 9. 알림 규칙
CREATE TABLE IF NOT EXISTS alert_rule (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    condition_json TEXT,
    channel        TEXT DEFAULT 'app',
    enabled        INTEGER DEFAULT 1,
    created_at     TEXT DEFAULT (datetime('now'))
);

-- 10. 알림 이벤트
CREATE TABLE IF NOT EXISTS alert_event (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id      INTEGER NOT NULL REFERENCES alert_rule(id),
    triggered_at TEXT NOT NULL,
    delivered_at TEXT,
    message      TEXT,
    status       TEXT DEFAULT 'DELIVERED'
);

-- 11. 데이터 수집 작업 로그
CREATE TABLE IF NOT EXISTS ingestion_job (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source       TEXT NOT NULL,
    started_at   TEXT,
    ended_at     TEXT,
    status       TEXT DEFAULT 'SUCCESS',
    rows_written INTEGER DEFAULT 0,
    error        TEXT
);

CREATE INDEX IF NOT EXISTS idx_obs_ind_date ON indicator_observation(indicator_id, observation_date);
CREATE INDEX IF NOT EXISTS idx_mp_sym_date  ON market_price(symbol, trade_date);
CREATE INDEX IF NOT EXISTS idx_ec_idx_date  ON earnings_consensus(index_code, asof_date);
"""


def _check_schema_valid(conn: sqlite3.Connection) -> bool:
    """기존 DB 테이블이 새 스키마(observation_date 등)와 일치하는지 확인."""
    try:
        cur = conn.execute("PRAGMA table_info(indicator_observation)")
        cols = {row[1] for row in cur.fetchall()}
        return "observation_date" in cols
    except Exception:
        return False


def insert_sample_data(conn: sqlite3.Connection) -> None:
    """9개 화면 설계서 및 레퍼런스 이미지에 맞춘 시계열/스냅샷 샘플 데이터 삽입."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM indicator_catalog")
    if cur.fetchone()[0] > 0:
        return

    random.seed(2026)
    base_date = datetime(2026, 11, 6)

    # ── 1. indicator_catalog ─────────────────────────────────
    catalog = [
        ("FED_NET_LIQ",          "Fed 순유동성",       "조$", "weekly",  "FRED",      "PUBLIC"),
        ("WALCL",                "연준 총자산",        "조$", "weekly",  "FRED",      "PUBLIC"),
        ("WTREGEN",              "재무부 일반계정(TGA)", "조$", "weekly",  "FRED",      "PUBLIC"),
        ("WDTGAL",               "재무부 일반계정",     "조$", "weekly",  "FRED",      "PUBLIC"),
        ("RRPONTSYD",            "역레포(ON RRP)",    "조$", "daily",   "FRED",      "PUBLIC"),
        ("M2SL",                 "M2 통화량",         "조$", "monthly", "FRED",      "PUBLIC"),
        ("M2_YOY",               "M2 증가율 (YoY)",   "%",   "monthly", "FRED",      "PUBLIC"),
        ("MMMFFAQ027S",          "MMF 잔액",          "조$", "weekly",  "ICI/FRED",  "PUBLIC"),
        ("WRESBAL",              "지급준비금",         "조$", "weekly",  "FRED",      "PUBLIC"),
        ("FORWARD_EPS",          "예상 EPS",          "pt",  "monthly", "Consensus", "DEMO"),
        ("EPS_REV_3M",           "EPS Revision (3개월)", "%", "monthly", "Consensus", "DEMO"),
        ("EPS_SURPRISE",         "실적 서프라이즈",     "%",   "quarterly","Consensus","DEMO"),
        ("EPS_GROWTH_YOY",       "이익 성장률 (YoY)",  "%",   "quarterly","Consensus","DEMO"),
        ("FORWARD_PER",          "Forward PER",      "배",  "monthly", "Consensus", "DEMO"),
        ("CNN_FG",               "CNN 공포탐욕지수",   "pt",  "daily",   "CNN",       "DEMO"),
        ("MARKET_MOMENTUM",      "시장 모멘텀",        "pt",  "daily",   "CNN",       "DEMO"),
        ("STOCK_PRICE_STRENGTH", "주가 강도",          "pt",  "daily",   "CNN",       "DEMO"),
        ("STOCK_PRICE_BREADTH",  "시장 폭",            "pt",  "daily",   "CNN",       "DEMO"),
        ("PUT_CALL_RATIO",       "풋/콜 옵션",         "pt",  "daily",   "CNN",       "DEMO"),
        ("VIX",                  "변동성 (VIX)",       "pt",  "daily",   "CNN",       "DEMO"),
        ("JUNK_BOND_DEMAND",     "정크본드 수요",      "pt",  "daily",   "CNN",       "DEMO"),
        ("SAFE_HAVEN_DEMAND",    "안전자산 수요",      "pt",  "daily",   "CNN",       "DEMO"),
        ("US3M",                 "미국채 3개월 스팟",   "%",   "daily",   "Treasury",  "PUBLIC"),
        ("US1Y",                 "미국채 1년 스팟",    "%",   "daily",   "Treasury",  "PUBLIC"),
        ("US02Y",                "미국채 2년 스팟",    "%",   "daily",   "Treasury",  "PUBLIC"),
        ("US05Y",                "5년 스팟",          "%",   "daily",   "Treasury",  "PUBLIC"),
        ("US10Y",                "10년 스팟",         "%",   "daily",   "Treasury",  "PUBLIC"),
        ("US30Y",                "30년 스팟",         "%",   "daily",   "Treasury",  "PUBLIC"),
        ("US10Y_US05Y_SPREAD",   "10년-5년 스프레드",   "%p",  "daily",   "Treasury",  "PUBLIC"),
        ("US30Y_US10Y_SPREAD",   "30년-10년 스프레드",  "%p",  "daily",   "Treasury",  "PUBLIC"),
        ("US10Y_US02Y_SPREAD",   "10년-2년 스프레드",   "%p",  "daily",   "Treasury",  "PUBLIC"),
        ("DFF",                  "연방기금금리",        "%",   "daily",   "FRED",      "PUBLIC"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO indicator_catalog (code, name, unit, frequency, provider, license_status) VALUES (?,?,?,?,?,?)",
        catalog,
    )

    cur.execute("SELECT id, code FROM indicator_catalog")
    code_to_id = {row[1]: row[0] for row in cur.fetchall()}

    obs_rows = []

    def add_obs(code: str, dt_str: str, val: float):
        if code in code_to_id:
            obs_rows.append((code_to_id[code], dt_str, dt_str, round(val, 4), "latest", "https://fred.stlouisfed.org"))

    # ── 5년 월별 시계열 (2021-01 ~ 2026-11, 71개월) ────────────
    months_5y = []
    y, m = 2021, 1
    while (y, m) <= (2026, 11):
        months_5y.append(f"{y:04d}-{m:02d}-01")
        m += 1
        if m > 12:
            m = 1
            y += 1

    mp_rows = []
    ec_rows = []

    for idx, dt_str in enumerate(months_5y):
        t = idx / max(1, len(months_5y) - 1)
        # 나스닥 100 지수 (12,000 -> 21,500 부근, 2022 조정 반영)
        dip = -3200 * math.exp(-((t - 0.30) / 0.12) ** 2)
        wave = 1200 * math.sin(idx * 0.45)
        ndx_val = round(12500 + 9500 * t + dip + wave, 2)
        if idx == len(months_5y) - 1:
            ndx_val = 21450.0

        tqqq_val = round(25.0 + 55.0 * t + (dip / 150.0) + (wave / 200.0), 2)
        qqq_val = round(ndx_val / 41.5, 2)

        mp_rows.append(("NDX", dt_str, ndx_val * 0.99, ndx_val * 1.01, ndx_val * 0.98, ndx_val, ndx_val, 250000000, "Index"))
        mp_rows.append(("TQQQ", dt_str, tqqq_val * 0.98, tqqq_val * 1.03, tqqq_val * 0.96, tqqq_val, tqqq_val, 65000000, "ETF"))
        mp_rows.append(("QQQ", dt_str, qqq_val * 0.99, qqq_val * 1.01, qqq_val * 0.98, qqq_val, qqq_val, 45000000, "ETF"))

        # Fed 순유동성 (5.2조 ~ 6.7조 ~ 5.81조)
        liq_peak = 0.85 * math.sin(idx * 0.18) + 0.25 * math.cos(idx * 0.35)
        net_liq = round(5.65 + liq_peak, 2)
        if idx == len(months_5y) - 2:
            net_liq = 5.72
        elif idx == len(months_5y) - 1:
            net_liq = 5.81

        tga = round(0.65 + 0.20 * math.sin(idx * 0.3), 2)
        rrp = round(max(0.15, 1.8 * math.exp(-((t - 0.35) / 0.22) ** 2)), 2)
        if idx == len(months_5y) - 1:
            tga = 0.78
            rrp = 0.46
        walcl = round(net_liq + tga + rrp, 2)

        add_obs("FED_NET_LIQ", dt_str, net_liq)
        add_obs("WALCL", dt_str, walcl)
        add_obs("WTREGEN", dt_str, tga)
        add_obs("WDTGAL", dt_str, tga)
        add_obs("RRPONTSYD", dt_str, rrp)

        # M2, MMF, 지급준비금
        m2_val = round(19.5 + 2.1 * t + 0.4 * math.sin(idx * 0.2), 2)
        m2_yoy = round(2.5 + 3.0 * math.sin(idx * 0.15 - 0.5), 2)
        mmf_val = round(4.6 + 2.2 * t + 0.1 * math.sin(idx * 0.3), 2)
        res_val = round(3.1 + 0.35 * math.sin(idx * 0.22), 2)

        if idx == len(months_5y) - 2:
            m2_val, m2_yoy, mmf_val, res_val = 21.31, 4.1, 6.78, 3.30
        elif idx == len(months_5y) - 1:
            m2_val, m2_yoy, mmf_val, res_val = 21.40, 4.3, 6.74, 3.33

        add_obs("M2SL", dt_str, m2_val)
        add_obs("M2_YOY", dt_str, m2_yoy)
        add_obs("MMMFFAQ027S", dt_str, mmf_val)
        add_obs("WRESBAL", dt_str, res_val)

        # 예상 EPS (820 -> 1378)
        eps_val = round(840 + 538 * (t ** 1.15) + 18 * math.sin(idx * 0.4), 1)
        if idx == len(months_5y) - 4:
            eps_val = 1316.0
        elif idx == len(months_5y) - 2:
            eps_val = 1350.0
        elif idx == len(months_5y) - 1:
            eps_val = 1378.0
        add_obs("FORWARD_EPS", dt_str, eps_val)
        ec_rows.append(("NDX", dt_str, "NTM", eps_val, "FactSet/LSEG", "Bottom-Up"))
        ec_rows.append(("NDX", dt_str, "FY1", round(eps_val * 0.96, 1), "FactSet/LSEG", "Bottom-Up"))
        ec_rows.append(("NDX", dt_str, "FY2", round(eps_val * 1.12, 1), "FactSet/LSEG", "Bottom-Up"))

        # 국채 스팟 금리 (5Y, 10Y, 30Y)
        r5 = round(3.65 + 1.15 * t + 0.28 * math.sin(idx * 0.35), 2)
        r10 = round(r5 + 0.18 + 0.08 * math.cos(idx * 0.25), 2)
        r30 = round(r10 + 0.38 + 0.06 * math.sin(idx * 0.2), 2)
        if idx == len(months_5y) - 2:
            r5, r10, r30 = 4.68, 4.94, 5.42
        elif idx == len(months_5y) - 1:
            r5, r10, r30 = 4.65, 4.90, 5.37

        add_obs("US05Y", dt_str, r5)
        add_obs("US10Y", dt_str, r10)
        add_obs("US30Y", dt_str, r30)
        add_obs("US02Y", dt_str, round(r5 - 0.13, 2))
        add_obs("US10Y_US05Y_SPREAD", dt_str, round(r10 - r5, 2))
        add_obs("US30Y_US10Y_SPREAD", dt_str, round(r30 - r10, 2))
        add_obs("US10Y_US02Y_SPREAD", dt_str, round(r10 - (r5 - 0.13), 2))
        add_obs("DFF", dt_str, 4.75)

    # 현재 수익률 곡선 단기물
    add_obs("US3M", "2026-11-01", 4.35)
    add_obs("US1Y", "2026-11-01", 4.42)
    add_obs("EPS_REV_3M", "2026-11-01", 4.7)
    add_obs("EPS_SURPRISE", "2026-11-01", 5.2)
    add_obs("EPS_GROWTH_YOY", "2026-11-01", 12.3)

    # ── 20년 Forward PER 시계열 (2006 ~ 2026, 250개월) ─────────
    y, m = 2006, 1
    idx_20y = 0
    while (y, m) <= (2026, 11):
        dt_str = f"{y:04d}-{m:02d}-01"
        # 2006~2014: 13~19배, 2020~2021 피크 31배, 2023~2024 27배, 현재 18.07배
        if y < 2015:
            per_v = 16.5 + 3.2 * math.sin(idx_20y * 0.15)
        elif y < 2020:
            per_v = 20.5 + 2.5 * math.sin(idx_20y * 0.2)
        elif y in (2020, 2021):
            per_v = 28.5 + 3.0 * math.sin((idx_20y - 168) * 0.25)
        elif y in (2022, 2023, 2024):
            per_v = 24.5 + 3.5 * math.cos((idx_20y - 190) * 0.2)
        else:
            per_v = 21.0 - (idx_20y - 228) * 0.14 + 0.8 * math.sin(idx_20y * 0.4)

        per_v = round(max(12.5, min(32.5, per_v)), 2)
        if (y, m) == (2026, 10):
            per_v = 18.55
        elif (y, m) == (2026, 11):
            per_v = 18.07

        add_obs("FORWARD_PER", dt_str, per_v)
        idx_20y += 1
        m += 1
        if m > 12:
            m = 1
            y += 1

    # ── CNN Fear & Greed 최근 3개월 일별 추이 및 7개 구성요소 ──
    fg_days = 90
    for d_idx in range(fg_days):
        dt_obj = base_date - timedelta(days=(fg_days - 1 - d_idx))
        dt_str = dt_obj.strftime("%Y-%m-%d")
        # 65 -> 35 -> 50 -> 22 하락 흐름
        fg_val = round(58 - 32 * (d_idx / fg_days) + 12 * math.sin(d_idx * 0.22), 0)
        fg_val = max(10, min(85, fg_val))
        if d_idx == fg_days - 7:
            fg_val = 28
        elif d_idx == fg_days - 2:
            fg_val = 24
        elif d_idx == fg_days - 1:
            fg_val = 22
        add_obs("CNN_FG", dt_str, fg_val)

    latest_dt = base_date.strftime("%Y-%m-%d")
    fg_comps = [
        ("MARKET_MOMENTUM",      8),
        ("STOCK_PRICE_STRENGTH", 42),
        ("STOCK_PRICE_BREADTH",  45),
        ("PUT_CALL_RATIO",       13),
        ("VIX",                  9),
        ("JUNK_BOND_DEMAND",     36),
        ("SAFE_HAVEN_DEMAND",    1),
    ]
    for c_code, c_val in fg_comps:
        add_obs(c_code, latest_dt, c_val)

    cur.executemany(
        "INSERT OR IGNORE INTO indicator_observation (indicator_id, observation_date, published_at, value, vintage, source_url) VALUES (?,?,?,?,?,?)",
        obs_rows,
    )
    cur.executemany(
        "INSERT OR IGNORE INTO market_price (symbol, trade_date, open, high, low, close, adj_close, volume, source) VALUES (?,?,?,?,?,?,?,?,?)",
        mp_rows,
    )
    cur.executemany(
        "INSERT OR IGNORE INTO earnings_consensus (index_code, asof_date, horizon, estimated_eps, provider, methodology) VALUES (?,?,?,?,?,?)",
        ec_rows,
    )

    # ── 5. strategy_definition ───────────────────────────────
    strategies = [
        (
            "분할매수 전략 (권장)",
            "1.0",
            json.dumps({
                "description": "유동성·밸류에이션·공포탐욕 복합 시그널 기반 TQQQ 분할매수 전략",
                "profile": "성장형 (TQQQ 중심)",
                "allocation": [
                    {"asset": "TQQQ", "ratio": 60, "color": "#38bdf8"},
                    {"asset": "QQQ",  "ratio": 20, "color": "#22c55e"},
                    {"asset": "국채", "ratio": 10, "color": "#eab308"},
                    {"asset": "현금", "ratio": 10, "color": "#94a3b8"},
                ],
                "rules": [
                    {"type": "매수 (권장)", "condition": "PER ≤ 20 AND EPS↑ AND 공포탐욕 ≤ 25", "action": "TQQQ 분할매수", "badge": "green"},
                    {"type": "추가 매수",   "condition": "지수 -10% 이상 조정 시",                 "action": "추가 매수 (비중 확대)", "badge": "blue"},
                    {"type": "일부 매도",   "condition": "지수 +15% 이상 단기 급등",               "action": "일부 매도 (10~20%)", "badge": "yellow"},
                    {"type": "비중 축소",   "condition": "PER ≥ 26 OR EPS Revision ↓",          "action": "비중 축소 ↓", "badge": "red"},
                ],
            }, ensure_ascii=False),
            1,
        ),
        (
            "무한매수법",
            "1.0",
            json.dumps({
                "description": "원금을 40분할하여 매일 평단가 대비 유리한 구간에서 기계적 분할 매수 및 목표수익 도달 시 일괄 익절",
                "profile": "안정 회전형",
                "allocation": [
                    {"asset": "TQQQ", "ratio": 50, "color": "#38bdf8"},
                    {"asset": "QQQ",  "ratio": 15, "color": "#22c55e"},
                    {"asset": "국채", "ratio": 10, "color": "#eab308"},
                    {"asset": "현금", "ratio": 25, "color": "#94a3b8"},
                ],
                "rules": [
                    {"type": "매수 (전반전)", "condition": "진행률 50% 미만 & 현재가 ≤ 평단가", "action": "1회분 LOC 매수", "badge": "green"},
                    {"type": "추가 매수",     "condition": "현재가 < 평단가 -5%",             "action": "1.5회분 분할 매수", "badge": "blue"},
                    {"type": "목표 매도",     "condition": "수익률 +10% 이상 도달",           "action": "전량 지정가 매도", "badge": "yellow"},
                    {"type": "비중 축소",     "condition": "40회 소진 시",                    "action": "쿼터 손절/리밸런싱", "badge": "red"},
                ],
            }, ensure_ascii=False),
            1,
        ),
        (
            "밸류리밸런싱",
            "1.0",
            json.dumps({
                "description": "목표 평가금 경로(V)를 설정하고 밴드(±15%) 이탈 시에만 매수/매도하여 변동성을 수익으로 전환",
                "profile": "장기 적립/인출형",
                "allocation": [
                    {"asset": "TQQQ", "ratio": 55, "color": "#38bdf8"},
                    {"asset": "QQQ",  "ratio": 20, "color": "#22c55e"},
                    {"asset": "국채", "ratio": 10, "color": "#eab308"},
                    {"asset": "현금", "ratio": 15, "color": "#94a3b8"},
                ],
                "rules": [
                    {"type": "매수 (권장)", "condition": "평가금 < 최소밴드 (V × 0.85)", "action": "TQQQ 분할 매수", "badge": "green"},
                    {"type": "적립 유지",   "condition": "최소밴드 ≤ 평가금 ≤ 최대밴드", "action": "Pool 현금 적립 유지", "badge": "blue"},
                    {"type": "일부 매도",   "condition": "평가금 > 최대밴드 (V × 1.15)", "action": "초과분 일부 매도", "badge": "yellow"},
                    {"type": "비중 축소",   "condition": "Pool 현금 비중 5% 미만",      "action": "G값 하향 조정", "badge": "red"},
                ],
            }, ensure_ascii=False),
            1,
        ),
        (
            "가치평균매수 (VA)",
            "1.0",
            json.dumps({
                "description": "매월 목표 자산가치 증가분을 정해두고 하락 시 추가 매수, 급등 시 일부 현금화",
                "profile": "가치 평균형",
                "allocation": [
                    {"asset": "TQQQ", "ratio": 45, "color": "#38bdf8"},
                    {"asset": "QQQ",  "ratio": 25, "color": "#22c55e"},
                    {"asset": "국채", "ratio": 15, "color": "#eab308"},
                    {"asset": "현금", "ratio": 15, "color": "#94a3b8"},
                ],
                "rules": [
                    {"type": "매수 (권장)", "condition": "월간 평가액 < 목표 경로", "action": "부족분 TQQQ 매수", "badge": "green"},
                    {"type": "추가 매수",   "condition": "Forward PER ≤ 19배",    "action": "목표 증액분 1.2배 상향", "badge": "blue"},
                    {"type": "일부 매도",   "condition": "월간 평가액 > 목표 경로 +10%", "action": "초과분 현금 확보", "badge": "yellow"},
                    {"type": "비중 축소",   "condition": "연준 순유동성 4주 연속 감소", "action": "안전자산 비중 확대", "badge": "red"},
                ],
            }, ensure_ascii=False),
            1,
        ),
        (
            "커버드콜 (QQQ)",
            "1.0",
            json.dumps({
                "description": "QQQ/TQQQ 코어 자산에 현금흐름(배당/옵션 프리미엄)을 결합하여 하락장 방어력 확보",
                "profile": "인컴 결합형",
                "allocation": [
                    {"asset": "TQQQ", "ratio": 30, "color": "#38bdf8"},
                    {"asset": "QQQ",  "ratio": 45, "color": "#22c55e"},
                    {"asset": "국채", "ratio": 15, "color": "#eab308"},
                    {"asset": "현금", "ratio": 10, "color": "#94a3b8"},
                ],
                "rules": [
                    {"type": "매수 (권장)", "condition": "분배금 수령 시 공포탐욕 ≤ 35", "action": "TQQQ 재투자 매수", "badge": "green"},
                    {"type": "추가 매수",   "condition": "VIX ≥ 25 변동성 확대",        "action": "프리미엄으로 QQQ 매수", "badge": "blue"},
                    {"type": "일부 매도",   "condition": "Forward PER ≥ 25배",         "action": "TQQQ → QQQ 전환", "badge": "yellow"},
                    {"type": "비중 축소",   "condition": "10Y 금리 ≥ 5.25%",           "action": "단기채 비중 확대", "badge": "red"},
                ],
            }, ensure_ascii=False),
            1,
        ),
    ]
    cur.executemany(
        "INSERT INTO strategy_definition (name, version, params_json, enabled) VALUES (?,?,?,?)",
        strategies,
    )

    # ── 6. signal_snapshot (대시보드 & 리포트용) ────────────────
    snapshots = [
        (
            "2026-11-06 18:00",
            1,
            72.0,
            "TQQQ: 분할매수 유리",
            json.dumps({
                "title": "주간 시장 분석 리포트",
                "summary": "Fed 순유동성 +1.5% 개선 및 Forward PER 18.07배 저평가, 공포탐욕 22(극단적 공포)로 분할매수 유리 구간 진입",
                "bullets": [
                    {"label": "유동성: 개선 (+1.5%)", "status": "good"},
                    {"label": "실적(EPS): 성장 (+2.1%)", "status": "good"},
                    {"label": "밸류에이션: 낮은 수준 (18.07배)", "status": "good"},
                    {"label": "공포탐욕: 극단적 공포 (22)", "status": "good"},
                    {"label": "금리: 10년 4.90% (안정)", "status": "warn"},
                ],
            }, ensure_ascii=False),
            "GOOD",
        ),
        (
            "2026-11-05 09:00",
            2,
            68.0,
            "미국 금리/유동성 동향",
            json.dumps({
                "title": "미국 금리/유동성 동향",
                "summary": "10년물 스팟 금리 4.90%(-0.04%p) 안정화 및 역레포 잔고 감소에 따른 시중 유동성 공급 지속",
            }, ensure_ascii=False),
            "GOOD",
        ),
        (
            "2026-11-03 16:00",
            3,
            75.0,
            "나스닥100 실적 전망 업데이트",
            json.dumps({
                "title": "나스닥100 실적 전망 업데이트",
                "summary": "향후 12개월 예상 EPS 1,378(+2.1%), 3개월 EPS Revision +4.7% 상향 조정 지속",
            }, ensure_ascii=False),
            "GOOD",
        ),
    ]
    cur.executemany(
        "INSERT INTO signal_snapshot (asof_date, strategy_id, score, recommendation, features_json, data_quality) VALUES (?,?,?,?,?,?)",
        snapshots,
    )

    # ── 7. backtest_run & 8. backtest_trade ──────────────────
    bt_runs = [
        (
            "분할매수 전략",
            "2006-01",
            "2026-10",
            json.dumps({"fee_pct": 0.1, "slippage_pct": 0.05}),
            json.dumps({
                "cum_return_pct": 3790,
                "cagr": 37.9,
                "mdd": -56.4,
                "sharpe": 1.11,
                "comparison": [
                    {"metric": "CAGR",    "buy_hold": "+26.3%", "dca": "+37.9%", "value_reb": "+34.1%", "inf_buy": "+31.4%"},
                    {"metric": "MDD",     "buy_hold": "-79.7%", "dca": "-56.4%", "value_reb": "-58.1%", "inf_buy": "-60.3%"},
                    {"metric": "샤프지수", "buy_hold": "0.82",   "dca": "1.11",   "value_reb": "1.05",   "inf_buy": "0.98"},
                ],
            }, ensure_ascii=False),
            "COMPLETED",
        ),
        (
            "밸류리밸런싱",
            "2006-01",
            "2026-10",
            json.dumps({"fee_pct": 0.1, "slippage_pct": 0.05}),
            json.dumps({"cum_return_pct": 2510, "cagr": 34.1, "mdd": -58.1, "sharpe": 1.05}),
            "COMPLETED",
        ),
        (
            "무한매수법",
            "2006-01",
            "2026-10",
            json.dumps({"fee_pct": 0.1, "slippage_pct": 0.05}),
            json.dumps({"cum_return_pct": 1980, "cagr": 31.4, "mdd": -60.3, "sharpe": 0.98}),
            "COMPLETED",
        ),
        (
            "단순 보유 (Buy & Hold)",
            "2006-01",
            "2026-10",
            json.dumps({"fee_pct": 0.05, "slippage_pct": 0.02}),
            json.dumps({"cum_return_pct": 1340, "cagr": 26.3, "mdd": -79.7, "sharpe": 0.82}),
            "COMPLETED",
        ),
    ]
    cur.executemany(
        "INSERT INTO backtest_run (strategy_version, period_start, period_end, costs_json, metrics_json, status) VALUES (?,?,?,?,?,?)",
        bt_runs,
    )

    trades = [
        (1, "2026-11-05", "TQQQ", "매수", 120, 74.50, 0.89),
        (1, "2026-10-22", "TQQQ", "매수", 150, 71.20, 1.07),
        (1, "2026-09-18", "TQQQ", "일부매도", 80, 79.40, 0.64),
        (1, "2026-08-11", "TQQQ", "추가매수", 200, 65.80, 1.32),
        (1, "2026-07-15", "QQQ",  "매수", 40, 488.20, 1.95),
        (1, "2026-06-03", "TQQQ", "매수", 100, 68.90, 0.69),
    ]
    cur.executemany(
        "INSERT INTO backtest_trade (run_id, trade_date, symbol, side, quantity, price, fee) VALUES (?,?,?,?,?,?,?)",
        trades,
    )

    # ── 9. alert_rule & 10. alert_event ──────────────────────
    rules = [
        ("분할매수 신호 발생", json.dumps({"condition": "PER ≤ 20 AND 공포탐욕 ≤ 25", "color": "green"}, ensure_ascii=False), "앱 알림", 1),
        ("유동성 증가 감지",   json.dumps({"condition": "Fed 순유동성 주간 +1.0% 이상", "color": "blue"}, ensure_ascii=False), "앱 알림", 1),
        ("금리 하락 알림",     json.dumps({"condition": "10년 스팟 금리 일간 -0.03%p 이하", "color": "yellow"}, ensure_ascii=False), "앱 알림", 1),
    ]
    cur.executemany(
        "INSERT INTO alert_rule (name, condition_json, channel, enabled) VALUES (?,?,?,?)",
        rules,
    )

    events = [
        (1, "2026-11-06 10:10", "2026-11-06 10:10", "PER 18.07배, 공포탐욕 22", "DELIVERED"),
        (2, "2026-11-05 08:30", "2026-11-05 08:30", "Fed 순유동성 +1.5%", "DELIVERED"),
        (3, "2026-11-04 07:00", "2026-11-04 07:00", "10년 금리 4.90% (-0.04%p)", "DELIVERED"),
    ]
    cur.executemany(
        "INSERT INTO alert_event (rule_id, triggered_at, delivered_at, message, status) VALUES (?,?,?,?,?)",
        events,
    )

    conn.commit()


def init_database(force_reset: bool = False) -> None:
    """DB 파일 생성, 스키마 검증 후 테이블 생성 및 샘플 데이터 삽입."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        valid = _check_schema_valid(conn)
        conn.close()
        if not valid or force_reset:
            os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(DDL)
    insert_sample_data(conn)
    conn.close()


if __name__ == "__main__":
    init_database(force_reset=True)
    print(f"DB initialized at: {DB_PATH}")
