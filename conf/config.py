"""
TQQQ Lab - Configuration & Design Tokens
"""
import os

# ── 프로젝트 루트 ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── SQLite DB ──────────────────────────────────────────────────
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "tqqq_lab.db")

# ── SQL XML 매퍼 경로 ─────────────────────────────────────────
SQL_DIR = os.path.join(BASE_DIR, "sqls")

# ── 앱 설정 ───────────────────────────────────────────────────
APP_TITLE = "TQQQ Lab — NASDAQ-100 Quant Terminal"
APP_HOST = "0.0.0.0"
APP_PORT = 8080
APP_RELOAD = False

# ── 프리미엄 다크 핀테크 디자인 토큰 ──────────────────────────
COLORS = {
    "bg_dark":    "#070b14",
    "card":       "#11192c",
    "card_hover": "#162038",
    "sidebar":    "#0a101f",
    "accent":     "#38bdf8",
    "primary":    "#3b82f6",
    "purple":     "#a855f7",
    "green":      "#10b981",
    "red":        "#f43f5e",
    "yellow":     "#f59e0b",
    "text":       "#f1f5f9",
    "text_muted": "#94a3b8",
    "border":     "rgba(148, 163, 184, 0.15)",
}

FRED_API_KEY = os.getenv("FRED_API_KEY", "")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "")
