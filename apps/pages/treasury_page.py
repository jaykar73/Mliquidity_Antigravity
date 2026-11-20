"""
06. TQQQ Lab — 미국 국채 금리 (Spot Rate) 페이지 UI (프리미엄 다크 테마 + EChart)
"""
from nicegui import ui
from conf.config import COLORS
from utils.ui_theme import CARD_STYLE, kpi_card, page_header, section_title
from apps.funcs.treasury_func import (
    get_treasury_kpi,
    get_treasury_history,
    get_treasury_spread,
    get_yield_curve,
)


def _spot_trend_echart(hist: dict):
    """국채 스팟 금리 추이 (5년) EChart."""
    options = {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "rgba(15, 23, 42, 0.94)",
            "textStyle": {"color": "#f8fafc"},
        },
        "legend": {
            "data": ["5년 스팟", "10년 스팟", "30년 스팟"],
            "top": 0,
            "textStyle": {"color": "#cbd5e1", "fontSize": 12},
        },
        "grid": {"left": "8%", "right": "4%", "top": "15%", "bottom": "10%"},
        "xAxis": {
            "type": "category",
            "data": hist["dates"],
            "axisLabel": {"color": "#94a3b8"},
        },
        "yAxis": {
            "type": "value",
            "min": 3.0,
            "max": 6.0,
            "axisLabel": {"color": "#94a3b8", "formatter": "{value}%"},
            "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.08)"}},
        },
        "series": [
            {
                "name": "5년 스팟",
                "type": "line",
                "data": hist["5y"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#38bdf8", "width": 2.2},
                "itemStyle": {"color": "#38bdf8"},
            },
            {
                "name": "10년 스팟",
                "type": "line",
                "data": hist["10y"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#f59e0b", "width": 2.4},
                "itemStyle": {"color": "#f59e0b"},
            },
            {
                "name": "30년 스팟",
                "type": "line",
                "data": hist["30y"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#c084fc", "width": 2.2},
                "itemStyle": {"color": "#c084fc"},
            },
        ],
    }
    ui.echart(options).classes("w-full").style("height:320px;")


def _yield_curve_echart(yc: dict):
    """수익률 곡선 (스팟, 현재) EChart."""
    options = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis"},
        "grid": {"left": "11%", "right": "6%", "top": "14%", "bottom": "10%"},
        "xAxis": {
            "type": "category",
            "data": yc["maturities"],
            "axisLabel": {"color": "#94a3b8"},
        },
        "yAxis": {
            "type": "value",
            "min": 4.0,
            "max": 5.75,
            "axisLabel": {"color": "#94a3b8", "formatter": "{value}%"},
            "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.08)"}},
        },
        "series": [
            {
                "name": "현재 스팟 금리",
                "type": "line",
                "data": yc["rates"],
                "smooth": True,
                "symbolSize": 8,
                "label": {
                    "show": True,
                    "position": "top",
                    "color": "#f8fafc",
                    "formatter": "{c}%",
                    "fontSize": 11,
                },
                "lineStyle": {"color": "#38bdf8", "width": 3},
                "itemStyle": {"color": "#38bdf8"},
                "areaStyle": {"color": "rgba(56,189,248,0.18)"},
            }
        ],
    }
    ui.echart(options).classes("w-full").style("height:320px;")


def _spread_echart(spread: dict):
    """금리 스프레드 (10Y-5Y, 30Y-10Y) EChart."""
    options = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": ["10년 − 5년", "30년 − 10년"],
            "top": 0,
            "textStyle": {"color": "#cbd5e1"},
        },
        "grid": {"left": "8%", "right": "4%", "top": "14%", "bottom": "10%"},
        "xAxis": {
            "type": "category",
            "data": spread["dates"],
            "axisLabel": {"color": "#94a3b8"},
        },
        "yAxis": {
            "type": "value",
            "axisLabel": {"color": "#94a3b8", "formatter": "{value}%p"},
            "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.08)"}},
        },
        "series": [
            {
                "name": "10년 − 5년",
                "type": "line",
                "data": spread["10y_5y"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#38bdf8", "width": 2.5},
                "itemStyle": {"color": "#38bdf8"},
            },
            {
                "name": "30년 − 10년",
                "type": "line",
                "data": spread["30y_10y"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#10b981", "width": 2.5},
                "itemStyle": {"color": "#10b981"},
            },
        ],
    }
    ui.echart(options).classes("w-full").style("height:320px;")


def create_treasury_page():
    """미국 국채 금리 (Spot Rate) 페이지 전체 레이아웃."""
    kpi = get_treasury_kpi()
    hist = get_treasury_history()
    spread = get_treasury_spread()
    yc = get_yield_curve()

    r10_val = kpi["10y"]["rate"]
    r10_chg = kpi["10y"]["change"]
    s10_5_val = kpi["10y_5y"]["spread"]
    s30_10_val = kpi["30y_10y"]["spread"]

    with ui.column().classes("w-full gap-5 page-container"):
        page_header(
            "미국 국채 금리 (Spot Rate)",
            "미국 재무부 5년·10년·30년 제로쿠폰 스팟 금리 · 수익률 곡선(Yield Curve) · 장단기 금리 스프레드",
            icon="show_chart",
            badge_text=f"10Y {r10_val:.2f}% ({r10_chg:+.2f}%p)",
            badge_color="#2563eb",
        )

        with ui.tabs().props("mobile-arrows outside-arrows").classes("w-full") as tabs:
            tab_ov = ui.tab("개요")
            tab_tr = ui.tab("금리 추이")
            tab_yc = ui.tab("수익률 곡선")
            tab_sp = ui.tab("금리 스프레드")

        with ui.element("div").classes("kpi-grid-5"):
            kpi_card("5년 스팟", f"{kpi['5y']['rate']:.2f}%", f"{kpi['5y']['change']:+.2f}%p", "down" if kpi["5y"]["change"] <= 0 else "up", False, "looks_5", "#38bdf8")
            kpi_card("10년 스팟", f"{r10_val:.2f}%", f"{r10_chg:+.2f}%p", "down" if r10_chg <= 0 else "up", False, "timeline", "#f59e0b")
            kpi_card("30년 스팟", f"{kpi['30y']['rate']:.2f}%", f"{kpi['30y']['change']:+.2f}%p", "down" if kpi["30y"]["change"] <= 0 else "up", False, "public", "#c084fc")
            kpi_card("10년 − 5년", f"{s10_5_val:+.2f}%p", "정상 스프레드" if s10_5_val >= 0 else "장단기 역전", "up" if s10_5_val >= 0 else "down", True, "compare_arrows", "#10b981")
            kpi_card("30년 − 10년", f"{s30_10_val:+.2f}%p", "기간 프리미엄", "up" if s30_10_val >= 0 else "down", True, "swap_horiz", "#10b981")

        with ui.tab_panels(tabs, value=tab_ov).classes("w-full"):
            with ui.tab_panel(tab_ov).classes("p-0"):
                with ui.row().classes("w-full gap-4 items-stretch responsive-row"):
                    with ui.column().classes("flex-[6] min-w-0"):
                        with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                            section_title("국채 스팟 금리 추이 (5년)", "5Y · 10Y · 30Y")
                            _spot_trend_echart(hist)
                    with ui.column().classes("flex-[4] min-w-0").style("min-width:260px;"):
                        with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                            section_title("수익률 곡선 (스팟, 현재)", "3M ~ 30Y", "rgba(56,189,248,0.16)", "#38bdf8")
                            _yield_curve_echart(yc)

            with ui.tab_panel(tab_tr).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("미국 국채 5년·10년·30년 스팟 제로쿠폰 금리 추이", "5년 시계열")
                    _spot_trend_echart(hist)

            with ui.tab_panel(tab_yc).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("만기별 미국 국채 스팟 수익률 곡선", "Yield Curve")
                    _yield_curve_echart(yc)

            with ui.tab_panel(tab_sp).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("장단기 금리 스프레드 (10Y−5Y, 30Y−10Y)", f"{s10_5_val:+.2f}%p / {s30_10_val:+.2f}%p", "rgba(16,185,129,0.16)", "#34d399")
                    _spread_echart(spread)
