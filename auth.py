from __future__ import annotations
import hashlib,hmac,os
import streamlit as st

ITERATIONS=310000

def _configured_hash()->str:
    try: value=str(st.secrets.get('auth',{}).get('admin_password_hash',''))
    except Exception: value=''
    return value or os.getenv('PS_TOOLKIT_ADMIN_PASSWORD_HASH','')

def hash_password(password:str,salt:bytes|None=None)->str:
    salt=salt or os.urandom(16)
    digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}'

def verify_password(password:str,encoded:str)->bool:
    try:
        algo,iterations,salt_hex,digest_hex=encoded.split('$',3)
        if algo!='pbkdf2_sha256': return False
        actual=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt_hex),int(iterations)).hex()
        return hmac.compare_digest(actual,digest_hex)
    except Exception: return False

def configured()->bool: return bool(_configured_hash())
def login(password:str)->bool:
    if verify_password(password,_configured_hash()): st.session_state.role='Admin'; return True
    return False
def logout()->None: st.session_state.role='User'; st.session_state.route='Library'
def is_admin()->bool: return st.session_state.get('role')=='Admin'
