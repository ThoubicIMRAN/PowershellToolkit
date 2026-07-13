import shutil,sqlite3,tempfile
from pathlib import Path
from services import repository as repo

def test_database_integrity():
    health=repo.health()
    assert health['integrity']=='ok'
    assert health['foreign_key_errors']==0
    assert health['commands']==420
    assert health['categories']==22

def test_search():
    rows,total=repo.list_commands(search='Flush DNS',page_size=10)
    assert total>=1
    assert any('Flush DNS' in row['title'] for row in rows)

def test_no_delete_api():
    assert not hasattr(repo,'delete_command')
