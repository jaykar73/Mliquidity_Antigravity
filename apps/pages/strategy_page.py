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
    get_signal_score,
    save_strategy,
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

        @ui.refreshable
        def render_weight_tab():
            curr = strategies[selected_idx["value"]] if strategies else {}
            alloc = curr.get("allocation", [])
            sig = get_signal_score()
            capital_state = {"amount": 5000}

            with ui.row().classes("w-full gap-4 items-stretch responsive-row"):
                with ui.column().classes("flex-[6] min-w-0"):
                    with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                        section_title(f"포트폴리오 자산 배분 계산기 — {curr.get('name', '')}", curr.get("profile", "성장형"))
                        with ui.row().classes("w-full items-center gap-3 mb-3 flex-wrap"):
                            ui.label("총 운용 자금 (만원):").style("color:#94a3b8;font-size:0.86rem;font-weight:700;")
                            cap_input = ui.number(value=5000, min=100, step=500, format="%.0f").props("outlined dark dense").classes("w-40 num-mono")
                            ui.button("배분 금액 재계산", icon="calculate", on_click=lambda: (capital_state.update(amount=float(cap_input.value or 5000)), alloc_table_view.refresh())).props("unelevated color=primary dense").classes("px-3")

                        @ui.refreshable
                        def alloc_table_view():
                            tot = capital_state["amount"]
                            with ui.column().classes("w-full gap-2.5"):
                                for a in alloc:
                                    amt = round(tot * (float(a["ratio"]) / 100.0), 1)
                                    with ui.row().classes("w-full items-center justify-between p-3 rounded-xl").style(
                                        "background:rgba(15,23,42,0.55);border:1px solid rgba(148,163,184,0.12);"
                                    ):
                                        with ui.row().classes("items-center gap-2.5"):
                                            ui.element("div").style(f"width:12px;height:12px;border-radius:50%;background:{a['color']};")
                                            ui.label(a["asset"]).style("color:#f1f5f9;font-size:0.95rem;font-weight:700;width:70px;")
                                            ui.badge(f"목표 비중 {a['ratio']}%").classes("num-mono").style("background:rgba(56,189,248,0.15);color:#38bdf8;font-weight:700;")
                                        ui.label(f"{amt:,.0f} 만원").classes("num-mono").style("color:#34d399;font-size:1.0rem;font-weight:800;")

                        alloc_table_view()

                with ui.column().classes("flex-[4] min-w-0"):
                    with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                        section_title("5대 퀀트 팩터별 시그널 점수", f"종합 {sig['score']}점", "rgba(16,185,129,0.16)", "#34d399")
                        with ui.column().classes("w-full gap-3 mt-2"):
                            for d in sig.get("details", []):
                                sc = int(d["score"])
                                clr = "#10b981" if sc >= 70 else ("#38bdf8" if sc >= 55 else "#f59e0b")
                                with ui.column().classes("w-full gap-1"):
                                    with ui.row().classes("w-full justify-between"):
                                        ui.label(d["name"]).style("color:#e2e8f0;font-size:0.84rem;font-weight:600;")
                                        ui.label(f"{sc} / 100").classes("num-mono").style(f"color:{clr};font-size:0.84rem;font-weight:800;")
                                    with ui.element("div").classes("w-full").style("height:8px;background:rgba(15,23,42,0.85);border-radius:4px;overflow:hidden;"):
                                        ui.element("div").style(f"width:{sc}%;height:100%;background:{clr};border-radius:4px;")

        @ui.refreshable
        def render_simulation_tab():
            curr = strategies[selected_idx["value"]] if strategies else {}
            sim_params = {"init_cap": 1000.0, "monthly_add": 100.0, "years": 10, "cagr": 28.0}

            with ui.card().style(CARD_STYLE).classes("w-full"):
                section_title(f"적립식 분할매수 복리 성장 시뮬레이터 — {curr.get('name', '')}", "Compound Simulator")
                with ui.row().classes("w-full items-center gap-3 mb-3 flex-wrap"):
                    in_init = ui.number(label="초기 거치금 (만원)", value=1000, min=0, step=100).props("outlined dark dense").classes("w-36 num-mono")
                    in_mon = ui.number(label="월 적립금 (만원)", value=100, min=0, step=10).props("outlined dark dense").classes("w-36 num-mono")
                    in_yrs = ui.number(label="투자 기간 (년)", value=10, min=1, max=25, step=1).props("outlined dark dense").classes("w-32 num-mono")
                    in_cagr = ui.number(label="기대 연수익률 (%)", value=28.0, min=5.0, max=60.0, step=1.0).props("outlined dark dense").classes("w-36 num-mono")

                    def _run_sim():
                        sim_params["init_cap"] = float(in_init.value or 1000)
                        sim_params["monthly_add"] = float(in_mon.value or 100)
                        sim_params["years"] = max(1, min(25, int(in_yrs.value or 10)))
                        sim_params["cagr"] = float(in_cagr.value or 28.0)
                        sim_chart_box.refresh()

                    ui.button("시뮬레이션 계산", icon="play_arrow", on_click=_run_sim).props("unelevated color=primary").classes("px-4")

                @ui.refreshable
                def sim_chart_box():
                    yrs = sim_params["years"]
                    r_yr = sim_params["cagr"] / 100.0
                    r_mo = (1.0 + r_yr) ** (1.0 / 12.0) - 1.0
                    x_labels = [f"{y}년차" for y in range(0, yrs + 1)]
                    principal_arr = []
                    total_arr = []
                    bal = sim_params["init_cap"]
                    prin = sim_params["init_cap"]
                    principal_arr.append(round(prin, 0))
                    total_arr.append(round(bal, 0))
                    for _ in range(1, yrs + 1):
                        for _ in range(12):
                            bal = bal * (1.0 + r_mo) + sim_params["monthly_add"]
                            prin += sim_params["monthly_add"]
                        principal_arr.append(round(prin, 0))
                        total_arr.append(round(bal, 0))

                    with ui.row().classes("w-full gap-4 mb-2 flex-wrap"):
                        ui.badge(f"총 투입 원금: {int(principal_arr[-1]):,} 만원").classes("num-mono").style("background:rgba(148,163,184,0.18);color:#e2e8f0;padding:6px 12px;font-size:0.82rem;font-weight:700;")
                        ui.badge(f"예상 최종 평가자산: {int(total_arr[-1]):,} 만원").classes("num-mono").style("background:rgba(16,185,129,0.2);color:#34d399;padding:6px 12px;font-size:0.85rem;font-weight:800;")

                    opts = {
                        "backgroundColor": "transparent",
                        "tooltip": {"trigger": "axis", "confine": True},
                        "legend": {"data": ["예상 평가자산(만원)", "누적 투입원금(만원)"], "top": 0, "textStyle": {"color": "#cbd5e1"}},
                        "grid": {"left": "3%", "right": "3%", "top": "15%", "bottom": "6%", "containLabel": True},
                        "xAxis": {"type": "category", "data": x_labels, "axisLabel": {"color": "#94a3b8"}},
                        "yAxis": {"type": "value", "axisLabel": {"color": "#94a3b8"}, "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.08)"}}},
                        "series": [
                            {"name": "예상 평가자산(만원)", "type": "line", "data": total_arr, "smooth": True, "lineStyle": {"color": "#10b981", "width": 3}, "itemStyle": {"color": "#10b981"}, "areaStyle": {"color": "rgba(16,185,129,0.18)"}},
                            {"name": "누적 투입원금(만원)", "type": "line", "data": principal_arr, "smooth": True, "lineStyle": {"color": "#38bdf8", "width": 2, "type": "dashed"}, "itemStyle": {"color": "#38bdf8"}},
                        ],
                    }
                    ui.echart(opts).classes("w-full echart-box").style("height:290px;")

                sim_chart_box()

        with ui.tab_panels(tabs, value=tab_ov).classes("w-full"):
            with ui.tab_panel(tab_ov).classes("p-0"):
                render_main_content()
            with ui.tab_panel(tab_rl).classes("p-0"):
                render_main_content()
            with ui.tab_panel(tab_wt).classes("p-0"):
                render_weight_tab()
            with ui.tab_panel(tab_sm).classes("p-0"):
                render_simulation_tab()
