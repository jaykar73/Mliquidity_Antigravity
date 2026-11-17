"""
04. TQQQ Lab — 밸류에이션 (Forward PER) 페이지 UI (프리미엄 다크 테마 + EChart + 실시간 데이터 연동)
"""
import asyncio
from nicegui import ui
from conf.config import COLORS
from utils.ui_theme import CARD_STYLE, kpi_card, page_header, section_title
from apps.funcs.valuation_func import (
    get_valuation_kpi,
    get_per_trend_chart_data,
    get_per_distribution_data,
    get_per_analysis_table,
    sync_live_forward_per,
    save_manual_forward_per,
    reset_demo_forward_per,
)


def _per_trend_echart(data: dict):
    """나스닥100 Forward PER 추이 (20년) EChart."""
    avg_val = data["avg_10y"][0] if data.get("avg_10y") else 23.01
    options = {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "rgba(15, 23, 42, 0.94)",
            "borderColor": "rgba(192, 132, 252, 0.35)",
            "textStyle": {"color": "#f8fafc"},
        },
        "legend": {
            "data": ["Forward PER", f"10년 평균 ({avg_val:.2f}배)"],
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
            "min": 10,
            "max": 38,
            "axisLabel": {"color": "#94a3b8"},
            "splitLine": {"lineStyle": {"color": "rgba(148,163,184,0.08)"}},
        },
        "series": [
            {
                "name": "Forward PER",
                "type": "line",
                "data": data["forward_per"],
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"color": "#c084fc", "width": 2.8},
                "itemStyle": {"color": "#c084fc"},
                "areaStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [
                            {"offset": 0, "color": "rgba(192,132,252,0.36)"},
                            {"offset": 1, "color": "rgba(192,132,252,0.02)"},
                        ],
                    }
                },
            },
            {
                "name": f"10년 평균 ({avg_val:.2f}배)",
                "type": "line",
                "data": data["avg_10y"],
                "showSymbol": False,
                "lineStyle": {"color": "#94a3b8", "width": 1.6, "type": "dashed"},
                "itemStyle": {"color": "#94a3b8"},
            },
        ],
    }
    ui.echart(options).classes("w-full").style("height:320px;")


def _per_distribution_panel(dist: dict):
    """PER 분포 (20년) 가로 바 차트."""
    buckets = list(reversed(dist["buckets"]))
    with ui.card().style(CARD_STYLE).classes("w-full h-full"):
        section_title("PER 분포 (20년)", f"현재 {dist.get('current', 18.07):.2f}배", "rgba(245,158,11,0.16)", "#fbbf24")
        with ui.column().classes("w-full gap-2.5 mt-1"):
            for b in buckets:
                is_act = b.get("active", False)
                bar_clr = "linear-gradient(90deg,#f59e0b,#fbbf24)" if is_act else "linear-gradient(90deg,#4f46e5,#6366f1)"
                txt_clr = "#fbbf24" if is_act else "#cbd5e1"
                pct = b["pct"]
                with ui.row().classes("w-full items-center gap-2.5 py-1"):
                    ui.label(b["label"]).classes("w-14 text-xs font-bold num-mono").style(f"color:{txt_clr};")
                    with ui.element("div").classes("flex-1").style(
                        "height:14px;background:rgba(15,23,42,0.75);border-radius:6px;overflow:hidden;"
                        "border:1px solid rgba(148,163,184,0.1);"
                    ):
                        ui.element("div").style(
                            f"width:{min(100, pct * 4.5)}%;height:100%;background:{bar_clr};border-radius:5px;"
                        )
                    ui.label(f"{pct}%").classes("w-10 text-right text-xs font-bold num-mono").style(f"color:{txt_clr};")


def create_valuation_page():
    """밸류에이션(Forward PER) 페이지 전체 레이아웃."""

    @ui.refreshable
    def render_valuation_view():
        kpi = get_valuation_kpi()
        trend_data = get_per_trend_chart_data()
        dist_data = get_per_distribution_data()
        analysis_rows = get_per_analysis_table()
        meta = kpi.get("meta", {})
        status = meta.get("license_status", "DEMO")
        provider = meta.get("provider", "Consensus")
        collected_at = meta.get("collected_at", "")
        curr_per_str = kpi["forward_per"]["value"]

        # ── 수동/계산 연동 다이얼로그 (모바일/PC 반응형 너비) ──
        with ui.dialog() as config_dialog, ui.card().style(
            f"{CARD_STYLE} width: min(92vw, 480px);"
        ):
            ui.label("⚙️ Forward PER 데이터 연동 및 직접 계산").style(
                "color:#f8fafc;font-size:1.15rem;font-weight:800;margin-bottom:4px;"
            )
            ui.label("실시간 외부 소스를 선택하거나 NDX 지수 ÷ 12M 예상 EPS로 직접 계산해 DB에 반영합니다.").style(
                "color:#94a3b8;font-size:0.8rem;margin-bottom:12px;"
            )

            source_select = ui.select(
                options={
                    "auto": "자동 (Yahoo Finance QQQ → Finviz → FRED 순차 연동)",
                    "yahoo": "Yahoo Finance (QQQ Forward P/E 실시간)",
                    "finviz": "Finviz (QQQ / NDX 빅테크 가중 Forward P/E)",
                },
                value="auto",
                label="실시간 수집 소스 선택",
            ).props("outlined dark dense").classes("w-full mb-3")

            async def _run_source_sync():
                ui.notify("선택한 소스에서 데이터를 가져오는 중...", type="info")
                res = await asyncio.to_thread(sync_live_forward_per, source_select.value)
                if res.get("ok"):
                    config_dialog.close()
                    render_valuation_view.refresh()
                    ui.notify(
                        f"연동 완료! Forward PER: {res['forward_per']}배 (출처: {res['provider']})",
                        type="positive",
                    )
                else:
                    ui.notify(res.get("message", "연동 실패"), type="warning")

            ui.button("선택한 소스로 즉시 수집", icon="cloud_download", on_click=_run_source_sync).props(
                "color=primary unelevated"
            ).classes("w-full mb-4")

            ui.separator().style("background:rgba(148,163,184,0.16);margin:8px 0;")
            ui.label("📐 직접 수치 입력 / 지수÷EPS 계산").style(
                "color:#f8fafc;font-size:0.92rem;font-weight:700;margin-top:4px;"
            )

            with ui.row().classes("w-full gap-3 mt-2"):
                ndx_input = ui.number(
                    label="나스닥100 지수 (NDX)", value=21450.0, format="%.1f"
                ).props("outlined dark dense").classes("flex-1")
                eps_input = ui.number(
                    label="12M Forward EPS", value=1187.0, format="%.1f"
                ).props("outlined dark dense").classes("flex-1")

            manual_per_input = ui.number(
                label="또는 Forward PER 직접 입력 (배)",
                value=float(kpi["forward_per"].get("raw", 18.07)),
                format="%.2f",
                step=0.1,
            ).props("outlined dark dense").classes("w-full mt-2")

            def _apply_calc_from_eps():
                res = save_manual_forward_per(
                    ndx_price=ndx_input.value,
                    eps_val=eps_input.value,
                    provider="NDX ÷ 12M Forward EPS (직접 계산)",
                )
                if res.get("ok"):
                    config_dialog.close()
                    render_valuation_view.refresh()
                    ui.notify(f"지수÷EPS 계산 적용 완료: {res['forward_per']}배", type="positive")

            def _apply_direct_per():
                res = save_manual_forward_per(
                    per_val=manual_per_input.value,
                    provider="Manual Input (사용자 지정)",
                )
                if res.get("ok"):
                    config_dialog.close()
                    render_valuation_view.refresh()
                    ui.notify(f"수동 Forward PER 적용 완료: {res['forward_per']}배", type="positive")

            def _restore_demo():
                res = reset_demo_forward_per()
                if res.get("ok"):
                    config_dialog.close()
                    render_valuation_view.refresh()
                    ui.notify("데모 기준값(18.07배)으로 복원되었습니다.", type="info")

            with ui.row().classes("w-full justify-between gap-2 mt-3"):
                ui.button("지수÷EPS로 계산 적용", icon="calculate", on_click=_apply_calc_from_eps).props(
                    "outline color=info dense"
                ).classes("flex-1")
                ui.button("직접 입력값 저장", icon="save", on_click=_apply_direct_per).props(
                    "outline color=positive dense"
                ).classes("flex-1")

            with ui.row().classes("w-full justify-between items-center mt-3"):
                ui.button("데모값(18.07배) 복원", icon="restart_alt", on_click=_restore_demo).props(
                    "flat dense color=grey-5"
                )
                ui.button("닫기", on_click=config_dialog.close).props("flat dense color=grey-4")

        # ── 상단 타이틀 & 실시간 연동 액션 바 ──
        with ui.row().classes("w-full items-center justify-between flex-wrap gap-3"):
            badge_bg = "#059669" if status == "LIVE" else ("#2563eb" if status == "CUSTOM" else "#475569")
            page_header(
                "밸류에이션 (Forward PER)",
                f"나스닥100 12M 선행 PER 20년 시계열 · 역사적 분위수 · 현재 출처: {provider} ({collected_at})",
                icon="pie_chart",
                badge_text=f"{status} · {provider}",
                badge_color=badge_bg,
            )

            with ui.row().classes("items-center gap-2"):
                async def _on_quick_sync():
                    sync_btn.props("loading")
                    ui.notify("실시간 Forward PER 데이터를 수집 중입니다 (Yahoo/Finviz/FRED)...", type="info")
                    res = await asyncio.to_thread(sync_live_forward_per, "auto")
                    sync_btn.props(remove="loading")
                    if res.get("ok"):
                        render_valuation_view.refresh()
                        extra = f", NDX: {res['ndx_price']:,.1f}" if res.get("ndx_price") else ""
                        ui.notify(
                            f"실시간 연동 완료! Forward PER: {res['forward_per']}배 ({res['provider']}{extra})",
                            type="positive",
                        )
                    else:
                        ui.notify(res.get("message", "연동 실패"), type="warning")

                sync_btn = ui.button(
                    "실시간 Forward PER 연동",
                    icon="sync",
                    on_click=_on_quick_sync,
                ).props("unelevated dense").style(
                    "background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;"
                    "font-weight:700;padding:6px 14px;border-radius:8px;"
                )

                ui.button(
                    "연동 설정 / 직접 계산",
                    icon="tune",
                    on_click=config_dialog.open,
                ).props("outline color=info dense").classes("px-3")

        with ui.tabs().props("mobile-arrows outside-arrows").classes("w-full") as tabs:
            tab_ov = ui.tab("개요")
            tab_20y = ui.tab("장기 추이 (20년)")
            tab_dist = ui.tab("역사적 분포")
            tab_cmp = ui.tab("지표 비교")

        kpi_meta = [
            ("Forward PER (현재)", "forward_per", False, "pie_chart",   "#c084fc"),
            ("10년 평균",          "avg_10y",     False, "straighten",  "#38bdf8"),
            ("평균 대비",          "vs_avg",      True,  "percent",     "#10b981"),
            ("20년 백분위",        "percentile",  False, "leaderboard", "#f59e0b"),
        ]
        with ui.element("div").classes("kpi-grid-4"):
            for label, key, hl, ic, acc in kpi_meta:
                d = kpi.get(key, {"value": "-"})
                kpi_card(label, d["value"], "", "flat", hl, ic, acc)

        with ui.tab_panels(tabs, value=tab_ov).classes("w-full"):
            with ui.tab_panel(tab_ov).classes("p-0"):
                with ui.row().classes("w-full gap-4 items-stretch responsive-row"):
                    with ui.column().classes("flex-[7] min-w-0"):
                        with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                            section_title("나스닥100 Forward PER 추이 (20년)", curr_per_str, "rgba(192,132,252,0.18)", "#c084fc")
                            _per_trend_echart(trend_data)
                    with ui.column().classes("flex-[3] min-w-0").style("min-width:260px;"):
                        _per_distribution_panel(dist_data)

            with ui.tab_panel(tab_20y).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("나스닥100 Forward PER 20년 장기 시계열", curr_per_str, "rgba(192,132,252,0.18)", "#c084fc")
                    _per_trend_echart(trend_data)

            with ui.tab_panel(tab_dist).classes("p-0"):
                _per_distribution_panel(dist_data)

            with ui.tab_panel(tab_cmp).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("기간별 Forward PER 밸류에이션 비교", curr_per_str)
                    cols = [
                        {"name": k, "label": k, "field": k, "align": "left" if k == "구간" else "right"}
                        for k in ["구간", "Forward PER", "10년 평균 대비", "분위수", "평가"]
                    ]
                    ui.table(columns=cols, rows=analysis_rows, row_key="구간").classes("w-full")

    with ui.column().classes("w-full gap-5 page-container"):
        render_valuation_view()
