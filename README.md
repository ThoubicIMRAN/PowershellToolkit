# PowerShell Master Toolkit Enterprise

A production-oriented Streamlit command library with SQLite persistence and role-based administration.

## Included
- 420 commands and 22 categories migrated from the supplied HTML
- Dark responsive interface
- Search, category, risk and usage filters
- Pagination and native code-block copy control
- Default User role: browse, view, copy, filter and export
- Admin role: add, edit, import, audit and database health
- Command deletion is not implemented
- Reset Filters changes only UI filters and never modifies database data
- PBKDF2-SHA256 administrator password verification
- SQLite WAL mode, foreign keys, transactions, indexes and audit logs
- Windows, Linux and Docker launch options

## Windows quick start
1. Extract the ZIP.
2. Run `generate_password_hash.py` and copy the printed hash.
3. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
4. Replace the example hash in `secrets.toml`.
5. Run `start_windows.bat`.
6. Open `http://localhost:8501`.

## Manual start
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python generate_password_hash.py
streamlit run app.py
```

## Docker
Generate a password hash, copy `.env.example` to `.env`, add the hash, then run:
```bash
docker compose up -d --build
```

## Permissions
### User
- Browse, search and filter
- View and copy commands
- Export JSON
- Reset filters

### Administrator
- All User capabilities
- Add and edit commands
- Import commands
- View audit logs and database health

Deletion is disabled for both roles.

## Enterprise notes
- Put the application behind an approved reverse proxy or Entra ID for shared deployment.
- SQLite is suitable for a single Streamlit instance. Use PostgreSQL for multiple replicas or heavy concurrent writing.
- Back up `database/toolkit.db` regularly and protect filesystem permissions.
