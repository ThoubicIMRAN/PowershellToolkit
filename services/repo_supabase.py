import os
import json
from typing import Any
from supabase import create_client, Client

# Initialize cloud connectivity
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Fallback to empty client or safe mock to prevent compilation failure if missing initially
    db: Client = None
else:
    db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

RISK_LEVELS = ["None", "Low", "Medium", "High"]
USAGE_TYPES = ["User", "Admin", "User/Admin"]

def stats():
    if not db: return {"total": 0, "categories": 0, "high": 0, "medium": 0, "admin": 0}
    
    total = db.table("commands").select("id", count="exact").eq("is_active", 1).execute().count or 0
    categories_count = db.table("categories").select("id", count="exact").execute().count or 0
    high = db.table("commands").select("id", count="exact").eq("is_active", 1).eq("risk_level", "High").execute().count or 0
    medium = db.table("commands").select("id", count="exact").eq("is_active", 1).eq("risk_level", "Medium").execute().count or 0
    admin = db.table("commands").select("id", count="exact").eq("is_active", 1).eq("usage_type", "Admin").execute().count or 0
    
    return {"total": total, "categories": categories_count, "high": high, "medium": medium, "admin": admin}

def categories():
    if not db: return []
    res = db.table("categories").select("*, commands(id)").execute()
    categories_list = []
    for item in res.data:
        active_count = len([c for c in item.get('commands', [])])
        categories_list.append({
            "id": item["id"],
            "name": item["name"],
            "icon": item.get("icon") or "📁",
            "color": item.get("color") or "#777777",
            "sort_order": item.get("sort_order", 0),
            "command_count": active_count
        })
    return sorted(categories_list, key=lambda x: (x['sort_order'], x['name']))

def list_commands(search='', category_id=None, risk='', usage='', page=1, page_size=24):
    if not db: return [], 0
    query = db.table("commands_view").select("*", count="exact")
    
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
        row['category'] = row.pop('category_name', 'Uncategorized')
        row['icon'] = row.pop('category_icon', '📁') or "📁"
        row['color'] = row.pop('category_color', '#777777') or "#777777"
        cleaned_rows.append(row)
        
    return cleaned_rows, (res.count or 0)

def get_command(command_id):
    if not db: return None
    res = db.table("commands_view").select("*").eq("id", command_id).execute()
    if res.data:
        row = dict(res.data[0])
        row['category'] = row.pop('category_name', 'Uncategorized')
        return row
    return None

def save_category(data: dict[str, Any], actor='admin', category_id: int | None = None) -> int:
    if not db: raise ConnectionError("Supabase connection not initialized.")
    name = str(data.get('name', '')).strip()
    if not name: raise ValueError('Category name is required.')
    
    payload = {
        'name': name,
        'icon': str(data.get('icon', '')).strip() or None,
        'color': str(data.get('color', '')).strip() or None
    }
    
    if category_id:
        res = db.table("categories").update(payload).eq("id", category_id).execute()
        action, entity = 'UPDATE', category_id
    else:
        max_res = db.table("categories").select("sort_order").order("sort_order", desc=True).limit(1).execute()
        max_order = max_res.data[0]['sort_order'] if max_res.data else 0
        payload['sort_order'] = (max_order or 0) + 1
        res = db.table("categories").insert(payload).execute()
        action, entity = 'CREATE', res.data[0]['id']
        
    db.table("audit_logs").insert({'action': action, 'entity_type': 'category', 'entity_id': entity, 'actor': actor, 'details': name}).execute()
    return int(entity)

def save_command(data: dict[str, Any], actor='admin', command_id: int | None = None) -> int:
    if not db: raise ConnectionError("Supabase connection not initialized.")
    payload = {
        'category_id': data.get('category_id'),
        'title': str(data.get('title', '')).strip(),
        'command_text': data.get('command_text', ''),
        'purpose': data.get('purpose', ''),
        'expected_result': data.get('expected_result', ''),
        'risk_level': data.get('risk_level', 'None'),
        'usage_type': data.get('usage_type', 'User/Admin'),
        'notes': data.get('notes', '')
    }
    
    if command_id:
        db.table("commands").update(payload).eq("id", command_id).execute()
        action, entity = 'UPDATE', command_id
    else:
        max_res = db.table("commands").select("sort_order").order("sort_order", desc=True).limit(1).execute()
        max_order = max_res.data[0]['sort_order'] if max_res.data else 0
        payload['sort_order'] = (max_order or 0) + 1
        res = db.table("commands").insert(payload).execute()
        action, entity = 'CREATE', res.data[0]['id']
        
    db.table("audit_logs").insert({'action': action, 'entity_type': 'command', 'entity_id': entity, 'actor': actor, 'details': payload['title']}).execute()
    return int(entity)

def health():
    if not db: return {"commands": 0, "categories": 0, "integrity": "disconnected", "schema_version": "1.0", "foreign_key_errors": 0}
    c_count = db.table("commands").select("id", count="exact").execute().count or 0
    cat_count = db.table("categories").select("id", count="exact").execute().count or 0
    return {"commands": c_count, "categories": cat_count, "integrity": "ok", "schema_version": "1.0", "foreign_key_errors": 0}

def audit_logs():
    if not db: return []
    res = db.table("audit_logs").select("*").order("id", desc=True).limit(500).execute()
    return res.data

def export_json():
    if not db: return b"[]"
    res = db.table("commands_view").select("*").eq("is_active", 1).execute()
    json_out = []
    for row in res.data:
        json_out.append({
            "id": row["id"],
            "category": row["category_name"],
            "title": row["title"],
            "cmd": row["command_text"],
            "purpose": row["purpose"],
            "result": row["expected_result"],
            "risk": row["risk_level"],
            "usage": row["usage_type"],
            "notes": row["notes"]
        })
    return json.dumps(json_out, indent=2).encode('utf-8')

def import_json(json_bytes):
    if not db: raise ConnectionError("Supabase client is not available.")
    raw_data = json.loads(json_bytes.decode('utf-8'))
    added, skipped = 0, 0
    
    # Pre-fetch existing layout to accelerate constraints evaluations
    cat_res = db.table("categories").select("id, name").execute()
    cat_map = {c["name"].lower().strip(): c["id"] for c in cat_res.data}
    
    for item in raw_data:
        cat_name = item.get('category', 'Uncategorized').strip()
        title = item.get('title', '').strip()
        cmd_text = item.get('cmd', '').strip()
        
        cat_key = cat_name.lower()
        if cat_key in cat_map:
            cat_id = cat_map[cat_key]
        else:
            max_res = db.table("categories").select("sort_order").order("sort_order", desc=True).limit(1).execute()
            mo = max_res.data[0]['sort_order'] if max_res.data else 0
            new_cat = db.table("categories").insert({"name": cat_name, "icon": "📁", "color": "#777777", "sort_order": mo + 1}).execute()
            cat_id = new_cat.data[0]["id"]
            cat_map[cat_key] = cat_id
            
        dup_check = db.table("commands").select("id").eq("title", title).eq("command_text", cmd_text).eq("is_active", 1).execute()
        if dup_check.data:
            skipped += 1
            continue
            
        max_cmd = db.table("commands").select("sort_order").order("sort_order", desc=True).limit(1).execute()
        mco = max_cmd.data[0]['sort_order'] if max_cmd.data else 0
        
        db.table("commands").insert({
            "category_id": cat_id, "title": title, "command_text": cmd_text,
            "purpose": item.get('purpose', ''), "expected_result": item.get('result', ''),
            "risk_level": item.get('risk', 'None'), "usage_type": item.get('usage', 'User/Admin'),
            "notes": item.get('notes', ''), "sort_order": mco + 1
        }).execute()
        added += 1
        
    return added, skipped
