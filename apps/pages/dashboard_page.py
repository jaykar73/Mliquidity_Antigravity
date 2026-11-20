"""
01. TQQQ Lab — 대시보드 페이지 UI (프리미엄 핀테크 다크 테마 + EChart)
"""
from nicegui import ui
from conf.config import COLORS
from utils.ui_theme import CARD_STYLE, kpi_card, page_header, section_title
from apps.funcs.dashboard_func import (
    get_dashboard_kpi,
    get_nasdaq_chart_data,
    get_investment_signal_score,
)


def _nasdaq_echart(data: dict):
    """나스닥100 지수 & 주요 지표 추이 (5년) EChart."""
    ndx_vals = data.get("nasdaq100") or [12000, 25000]
    ndx_max = max(26000, int((max(ndx_vals) * 1.06) // 1000 * 1000 + 1000))
    options = {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "rgba(15, 23, 42, 0.94)",
            "borderColor": "rgba(56, 189, 248, 0.3)",
            "textStyle": {"color": "#f8fafc", "fontSize": 12},
            "confine": True,
        },
        "legend": {
            "data": ["나스닥100", "Fed 순유동성(조$)", "Forward PER(배)"],
            "top": 2,
            "textStyle": {"color": "#cbd5e1", "fontSize": 11},
        },
        "grid": {"left": "2%", "right": "2%", "top": "16%", "bottom": "4%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": data["dates"],
            "axisLine": {"lineStyle": {"color": "rgba(148,163,184,0.2)"}},
            "axisLabel": {"color": "#94a3b8", "fontSize": 11},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "나스닥100",
                "nameTextStyle": {"color": "#64748b"},
                "min": 8000,
                "max": ndx_max,
                "axisLabel": {"color": "#94a3b8", "fontSize": 11},
                "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.08)"}},
            },
            {
                "type": "value",
                "name": "PER / 유동성",
                "nameTextStyle": {"color": "#64748b"},
                "min": 4,
                "max": 34,
                "position": "right",
                "axisLabel": {"color": "#94a3b8", "fontSize": 11},
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "나스닥100",
                "type": "line",
                "yAxisIndex": 0,
                "data": data["nasdaq100"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#38bdf8", "width": 3},
                "itemStyle": {"color": "#38bdf8"},
                "areaStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(56,189,248,0.32)"},
                            {"offset": 1, "color": "rgba(56,189,248,0.01)"},
                        ],
                    }
                },
            },
            {
                "name": "Fed 순유동성(조$)",
                "type": "line",
                "yAxisIndex": 1,
                "data": data["fed_liquidity"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#10b981", "width": 2.2},
                "itemStyle": {"color": "#10b981"},
            },
            {
                "name": "Forward PER(배)",
                "type": "line",
                "yAxisIndex": 1,
                "data": data["forward_per"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#f59e0b", "width": 2.2},
                "itemStyle": {"color": "#f59e0b"},
            },
        ],
    }
    ui.echart(options).classes("w-full echart-box").style("height:355px;")


def _signal_panel(signal: dict):
    """종합 투자 신호 카드 (게이지 + 5대 핵심 근거)."""
    score = signal.get("score", 72)
    rec = signal.get("recommendation", "TQQQ: 분할매수 유리")
    bullets = signal.get("bullets") or [
        {"label": "유동성: 개선 (+1.5%)", "status": "good"},
        {"label": "실적(EPS): 성장 (+2.1%)", "status": "good"},
        {"label": "밸류에이션: 낮은 수준 (18.07배)", "status": "good"},
        {"label": "공포탐욕: 극단적 공포 (22)", "status": "good"},
        {"label": "금리: 10년 4.90% (안정)", "status": "warn"},
    ]

    with ui.card().style(CARD_STYLE).classes("w-full h-full justify-between"):
        section_title("종합 투자 신호", "QUANT SIGNAL", "rgba(16,185,129,0.16)", "#34d399")

        with ui.row().classes("w-full justify-center my-1"):
            ui.badge(rec).style(
                "background:linear-gradient(135deg,#059669 0%,#10b981 100%);color:#ffffff;"
                "font-size:0.92rem;font-weight:800;padding:8px 20px;border-radius:9999px;"
                "box-shadow:0 4px 14px rgba(16,185,129,0.35);"
            )

        gauge_opts = {
            "backgroundColor": "transparent",
            "series": [
                {
                    "type": "gauge",
                    "startAngle": 90,
                    "endAngle": -270,
                    "min": 0,
                    "max": 100,
                    "radius": "84%",
                    "pointer": {"show": False},
                    "progress": {
                        "show": True,
                        "overlap": False,
                        "roundCap": True,
                        "clip": False,
                        "itemStyle": {"color": "#10b981"},
                    },
                    "axisLine": {
                        "lineStyle": {
                            "width": 12,
                            "color": [[1, "rgba(148,163,184,0.12)"]],
                        }
                    },
                    "splitLine": {"show": False},
                    "axisTick": {"show": False},
                    "axisLabel": {"show": False},
                    "data": [{"value": score}],
                    "detail": {
                        "width": 70,
                        "height": 24,
                        "fontSize": 26,
                        "fontWeight": "bold",
                        "color": "#34d399",
                        "formatter": "{value}\n/ 100",
                        "offsetCenter": [0, "0%"],
                    },
                }
            ],
        }
        ui.echart(gauge_opts).classes("w-full").style("height:145px;")

        with ui.column().classes("w-full gap-2 mt-1"):
            for b in bullets:
                dot_clr = "#10b981" if b.get("status") == "good" else "#f59e0b"
                with ui.row().classes("w-full items-center gap-2.5 px-3 py-1.5 rounded-lg").style(
                    "background:rgba(15,23,42,0.6);border:1px solid rgba(148,163,184,0.08);"
                ):
                    ui.icon("check_circle", size="16px").style(f"color:{dot_clr};")
                    ui.label(b["label"]).style("color:#e2e8f0;font-size:0.83rem;font-weight:600;")


def create_dashboard_page():
    """대시보드 페이지 렌더링."""
    kpi = get_dashboard_kpi()
    chart_data = get_nasdaq_chart_data("NDX")
    signal = get_investment_signal_score()

    with ui.column().classes("w-full gap-5 page-container"):
        page_header(
            "나스닥100 / TQQQ 투자 대시보드",
            "연준 유동성 · 컨센서스 EPS · Forward PER · CNN 공포탐욕 · 국채 금리 통합 시그널",
            icon="space_dashboard",
            badge_text=f"{signal.get('recommendation', 'TQQQ 분할매수 유리')} ({signal.get('score', 72)}점)",
            badge_color="#059669" if signal.get("score", 72) >= 65 else "#2563eb",
        )

        # 6대 KPI 카드 그리드 (PC 6열 / 태블릿 3열 / 스마트폰 2열 자동 전환)
        kpi_meta = [
            ("Fed 순유동성", "fed_net_liquidity", False, "water_drop",      "#38bdf8"),
            ("M2 증가율",    "m2_yoy",            True,  "payments",        "#10b981"),
            ("예상 EPS",     "expected_eps",      False, "trending_up",     "#3b82f6"),
            ("Forward PER",  "forward_per",       False, "pie_chart",       "#a855f7"),
            ("CNN 공포탐욕", "cnn_fear_greed",    False, "speed",           "#f43f5e"),
            ("미국채 10년",  "treasury_10y",      False, "account_balance", "#f59e0b"),
        ]
        with ui.element("div").classes("kpi-grid-6"):
            for label, key, hl, ic, acc in kpi_meta:
                d = kpi.get(key, {"value": "-", "change": "-", "direction": "flat"})
                kpi_card(label, d["value"], d["change"], d.get("direction", "flat"), hl, ic, acc)

        # 하단 차트 + 종합 투자 신호 (PC: 좌우 7:3 / 스마트폰·태블릿: 상하 100% 스택)
        with ui.row().classes("w-full gap-4 items-stretch responsive-row"):
            with ui.column().classes("flex-[7] min-w-0"):
                with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                    section_title("나스닥100 지수 & 주요 지표 추이 (5년)", "NDX · 유동성 · PER", "rgba(56,189,248,0.15)", "#38bdf8")
                    _nasdaq_echart(chart_data)

            with ui.column().classes("flex-[3] min-w-0").style("min-width:280px;"):
                _signal_panel(signal)
