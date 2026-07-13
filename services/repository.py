from __future__ import annotations
import json
import streamlit as st
from typing import Any
from supabase import create_client, Client

# 1. Initialize Global Cloud Database Client Connection
SUPABASE_URL: str = st.secrets["supabase"]["url"]
SUPABASE_KEY: str = st.secrets["supabase"]["key"]
db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

RISK_LEVELS = ('None', 'Low', 'Medium', 'High')
USAGE_TYPES = ('User', 'Admin', 'User/Admin')

def init_db():
    """No longer requires manual local structural generation; Supabase manages persistence."""
    pass

def health() -> dict[str, Any]:
    try:
        cmd_count = db.table("commands").select("id", count="exact").eq("is_active", 1).limit(1).execute().count
        cat_count = db.table("categories").select("id", count="exact").limit(1).execute().count
        return {
            'integrity': 'ok',
            'foreign_key_errors': 0,
            'commands': cmd_count or 0,
            'categories': cat_count or 0,
            'schema_version': 1
        }
    except Exception as e:
        return {'integrity': f'Error: {str(e)}', 'foreign_key_errors': 1, 'commands': 0, 'categories': 0, 'schema_version': 0}

def categories() -> list[dict[str, Any]]:
    # Pull categories along with relational active command IDs to count them
    res = db.table("categories").select("*, commands(id, is_active)").execute()
    categories_list = []
    
    for item in res.data:
        c_dict = dict(item)
        active_cmds = [c for c in c_dict.get('commands', []) if c.get('is_active') == 1]
        c_dict['command_count'] = len(active_cmds)
        c_dict.pop('commands', None)
        categories_list.append(c_dict)
        
    categories_list.sort(key=lambda x: (x.get('sort_order') or 0, x.get('name') or ''))
    return categories_list

def stats() -> dict[str, int]:
    res = db.table("commands").select("category_id, risk_level, usage_type").eq("is_active", 1).execute()
    data = res.data
    
    total = len(data)
    unique_categories = len({item['category_id'] for item in data if item.get('category_id')})
    high = sum(1 for item in data if item.get('risk_level') == 'High')
    medium = sum(1 for item in data if item.get('risk_level') == 'Medium')
    admin = sum(1 for item in data if item.get('usage_type') == 'Admin')
    
    return {
        'total': total,
        'categories': unique_categories,
        'high': high,
        'medium': medium,
        'admin': admin
    }

def list_commands(search='', category_id=None, risk='', usage='', page=1, page_size=24):
    query = db.table("commands").select("*, categories(name, icon, color)", count="exact").eq("is_active", 1)
    
    if search.strip():
        term = f"%{search.strip()}%"
        query = query.or_(f"title.ilike.{term},command_text.ilike.{term},purpose.ilike.{term},expected_result.ilike.{term},notes.ilike.{term}")
    if category_id:
        query = query.eq('category_id', category_id)
    if risk:
        query = query.eq('risk_level', risk)
    if usage:
        query = query.or_(f"usage_type.eq.{usage},usage_type.eq.User/Admin")
        
    page = max(1, int(page))
    page_size = min(100, max(1, int(page_size)))
    start = (page - 1) * page_size
    end = start + page_size - 1
    
    res = query.order('sort_order').order('id').range(start, end).execute()
    
    cleaned_rows = []
    for item in res.data:
        row = dict(item)
        cat_info = row.pop('categories', None) or {}
        row['category'] = cat_info.get('name', 'Uncategorized')
        row['icon'] = cat_info.get('icon')
        row['color'] = cat_info.get('color')
        row['category_sequence'] = 1 
        cleaned_rows.append(row)
        
    return cleaned_rows, (res.count or 0)

def get_command(command_id: int):
    res = db.table("commands").select("*, categories(name)").eq("id", command_id).eq("is_active", 1).execute()
    if res.data:
        row = dict(res.data[0])
        cat_info = row.pop('categories', None) or {}
        row['category'] = cat_info.get('name', 'Uncategorized')
        return row
    return None

def save_command(data: dict[str, Any], actor='admin', command_id: int | None = None) -> int:
    title = str(data.get('title', '')).strip()
    text = str(data.get('command_text', '')).strip()
    if not title or not text: 
        raise ValueError('Title and PowerShell Command are required.')
        
    risk = data.get('risk_level')
    usage = data.get('usage_type')
    if risk not in RISK_LEVELS or usage not in USAGE_TYPES: 
        raise ValueError('Invalid risk or usage value.')
        
    payload = {
        'category_id': int(data['category_id']),
        'title': title,
        'command_text': text,
        'purpose': str(data.get('purpose', '')).strip(),
        'expected_result': str(data.get('expected_result', '')).strip(),
        'risk_level': risk,
        'usage_type': usage,
        'notes': str(data.get('notes', '')).strip()
    }
    
    if command_id:
        res = db.table("commands").update(payload).eq("id", command_id).eq("is_active", 1).execute()
        if not res.data: 
            raise LookupError('Command not found.')
        action = 'UPDATE'
        entity = command_id
    else:
        max_res = db.table("commands").select("sort_order").order("sort_order", desc=True).limit(1).execute()
        max_order = max_res.data[0]['sort_order'] if max_res.data else 0
        payload['sort_order'] = (max_order or 0) + 1
        
        res = db.table("commands").insert(payload).execute()
        action = 'CREATE'
        entity = res.data[0]['id']
        
    db.table("audit_logs").insert({
        'action': action,
        'entity_type': 'command',
        'entity_id': entity,
        'actor': actor,
        'details': title
    }).execute()
    
    return int(entity)

def import_json(payload: bytes, actor='admin'):
    data = json.loads(payload.decode('utf-8-sig'))
    if not isinstance(data, list): 
        raise ValueError('JSON must contain an array.')
        
    added = skipped = 0
    
    # 1. Network Request 1: Fetch all categories at once to map in memory
    cat_res = db.table("categories").select("id, name").execute()
    cmap = {r['name'].casefold(): r['id'] for r in cat_res.data}
    
    max_cat = db.table("categories").select("sort_order").order("sort_order", desc=True).limit(1).execute()
    next_cat_order = (max_cat.data[0]['sort_order'] if max_cat.data else 0) + 1

    # 2. Network Request 2: Fetch active commands for fast in-memory duplicate checks
    exist_res = db.table("commands").select("title, command_text").eq("is_active", 1).execute()
    existing_set = {(r['title'].casefold(), r['command_text']) for r in exist_res.data}
    
    max_cmd = db.table("commands").select("sort_order").order("sort_order", desc=True).limit(1).execute()
    cmd_order = (max_cmd.data[0]['sort_order'] if max_cmd.data else 0) + 1

    # Phase A: Handle new categories in a single batch
    new_categories_to_create = {}
    for item in data:
        category = str(item.get('category', 'Uncategorized')).strip() or 'Uncategorized'
        key = category.casefold()
        if key not in cmap and key not in new_categories_to_create:
            new_categories_to_create[key] = {
                'name': category,
                'sort_order': next_cat_order
            }
            next_cat_order += 1
            
    if new_categories_to_create:
        created_cats = db.table("categories").insert(list(new_categories_to_create.values())).execute()
        for c in created_cats.data:
            cmap[c['name'].casefold()] = c['id']

    # Phase B: Process and validate commands locally in memory
    commands_to_insert = []
    
    for item in data:
        try:
            title = str(item['title']).strip()
            text = str(item.get('cmd', item.get('command_text', ''))).strip()
            category = str(item.get('category', 'Uncategorized')).strip() or 'Uncategorized'
            risk = str(item.get('risk', 'None'))
            usage = str(item.get('usage', 'User/Admin'))
            
            if not title or not text or risk not in RISK_LEVELS or usage not in USAGE_TYPES: 
                raise ValueError
                
            # Instant local duplicate check (No network lag)
            if (title.casefold(), text) in existing_set:
                skipped += 1
                continue
                
            commands_to_insert.append({
                'category_id': cmap[category.casefold()],
                'title': title,
                'command_text': text,
                'purpose': str(item.get('purpose', '')),
                'expected_result': str(item.get('result', '')),
                'risk_level': risk,
                'usage_type': usage,
                'notes': str(item.get('notes', '')),
                'sort_order': cmd_order
            })
            
            # Add to local cache set to catch duplicates within the same file import
            existing_set.add((title.casefold(), text))
            cmd_order += 1
            added += 1
        except Exception:
            skipped += 1

    # Phase C: Final Network Request 3: Bulk Insert Everything
    if commands_to_insert:
        # Push all records down to Supabase in a single payload layout
        inserted_cmds = db.table("commands").insert(commands_to_insert).execute()
        
        # Build and push audit logs in bulk using the returned record IDs
        audit_logs_to_insert = [{
            'action': 'IMPORT',
            'entity_type': 'command',
            'entity_id': cmd_row['id'],
            'actor': actor,
            'details': cmd_row['title']
        } for cmd_row in inserted_cmds.data]
        
        if audit_logs_to_insert:
            db.table("audit_logs").insert(audit_logs_to_insert).execute()
            
    return added, skipped
def export_json() -> bytes:
    res = db.table("commands").select("id, title, command_text, purpose, expected_result, risk_level, usage_type, notes, categories(name)").eq("is_active", 1).order("id").execute()
    rows = []
    for r in res.data:
        rows.append({
            'id': r['id'],
            'category': (r.get('categories') or {}).get('name', 'Uncategorized'),
            'title': r['title'],
            'cmd': r['command_text'],
            'purpose': r['purpose'],
            'result': r['expected_result'],
            'risk': r['risk_level'],
            'usage': r['usage_type'],
            'notes': r['notes']
        })
    return json.dumps(rows, ensure_ascii=False, indent=2).encode()

def audit_logs(limit=500):
    res = db.table("audit_logs").select("*").order("id", desc=True).limit(limit).execute()
    return [dict(r) for r in res.data]
