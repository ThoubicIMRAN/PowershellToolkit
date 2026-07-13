from __future__ import annotations
import math,sqlite3
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st
from services import auth,repository as repo

st.set_page_config(page_title='PowerShell Master Toolkit',page_icon='⚡',layout='wide',initial_sidebar_state='expanded')
st.markdown(f'<style>{(Path(__file__).parent/"assets/theme.css").read_text(encoding="utf-8")}</style>',unsafe_allow_html=True)
for key,value in {'role':'User','route':'Library','active_category':None,'page':1}.items(): st.session_state.setdefault(key,value)

def reset_filters():
    st.session_state.search=''; st.session_state.risk='All Risks'; st.session_state.usage='All Usage'; st.session_state.active_category=None; st.session_state.page=1

def command_form(command=None):
    if not auth.is_admin(): st.error('Administrator permission is required.'); return
    cats=repo.categories(); names=[x['name'] for x in cats]; ids={x['name']:x['id'] for x in cats}; selected=names.index(command['category']) if command and command['category'] in names else 0
    with st.form(f"command_{command['id'] if command else 'new'}"):
        a,b=st.columns(2); category=a.selectbox('Category',names,index=selected); title=b.text_input('Title *',value=command['title'] if command else '')
        text=st.text_area('PowerShell Command *',value=command['command_text'] if command else '',height=150)
        a,b=st.columns(2); purpose=a.text_input('Purpose',value=command['purpose'] if command else ''); expected=b.text_input('Expected Result',value=command['expected_result'] if command else '')
        a,b=st.columns(2); risk=a.selectbox('Risk Level',repo.RISK_LEVELS,index=repo.RISK_LEVELS.index(command['risk_level']) if command else 0); usage=b.selectbox('Usage',repo.USAGE_TYPES,index=repo.USAGE_TYPES.index(command['usage_type']) if command else 2)
        notes=st.text_input('Notes / Cautions',value=command['notes'] if command else '')
        if st.form_submit_button('Save Command',type='primary',use_container_width=True):
            try:
                repo.save_command({'category_id':ids[category],'title':title,'command_text':text,'purpose':purpose,'expected_result':expected,'risk_level':risk,'usage_type':usage,'notes':notes},command_id=command['id'] if command else None)
                st.success('Command saved.'); st.rerun()
            except Exception as error: st.error(str(error))

@st.dialog('Add Command',width='large')
def add_dialog(): command_form()
@st.dialog('Edit Command',width='large')
def edit_dialog(command_id):
    command=repo.get_command(command_id)
    if command: command_form(command)
    else: st.error('Command not found.')
@st.dialog('Command Preview',width='large')
def preview_dialog(command_id):
    command=repo.get_command(command_id)
    if not command: st.error('Command not found.'); return
    st.subheader(f"#{command['id']} — {command['title']}"); st.caption('Use the copy icon in the code block.'); st.code(command['command_text'],language='powershell')
    a,b=st.columns(2); a.markdown(f"**Purpose**\n\n{command['purpose'] or '—'}"); b.markdown(f"**Expected Result**\n\n{command['expected_result'] or '—'}")
    a,b=st.columns(2); a.markdown(f"**Risk Level**\n\n{command['risk_level']}"); b.markdown(f"**Usage**\n\n{command['usage_type']}")
    st.markdown(f"**Category**\n\n{command['category']}")
    if command['notes']: st.warning(command['notes'])
    if auth.is_admin() and st.button('✏️ Edit This Command',type='primary',use_container_width=True): st.session_state.pending_edit=command_id; st.rerun()

summary=repo.stats(); categories=repo.categories()
with st.sidebar:
    st.markdown('<div class="brand">⚡ PS TOOLKIT</div>',unsafe_allow_html=True); st.markdown(f'<div class="brand-sub">{summary["total"]} Commands · {summary["categories"]} Categories</div>',unsafe_allow_html=True)
    if st.button(f"📋 All Commands · {summary['total']}",use_container_width=True,type='primary' if st.session_state.active_category is None else 'secondary'): st.session_state.active_category=None; st.session_state.page=1; st.session_state.route='Library'; st.rerun()
    st.caption('CATEGORIES')
    for item in categories:
        if st.button(f"{item['icon']} {item['name']} · {item['command_count']}",key=f"cat_{item['id']}",use_container_width=True,type='primary' if st.session_state.active_category==item['id'] else 'secondary'): st.session_state.active_category=item['id']; st.session_state.page=1; st.session_state.route='Library'; st.rerun()
    st.divider(); st.caption('ACCOUNT'); st.markdown(f"**Role:** {st.session_state.role}")
    if auth.is_admin():
        if st.button('⚙ Administration',use_container_width=True): st.session_state.route='Administration'; st.rerun()
        if st.button('Sign Out',use_container_width=True): auth.logout(); st.rerun()
    else:
        if st.button('🔐 Administrator Sign-in',use_container_width=True): st.session_state.route='Administration'; st.rerun()
    st.divider(); st.caption('USER ACTIONS'); st.download_button('↓ Export JSON',repo.export_json(),f'ps_toolkit_{date.today()}.json','application/json',use_container_width=True)

if st.session_state.get('pending_edit'):
    command_id=st.session_state.pop('pending_edit'); edit_dialog(command_id)

if st.session_state.route=='Administration':
    st.title('Administration')
    if not auth.is_admin():
        st.info('Administrator authentication is required to add, edit or import commands.')
        if not auth.configured(): st.error('Admin authentication is not configured. Set auth.admin_password_hash in .streamlit/secrets.toml or PS_TOOLKIT_ADMIN_PASSWORD_HASH.')
        with st.form('admin_login'):
            password=st.text_input('Administrator password',type='password')
            if st.form_submit_button('Sign In',type='primary',use_container_width=True):
                if auth.login(password): st.success('Access granted.'); st.rerun()
                else: st.error('Invalid administrator credentials.')
        if st.button('← Return to Library'): st.session_state.route='Library'; st.rerun()
        st.stop()
    h=repo.health(); metrics=st.columns(4)
    for col,(label,value) in zip(metrics,[('Commands',h['commands']),('Categories',h['categories']),('Integrity',h['integrity']),('Schema',h['schema_version'])]): col.metric(label,value)
    manage,transfer,audit=st.tabs(['Command Management','Import / Export','Audit & Health'])
    with manage:
        st.caption('Administrators can add and edit commands. Command deletion is intentionally disabled.')
        if st.button('＋ Add New Command',type='primary'): add_dialog()
        search=st.text_input('Find command to edit',placeholder='Search by title or command')
        rows,total=repo.list_commands(search=search,page_size=20)
        for command in rows:
            a,b=st.columns([5,1]); a.write(f"**{command['title']}** · {command['category']}");
            if b.button('Edit',key=f"admin_edit_{command['id']}",use_container_width=True): edit_dialog(command['id'])
    with transfer:
        uploaded=st.file_uploader('Import JSON',type=['json'])
        if uploaded and st.button('Import Commands',type='primary'):
            try: added,skipped=repo.import_json(uploaded.getvalue()); st.success(f'Imported {added}; skipped {skipped}.'); st.rerun()
            except Exception as error: st.error(str(error))
        st.download_button('Export Current Commands',repo.export_json(),f'ps_toolkit_{date.today()}.json','application/json')
    with audit:
        if h['integrity']=='ok' and h['foreign_key_errors']==0: st.success('Database integrity and foreign-key checks passed.')
        else: st.error(f"Integrity: {h['integrity']}; foreign-key issues: {h['foreign_key_errors']}")
        st.dataframe(pd.DataFrame(repo.audit_logs()),use_container_width=True,hide_index=True)
    if st.button('← Return to Command Library'): st.session_state.route='Library'; st.rerun()
    st.stop()

search_col,risk_col,usage_col,size_col,reset_col=st.columns([4,1.45,1.45,1,1.25])
search=search_col.text_input('Search',placeholder='Search commands, titles, purpose, category...',key='search',label_visibility='collapsed')
risk_choice=risk_col.selectbox('Risk',['All Risks',*repo.RISK_LEVELS],key='risk',label_visibility='collapsed')
usage_choice=usage_col.selectbox('Usage',['All Usage',*repo.USAGE_TYPES],key='usage',label_visibility='collapsed')
page_size=size_col.selectbox('Page size',[12,24,48,96],index=1,label_visibility='collapsed')
reset_col.button('↺ Reset Filters',use_container_width=True,on_click=reset_filters,help='Clear filters without changing data')
risk='' if risk_choice=='All Risks' else risk_choice; usage='' if usage_choice=='All Usage' else usage_choice
rows,total=repo.list_commands(search,st.session_state.active_category,risk,usage,st.session_state.page,page_size); pages=max(1,math.ceil(total/page_size))
if st.session_state.page>pages: st.session_state.page=pages; st.rerun()
metrics=st.columns(6)
for col,(label,value) in zip(metrics,[('📋 Total',summary['total']),('📂 Categories',summary['categories']),('🔍 Showing',total),('🔴 High Risk',summary['high']),('🟠 Medium Risk',summary['medium']),('🛡 Admin Only',summary['admin'])]): col.metric(label,value)
a,b,c=st.columns([1,3,1])
if a.button('← Previous',disabled=st.session_state.page<=1,use_container_width=True): st.session_state.page-=1; st.rerun()
b.markdown(f"<p class='hint' style='text-align:center'>Page {st.session_state.page} of {pages} · {total} matching commands</p>",unsafe_allow_html=True)
if c.button('Next →',disabled=st.session_state.page>=pages,use_container_width=True): st.session_state.page+=1; st.rerun()
if not rows:
    st.info('No commands match your filters.')
else:
    grouped={}
    for command in rows: grouped.setdefault(command['category'],[]).append(command)
    for category,items in grouped.items():
        meta=items[0]; st.markdown(f'<div class="category-title" style="color:{meta["color"]}">{meta["icon"]} {category} · {len(items)} shown</div>',unsafe_allow_html=True)
        for command in items:
            with st.expander(f"{command['category_sequence']:02d} · {command['title']} | {command['risk_level']} · {command['usage_type']}"):
                st.caption(command['purpose'] or 'No purpose specified'); st.code(command['command_text'],language='powershell')
                x,y=st.columns(2); x.caption(f"Expected: {command['expected_result'] or '—'}"); y.caption(f"Notes: {command['notes'] or '—'}")
                if auth.is_admin():
                    x,y=st.columns(2)
                    if x.button('👁 View',key=f"view_{command['id']}",use_container_width=True): preview_dialog(command['id'])
                    if y.button('✏️ Edit',key=f"edit_{command['id']}",use_container_width=True): edit_dialog(command['id'])
                elif st.button('👁 View Details',key=f"view_{command['id']}",use_container_width=True): preview_dialog(command['id'])
