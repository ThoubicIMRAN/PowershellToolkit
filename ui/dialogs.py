"""Add / Edit / Preview dialogs (st.dialog)."""
from __future__ import annotations
import streamlit as st

from services import auth, repository as repo
from ui.components import e, multiline, risk_class


def flash(message: str, icon: str = '✅') -> None:
    """Queue a toast that survives the st.rerun() that follows a successful action."""
    st.session_state['flash'] = (message, icon)


def command_form(command=None) -> None:
    if not auth.is_admin():
        st.error('Administrator permission is required.')
        return
    cats = repo.categories()
    names = [x['name'] for x in cats]
    ids = {x['name']: x['id'] for x in cats}
    icons = {x['name']: (x.get('icon') or '📁') for x in cats}
    selected = names.index(command['category']) if command and command['category'] in names else 0

    with st.form(f"command_{command['id'] if command else 'new'}", border=False):
        a, b = st.columns(2)
        a.text_input('Command ID', value=str(command['id']) if command else '', placeholder='Auto-assigned',
                     disabled=True, help='IDs are assigned by the database and cannot be edited.')
        category = b.selectbox('Category', names, index=selected, format_func=lambda n: f'{icons[n]}  {n}')
        title = st.text_input('Title *', value=command['title'] if command else '', placeholder='e.g. High CPU Processes')
        text = st.text_area('PowerShell Command *', value=command['command_text'] if command else '', height=150,
                            placeholder='Get-Process | Sort CPU -Desc | Select -First 10')
        a, b = st.columns(2)
        purpose = a.text_input('Purpose', value=command['purpose'] if command else '', placeholder='What it does')
        expected = b.text_input('Expected Result', value=command['expected_result'] if command else '',
                                placeholder='What you see')
        a, b = st.columns(2)
        risk = a.selectbox('Risk Level', repo.RISK_LEVELS,
                           index=repo.RISK_LEVELS.index(command['risk_level']) if command and command['risk_level'] in repo.RISK_LEVELS else 0)
        usage = b.selectbox('Usage', repo.USAGE_TYPES,
                            index=repo.USAGE_TYPES.index(command['usage_type']) if command and command['usage_type'] in repo.USAGE_TYPES else 2)
        notes = st.text_input('Notes / Cautions (optional)', value=command['notes'] if command else '',
                              placeholder='Warnings, prerequisites, tips...')
        if st.form_submit_button('Save Command', type='primary', width='stretch'):
            if not title.strip() or not text.strip():
                st.error('Title and PowerShell Command are required.')
                return
            try:
                repo.save_command({
                    'category_id': ids[category], 'title': title, 'command_text': text,
                    'purpose': purpose, 'expected_result': expected, 'risk_level': risk,
                    'usage_type': usage, 'notes': notes,
                }, command_id=command['id'] if command else None)
                flash('Command updated' if command else 'Command added')
                st.rerun()
            except Exception as error:
                st.error(str(error))


@st.dialog('Add Command', width='large')
def add_dialog():
    command_form()


@st.dialog('Edit Command', width='large')
def edit_dialog(command_id):
    command = repo.get_command(command_id)
    if command:
        command_form(command)
    else:
        st.error('Command not found.')


@st.dialog('Command Preview', width='large')
def preview_dialog(command_id):
    command = repo.get_command(command_id)
    if not command:
        st.error('Command not found.')
        return
    st.html(f'<div class="pv-title"><span class="card-id">#{int(command["id"])}</span> {e(command["title"])}</div>')
    st.code(command['command_text'], language='powershell')   # built-in copy button

    def item(label, value, cls='', full=False):
        return (f'<div class="pv-item{" pv-full" if full else ""}"><div class="pv-label">{label}</div>'
                f'<div class="pv-value {cls}">{value}</div></div>')

    blocks = [
        item('Purpose', e(command['purpose']) or '—'),
        item('Expected Result', e(command['expected_result']) or '—'),
        item('Risk Level', f'<span class="risk-badge {risk_class(command["risk_level"])}">{e(command["risk_level"])}</span>'),
        item('Usage', e(command['usage_type'])),
        item('Category', e(command['category']), full=True),
    ]
    if command.get('notes'):
        blocks.append(item('⚠️ Notes / Caution', e(command['notes']), 'pv-notes-value', full=True))
    st.html(f'<div class="pv-grid">{"".join(blocks)}</div>')

    if auth.is_admin() and st.button('✏️ Edit This Command', key=f'pv_edit_{command_id}', type='primary', width='stretch'):
        st.session_state.pending_edit = command_id
        st.rerun()
