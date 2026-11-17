"""
TQQQ Lab - NiceGUI & FastAPI 통합 진입점
프리미엄 핀테크 다크 테마 + 기능별 그룹핑 사이드바 네비게이션
"""
import asyncio
import os
import sys

# 프로젝트 루트를 path 에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nicegui import ui, app

from conf.config import APP_TITLE, APP_HOST, APP_PORT, APP_RELOAD, COLORS
from init_db import init_database

# DB 초기화 실행
init_database()

# 페이지 UI 모듈 임포트
from apps.pages.dashboard_page import create_dashboard_page
from apps.pages.liquidity_page import create_liquidity_page
from apps.pages.earnings_page import create_earnings_page
from apps.pages.valuation_page import create_valuation_page
from apps.pages.sentiment_page import create_sentiment_page
from apps.pages.treasury_page import create_treasury_page
from apps.pages.strategy_page import create_strategy_page
from apps.pages.backtest_page import create_backtest_page
from apps.pages.reports_page import create_reports_page

# 백엔드 함수 임포트
from apps.funcs.dashboard_func import get_dashboard_kpi, get_investment_signal_score
from apps.funcs.treasury_func import get_yield_curve
from apps.funcs.sentiment_func import get_fear_greed_score, get_fear_greed_components
from apps.funcs.valuation_func import get_valuation_kpi, sync_live_forward_per
from utils.live_sync import sync_all_live_data_async

# ── 글로벌 프리미엄 핀테크 CSS (반응형 모바일/태블릿/PC 자동 대응) ──
GLOBAL_CSS = """
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" />
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700;800&display=swap" rel="stylesheet">
<style>
:root {
    --bg-dark:    #070b14;
    --card-bg:    #101829;
    --sidebar-bg: #090e1a;
    --accent:     #38bdf8;
    --primary:    #3b82f6;
    --green:      #10b981;
    --red:        #f43f5e;
    --yellow:     #f59e0b;
    --text:       #f1f5f9;
    --text-muted: #94a3b8;
    --border:     rgba(148, 163, 184, 0.14);
}

body, .q-page, .nicegui-content {
    background-color: var(--bg-dark) !important;
    background-image:
        radial-gradient(at 15% 10%, rgba(37, 99, 235, 0.10) 0px, transparent 45%),
        radial-gradient(at 85% 5%, rgba(16, 185, 129, 0.06) 0px, transparent 40%);
    color: var(--text) !important;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
    letter-spacing: -0.01em;
    overflow-x: hidden !important;
}

.nicegui-content {
    padding: 0 !important;
    width: 100% !important;
    max-width: 100vw !important;
}

/* 스크롤바 커스텀 */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #070b14; }
::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #334155; }

/* 사이드바 & 헤더 */
.q-drawer {
    background: linear-gradient(180deg, #0a101f 0%, #070b14 100%) !important;
    border-right: 1px solid rgba(148, 163, 184, 0.12) !important;
}
.q-header {
    background: rgba(10, 16, 31, 0.88) !important;
    backdrop-filter: blur(12px) !important;
    border-bottom: 1px solid rgba(148, 163, 184, 0.12) !important;
}

/* 그룹 헤더 */
.nav-group-header {
    font-size: 0.68rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748b;
    padding: 14px 18px 6px 18px;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* 사이드바 메뉴 아이템 */
.menu-item {
    color: #94a3b8;
    padding: 9px 14px;
    border-radius: 10px;
    margin: 2px 10px;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid transparent;
}
.menu-item:hover {
    background: rgba(56, 189, 248, 0.08);
    color: #f8fafc;
    border-color: rgba(56, 189, 248, 0.15);
    transform: translateX(2px);
}
.menu-item.active {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.28) 0%, rgba(29, 78, 216, 0.12) 100%);
    color: #ffffff !important;
    border: 1px solid rgba(56, 189, 248, 0.35);
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.18);
}
.menu-icon-box {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(148, 163, 184, 0.08);
    transition: all 0.2s;
}
.menu-item.active .menu-icon-box {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.45);
}

/* 공통 프리미엄 카드 */
.q-card {
    background: linear-gradient(145deg, rgba(19, 28, 49, 0.92) 0%, rgba(12, 19, 34, 0.96) 100%) !important;
    border: 1px solid rgba(148, 163, 184, 0.14) !important;
    border-radius: 14px !important;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.45), inset 0 1px 0 0 rgba(255, 255, 255, 0.05) !important;
    transition: border-color 0.2s ease, transform 0.2s ease;
    max-width: 100% !important;
}
.q-card:hover {
    border-color: rgba(56, 189, 248, 0.28) !important;
}

/* 세그먼트 탭 바 스타일 */
.q-tabs {
    background: #0b1120 !important;
    border: 1px solid rgba(148, 163, 184, 0.14) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    min-height: 44px !important;
    max-width: 100% !important;
}
.q-tab {
    border-radius: 8px !important;
    min-height: 36px !important;
    padding: 0 18px !important;
    color: #94a3b8 !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    text-transform: none !important;
    transition: all 0.2s ease !important;
}
.q-tab--active {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 10px rgba(37, 99, 235, 0.35) !important;
}
.q-tab__indicator {
    display: none !important;
}
.q-tab-panels, .q-tab-panel {
    background: transparent !important;
}

/* 테이블 다크 스타일 */
.q-table__container {
    background: transparent !important;
    border: 1px solid rgba(148, 163, 184, 0.12) !important;
    border-radius: 10px !important;
    box-shadow: none !important;
    overflow-x: auto !important;
}
.q-table th {
    background: rgba(15, 23, 42, 0.8) !important;
    color: #94a3b8 !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    border-bottom: 1px solid rgba(148, 163, 184, 0.16) !important;
}
.q-table td {
    color: #e2e8f0 !important;
    font-size: 0.88rem !important;
    border-bottom: 1px solid rgba(148, 163, 184, 0.08) !important;
}
.q-table tbody tr:hover {
    background: rgba(56, 189, 248, 0.06) !important;
}

/* 숫자 전용 폰트 */
.num-mono {
    font-family: 'JetBrains Mono', 'Pretendard', monospace;
    font-variant-numeric: tabular-nums;
}

/* ── 반응형 레이아웃 그리드 & 컨테이너 ───────────────────────── */
.page-container {
    width: 100%;
    padding: 24px;
    box-sizing: border-box;
}

.kpi-grid-6 {
    display: grid !important;
    grid-template-columns: repeat(6, minmax(0, 1fr)) !important;
    gap: 14px !important;
    width: 100% !important;
}
.kpi-grid-5 {
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    gap: 14px !important;
    width: 100% !important;
}
.kpi-grid-4 {
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: 16px !important;
    width: 100% !important;
}

.responsive-row {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: stretch !important;
    width: 100% !important;
}

/* 태블릿 가로 & 소형 노트북 (1024px ~ 1279px) */
@media (max-width: 1279px) {
    .kpi-grid-6 {
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    }
    .kpi-grid-5 {
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    }
}

/* 태블릿 세로 & 모바일 공통 (< 1024px) */
@media (max-width: 1023px) {
    .page-container {
        padding: 16px !important;
        gap: 14px !important;
    }
    .responsive-row {
        flex-direction: column !important;
        flex-wrap: wrap !important;
        gap: 14px !important;
    }
    .responsive-row > div,
    .responsive-row > .q-card {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        flex: 1 1 100% !important;
    }
    .kpi-grid-4 {
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        gap: 12px !important;
    }
}

/* 스마트폰 (< 640px) */
@media (max-width: 639px) {
    .page-container {
        padding: 10px 12px !important;
        gap: 12px !important;
    }
    .kpi-grid-6,
    .kpi-grid-5,
    .kpi-grid-4 {
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        gap: 10px !important;
    }
    .kpi-card-box {
        padding: 12px 13px !important;
        border-radius: 12px !important;
    }
    .kpi-value-text {
        font-size: 1.28rem !important;
        margin: 4px 0 !important;
    }
    .page-header-title {
        font-size: 1.12rem !important;
    }
    .page-header-sub {
        font-size: 0.74rem !important;
        line-height: 1.35 !important;
    }
    .q-card {
        padding: 14px !important;
        border-radius: 12px !important;
    }
    .q-tab {
        padding: 0 11px !important;
        font-size: 0.78rem !important;
        min-height: 32px !important;
    }
    .echart-box {
        height: 250px !important;
    }
    .echart-box-sm {
        height: 190px !important;
    }
    .strategy-rule-row {
        flex-wrap: wrap !important;
        gap: 6px !important;
    }
    .strategy-rule-action {
        width: 100% !important;
        text-align: left !important;
        padding-left: 4px !important;
    }
}

/* 초소형 화면 (< 359px) */
@media (max-width: 359px) {
    .kpi-grid-6,
    .kpi-grid-5,
    .kpi-grid-4 {
        grid-template-columns: repeat(1, minmax(0, 1fr)) !important;
    }
}
</style>
<script>
window.addEventListener('resize', () => {
    setTimeout(() => {
        document.querySelectorAll('.nicegui-echart, [_echarts_instance_]').forEach(el => {
            if (window.echarts) {
                const inst = window.echarts.getInstanceByDom(el);
                if (inst) inst.resize();
            }
        });
    }, 120);
});
</script>
"""

# ── 기능별 그룹핑된 사이드바 메뉴 정의 ──────────────────────────
MENU_GROUPS = [
    {
        "group_title": "종합 현황",
        "group_icon": "space_dashboard",
        "items": [
            {
                "label": "대시보드",
                "sub": "전체 시장 요약 · 종합 신호",
                "icon": "dashboard",
                "path": "/",
            },
        ],
    },
    {
        "group_title": "거시경제 · 유동성",
        "group_icon": "account_balance",
        "items": [
            {
                "label": "시장 유동성",
                "sub": "Fed 순유동성 · M2 · MMF",
                "icon": "water_drop",
                "path": "/liquidity",
            },
            {
                "label": "미국 국채 금리",
                "sub": "5·10·30Y 스팟 · 수익률곡선",
                "icon": "show_chart",
                "path": "/treasury",
            },
        ],
    },
    {
        "group_title": "펀더멘털 · 밸류 · 심리",
        "group_icon": "analytics",
        "items": [
            {
                "label": "기업실적 (EPS)",
                "sub": "12M 예상 EPS · Revision",
                "icon": "trending_up",
                "path": "/earnings",
            },
            {
                "label": "밸류에이션 (PER)",
                "sub": "20년 Forward PER · 분포",
                "icon": "pie_chart",
                "path": "/valuation",
            },
            {
                "label": "시장심리 (CNN)",
                "sub": "공포·탐욕 지수 · 7대 요소",
                "icon": "speed",
                "path": "/sentiment",
            },
        ],
    },
    {
        "group_title": "투자 전략 · 검증 · 알림",
        "group_icon": "bolt",
        "items": [
            {
                "label": "투자 전략",
                "sub": "매수·매도 규칙 · 비중관리",
                "icon": "track_changes",
                "path": "/strategy",
            },
            {
                "label": "백테스트",
                "sub": "전략별 성과 · 리스크 분석",
                "icon": "insights",
                "path": "/backtest",
            },
            {
                "label": "리포트 / 알림",
                "sub": "분석 리포트 · 신호 알림",
                "icon": "notifications_active",
                "path": "/reports",
            },
        ],
    },
]


def _find_current_menu_info(current_path: str) -> tuple[str, str]:
    for grp in MENU_GROUPS:
        for item in grp["items"]:
            if item["path"] == current_path:
                return grp["group_title"], item["label"]
    return "종합 현황", "대시보드"


def create_layout(current_path: str = "/"):
    """공통 상단 헤더 + 기능별 그룹핑된 좌측 사이드바 레이아웃 생성."""
    ui.add_head_html(GLOBAL_CSS)
    grp_title, page_title = _find_current_menu_info(current_path)
    live_kpi = get_dashboard_kpi()
    per_str = live_kpi["forward_per"]["value"]
    per_chg = live_kpi["forward_per"]["change"]
    us10_str = live_kpi["treasury_10y"]["value"]
    us10_chg = live_kpi["treasury_10y"]["change"]
    fg_str = live_kpi["cnn_fear_greed"]["value"]
    fg_lbl = live_kpi["cnn_fear_greed"]["change"]
    eps_str = live_kpi["expected_eps"]["value"]
    eps_chg = live_kpi["expected_eps"]["change"]

    # ── 좌측 사이드바 (PC: 고정 표시 / 스마트폰·태블릿 <1024px: 자동 슬라이드 오버레이) ──
    with ui.left_drawer(fixed=True).props("breakpoint=1024 width=256").classes("q-pa-none") as drawer:
        with ui.column().classes("w-full h-full justify-between no-wrap"):
            with ui.column().classes("w-full q-pb-md"):
                # 사이드바 상단 브랜드 배너
                with ui.row().classes("w-full items-center gap-3 px-4 py-4 cursor-pointer").style(
                    "border-bottom: 1px solid rgba(148, 163, 184, 0.12);"
                ).on("click", lambda: ui.navigate.to("/")):
                    with ui.element("div").style(
                        "width:38px;height:38px;border-radius:10px;"
                        "background:linear-gradient(135deg,#2563eb 0%,#06b6d4 100%);"
                        "display:flex;align-items:center;justify-content:center;"
                        "box-shadow:0 4px 12px rgba(37,99,235,0.4);"
                    ):
                        ui.icon("candlestick_chart", size="22px").style("color:#ffffff;")
                    with ui.column().classes("gap-0"):
                        with ui.row().classes("items-center gap-1.5"):
                            ui.label("TQQQ Lab").style(
                                "font-size:1.15rem;font-weight:800;color:#f8fafc;letter-spacing:-0.02em;"
                            )
                            ui.badge("PRO").style(
                                "background:rgba(56,189,248,0.18);color:#38bdf8;font-size:0.62rem;"
                                "font-weight:800;padding:1px 6px;border-radius:4px;"
                            )
                        ui.label("NASDAQ-100 Quant Platform").style(
                            "font-size:0.7rem;color:#64748b;font-weight:600;"
                        )

                # 그룹별 메뉴 렌더링
                for grp in MENU_GROUPS:
                    with ui.element("div").classes("nav-group-header"):
                        ui.icon(grp["group_icon"], size="14px").style("color:#475569;")
                        ui.label(grp["group_title"])

                    for item in grp["items"]:
                        is_active = current_path == item["path"]
                        active_cls = "active" if is_active else ""
                        icon_color = "#ffffff" if is_active else "#94a3b8"
                        title_color = "#ffffff" if is_active else "#e2e8f0"
                        sub_color = "#93c5fd" if is_active else "#64748b"

                        with ui.row().classes(f"menu-item {active_cls} items-center gap-3 no-wrap").on(
                            "click", lambda p=item["path"]: ui.navigate.to(p)
                        ):
                            with ui.element("div").classes("menu-icon-box"):
                                ui.icon(item["icon"], size="18px").style(f"color:{icon_color};")
                            with ui.column().classes("gap-0 flex-1"):
                                ui.label(item["label"]).style(
                                    f"font-size:0.88rem;font-weight:{'700' if is_active else '600'};color:{title_color};line-height:1.2;"
                                )
                                ui.label(item["sub"]).style(
                                    f"font-size:0.69rem;color:{sub_color};margin-top:2px;line-height:1.1;"
                                )

            # 사이드바 하단 미니 시그널 상태 카드
            with ui.column().classes("w-full px-3 pb-4"):
                with ui.element("div").style(
                    "background:linear-gradient(135deg,rgba(16,185,129,0.12) 0%,rgba(15,23,42,0.9) 100%);"
                    "border:1px solid rgba(16,185,129,0.3);border-radius:12px;padding:12px;"
                ):
                    with ui.row().classes("w-full items-center justify-between mb-1"):
                        ui.label("종합 투자 시그널").style("font-size:0.72rem;color:#94a3b8;font-weight:600;")
                        ui.badge("72 / 100").style(
                            "background:#10b981;color:#fff;font-size:0.68rem;font-weight:800;padding:2px 7px;"
                        )
                    ui.label("TQQQ 분할매수 유리").style(
                        "font-size:0.86rem;font-weight:800;color:#34d399;"
                    )
                    ui.label(f"PER {per_str} · 공포탐욕 {fg_str}").style(
                        "font-size:0.7rem;color:#64748b;margin-top:2px;"
                    )

    # ── 상단 글래스모피즘 헤더 바 (모바일/PC 반응형) ────────────
    ticker_items = [
        ("Fwd EPS", eps_str, eps_chg, True),
        ("Fwd PER", per_str, per_chg, True),
        ("CNN F&G", fg_str, fg_lbl, False),
        ("US 10Y", us10_str, us10_chg, False),
    ]

    with ui.header().classes("q-px-sm q-px-md-lg q-py-xs"):
        with ui.column().classes("w-full gap-1"):
            with ui.row().classes("w-full items-center justify-between no-wrap"):
                # 좌측: 사이드바 토글 + 브레드크럼(현재 그룹 > 현재 메뉴)
                with ui.row().classes("items-center gap-2 no-wrap"):
                    ui.button(icon="menu", on_click=drawer.toggle).props("flat dense round color=grey-4")
                    with ui.row().classes("items-center gap-1.5 no-wrap"):
                        ui.label(grp_title).classes("gt-xs").style("color:#64748b;font-size:0.82rem;font-weight:600;")
                        ui.icon("chevron_right", size="16px").classes("gt-xs").style("color:#475569;")
                        ui.label(page_title).style("color:#f8fafc;font-size:0.9rem;font-weight:700;white-space:nowrap;")

                # 중앙(PC 전용): 실시간 미니 마켓 티커 바
                with ui.row().classes("items-center gap-4 px-4 py-1.5 rounded-full gt-sm no-wrap").style(
                    "background:rgba(15,23,42,0.75);border:1px solid rgba(148,163,184,0.14);"
                ):
                    for sym, val, chg, is_up in ticker_items:
                        with ui.row().classes("items-center gap-1.5 no-wrap"):
                            ui.label(sym).style("color:#64748b;font-size:0.74rem;font-weight:700;")
                            ui.label(val).classes("num-mono").style("color:#f1f5f9;font-size:0.76rem;font-weight:700;")
                            ui.label(chg).classes("num-mono").style(
                                f"color:{'#34d399' if is_up else '#f87171'};font-size:0.72rem;font-weight:600;"
                            )

                # 우측: 실시간 데이터 연동 버튼 + 기준일
                with ui.row().classes("items-center gap-2 no-wrap"):
                    async def _global_sync():
                        sync_header_btn.props("loading")
                        ui.notify("전체 지표(FRED 유동성·금리·주가·PER·공포탐욕) 실시간 수집 중...", type="info")
                        res = await sync_all_live_data_async()
                        sync_header_btn.props(remove="loading")
                        if res.get("ok"):
                            ui.notify(
                                f"실시간 연동 완료 ({res['rows_written']}건 갱신): {res['summary']}",
                                type="positive",
                            )
                            ui.navigate.reload()
                        else:
                            ui.notify(res.get("message", "연동 실패"), type="warning")

                    sync_header_btn = ui.button("실시간 연동", icon="sync", on_click=_global_sync).props(
                        "unelevated dense size=sm"
                    ).style(
                        "background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;"
                        "font-weight:700;padding:4px 10px;border-radius:8px;white-space:nowrap;"
                    )
                    with ui.row().classes("items-center gap-1.5 px-2.5 py-1 rounded-md gt-xs no-wrap").style(
                        "background:rgba(255,255,255,0.04);border:1px solid rgba(148,163,184,0.12);"
                    ):
                        ui.icon("schedule", size="14px").style("color:#38bdf8;")
                        ui.label("LIVE DB").classes("num-mono").style("color:#34d399;font-size:0.76rem;font-weight:700;")

            # 모바일/태블릿 전용 (< 1024px): 가로 스크롤 가능한 미니 마켓 티커 바
            with ui.row().classes("w-full items-center justify-between gap-3 px-2.5 py-1 rounded-lg lt-md no-wrap").style(
                "background:rgba(15,23,42,0.8);border:1px solid rgba(148,163,184,0.12);overflow-x:auto;"
            ):
                for sym, val, chg, is_up in ticker_items:
                    with ui.row().classes("items-center gap-1 no-wrap").style("flex-shrink:0;"):
                        ui.label(sym).style("color:#64748b;font-size:0.68rem;font-weight:700;")
                        ui.label(val).classes("num-mono").style("color:#f1f5f9;font-size:0.71rem;font-weight:700;")
                        ui.label(chg).classes("num-mono").style(
                            f"color:{'#34d399' if is_up else '#f87171'};font-size:0.67rem;font-weight:600;"
                        )


# ══════════════════════════════════════════════════════════════
#  9개 화면 라우트 등록
# ══════════════════════════════════════════════════════════════

@ui.page("/")
def page_dashboard():
    create_layout("/")
    create_dashboard_page()


@ui.page("/liquidity")
def page_liquidity():
    create_layout("/liquidity")
    create_liquidity_page()


@ui.page("/earnings")
def page_earnings():
    create_layout("/earnings")
    create_earnings_page()


@ui.page("/valuation")
def page_valuation():
    create_layout("/valuation")
    create_valuation_page()


@ui.page("/sentiment")
def page_sentiment():
    create_layout("/sentiment")
    create_sentiment_page()


@ui.page("/treasury")
def page_treasury():
    create_layout("/treasury")
    create_treasury_page()


@ui.page("/strategy")
def page_strategy():
    create_layout("/strategy")
    create_strategy_page()


@ui.page("/backtest")
def page_backtest():
    create_layout("/backtest")
    create_backtest_page()


@ui.page("/reports")
def page_reports():
    create_layout("/reports")
    create_reports_page()


# ══════════════════════════════════════════════════════════════
#  설계서 API 명세 (FastAPI 엔드포인트)
# ══════════════════════════════════════════════════════════════

@app.get("/healthz")
def api_healthz():
    return {"status": "ok", "service": "tqqq-lab"}


@app.get("/readyz")
def api_readyz():
    return {"status": "ready", "db": "sqlite3", "mapper": "mybatis-mapper2sql"}


@app.get("/api/v1/overview")
def api_overview():
    return {
        "kpi": get_dashboard_kpi(),
        "signal": get_investment_signal_score(),
    }


@app.get("/api/v1/treasury/curve")
def api_treasury_curve():
    return get_yield_curve()


@app.get("/api/v1/sentiment/fear-greed")
def api_fear_greed():
    return {
        "score": get_fear_greed_score(),
        "components": get_fear_greed_components(),
    }


@app.get("/api/v1/valuation/forward-pe")
def api_forward_pe():
    return get_valuation_kpi()


if __name__ == "__main__":
    ui.run(
        title=APP_TITLE,
        host=APP_HOST,
        port=APP_PORT,
        reload=APP_RELOAD,
        dark=True,
        favicon="📈",
    )
