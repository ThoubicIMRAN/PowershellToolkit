from __future__ import annotations
import json, sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

ROOT=Path(__file__).resolve().parents[1]
DB_PATH=ROOT/'database'/'toolkit.db'
RISK_LEVELS=('None','Low','Medium','High')
USAGE_TYPES=('User','Admin','User/Admin')

@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(DB_PATH,timeout=30)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA synchronous=NORMAL')
    con.execute('PRAGMA busy_timeout=30000')
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def health() -> dict[str,Any]:
    with connect() as con:
        return {'integrity':con.execute('PRAGMA integrity_check').fetchone()[0],
                'foreign_key_errors':len(con.execute('PRAGMA foreign_key_check').fetchall()),
                'commands':con.execute('SELECT COUNT(*) FROM commands WHERE is_active=1').fetchone()[0],
                'categories':con.execute('SELECT COUNT(*) FROM categories').fetchone()[0],
                'schema_version':con.execute('SELECT MAX(version) FROM schema_version').fetchone()[0]}

def categories() -> list[dict[str,Any]]:
    with connect() as con:
        return [dict(r) for r in con.execute('''SELECT c.*,COUNT(x.id) command_count FROM categories c LEFT JOIN commands x ON x.category_id=c.id AND x.is_active=1 GROUP BY c.id ORDER BY c.sort_order,c.name''')]

def stats() -> dict[str,int]:
    with connect() as con:
        return dict(con.execute('''SELECT COUNT(*) total,COUNT(DISTINCT category_id) categories,COALESCE(SUM(risk_level='High'),0) high,COALESCE(SUM(risk_level='Medium'),0) medium,COALESCE(SUM(usage_type='Admin'),0) admin FROM commands WHERE is_active=1''').fetchone())

def list_commands(search='',category_id=None,risk='',usage='',page=1,page_size=24):
    clauses=['x.is_active=1']; params=[]
    if search.strip():
        term=f'%{search.strip()}%'; clauses.append('(x.title LIKE ? OR x.command_text LIKE ? OR x.purpose LIKE ? OR x.expected_result LIKE ? OR x.notes LIKE ? OR c.name LIKE ?)'); params.extend([term]*6)
    if category_id: clauses.append('x.category_id=?'); params.append(category_id)
    if risk: clauses.append('x.risk_level=?'); params.append(risk)
    if usage: clauses.append("(x.usage_type=? OR x.usage_type='User/Admin')"); params.append(usage)
    where=' AND '.join(clauses); page=max(1,int(page)); page_size=min(100,max(1,int(page_size))); offset=(page-1)*page_size
    with connect() as con:
        total=con.execute(f'SELECT COUNT(*) FROM commands x JOIN categories c ON c.id=x.category_id WHERE {where}',params).fetchone()[0]
        rows=con.execute(f'''SELECT x.*,c.name category,c.icon,c.color,ROW_NUMBER() OVER(PARTITION BY x.category_id ORDER BY x.sort_order,x.id) category_sequence FROM commands x JOIN categories c ON c.id=x.category_id WHERE {where} ORDER BY c.sort_order,x.sort_order,x.id LIMIT ? OFFSET ?''',params+[page_size,offset]).fetchall()
    return [dict(r) for r in rows],int(total)

def get_command(command_id:int):
    with connect() as con:
        row=con.execute('''SELECT x.*,c.name category FROM commands x JOIN categories c ON c.id=x.category_id WHERE x.id=? AND x.is_active=1''',(command_id,)).fetchone()
        return dict(row) if row else None

def save_command(data:dict[str,Any],actor='admin',command_id:int|None=None)->int:
    title=str(data.get('title','')).strip(); text=str(data.get('command_text','')).strip()
    if not title or not text: raise ValueError('Title and PowerShell Command are required.')
    risk=data.get('risk_level'); usage=data.get('usage_type')
    if risk not in RISK_LEVELS or usage not in USAGE_TYPES: raise ValueError('Invalid risk or usage value.')
    values=(int(data['category_id']),title,text,str(data.get('purpose','')).strip(),str(data.get('expected_result','')).strip(),risk,usage,str(data.get('notes','')).strip())
    with connect() as con:
        if command_id:
            cur=con.execute('''UPDATE commands SET category_id=?,title=?,command_text=?,purpose=?,expected_result=?,risk_level=?,usage_type=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=? AND is_active=1''',values+(command_id,))
            if cur.rowcount!=1: raise LookupError('Command not found.')
            action='UPDATE'; entity=command_id
        else:
            order=con.execute('SELECT COALESCE(MAX(sort_order),0)+1 FROM commands').fetchone()[0]
            cur=con.execute('''INSERT INTO commands(category_id,title,command_text,purpose,expected_result,risk_level,usage_type,notes,sort_order) VALUES(?,?,?,?,?,?,?,?,?)''',values+(order,)); action='CREATE'; entity=cur.lastrowid
        con.execute('INSERT INTO audit_logs(action,entity_type,entity_id,actor,details) VALUES(?,?,?,?,?)',(action,'command',entity,actor,title))
        return int(entity)

def import_json(payload:bytes,actor='admin'):
    data=json.loads(payload.decode('utf-8-sig'))
    if not isinstance(data,list): raise ValueError('JSON must contain an array.')
    added=skipped=0
    with connect() as con:
        cmap={r['name'].casefold():r['id'] for r in con.execute('SELECT id,name FROM categories')}
        for item in data:
            try:
                title=str(item['title']).strip(); text=str(item.get('cmd',item.get('command_text',''))).strip(); category=str(item.get('category','Uncategorized')).strip() or 'Uncategorized'; risk=str(item.get('risk','None')); usage=str(item.get('usage','User/Admin'))
                if not title or not text or risk not in RISK_LEVELS or usage not in USAGE_TYPES: raise ValueError
                key=category.casefold()
                if key not in cmap: cmap[key]=con.execute('INSERT INTO categories(name,sort_order) VALUES(?,(SELECT COALESCE(MAX(sort_order),0)+1 FROM categories))',(category,)).lastrowid
                if con.execute('SELECT 1 FROM commands WHERE title=? COLLATE NOCASE AND command_text=? AND is_active=1',(title,text)).fetchone(): skipped+=1; continue
                order=con.execute('SELECT COALESCE(MAX(sort_order),0)+1 FROM commands').fetchone()[0]
                cur=con.execute('''INSERT INTO commands(category_id,title,command_text,purpose,expected_result,risk_level,usage_type,notes,sort_order) VALUES(?,?,?,?,?,?,?,?,?)''',(cmap[key],title,text,str(item.get('purpose','')),str(item.get('result','')),risk,usage,str(item.get('notes','')),order))
                con.execute("INSERT INTO audit_logs(action,entity_type,entity_id,actor,details) VALUES('IMPORT','command',?,?,?)",(cur.lastrowid,actor,title)); added+=1
            except Exception: skipped+=1
    return added,skipped

def export_json()->bytes:
    with connect() as con:
        rows=[dict(r) for r in con.execute('''SELECT x.id,c.name category,x.title,x.command_text cmd,x.purpose,x.expected_result result,x.risk_level risk,x.usage_type usage,x.notes FROM commands x JOIN categories c ON c.id=x.category_id WHERE x.is_active=1 ORDER BY x.id''')]
    return json.dumps(rows,ensure_ascii=False,indent=2).encode()

def audit_logs(limit=500):
    with connect() as con: return [dict(r) for r in con.execute('SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?',(limit,))]
