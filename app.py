from __future__ import annotations
import math
import streamlit as st

st.set_page_config(page_title='PowerShell Master Toolkit', page_icon='⚡', layout='wide',
                   initial_sidebar_state='auto')

from services import repository as repo          # noqa: E402  (after set_page_config by design)
from ui import components as ui                   # noqa: E402
from ui.admin import render_admin                 # noqa: E402
from ui.dialogs import add_dialog, edit_dialog, preview_dialog  # noqa: E402
from ui.theme import build_css                    # noqa: E402

PAGE_SIZES = [12, 24, 48, 96]
for key, value in {
    'role': 'User',
    'route': 'Library',
    'active_category': None,
    'page': 1,
    'page_size': 24,
    'platform': 'All',
    'scope': 'All Scopes',
}.items():
    st.session_state.setdefault(key, value)


def reset_page() -> None:
    st.session_state.page = 1


def reset_filters() -> None:
    st.session_state.search = ''
    st.session_state.risk = 'All Risks'
    st.session_state.usage = 'All Usage'
    st.session_state.platform = 'All'
    st.session_state.scope = 'All Scopes'
    st.session_state.active_category = None
    st.session_state.page = 1


summary = repo.stats()
categories = repo.categories()
st.markdown(build_css(categories), unsafe_allow_html=True)

if st.session_state.get('flash'):
    message, icon = st.session_state.pop('flash')
    st.toast(message, icon=icon)

# Resolve active platform / scope filters for the data layer
platform_filter = '' if st.session_state.platform == 'All' else st.session_state.platform
scope_filter = '' if st.session_state.scope == 'All Scopes' else st.session_state.scope

ui.render_sidebar(summary, categories, platform_filter, scope_filter)

if st.session_state.get('pending_edit'):
    edit_dialog(st.session_state.pop('pending_edit'))

if st.session_state.route == 'Administration':
    render_admin(categories)      # calls st.stop()

# ── Library ──────────────────────────────────────────────
with st.container(key='sticky_head'):
    # Platform selector (horizontal)
    ui.render_platform_selector(reset_page)

    search, risk, usage, scope = ui.render_toolbar(reset_page, reset_filters, add_dialog)
    page_size = st.session_state.page_size

    rows, total = repo.list_commands(
        search,
        st.session_state.active_category,
        risk,
        usage,
        platform=platform_filter,
        scope=scope_filter,
        page=st.session_state.page,
        page_size=page_size,
    )
    pages = max(1, math.ceil(total / page_size))
    ui.render_stats(summary, total)

if st.session_state.page > pages:
    st.session_state.page = pages
    st.rerun()

with st.container(key='grid'):
    if not rows:
        ui.empty_state()
    else:
        grouped: dict[str, list[dict]] = {}
        for command in rows:
            grouped.setdefault(command['category'], []).append(command)
        for category, items in grouped.items():
            meta = items[0]
            ui.section_header(category, meta.get('icon') or '📁', meta.get('color'), len(items))
            for command in items:
                ui.command_card(command, on_view=preview_dialog, on_edit=edit_dialog)

ui.render_pager(total, pages, PAGE_SIZES, reset_page)
ui.copy_script()