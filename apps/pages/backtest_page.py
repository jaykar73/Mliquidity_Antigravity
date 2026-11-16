"""
08. TQQQ Lab — 백테스트 페이지 UI (프리미엄 다크 테마 + EChart)
"""
from nicegui import ui
from conf.config import COLORS
from utils.ui_theme import CARD_STYLE, page_header, section_title
from apps.funcs.backtest_func import (
    get_backtest_result,
    run_backtest,
)


def _cum_return_echart(data: dict):
    """누적 수익률 비교 멀티 라인 EChart."""
    s = data["series"]
    options = {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "rgba(15, 23, 42, 0.94)",
            "textStyle": {"color": "#f8fafc"},
        },
        "legend": {
            "data": ["분할매수 (+3,790%)", "밸류매수 (+2,510%)", "무한매수 (+1,980%)", "단순보유 (+1,340%)"],
            "top": 0,
            "textStyle": {"color": "#cbd5e1", "fontSize": 11},
        },
        "grid": {"left": "9%", "right": "4%", "top": "15%", "bottom": "10%"},
        "xAxis": {
            "type": "category",
            "data": data["years"],
            "axisLabel": {"color": "#94a3b8"},
        },
        "yAxis": {
            "type": "value",
            "axisLabel": {"color": "#94a3b8", "formatter": "{value}%"},
            "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.08)"}},
        },
        "series": [
            {
                "name": "분할매수 (+3,790%)",
                "type": "line",
                "data": s["dca"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#10b981", "width": 3},
                "itemStyle": {"color": "#10b981"},
            },
            {
                "name": "밸류매수 (+2,510%)",
                "type": "line",
                "data": s["val"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#f59e0b", "width": 2.2},
                "itemStyle": {"color": "#f59e0b"},
            },
            {
                "name": "무한매수 (+1,980%)",
                "type": "line",
                "data": s["inf"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#c084fc", "width": 2.2},
                "itemStyle": {"color": "#c084fc"},
            },
            {
                "name": "단순보유 (+1,340%)",
                "type": "line",
                "data": s["bh"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#38bdf8", "width": 2},
                "itemStyle": {"color": "#38bdf8"},
            },
        ],
    }
    ui.echart(options).classes("w-full").style("height:320px;")


def _comparison_table_panel(rows: list[dict]):
    """성과 지표 비교 테이블."""
    with ui.card().style(CARD_STYLE).classes("w-full h-full"):
        section_title("성과 지표 비교", "분할매수 우위", "rgba(16,185,129,0.16)", "#34d399")
        headers = ["지표", "단순 보유", "분할매수", "밸류리", "무한매수"]
        with ui.row().classes("w-full py-2.5 px-2 rounded-lg").style(
            "background:rgba(15,23,42,0.85);border:1px solid rgba(148,163,184,0.12);"
        ):
            for h in headers:
                ui.label(h).classes("flex-1 text-center text-xs font-bold").style(
                    f"color:{'#34d399' if h == '분할매수' else '#94a3b8'};"
                )

        with ui.column().classes("w-full gap-2.5 mt-2"):
            for r in rows:
                with ui.row().classes("w-full items-center py-4 px-2 rounded-lg").style(
                    "background:rgba(15,23,42,0.45);border:1px solid rgba(148,163,184,0.08);"
                ):
                    for h in headers:
                        is_hl = h == "분할매수"
                        clr = "#34d399" if is_hl else ("#94a3b8" if h == "지표" else "#f1f5f9")
                        ui.label(r[h]).classes("flex-1 text-center text-sm font-bold num-mono").style(f"color:{clr};")


def create_backtest_page():
    """백테스트 페이지 전체 레이아웃."""
    result = get_backtest_result()

    with ui.column().classes("w-full gap-5 p-6"):
        page_header(
            "백테스트 (Backtest Simulation)",
            "전략별 과거 누적 수익률 · 연평균 성장률(CAGR) · 최대낙폭(MDD) · 샤프지수 검증",
            icon="insights",
            badge_text="CAGR +37.9% · Sharpe 1.11",
            badge_color="#059669",
        )

        with ui.tabs().classes("w-full") as tabs:
            tab_perf = ui.tab("전략별 성과")
            tab_comp = ui.tab("수익률 비교")
            tab_risk = ui.tab("리스크 분석")
            tab_logs = ui.tab("상세 결과")

        with ui.card().style(CARD_STYLE).classes("w-full py-3"):
            with ui.row().classes("w-full items-center justify-between flex-wrap gap-4"):
                with ui.row().classes("items-center gap-3"):
                    ui.icon("date_range", size="18px").style("color:#38bdf8;")
                    ui.label("백테스트 기간").style("color:#94a3b8;font-size:0.85rem;font-weight:700;")
                    ui.input(value="2006-01 ~ 2026-10").props("dense outlined dark").classes("w-48 num-mono")
                with ui.row().classes("items-center gap-4"):
                    ui.label("비교 전략").style("color:#94a3b8;font-size:0.85rem;font-weight:700;")
                    ui.checkbox("단순 보유 (Buy & Hold)", value=True).props("dark dense")
                    ui.checkbox("분할매수 전략", value=True).props("dark dense")
                    ui.checkbox("밸류매수법", value=True).props("dark dense")

                def _on_run():
                    run_id = run_backtest("분할매수 전략", "2006-01", "2026-10")
                    ui.notify(f"백테스트 시뮬레이션 실행 완료 (Run #{run_id})", type="positive")

                ui.button("실행하기", icon="play_arrow", on_click=_on_run).props("unelevated").style(
                    "background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;font-weight:700;padding:6px 18px;border-radius:8px;"
                )

        with ui.tab_panels(tabs, value=tab_perf).classes("w-full"):
            with ui.tab_panel(tab_perf).classes("p-0"):
                with ui.row().classes("w-full gap-4 items-stretch no-wrap"):
                    with ui.column().classes("flex-[6]"):
                        with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                            section_title("누적 수익률 비교", "+3,790% (분할매수)", "rgba(16,185,129,0.16)", "#34d399")
                            _cum_return_echart(result)
                    with ui.column().classes("flex-[4]").style("min-width:330px;"):
                        _comparison_table_panel(result["comparison_table"])

            with ui.tab_panel(tab_comp).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("전략별 장기 누적 수익률 비교 (2006~2026)", "20년 시뮬레이션")
                    _cum_return_echart(result)

            with ui.tab_panel(tab_risk).classes("p-0"):
                _comparison_table_panel(result["comparison_table"])

            with ui.tab_panel(tab_logs).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("백테스트 최근 거래 로그 (SQLite DB 조회)", f"총 {len(result['trades'])}건")
                    cols = [
                        {"name": "trade_date", "label": "거래일", "field": "trade_date", "align": "left"},
                        {"name": "symbol",     "label": "종목",   "field": "symbol",     "align": "center"},
                        {"name": "side",       "label": "구분",   "field": "side",       "align": "center"},
                        {"name": "quantity",   "label": "수량",   "field": "quantity",   "align": "right"},
                        {"name": "price",      "label": "체결가($)", "field": "price",   "align": "right"},
                        {"name": "fee",        "label": "수수료($)", "field": "fee",     "align": "right"},
                    ]
                    ui.table(columns=cols, rows=result["trades"], row_key="id").classes("w-full")
