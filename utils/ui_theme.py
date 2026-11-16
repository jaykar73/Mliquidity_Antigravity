"""
TQQQ Lab — 공통 프리미엄 핀테크 UI 컴포넌트 빌더
"""
from nicegui import ui
from conf.config import COLORS

CARD_STYLE = (
    "background: linear-gradient(145deg, rgba(19, 28, 49, 0.92) 0%, rgba(11, 18, 33, 0.96) 100%);"
    "border: 1px solid rgba(148, 163, 184, 0.14);"
    "border-radius: 14px;"
    "padding: 20px;"
    "box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.45), inset 0 1px 0 0 rgba(255, 255, 255, 0.05);"
)


def page_header(title: str, subtitle: str, icon: str = "analytics", badge_text: str | None = None, badge_color: str = "#2563eb"):
    """상단 페이지 타이틀 배너."""
    with ui.row().classes("w-full items-center justify-between mb-1 flex-wrap gap-3"):
        with ui.row().classes("items-center gap-3"):
            with ui.element("div").style(
                "width:42px;height:42px;border-radius:12px;"
                "background:linear-gradient(135deg,rgba(59,130,246,0.22) 0%,rgba(6,182,212,0.12) 100%);"
                "border:1px solid rgba(56,189,248,0.3);"
                "display:flex;align-items:center;justify-content:center;"
            ):
                ui.icon(icon, size="22px").style("color:#38bdf8;")
            with ui.column().classes("gap-0"):
                with ui.row().classes("items-center gap-2"):
                    ui.label(title).style("color:#f8fafc;font-size:1.38rem;font-weight:800;letter-spacing:-0.02em;")
                    if badge_text:
                        ui.badge(badge_text).style(
                            f"background:{badge_color};color:#fff;font-weight:700;font-size:0.72rem;padding:3px 9px;border-radius:6px;"
                        )
                ui.label(subtitle).style("color:#64748b;font-size:0.8rem;font-weight:500;")


def kpi_card(
    title: str,
    value: str,
    change: str = "",
    direction: str = "flat",
    highlight: bool = False,
    icon: str | None = None,
    accent_color: str = "#38bdf8",
):
    """핀테크 터미널 스타일 KPI 카드."""
    val_color = "#34d399" if highlight else "#f8fafc"
    with ui.card().style(
        "background: linear-gradient(155deg, rgba(22, 32, 56, 0.94) 0%, rgba(12, 19, 34, 0.98) 100%);"
        "border: 1px solid rgba(148, 163, 184, 0.14);"
        f"border-top: 2px solid {accent_color};"
        "border-radius: 14px; padding: 16px 18px;"
    ).classes("w-full justify-between"):
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            ui.label(title).style("color:#94a3b8;font-size:0.8rem;font-weight:600;")
            if icon:
                ui.icon(icon, size="16px").style(f"color:{accent_color};opacity:0.85;")

        ui.label(value).classes("num-mono").style(
            f"color:{val_color};font-size:1.68rem;font-weight:800;margin:6px 0;letter-spacing:-0.03em;"
        )

        if change:
            if direction == "badge_red":
                with ui.row().classes("items-center"):
                    ui.badge(change).style(
                        "background:rgba(244,63,94,0.18);color:#fb7185;border:1px solid rgba(244,63,94,0.4);"
                        "font-weight:700;font-size:0.75rem;padding:3px 10px;border-radius:9999px;"
                    )
            else:
                is_up = direction == "up"
                is_down = direction == "down"
                arrow = "▲" if is_up else ("▼" if is_down else "•")
                bg = "rgba(16,185,129,0.14)" if is_up else ("rgba(244,63,94,0.14)" if is_down else "rgba(148,163,184,0.12)")
                fg = "#34d399" if is_up else ("#fb7185" if is_down else "#94a3b8")
                bd = "rgba(16,185,129,0.3)" if is_up else ("rgba(244,63,94,0.3)" if is_down else "rgba(148,163,184,0.2)")
                with ui.row().classes("items-center"):
                    ui.label(f"{arrow} {change}").classes("num-mono").style(
                        f"background:{bg};color:{fg};border:1px solid {bd};"
                        "font-size:0.75rem;font-weight:700;padding:2px 9px;border-radius:9999px;"
                    )
        else:
            ui.label("장기 시계열 기준").style("color:#475569;font-size:0.73rem;font-weight:500;")


def section_title(title: str, badge_text: str | None = None, badge_color: str = "rgba(56,189,248,0.16)", badge_fg: str = "#38bdf8"):
    """카드 내부 섹션 타이틀 헤더."""
    with ui.row().classes("w-full items-center justify-between mb-2"):
        with ui.row().classes("items-center gap-2"):
            ui.element("div").style(f"width:4px;height:16px;border-radius:2px;background:{badge_fg};")
            ui.label(title).style("color:#f1f5f9;font-size:1.0rem;font-weight:700;")
        if badge_text:
            ui.badge(badge_text).classes("num-mono").style(
                f"background:{badge_color};color:{badge_fg};border:1px solid {badge_fg}44;"
                "font-weight:700;font-size:0.78rem;padding:4px 10px;border-radius:8px;"
            )
