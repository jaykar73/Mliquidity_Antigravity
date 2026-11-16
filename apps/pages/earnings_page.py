"""
03. TQQQ Lab — 기업실적(EPS) 페이지 UI (프리미엄 다크 테마 + EChart)
"""
from nicegui import ui
from conf.config import COLORS
from utils.ui_theme import CARD_STYLE, kpi_card, page_header, section_title
from apps.funcs.earnings_func import (
    get_earnings_kpi,
    get_eps_trend_chart_data,
    get_eps_revision_chart_data,
    get_eps_forecast_table,
)


def _eps_trend_echart(data: dict):
    """나스닥100 예상 EPS (향후 12개월) EChart."""
    options = {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "rgba(15, 23, 42, 0.94)",
            "borderColor": "rgba(16, 185, 129, 0.3)",
            "textStyle": {"color": "#f8fafc"},
        },
        "grid": {"left": "8%", "right": "4%", "top": "12%", "bottom": "10%"},
        "xAxis": {
            "type": "category",
            "data": data["dates"],
            "axisLine": {"lineStyle": {"color": "rgba(148,163,184,0.2)"}},
            "axisLabel": {"color": "#94a3b8"},
        },
        "yAxis": {
            "type": "value",
            "min": 800,
            "max": 1450,
            "axisLabel": {"color": "#94a3b8"},
            "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.08)"}},
        },
        "series": [
            {
                "name": "예상 EPS (NTM)",
                "type": "line",
                "data": data["eps_estimate"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#10b981", "width": 3},
                "itemStyle": {"color": "#10b981"},
                "areaStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(16,185,129,0.38)"},
                            {"offset": 1, "color": "rgba(16,185,129,0.02)"},
                        ],
                    }
                },
            }
        ],
    }
    ui.echart(options).classes("w-full").style("height:320px;")


def _eps_revision_echart(data: dict):
    """EPS Revision 추이 (상향/하향 막대 + 순변화 라인) EChart."""
    options = {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "rgba(15, 23, 42, 0.94)",
            "textStyle": {"color": "#f8fafc"},
        },
        "legend": {
            "data": ["상향", "하향", "순변화"],
            "top": 0,
            "textStyle": {"color": "#cbd5e1", "fontSize": 12},
        },
        "grid": {"left": "11%", "right": "5%", "top": "15%", "bottom": "10%"},
        "xAxis": {
            "type": "category",
            "data": data["months"],
            "axisLine": {"lineStyle": {"color": "rgba(148,163,184,0.2)"}},
            "axisLabel": {"color": "#94a3b8"},
        },
        "yAxis": {
            "type": "value",
            "min": -10,
            "max": 10,
            "axisLabel": {"color": "#94a3b8", "formatter": "{value}%"},
            "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.08)"}},
        },
        "series": [
            {
                "name": "상향",
                "type": "bar",
                "stack": "rev",
                "data": data["up_revision"],
                "itemStyle": {"color": "#10b981", "borderRadius": [4, 4, 0, 0]},
            },
            {
                "name": "하향",
                "type": "bar",
                "stack": "rev",
                "data": data["down_revision"],
                "itemStyle": {"color": "#f43f5e", "borderRadius": [0, 0, 4, 4]},
            },
            {
                "name": "순변화",
                "type": "line",
                "data": data["net_revision"],
                "smooth": True,
                "lineStyle": {"color": "#38bdf8", "width": 2.5},
                "itemStyle": {"color": "#38bdf8"},
            },
        ],
    }
    ui.echart(options).classes("w-full").style("height:320px;")


def create_earnings_page():
    """기업실적(EPS) 페이지 전체 레이아웃."""
    kpi = get_earnings_kpi()
    trend_data = get_eps_trend_chart_data()
    rev_data = get_eps_revision_chart_data()
    forecast_rows = get_eps_forecast_table()

    with ui.column().classes("w-full gap-5 p-6"):
        page_header(
            "기업실적 (EPS)",
            "나스닥100 향후 12개월(NTM) 예상 EPS 추이 · 3개월 추정치 수정률(Revision) · 빅테크 실적 기여도",
            icon="trending_up",
            badge_text="이익 모멘텀 견조",
            badge_color="#059669",
        )

        with ui.tabs().classes("w-full") as tabs:
            tab_ov = ui.tab("개요")
            tab_trend = ui.tab("예상 EPS 추이")
            tab_rev = ui.tab("EPS Revision")
            tab_sec = ui.tab("업종별 EPS")
            tab_top = ui.tab("주요 기업")

        kpi_meta = [
            ("예상 EPS (나스닥100)", "expected_eps",    "analytics",    "#38bdf8"),
            ("EPS Revision (3개월)", "eps_revision_3m", "Upgrade",      "#10b981"),
            ("실적 서프라이즈 (최근)", "eps_surprise",   "stars",        "#a855f7"),
            ("이익 성장률 (예상, YoY)", "eps_growth_yoy","rocket_launch","#f59e0b"),
        ]
        with ui.grid(columns=4).classes("w-full gap-4"):
            for label, key, ic, acc in kpi_meta:
                d = kpi.get(key, {"value": "-", "change": "-", "direction": "up"})
                kpi_card(label, d["value"], d["change"], d.get("direction", "up"), d.get("highlight", False), ic.lower(), acc)

        with ui.tab_panels(tabs, value=tab_ov).classes("w-full"):
            with ui.tab_panel(tab_ov).classes("p-0"):
                with ui.row().classes("w-full gap-4 items-stretch no-wrap"):
                    with ui.column().classes("flex-[6]"):
                        with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                            section_title("나스닥100 예상 EPS (향후 12개월)", "1,378 (+2.1%)", "rgba(16,185,129,0.16)", "#34d399")
                            _eps_trend_echart(trend_data)

                    with ui.column().classes("flex-[4]").style("min-width:310px;"):
                        with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                            section_title("EPS Revision 추이", "+4.7%", "rgba(56,189,248,0.16)", "#38bdf8")
                            _eps_revision_echart(rev_data)

            with ui.tab_panel(tab_trend).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("나스닥100 예상 EPS 장기 시계열 (NTM)", "1,378 pt", "rgba(16,185,129,0.16)", "#34d399")
                    _eps_trend_echart(trend_data)

            with ui.tab_panel(tab_rev).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("월별 EPS 추정치 상향/하향 Revision", "+4.7%")
                    _eps_revision_echart(rev_data)

            for t_obj in (tab_sec, tab_top):
                with ui.tab_panel(t_obj).classes("p-0"):
                    with ui.card().style(CARD_STYLE).classes("w-full"):
                        section_title("나스닥100 주요 빅테크 컨센서스 기여도", "Top 6")
                        cols = [
                            {"name": k, "label": k, "field": k, "align": "left" if k == "종목/섹터" else "right"}
                            for k in ["종목/섹터", "비중", "12M Fwd EPS", "3M 수정률", "서프라이즈"]
                        ]
                        ui.table(columns=cols, rows=forecast_rows, row_key="종목/섹터").classes("w-full")
