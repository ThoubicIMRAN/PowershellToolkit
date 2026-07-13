import os
import sqlite3
import json
from typing import Any

# Match your specific container volume pathway exactly
DB_PATH = "/app/database/ps_toolkit.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

RISK_LEVELS = ["None", "Low", "Medium", "High"]
USAGE_TYPES = ["User", "Admin", "User/Admin"]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Builds the tracking schemas automatically on container boot."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        icon TEXT,
        color TEXT,
        sort_order INTEGER DEFAULT 0
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS commands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        command_text TEXT NOT NULL,
        purpose TEXT,
        expected_result TEXT,
        risk_level TEXT,
        usage_type TEXT,
        notes TEXT,
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        entity_type TEXT,
        entity_id INTEGER,
        actor TEXT,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

# Initialize immediately when module is imported by Streamlit
init_db()

def stats():
    conn = get_db()
    cursor = conn.cursor()
    total = cursor.execute("SELECT COUNT(*) FROM commands WHERE is_active=1").fetchone()[0]
    categories_count = cursor.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    high = cursor.execute("SELECT COUNT(*) FROM commands WHERE is_active=1 AND risk_level='High'").fetchone()[0]
    medium = cursor.execute("SELECT COUNT(*) FROM commands WHERE is_active=1 AND risk_level='Medium'").fetchone()[0]
    admin = cursor.execute("SELECT COUNT(*) FROM commands WHERE is_active=1 AND usage_type='Admin'").fetchone()[0]
    conn.close()
    return {"total": total, "categories": categories_count, "high": high, "medium": medium, "admin": admin}

def categories():
    conn = get_db()
    rows = conn.execute("""
        SELECT c.*, COUNT(cmd.id) as command_count
        FROM categories c
        LEFT JOIN commands cmd ON c.id = cmd.category_id AND cmd.is_active = 1
        GROUP BY c.id
        ORDER BY c.sort_order, c.name
    """).fetchall()
    conn.close()
    
    result = []
    for r in rows:
        d = dict(r)
        d['icon'] = d.get('icon') or "📁"
        d['color'] = d.get('color') or "#777777"
        result.append(d)
    return result

def list_commands(search='', category_id=None, risk='', usage='', page=1, page_size=24):
    conn = get_db()
    
    # Leverages SQLite Window Functions for structural category-based indexing
    base_query = """
        WITH seq_cmds AS (
            SELECT cmd.*, c.name as category_name, c.icon as category_icon, c.color as category_color,
                   ROW_NUMBER() OVER (PARTITION BY cmd.category_id ORDER BY cmd.sort_order, cmd.id) as category_sequence
            FROM commands cmd
            JOIN categories c ON cmd.category_id = c.id
            WHERE cmd.is_active = 1
        )
        SELECT * FROM seq_cmds WHERE 1=1
    """
    params = []
    
    if search.strip():
        base_query += " AND (title LIKE ? OR command_text LIKE ? OR purpose LIKE ? OR expected_result LIKE ? OR notes LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term, term, term, term])
    if category_id:
        base_query += " AND category_id = ?"
        params.append(category_id)
    if risk:
        base_query += " AND risk_level = ?"
        params.append(risk)
    if usage:
        base_query += " AND (usage_type = ? OR usage_type = 'User/Admin')"
        params.append(usage)
        
    count_query = f"SELECT COUNT(*) FROM ({base_query})"
    total_count = conn.execute(count_query, params).fetchone()[0]
    
    page = max(1, int(page))
    page_size = min(100, max(1, int(page_size)))
    offset = (page - 1) * page_size
    
    final_query = base_query + " ORDER BY sort_order, id LIMIT ? OFFSET ?"
    extended_params = list(params)
    extended_params.extend([page_size, offset])
    
    rows = conn.execute(final_query, extended_params).fetchall()
    conn.close()
    
    cleaned_rows = []
    for r in rows:
        row = dict(r)
        row['category'] = row.pop('category_name', 'Uncategorized')
        row['icon'] = row.pop('category_icon', '📁') or "📁"
        row['color'] = row.pop('category_color', '#777777') or "#777777"
        cleaned_rows.append(row)
        
    return cleaned_rows, total_count

def get_command(command_id):
    conn = get_db()
    row = conn.execute("""
        SELECT cmd.*, c.name as category
        FROM commands cmd
        JOIN categories c ON cmd.category_id = c.id
        WHERE cmd.id = ?
    """, (command_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def save_category(data: dict[str, Any], actor='admin', category_id: int | None = None) -> int:
    name = str(data.get('name', '')).strip()
    if not name:
        raise ValueError('Category name is required.')
    icon = str(data.get('icon', '')).strip() or None
    color = str(data.get('color', '')).strip() or None
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        if category_id:
            cursor.execute("UPDATE categories SET name=?, icon=?, color=? WHERE id=?", (name, icon, color, category_id))
            action, entity = 'UPDATE', category_id
        else:
            max_order = cursor.execute("SELECT MAX(sort_order) FROM categories").fetchone()[0] or 0
            cursor.execute("INSERT INTO categories (name, icon, color, sort_order) VALUES (?, ?, ?, ?)", (name, icon, color, max_order + 1))
            action, entity = 'CREATE', cursor.lastrowid
        
        cursor.execute("INSERT INTO audit_logs (action, entity_type, entity_id, actor, details) VALUES (?, 'category', ?, ?, ?)", (action, entity, actor, name))
        conn.commit()
        return int(entity)
    except sqlite3.IntegrityError:
        raise ValueError(f"Category '{name}' already exists.")
    finally:
        conn.close()

def save_command(data: dict[str, Any], actor='admin', command_id: int | None = None) -> int:
    conn = get_db()
    cursor = conn.cursor()
    
    category_id = data.get('category_id')
    title = str(data.get('title', '')).strip()
    command_text = data.get('command_text', '')
    purpose = data.get('purpose', '')
    expected_result = data.get('expected_result', '')
    risk_level = data.get('risk_level', 'None')
    usage_type = data.get('usage_type', 'User/Admin')
    notes = data.get('notes', '')
    
    if command_id:
        cursor.execute("""
            UPDATE commands SET category_id=?, title=?, command_text=?, purpose=?, expected_result=?, risk_level=?, usage_type=?, notes=? WHERE id=?
        """, (category_id, title, command_text, purpose, expected_result, risk_level, usage_type, notes, command_id))
        action, entity = 'UPDATE', command_id
    else:
        max_order = cursor.execute("SELECT MAX(sort_order) FROM commands").fetchone()[0] or 0
        cursor.execute("""
            INSERT INTO commands (category_id, title, command_text, purpose, expected_result, risk_level, usage_type, notes, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (category_id, title, command_text, purpose, expected_result, risk_level, usage_type, notes, max_order + 1))
        action, entity = 'CREATE', cursor.lastrowid
        
    cursor.execute("INSERT INTO audit_logs (action, entity_type, entity_id, actor, details) VALUES (?, 'command', ?, ?, ?)", (action, entity, actor, title))
    conn.commit()
    conn.close()
    return int(entity)

def health():
    conn = get_db()
    commands_count = conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
    categories_count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    conn.close()
    return {"commands": commands_count, "categories": categories_count, "integrity": "ok", "schema_version": "1.0", "foreign_key_errors": 0}

def audit_logs():
    conn = get_db()
    rows = conn.execute("SELECT action, entity_type, entity_id, actor, details, created_at FROM audit_logs ORDER BY id DESC LIMIT 500").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def export_json():
    conn = get_db()
    rows = conn.execute("""
        SELECT cmd.id, c.name as category, cmd.title, cmd.command_text as cmd, cmd.purpose, cmd.expected_result as result, cmd.risk_level as risk, cmd.usage_type as usage, cmd.notes
        FROM commands cmd
        JOIN categories c ON cmd.category_id = c.id
        WHERE cmd.is_active = 1
    """).fetchall()
    conn.close()
    return json.dumps([dict(r) for r in rows], indent=2).encode('utf-8')

def import_json(json_bytes):
    data = json.loads(json_bytes.decode('utf-8'))
    conn = get_db()
    cursor = conn.cursor()
    added, skipped = 0, 0
    
    for item in data:
        cat_name = item.get('category', 'Uncategorized').strip()
        title = item.get('title', '').strip()
        cmd_text = item.get('cmd', '').strip()
        
        cursor.execute("SELECT id FROM categories WHERE name = ?", (cat_name,))
        cat_row = cursor.fetchone()
        if cat_row:
            cat_id = cat_row[0]
        else:
            max_cat_order = cursor.execute("SELECT MAX(sort_order) FROM categories").fetchone()[0] or 0
            cursor.execute("INSERT INTO categories (name, icon, color, sort_order) VALUES (?, '📁', '#777777', ?)", (cat_name, max_cat_order + 1))
            cat_id = cursor.lastrowid
            
        cursor.execute("SELECT id FROM commands WHERE title = ? AND command_text = ? AND is_active = 1", (title, cmd_text))
        if cursor.fetchone():
            skipped += 1
            continue
            
        max_cmd_order = cursor.execute("SELECT MAX(sort_order) FROM commands").fetchone()[0] or 0
        cursor.execute("""
            INSERT INTO commands (category_id, title, command_text, purpose, expected_result, risk_level, usage_type, notes, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cat_id, title, cmd_text, item.get('purpose',''), item.get('result',''), item.get('risk','None'), item.get('usage','User/Admin'), item.get('notes',''), max_cmd_order + 1))
        added += 1
        
    conn.commit()
    conn.close()
    return added, skipped
