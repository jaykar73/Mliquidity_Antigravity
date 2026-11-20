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


def _cum_return_echart(data: dict, active_strats: dict | None = None):
    """누적 수익률 비교 멀티 라인 EChart (체크박스 필터 및 기간 동적 연동)."""
    s = data["series"]
    tg = data.get("targets", {"dca": 3790, "val": 2510, "inf": 1980, "bh": 1340})
    act = active_strats or {"dca": True, "val": True, "inf": True, "bh": True}

    all_series = [
        ("dca", f"분할매수 (+{tg['dca']:,}%)", s["dca"], "#10b981", 3.0),
        ("val", f"밸류매수 (+{tg['val']:,}%)", s["val"], "#f59e0b", 2.2),
        ("inf", f"무한매수 (+{tg['inf']:,}%)", s["inf"], "#c084fc", 2.2),
        ("bh",  f"단순보유 (+{tg['bh']:,}%)",  s["bh"],  "#38bdf8", 2.0),
    ]
    filtered = [item for item in all_series if act.get(item[0], True)] or all_series

    options = {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "rgba(15, 23, 42, 0.94)",
            "textStyle": {"color": "#f8fafc"},
            "confine": True,
        },
        "legend": {
            "data": [item[1] for item in filtered],
            "top": 0,
            "textStyle": {"color": "#cbd5e1", "fontSize": 11},
        },
        "grid": {"left": "3%", "right": "3%", "top": "15%", "bottom": "6%", "containLabel": True},
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
                "name": label,
                "type": "line",
                "data": vals,
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": clr, "width": w},
                "itemStyle": {"color": clr},
            }
            for _, label, vals, clr, w in filtered
        ],
    }
    ui.echart(options).classes("w-full echart-box").style("height:320px;")


def _drawdown_echart(data: dict):
    """전략별 연도별 최대낙폭(Drawdown / MDD) 비교 EChart."""
    dd = data.get("dd_series", {})
    options = {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "rgba(15, 23, 42, 0.94)",
            "textStyle": {"color": "#f8fafc"},
            "confine": True,
        },
        "legend": {
            "data": ["분할매수 MDD", "밸류리밸런싱 MDD", "단순보유 MDD"],
            "top": 0,
            "textStyle": {"color": "#cbd5e1", "fontSize": 11},
        },
        "grid": {"left": "3%", "right": "3%", "top": "15%", "bottom": "6%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": data["years"],
            "axisLabel": {"color": "#94a3b8"},
        },
        "yAxis": {
            "type": "value",
            "max": 0,
            "min": -85,
            "axisLabel": {"color": "#94a3b8", "formatter": "{value}%"},
            "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.08)"}},
        },
        "series": [
            {
                "name": "분할매수 MDD",
                "type": "line",
                "data": dd.get("dca", []),
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#10b981", "width": 2.6},
                "itemStyle": {"color": "#10b981"},
                "areaStyle": {"color": "rgba(16,185,129,0.14)"},
            },
            {
                "name": "밸류리밸런싱 MDD",
                "type": "line",
                "data": dd.get("val", []),
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#f59e0b", "width": 2.0},
                "itemStyle": {"color": "#f59e0b"},
            },
            {
                "name": "단순보유 MDD",
                "type": "line",
                "data": dd.get("bh", []),
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#f43f5e", "width": 2.0, "type": "dashed"},
                "itemStyle": {"color": "#f43f5e"},
            },
        ],
    }
    ui.echart(options).classes("w-full echart-box").style("height:290px;")


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
    """백테스트 페이지 전체 레이아웃 (실시간 기간·전략 필터 및 MDD 리스크 분석 연동)."""
    bt_state = {
        "period": "2006-01 ~ 2026-11",
        "bh": True,
        "dca": True,
        "val": True,
        "inf": True,
    }

    def _parse_period(p_str: str) -> tuple[str, str]:
        parts = [x.strip() for x in p_str.replace("~", " ").split() if x.strip()]
        if len(parts) >= 2:
            return parts[0], parts[-1]
        return "2006-01", "2026-11"

    with ui.column().classes("w-full gap-5 page-container"):
        p_start, p_end = _parse_period(bt_state["period"])
        init_res = get_backtest_result(p_start, p_end)

        page_header(
            "백테스트 (Backtest Simulation)",
            "전략별 과거 누적 수익률 · 연평균 성장률(CAGR) · 최대낙폭(MDD) · 샤프지수 검증",
            icon="insights",
            badge_text=f"CAGR +{init_res['metrics']['cagr']}% · Sharpe {init_res['metrics']['sharpe']}",
            badge_color="#059669",
        )

        with ui.tabs().props("mobile-arrows outside-arrows").classes("w-full") as tabs:
            tab_perf = ui.tab("전략별 성과")
            tab_comp = ui.tab("수익률 비교")
            tab_risk = ui.tab("리스크 분석")
            tab_logs = ui.tab("상세 결과")

        with ui.card().style(CARD_STYLE).classes("w-full py-3"):
            with ui.row().classes("w-full items-center justify-between flex-wrap gap-3"):
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    ui.icon("date_range", size="18px").style("color:#38bdf8;")
                    ui.label("백테스트 기간").style("color:#94a3b8;font-size:0.85rem;font-weight:700;")
                    period_input = ui.input(value=bt_state["period"]).props("dense outlined dark").classes("w-44 num-mono")
                with ui.row().classes("items-center gap-3 flex-wrap"):
                    ui.label("비교 전략").style("color:#94a3b8;font-size:0.85rem;font-weight:700;")
                    cb_bh = ui.checkbox("단순 보유 (Buy & Hold)", value=True).props("dark dense")
                    cb_dca = ui.checkbox("분할매수 전략", value=True).props("dark dense")
                    cb_val = ui.checkbox("밸류매수법", value=True).props("dark dense")
                    cb_inf = ui.checkbox("무한매수법", value=True).props("dark dense")

                def _on_run():
                    bt_state["period"] = period_input.value or "2006-01 ~ 2026-11"
                    bt_state["bh"] = bool(cb_bh.value)
                    bt_state["dca"] = bool(cb_dca.value)
                    bt_state["val"] = bool(cb_val.value)
                    bt_state["inf"] = bool(cb_inf.value)
                    ps, pe = _parse_period(bt_state["period"])
                    run_id = run_backtest("분할매수 전략", ps, pe)
                    render_bt_panels.refresh()
                    ui.notify(f"백테스트 시뮬레이션 실행 완료 ({ps} ~ {pe}, Run #{run_id})", type="positive")

                ui.button("실행하기", icon="play_arrow", on_click=_on_run).props("unelevated").style(
                    "background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;font-weight:700;padding:6px 18px;border-radius:8px;"
                )

        @ui.refreshable
        def render_bt_panels():
            ps, pe = _parse_period(bt_state["period"])
            result = get_backtest_result(ps, pe)
            act_map = {
                "bh": bt_state["bh"],
                "dca": bt_state["dca"],
                "val": bt_state["val"],
                "inf": bt_state["inf"],
            }
            dca_ret = result.get("targets", {}).get("dca", 3790)

            with ui.tab_panels(tabs, value=tab_perf).classes("w-full"):
                with ui.tab_panel(tab_perf).classes("p-0"):
                    with ui.row().classes("w-full gap-4 items-stretch responsive-row"):
                        with ui.column().classes("flex-[6] min-w-0"):
                            with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                                section_title("누적 수익률 비교", f"+{dca_ret:,}% (분할매수)", "rgba(16,185,129,0.16)", "#34d399")
                                _cum_return_echart(result, act_map)
                        with ui.column().classes("flex-[4] min-w-0").style("min-width:260px;"):
                            _comparison_table_panel(result["comparison_table"])

                with ui.tab_panel(tab_comp).classes("p-0"):
                    with ui.card().style(CARD_STYLE).classes("w-full"):
                        section_title(f"전략별 장기 누적 수익률 비교 ({ps} ~ {pe})", f"+{dca_ret:,}%")
                        _cum_return_echart(result, act_map)

                with ui.tab_panel(tab_risk).classes("p-0"):
                    with ui.row().classes("w-full gap-4 items-stretch responsive-row"):
                        with ui.column().classes("flex-[6] min-w-0"):
                            with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                                section_title("연도별 최대낙폭 (Drawdown / MDD) 추이", f"MDD {result['metrics']['mdd']}%", "rgba(244,63,94,0.16)", "#fb7185")
                                _drawdown_echart(result)
                        with ui.column().classes("flex-[4] min-w-0").style("min-width:260px;"):
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

        render_bt_panels()
