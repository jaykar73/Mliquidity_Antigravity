"""
07. TQQQ Lab — 투자 전략 페이지 UI (프리미엄 다크 테마 + EChart)
"""
from nicegui import ui
from conf.config import COLORS
from utils.ui_theme import CARD_STYLE, page_header, section_title
from apps.funcs.strategy_func import (
    get_strategies,
    get_trade_rules,
    get_portfolio_allocation,
)


def _portfolio_donut_echart(alloc: list[dict], profile_label: str = "성장형\n(TQQQ 중심)"):
    """추천 포트폴리오 도넛 EChart."""
    pie_data = [
        {"name": a["asset"], "value": a["ratio"], "itemStyle": {"color": a["color"]}}
        for a in alloc
    ]
    options = {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "item", "formatter": "{b}: {c}%"},
        "title": {
            "text": profile_label,
            "left": "center",
            "top": "38%",
            "textStyle": {"color": "#f8fafc", "fontSize": 13, "fontWeight": "bold"},
        },
        "series": [
            {
                "name": "포트폴리오 비중",
                "type": "pie",
                "radius": ["56%", "82%"],
                "center": ["50%", "48%"],
                "avoidLabelOverlap": False,
                "label": {"show": False},
                "data": pie_data,
            }
        ],
    }
    return ui.echart(options).classes("w-full").style("height:205px;")


def create_strategy_page():
    """투자 전략 페이지 전체 레이아웃."""
    strategies = get_strategies()
    selected_idx = {"value": 0}

    with ui.column().classes("w-full gap-5 page-container"):
        page_header(
            "투자 전략 (Quant Strategy)",
            "매수·매도 조건부 규칙 설정 · 전략별 추천 포트폴리오 자산 비중 · 리밸런싱 가이드",
            icon="track_changes",
            badge_text="분할매수 전략 권장",
            badge_color="#059669",
        )

        with ui.tabs().props("mobile-arrows outside-arrows").classes("w-full") as tabs:
            tab_ov = ui.tab("전략 개요")
            tab_rl = ui.tab("매수·매도 규칙")
            tab_wt = ui.tab("비중 관리")
            tab_sm = ui.tab("시뮬레이션")

        @ui.refreshable
        def render_main_content():
            curr = strategies[selected_idx["value"]] if strategies else {
                "name": "분할매수 전략 (권장)",
                "profile": "성장형 (TQQQ 중심)",
                "rules": get_trade_rules(1),
                "allocation": get_portfolio_allocation(1),
            }
            rules = curr.get("rules", [])
            alloc = curr.get("allocation", [])

            with ui.row().classes("w-full gap-4 items-stretch responsive-row"):
                # 1. 좌측: 전략 선택
                with ui.column().classes("flex-[3] min-w-0").style("min-width:220px;"):
                    with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                        section_title("전략 선택", f"{len(strategies)}종")
                        with ui.column().classes("w-full gap-2 mt-1"):
                            for idx, s in enumerate(strategies):
                                is_sel = idx == selected_idx["value"]
                                bg = "linear-gradient(135deg,rgba(16,185,129,0.20),rgba(15,23,42,0.8))" if is_sel else "rgba(15,23,42,0.5)"
                                bd = "#10b981" if is_sel else "rgba(148,163,184,0.12)"
                                icon_name = "radio_button_checked" if is_sel else "radio_button_unchecked"
                                icon_clr = "#34d399" if is_sel else "#64748b"

                                def _on_select(i=idx):
                                    selected_idx["value"] = i
                                    render_main_content.refresh()

                                with ui.row().classes(
                                    "w-full items-center gap-3 p-3.5 rounded-xl cursor-pointer transition-all"
                                ).style(f"background:{bg};border:1px solid {bd};").on("click", _on_select):
                                    ui.icon(icon_name, size="20px").style(f"color:{icon_clr};")
                                    with ui.column().classes("gap-0 flex-1"):
                                        ui.label(s["name"]).style(
                                            f"color:{'#34d399' if is_sel else '#f1f5f9'};"
                                            f"font-weight:{'800' if is_sel else '600'};font-size:0.9rem;"
                                        )
                                        ui.label(s.get("profile", "")).style("color:#64748b;font-size:0.72rem;")

                # 2. 중앙: 매수·매도 규칙
                with ui.column().classes("flex-[5] min-w-0"):
                    with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                        section_title("매수·매도 규칙 (예시)", curr["name"], "rgba(56,189,248,0.15)", "#38bdf8")
                        if curr.get("desc"):
                            ui.label(curr["desc"]).style("color:#94a3b8;font-size:0.82rem;margin-bottom:8px;")

                        with ui.row().classes("w-full py-2.5 px-3 rounded-lg gt-xs").style(
                            "background:rgba(15,23,42,0.85);border:1px solid rgba(148,163,184,0.12);"
                        ):
                            ui.label("구분").classes("w-28 text-xs font-bold").style("color:#94a3b8;")
                            ui.label("조건").classes("flex-1 text-xs font-bold").style("color:#94a3b8;")
                            ui.label("실행").classes("w-36 text-right text-xs font-bold").style("color:#94a3b8;")

                        badge_colors = {
                            "green":  ("rgba(16,185,129,0.18)", "#34d399"),
                            "blue":   ("rgba(56,189,248,0.18)", "#38bdf8"),
                            "yellow": ("rgba(245,158,11,0.18)", "#fbbf24"),
                            "red":    ("rgba(244,63,94,0.18)",  "#fb7185"),
                        }
                        with ui.column().classes("w-full gap-2 mt-2"):
                            for r in rules:
                                b_bg, b_fg = badge_colors.get(r.get("badge", "blue"), ("rgba(56,189,248,0.18)", "#38bdf8"))
                                with ui.row().classes("w-full items-center py-3 px-3 rounded-lg strategy-rule-row").style(
                                    "background:rgba(15,23,42,0.45);border:1px solid rgba(148,163,184,0.08);"
                                ):
                                    with ui.element("div").classes("w-28"):
                                        ui.badge(r["type"]).style(
                                            f"background:{b_bg};color:{b_fg};font-weight:700;padding:4px 10px;border-radius:6px;"
                                        )
                                    ui.label(f"• {r['condition']}").classes("flex-1 text-sm font-medium").style("color:#e2e8f0;")
                                    ui.label(r["action"]).classes("w-36 text-right text-sm font-bold strategy-rule-action").style(f"color:{b_fg};")

                # 3. 우측: 추천 포트폴리오
                with ui.column().classes("flex-[3] min-w-0").style("min-width:240px;"):
                    with ui.card().style(CARD_STYLE).classes("w-full h-full justify-between"):
                        section_title("추천 포트폴리오", curr.get("profile", "성장형"), "rgba(16,185,129,0.16)", "#34d399")
                        _portfolio_donut_echart(alloc, curr.get("profile", "성장형\n(TQQQ 중심)"))
                        with ui.column().classes("w-full gap-2 mt-1"):
                            for a in alloc:
                                with ui.row().classes("w-full items-center justify-between py-1.5 px-2.5 rounded-lg").style(
                                    "background:rgba(15,23,42,0.5);border:1px solid rgba(148,163,184,0.08);"
                                ):
                                    with ui.row().classes("items-center gap-2"):
                                        ui.element("div").style(
                                            f"width:10px;height:10px;border-radius:50%;background:{a['color']};"
                                        )
                                        ui.label(a["asset"]).style("color:#e2e8f0;font-size:0.86rem;font-weight:600;")
                                    ui.label(f"{a['ratio']}%").classes("num-mono").style(
                                        "color:#f8fafc;font-size:0.9rem;font-weight:800;"
                                    )

        with ui.tab_panels(tabs, value=tab_ov).classes("w-full"):
            for t_obj in (tab_ov, tab_rl, tab_wt, tab_sm):
                with ui.tab_panel(t_obj).classes("p-0"):
                    render_main_content()
