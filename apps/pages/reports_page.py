"""
09. TQQQ Lab — 리포트 / 알림 페이지 UI (프리미엄 다크 테마)
"""
from datetime import datetime
from nicegui import ui
from conf.config import COLORS
from utils.ui_theme import CARD_STYLE, page_header, section_title
from apps.funcs.reports_func import (
    get_reports,
    get_alerts,
    get_asset_signals,
    create_report,
    save_alert,
)
from apps.funcs.dashboard_func import get_dashboard_kpi, get_investment_signal_score


def create_reports_page():
    """리포트 / 알림 페이지 전체 레이아웃 (실시간 리포트 발행 및 알림 규칙 DB 저장 연동)."""

    @ui.refreshable
    def render_reports_view():
        reports = get_reports(limit=10)
        alerts = get_alerts()
        signals = get_asset_signals()

        with ui.tabs().props("mobile-arrows outside-arrows").classes("w-full") as tabs:
            tab_rep = ui.tab("시장 리포트")
            tab_alt = ui.tab("투자 신호 알림")
            tab_cal = ui.tab("이벤트 캘린더")
            tab_set = ui.tab("설정")

        with ui.tab_panels(tabs, value=tab_rep).classes("w-full"):
            with ui.tab_panel(tab_rep).classes("p-0"):
                with ui.row().classes("w-full gap-4 items-stretch responsive-row"):
                    # 좌측: 최근 리포트
                    with ui.column().classes("flex-1 min-w-0"):
                        with ui.card().style(CARD_STYLE).classes("w-full h-full justify-between"):
                            with ui.column().classes("w-full gap-3"):
                                section_title("최근 리포트", f"{len(reports)}건 발행")
                                for r in reports:
                                    with ui.row().classes(
                                        "w-full items-center justify-between p-4 rounded-xl gap-3"
                                    ).style(
                                        "background:rgba(15,23,42,0.55);border:1px solid rgba(148,163,184,0.12);"
                                    ):
                                        with ui.row().classes("items-center gap-3.5 flex-1 min-w-0 no-wrap"):
                                            with ui.element("div").style(
                                                "width:40px;height:40px;min-width:40px;border-radius:10px;"
                                                "background:rgba(56,189,248,0.14);border:1px solid rgba(56,189,248,0.3);"
                                                "display:flex;align-items:center;justify-content:center;"
                                            ):
                                                ui.icon("description", size="22px").style("color:#38bdf8;")
                                            with ui.column().classes("gap-0.5 flex-1 min-w-0"):
                                                ui.label(r["title"]).style(
                                                    "color:#f1f5f9;font-size:0.95rem;font-weight:700;"
                                                )
                                                if r.get("summary"):
                                                    ui.label(r["summary"]).style(
                                                        "color:#94a3b8;font-size:0.78rem;line-height:1.35;"
                                                    )
                                                ui.label(f"{r['date']} · 시그널 {int(r.get('score', 72))}점").classes("num-mono").style(
                                                    "color:#64748b;font-size:0.74rem;"
                                                )
                                        ui.button(
                                            "PDF",
                                            icon="download",
                                            on_click=lambda t=r["title"]: ui.notify(f"'{t}' PDF 다운로드 완료", type="positive"),
                                        ).props("outline dense color=info").classes("px-3 font-bold")

                            def _generate_live_report():
                                kpi = get_dashboard_kpi()
                                sig = get_investment_signal_score()
                                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                                summary_txt = (
                                    f"Fed 순유동성 {kpi['fed_net_liquidity']['value']}({kpi['fed_net_liquidity']['change']}), "
                                    f"Forward PER {kpi['forward_per']['value']}, 예상 EPS {kpi['expected_eps']['value']}, "
                                    f"CNN 공포탐욕 {kpi['cnn_fear_greed']['value']}({kpi['cnn_fear_greed']['change']}), "
                                    f"10Y 금리 {kpi['treasury_10y']['value']} → {sig['recommendation']}"
                                )
                                create_report(
                                    asof_date=now_str,
                                    strategy_id=1,
                                    score=float(sig["score"]),
                                    recommendation=sig["recommendation"],
                                    features={
                                        "title": f"실시간 퀀트 시장 분석 리포트 ({now_str[:10]})",
                                        "summary": summary_txt,
                                        "bullets": sig.get("bullets", []),
                                    },
                                )
                                render_reports_view.refresh()
                                ui.notify(f"현재 시장 지표 기준 신규 리포트 발행 완료 (시그널 {sig['score']}점)", type="positive")

                            with ui.row().classes("w-full gap-2 mt-4 flex-wrap"):
                                ui.button(
                                    "현재 시장 상태 리포트 즉시 발행",
                                    icon="post_add",
                                    on_click=_generate_live_report,
                                ).props("unelevated color=primary").classes("flex-1")
                                ui.button(
                                    "자동 생성 스케줄 확인",
                                    icon="schedule",
                                    on_click=lambda: ui.notify("매주 금요일 18:00 주간 리포트 자동 생성이 활성화되어 있습니다.", type="info"),
                                ).props("outline color=info").classes("flex-1")

                    # 우측: 투자 신호 알림
                    with ui.column().classes("flex-1 min-w-0"):
                        with ui.card().style(CARD_STYLE).classes("w-full h-full"):
                            section_title("투자 신호 알림", "앱 ON", "rgba(16,185,129,0.18)", "#34d399")

                            bell_colors = {
                                "green":  ("#34d399", "rgba(16,185,129,0.14)", "rgba(16,185,129,0.3)"),
                                "blue":   ("#38bdf8", "rgba(56,189,248,0.14)", "rgba(56,189,248,0.3)"),
                                "yellow": ("#fbbf24", "rgba(245,158,11,0.14)", "rgba(245,158,11,0.3)"),
                            }
                            with ui.column().classes("w-full gap-3 mt-1"):
                                for al in alerts:
                                    b_fg, b_bg, b_bd = bell_colors.get(
                                        al.get("color", "green"),
                                        ("#34d399", "rgba(16,185,129,0.14)", "rgba(16,185,129,0.3)"),
                                    )
                                    with ui.row().classes(
                                        "w-full items-center gap-3.5 p-4 rounded-xl"
                                    ).style(
                                        "background:rgba(15,23,42,0.55);border:1px solid rgba(148,163,184,0.12);"
                                    ):
                                        with ui.element("div").style(
                                            f"width:40px;height:40px;min-width:40px;border-radius:10px;background:{b_bg};border:1px solid {b_bd};"
                                            "display:flex;align-items:center;justify-content:center;"
                                        ):
                                            ui.icon("notifications_active", size="22px").style(f"color:{b_fg};")
                                        with ui.column().classes("gap-0.5 flex-1"):
                                            ui.label(al["name"]).style(
                                                f"color:{b_fg};font-size:0.95rem;font-weight:800;"
                                            )
                                            ui.label(f"{al['message']} ({al['triggered_at']})").style(
                                                "color:#cbd5e1;font-size:0.84rem;"
                                            )

            with ui.tab_panel(tab_alt).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("자산군별 실시간 투자 신호 현황", "4대 자산")
                    cols = [
                        {"name": "asset",  "label": "자산",   "field": "asset",  "align": "left"},
                        {"name": "signal", "label": "신호",   "field": "signal", "align": "center"},
                        {"name": "score",  "label": "점수",   "field": "score",  "align": "right"},
                        {"name": "reason", "label": "근거",   "field": "reason", "align": "left"},
                    ]
                    ui.table(columns=cols, rows=signals, row_key="asset").classes("w-full")

            with ui.tab_panel(tab_cal).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("주요 매크로 & 실적 발표 캘린더", "Upcoming Events")
                    cal_rows = [
                        {"일자": "2026-11-12", "이벤트": "미국 10월 CPI 소비자물가지수 발표", "중요도": "높음"},
                        {"일자": "2026-11-14", "이벤트": "연준 H.4.1 대차대조표 (WALCL) 주간 발표", "중요도": "중간"},
                        {"일자": "2026-11-20", "이벤트": "NVIDIA (NVDA) 분기 실적 발표", "중요도": "높음"},
                        {"일자": "2026-12-16", "이벤트": "12월 FOMC 기준금리 결정 및 점도표", "중요도": "높음"},
                    ]
                    cols = [
                        {"name": k, "label": k, "field": k, "align": "left"}
                        for k in ["일자", "이벤트", "중요도"]
                    ]
                    ui.table(columns=cols, rows=cal_rows, row_key="일자").classes("w-full")

            with ui.tab_panel(tab_set).classes("p-0"):
                with ui.card().style(CARD_STYLE).classes("w-full"):
                    section_title("알림 채널 및 규칙 활성화 설정 (SQLite DB 연동)", "Alert Rules")
                    for al in alerts:
                        with ui.row().classes("w-full items-center justify-between py-3 px-3 rounded-lg mb-2").style(
                            "background:rgba(15,23,42,0.5);border:1px solid rgba(148,163,184,0.1);"
                        ):
                            with ui.column().classes("gap-0"):
                                ui.label(al["name"]).style("color:#f1f5f9;font-weight:700;")
                                ui.label(al["condition"]).style("color:#94a3b8;font-size:0.8rem;")

                            def _toggle_alert(e, item=al):
                                save_alert(
                                    name=item["name"],
                                    condition={"condition": item["condition"], "color": item["color"]},
                                    channel=item["channel"],
                                    enabled=bool(e.value),
                                    alert_id=item["id"],
                                )
                                state_txt = "활성화" if e.value else "비활성화"
                                ui.notify(f"'{item['name']}' 알림이 {state_txt}되었습니다.", type="info")

                            ui.switch(value=al["enabled"], on_change=_toggle_alert).props("color=positive")

    with ui.column().classes("w-full gap-5 page-container"):
        page_header(
            "리포트 / 알림 (Reports & Alerts)",
            "일/주간 자동 생성 시장 분석 리포트 · 조건별 투자 신호 실시간 알림 · 매크로 이벤트 캘린더",
            icon="notifications_active",
            badge_text="앱 알림 ON",
            badge_color="#059669",
        )
        render_reports_view()
