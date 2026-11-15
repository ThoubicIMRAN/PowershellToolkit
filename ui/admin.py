"""Administration route (sign-in, command/category management, import/export, audit & health).
Behaviour is unchanged from the previous app.py; only presentation and notifications differ."""
from __future__ import annotations
from datetime import date
import pandas as pd
import streamlit as st

from services import auth, repository as repo
from ui.dialogs import add_dialog, edit_dialog, flash


def _back(label: str, key: str) -> None:
    if st.button(label, key=key):
        st.session_state.route = 'Library'
        st.rerun()


def render_admin(categories: list[dict]) -> None:
    st.title('Administration')
    if not auth.is_admin():
        st.info('Administrator authentication is required to add, edit or import commands.')
        if not auth.configured():
            st.error('Admin authentication is not configured. Set auth.admin_password_hash in '
                     '.streamlit/secrets.toml or PS_TOOLKIT_ADMIN_PASSWORD_HASH.')
        with st.form('admin_login'):
            password = st.text_input('Administrator password', type='password')
            if st.form_submit_button('Sign In', type='primary', width='stretch'):
                if auth.login(password):
                    flash('Access granted', '🔓')
                    st.rerun()
                else:
                    st.error('Invalid administrator credentials.')
        _back('← Return to Library', 'admin_back_login')
        st.stop()

    h = repo.health()
    for col, (label, value) in zip(st.columns(4), [('Commands', h['commands']), ('Categories', h['categories']),
                                                   ('Integrity', h['integrity']), ('Schema', h['schema_version'])]):
        col.metric(label, value)

    manage, transfer, audit = st.tabs(['Command Management', 'Import / Export', 'Audit & Health'])

    with manage:
        st.caption('Administrators can add and edit commands. Command deletion is intentionally disabled.')
        if st.button('＋ Add New Command', type='primary', key='admin_add'):
            add_dialog()

        search = st.text_input('Find command to edit', placeholder='Search by title or command')
        rows, _total = repo.list_commands(search=search, page_size=20)
        for command in rows:
            a, b = st.columns([5, 1])
            a.write(f"**{command['title']}** · {command['category']}")
            if b.button('Edit', key=f"admin_edit_{command['id']}", width='stretch'):
                edit_dialog(command['id'])

        st.divider()
        st.subheader('📁 Manage Categories')
        cat_action = st.radio('Choose Action', ['Add New Category', 'Edit Existing Category'], horizontal=True)

        if cat_action == 'Add New Category':
            with st.form('add_category_form'):
                new_name = st.text_input('Category Name', placeholder='e.g., Active Directory')
                new_icon = st.text_input('Emoji Icon', placeholder='e.g., 🔑')
                new_color = st.color_picker('Category Color Theme', '#3b82f6')
                if st.form_submit_button('Create Category', type='primary', width='stretch'):
                    if new_name.strip():
                        try:
                            repo.save_category({'name': new_name, 'icon': new_icon, 'color': new_color})
                            flash(f"Category '{new_name}' created")
                            st.rerun()
                        except Exception as error:
                            st.error(f'Error saving category: {error}')
                    else:
                        st.warning('Category name field cannot be blank.')
        else:
            cat_options = {c['name']: c for c in categories}
            if cat_options:
                selected_name = st.selectbox('Select Category to Modify', list(cat_options))
                target = cat_options[selected_name]
                with st.form('edit_category_form'):
                    edit_name = st.text_input('Category Name', value=target['name'])
                    edit_icon = st.text_input('Emoji Icon', value=target.get('icon') or '📁')
                    color = target.get('color') if str(target.get('color')).startswith('#') else '#3b82f6'
                    edit_color = st.color_picker('Category Color Theme', value=color)
                    if st.form_submit_button('Save Category Changes', type='primary', width='stretch'):
                        try:
                            repo.save_category({'name': edit_name, 'icon': edit_icon, 'color': edit_color},
                                               category_id=target['id'])
                            flash('Category updated')
                            st.rerun()
                        except Exception as error:
                            st.error(f'Error: {error}')
            else:
                st.info('No active categories found to modify.')

    with transfer:
        uploaded = st.file_uploader('Import JSON', type=['json'])
        if uploaded and st.button('Import Commands', type='primary', key='admin_import'):
            try:
                added, skipped = repo.import_json(uploaded.getvalue())
                flash(f'Imported {added}; skipped {skipped}', '📥')
                st.rerun()
            except Exception as error:
                st.error(str(error))
        st.download_button('Export Current Commands', repo.export_json(), f'ps_toolkit_{date.today()}.json',
                           'application/json', key='admin_export')

    with audit:
        if h['integrity'] == 'ok' and h['foreign_key_errors'] == 0:
            st.success('Database integrity and foreign-key checks passed.')
        else:
            st.error(f"Integrity: {h['integrity']}; foreign-key issues: {h['foreign_key_errors']}")
        st.dataframe(pd.DataFrame(repo.audit_logs()), width='stretch', hide_index=True)

    _back('← Return to Command Library', 'admin_back')
    st.stop()
