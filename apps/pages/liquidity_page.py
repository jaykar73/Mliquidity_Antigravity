"""
02. TQQQ Lab — 시장 유동성 (Liquidity) 페이지 UI (프리미엄 다크 테마 + EChart)
"""
from nicegui import ui
from conf.config import COLORS
from utils.ui_theme import CARD_STYLE, kpi_card, page_header, section_title
from apps.funcs.liquidity_func import (
    get_liquidity_kpi,
    get_fed_liquidity_chart_data,
    get_m2_chart_data,
    get_mmf_chart_data,
    get_liquidity_summary_table,
)


def _fed_liquidity_echart(data: dict):
    """Fed 순유동성 추이 (최근 5년) Area Line EChart."""
    options = {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "rgba(15, 23, 42, 0.94)",
            "borderColor": "rgba(56, 189, 248, 0.3)",
            "textStyle": {"color": "#f8fafc"},
        },
        "legend": {
            "data": ["Fed 순유동성(조$)", "연준 자산(WALCL)"],
            "top": 0,
            "textStyle": {"color": "#cbd5e1", "fontSize": 12},
        },
        "grid": {"left": "7%", "right": "4%", "top": "14%", "bottom": "10%"},
        "xAxis": {
            "type": "category",
            "data": data["dates"],
            "axisLine": {"lineStyle": {"color": "rgba(148,163,184,0.2)"}},
            "axisLabel": {"color": "#94a3b8"},
        },
        "yAxis": {
            "type": "value",
            "min": 4.0,
            "max": 8.0,
            "axisLabel": {"color": "#94a3b8", "formatter": "{value}조"},
            "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.08)"}},
        },
        "series": [
            {
                "name": "Fed 순유동성(조$)",
                "type": "line",
                "data": data["net_liquidity"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#38bdf8", "width": 3},
                "itemStyle": {"color": "#38bdf8"},
                "areaStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(56,189,248,0.38)"},
                            {"offset": 1, "color": "rgba(56,189,248,0.02)"},
                        ],
                    }
                },
            },
            {
                "name": "연준 자산(WALCL)",
                "type": "line",
                "data": data["fed_assets"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#10b981", "width": 1.8, "type": "dashed"},
                "itemStyle": {"color": "#10b981"},
            },
        ],
    }
    ui.echart(options).classes("w-full").style("height:320px;")


def _m2_echart(data: dict):
    """M2 통화량 & YoY 증가율 EChart."""
    options = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": ["M2 통화량(조$)", "M2 YoY(%)"],
            "top": 0,
            "textStyle": {"color": "#cbd5e1"},
        },
        "grid": {"left": "7%", "right": "7%", "top": "14%", "bottom": "10%"},
        "xAxis": {
            "type": "category",
            "data": data["dates"],
            "axisLabel": {"color": "#94a3b8"},
        },
        "yAxis": [
            {"type": "value", "name": "조$", "min": 18, "max": 23, "axisLabel": {"color": "#94a3b8"}},
            {"type": "value", "name": "YoY(%)", "position": "right", "axisLabel": {"color": "#94a3b8"}},
        ],
        "series": [
            {
                "name": "M2 통화량(조$)",
                "type": "bar",
                "yAxisIndex": 0,
                "data": data["m2"],
                "itemStyle": {"color": "rgba(56,189,248,0.45)", "borderRadius": [4, 4, 0, 0]},
            },
            {
                "name": "M2 YoY(%)",
                "type": "line",
                "yAxisIndex": 1,
                "data": data["m2_yoy"],
                "smooth": True,
                "lineStyle": {"color": "#10b981", "width": 2.5},
                "itemStyle": {"color": "#10b981"},
            },
        ],
    }
    ui.echart(options).classes("w-full").style("height:320px;")


def _mmf_echart(data: dict, mode: str = "mmf"):
    """MMF 잔액 또는 지급준비금 추이 EChart."""
    y_vals = data["mmf_total"] if mode == "mmf" else data["reserves"]
    title = "MMF 잔액 (조$)" if mode == "mmf" else "지급준비금 (조$)"
    clr = "#f59e0b" if mode == "mmf" else "#a855f7"
    options = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis"},
        "grid": {"left": "7%", "right": "4%", "top": "12%", "bottom": "10%"},
        "xAxis": {
            "type": "category",
            "data": data["dates"],
            "axisLabel": {"color": "#94a3b8"},
        },
        "yAxis": {
            "type": "value",
            "axisLabel": {"color": "#94a3b8", "formatter": "{value}조"},
            "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.08)"}},
        },
        "series": [
            {
                "name": title,
                "type": "line",
                "data": y_vals,
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": clr, "width": 2.8},
                "itemStyle": {"color": clr},
                "areaStyle": {"color": "rgba(245,158,11,0.16)"},
            }
        ],
    }
    ui.echart(options).classes("w-full").style("height:320px;")


def _summary_card(rows: list[dict]):
    """유동성 요약 우측 패널."""
    with ui.card().style(CARD_STYLE).classes("w-full h-full"):
        section_title("유동성 요약", "주간 변화", "rgba(16,185,129,0.15)", "#34d399")
        with ui.row().classes("w-full justify-between py-2.5 px-3 rounded-lg").style(
            "background:rgba(15,23,42,0.75);border:1px solid rgba(148,163,184,0.1);"
        ):
            ui.label("지표").style("color:#94a3b8;font-size:0.8rem;font-weight:700;")
            ui.label("변화(주간)").style("color:#94a3b8;font-size:0.8rem;font-weight:700;")

        with ui.column().classes("w-full gap-2 mt-2"):
            for r in rows:
                is_up = r.get("direction") == "up"
                clr = "#34d399" if is_up else "#fb7185"
                bg = "rgba(16,185,129,0.12)" if is_up else "rgba(244,63,94,0.12)"
                with ui.row().classes("w-full items-center justify-between py-3 px-3 rounded-lg").style(
                    "background:rgba(15,23,42,0.45);border:1px solid rgba(148,163,184,0.08);"
                ):
                    with ui.column().classes("gap-0"):
                        ui.label(r["지표"]).style("color:#f1f5f9;font-size:0.9rem;font-weight:700;")
                        ui.label(r.get("현재값", "")).classes("num-mono").style("color:#64748b;font-size:0.76rem;")
                    ui.badge(r["변화(주간)"]).classes("num-mono").style(
                        f"background:{bg};color:{clr};font-size:0.82rem;font-weight:700;padding:4px 10px;border-radius:9999px;"
                    )


def create_liquidity_page():
    """시장 유동성 페이지 전체 레이아웃."""
    kpi = get_liquidity_kpi()
    fed_data = get_fed_liquidity_chart_data()
    m2_data = get_m2_chart_data()
    mmf_data = get_mmf_chart_data()
    summary = get_liquidity_summary_table()

    with ui.column().classes("w-full gap-5 page-container"):
        page_header(
            "시장 유동성 (Liquidity)",
            "Fed 순유동성 (WALCL − TGA − ON RRP) · M2 통화량 · MMF 잔액 · 지급준비금 추적",
            icon="water_drop",
            badge_text="FRED 공식 지표",
            badge_color="#2563eb",
        )

        with ui.tabs().props("mobile-arrows outside-arrows").classes("w-full") as tabs:
            tab_ov = ui.tab("개요")
            tab_fed = ui.tab("Fed 순유동성")
            tab_m2 = ui.tab("M2 통화량")
            tab_mmf = ui.tab("MMF")
            tab_res = ui.tab("지급준비금")

        kpi_meta = [
            ("Fed 순유동성", "fed_net_liquidity", "water_drop",      "#38bdf8"),
            ("M2 (YoY)",    "m2_yoy",            "payments",        "#10b981"),
            ("MMF 잔액",     "mmf_balance",       "savings",         "#f59e0b"),
            ("지급준비금",    "reserves",          "account_balance", "#a855f7"),
        ]
        with ui.element("div").classes("kpi-grid-4"):
            for label, key, ic, acc in kpi_meta:
                d = kpi.get(key, {"value": "-", "change": "-", "direction": "flat"})
                kpi_card(label, d["value"], d["change"], d.get("direction", "flat"), d.get("highlight", False), ic, acc)

        fed_val = kpi["fed_net_liquidity"]["value"]
        m2_val = kpi["m2_yoy"]["value"]
        mmf_val = kpi["mmf_balance"]["value"]
        res_val = kpi["reserves"]["value"]

        with ui.tab_panels(tabs, value=tab_ov).classes("w-full"):
            with ui.tab_panel(tab_ov).classes("p-0"):
                with ui.row().classes("w-full gap-4 items-stretch responsive-row"):
                    with ui.column().classes("flex-[7] min-w-0"):
                        with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                            section_title("Fed 순유동성 추이 (최근 5년)", fed_val, "rgba(56,189,248,0.18)", "#38bdf8")
                            _fed_liquidity_echart(fed_data)
                    with ui.column().classes("flex-[3] min-w-0").style("min-width:260px;"):
                        _summary_card(summary)

            with ui.tab_panel(tab_fed).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("Fed 순유동성 구성요소 (WALCL − TGA − ON RRP)", fed_val)
                    _fed_liquidity_echart(fed_data)

            with ui.tab_panel(tab_m2).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("M2 통화량 & YoY 증가율 추이", f"{m2_val} YoY", "rgba(16,185,129,0.16)", "#34d399")
                    _m2_echart(m2_data)

            with ui.tab_panel(tab_mmf).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("MMF 머니마켓펀드 잔액 추이", mmf_val, "rgba(245,158,11,0.16)", "#fbbf24")
                    _mmf_echart(mmf_data, "mmf")

            with ui.tab_panel(tab_res).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("연준 지급준비금 (WRESBAL) 추이", res_val, "rgba(168,85,247,0.16)", "#c084fc")
                    _mmf_echart(mmf_data, "res")
