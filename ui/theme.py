"""Design-token CSS loading. Static tokens live in assets/theme.css;
only per-category accent colours are generated here."""
from __future__ import annotations
import re
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
DEFAULT_ACCENT = '#3b82f6'
_HEX = re.compile(r'^#[0-9a-fA-F]{6}$')


def safe_color(value, fallback: str = DEFAULT_ACCENT) -> str:
    """Only ever emit a strict #rrggbb value into CSS/HTML (prevents style injection)."""
    v = str(value or '').strip()
    return v.lower() if _HEX.match(v) else fallback


def build_css(categories: list[dict]) -> str:
    base = (ASSETS / 'theme.css').read_text(encoding='utf-8')
    rules = '\n'.join(
        f'[class*="st-key-card_c{int(c["id"])}_"]{{--accent:{safe_color(c.get("color"))}}}'
        for c in categories
    )
    return f'<style>{base}\n{rules}</style>'
