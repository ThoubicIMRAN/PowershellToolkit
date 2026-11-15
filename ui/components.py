"""Reusable UI pieces. All user/DB-supplied text is HTML-escaped before it reaches st.html."""
from __future__ import annotations
from html import escape
import streamlit as st
import streamlit.components.v1 as components

from services import auth, repository as repo
from ui.theme import safe_color

RISK_LABELS = {'All Risks': 'All Risks', 'None': '✅ None', 'Low': '🟡 Low', 'Medium': '🟠 Medium', 'High': '🔴 High'}
USAGE_LABELS = {'All Usage': 'All Usage', 'User': '👤 User', 'Admin': '🛡 Admin', 'User/Admin': '🔑 Both'}
SCOPE_LABELS = {
    'All Scopes': 'All Scopes',
    'Client / Desktop': '🖥 Client / Desktop',
    'Server / Infra': '🖧 Server / Infra',
    'Cloud / SaaS': '☁ Cloud / SaaS',
    'CLI / DevOps': '⌨ CLI / DevOps',
}
_RISK_CLASSES = {'None', 'Low', 'Medium', 'High'}

PLATFORM_OPTIONS = ['All'] + list(getattr(repo, 'PLATFORMS', [
    'Windows', 'Linux', 'Microsoft 365', 'GitHub', 'Cross-Platform',
]))

# Color map for platform badges
_PLATFORM_COLORS = {
    'Windows':       ('#3b82f6', 'rgba(59,130,246,.12)'),
    'Linux':         ('#fbbf24', 'rgba(251,191,36,.12)'),
    'Microsoft 365': ('#a78bfa', 'rgba(167,139,250,.12)'),
    'GitHub':        ('#94a3b8', 'rgba(148,163,184,.12)'),
    'Cross-Platform':('#22d3ee', 'rgba(34,211,238,.12)'),
}

_SCOPE_COLORS = {
    'Client / Desktop': ('#34d399', 'rgba(52,211,153,.12)'),
    'Server / Infra':   ('#fb923c', 'rgba(251,146,60,.12)'),
    'Cloud / SaaS':     ('#a78bfa', 'rgba(167,139,250,.12)'),
    'CLI / DevOps':     ('#22d3ee', 'rgba(34,211,238,.12)'),
}


def e(value) -> str:
    return escape(str(value if value is not None else ''), quote=True)


def multiline(value) -> str:
    """Escape and keep newlines/indentation (white-space: pre-wrap) without breaking the HTML."""
    return e(value).replace('\r\n', '\n').replace('\r', '\n').replace('\n', '&#10;')


def risk_class(risk) -> str:
    return f'risk-{risk}' if risk in _RISK_CLASSES else 'risk-None'


# ───────────────────────── sidebar ─────────────────────────
def render_sidebar(summary: dict, categories: list[dict],
                   platform_filter: str = '', scope_filter: str = '') -> None:
    with st.sidebar:
        st.html(
            '<div class="s-logo"><h1>⚡ PS Toolkit</h1>'
            f'<p>{int(summary["total"])} Commands · {int(summary["categories"])} Categories</p></div>'
        )
        with st.container(key='side_nav'):
            st.html('<span class="s-nav-label">Library</span>')
            if st.button(f"📋  All Commands  ·  {summary['total']}", key='cat_all', width='stretch',
                         type='primary' if st.session_state.active_category is None else 'secondary'):
                _go_category(None)
            st.html('<span class="s-nav-label">Categories</span>')
            for item in categories:
                # When platform/scope filters are active, only show categories that still have matches
                if platform_filter or scope_filter:
                    _, cat_total = repo.list_commands(
                        category_id=item['id'],
                        platform=platform_filter,
                        scope=scope_filter,
                        page=1,
                        page_size=1,
                    )
                    if cat_total == 0:
                        continue
                    count = cat_total
                else:
                    count = item['command_count']

                icon = item.get('icon') or '📁'
                active = st.session_state.active_category == item['id']
                if st.button(f"{icon}  {item['name']}  ·  {count}", key=f"cat_{item['id']}",
                             width='stretch', type='primary' if active else 'secondary'):
                    _go_category(item['id'])

        with st.container(key='side_footer'):
            a, b = st.columns(2, gap='small')
            if a.button('↑ Import', key='nav_import', width='stretch',
                        help='Open Administration → Import / Export (administrator sign-in required)'):
                st.session_state.route = 'Administration'
                st.rerun()
            b.download_button('↓ Export', repo.export_json(), f'ps_toolkit_{_today()}.json', 'application/json',
                              width='stretch', key='nav_export', type='primary')
            if auth.is_admin():
                c, d = st.columns(2, gap='small')
                if c.button('⚙ Admin', key='nav_admin', width='stretch'):
                    st.session_state.route = 'Administration'
                    st.rerun()
                if d.button('Sign Out', key='nav_signout', width='stretch'):
                    auth.logout()
                    st.rerun()
                st.html('<div class="s-role">● Signed in as <b>Admin</b></div>')
            else:
                if st.button('🔐 Administrator Sign-in', key='nav_signin', width='stretch'):
                    st.session_state.route = 'Administration'
                    st.rerun()
                st.html('<div class="s-role">○ Read-only <b>User</b></div>')


def _today() -> str:
    from datetime import date
    return str(date.today())


def _go_category(category_id) -> None:
    st.session_state.active_category = category_id
    st.session_state.page = 1
    st.session_state.route = 'Library'
    st.rerun()


# ───────────────────────── platform selector ─────────────────────────
def render_platform_selector(on_change) -> None:
    """Horizontal platform pills at the top of the library view."""
    current = st.session_state.get('platform', 'All')
    cols = st.columns(len(PLATFORM_OPTIONS), gap='small')
    for i, plat in enumerate(PLATFORM_OPTIONS):
        label = '🌐 All' if plat == 'All' else plat
        is_active = current == plat
        if cols[i].button(
            label,
            key=f'plat_{plat.replace(" ", "_").replace("/", "_")}',
            width='stretch',
            type='primary' if is_active else 'secondary',
            help=f'Filter by {plat}' if plat != 'All' else 'Show all platforms',
        ):
            if st.session_state.platform != plat:
                st.session_state.platform = plat
                on_change()
                st.rerun()


# ───────────────────────── toolbar & stats ─────────────────────────
def render_toolbar(on_filter_change, on_reset, on_add) -> tuple[str, str, str, str]:
    c_search, c_risk, c_usage, c_scope, c_add, c_reset = st.columns(
        [4.2, 1.3, 1.3, 1.6, 0.9, 0.9], gap='small', vertical_alignment='center'
    )
    search = c_search.text_input(
        'Search', placeholder='Search commands, titles, purpose, category...', key='search',
        label_visibility='collapsed', on_change=on_filter_change,
    )
    risk_choice = c_risk.selectbox(
        'Risk', list(RISK_LABELS), key='risk', label_visibility='collapsed',
        format_func=RISK_LABELS.get, on_change=on_filter_change,
    )
    usage_choice = c_usage.selectbox(
        'Usage', list(USAGE_LABELS), key='usage', label_visibility='collapsed',
        format_func=USAGE_LABELS.get, on_change=on_filter_change,
    )
    scope_choice = c_scope.selectbox(
        'Scope', list(SCOPE_LABELS), key='scope', label_visibility='collapsed',
        format_func=SCOPE_LABELS.get, on_change=on_filter_change,
    )
    admin = auth.is_admin()
    if c_add.button(
        '＋ Add', key='btn_add', type='primary', width='stretch', disabled=not admin,
        help='Add a new command' if admin else 'Administrator sign-in required',
    ):
        on_add()
    c_reset.button(
        '↺ Reset', key='btn_reset', width='stretch', on_click=on_reset,
        help='Clear search, filters and category selection (data is not changed)',
    )
    return (
        search,
        ('' if risk_choice == 'All Risks' else risk_choice),
        ('' if usage_choice == 'All Usage' else usage_choice),
        ('' if scope_choice == 'All Scopes' else scope_choice),
    )


def render_stats(summary: dict, showing: int) -> None:
    items = [
        ('📋', 'Total', summary['total']),
        ('📂', 'Categories', summary['categories']),
        ('🔍', 'Showing', showing),
        ('🔴', 'High Risk', summary['high']),
        ('🟠', 'Medium Risk', summary['medium']),
        ('🛡', 'Admin Only', summary['admin']),
    ]
    cells = ''.join(
        f'<div class="stat">{icon} {label} <b>{int(value)}</b></div>'
        for icon, label, value in items
    )
    st.html(f'<div class="statsbar">{cells}</div>')


# ───────────────────────── grid pieces ─────────────────────────
def section_header(name: str, icon: str, color: str, shown: int) -> None:
    st.html(
        f'<div class="sec-hdr"><h3 style="color:{safe_color(color)}">{e(icon)} {e(name)}</h3>'
        f'<div class="sec-hdr-line"></div><span class="sec-hdr-count">{int(shown)} shown</span></div>'
    )


def empty_state() -> None:
    st.html(
        '<div class="empty"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>'
        '<span>No commands match your filters.</span></div>'
    )


def _badge(text: str, fg: str, bg: str) -> str:
    return (
        f'<span class="meta-badge" style="color:{fg};background:{bg};border:1px solid {fg}33">'
        f'{e(text)}</span>'
    )


def _card_html(cmd: dict, seq: int) -> str:
    notes = (cmd.get('notes') or '').strip()
    notes_html = (
        f'<div class="card-notes" title="{e(notes)}">⚠ {e(notes)}</div>' if notes
        else '<div class="card-notes-empty"></div>'
    )

    platform = cmd.get('platform') or 'Windows'
    scope = cmd.get('scope') or 'Client / Desktop'
    p_fg, p_bg = _PLATFORM_COLORS.get(platform, ('#94a3b8', 'rgba(148,163,184,.12)'))
    s_fg, s_bg = _SCOPE_COLORS.get(scope, ('#94a3b8', 'rgba(148,163,184,.12)'))

    badges = (
        f'{_badge(platform, p_fg, p_bg)}'
        f'{_badge(scope, s_fg, s_bg)}'
        f'<span class="risk-badge {risk_class(cmd.get("risk_level"))}">{e(cmd.get("risk_level"))}</span>'
    )

    return (
        '<div class="cmd-body">'
        '<div class="card-top"><div class="card-head-row">'
        f'<div class="card-id">{seq:02d}</div>'
        '<div class="card-title-block">'
        f'<div class="card-title">{e(cmd.get("title"))}</div>'
        f'<div class="card-purpose">{e(cmd.get("purpose") or "No purpose specified")}</div></div>'
        f'<div class="card-badges">{badges}</div>'
        '</div></div>'
        f'<div class="card-code-wrap"><div class="card-code">{multiline(cmd.get("command_text"))}</div></div>'
        f'{notes_html}<div class="card-spacer"></div>'
        '<div class="card-meta">'
        f'<span class="card-usage">{e(cmd.get("usage_type"))}</span>'
        '<span class="card-cat-dot"></span>'
        f'<span class="card-cat-name">{e(cmd.get("category"))}</span></div></div>'
    )


def command_card(cmd: dict, on_view, on_edit) -> None:
    cid = cmd['id']
    seq = int(cmd.get('category_sequence', 1))
    admin = auth.is_admin()
    with st.container(key=f"card_c{int(cmd.get('category_id') or 0)}_{cid}"):
        st.html(_card_html(cmd, seq))
        a, b, c, d = st.columns(4, gap='small')
        # Copy is handled client-side (see copy_script); the button itself needs no server logic.
        a.button('📋 Copy', key=f'copy_{cid}', width='stretch', help='Copy command to clipboard')
        if b.button('👁 View', key=f'view_{cid}', width='stretch', help='View full details'):
            on_view(cid)
        if c.button('✏️ Edit', key=f'edit_{cid}', width='stretch', disabled=not admin,
                    help='Edit command' if admin else 'Administrator sign-in required'):
            on_edit(cid)
        d.button('🗑 Delete', key=f'del_{cid}', width='stretch', disabled=True,
                 help='Deletion is intentionally disabled in this deployment')


def render_pager(total: int, pages: int, page_sizes: list[int], on_size_change) -> None:
    prev_c, info_c, size_c, next_c = st.columns([1, 3, 1.2, 1], gap='small', vertical_alignment='center')
    if prev_c.button('← Previous', key='pg_prev', disabled=st.session_state.page <= 1, width='stretch'):
        st.session_state.page -= 1
        st.rerun()
    info_c.html(f'<div class="pager-info">Page {st.session_state.page} of {pages} · {total} matching commands</div>')
    size_c.selectbox('Page size', page_sizes, key='page_size', label_visibility='collapsed',
                     format_func=lambda n: f'{n} / page', on_change=on_size_change)
    if next_c.button('Next →', key='pg_next', disabled=st.session_state.page >= pages, width='stretch'):
        st.session_state.page += 1
        st.rerun()


# ───────────────────────── client-side copy ─────────────────────────
_COPY_JS = """
<script>
(function () {
  var P = window.parent, D = P.document;
  if (P.__psCopyBound) return;
  P.__psCopyBound = true;
  function toast(msg, ok) {
    var t = D.getElementById('ps-toast');
    if (!t) { t = D.createElement('div'); t.id = 'ps-toast'; D.body.appendChild(t); }
    t.textContent = msg; t.className = 'show ' + (ok ? 'ok' : 'err');
    P.clearTimeout(P.__psToastT);
    P.__psToastT = P.setTimeout(function () { t.className = ''; }, 2200);
  }
  function fallback(text) {
    var ta = D.createElement('textarea');
    ta.value = text; ta.style.cssText = 'position:fixed;opacity:0;top:0;left:0';
    D.body.appendChild(ta); ta.select();
    var ok = false; try { ok = D.execCommand('copy'); } catch (_) {}
    ta.remove(); return ok;
  }
  D.addEventListener('click', function (ev) {
    var btn = ev.target.closest('[class*="st-key-copy_"] button');
    if (!btn) return;
    ev.stopImmediatePropagation(); ev.preventDefault();   // no Streamlit rerun for a pure clipboard action
    var card = btn.closest('[class*="st-key-card_"]');
    var code = card && card.querySelector('.card-code');
    if (!code) { toast('Nothing to copy', false); return; }
    var text = code.textContent;
    var done = function (ok) { toast(ok ? '✓ Command copied to clipboard' : 'Copy failed — use View and copy from there', ok); };
    if (P.navigator.clipboard && P.isSecureContext) {
      P.navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(fallback(text)); });
    } else { done(fallback(text)); }
  }, true);
})();
</script>
"""


def copy_script() -> None:
    with st.container(key='js_mount'):
        components.html(_COPY_JS, height=0)